#!/usr/bin/env bash
# 在生产服务器上 git pull 后运行：sudo bash deploy-all-20261128_214052.sh
#
# 这个仓库是公开的：服务器地址、内网地址、公网网址这类私有信息一律不写进仓库，
# 放在仓库根目录下不进 git 的 deploy.local.env（见 deploy.local.env.example），也可以用同名环境变量覆盖：
#   LINGUA_SERVER_NAME  这台机器的地址（必填）
#   LEXICA_UPSTREAM     词境后端的 主机:端口（必填；写 none = 用本机后端 127.0.0.1:8765）
#   LEXICA_CTID         学生版容器的编号（选填）。写了，这个脚本就连容器里的词境一起更新
#                       （把仓库里的整站——词境、主页、五个模块——推进容器并重跑 family/install.sh）；不写就只更新宿主机。
#   LEXICA_PUBLIC_URL   学生版的对外网址（写了 LEXICA_CTID 就必填），例如 Funnel 网址，不带斜杠
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$REPO_DIR/deploy.local.env" ]]; then
  # 只认 KEY=VALUE 行，已经在环境里设过的变量不被覆盖
  # 最后一行没有换行符也要读到（|| [[ -n $key ]]）；Windows 换行（\r）去掉
  while IFS='=' read -r key value || [[ -n "$key" ]]; do
    value="${value%$'\r'}"
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
  word-puzzle/tools/recalculate_scores.py \
  word-puzzle/tools/asr_worker.py \
  word-puzzle/server/items.py \
  word-puzzle/server/scoring.py \
  word-puzzle/server/recordings.py \
  word-puzzle/server/asr.py \
  word-puzzle/server/awards.py \
  word-puzzle/server/templates.py \
  word-puzzle/server/xlsx.py \
  word-puzzle/web/me.html \
  word-puzzle/web/js/awards-ui.js \
  word-puzzle/web/js/page-honors.js \
  word-puzzle/web/spell.html \
  word-puzzle/web/order.html \
  word-puzzle/web/verb.html \
  word-puzzle/web/js/verb-ui.js \
  word-puzzle/web/js/game-adapter-online.js \
  word-puzzle/web/js/item-core.js \
  word-puzzle/web/js/order-ui.js \
  word-puzzle/web/js/spell-ui.js \
  hub/deploy/install.sh \
  hub/deploy/lingua-grove.conf \
  hub/deploy/site-proxy.conf \
  hub/privacy.html \
  hub/shared/site-footer.js \
  hub/shared/module-progress.js \
  topic-app/topic-app/index.html \
  ham-exam/index.html \
  chemistry/index.html \
  chemistry/js/chemistry.js \
  chemistry/js/chemistry-core.js \
  chemistry/data/chemistry.json \
  physics/index.html \
  physics/js/physics.js \
  physics/data/physics.json \
  nvidia-exam/index.html \
  nvidia-exam/css/style.css \
  nvidia-exam/js/app.js \
  nvidia-exam/js/store.js \
  nvidia-exam/data/bank.js \
  nvidia-exam/data/bank.json \
  nvidia-exam/data/guides.js \
  nvidia-exam/data/guides.json \
  nvidia-exam/docs/采集说明.md \
  nvidia-exam/docs/guides/NCA-AIIO.md \
  nvidia-exam/docs/guides/NCP-OUSD.md \
  backends/index.html \
  backends/js/backends.js \
  backends/css/backends.css; do
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

# 容器：整站（主页、四个模块、词境学生版和公开版）都在容器里，宿主机只做转发。宿主机的 install.sh 碰不到容器，
# 所以在这里把代码推进去，再在容器里跑 family/install.sh。数据库在容器外的目录里，不会被覆盖。
if [[ -n "$LEXICA_CTID" ]]; then
  say "更新学生版容器 $LEXICA_CTID 里的词境（代码来自当前仓库）"
  SRC_TGZ="$(mktemp /tmp/lexica-src.XXXXXX.tgz)"
  trap 'rm -f "$SRC_TGZ"' EXIT
  # 整站：词境 + 主页 + 五个模块（容器的 nginx 在根路径提供主页）；测试、原始资料、工具脚本不进网站
  (cd "$REPO_DIR" && COPYFILE_DISABLE=1 tar czf "$SRC_TGZ" \
    --exclude='word-puzzle/var' --exclude='__pycache__' --exclude='.DS_Store' --exclude='*/tests' \
    --exclude='ham-exam/raw-files' --exclude='ham-exam/tools' \
    --exclude='nvidia-exam/raw-files' --exclude='nvidia-exam/tools' \
    word-puzzle hub topic-app/topic-app ham-exam chemistry physics nvidia-exam backends)
  pct push "$LEXICA_CTID" "$SRC_TGZ" /root/lexica-src.tgz
  # 只替换无 git 的代码副本；旧副本保留，解包失败时不动当前目录。
  pct exec "$LEXICA_CTID" -- bash -s <<'CONTAINER_SWAP'
set -euo pipefail
[[ ! -L /root/language-learning && ! -e /root/language-learning/.git ]] || {
  echo "拒绝替换符号链接或 git 工作树" >&2
  exit 1
}
stage="$(mktemp -d /root/lexica-release.XXXXXX)"
tar xzf /root/lexica-src.tgz -C "$stage"
if [[ -d /root/language-learning ]]; then
  mv /root/language-learning "$stage.previous"
  echo "旧代码副本保留在 $stage.previous"
