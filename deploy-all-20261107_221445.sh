#!/usr/bin/env bash
# 把仓库拷到服务器后运行（服务器上不 git pull）：sudo bash deploy-all-20261107_221445.sh
# 可通过 LINGUA_SERVER_NAME 覆盖默认的生产服务器地址。
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_NAME="${LINGUA_SERVER_NAME:-10.1.1.93}"
WP_PORT=8765

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

[[ "$(id -u)" -eq 0 ]] || die "请使用 sudo 运行：sudo bash $0"
[[ "$SERVER_NAME" =~ ^[A-Za-z0-9.-]+$ ]] || die "LINGUA_SERVER_NAME 格式无效"
command -v curl >/dev/null 2>&1 || die "缺少 curl，请先安装 curl"

for path in \
  word-puzzle/deploy/install.sh \
  hub/deploy/install.sh \
  hub/deploy/lingua-grove.conf \
  topic-app/topic-app/index.html \
  ham-exam/index.html \
  chemistry/index.html \
  chemistry/data/chemistry.json; do
  [[ -f "$REPO_DIR/$path" ]] || die "仓库文件缺失：$path；请确认仓库已完整拷到服务器"
done

say "部署词境后端（保留现有数据库）"
WP_PORT="$WP_PORT" \
SITE_NAME=word-puzzle \
WP_SERVER_NAME="$SERVER_NAME" \
WP_SKIP_NGINX=1 \
  bash "$REPO_DIR/word-puzzle/deploy/install.sh"

say "部署语林门户、每日话题、无线电执照、化学探秘和统一 nginx 入口"
LINGUA_SERVER_NAME="$SERVER_NAME" bash "$REPO_DIR/hub/deploy/install.sh"

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
check_path /word-puzzle/
check_path /word-puzzle/css/app.css

retry "词境 API 健康检查失败或返回异常" health_ok
printf '    OK /word-puzzle/api/health\n'

cat <<EOF

整站部署完成：
  语林门户：http://$SERVER_NAME/
  每日话题：http://$SERVER_NAME/topics/
  无线电执照：http://$SERVER_NAME/ham/
  化学探秘：http://$SERVER_NAME/chemistry/
  词境 Lexica：http://$SERVER_NAME/word-puzzle/

词境服务：systemctl status word-puzzle
EOF
