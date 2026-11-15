#!/usr/bin/env bash
# Deploy Lingua Grove and its five projects behind the host's nginx.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
# 目标机器地址必须显式给出（环境变量 LINGUA_SERVER_NAME；根目录的 deploy-all 会从不进 git 的 deploy.local.env 读）。
SERVER_NAME="${LINGUA_SERVER_NAME:-}"
[[ -n "$SERVER_NAME" ]] || { printf '请用 LINGUA_SERVER_NAME 指定这台机器的地址\n' >&2; exit 1; }
HUB_ROOT=/var/www/lingua-grove
TOPICS_ROOT=/var/www/topic-app
HAM_ROOT=/var/www/ham-exam
CHEM_ROOT=/var/www/chemistry
PHYS_ROOT=/var/www/physics
CONF_DIR=/etc/nginx/conf.d
CONF_FILE=$CONF_DIR/lingua-grove.conf
LEGACY_HUB_ENABLED=/etc/nginx/sites-enabled/lingua-grove
LEXICA_ENABLED=/etc/nginx/sites-enabled/word-puzzle.conf

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

[[ $(id -u) -eq 0 ]] || die "请使用 sudo 运行此脚本"
[[ "$SERVER_NAME" =~ ^[A-Za-z0-9.-]+$ ]] || die "LINGUA_SERVER_NAME 格式无效"

BACKUP_DIR="$(mktemp -d)"
TEMP_CONF="$CONF_FILE.tmp.$$"
trap 'rm -rf "$BACKUP_DIR"; rm -f "$TEMP_CONF"' EXIT

say "检查项目依赖"
bash "$REPO_DIR/word-puzzle/deploy/check-deps.sh"

# LEXICA_UPSTREAM=主机:端口（例如 <容器IP>:8082）：词境后端在学生版容器里，这台机器的 /word-puzzle/api/ 转给它的内网入口；
# 不设就是本机的 word-puzzle 服务（127.0.0.1:8765）。
LEXICA_UPSTREAM="${LEXICA_UPSTREAM:-}"
if [[ -n "$LEXICA_UPSTREAM" ]]; then
  [[ "$LEXICA_UPSTREAM" =~ ^[A-Za-z0-9.-]+:[0-9]{2,5}$ ]] || die "LEXICA_UPSTREAM 格式应为 主机:端口"
  curl --noproxy '*' -fsS --max-time 8 "http://$LEXICA_UPSTREAM/word-puzzle/api/health" >/dev/null \
    || die "连不上词境后端 http://$LEXICA_UPSTREAM/word-puzzle/api/health；先确认容器的内网入口已部署（WP_LAN_ADDR）"
else
  systemctl is-active --quiet word-puzzle || die "词境后端 word-puzzle 未运行，请先部署并启动它"
fi

say "部署五个前端项目"
[[ -f "$REPO_DIR/chemistry/index.html" ]] || die "缺少化学探秘页面"
[[ -f "$REPO_DIR/physics/index.html" ]] || die "缺少物理探秘页面"
install -d "$HUB_ROOT" "$HUB_ROOT/shared" "$TOPICS_ROOT" "$HAM_ROOT" "$CHEM_ROOT" "$PHYS_ROOT"
cp -a "$REPO_DIR/hub/index.html" "$REPO_DIR/hub/css" "$REPO_DIR/hub/js" "$HUB_ROOT/"
cp -a "$REPO_DIR/hub/shared/." "$HUB_ROOT/shared/"
# 每次部署给 css/js 链接打上新版本号，浏览器一定会重新取。
sed -i "s/__ASSET_VERSION__/$(date +%Y%m%d%H%M%S)/g" "$HUB_ROOT/index.html"
cp -a "$REPO_DIR/topic-app/topic-app/." "$TOPICS_ROOT/"
cp -a "$REPO_DIR/ham-exam/index.html" "$REPO_DIR/ham-exam/css" \
  "$REPO_DIR/ham-exam/data" "$REPO_DIR/ham-exam/images" "$REPO_DIR/ham-exam/js" "$HAM_ROOT/"
