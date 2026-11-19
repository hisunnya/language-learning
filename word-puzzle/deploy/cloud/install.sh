#!/usr/bin/env bash
# 词境 学生版 · 云服务器（生产）一键部署：一台独立的 Debian 服务器，nginx + systemd + Python 标准库。
#
#   sudo env WP_DOMAIN=<域名> bash word-puzzle/deploy/cloud/install.sh
#
# 和 family/install.sh 的关系：后端、数据库、systemd 单元、备份、看门狗、管理命令都复用它（WP_CLOUD=1 只是让它
# 不再提 Tailscale Funnel）；这里只补云服务器才需要的部分：
#   - 公网入口：nginx 监听 80 / 443，只认 WP_DOMAIN；用 IP 或别的域名访问一律断开（444）
#   - 没有证书之前，80 端口只放行证书验证，网站本身只能从本机（SSH 隧道）访问：登录用的 Cookie 带 Secure，
#     明文 http 暴露在公网既登不上，账号密码也会明文走公网
#   - 证书和 SSH 加固是另外两步（enable-tls.sh、harden.sh），要你确认后各跑一次
#
# 域名、IP 这类私有值不写进仓库：WP_DOMAIN 只在这条命令里给。
set -euo pipefail

CLOUD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(cd "$CLOUD_DIR/../.." && pwd)"
DOMAIN="${WP_DOMAIN:-}"
BACKUP_DIR="${WP_BACKUP_DIR:-/var/backups/lexica}"

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

[[ $(id -u) -eq 0 ]] || die "请用 sudo 运行"
[[ -n "$DOMAIN" ]] || die "请用 WP_DOMAIN 指定对外的域名（不含 https://），写成 WP_DOMAIN=<域名>"
[[ "$DOMAIN" =~ ^[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?(\.[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?)+$ ]] || die "WP_DOMAIN 格式无效：$DOMAIN"
[[ -f "$SRC_DIR/deploy/family/install.sh" ]] || die "找不到 deploy/family/install.sh：请在完整的仓库里运行"

say "安装词境后端、数据库、备份、看门狗（复用 family/install.sh）"
WP_CLOUD=1 \
WP_PUBLIC_URL="https://$DOMAIN" \
WP_BACKUP_DIR="$BACKUP_DIR" \
  bash "$SRC_DIR/deploy/family/install.sh"

say "安装公网 nginx 入口（80 / 443，只认 ${DOMAIN}）"
WP_DOMAIN="$DOMAIN" bash "$CLOUD_DIR/render-nginx.sh"

cat <<EOF2

云服务器部署完成。网站现在只能从本机访问（还没有证书）：
  在你的电脑上： ssh -L 8081:127.0.0.1:8081 <服务器别名>
  浏览器（用 Chrome）打开： http://127.0.0.1:8081/word-puzzle/

下一步（见 deploy/cloud/部署说明.md）：
  1) sudo bash $CLOUD_DIR/harden.sh          SSH 只许密钥登录 + fail2ban（先确认密钥登录没问题）
  2) 备案通过、域名解析到本机之后： sudo env WP_DOMAIN=$DOMAIN WP_ACME_EMAIL=<邮箱> bash $CLOUD_DIR/enable-tls.sh
EOF2
