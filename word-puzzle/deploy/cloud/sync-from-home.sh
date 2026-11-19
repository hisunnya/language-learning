#!/usr/bin/env bash
# 在你的电脑上运行：把家里（PVE 宿主机上的 lexica 容器）的数据库整体迁到云服务器。
#
#   bash sync-from-home.sh rehearse            演练：家里的服务不停，取一份在线备份，云上只检查
#   bash sync-from-home.sh rehearse --apply    演练：并且真的换进云上（云上还没对外时可以反复做）
#   bash sync-from-home.sh cutover --yes       正式切换：先停家里的服务，再备份、迁移；家里的服务保持停止
#
# 数据只在家里宿主机和云服务器之间走（scp -3 经你的电脑中转，不在你的电脑上落地）。
# 私有值从环境变量读，不写进仓库：
#   HOME_SSH         登录家里 PVE 宿主机的 ssh 目标（例如 root@<地址>）
#   HOME_CTID        lexica 容器编号
#   HOME_BACKUP_DIR  宿主机上挂进容器的备份目录（容器里是 /backup）
#   CLOUD_SSH        云服务器的 ssh 别名
#
# 切换失败时，如果家里的服务已经停了，脚本会自动把它起回来（学生不该因为迁移失败而一直用不了）。
set -euo pipefail

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

MODE="${1:-}"; shift || true
APPLY=0; YES=0
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --yes) YES=1 ;;
    *) die "不认识的参数：$arg" ;;
  esac
done
[[ "$MODE" == "rehearse" || "$MODE" == "cutover" ]] || die "用法：bash sync-from-home.sh rehearse [--apply] | cutover --yes"
[[ "$MODE" != "cutover" || "$YES" -eq 1 ]] || die "正式切换会停掉家里的服务：确认之后加 --yes"
[[ "$MODE" != "rehearse" || "$YES" -eq 0 ]] || die "--yes 只用于 cutover"
[[ "$MODE" != "cutover" ]] || APPLY=1

HOME_SSH="${HOME_SSH:-}"; HOME_CTID="${HOME_CTID:-}"; HOME_BACKUP_DIR="${HOME_BACKUP_DIR:-}"; CLOUD_SSH="${CLOUD_SSH:-}"
[[ -n "$HOME_SSH" && -n "$HOME_CTID" && -n "$HOME_BACKUP_DIR" && -n "$CLOUD_SSH" ]] \
  || die "要设置 HOME_SSH、HOME_CTID、HOME_BACKUP_DIR、CLOUD_SSH（见脚本开头的说明；私有值在 AGENTS.local.md）"
[[ "$HOME_CTID" =~ ^[0-9]+$ ]] || die "HOME_CTID 必须是数字"
[[ "$HOME_BACKUP_DIR" =~ ^/[A-Za-z0-9._/-]+$ ]] || die "HOME_BACKUP_DIR 必须是绝对路径（字母、数字、._/-）"
[[ "$HOME_SSH" =~ ^[A-Za-z0-9._@:-]+$ && "$CLOUD_SSH" =~ ^[A-Za-z0-9._@:-]+$ ]] || die "HOME_SSH / CLOUD_SSH 格式无效"

SSH=(ssh -o BatchMode=yes -o ConnectTimeout=15)
home() { "${SSH[@]}" "$HOME_SSH" "$@"; }
cloud() { "${SSH[@]}" "$CLOUD_SSH" "$@"; }
SERVICE=word-puzzle-family
REMOTE_COPY=/root/migration/incoming.db

HOME_STOPPED=0
cleanup() {
  local code=$?
  cloud "rm -f $REMOTE_COPY" >/dev/null 2>&1 || true
  if [[ $code -ne 0 && "$HOME_STOPPED" -eq 1 ]]; then
    warn "没有成功：把家里的服务起回来"
    if home "pct exec $HOME_CTID -- systemctl start $SERVICE"; then
      warn "家里的服务已经恢复（云上如果已经换了库，也没关系：云上还没对外）"
    else
      warn "家里的服务没起来！立刻手动：ssh $HOME_SSH 'pct exec $HOME_CTID -- systemctl start $SERVICE'"
    fi
  fi
}
trap cleanup EXIT

say "确认两边都连得上"
home "pct status $HOME_CTID" >/dev/null || die "家里连不上，或者找不到容器 $HOME_CTID"
cloud "test -x /srv/word-puzzle-family/deploy/cloud/migrate-data.sh" || die "云服务器上连不上，或者还没装 deploy/cloud/（先跑 install.sh）"

if [[ "$MODE" == "cutover" ]]; then
  say "正式切换：停掉家里的服务（从这一刻起学生用不了，直到云上接手）"
  home "pct exec $HOME_CTID -- systemctl stop $SERVICE"
  HOME_STOPPED=1
  home "pct exec $HOME_CTID -- systemctl is-active $SERVICE" >/dev/null 2>&1 && die "家里的服务没停下来：不继续"
fi

say "在家里取一份一致的数据库备份（SQLite 在线备份接口）"
home "pct exec $HOME_CTID -- runuser -u wpfamily -- python3 /srv/word-puzzle-family/deploy/family/backup.py /var/lib/word-puzzle-family/app.db /backup 30" \
  || die "家里的备份没做成"
BACKUP_FILE="$(home "ls -1t $HOME_BACKUP_DIR/app-*.db 2>/dev/null | head -1")"
[[ -n "$BACKUP_FILE" ]] || die "家里的备份目录 $HOME_BACKUP_DIR 里没找到 app-*.db"
say "用这份备份：$(basename "$BACKUP_FILE")"

say "送到云服务器（宿主机 → 云，不在你的电脑上留文件）"
cloud "install -d -m 700 /root/migration"
scp -3 -q -o BatchMode=yes "$HOME_SSH:$BACKUP_FILE" "$CLOUD_SSH:$REMOTE_COPY" || die "传输失败"

say "在云服务器上$([[ "$APPLY" -eq 1 ]] && echo '检查并换上' || echo '检查（不改）')"
args=("$REMOTE_COPY"); [[ "$APPLY" -eq 0 ]] || args+=(--apply)
cloud "bash /srv/word-puzzle-family/deploy/cloud/migrate-data.sh ${args[*]}"

if [[ "$MODE" == "cutover" ]]; then
  HOME_STOPPED=0   # 成功了：家里的服务保持停止
  cat <<'EOF'

切换完成：云上已经是最新数据，家里的服务保持停止。
接下来：
  1) 备案已通过的话：域名解析到云服务器 → enable-tls.sh（见 部署说明.md）
  2) 在云上用家里原来的管理员账号登录检查（账号和密码都是家里的，没有变）
  3) 学生换新网址
  如果要退回家里：ssh <家里> 'pct exec <容器编号> -- systemctl start word-puzzle-family'
  （退回之后家里的数据停在切换那一刻；云上之后产生的新数据不会回来）
EOF
fi
