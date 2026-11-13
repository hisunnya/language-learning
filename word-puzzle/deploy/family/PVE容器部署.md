# 在 PVE 里用容器跑「词境 家庭版」+ Tailscale Funnel

目标：**家庭版只跑在一个独立的 LXC 容器里**，容器里装本程序和 Tailscale，由 Funnel 对外。
PVE 宿主机（管理界面、SSH、其他虚拟机）不在对外的路径上。

```
学生手机 --HTTPS--> Tailscale Funnel --> [LXC 容器 lexica]
                                           tailscaled
                                           nginx 127.0.0.1:8081 --> 后端 127.0.0.1:8766
PVE 宿主机 pve03：只负责跑这个容器，不装本程序，不开 Funnel
```

下面的命令分两处执行：标「宿主机」的在 PVE 宿主机上（root），标「容器内」的在容器里（用 `pct enter $CTID` 进去，不需要密码，**也不要给容器开 SSH**）。

文中的 `$CTID` 是一个 shell 变量，存的是容器编号。**先在宿主机上设好它，后面的命令就可以原样复制**。
变量只在**当前这个终端窗口**里有效：重新登录、换了窗口，它就是空的，需要重新设一次。
用到它的每个命令块开头都有一行检查，没设置时会直接提示「先设置容器编号」，不会闷头往下跑。
（也不要把 `CTID` 这几个字母直接当成编号写进命令，会报 `vmid: type check ('integer') failed`，见第十节。）

```bash
# 宿主机：先看哪些编号已经被占用（虚拟机和容器共用一套编号）
qm list; pct list
CTID=120                  # 选一个没出现在上面两张表里的数字；换了新的终端窗口要重新设一次
```

> 版本说明：宿主机是 PVE 9（Debian 13）。Tailscale 官方给的容器配置针对 PVE 7 及以上（cgroup2），
> 本文照这个写；个别命令的参数以你机器上的 `pct help create`、`tailscale funnel --help` 为准。

---

## 一、创建容器（宿主机）

```bash
pveam update
pveam available --section system | grep debian-13        # 找到 Debian 13 的模板名
pveam download local debian-13-standard_13.6-1_amd64.tar.zst    # 模板名以上一条命令的输出为准，版本号会变
pvesm status                                              # 看存储名：下面的 local-lvm 要换成这里有的（需要「Content 含 rootdir」）
```

确认 IP 没被占用：`ping -c 2 10.1.1.100` 应该全部丢包；同时进路由器把 `10.1.1.100` 排除出 DHCP 地址池
（或者确认它不在池子里），否则以后某台手机可能被分到同一个地址。

```bash
: "${CTID:?先设置容器编号，例如 CTID=120}"
TEMPLATE=debian-13-standard_13.6-1_amd64.tar.zst

pct create $CTID local:vztmpl/$TEMPLATE \
  --hostname lexica \
  --unprivileged 1 \
  --features nesting=1,keyctl=1 \
  --cores 1 --memory 1024 --swap 512 \
  --rootfs local-lvm:8 \
  --net0 name=eth0,bridge=vmbr0,ip=10.1.1.100/20,gw=10.1.1.1 \
  --onboot 1 --start 0
```

- **一定要非特权容器**（`--unprivileged 1`）：容器里即使被攻破，也只是宿主机上一个没有权限的普通用户。
- 网络：静态地址 `10.1.1.100`，掩码 `/20`（255.255.240.0），网关 `10.1.1.1`，桥接 `vmbr0`（和宿主机 `10.1.1.93` 同一个网络）。
  换地址就改 `ip=` 和 `gw=` 两处。
- DNS 不写就继承宿主机的设置。如果以后容器里能 ping 通 IP 却解析不了域名，再加一条
  `pct set $CTID --nameserver 10.1.1.1`（路由器做 DNS 转发）或者你家实际在用的 DNS 服务器。
