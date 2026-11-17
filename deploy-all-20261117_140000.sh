#!/usr/bin/env bash
# 在生产服务器上 git pull 后运行：sudo bash deploy-all-20261117_140000.sh
#
# 这个仓库是公开的：服务器地址、内网地址、公网网址这类私有信息一律不写进仓库，
# 放在仓库根目录下不进 git 的 deploy.local.env（见 deploy.local.env.example），也可以用同名环境变量覆盖：
#   LINGUA_SERVER_NAME  这台机器的地址（必填）
#   LEXICA_UPSTREAM     词境后端的 主机:端口（必填；写 none = 用本机后端 127.0.0.1:8765）
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$REPO_DIR/deploy.local.env" ]]; then
  # 只认 KEY=VALUE 行，已经在环境里设过的变量不被覆盖
  while IFS='=' read -r key value; do
    [[ "$key" =~ ^(LINGUA_SERVER_NAME|LEXICA_UPSTREAM)$ ]] || continue
    [[ -n "${!key:-}" ]] || export "$key=${value//\"/}"
  done < "$REPO_DIR/deploy.local.env"
fi
SERVER_NAME="${LINGUA_SERVER_NAME:-}"
WP_PORT=8765
LEXICA_UPSTREAM="${LEXICA_UPSTREAM:-}"

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

[[ "$(id -u)" -eq 0 ]] || die "请使用 sudo 运行：sudo bash $0"
[[ -n "$SERVER_NAME" ]] || die "没有 LINGUA_SERVER_NAME：请在 deploy.local.env 里写上这台机器的地址（见 deploy.local.env.example）"
[[ "$SERVER_NAME" =~ ^[A-Za-z0-9.-]+$ ]] || die "LINGUA_SERVER_NAME 格式无效"
[[ -n "$LEXICA_UPSTREAM" ]] || die "没有 LEXICA_UPSTREAM：写 主机:端口，或写 none 使用本机后端（见 deploy.local.env.example）"
[[ "$LEXICA_UPSTREAM" != "none" ]] || LEXICA_UPSTREAM=""
command -v curl >/dev/null 2>&1 || die "缺少 curl，请先安装 curl"

for path in \
  word-puzzle/deploy/install.sh \
  word-puzzle/web/img/icon.svg \
  word-puzzle/web/js/release-presets.js \
  word-puzzle/web/js/i18n.js \
  word-puzzle/web/js/i18n-lexica.js \
  word-puzzle/server/accesslog.py \
  word-puzzle/server/tenancy.py \
  word-puzzle/web/tenants.html \
  word-puzzle/web/js/page-tenants.js \
  word-puzzle/web/js/tracker.js \
  word-puzzle/web/visits.html \
  word-puzzle/web/js/page-visits.js \
  hub/deploy/install.sh \
  hub/deploy/lingua-grove.conf \
  topic-app/topic-app/index.html \
  ham-exam/index.html \
  chemistry/index.html \
  chemistry/data/chemistry.json \
  physics/index.html \
  physics/data/physics.json; do
  [[ -f "$REPO_DIR/$path" ]] || die "仓库文件缺失：$path；请确认 git pull 已完成"
done

say "部署词境后端（保留现有数据库）"
WP_PORT="$WP_PORT" \
WP_REMOTE_BACKEND="$([[ -n "$LEXICA_UPSTREAM" ]] && echo 1 || echo 0)" \
SITE_NAME=word-puzzle \
WP_SERVER_NAME="$SERVER_NAME" \
WP_SKIP_NGINX=1 \
  bash "$REPO_DIR/word-puzzle/deploy/install.sh"

say "部署语林门户、每日话题、无线电执照、化学探秘、物理探秘和统一 nginx 入口"
LINGUA_SERVER_NAME="$SERVER_NAME" LEXICA_UPSTREAM="$LEXICA_UPSTREAM" bash "$REPO_DIR/hub/deploy/install.sh"

say "执行整站冒烟检查"
# nginx reload 是异步的：旧 worker 还在应答时会拿到旧配置的 404，所以失败要重试几次。
retry() {
  local what="$1"; shift
  local attempt
  for attempt in 1 2 3 4 5 6 7 8 9 10; do
    "$@" && return 0
    sleep 1
  done
  die "$what"
}

fetch() {
  curl --noproxy '*' --fail --silent --show-error --max-time 15 \
    -H "Host: $SERVER_NAME" "http://127.0.0.1$1"
}

path_ok() { fetch "$1" >/dev/null 2>&1; }

health_ok() {
  fetch /word-puzzle/api/health 2>/dev/null \
    | python3 -c 'import json, sys; sys.exit(0 if json.load(sys.stdin).get("ok") is True else 1)'
}

check_path() {
  retry "访问检查失败：$1" path_ok "$1"
  printf '    OK %s\n' "$1"
}

check_path /
check_path /shared/module-header.css
check_path /topics/
check_path /ham/
check_path /chemistry/
check_path /chemistry/data/chemistry.json
check_path /chemistry/js/chemistry.js
check_path /physics/
check_path /physics/data/physics.json
check_path /physics/js/physics-core.js
check_path /physics/js/physics.js
check_path /word-puzzle/
check_path /word-puzzle/css/app.css
check_path /word-puzzle/img/icon.svg
check_path /word-puzzle/js/release-presets.js
check_path /word-puzzle/js/i18n.js
check_path /word-puzzle/js/i18n-lexica.js

retry "词境 API 健康检查失败或返回异常" health_ok
printf '    OK /word-puzzle/api/health\n'

cat <<EOF

整站部署完成：
  语林门户：http://$SERVER_NAME/
  每日话题：http://$SERVER_NAME/topics/
  无线电执照：http://$SERVER_NAME/ham/
  化学探秘：http://$SERVER_NAME/chemistry/
  物理探秘：http://$SERVER_NAME/physics/
  词境 Lexica：http://$SERVER_NAME/word-puzzle/

词境服务：systemctl status word-puzzle
EOF
