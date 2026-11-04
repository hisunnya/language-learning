#!/usr/bin/env bash
# Deploy Lingua Grove and its three projects behind the host's nginx.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
SERVER_NAME="${LINGUA_SERVER_NAME:-10.211.55.5}"
HUB_ROOT=/var/www/lingua-grove
TOPICS_ROOT=/var/www/topic-app
HAM_ROOT=/var/www/ham-exam
AVAILABLE=/etc/nginx/sites-available/lingua-grove
ENABLED=/etc/nginx/sites-enabled/lingua-grove
LEXICA_ENABLED=/etc/nginx/sites-enabled/word-puzzle.conf

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

[[ $(id -u) -eq 0 ]] || die "请使用 sudo 运行此脚本"
[[ "$SERVER_NAME" =~ ^[A-Za-z0-9.-]+$ ]] || die "LINGUA_SERVER_NAME 格式无效"

say "检查项目依赖"
bash "$REPO_DIR/word-puzzle/deploy/check-deps.sh"

systemctl is-active --quiet word-puzzle || die "词境后端 word-puzzle 未运行，请先部署并启动它"

say "部署三个前端项目"
install -d "$HUB_ROOT" "$HUB_ROOT/shared" "$TOPICS_ROOT" "$HAM_ROOT"
cp -a "$REPO_DIR/hub/index.html" "$REPO_DIR/hub/css" "$REPO_DIR/hub/js" "$HUB_ROOT/"
cp -a "$REPO_DIR/hub/shared/." "$HUB_ROOT/shared/"
cp -a "$REPO_DIR/topic-app/topic-app/." "$TOPICS_ROOT/"
cp -a "$REPO_DIR/ham-exam/index.html" "$REPO_DIR/ham-exam/css" \
  "$REPO_DIR/ham-exam/data" "$REPO_DIR/ham-exam/images" "$REPO_DIR/ham-exam/js" "$HAM_ROOT/"
chown -R www-data:www-data "$HUB_ROOT" "$TOPICS_ROOT" "$HAM_ROOT"

say "启用总主页并将词境挂到 /word-puzzle/"
sed "s|__LINGUA_SERVER_NAME__|$SERVER_NAME|g" \
  "$REPO_DIR/hub/deploy/lingua-grove.conf" > "$AVAILABLE"
ln -sfn "$AVAILABLE" "$ENABLED"

lexica_link_target=""
if [[ -L "$LEXICA_ENABLED" ]]; then
  lexica_link_target="$(readlink "$LEXICA_ENABLED")"
  rm "$LEXICA_ENABLED"
fi

if ! nginx -t; then
  rm -f "$ENABLED"
  if [[ -n "$lexica_link_target" ]]; then
    ln -s "$lexica_link_target" "$LEXICA_ENABLED"
  fi
  die "nginx 配置检查失败；已恢复词境原站点链接"
fi
systemctl reload nginx

cat <<EOF

部署完成。

  总主页：http://$SERVER_NAME/
  每日话题：http://$SERVER_NAME/topics/
  无线电执照：http://$SERVER_NAME/ham/
  词境 Lexica：http://$SERVER_NAME/word-puzzle/

EOF
