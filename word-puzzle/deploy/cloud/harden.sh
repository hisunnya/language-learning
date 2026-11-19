#!/usr/bin/env bash
# 云服务器 SSH 加固：只允许密钥登录 + fail2ban 封禁反复失败的地址。可以重复运行。
#
#   sudo bash word-puzzle/deploy/cloud/harden.sh
#
# 防止把自己锁在外面：
#   - root 的 authorized_keys 里必须已经有公钥，否则拒绝执行；
#   - 新配置先用 sshd -t 检查，通过才重载；已经建立的连接不受影响，
#     所以请**保持当前这个终端不关**，另开一个终端用密钥登录成功之后再关。
# 配置放在 sshd_config.d/00-… 里：sshd 取第一次出现的值，00 在腾讯云自带的 50-cloud-init 之前，所以它说了算。
set -euo pipefail

DROPIN="${WP_SSHD_DROPIN:-/etc/ssh/sshd_config.d/00-lexica-hardening.conf}"
AUTH_KEYS="${WP_AUTH_KEYS:-/root/.ssh/authorized_keys}"

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

[[ $(id -u) -eq 0 ]] || die "请用 sudo 运行"
grep -qE '^(ssh-(rsa|ed25519)|ecdsa-sha2-[a-z0-9-]+|sk-[a-z0-9@.-]+) ' "$AUTH_KEYS" 2>/dev/null \
  || die "$AUTH_KEYS 里没有公钥：现在关掉密码登录会把你锁在外面。先确认密钥登录可用"

say "SSH：只许密钥登录"
install -d "$(dirname "$DROPIN")"
cat > "$DROPIN" <<'CONF'
# 由 deploy/cloud/harden.sh 生成。
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin prohibit-password
PubkeyAuthentication yes
MaxAuthTries 3
LoginGraceTime 30
X11Forwarding no
CONF
chmod 0644 "$DROPIN"
if ! sshd -t; then
  rm -f "$DROPIN"
  die "sshd 配置检查失败，已撤销"
fi
effective="$(sshd -T | grep -E '^(passwordauthentication|permitrootlogin) ' | tr '\n' ' ')"
echo "    生效的设置：$effective"
grep -q 'passwordauthentication no' <<<"$effective" || { rm -f "$DROPIN"; die "密码登录没有被关掉（有别的配置在前面覆盖了它），已撤销，请检查 sshd -T"; }
systemctl reload ssh 2>/dev/null || systemctl reload sshd

say "fail2ban：反复登录失败的地址封一小时"
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq fail2ban python3-systemd >/dev/null
install -d /etc/fail2ban/jail.d
cat > /etc/fail2ban/jail.d/lexica-sshd.local <<'JAIL'
[sshd]
enabled = true
backend = systemd
maxretry = 5
findtime = 10m
bantime = 1h
JAIL
systemctl enable --now fail2ban >/dev/null 2>&1
systemctl restart fail2ban
sleep 2
fail2ban-client status sshd >/dev/null 2>&1 || die "fail2ban 的 sshd 监狱没有起来：journalctl -u fail2ban -n 30"
echo "    OK fail2ban 在监视 sshd"

echo
echo "完成。请保持当前终端，另开一个终端用密钥登录确认没问题，再关掉这个。"