fi
mv "$stage" /root/language-learning
rm -f /root/lexica-src.tgz
CONTAINER_SWAP
  # 访问记录里要跳过的前置代理 = 宿主机：WP_TRUSTED_PROXIES 只收 IP，LINGUA_SERVER_NAME 是域名时先解析成 IPv4
  TRUSTED_PROXY="$SERVER_NAME"
  if [[ ! "$TRUSTED_PROXY" =~ ^[0-9.]+$ ]]; then
    TRUSTED_PROXY="$(getent ahostsv4 "$SERVER_NAME" | awk 'NR==1{print $1}')"
    [[ -n "$TRUSTED_PROXY" ]] || die "解析不了 $SERVER_NAME 的 IPv4 地址（访问记录要用它跳过宿主机这一层代理）"
  fi
  pct exec "$LEXICA_CTID" -- env DEBIAN_FRONTEND=noninteractive \
    WP_PUBLIC_URL="$LEXICA_PUBLIC_URL" WP_LAN_ADDR="${LEXICA_UPSTREAM%%:*}" \
    WP_TRUSTED_PROXIES="$TRUSTED_PROXY" WP_BACKUP_DIR=/backup \
    bash -lc "cd /root/language-learning && bash word-puzzle/deploy/family/install.sh"
  # 核对：容器真正提供出去的页面要和仓库里的一字不差，否则就是没更新上
  want="$(sha256sum "$REPO_DIR/word-puzzle/web/visits.html" | cut -d' ' -f1)"
  have_ok() {
    [[ "$(curl --noproxy '*' -fsS --max-time 15 "http://$LEXICA_UPSTREAM/word-puzzle/visits.html" | sha256sum | cut -d' ' -f1)" == "$want" ]]
  }
  for _ in 1 2 3 4 5 6 7 8 9 10; do have_ok && break; sleep 1; done
  if have_ok; then
    printf '    OK 容器里的页面与仓库一致\n'
    # 先把正文取下来再 grep：curl | grep -q 里 grep 找到就退出，curl 会收到 SIGPIPE（退出码 23），
    # 配合 set -o pipefail 会把「找到了」误判成「不是主页」。
    home_body="$(curl --noproxy '*' -fsS --max-time 15 "http://$LEXICA_UPSTREAM/" 2>/dev/null || true)"
    if [[ "$home_body" == *词境* ]]; then
      printf '    OK 容器的根路径是词境主页\n'
    else
      printf '\033[1;33m[!]\033[0m 容器的根路径不是词境主页，请自己核对\n' >&2
    fi
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

say "部署主页（词境）、每日话题、无线电执照、化学探秘、物理探秘、NVIDIA 认证模拟考试和统一 nginx 入口"
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
check_path /nvidia-exam/
check_path /nvidia-exam/data/bank.json
check_path /nvidia-exam/data/bank.js
check_path /nvidia-exam/data/guides.js
check_path /nvidia-exam/docs/guides/NCA-AIIO.md
check_path /nvidia-exam/js/app.js
check_path /nvidia-exam/css/style.css
check_path /backends/
check_path /backends/js/backends.js
check_path /backends/css/backends.css
check_path /word-puzzle/
check_path /word-puzzle/css/app.css
check_path /word-puzzle/spell.html
check_path /word-puzzle/me.html
check_path /word-puzzle/js/awards-ui.js
check_path /word-puzzle/order.html
check_path /word-puzzle/verb.html
check_path /word-puzzle/js/item-core.js
check_path /word-puzzle/js/verb-ui.js
check_path /word-puzzle/js/game-adapter-online.js
check_path /word-puzzle/js/order-ui.js
check_path /word-puzzle/js/spell-ui.js
check_path /word-puzzle/img/icon.svg
check_path /word-puzzle/js/release-presets.js
check_path /word-puzzle/js/i18n.js
check_path /word-puzzle/js/i18n-lexica.js
check_path /word-puzzle/leaderboard.html
check_path /word-puzzle/css/leaderboard.css
check_path /word-puzzle/js/page-leaderboard.js
if [[ -n "$LEXICA_CTID" ]]; then
  check_path /words/
  check_path /words/api/banks
fi

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
  NVIDIA 认证模拟考试：http://$SERVER_NAME/nvidia-exam/
  总后台：http://$SERVER_NAME/backends/   （要老师账号，不放在主页上）
  词境学生版：http://$SERVER_NAME/word-puzzle/   （要登录，不放在主页上）
  动词猎手：http://$SERVER_NAME/word-puzzle/verb.html   （要登录）
  积分规则：四种玩法已启用新版计分；历史重算须另行备份并显式执行，不随安装重复运行。

$([[ -n "$LEXICA_CTID" ]] && echo "整站在容器 $LEXICA_CTID 里，已经更新（服务：pct exec $LEXICA_CTID -- systemctl status word-puzzle-family）；浏览器 Ctrl+Shift+R 强刷。" || echo "没有写 LEXICA_CTID：只更新了这台机器（词境服务：systemctl status word-puzzle），容器没有更新。")
EOF
