#!/usr/bin/env bash
# 检查「Tailscale 里这台机器的网址」和「我们记录/配置的对外网址」是不是同一个。
#
#   bash check-url.sh                      # 用安装时记下的网址（/var/lib/word-puzzle-family/public-url）
#   bash check-url.sh https://lexica.tailXXXX.ts.net
#
# 什么时候跑：安装之后、重建容器之后、改过机器名或 tailnet 名之后、发网址给学生之前。
# 网址变了，学生手里的链接和二维码就全废了，所以越早发现越好。
#
# 退出码：0 一致；1 不一致；2 查不到（没装 Tailscale、没登录、没开 MagicDNS 等）。
set -uo pipefail

RECORD="${WP_FAMILY_PUBLIC_URL_FILE:-/var/lib/word-puzzle-family/public-url}"
expected="${1:-${WP_PUBLIC_URL:-}}"
if [[ -z "$expected" && -r "$RECORD" ]]; then expected="$(head -n1 "$RECORD")"; fi
if [[ -z "$expected" ]]; then
  echo "没有可以比对的网址：请把它作为参数给出，例如 bash check-url.sh https://lexica.tailXXXX.ts.net" >&2
  echo "（安装时记下的网址在 $RECORD，需要用 root 运行才读得到）" >&2
  exit 2
fi

host_of() { # https://Host.Example.:8443/x  ->  host.example
  local h="${1#*://}"; h="${h%%/*}"; h="${h%%:*}"; h="${h%.}"
  printf '%s' "$h" | tr 'A-Z' 'a-z'
}

if ! command -v tailscale >/dev/null 2>&1; then
  echo "这台机器上没有 tailscale 命令（要在装了 Tailscale 的容器里运行）" >&2
  exit 2
fi
status="$(tailscale status --json 2>/dev/null)" || { echo "tailscale status 失败：Tailscale 没在运行？" >&2; exit 2; }
actual="$(python3 -c '
import json, sys
try:
    self_node = json.load(sys.stdin).get("Self") or {}
except ValueError:
    self_node = {}
print((self_node.get("DNSName") or "").rstrip("."))
' <<<"$status")"
if [[ -z "$actual" ]]; then
  echo "查不到本机的 Tailscale 域名：还没登录，或者管理后台没开 MagicDNS？" >&2
  exit 2
fi

want="$(host_of "$expected")"
have="$(host_of "$actual")"
if [[ "$want" == "$have" ]]; then
  echo "OK 网址一致：https://$have"
  exit 0
fi

echo "[x] 网址变了！" >&2
echo "    记录的：https://$want" >&2
echo "    现在的：https://$have" >&2
first_want="${want%%.*}"; first_have="${have%%.*}"
if [[ "${want#*.}" == "${have#*.}" ]]; then
  if [[ "$first_have" =~ ^${first_want}-[0-9]+$ ]]; then
    echo "    原因：机器名后面多了 -N，说明管理后台里还留着旧的「$first_want」记录。" >&2
    echo "    处理：在管理后台 Machines 页删掉旧记录，再运行 tailscale set --hostname=$first_want，然后重新运行本脚本。" >&2
  else
    echo "    原因：机器名变了（系统主机名被改过，或者重新注册时起了别的名字）。" >&2
    echo "    处理：tailscale set --hostname=$first_want，并在管理后台取消「按系统主机名自动生成」。" >&2
  fi
else
  echo "    原因：tailnet 名变了（改过名，或者登录了另一个 Tailscale 账号）。" >&2
  echo "    处理：如果是误操作，在管理后台 DNS 页改回原来的名字；已经发出去的链接要重新通知。" >&2
fi
exit 1
