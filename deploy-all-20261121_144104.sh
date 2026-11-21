#!/usr/bin/env bash
# 在生产服务器上 git pull 后运行：sudo bash deploy-all-20261121_144104.sh
#
# 这个仓库是公开的：服务器地址、内网地址、公网网址这类私有信息一律不写进仓库，
# 放在仓库根目录下不进 git 的 deploy.local.env（见 deploy.local.env.example），也可以用同名环境变量覆盖：
#   LINGUA_SERVER_NAME  这台机器的地址（必填）
#   LEXICA_UPSTREAM     词境后端的 主机:端口（必填；写 none = 用本机后端 127.0.0.1:8765）
#   LEXICA_CTID         学生版容器的编号（选填）。写了，这个脚本就连容器里的词境一起更新
#                       （把仓库里的整站——词境、主页、四个模块——推进容器并重跑 family/install.sh）；不写就只更新宿主机。
#   LEXICA_PUBLIC_URL   学生版的对外网址（写了 LEXICA_CTID 就必填），例如 Funnel 网址，不带斜杠
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$REPO_DIR/deploy.local.env" ]]; then
  # 只认 KEY=VALUE 行，已经在环境里设过的变量不被覆盖
  while IFS='=' read -r key value; do
    [[ "$key" =~ ^(LINGUA_SERVER_NAME|LEXICA_UPSTREAM|LEXICA_CTID|LEXICA_PUBLIC_URL)$ ]] || continue
    [[ -n "${!key:-}" ]] || export "$key=${value//\"/}"
  done < "$REPO_DIR/deploy.local.env"
fi
SERVER_NAME="${LINGUA_SERVER_NAME:-}"
WP_PORT=8765
LEXICA_UPSTREAM="${LEXICA_UPSTREAM:-}"
LEXICA_CTID="${LEXICA_CTID:-}"
LEXICA_PUBLIC_URL="${LEXICA_PUBLIC_URL:-}"

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

