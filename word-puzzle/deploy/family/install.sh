#!/usr/bin/env bash
# 词境整站一键部署（主页 + 模块 + 词境学生版 + 公开版）：Debian / Ubuntu，nginx + systemd + Python 标准库。
#
#   sudo env WP_PUBLIC_URL=https://lexica.tailXXXX.ts.net bash word-puzzle/deploy/family/install.sh
#
# 和家庭版（word-puzzle/deploy/install.sh）互不干扰：用户、目录、端口、systemd 服务名都是单独的，
# 所以可以装在同一台机器上试，也可以单独装在一个容器里（推荐，见 部署说明.md）。
#
# 做的事：
#   1. 建系统用户 wpfamily，代码放 /srv/word-puzzle-family，数据库放 /var/lib/word-puzzle-family
#   2. 装 systemd 服务（WP_AUTH=1，后端只监听 127.0.0.1）
#   3. 装 nginx 配置：整站（主页、四个模块、公开版 /words/、要登录的 /word-puzzle/），只监听 127.0.0.1:8081，
#      由 Tailscale Funnel 或云服务器的公网 nginx 转进来；可选再开一个内网入口（WP_LAN_ADDR）
#   4. 装管理命令 wp-family-admin（创建管理员、导入名单、重置密码）
#   5. 自检：未登录访问接口必须被拒绝
#
# 不会覆盖已有数据库，不会碰 Tailscale 和 Funnel（那一步见 部署说明.md，要你自己确认）。
set -euo pipefail

SRC_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
REPO_DIR="$(cd "$SRC_DIR/.." && pwd)"
INSTALL_DIR="${WP_FAMILY_INSTALL_DIR:-/srv/word-puzzle-family}"
DATA_DIR="${WP_FAMILY_DATA_DIR:-/var/lib/word-puzzle-family}"
RUN_USER=wpfamily
SITE_NAME=word-puzzle-family
PORT="${WP_FAMILY_PORT:-8766}"
NGINX_PORT="${WP_FAMILY_NGINX_PORT:-8081}"
TTS_VENV="${WP_FAMILY_TTS_VENV:-/opt/word-puzzle-family/tts-venv}"
# 排排坐的朗读识别：本机离线模型（faster-whisper），录音不出这台机器。模型可换：tiny.en 最快、base.en 更准。
ASR_VENV="${WP_FAMILY_ASR_VENV:-/opt/word-puzzle-family/asr-venv}"
ASR_MODELS="${WP_FAMILY_ASR_MODELS:-/opt/word-puzzle-family/asr-models}"
ASR_MODEL="${WP_ASR_MODEL:-base.en}"
PUBLIC_URL="${WP_PUBLIC_URL:-}"
PROXY_INC=/etc/nginx/word-puzzle-family-proxy.inc
# 内网入口（可选）：WP_LAN_ADDR=容器的内网地址（例如 <容器IP>），端口默认 8082。
# 同一个后端、同一个数据库、同一份网站，只是多一个只监听内网地址的明文 http 入口（宿主机 80 端口转发到这里）。
# 内容和公网入口完全一样（/word-puzzle/ 要登录）；以前的「内网不登录也能做题」只有设 WP_LAN_GUEST=1 才会打开。
# WP_TRUSTED_PROXIES=我们自己的前置代理地址（逗号分隔，例如 PVE 宿主机 的 <服务器IP>），访问记录里会跳过它们。
LAN_ADDR="${WP_LAN_ADDR:-}"
LAN_PORT="${WP_LAN_PORT:-8082}"
TRUSTED_PROXIES="${WP_TRUSTED_PROXIES:-}"
# 数据库每日备份（可选）：WP_BACKUP_DIR=备份目录（建议是挂进容器的宿主机目录，且和数据库不在同一块盘上）。
BACKUP_DIR="${WP_BACKUP_DIR:-}"
LAN_PROXY_INC=/etc/nginx/word-puzzle-family-proxy-lan.inc
# 云服务器专用：SSH 隧道入口的转发头（明文 http，见下面安装 nginx 配置那段）
TUNNEL_PROXY_INC=/etc/nginx/word-puzzle-family-proxy-tunnel.inc
NGINX_DROPIN=/etc/systemd/system/nginx.service.d/lexica-wait-lan.conf
LAN_CONF_FILE=/etc/nginx/conf.d/word-puzzle-family-lan.conf
CONF_FILE=/etc/nginx/conf.d/$SITE_NAME.conf

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

