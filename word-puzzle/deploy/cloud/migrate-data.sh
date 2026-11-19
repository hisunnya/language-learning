#!/usr/bin/env bash
# 把一份数据库备份整体换进云服务器上的词境（在云服务器上、root 运行）。
#
#   bash migrate-data.sh <备份文件.db>            只检查，什么都不改（默认）
#   bash migrate-data.sh <备份文件.db> --apply    真的换上去
#
# 备份文件是家里用 deploy/family/backup.py 做的一致性备份（SQLite 在线备份接口，不是直接 cp 的半截文件）。
# 换上去之后，云上原来的账号和记录就没有了——整个数据库被家里的替换。所以：
#   - 先把当前云上的库另存一份快照（before-migration-<时间>.db）；
#   - 先检查：完整性、要运行的这版代码能不能打开它（会升级表结构）、里面有没有账号；
#   - 停服务 → 换库 → 起服务 → 健康检查 → 对一遍行数；任何一步不对，自动把快照放回去再起服务，退出码非 0。
# 不碰：.lexica-data 标记、public-url、语音缓存（会按需重新合成）、nginx、证书。
#
# 可以用环境变量改默认值（测试用）：WP_FAMILY_DATA_DIR、WP_FAMILY_INSTALL_DIR、WP_FAMILY_SERVICE、
# WP_FAMILY_NGINX_PORT、WP_FAMILY_USER、WP_MIGRATION_DIR。
set -euo pipefail

CLOUD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${WP_FAMILY_DATA_DIR:-/var/lib/word-puzzle-family}"
INSTALL_DIR="${WP_FAMILY_INSTALL_DIR:-/srv/word-puzzle-family}"
SERVICE="${WP_FAMILY_SERVICE:-word-puzzle-family}"
NGINX_PORT="${WP_FAMILY_NGINX_PORT:-8081}"
RUN_USER="${WP_FAMILY_USER:-wpfamily}"
SNAP_DIR="${WP_MIGRATION_DIR:-/var/backups/lexica/before-migration}"
CHECK="$CLOUD_DIR/dbcheck.py"
DB="$DATA_DIR/app.db"
# 正在使用的库只用服务账号去打开：root 去打开一个 WAL 模式的库，可能留下 root 属主的 -shm，服务就再也打不开它了。
# 脚本可能放在 /root 或某人的家目录里，服务账号读不到，所以复制一份到所有人都能读的临时目录里给它用。
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
chmod 0755 "$WORK"
cp "$CHECK" "$WORK/dbcheck.py"
chmod 0644 "$WORK/dbcheck.py"
as_service() { runuser -u "$RUN_USER" -- python3 "$WORK/dbcheck.py" "$@"; }

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

SOURCE=""; APPLY=0
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    -*) die "不认识的参数：$arg" ;;
    *) [[ -z "$SOURCE" ]] || die "只能给一个备份文件"; SOURCE="$arg" ;;
  esac
done
[[ -n "$SOURCE" ]] || die "用法：bash migrate-data.sh <备份文件.db> [--apply]"
[[ -f "$SOURCE" ]] || die "找不到备份文件：$SOURCE"
[[ $(id -u) -eq 0 ]] || die "请用 root 运行（要停服务、改属主）"
[[ -f "$DB" ]] || die "找不到云上现在的数据库 ${DB}：先运行 deploy/cloud/install.sh"
[[ -e "$DATA_DIR/.lexica-data" ]] || die "$DATA_DIR 里没有 .lexica-data 标记：不像是装好的词境数据目录"