[[ "$(id -u)" -eq 0 ]] || die "请使用 sudo 运行：sudo bash $0"
[[ -n "$SERVER_NAME" ]] || die "没有 LINGUA_SERVER_NAME：请在 deploy.local.env 里写上这台机器的地址（见 deploy.local.env.example）"
[[ "$SERVER_NAME" =~ ^[A-Za-z0-9.-]+$ ]] || die "LINGUA_SERVER_NAME 格式无效"
[[ -n "$LEXICA_UPSTREAM" ]] || die "没有 LEXICA_UPSTREAM：写 主机:端口，或写 none 使用本机后端（见 deploy.local.env.example）"
[[ "$LEXICA_UPSTREAM" != "none" ]] || LEXICA_UPSTREAM=""
if [[ -n "$LEXICA_CTID" ]]; then
  [[ "$LEXICA_CTID" =~ ^[0-9]+$ ]] || die "LEXICA_CTID 应该是容器编号（数字）"
  [[ "$LEXICA_PUBLIC_URL" =~ ^https?://[A-Za-z0-9.:-]+$ ]] || die "写了 LEXICA_CTID 就要写 LEXICA_PUBLIC_URL（形如 https://主机名，不带斜杠）"
  [[ -n "$LEXICA_UPSTREAM" ]] || die "更新学生版容器需要 LEXICA_UPSTREAM（容器的 内网IP:8082）"
  command -v pct >/dev/null 2>&1 || die "写了 LEXICA_CTID 但找不到 pct：要在 PVE 宿主机上运行"
fi
command -v curl >/dev/null 2>&1 || die "缺少 curl，请先安装 curl"

for path in \
  word-puzzle/deploy/install.sh \
  word-puzzle/deploy/family/install.sh \
  word-puzzle/deploy/cloud/install.sh \
  word-puzzle/deploy/cloud/render-nginx.sh \
  word-puzzle/deploy/cloud/enable-tls.sh \
  word-puzzle/deploy/cloud/harden.sh \
  word-puzzle/deploy/cloud/migrate-data.sh \
  word-puzzle/deploy/cloud/dbcheck.py \
  word-puzzle/deploy/cloud/sync-from-home.sh \
  word-puzzle/web/img/icon.svg \
  word-puzzle/web/js/release-presets.js \
  word-puzzle/web/js/i18n.js \
  word-puzzle/web/js/i18n-lexica.js \
  word-puzzle/server/accesslog.py \
  word-puzzle/server/tenancy.py \
  word-puzzle/server/leaderboard.py \
  word-puzzle/web/leaderboard.html \
  word-puzzle/web/js/page-leaderboard.js \
  word-puzzle/web/css/leaderboard.css \
  word-puzzle/web/tenants.html \
  word-puzzle/web/js/page-tenants.js \
  word-puzzle/web/js/tracker.js \
  word-puzzle/web/visits.html \
  word-puzzle/web/js/page-visits.js \
  word-puzzle/tools/build_public_web.py \
  word-puzzle/tools/import_items.py \
  word-puzzle/tools/asr_worker.py \
  word-puzzle/server/items.py \
  word-puzzle/server/recordings.py \
  word-puzzle/server/asr.py \
  word-puzzle/web/spell.html \
  word-puzzle/web/order.html \
  hub/deploy/install.sh \
  hub/deploy/lingua-grove.conf \
  hub/deploy/site-proxy.conf \
  hub/privacy.html \
  hub/shared/site-footer.js \
  topic-app/topic-app/index.html \
  ham-exam/index.html \
  chemistry/index.html \
  chemistry/data/chemistry.json \
  physics/index.html \
  physics/data/physics.json; do
  [[ -f "$REPO_DIR/$path" ]] || die "仓库文件缺失：$path；请确认 git pull 已完成"
done

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

# 学生版容器（家庭版和学生版共用的那个后端）：宿主机的 install.sh 碰不到它，所以在这里一并推进去。
# 数据库在容器外的目录里，family/install.sh 不会覆盖它。
if [[ -n "$LEXICA_CTID" ]]; then
  say "更新学生版容器 $LEXICA_CTID 里的词境（代码来自当前仓库）"
  SRC_TGZ="$(mktemp /tmp/lexica-src.XXXXXX.tgz)"
  trap 'rm -f "$SRC_TGZ"' EXIT
  # 整站：词境 + 主页 + 四个模块（容器的 nginx 在根路径提供主页）；测试、原始资料、工具脚本不进网站
  (cd "$REPO_DIR" && COPYFILE_DISABLE=1 tar czf "$SRC_TGZ" \
    --exclude='word-puzzle/var' --exclude='__pycache__' --exclude='.DS_Store' --exclude='*/tests' \
    --exclude='ham-exam/raw-files' --exclude='ham-exam/tools' \
    word-puzzle hub topic-app/topic-app ham-exam chemistry physics)
  pct push "$LEXICA_CTID" "$SRC_TGZ" /root/lexica-src.tgz
  pct exec "$LEXICA_CTID" -- bash -lc "mkdir -p /root/language-learning && tar xzf /root/lexica-src.tgz -C /root/language-learning && rm -f /root/lexica-src.tgz"
  pct exec "$LEXICA_CTID" -- env DEBIAN_FRONTEND=noninteractive \
    WP_PUBLIC_URL="$LEXICA_PUBLIC_URL" WP_LAN_ADDR="${LEXICA_UPSTREAM%%:*}" \
    WP_TRUSTED_PROXIES="$SERVER_NAME" WP_BACKUP_DIR=/backup \
    bash -lc "cd /root/language-learning && bash word-puzzle/deploy/family/install.sh"
  # 核对：容器真正提供出去的页面要和仓库里的一字不差，否则就是没更新上
  want="$(sha256sum "$REPO_DIR/word-puzzle/web/visits.html" | cut -d' ' -f1)"
  have_ok() {
    [[ "$(curl --noproxy '*' -fsS --max-time 15 "http://$LEXICA_UPSTREAM/word-puzzle/visits.html" | sha256sum | cut -d' ' -f1)" == "$want" ]]
  }
  for _ in 1 2 3 4 5 6 7 8 9 10; do have_ok && break; sleep 1; done
  if have_ok; then
    printf '    OK 容器里的页面与仓库一致\n'
    curl --noproxy '*' -fsS --max-time 15 "http://$LEXICA_UPSTREAM/" | grep -q '词境' \
      && printf '    OK 容器的根路径是词境主页\n' \
      || printf '\033[1;33m[!]\033[0m 容器的根路径不是词境主页，请自己核对\n' >&2
  else
    printf '\033[1;33m[!]\033[0m 容器里的 visits.html 和仓库不一致：学生版可能没有更新成功，请自己核对（不中断后面的部署）\n' >&2
  fi
fi

say "部署词境后端（保留现有数据库）"
WP_PORT="$WP_PORT" \
WP_REMOTE_BACKEND="$([[ -n "$LEXICA_UPSTREAM" ]] && echo 1 || echo 0)" \
SITE_NAME=word-puzzle \
WP_SERVER_NAME="$SERVER_NAME" \
WP_SKIP_NGINX=1 \
  bash "$REPO_DIR/word-puzzle/deploy/install.sh"

say "部署主页（词境）、每日话题、无线电执照、化学探秘、物理探秘和统一 nginx 入口"
LINGUA_SERVER_NAME="$SERVER_NAME" LEXICA_UPSTREAM="$LEXICA_UPSTREAM" bash "$REPO_DIR/hub/deploy/install.sh"

say "执行整站冒烟检查"
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
check_path /privacy.html
check_path /shared/module-header.css
check_path /shared/site-footer.js
check_path /shared/wechat.js
check_path /topics/
check_path /ham/
check_path /chemistry/
check_path /chemistry/data/chemistry.json
check_path /chemistry/js/chemistry.js
check_path /physics/
check_path /physics/data/physics.json
check_path /physics/js/physics-core.js
check_path /physics/js/physics.js
check_path /words/
check_path /words/api/banks
check_path /word-puzzle/
check_path /word-puzzle/css/app.css
check_path /word-puzzle/spell.html
check_path /word-puzzle/order.html
check_path /word-puzzle/js/item-core.js
check_path /word-puzzle/img/icon.svg
check_path /word-puzzle/js/release-presets.js
check_path /word-puzzle/js/i18n.js
check_path /word-puzzle/js/i18n-lexica.js
check_path /word-puzzle/leaderboard.html
check_path /word-puzzle/css/leaderboard.css
check_path /word-puzzle/js/page-leaderboard.js

retry "词境 API 健康检查失败或返回异常" health_ok
printf '    OK /word-puzzle/api/health\n'

cat <<EOF

整站部署完成：
  词境主页：http://$SERVER_NAME/
  隐私说明：http://$SERVER_NAME/privacy.html
  词境公开版：http://$SERVER_NAME/words/   （不用登录，只有初中、高中）
  每日话题：http://$SERVER_NAME/topics/
  无线电执照：http://$SERVER_NAME/ham/
  化学探秘：http://$SERVER_NAME/chemistry/
  物理探秘：http://$SERVER_NAME/physics/
  词境学生版：http://$SERVER_NAME/word-puzzle/   （要登录，不放在主页上）

词境服务：systemctl status word-puzzle
$([[ -n "$LEXICA_CTID" ]] && echo "学生版容器 $LEXICA_CTID 也已更新（pct exec $LEXICA_CTID -- systemctl status word-puzzle-family）；浏览器 Ctrl+Shift+R 强刷。" || echo "没有写 LEXICA_CTID：学生版容器没有更新，要另外推送。")
EOF
