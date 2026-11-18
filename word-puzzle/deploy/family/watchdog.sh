#!/usr/bin/env bash
# 词境学生版看门狗：每分钟由 systemd 定时器运行一次（容器里，root）。装好之后叫 /usr/local/sbin/lexica-watchdog。
#
# 做两件事，都只在出了问题时才动手：
#   1. 网站不正常（本机 nginx 入口的健康检查不通）：先看后端服务在不在，不在就启动、在但不应答就重启；nginx 没运行也启动。
#   2. 公网入口（Tailscale Funnel）：只有存在 /etc/lexica/funnel-keep 这个文件时才管——它表示「公网入口要常开」，
#      是你明确选的。Funnel 掉了（停电重启后常见）就等 Tailscale 连上，再重新 tailscale funnel --bg 一次。
#      想关掉公网入口：先 rm /etc/lexica/funnel-keep，再 tailscale funnel reset（否则一分钟后又被打开）。
# Funnel 永远只指向 nginx 的 @NGINX_PORT@，不会指向别处；看到别的目标只告警，不去改。
set -u

SERVICE="@SITE_NAME@"
NGINX_PORT="@NGINX_PORT@"
BACKEND_PORT="@PORT@"
KEEP_FILE="${LEXICA_FUNNEL_KEEP:-/etc/lexica/funnel-keep}"

say() { echo "lexica-watchdog: $*"; }
healthy() { curl --noproxy '*' -fsS --max-time 8 "http://127.0.0.1:$1/word-puzzle/api/health" >/dev/null 2>&1; }

# ---- 1. 网站本身 ----
if ! healthy "$NGINX_PORT"; then
  say "健康检查不通（nginx 入口 ${NGINX_PORT}）"
  if ! systemctl is-active --quiet "$SERVICE"; then
    say "后端服务没在运行，启动它"
    systemctl start "$SERVICE"
  elif ! healthy "$BACKEND_PORT"; then
    say "后端服务在运行但不应答，重启它"
    systemctl restart "$SERVICE"
  fi
  if ! systemctl is-active --quiet nginx; then
    say "nginx 没在运行，启动它"
    systemctl start nginx
  fi
fi

# ---- 2. 公网入口 ----
[[ -e "$KEEP_FILE" ]] || exit 0
command -v tailscale >/dev/null 2>&1 || { say "要求常开公网入口，但这里没有 tailscale 命令"; exit 0; }

status="$(timeout 20 tailscale funnel status 2>&1 || true)"
if grep -q "Funnel on" <<<"$status" && grep -q "127.0.0.1:$NGINX_PORT" <<<"$status"; then
  # 正常。顺便提醒：如果还指向了别的端口，不去动它，只记一笔
  if grep -E "proxy|http" <<<"$status" | grep -v "127.0.0.1:$NGINX_PORT" | grep -q "127.0.0.1\|localhost"; then
    say "注意：Funnel 里除了 $NGINX_PORT 还有别的目标，请检查 tailscale funnel status"
  fi
  exit 0
fi

say "公网入口（Funnel）没开，准备重新打开"
systemctl is-active --quiet tailscaled || { say "tailscaled 没在运行，启动它"; systemctl start tailscaled; }
connected=0
for _ in 1 2 3 4 5 6 7 8 9 10 11 12; do         # 最多等 2 分钟：停电后路由器和宽带常常比服务器慢
  if timeout 15 tailscale status --json 2>/dev/null | grep -q '"BackendState": *"Running"'; then connected=1; break; fi
  sleep 10
done
if [[ "$connected" != 1 ]]; then
  say "Tailscale 还没连上（网络没恢复，或者需要重新登录），下一分钟再试"
  exit 0
fi
if timeout 60 tailscale funnel --bg "$NGINX_PORT" >/dev/null 2>&1; then
  say "已重新打开 Funnel → $NGINX_PORT"
else
  say "重新打开 Funnel 失败：手动运行 tailscale funnel --bg $NGINX_PORT 看提示（可能要在 Tailscale 管理后台批准 Funnel）"
fi
exit 0
