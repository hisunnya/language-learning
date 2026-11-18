#!/usr/bin/env bash
# 部署前保险：在 PVE 宿主机上、部署之前运行一次。
#   1. 备份容器里已安装的代码（/srv/word-puzzle-family 打成 tar，放进备份挂载目录）；
#      存储支持时再给容器打一个快照。挂了宿主机目录（bind mount）的容器，Proxmox 不允许快照，
#      那就只靠 tar + 数据库备份，两者合起来够回滚。
#   2. 用 SQLite 的 backup 接口给数据库做一份一致的备份（回滚数据；不能直接 cp，库是 WAL 模式）
#   3. 记下当前提交，打印出出问题时该敲的回滚命令
# 需要 deploy.local.env 里有 LEXICA_CTID=容器编号（和别的私有值一样，不进仓库）。
# 顺序：先 pre-deploy.sh，再 git pull，再 deploy-all（记下的提交是 pull 之前的，宿主机回滚就回到它）。
#   sudo bash pre-deploy.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$REPO_DIR/deploy.local.env"
[[ -f "$ENV_FILE" ]] || { echo "没有 $ENV_FILE" >&2; exit 1; }
CTID=""
while IFS='=' read -r key value; do
  [[ "$key" == "LEXICA_CTID" ]] && CTID="${value//\"/}"
done < "$ENV_FILE"
[[ "$CTID" =~ ^[0-9]+$ ]] || { echo "deploy.local.env 里要有 LEXICA_CTID=容器编号" >&2; exit 1; }
command -v pct >/dev/null || { echo "要在 PVE 宿主机上运行（找不到 pct）" >&2; exit 1; }

STAMP="$(date +%Y%m%d_%H%M%S)"
SNAP="pre_deploy_$STAMP"
COMMIT="$(git -C "$REPO_DIR" rev-parse --short HEAD)"
NOTE="/root/pre-deploy-$STAMP.txt"

echo "==> 1/3 备份已安装的代码，并尝试容器快照"
CODE_TAR="/backup/$SNAP-code.tgz"
pct exec "$CTID" -- tar czf "$CODE_TAR" -C /srv word-puzzle-family
pct exec "$CTID" -- test -s "$CODE_TAR" || { echo "代码备份没有生成" >&2; exit 1; }
SNAP_OK=0
if pct snapshot "$CTID" "$SNAP" --description "before deploy, repo at $COMMIT" 2>/dev/null; then
  SNAP_OK=1
else
  echo "    容器快照不可用（容器挂了宿主机目录时正常），只用代码 tar + 数据库备份回滚"
fi

echo "==> 2/3 数据库备份"
BACKUP_FILE="/backup/$SNAP.db"
pct exec "$CTID" -- runuser -u wpfamily -- python3 - "$BACKUP_FILE" <<'PY'
import sqlite3, sys
src = sqlite3.connect("/var/lib/word-puzzle-family/app.db", timeout=30)
dst = sqlite3.connect(sys.argv[1])
src.backup(dst)
ok = dst.execute("PRAGMA integrity_check").fetchone()[0]
print("备份完成，完整性检查：", ok, "，schema 版本：", src.execute("PRAGMA user_version").fetchone()[0])
dst.close(); src.close()
if ok != "ok":
    sys.exit("备份没通过完整性检查")
PY

echo "==> 3/3 记录"
cat > "$NOTE" <<NOTE_EOF
部署前状态 $STAMP
  仓库提交      ： $COMMIT
  容器快照      ： $([[ $SNAP_OK == 1 ]] && echo "${SNAP}（容器 ${CTID}）" || echo "无")
  代码备份      ： 容器里 $CODE_TAR
  数据库备份    ： 容器里 $BACKUP_FILE
NOTE_EOF
chmod 600 "$NOTE"

cat <<DONE

保险做好了（记录在 ${NOTE}）。现在可以部署。

出问题时的回滚（学生版容器：代码 + 数据库）：
    pct exec $CTID -- systemctl stop word-puzzle-family
    pct exec $CTID -- bash -c 'rm -rf /srv/word-puzzle-family && tar xzf $CODE_TAR -C /srv'
    pct exec $CTID -- bash -c 'rm -f /var/lib/word-puzzle-family/app.db-wal /var/lib/word-puzzle-family/app.db-shm && cp $BACKUP_FILE /var/lib/word-puzzle-family/app.db && chown wpfamily:wpfamily /var/lib/word-puzzle-family/app.db'
    pct exec $CTID -- systemctl start word-puzzle-family
  （有快照时，也可以 pct stop / pct rollback $CTID $SNAP / pct start 回滚代码和系统，数据库仍要照上面放回备份。）
  宿主机（静态站、nginx）：
    cd $REPO_DIR && git checkout $COMMIT && sudo bash deploy-all-*.sh   # 用那个提交里自带的旧脚本
  回滚数据库会丢掉部署之后产生的成绩和访问记录。
DONE
