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
SERVER_NAME="${WP_SERVER_NAME:-word-puzzle.example.com}"

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "请用 sudo 运行"

[[ "$SERVER_NAME" =~ ^[A-Za-z0-9.-]+$ ]] || die "WP_SERVER_NAME 只能包含字母、数字、点和连字符"

say "检查并安装系统依赖"
bash "$SRC_DIR/deploy/check-deps.sh"

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
mkdir -p "$DATA_DIR" "$INSTALL_DIR/var/offline" "$INSTALL_DIR/var/audio"
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

if [[ "${WP_SKIP_NGINX:-0}" == "1" ]]; then
  say "跳过独立 nginx 站点（由整站入口统一配置）"
else
  say "安装 nginx conf.d 配置"
  CONF_DIR=/etc/nginx/conf.d
  CONF_FILE="$CONF_DIR/$SITE_NAME.conf"
  LEGACY_LINK="/etc/nginx/sites-enabled/$SITE_NAME.conf"
  install -d "$CONF_DIR"
  if [ -f "$CONF_FILE" ]; then
    cp "$CONF_FILE" "$CONF_FILE.bak.$(date +%s)"
  fi
  sed -e "s|/srv/word-puzzle|$INSTALL_DIR|g" \
      -e "s|127.0.0.1:8765|127.0.0.1:$PORT|g" \
      -e "s|word-puzzle.example.com|$SERVER_NAME|g" \
    "$INSTALL_DIR/deploy/nginx/word-puzzle.conf" \
      > "$CONF_FILE"
  if [[ -L "$LEGACY_LINK" ]]; then
    rm "$LEGACY_LINK"
  fi
  nginx -t
  systemctl reload nginx
fi

cat <<EOF

  部署完成。

  * 后端：127.0.0.1:$PORT   （systemd: $SITE_NAME）
  * 数据库：$DATA_DIR/app.db
  * nginx：$([[ "${WP_SKIP_NGINX:-0}" == "1" ]] && echo "交由整站入口配置" || echo "http://$SERVER_NAME/")

  能力自检：
    PDF 文本抽取 : $(command -v pdftotext >/dev/null 2>&1 && echo "已启用 (poppler)" || echo "未安装（用内置解析器）")
    图片版 PDF   : $(command -v tesseract >/dev/null 2>&1 && echo "已启用 (OCR)" || echo "未安装（扫描件读不了）")
    美式女声发音 : $(command -v espeak-ng >/dev/null 2>&1 && echo "已启用 (en-us+f3)" || echo "未安装（用浏览器自带发音）")

  常用命令：
    sudo systemctl status $SITE_NAME
    sudo journalctl -u $SITE_NAME -f
    sudo systemctl restart $SITE_NAME

EOF