[[ $(id -u) -eq 0 ]] || die "请用 sudo 运行"
[[ -n "$PUBLIC_URL" ]] || die "请用 WP_PUBLIC_URL 指定对外的 https 地址，例如 https://lexica.tailXXXX.ts.net（没有它，离线页里的链接会信客户端传来的主机名）"
[[ "$PUBLIC_URL" =~ ^https://[A-Za-z0-9.-]+(:[0-9]{2,5})?$ ]] || die "WP_PUBLIC_URL 必须是 https://主机名[:端口]，结尾不要带斜杠"
[[ "$PORT" =~ ^[0-9]+$ && "$NGINX_PORT" =~ ^[0-9]+$ && "$LAN_PORT" =~ ^[0-9]+$ ]] || die "端口必须是数字"
[[ -z "$BACKUP_DIR" || "$BACKUP_DIR" =~ ^/[A-Za-z0-9._/-]+$ ]] || die "WP_BACKUP_DIR 必须是绝对路径（字母、数字、._/-）"
[[ "$TRUSTED_PROXIES" =~ ^[0-9a-fA-F:.,]*$ ]] || die "WP_TRUSTED_PROXIES 只能是逗号分隔的 IP 地址"
# 内网入口和公网入口现在完全一样（2026-11-21 决定）：/word-puzzle 要登录。要恢复「内网不登录也能做题」才设 WP_LAN_GUEST=1。
LAN_GUEST="${WP_LAN_GUEST:-0}"
[[ "$LAN_GUEST" == "0" || "$LAN_GUEST" == "1" ]] || die "WP_LAN_GUEST 只能是 0 或 1"
[[ "$LAN_GUEST" == "0" || -n "$LAN_ADDR" ]] || die "WP_LAN_GUEST=1 需要同时设 WP_LAN_ADDR"
[[ -z "$LAN_ADDR" || "$LAN_ADDR" =~ ^(10|192\.168|172\.(1[6-9]|2[0-9]|3[01]))\.[0-9.]+$ ]] || die "WP_LAN_ADDR 必须是内网地址（10.x / 172.16-31.x / 192.168.x），不能是公网地址"
[[ -f "$REPO_DIR/hub/shared/module-header.js" ]] || die "找不到 hub/shared（页眉和配色切换用）：请在完整的仓库里运行"
# 主页和不用登录的模块也由这里提供（网站根路径 / 就是主页），缺一个就不装，免得上线一个残缺的网站
for f in hub/index.html hub/privacy.html hub/css hub/js topic-app/topic-app/index.html ham-exam/index.html \
         chemistry/index.html chemistry/data physics/index.html physics/data; do
  [[ -e "$REPO_DIR/$f" ]] || die "缺少 $f：主页和模块要一起部署（打包时带上 hub topic-app ham-exam chemistry physics）"
done

say "检查并安装系统依赖"
bash "$SRC_DIR/deploy/check-deps.sh"

say "创建系统用户 $RUN_USER"
if ! id "$RUN_USER" >/dev/null 2>&1; then
  useradd --system --home-dir "$INSTALL_DIR" --shell /usr/sbin/nologin "$RUN_USER"
fi

# 依赖先装好（ffmpeg、朗读识别、自然语音）：pip 安装和模型下载可能要好几分钟，放在换代码之前，
# 换上新代码之后紧接着就重启服务，不会出现「新网页 + 旧后端」混着跑好几分钟的情况。
say "安装 ffmpeg（排排坐的录音统一转成 MP3、交给识别）"
if ! command -v ffmpeg >/dev/null 2>&1; then
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ffmpeg \
    || warn "ffmpeg 安装失败：录音照收（原样保存），但识别和统一格式要等装好 ffmpeg"
else
  echo "    已安装，跳过"
fi

say "安装朗读识别（faster-whisper，模型 $ASR_MODEL；失败时录音照收，只是没有奖励分）"
install -d "$(dirname "$ASR_VENV")" "$ASR_MODELS"
if [[ ! -x "$ASR_VENV/bin/python" ]] || ! "$ASR_VENV/bin/python" -c 'import faster_whisper' >/dev/null 2>&1; then
  if python3 -m venv "$ASR_VENV" \
      && PIP_DISABLE_PIP_VERSION_CHECK=1 timeout 900 "$ASR_VENV/bin/python" -m pip install --upgrade 'faster-whisper>=1.1,<2'; then
    echo "    faster-whisper 已安装"
  else
    warn "faster-whisper 安装失败；排排坐的录音照收、照给「提交朗读」的分，没有奖励分"
  fi
else
  echo "    已安装，跳过"
fi
if [[ -x "$ASR_VENV/bin/python" ]] && "$ASR_VENV/bin/python" -c 'import faster_whisper' >/dev/null 2>&1; then
  # 模型只在安装时下载一次（国内服务器连不上下载站时，可以设 WP_ASR_HF_ENDPOINT 用镜像，或者把这个目录从别处整个拷过来）；
  # 服务运行时只读本地文件，不联网。
  # 家里实测（2026-11-21）：huggingface.co 的域名解析被干扰（解析到无关地址，连接 20 秒超时），镜像 hf-mirror.com 两秒就通。
  # 所以先用 WP_ASR_HF_ENDPOINT（设了的话）或官方地址，失败了自动换镜像再试一次。
  fetch_model() {
    env ${1:+HF_ENDPOINT="$1"} HF_HUB_DISABLE_TELEMETRY=1 timeout 900 "$ASR_VENV/bin/python" -c \
      "from faster_whisper import WhisperModel; WhisperModel('$ASR_MODEL', device='cpu', compute_type='int8', download_root='$ASR_MODELS')" \
      >/tmp/lexica-asr-model.log 2>&1
  }
  if HF_HUB_OFFLINE=1 timeout 300 "$ASR_VENV/bin/python" -c \
      "from faster_whisper import WhisperModel; WhisperModel('$ASR_MODEL', device='cpu', compute_type='int8', download_root='$ASR_MODELS', local_files_only=True)" \
      >/dev/null 2>&1; then
    echo "    模型 $ASR_MODEL 已在本地，跳过下载"
  elif fetch_model "${WP_ASR_HF_ENDPOINT:-}" || { [[ -z "${WP_ASR_HF_ENDPOINT:-}" ]] && echo "    官方下载站不通（$(tail -1 /tmp/lexica-asr-model.log | cut -c1-120)），换镜像 hf-mirror.com" && fetch_model https://hf-mirror.com; }; then
    echo "    模型 $ASR_MODEL 已就绪（$ASR_MODELS）"
  else
    warn "模型 $ASR_MODEL 下载失败（$ASR_MODELS）：$(tail -1 /tmp/lexica-asr-model.log | cut -c1-200)；没有模型时不做识别"
  fi
fi
chmod -R a+rX "$ASR_MODELS" 2>/dev/null || true

say "安装 Edge Neural 自然语音（失败时保留 eSpeak 兜底）"
install -d "$(dirname "$TTS_VENV")"
if [[ ! -x "$TTS_VENV/bin/edge-tts" ]]; then
  if python3 -m venv "$TTS_VENV" \
      && PIP_DISABLE_PIP_VERSION_CHECK=1 "$TTS_VENV/bin/python" -m pip install --upgrade 'edge-tts>=7,<8'; then
    echo "    Edge Neural TTS 已安装"
  else
    warn "Edge Neural TTS 安装失败；将使用本地 eSpeak 美式女声"
  fi
else
  echo "    已安装，跳过"
fi

say "同步代码到 $INSTALL_DIR"
install -d "$INSTALL_DIR"
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete \
    --exclude 'var/' --exclude '.*' --exclude '__pycache__/' --exclude 'tests/' --exclude '/site/' --exclude '/shared/' --exclude '/web-public/' \
    "$SRC_DIR"/ "$INSTALL_DIR"/
else
  find "$SRC_DIR" -mindepth 1 -maxdepth 1 ! -name var ! -name '.*' ! -name tests -exec cp -a {} "$INSTALL_DIR"/ \;
fi
# 页眉、配色切换、页脚是仓库里 hub/shared 的公共文件，网站里用 /shared/ 访问
install -d "$INSTALL_DIR/shared"
cp -a "$REPO_DIR/hub/shared/." "$INSTALL_DIR/shared/"

say "生成词境公开版 /words/（只有初中、高中，不用登录）"
python3 "$INSTALL_DIR/tools/build_public_web.py" "$INSTALL_DIR/web" "$INSTALL_DIR/web-public.new.$$"
rm -rf "$INSTALL_DIR/web-public.old"
[[ ! -d "$INSTALL_DIR/web-public" ]] || mv "$INSTALL_DIR/web-public" "$INSTALL_DIR/web-public.old"
mv "$INSTALL_DIR/web-public.new.$$" "$INSTALL_DIR/web-public"
rm -rf "$INSTALL_DIR/web-public.old"
chmod -R a+rX "$INSTALL_DIR/web-public"

say "同步主页和不用登录的模块到 $INSTALL_DIR/site"
# 先在旁边拼好一份完整的，再整体换上去：换的那一瞬间之外，网站上永远是一份完整的旧版或新版
SITE_NEW="$INSTALL_DIR/site.new.$$"
rm -rf "$SITE_NEW"
install -d "$SITE_NEW/hub" "$SITE_NEW/topics" "$SITE_NEW/ham" "$SITE_NEW/chemistry" "$SITE_NEW/physics" "$SITE_NEW/backends"
cp -a "$REPO_DIR/hub/index.html" "$REPO_DIR/hub/privacy.html" "$REPO_DIR/hub/css" "$REPO_DIR/hub/js" "$SITE_NEW/hub/"
cp -a "$REPO_DIR/backends/." "$SITE_NEW/backends/"
sed -i "s/__ASSET_VERSION__/$(date +%Y%m%d%H%M%S)/g" "$SITE_NEW/hub/index.html"
cp -a "$REPO_DIR/topic-app/topic-app/." "$SITE_NEW/topics/"
for f in index.html css data images js; do cp -a "$REPO_DIR/ham-exam/$f" "$SITE_NEW/ham/"; done
for m in chemistry physics; do
  for f in index.html css data js; do cp -a "$REPO_DIR/$m/$f" "$SITE_NEW/$m/"; done
done
find "$SITE_NEW" -name '.*' -prune -exec rm -rf {} +
chmod -R a+rX "$SITE_NEW"
rm -rf "$INSTALL_DIR/site.old"
[[ ! -d "$INSTALL_DIR/site" ]] || mv "$INSTALL_DIR/site" "$INSTALL_DIR/site.old"
mv "$SITE_NEW" "$INSTALL_DIR/site"
rm -rf "$INSTALL_DIR/site.old"

say "准备数据目录 $DATA_DIR"
install -d "$DATA_DIR" "$INSTALL_DIR/var/offline" "$INSTALL_DIR/var/audio"
chown -R "$RUN_USER:$RUN_USER" "$DATA_DIR" "$INSTALL_DIR/var"
chmod 750 "$DATA_DIR"

say "生成内置词库（如果还没有）"
if [[ ! -f "$INSTALL_DIR/data/pep_curriculum.json" ]]; then
  (cd "$INSTALL_DIR" && python3 tools/build_seed_data.py)
else
  echo "    已存在，跳过"
fi

# 数据目录标记：后端的服务单元要先看到它才肯启动（数据盘没挂上时，挂进来的是空目录，没有这个文件，就不会悄悄建一个空数据库）。
# 只在「已经有数据库」或「第一次安装」时放；数据盘没挂上时重装，不会把标记放到空目录里。
if [[ -f "$DATA_DIR/app.db" || ! -e "/etc/systemd/system/$SITE_NAME.service" ]]; then
  touch "$DATA_DIR/.lexica-data"
  chown "$RUN_USER:$RUN_USER" "$DATA_DIR/.lexica-data"
elif [[ ! -e "$DATA_DIR/.lexica-data" ]]; then
  warn "数据目录里没有数据库，也没有 .lexica-data 标记：数据盘是不是没挂上？服务会拒绝启动，直到弄清楚为止"
fi

say "安装 systemd 服务 $SITE_NAME"
sed -e "s|@RUN_USER@|$RUN_USER|g" -e "s|@INSTALL_DIR@|$INSTALL_DIR|g" -e "s|@DATA_DIR@|$DATA_DIR|g" \
    -e "s|@PORT@|$PORT|g" -e "s|@PUBLIC_URL@|$PUBLIC_URL|g" -e "s|@TTS_VENV@|$TTS_VENV|g" \
    -e "s|@LAN_GUEST@|$LAN_GUEST|g" -e "s|@TRUSTED_PROXIES@|$TRUSTED_PROXIES|g" \
    -e "s|@ASR_VENV@|$ASR_VENV|g" -e "s|@ASR_MODELS@|$ASR_MODELS|g" -e "s|@ASR_MODEL@|$ASR_MODEL|g" \
    "$INSTALL_DIR/deploy/family/systemd/word-puzzle-family.service" > "/etc/systemd/system/$SITE_NAME.service"
systemctl daemon-reload
systemctl enable "$SITE_NAME" >/dev/null
systemctl restart "$SITE_NAME"

say "安装看门狗（每分钟检查网站；要求常开时，Funnel 掉了自动重新打开）"
install -d /etc/lexica
sed -e "s|@SITE_NAME@|$SITE_NAME|g" -e "s|@NGINX_PORT@|$NGINX_PORT|g" -e "s|@PORT@|$PORT|g" \
    "$INSTALL_DIR/deploy/family/watchdog.sh" > /usr/local/sbin/lexica-watchdog
chmod 0755 /usr/local/sbin/lexica-watchdog
for unit in lexica-watchdog.service lexica-watchdog.timer; do
  install -m 0644 "$INSTALL_DIR/deploy/family/systemd/$unit" "/etc/systemd/system/$unit"
done
if [[ "${WP_FUNNEL_KEEP:-}" == "1" ]]; then
  touch /etc/lexica/funnel-keep
  echo "    已设为公网入口常开（/etc/lexica/funnel-keep）；要关掉：先 rm 这个文件，再 tailscale funnel reset"
fi
systemctl daemon-reload
systemctl enable --now lexica-watchdog.timer >/dev/null

if [[ -n "$BACKUP_DIR" ]]; then
  say "安装每日备份定时器（$BACKUP_DIR，保留 30 份）"
  install -d -o "$RUN_USER" -g "$RUN_USER" -m 0750 "$BACKUP_DIR" \
    || warn "建不了或改不了备份目录 $BACKUP_DIR 的属主（非特权容器的挂载点常见）；请在宿主机上把它的属主设成服务账号"
  for unit in lexica-backup.service lexica-backup.timer; do
    sed -e "s|@RUN_USER@|$RUN_USER|g" -e "s|@INSTALL_DIR@|$INSTALL_DIR|g" -e "s|@DATA_DIR@|$DATA_DIR|g" \
        -e "s|@BACKUP_DIR@|$BACKUP_DIR|g" "$INSTALL_DIR/deploy/family/systemd/$unit" > "/etc/systemd/system/$unit"
  done
  systemctl daemon-reload
  systemctl enable --now lexica-backup.timer >/dev/null
  systemctl start lexica-backup.service || warn "第一次备份没成功，用 journalctl -u lexica-backup 看原因"
fi

say "安装 nginx 配置（只监听 127.0.0.1:$NGINX_PORT）"
install -d /etc/nginx/conf.d
install -m 0644 "$INSTALL_DIR/deploy/family/nginx/proxy.inc" "$PROXY_INC"
# 云服务器上，这个 127.0.0.1:8081 入口是给 SSH 隧道用的：浏览器看到的是明文 http
# （家里这台机器前面是 Funnel，浏览器看到的是 https，所以那边不用改）。
# 会话 Cookie 带 Secure 的话，浏览器只在「安全来源」（https，或 localhost）下才肯保存；
# 通过隧道用本机的局域网 IP 打开时（比如 http://192.168.x.x:8081）不是安全来源，
# 浏览器会把 Cookie 直接丢掉，表现为「登录成功但下一���又要求登录」。
# 所以这里另装一份转发头，告诉后端「这条是明文 http」，后端就不给 Cookie 加 Secure。
# 和内网入口一样，转发链由 nginx 亲自补上真实连接地址，客户端自己写的那个不作数。
if [[ "${WP_CLOUD:-}" == "1" ]]; then
  say "云服务器：SSH 隧道入口按明文 http 处理（会话 Cookie 不带 Secure）"
  sed -e 's|^proxy_set_header X-Forwarded-Proto .*|proxy_set_header X-Forwarded-Proto http;|' \
      -e 's|^proxy_set_header X-Wp-Edge-Xff .*|proxy_set_header X-Wp-Edge-Xff $proxy_add_x_forwarded_for;|' \
      "$PROXY_INC" > "$TUNNEL_PROXY_INC"
  chmod 0644 "$TUNNEL_PROXY_INC"
  CONTAINER_PROXY_INC="$TUNNEL_PROXY_INC"
else
  CONTAINER_PROXY_INC="$PROXY_INC"
fi
TEMP_CONF="$CONF_FILE.tmp.$$"
trap 'rm -f "$TEMP_CONF"' EXIT
sed -e "s|@INSTALL_DIR@|$INSTALL_DIR|g" -e "s|@PORT@|$PORT|g" -e "s|@NGINX_PORT@|$NGINX_PORT|g" \
    -e "s|@PROXY_INC@|$CONTAINER_PROXY_INC|g" \
    "$INSTALL_DIR/deploy/family/nginx/word-puzzle-family.conf" > "$TEMP_CONF"
had_old=0
if [[ -e "$CONF_FILE" ]]; then cp -a "$CONF_FILE" "$CONF_FILE.bak"; had_old=1; fi
mv "$TEMP_CONF" "$CONF_FILE"
if ! nginx -t; then
  rm -f "$CONF_FILE"
  [[ "$had_old" -eq 0 ]] || mv "$CONF_FILE.bak" "$CONF_FILE"
  die "nginx 配置检查失败；已恢复原样"
fi

if [[ -n "$LAN_ADDR" ]]; then
  say "安装内网入口 $LAN_ADDR:$LAN_PORT（和公网入口内容一样，走明文 http；只给内网）"
  # 在公网配置的基础上：换监听地址；标记为内网入口；告诉后端这是明文 http（会话 Cookie 不带 Secure）；转发链交给后端算真实 IP
  sed -e 's|^proxy_set_header X-Forwarded-Proto .*|proxy_set_header X-Forwarded-Proto http;|' \
      -e 's|^proxy_set_header X-Wp-Edge-Xff .*|proxy_set_header X-Wp-Edge-Xff $proxy_add_x_forwarded_for;|' \
      -e 's|^proxy_set_header X-Wp-Entry .*|proxy_set_header X-Wp-Entry lan;|' \
      "$PROXY_INC" > "$LAN_PROXY_INC"
  chmod 0644 "$LAN_PROXY_INC"
  sed -n '/^server {/,$p' "$INSTALL_DIR/deploy/family/nginx/word-puzzle-family.conf" \
    | sed -e "s|listen 127.0.0.1:@NGINX_PORT@;|listen $LAN_ADDR:$LAN_PORT;|" -e "s|@PROXY_INC@|$LAN_PROXY_INC|g" \
          -e "s|@INSTALL_DIR@|$INSTALL_DIR|g" -e "s|@PORT@|$PORT|g" -e "s|word-puzzle-family\\.|word-puzzle-family-lan.|g" \
    > "$LAN_CONF_FILE.tmp.$$"
  # 开机时 nginx 可能比容器的静态 IP 先起来，监听内网地址会失败，连公网入口一起带倒。
  # 所以让 nginx 启动前最多等 60 秒，等到这个地址出现，并且失败了自动重试。
  install -d /etc/systemd/system/nginx.service.d
  cat > "$NGINX_DROPIN" <<UNIT
[Service]
ExecStartPre=
ExecStartPre=/bin/sh -c 'i=0; while [ \$i -lt 60 ]; do ip -4 -o addr show | grep -q " $LAN_ADDR/" && exit 0; i=\$((i+1)); sleep 1; done; exit 0'
ExecStartPre=/usr/sbin/nginx -t -q -g 'daemon on; master_process on;'
Restart=on-failure
RestartSec=3
UNIT
  systemctl daemon-reload
  if [[ -e "$LAN_CONF_FILE" ]]; then cp -a "$LAN_CONF_FILE" "$LAN_CONF_FILE.bak"; fi
  mv "$LAN_CONF_FILE.tmp.$$" "$LAN_CONF_FILE"
  if ! nginx -t; then
    rm -f "$LAN_CONF_FILE"; if [[ -e "$LAN_CONF_FILE.bak" ]]; then mv "$LAN_CONF_FILE.bak" "$LAN_CONF_FILE"; fi
    die "内网入口的 nginx 配置检查失败；已恢复原样"
  fi
else
  rm -f "$LAN_CONF_FILE" "$LAN_PROXY_INC"
  if [[ -e "$NGINX_DROPIN" ]]; then rm -f "$NGINX_DROPIN"; systemctl daemon-reload; fi
fi
systemctl reload-or-restart nginx

say "安装管理命令 wp-family-admin"
cat > /usr/local/sbin/wp-family-admin <<ADMIN
#!/usr/bin/env bash
# 以服务用户的身份运行账号管理命令（数据库归服务用户所有，不能用 root 直接写）。
cd "$INSTALL_DIR" || exit 1
exec runuser -u $RUN_USER -- env WP_DB="$DATA_DIR/app.db" python3 -m server.admin "\$@"
ADMIN
chmod 0755 /usr/local/sbin/wp-family-admin

say "记录对外网址，并和 Tailscale 里的比对"
printf '%s\n' "$PUBLIC_URL" > "$DATA_DIR/public-url"
chown "$RUN_USER:$RUN_USER" "$DATA_DIR/public-url"
if [[ "${WP_CLOUD:-}" == "1" ]]; then
  echo "    云服务器（deploy/cloud/install.sh 调用）：没有 Tailscale Funnel，对外网址由 nginx + 域名提供，跳过比对"
elif command -v tailscale >/dev/null 2>&1; then
  bash "$INSTALL_DIR/deploy/family/check-url.sh" "$PUBLIC_URL" \
    || warn "对外网址和 Tailscale 里的不一致（见上），请先弄清楚再把网址发给学生"
else
  echo "    这台机器上还没有 Tailscale，先记下网址；装好 Tailscale 后运行 bash $INSTALL_DIR/deploy/family/check-url.sh"
fi

say "自检"
ok=0
for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  if curl --noproxy '*' -fsS --max-time 5 "http://127.0.0.1:$NGINX_PORT/word-puzzle/api/health" >/dev/null 2>&1; then ok=1; break; fi
  sleep 1
done
[[ "$ok" -eq 1 ]] || die "服务没有起来：journalctl -u $SITE_NAME -n 30"
me="$(curl --noproxy '*' -fsS --max-time 5 "http://127.0.0.1:$NGINX_PORT/word-puzzle/api/auth/me")"
python3 -c 'import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get("auth_enabled") is True and d.get("user") is None else 1)' <<<"$me" \
  || die "登录功能没有启用：$me"
code="$(curl --noproxy '*' -s -o /dev/null -w '%{http_code}' --max-time 5 "http://127.0.0.1:$NGINX_PORT/word-puzzle/api/banks")"
[[ "$code" == "401" ]] || die "未登录访问 /api/banks 应该返回 401，实际 $code —— 不要对外开放！"
code="$(curl --noproxy '*' -s -o /dev/null -w '%{http_code}' --max-time 5 "http://127.0.0.1:$NGINX_PORT/word-puzzle/login.html")"
[[ "$code" == "200" ]] || die "登录页打不开（HTTP $code）"
echo "    OK 登录已启用；未登录访问接口被拒绝（401）；登录页可访问"
# nginx reload 是异步的：旧 worker 还在应答时会按旧配置回答（刚装完时根路径是 302，不是 200），
# 所以每个页面都要重试几次，等新 worker 接手。这跟 deploy-all 里的 retry() 是同一个原因。
for page in / /privacy.html /topics/ /ham/ /chemistry/ /physics/ /shared/site-footer.js; do
  code=""
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    code="$(curl --noproxy '*' -s -o /dev/null -w '%{http_code}' --max-time 5 "http://127.0.0.1:$NGINX_PORT$page")"
    [[ "$code" == "200" ]] && break
    sleep 1
  done
  [[ "$code" == "200" ]] || die "主页 / 模块打不开：$page（HTTP $code）"
done
# 根路径的内容也要重试：新 worker 接手前，旧 worker 会返回 302 而不是词境主页。
# 先把正文取下来再 grep：curl | grep -q 里 grep 找到就退出，curl 会收到 SIGPIPE（退出码 23），
# 配合 set -o pipefail 会把「找到了」误判成「失败」。
home_body=""
for _ in 1 2 3 4 5 6 7 8 9 10; do
  home_body="$(curl --noproxy '*' -fsS --max-time 5 "http://127.0.0.1:$NGINX_PORT/" 2>/dev/null || true)"
  [[ "$home_body" == *词境* ]] && break
  sleep 1
done
[[ "$home_body" == *词境* ]] || die "根路径不是词境主页"
echo "    OK 主页、隐私说明和四个模块都能打开"
# 公开版：不登录能拿到题库，而且只有初中、高中；管理页、管理接口、离线页都打不开
pub="$(curl --noproxy '*' -fsS --max-time 5 "http://127.0.0.1:$NGINX_PORT/words/api/banks")" || die "公开版 /words/api/banks 打不开"
python3 -c 'import json,sys; b=json.load(sys.stdin)["banks"]; sys.exit(0 if b and all(x["level1"] in ("初中","高中") for x in b) else 1)' <<<"$pub" \
  || die "公开版的题库不对（应该只有内置的初中、高中，而且不能是空的）"
for page in /words/ /words/play.html /words/practice.html /words/stats.html; do
  code="$(curl --noproxy '*' -s -o /dev/null -w '%{http_code}' --max-time 5 "http://127.0.0.1:$NGINX_PORT$page")"
  [[ "$code" == "200" ]] || die "公开版页面打不开：$page（HTTP $code）"
done
for page in /words/admin.html /words/login.html /words/api/admin/users /words/api/leaderboard /words/api/offline; do
  code="$(curl --noproxy '*' -s -o /dev/null -w '%{http_code}' --max-time 5 "http://127.0.0.1:$NGINX_PORT$page")"
  [[ "$code" == "404" ]] || die "公开版不该能打开 $page（HTTP $code）—— 不要对外开放！"
done
echo "    OK 公开版 /words/：不登录能用，只有初中、高中；管理页、登录、积分榜、离线页都打不开"

cat <<EOF2

部署完成（还没有对外开放）。

  本机入口 ： http://127.0.0.1:$NGINX_PORT/word-puzzle/
$( [[ -z "$LAN_ADDR" ]] || echo "  内网入口 ： http://$LAN_ADDR:$LAN_PORT/   （和公网一样：主页和模块不用登录，/word-puzzle/ 要登录）" )
$( if [[ "${WP_CLOUD:-}" == "1" ]]; then echo "  对外地址 ： $PUBLIC_URL/word-puzzle/   （由 deploy/cloud/ 的 nginx 提供，见 deploy/cloud/部署说明.md）"; else echo "  对外地址 ： $PUBLIC_URL/word-puzzle/   （要先开 Tailscale Funnel，见 部署说明.md）"; fi )
  数据库   ： $DATA_DIR/app.db
  服务     ： systemctl status $SITE_NAME

下一步：
  1) 创建管理员：  sudo wp-family-admin create-admin 你的工号 --name 你的名字   （超级管理员；老师在网页「老师与分配」里加）
  2) 导入名单：    sudo wp-family-admin import /tmp/名单.xlsx --out /tmp/初始密码.csv
     （或者登录后在「账号管理」页面上传名单）
$( if [[ "${WP_CLOUD:-}" == "1" ]]; then echo "  3) （云服务器）不需要 Funnel，也不用 check-url.sh；接着看 deploy/cloud/部署说明.md"; else printf '%s\n' "  3) 开 Funnel：   tailscale funnel --bg $NGINX_PORT      （确认过再开，见 部署说明.md 的检查清单）" "  4) 网址会不会变： bash $INSTALL_DIR/deploy/family/check-url.sh   （重建容器、改名之后都要跑）"; fi )

EOF2