- `--rootfs local-lvm:8` 的存储名按 `pvesm status` 的结果改，8 GB 足够。
- 不用设 root 密码，也不要装 SSH，需要进去时在宿主机上 `pct enter $CTID`。
- 创建完查看一下：`pct config $CTID`，应该能看到 `unprivileged: 1`、`net0: ...ip=10.1.1.100/20,gw=10.1.1.1`。

## 二、给容器放行 TUN 设备（宿主机）

Tailscale 需要 `/dev/net/tun`。官方给了两种办法，二选一：

```bash
: "${CTID:?先设置容器编号，例如 CTID=120}"
# 办法 A：pct 的设备直通（官方也列为可选方式）
pct set $CTID --dev0 /dev/net/tun
```

```bash
: "${CTID:?先设置容器编号，例如 CTID=120}"
# 办法 B：直接改配置文件（PVE 7 及以上）
cat >> /etc/pve/lxc/$CTID.conf <<'CONF'
lxc.cgroup2.devices.allow: c 10:200 rwm
lxc.mount.entry: /dev/net/tun dev/net/tun none bind,create=file
CONF
```

然后启动容器：`pct start $CTID`，进去确认设备在：`pct enter $CTID` → `ls -l /dev/net/tun`。
再确认网络通：在容器里 `ip -4 addr show eth0`（应该是 10.1.1.100/20）、`ping -c 2 10.1.1.1`、`ping -c 2 debian.org`。

> 如果不想给容器 TUN 设备，官方还提到一种「用户态网络」模式（不需要设备权限）。
> **Funnel 在这个模式下能不能用我没有实测**，所以本文不用它；真遇到 TUN 放不通，改用虚拟机（VM）最省事。

## 三、容器内的基础准备（容器内）

```bash
apt-get update && apt-get -y upgrade
apt-get -y install curl ca-certificates tar
```

## 四、先装 Tailscale、定下网址（容器内，**这时还不开 Funnel**）

网址是 `主机名.tailnet名.ts.net`，要先确定下来，因为安装本程序时要用到完整网址。

**4.1 先在 Tailscale 管理后台（浏览器）准备好：**

1. **DNS 页 → Rename tailnet**：挑一个你喜欢的名字。只能从随机生成的里选，**不能自己输入**；发出网址之后再改，所有链接和二维码都作废，所以现在定。
2. 同一页确认 **MagicDNS** 和 **HTTPS Certificates** 已开启（第一次运行 `tailscale funnel` 时命令行也会引导你）。

**4.2 容器里安装并登录：**

```bash
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up --hostname=lexica          # 输出一个网址，用浏览器打开登录授权
tailscale status                        # 看到本机即可
```

**4.3 关掉这台机器的密钥过期（重要）：** 管理后台 → **Machines** → 找到 `lexica` → 右侧菜单 →
**Disable key expiry**。新设备的密钥默认 180 天过期，过期后这台机器的连接会停止工作，
学生就打不开了，而且容易被忘记。

**4.4 记下完整网址：** 形如 `https://lexica.xxxx.ts.net`（也能在管理后台的 Machines 页看到）。
下面叫它 `WP_PUBLIC_URL`。可以让命令自己读出来，省得手抄：

```bash
# 容器内
WP_PUBLIC_URL="https://$(tailscale status --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))')"
echo "$WP_PUBLIC_URL"          # 应该是 https://lexica.你的tailnet名.ts.net，不对就手工写：WP_PUBLIC_URL=https://...
```

（换了新终端要重新设一次；这条命令读的字段是按 Tailscale 的状态输出写的，我没有在真机上跑过，出错就手写。）

## 五、把代码放进容器并安装（宿主机 + 容器内）

容器里没有仓库时，从宿主机上的检出目录（`/root/language-learning`）推进去，只需要两个目录：

