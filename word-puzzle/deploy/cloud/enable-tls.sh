#!/usr/bin/env bash
# 给云服务器的公网入口签 Let's Encrypt 证书并打开 HTTPS（备案通过、域名已经解析到本机之后运行）。
#
#   sudo env WP_DOMAIN=<域名> WP_ACME_EMAIL=<邮箱> bash word-puzzle/deploy/cloud/enable-tls.sh
#
# 用 HTTP-01（webroot）验证：要求 80 端口能从公网被访问到——腾讯云防火墙放行 80，且域名已备案（未备案的域名
# 在国内机房的 80/443 会被运营商拦截，验证会失败，这时请先等备案）。证书由 certbot 的定时器自动续期，
# 续期成功后重载 nginx。WP_ACME_EMAIL 不写就不留邮箱（收不到到期提醒，但自动续期照常）。
# 先用 WP_ACME_STAGING=1 试跑可以不占用 Let's Encrypt 的正式额度。
set -euo pipefail

CLOUD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOMAIN="${WP_DOMAIN:-}"
EMAIL="${WP_ACME_EMAIL:-}"
WEBROOT="${WP_ACME_WEBROOT:-/var/www/letsencrypt}"

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

[[ $(id -u) -eq 0 ]] || die "请用 sudo 运行"
[[ "$DOMAIN" =~ ^[A-Za-z0-9.-]+$ ]] || die "请用 WP_DOMAIN 指定域名"
[[ -z "$EMAIL" || "$EMAIL" =~ ^[^[:space:]@]+@[^[:space:]@]+$ ]] || die "WP_ACME_EMAIL 格式无效"

say "安装 certbot"
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq certbot >/dev/null

say "确认 80 端口上的验证目录能从本机访问到（先让 nginx 带上验证入口）"
WP_DOMAIN="$DOMAIN" bash "$CLOUD_DIR/render-nginx.sh"
install -d "$WEBROOT/.well-known/acme-challenge"
echo ok > "$WEBROOT/.well-known/acme-challenge/lexica-probe"
code="$(curl --noproxy '*' -s -o /dev/null -w '%{http_code}' --max-time 8 -H "Host: $DOMAIN" "http://127.0.0.1/.well-known/acme-challenge/lexica-probe" || true)"
rm -f "$WEBROOT/.well-known/acme-challenge/lexica-probe"
[[ "$code" == "200" ]] || die "本机访问验证目录返回 $code，应为 200：看 nginx -t 和 $WEBROOT 的权限"

say "申请证书"
args=(certonly --webroot -w "$WEBROOT" -d "$DOMAIN" --agree-tos --non-interactive)
if [[ -n "$EMAIL" ]]; then args+=(-m "$EMAIL"); else args+=(--register-unsafely-without-email); fi
if [[ "${WP_ACME_STAGING:-}" == "1" ]]; then args+=(--staging --cert-name "$DOMAIN"); echo "    （试跑：用测试环境签的证书不被浏览器信任）"; fi
certbot "${args[@]}" || die "申请失败：域名是否已解析到这台机器？80 端口是否放行？是否已备案？（日志：/var/log/letsencrypt/letsencrypt.log）"

say "续期成功后自动重载 nginx"
install -d /etc/letsencrypt/renewal-hooks/deploy
cat > /etc/letsencrypt/renewal-hooks/deploy/lexica-reload-nginx.sh <<'HOOK'
#!/bin/sh
systemctl reload nginx
HOOK
chmod 0755 /etc/letsencrypt/renewal-hooks/deploy/lexica-reload-nginx.sh
systemctl enable --now certbot.timer >/dev/null 2>&1 || true

say "打开 HTTPS 入口"
WP_DOMAIN="$DOMAIN" bash "$CLOUD_DIR/render-nginx.sh"

say "自检"
code="$(curl --noproxy '*' -sk -o /dev/null -w '%{http_code}' --max-time 10 --resolve "$DOMAIN:443:127.0.0.1" "https://$DOMAIN/word-puzzle/api/banks" || true)"
[[ "$code" == "401" ]] || die "https 入口访问 /api/banks 应返回 401（未登录被拒绝），实际 $code"
code="$(curl --noproxy '*' -s -o /dev/null -w '%{http_code}' --max-time 10 --resolve "$DOMAIN:80:127.0.0.1" "http://$DOMAIN/word-puzzle/" || true)"
[[ "$code" == "301" ]] || die "80 端口应跳转到 https（301），实际 $code"
echo "    OK https 可用；未登录访问接口被拒绝（401）；80 跳转到 443"
echo
echo "完成。证书到期前 certbot 会自动续期，检查： certbot renew --dry-run"
