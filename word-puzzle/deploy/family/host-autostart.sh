#!/usr/bin/env bash
# 在 PVE 宿主机上运行一次：让学生版容器停电重启后自己起来，并且起得比较稳。
#   sudo bash host-autostart.sh <容器编号>        （不给编号就读 deploy.local.env 里的 LEXICA_CTID）
# 做的事：
#   1. 容器开机自启（--onboot 1），并且排在宿主机网络、磁盘就绪之后：启动顺序 2、之后等 45 秒再启动下一个。
#   2. 确认宿主机负责按「开机自启」拉起虚拟机 / 容器的服务是开着的（pve-guests）。
#   3. 检查两块数据盘（容器里的数据库和备份）是不是挂着，/etc/fstab 里有没有 nofail（没有的话盘坏了 / 慢了，
#      整台宿主机会卡在紧急模式，远程就连不上了）。只检查和提示，不改 fstab。
set -euo pipefail

CTID="${1:-}"
if [[ -z "$CTID" ]]; then
  ENV_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)/deploy.local.env"
  [[ -f "$ENV_FILE" ]] && CTID="$(grep -E '^LEXICA_CTID=' "$ENV_FILE" | head -1 | cut -d= -f2- | tr -d '"')"
fi
[[ "$CTID" =~ ^[0-9]+$ ]] || { echo "用法：bash host-autostart.sh <容器编号>" >&2; exit 1; }
command -v pct >/dev/null || { echo "要在 PVE 宿主机上运行（找不到 pct）" >&2; exit 1; }

echo "==> 容器 ${CTID}：开机自启，启动顺序 2，起来后等 45 秒"
pct set "$CTID" --onboot 1 --startup order=2,up=45
pct config "$CTID" | grep -E "^(onboot|startup):"

echo "==> 宿主机的自启动服务"
if systemctl is-enabled --quiet pve-guests 2>/dev/null; then echo "    pve-guests 已启用"; else
  echo "    pve-guests 没启用，现在启用"; systemctl enable pve-guests; fi

echo "==> 容器挂载的宿主机目录"
status=0
while read -r src; do
  [[ -n "$src" ]] || continue
  top="/$(echo "${src#/}" | cut -d/ -f1)"
  if mountpoint -q "$top"; then echo "    OK   $src 所在的 $top 已挂载"; else
    echo "    !!   $src 所在的 $top 没有挂载（现在是宿主机根盘上的一个普通目录）"; status=1; fi
  if [[ ! -d "$src" ]]; then echo "    !!   $src 不存在"; status=1; fi
  if grep -E "^[^#].*[[:space:]]$top[[:space:]]" /etc/fstab | grep -qv nofail; then
    echo "    !!   /etc/fstab 里 $top 那一行没有 nofail：这块盘一旦起不来，整台宿主机会停在紧急模式，远程连不上。"
    echo "         建议在挂载选项里加上 nofail（和 x-systemd.device-timeout=30s）；容器侧有保护，数据盘没挂上时服务会拒绝启动，不会建空数据库。"
  fi
done < <(pct config "$CTID" | grep -E "^mp[0-9]+:" | sed -E 's/^mp[0-9]+: *([^,]+),.*/\1/')
[[ $status == 0 ]] || { echo "有数据盘没挂好，先处理盘的问题（lsblk、mount -a）" >&2; exit 2; }
echo "完成。"