```bash
: "${CTID:?先设置容器编号，例如 CTID=120}"
# 宿主机
cd /root/language-learning && git pull
tar czf /tmp/lexica-src.tgz --exclude='word-puzzle/var' --exclude='__pycache__' --exclude='.DS_Store' \
    word-puzzle hub/shared
pct push $CTID /tmp/lexica-src.tgz /root/lexica-src.tgz
pct exec $CTID -- mkdir -p /root/language-learning
pct exec $CTID -- tar xzf /root/lexica-src.tgz -C /root/language-learning
```

然后在容器里安装（会装 nginx、Python 环境、语音等依赖，要几分钟）：

```bash
# 容器内
cd /root/language-learning
env WP_PUBLIC_URL="$WP_PUBLIC_URL" bash word-puzzle/deploy/family/install.sh
```

脚本最后会自检：未登录访问接口必须返回 401，不通过就报错退出。

创建管理员、导入名单（容器内）：

```bash
: "${CTID:?先设置容器编号，例如 CTID=120}"
wp-family-admin create-admin 你的工号 --name 你的名字
# 名单文件从宿主机推进来：pct push $CTID /路径/名单.xlsx /tmp/名单.xlsx
wp-family-admin import /tmp/名单.xlsx --out /tmp/初始密码.csv
# 把初始密码清单取出来发给学生，然后删掉（明文）：
#   宿主机： pct pull $CTID /tmp/初始密码.csv ./初始密码.csv
#   容器内： rm /tmp/初始密码.csv /tmp/名单.xlsx
```

## 六、上线前检查，然后开 Funnel（容器内）

先对照 `部署说明.md` 第四节的检查清单，再加这几条容器特有的：

- [ ] `ss -ltnp` 里除了 tailscaled，只有 `127.0.0.1:8081`（nginx）和 `127.0.0.1:8766`（后端）在监听
- [ ] `curl http://127.0.0.1:8081/word-puzzle/api/banks` 返回 401
- [ ] 管理员已创建，能登录并看到「账号管理」
- [ ] Machines 页里 `lexica` 显示 **Key expiry disabled**，并且已取消「Auto-generate from OS hostname」（第九节）
- [ ] `bash /srv/word-puzzle-family/deploy/family/check-url.sh` 输出 `OK 网址一致`，并把网址记在第九节的记录表里

```bash
tailscale funnel --bg 8081              # 具体参数以 tailscale funnel --help 为准
tailscale funnel status                 # 应该只看到 8081 这一条
```

用**没装 Tailscale 的手机、关掉 Wi-Fi** 打开 `WP_PUBLIC_URL/word-puzzle/`，应该看到登录页。
（装了同一个账号的设备解析到的是内网地址，没经过 Funnel，测不准。）

关掉对外访问：`tailscale funnel reset`。

## 七、宿主机上已有的 Tailscale

你之前在 pve03 宿主机上试过 Tailscale（节点名 `pve03`）。建议清理掉，免得宿主机的名字和节点留在 tailnet 里：

```bash
# 宿主机
tailscale funnel reset                  # 确认没有任何对外开放
tailscale logout
apt-get -y remove tailscale
```

然后在管理后台 Machines 页把 `pve03` 这条记录也删掉。
如果你想保留它用来远程管理宿主机，也可以留在 tailnet 里，但**绝不要**在宿主机上开 Funnel，
并确认 `tailscale funnel status` 显示 `No serve config`。

## 八、备份、更新、监控

- **备份：** 在 PVE 管理界面 Datacenter → Backup 给这个容器建定时任务，或手动：
  `vzdump $CTID --storage <备份存储> --mode snapshot --compress zstd`。
  备份里有学生的学号、姓名、成绩和密码哈希，**也包含这台机器在 Tailscale 里的身份**，要妥善保管；
  还原到别处时，不要让原容器和还原出来的副本同时在线（两个同身份的节点会互相抢）。
  数据库本身也可以在容器里 `sqlite3 /var/lib/word-puzzle-family/app.db ".backup '/tmp/app.db'"` 单独备份。
