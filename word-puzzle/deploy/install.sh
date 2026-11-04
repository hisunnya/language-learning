#!/usr/bin/env bash
# 一键部署到 Ubuntu（nginx + systemd + Python 标准库后端）。
#
#   sudo ./deploy/install.sh
#
# 会做这些事：
#   1. 建系统用户 wordpuzzle
#   2. 把代码放到 /srv/word-puzzle
#   3. 建数据目录 /var/lib/word-puzzle，权限给 wordpuzzle
#   4. 生成内置词库（如果还没有）
#   5. 装 systemd 服务并启动
#   6. 装 nginx 站点配置并重载
#
# 需要 sudo。不会覆盖已有数据库。
set -euo pipefail

SRC_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INSTALL_DIR=/srv/word-puzzle
DATA_DIR=/var/lib/word-puzzle
RUN_USER=wordpuzzle
PORT="${WP_PORT:-8765}"
SITE_NAME="${SITE_NAME:-word-puzzle}"

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "请用 sudo 运行"

command -v python3 >/dev/null 2>&1 || die "缺少 python3"
command -v nginx >/dev/null 2>&1 || die "缺少 nginx，请先 apt install nginx"

say "创建系统用户 $RUN_USER"
if ! id "$RUN_USER" >/dev/null 2>&1; then
  useradd --system --home-dir "$INSTALL_DIR" --shell /usr/sbin/nologin "$RUN_USER"
fi

say "同步代码到 $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete \
    --exclude 'var/' --exclude '.git/' --exclude '__pycache__/' \
    "$SRC_DIR"/ "$INSTALL_DIR"/
else
  cp -a "$SRC_DIR"/. "$INSTALL_DIR"/
  rm -rf "$INSTALL_DIR/.git" "$INSTALL_DIR/var"
fi

say "准备数据目录 $DATA_DIR"
mkdir -p "$DATA_DIR" "$INSTALL_DIR/var/offline"
chown -R "$RUN_USER:$RUN_USER" "$DATA_DIR" "$INSTALL_DIR/var"
chmod 750 "$DATA_DIR"

say "生成内置词库"
if [ ! -f "$INSTALL_DIR/data/pep_curriculum.json" ]; then
  (cd "$INSTALL_DIR" && python3 tools/build_seed_data.py)
else
  echo "    已存在，跳过"
fi

say "安装 systemd 服务"
sed "s|/var/lib/word-puzzle|$DATA_DIR|g" \
    "$INSTALL_DIR/deploy/systemd/word-puzzle.service" \
    > /etc/systemd/system/$SITE_NAME.service
systemctl daemon-reload
systemctl enable "$SITE_NAME"
systemctl restart "$SITE_NAME"
sleep 1
systemctl --no-pager --lines=5 status "$SITE_NAME" || true

say "安装 nginx 站点配置"
if [ -f /etc/nginx/sites-available/$SITE_NAME.conf ]; then
  cp /etc/nginx/sites-available/$SITE_NAME.conf "/etc/nginx/sites-available/$SITE_NAME.conf.bak.$(date +%s)"
fi
sed -e "s|/srv/word-puzzle|$INSTALL_DIR|g" \
    -e "s|127.0.0.1:8765|127.0.0.1:$PORT|g" \
    "$INSTALL_DIR/deploy/nginx/word-puzzle.conf" \
    > "/etc/nginx/sites-available/$SITE_NAME.conf"
ln -sf "/etc/nginx/sites-available/$SITE_NAME.conf" "/etc/nginx/sites-enabled/$SITE_NAME.conf"
nginx -t
systemctl reload nginx

cat <<EOF

  部署完成。

  * 后端：127.0.0.1:$PORT   （systemd: $SITE_NAME）
  * 数据库：$DATA_DIR/app.db
  * 站点：http://<服务器地址>/

  常用命令：
    sudo systemctl status $SITE_NAME
    sudo journalctl -u $SITE_NAME -f
    sudo systemctl restart $SITE_NAME

EOF
