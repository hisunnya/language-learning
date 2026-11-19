#!/usr/bin/env bash
# 生成云服务器的公网 nginx 配置（由 install.sh 和 enable-tls.sh 调用，可以重复运行）。
#
# 站点内容（location、限速、请求体上限、隐藏文件拦截）全部取自已经装好的 family 配置，只换监听和头，
# 这样两处不会各改各的。证书文件存在 → 生成 HTTPS 入口；不存在 → 80 端口只放行证书验证。
#
#   WP_DOMAIN=<域名>  必填
#   WP_FAMILY_INSTALL_DIR（默认 /srv/word-puzzle-family）、WP_FAMILY_PORT（默认 8766）
set -euo pipefail

DOMAIN="${WP_DOMAIN:-}"
INSTALL_DIR="${WP_FAMILY_INSTALL_DIR:-/srv/word-puzzle-family}"
PORT="${WP_FAMILY_PORT:-8766}"
WEBROOT="${WP_ACME_WEBROOT:-/var/www/letsencrypt}"
LIVE_DIR="${WP_CERT_DIR:-/etc/letsencrypt/live}/$DOMAIN"
CONF_DIR="${WP_NGINX_CONF_DIR:-/etc/nginx/conf.d}"
ETC_DIR="${WP_NGINX_ETC_DIR:-/etc/nginx}"
FAMILY_CONF="$INSTALL_DIR/deploy/family/nginx/word-puzzle-family.conf"
FAMILY_PROXY="$INSTALL_DIR/deploy/family/nginx/proxy.inc"
CLOUD_PROXY="$ETC_DIR/lexica-cloud-proxy.inc"
CONF_FILE="$CONF_DIR/lexica-cloud.conf"

die() { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

[[ "$DOMAIN" =~ ^[A-Za-z0-9.-]+$ ]] || die "WP_DOMAIN 缺失或格式无效"
[[ -f "$FAMILY_CONF" && -f "$FAMILY_PROXY" ]] || die "找不到 family 的 nginx 配置：先运行 deploy/cloud/install.sh"

install -d "$WEBROOT" "$CONF_DIR"

# 转给后端的头：直接面对公网，客户端地址就是 nginx 看到的 ${remote_addr}，不信任客户端自己带的任何转发头。
# （后端取 X-Wp-Edge-Xff 里最后一个地址当访客 IP，所以这里只放 nginx 亲眼看到的地址。）
sed -e 's|^proxy_set_header X-Wp-Edge-Xff .*|proxy_set_header X-Wp-Edge-Xff $remote_addr;|' \
    -e 's|^proxy_set_header X-Wp-Edge-Real-Ip .*|proxy_set_header X-Wp-Edge-Real-Ip $remote_addr;|' \
    -e 's|^proxy_set_header X-Wp-Edge-Forwarded .*|proxy_set_header X-Wp-Edge-Forwarded "";|' \
    -e 's|^proxy_set_header X-Wp-Edge-Tailscale .*|proxy_set_header X-Wp-Edge-Tailscale "";|' \
    "$FAMILY_PROXY" > "$CLOUD_PROXY"
chmod 0644 "$CLOUD_PROXY"

have_cert=0
[[ -s "$LIVE_DIR/fullchain.pem" && -s "$LIVE_DIR/privkey.pem" ]] && have_cert=1

TMP="$CONF_FILE.tmp.$$"
trap 'rm -f "$TMP"' EXIT
{
  echo "# 由 deploy/cloud/render-nginx.sh 生成，不要手改（重新运行会覆盖）。"
  echo "# 站点内容来自 family/nginx/word-puzzle-family.conf；这里只管监听、域名和证书。"
  echo
  echo "# 80：其他域名、IP 直接访问一律断开。"
  echo "server {"
  echo "    listen 80 default_server;"
  echo "    server_name _;"
  echo "    return 444;"
  echo "}"
  echo
  echo "# 80：证书验证；有证书就跳转到 https，没有证书就什么也不给（网站不走明文）。"
  echo "server {"
  echo "    listen 80;"
  echo "    server_name $DOMAIN;"
  echo "    location ^~ /.well-known/acme-challenge/ {"
  echo "        root $WEBROOT;"
  echo "        default_type text/plain;"
  echo "    }"
  echo "    location / {"
  if [[ "$have_cert" -eq 1 ]]; then
    echo "        return 301 https://$DOMAIN\$request_uri;"
  else
    echo "        return 404;"
  fi
  echo "    }"
  echo "}"
  if [[ "$have_cert" -eq 1 ]]; then
    echo
    echo "# 443：域名不对（包括直接用 IP）握手就被拒绝。"
    echo "server {"
    echo "    listen 443 ssl default_server;"
    echo "    ssl_reject_handshake on;"
    echo "}"
    echo
    # 监听行换成 TLS 监听 + 证书设置（用 awk 读环境变量：sed 的替换串里写换行，GNU 和 BSD 的写法不一样）
    SSL_BLOCK="    listen 443 ssl;
    http2 on;
    ssl_certificate $LIVE_DIR/fullchain.pem;
    ssl_certificate_key $LIVE_DIR/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_session_cache shared:lexica_ssl:10m;
    ssl_session_timeout 1d;"
    export SSL_BLOCK
    sed -n '/^server {/,$p' "$FAMILY_CONF" \
      | awk '/^    listen 127\.0\.0\.1:@NGINX_PORT@;/ { print ENVIRON["SSL_BLOCK"]; next } { print }' \
      | sed -e "s|^    server_name _;|    server_name $DOMAIN;|" \
            -e "s|@PROXY_INC@|$CLOUD_PROXY|g" \
            -e "s|@INSTALL_DIR@|$INSTALL_DIR|g" \
            -e "s|@PORT@|$PORT|g" \
            -e "s|word-puzzle-family\\.|word-puzzle-cloud.|g"
  fi
} > "$TMP"

# Debian 自带的默认站点也监听 80 default_server，会和上面冲突。
rm -f "$ETC_DIR/sites-enabled/default"

had_old=0
if [[ -e "$CONF_FILE" ]]; then cp -a "$CONF_FILE" "$CONF_FILE.bak"; had_old=1; fi
mv "$TMP" "$CONF_FILE"
if ! nginx -t; then
  rm -f "$CONF_FILE"
  [[ "$had_old" -eq 0 ]] || mv "$CONF_FILE.bak" "$CONF_FILE"
  die "nginx 配置检查失败；已恢复原样"
fi
systemctl reload nginx
if [[ "$have_cert" -eq 1 ]]; then
  echo "    公网入口：https://$DOMAIN/（80 跳转到 443）"
else
  echo "    还没有证书：80 只放行证书验证，网站只能从本机访问（SSH 隧道）"
fi