- **更新程序：** 宿主机 `git pull` → 重新打包推进去 → 容器里重新运行第五节的安装命令。数据库不会被覆盖，网址不变。
- **更新系统和 Tailscale：** 容器里定期 `apt-get update && apt-get -y upgrade`，**不要为了升级去重装或重建容器**。
  升级、重启之后按第九节第 4 条检查一遍。
- **日志：** `journalctl -u word-puzzle-family`；nginx 的在 `/var/log/nginx/word-puzzle-family.*.log`。
- **资源：** 100 多个学生，1 核 1 GB 足够；上课时同时在线的人多了再看 `top`。

## 九、网址会不会变，怎样让它不变

网址 = `机器名.tailnet名.ts.net`，例如 `lexica.tail705ad2.ts.net`。发给学生的链接和二维码都依赖它，所以要尽量不变。

**1. 什么操作会让它变**

| 操作 | 网址 |
|---|---|
| 重启容器、重启宿主机、`apt upgrade`、升级 Tailscale、重新运行安装脚本 | **不变**（Tailscale 的身份存在容器里的 `/var/lib/tailscale`） |
| 用 vzdump 还原到同一个容器（原容器已停掉并删除） | **不变**（沿用原来的身份） |
| 容器被销毁后重建，而管理后台里旧的 `lexica` 记录还在 | **会变**：新机器被命名为 `lexica-1` |
| 改了容器的系统主机名，而「按系统主机名自动生成」还勾着 | **会变**：机器名跟着系统主机名走 |
| 在管理后台 Rename tailnet，或把机器登录到另一个 Tailscale 账号 | **会变**（中间那段） |

**2. 现在就做的一次性防护**

- 管理后台 → Machines → `lexica` → Edit machine name → **取消「Auto-generate from OS hostname」**，机器名就固定了，
  系统主机名再怎么变也不影响。（命令行里 `tailscale set --hostname=lexica` 也行。）
- **发出网址之后不再改 tailnet 名。**
- **把网址记下来**（安装脚本会自动记在容器里的 `/var/lib/word-puzzle-family/public-url`，你自己也抄一份）：

  | 项目 | 你的值 |
  |---|---|
  | 对外网址 | `https://lexica.____________.ts.net` |
  | 容器编号 | `______` |
  | 机器名 | `lexica` |
  | tailnet 名 | `____________` |

- 随时可以检查网址有没有变：`bash /srv/word-puzzle-family/deploy/family/check-url.sh`。
  一致输出 `OK 网址一致`；不一致会告诉你原因（多了 `-1`、机器名变了、tailnet 名变了）和处理办法。

**3. 必须重建容器时的顺序（不要先建新的）**

优先用 vzdump **还原**，网址不会变。必须从零重建时：

1. 先记下网址，并把数据库取出来备份（`pct pull $CTID /var/lib/word-puzzle-family/app.db ./app.db`，或做一次 vzdump）。
2. `pct stop` 旧容器（先别删，留着当退路）。
3. **在管理后台 Machines 页删除旧的 `lexica` 记录。**
4. 新建容器（`--hostname lexica`），装 Tailscale，`tailscale up --hostname=lexica`。
5. 运行 `check-url.sh`，**看到 `OK 网址一致` 才继续**。如果出现 `lexica-1`，说明第 3 步漏了：删掉多余的记录，
   `tailscale set --hostname=lexica`，再检查一次。
6. 恢复数据库到 `/var/lib/word-puzzle-family/app.db`（属主 `wpfamily`），运行安装脚本，开 Funnel，用手机走流量再测一遍。
7. 确认没问题后再销毁旧容器。

备选做法：把旧容器的 `/var/lib/tailscale/` 整个目录带到新容器（先停掉 `tailscaled` 再放进去），身份完全沿用，
不用重新登录，也不用删记录。**官方文档没有写这种迁移，我没有实测**，所以只当备选；用了以后旧容器必须永久停用。

**4. 每次重启、升级之后检查三件事**

- `tailscale funnel status`：应该仍然只看到 8081 这一条。如果是空的，重新运行 `tailscale funnel --bg 8081`。
  （`--bg` 的配置能不能跨重启保留我没有实测，所以每次都看一眼。）