# 只拷运行时需要的文件，不把 tests/ 发布到网站目录。
cp -a "$REPO_DIR/chemistry/index.html" "$REPO_DIR/chemistry/css" \
  "$REPO_DIR/chemistry/data" "$REPO_DIR/chemistry/js" "$CHEM_ROOT/"
cp -a "$REPO_DIR/physics/index.html" "$REPO_DIR/physics/css" \
  "$REPO_DIR/physics/data" "$REPO_DIR/physics/js" "$PHYS_ROOT/"
chown -R www-data:www-data "$HUB_ROOT" "$TOPICS_ROOT" "$HAM_ROOT" "$CHEM_ROOT" "$PHYS_ROOT"

say "写入 conf.d 总入口并将词境挂到 /word-puzzle/"
install -d "$CONF_DIR"

old_conf=0
if [[ -e "$CONF_FILE" || -L "$CONF_FILE" ]]; then
  cp -a "$CONF_FILE" "$BACKUP_DIR/lingua-grove.conf"
  old_conf=1
fi
old_hub=0
if [[ -e "$LEGACY_HUB_ENABLED" || -L "$LEGACY_HUB_ENABLED" ]]; then
  cp -a "$LEGACY_HUB_ENABLED" "$BACKUP_DIR/legacy-lingua-grove"
  old_hub=1
  rm -f "$LEGACY_HUB_ENABLED"
fi
old_lexica=0
if [[ -e "$LEXICA_ENABLED" || -L "$LEXICA_ENABLED" ]]; then
  cp -a "$LEXICA_ENABLED" "$BACKUP_DIR/legacy-word-puzzle"
  old_lexica=1
  rm -f "$LEXICA_ENABLED"
fi

# 后端在别处时：upstream 换成它的内网入口，接口路径带上它那边的 /word-puzzle 前缀
UPSTREAM_SERVER="127.0.0.1:8765"
UPSTREAM_PATH="/api/"
if [[ -n "$LEXICA_UPSTREAM" ]]; then UPSTREAM_SERVER="$LEXICA_UPSTREAM"; UPSTREAM_PATH="/word-puzzle/api/"; fi
sed -e "s|__LINGUA_SERVER_NAME__|$SERVER_NAME|g" \
    -e "s|server 127.0.0.1:8765;|server $UPSTREAM_SERVER;|" \
    -e "s|proxy_pass http://lexica_api/api/;|proxy_pass http://lexica_api${UPSTREAM_PATH};|" \
  "$REPO_DIR/hub/deploy/lingua-grove.conf" > "$TEMP_CONF"
chmod 0644 "$TEMP_CONF"
mv "$TEMP_CONF" "$CONF_FILE"

if ! nginx -t; then
  rm -f "$CONF_FILE" "$LEGACY_HUB_ENABLED" "$LEXICA_ENABLED"
  [[ "$old_conf" -eq 0 ]] || cp -a "$BACKUP_DIR/lingua-grove.conf" "$CONF_FILE"
  [[ "$old_hub" -eq 0 ]] || cp -a "$BACKUP_DIR/legacy-lingua-grove" "$LEGACY_HUB_ENABLED"
  [[ "$old_lexica" -eq 0 ]] || cp -a "$BACKUP_DIR/legacy-word-puzzle" "$LEXICA_ENABLED"
  die "nginx 配置检查失败；已恢复部署前的配置"
fi
systemctl reload nginx

cat <<EOF

部署完成。

  总主页：http://$SERVER_NAME/
  每日话题：http://$SERVER_NAME/topics/
  无线电执照：http://$SERVER_NAME/ham/
  化学探秘：http://$SERVER_NAME/chemistry/
  物理探秘：http://$SERVER_NAME/physics/
  词境 Lexica：http://$SERVER_NAME/word-puzzle/

EOF