show() { python3 - "$1" "$2" <<'PY'
import json, sys
d = json.loads(sys.argv[2])
c = d["counts"]
print("  %-8s 账号 %s（%s） 题库 %s 成绩 %s 访问记录 %s 登录记录 %s 审计 %s  最近成绩 %s  表结构版本 %s  %.1f MB" % (
    sys.argv[1], c.get("users", "-"), ", ".join("%s %s" % kv for kv in sorted(d["roles"].items())) or "无",
    c.get("banks", "-"), c.get("scores", "-"), c.get("page_views", "-"), c.get("login_events", "-"),
    c.get("audit_log", "-"), d["newest"].get("score") or "无", d["user_version"], d["bytes"] / 1e6))
PY
}
field() { python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print(eval(sys.argv[2]))' "$1" "$2"; }

say "检查备份文件 $SOURCE"
NEW_JSON="$(python3 "$CHECK" inspect "$SOURCE")" || die "备份文件有问题（见上）"
[[ "$(field "$NEW_JSON" 'd["integrity"]')" == "ok" ]] || die "备份文件没通过完整性检查：$(field "$NEW_JSON" 'd["integrity"]')"
[[ "$(field "$NEW_JSON" 'd["counts"].get("users", 0)')" -ge 1 ]] || die "备份里一个账号也没有：很可能拿错了文件（或者是一个空库）。不换"
python3 "$CHECK" open "$SOURCE" "$INSTALL_DIR" >/dev/null || die "要运行的这版代码用不了这个备份（见上）。不换"
CUR_JSON="$(as_service inspect "$DB")" || die "读不了云上现在的库"

say "对比（换上去之后，云上的内容就是『备份』这一行）"
show "云上现在" "$CUR_JSON"
show "备份" "$NEW_JSON"
lost="$(field "$CUR_JSON" 'd["counts"].get("users", 0)')"
warn "云上现在的 $lost 个账号和它们的记录会被备份里的替换（先存一份快照，可以放回去）"

if [[ "$APPLY" -ne 1 ]]; then
  echo
  echo "只是检查，没有改任何东西。确认无误后加 --apply 真的换。"
  exit 0
fi

STAMP="$(date +%Y%m%d_%H%M%S)"
SNAP="$SNAP_DIR/before-migration-$STAMP.db"
install -d -m 0750 -o "$RUN_USER" -g "$(id -gn "$RUN_USER" 2>/dev/null || echo "$RUN_USER")" "$SNAP_DIR" 2>/dev/null || install -d -m 0750 "$SNAP_DIR"
say "存云上当前数据库的快照：$SNAP"
as_service snapshot "$DB" "$SNAP" >/dev/null || die "快照没做成：不换"
chmod 0640 "$SNAP"

healthy() { curl --noproxy '*' -fsS --max-time 5 "http://127.0.0.1:$NGINX_PORT/word-puzzle/api/health" >/dev/null 2>&1; }
wait_healthy() { local i; for i in $(seq 1 30); do healthy && return 0; sleep 1; done; return 1; }

put_db() {   # 把 $1 放成 app.db：属主和权限照现在的 app.db，清掉旧的 WAL / SHM（它们属于旧库）
  local src="$1" tmp="$DATA_DIR/app.db.incoming"
  cp "$src" "$tmp"
  chown --reference="$DB" "$tmp" 2>/dev/null || chown "$RUN_USER:$(id -gn "$RUN_USER" 2>/dev/null || echo "$RUN_USER")" "$tmp"
  chmod --reference="$DB" "$tmp" 2>/dev/null || chmod 0644 "$tmp"
  rm -f "$DB-wal" "$DB-shm"
  mv -f "$tmp" "$DB"
}

rollback() {
  warn "出问题了：把快照放回去，再起服务"
  systemctl stop "$SERVICE" 2>/dev/null || true
  put_db "$SNAP"
  systemctl start "$SERVICE" || true
  wait_healthy && warn "已经回到换之前的样子（快照：${SNAP}）" || warn "服务没起来：journalctl -u $SERVICE -n 50"
}

say "停服务 $SERVICE"
systemctl stop "$SERVICE"
sleep 1

say "换上备份"
if ! put_db "$SOURCE"; then rollback; die "换库失败，已回滚"; fi

say "起服务并做健康检查"
if ! systemctl start "$SERVICE"; then rollback; die "服务起不来，已回滚"; fi
if ! wait_healthy; then rollback; die "健康检查 30 秒内没通过，已回滚"; fi

say "对一遍行数（账号、题库、成绩、访问记录必须和备份一样）"
AFTER_JSON="$(as_service inspect "$DB")" || { rollback; die "读不了换完之后的库，已回滚"; }
bad="$(python3 - "$NEW_JSON" "$AFTER_JSON" <<'PY'
import json, sys
new, after = json.loads(sys.argv[1]), json.loads(sys.argv[2])
# 题库可以变多：后端启动时会补上缺的内置题库（这版代码新加的、或者备份里没有的）；变少才是出了问题。
# 其余的表是人产生的数据，一行都不能多也不能少。
for t in ("users", "banks", "scores", "page_views", "login_events", "teacher_students", "materials", "audit_log"):
    if t not in new["counts"]:
        continue
    got, want = after["counts"].get(t), new["counts"][t]
    if (got is None or got < want) if t == "banks" else got != want:
        print("%s：备份 %s，换完 %s" % (t, want, got))
if after["integrity"] != "ok":
    print("完整性：%s" % after["integrity"])
PY
)"
if [[ -n "$bad" ]]; then printf '%s\n' "$bad" >&2; rollback; die "换完之后的内容和备份对不上，已回滚"; fi
code="$(curl --noproxy '*' -s -o /dev/null -w '%{http_code}' --max-time 5 "http://127.0.0.1:$NGINX_PORT/word-puzzle/api/banks")"
[[ "$code" == "401" ]] || { rollback; die "换完之后未登录访问 /api/banks 应该返回 401，实际 ${code}，已回滚"; }

show "换完" "$AFTER_JSON"
echo
say "完成。云上现在用的是备份里的数据"
echo "    换之前的快照：${SNAP}（确认没问题之后可以删；里面有账号信息，不要留着不管）"
echo "    要放回去：  systemctl stop $SERVICE; cp $SNAP $DB; chown $RUN_USER:$RUN_USER $DB; rm -f $DB-wal $DB-shm; systemctl start $SERVICE"