- `bash /srv/word-puzzle-family/deploy/family/check-url.sh`：输出 `OK 网址一致`。
- 用没装 Tailscale 的手机、走流量打开网址，能看到登录页。

**5. 证书**：不要清空 `/var/lib/tailscale`，证书也缓存在那里。频繁重新申请证书会被 Let's Encrypt 临时限流。

**6. 万一网址还是变了**：账号和成绩都在数据库里，不受影响；但浏览器的登录状态按网址保存，所以学生要用新网址重新登录。
旧网址不会自动跳转（旧名字已经失效），需要把新网址和新二维码重新通知大家。

---

## 十、常见问题

| 现象 | 可能原因和办法 |
|---|---|
| `pct create` 报 `400 not enough arguments` | `$CTID` 是空的（重新登录或换了终端窗口，变量没了）：`echo $CTID` 看一下，空的就重新 `CTID=120`，再运行命令 |
| `pct create` 报 `vmid: type check ('integer') failed - got 'CTID'` | 把 `CTID` 这几个字母当成编号写进了命令。先 `CTID=120`（一个没被占用的数字），命令里写 `$CTID`，见开头 |
| `pct create` 报编号已存在 | 这个编号被虚拟机或容器占了：`qm list; pct list`，换一个 |
| `pct create` 报存储不存在 / 不支持 rootdir | `pvesm status` 看实际的存储名，把 `--rootfs local-lvm:8` 里的 `local-lvm` 换掉；这个存储的 Content 要包含 Container（rootdir） |
| 容器起来了，但 `ping 10.1.1.1` 不通 | 看 `pct config $CTID` 里 `net0` 的 `ip=`、`gw=` 有没有写对，桥是不是 `vmbr0`；地址被别的设备占了会时通时断（`ping` 它看看） |
| 容器里 ping IP 通，ping 域名不通 | 没有 DNS：`pct set $CTID --nameserver 10.1.1.1` 后 `pct reboot $CTID` |
| `tailscale up` 报 `/dev/net/tun` 打不开 | 第二节没生效：确认配置后**重启容器**（`pct reboot $CTID`），再 `ls -l /dev/net/tun` |
| `tailscale up` 一直卡着不出网址 | 容器出不了网：`curl -I https://login.tailscale.com`；检查 `--net0` 的网关和 DNS |
| `tailscale funnel` 提示 Funnel 没开 | 按它给的网址在管理后台批准一次；或者 ACL 里缺 `funnel` 属性 |
| 提示要开 HTTPS | 管理后台 DNS 页开启 HTTPS Certificates |
| 手机打不开，容器里 `curl http://127.0.0.1:8081/...` 正常 | `tailscale funnel status` 看有没有在开；用没装 Tailscale 的设备、走流量测试；等一两分钟（证书和 DNS 刚生效） |
| 反复重装 / 反复开关 Funnel 后打不开 | 证书申请频率过高会被 Let's Encrypt 暂时限流（官方文档提到最长 34 小时），等一等，别再折腾 |
| 过了几个月突然全断 | 多半是密钥过期，回第四节 4.3 |
| 网址突然多了 `-1`，或者名字变了 | 第九节：用 `check-url.sh` 看原因 |

## 十一、安全要点回顾

1. 容器是**非特权**的，里面只有本程序和 Tailscale，没有 SSH，也没有别的网页服务。
2. 对外只有 Funnel 指向的 `127.0.0.1:8081`；后端每个接口都要登录，nginx 挡掉扫描器常探的路径。
3. 宿主机不装本程序、不开 Funnel；PVE 管理界面和 SSH 不要映射到任何地方。
4. 不要在容器（或任何开着 Funnel 的机器）里用 `python3 -m http.server` 做临时测试：它会把当前目录里的所有文件都暴露出去。
5. 学生信息只存学号、姓名、班级、学院、院系和成绩；不存手机号。
