# 在 PVE 里用容器跑「词境 家庭版」+ Tailscale Funnel

目标：**家庭版只跑在一个独立的 LXC 容器里**，容器里装本程序和 Tailscale，由 Funnel 对外。
PVE 宿主机（管理界面、SSH、其他虚拟机）不在对外的路径上。

```
学生手机 --HTTPS--> Tailscale Funnel --> [LXC 容器 lexica]
                                           tailscaled
                                           nginx 127.0.0.1:8081 --> 后端 127.0.0.1:8766
PVE 宿主机 pve03：只负责跑这个容器，不装本程序，不开 Funnel
```

下面的命令分两处执行：标「宿主机」的在 PVE 宿主机上（root），标「容器内」的在容器里（用 `pct enter 容器号` 进去，不需要密码，**也不要给容器开 SSH**）。
文中 `CTID` 是容器编号（例如 120），换成你自己的。

> 版本说明：宿主机是 PVE 9（Debian 13）。Tailscale 官方给的容器配置针对 PVE 7 及以上（cgroup2），
> 本文照这个写；个别命令的参数以你机器上的 `pct help create`、`tailscale funnel --help` 为准。

---

## 一、创建容器（宿主机）

```bash
pveam update
pveam available --section system | grep debian-13        # 找到 Debian 13 的模板名
pveam download local <上一步看到的模板文件名>

pct create CTID local:vztmpl/<模板文件名> \
  --hostname lexica \
  --unprivileged 1 \
  --features nesting=1,keyctl=1 \
  --cores 1 --memory 1024 --swap 512 \
  --rootfs local-lvm:8 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --onboot 1 --start 0
```

- **一定要非特权容器**（`--unprivileged 1`）：容器里即使被攻破，也只是宿主机上一个没有权限的普通用户。
- `--rootfs local-lvm:8` 里的存储名换成你自己的（`pvesm status` 能看到），8 GB 足够。
- `--net0` 用 DHCP 即可；想固定地址就写 `ip=10.1.1.xx/24,gw=10.1.1.1`。
- 不用设 root 密码，也不要装 SSH，需要进去时在宿主机上 `pct enter CTID`。

## 二、给容器放行 TUN 设备（宿主机）

Tailscale 需要 `/dev/net/tun`。官方给了两种办法，二选一：

```bash
# 办法 A：pct 的设备直通（官方也列为可选方式）
pct set CTID --dev0 /dev/net/tun
```

```bash
# 办法 B：直接改配置文件（PVE 7 及以上）
cat >> /etc/pve/lxc/CTID.conf <<'CONF'
lxc.cgroup2.devices.allow: c 10:200 rwm
lxc.mount.entry: /dev/net/tun dev/net/tun none bind,create=file
CONF
```

然后启动容器：`pct start CTID`，进去确认设备在：`pct enter CTID` → `ls -l /dev/net/tun`。

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

**4.4 记下完整网址：** 形如 `https://lexica.<你的tailnet名>.ts.net`（管理后台的 Machines 页或
`tailscale status --json` 里的 `DNSName`，去掉末尾的点）。下面叫它 `WP_PUBLIC_URL`。

## 五、把代码放进容器并安装（宿主机 + 容器内）

容器里没有仓库时，从宿主机上的检出目录（`/root/language-learning`）推进去，只需要两个目录：

```bash
# 宿主机
cd /root/language-learning && git pull
tar czf /tmp/lexica-src.tgz --exclude='word-puzzle/var' --exclude='__pycache__' --exclude='.DS_Store' \
    word-puzzle hub/shared
pct push CTID /tmp/lexica-src.tgz /root/lexica-src.tgz
pct exec CTID -- mkdir -p /root/language-learning
pct exec CTID -- tar xzf /root/lexica-src.tgz -C /root/language-learning
```

然后在容器里安装（会装 nginx、Python 环境、语音等依赖，要几分钟）：

```bash
# 容器内
cd /root/language-learning
env WP_PUBLIC_URL=https://lexica.<你的tailnet名>.ts.net bash word-puzzle/deploy/family/install.sh
```

脚本最后会自检：未登录访问接口必须返回 401，不通过就报错退出。

创建管理员、导入名单（容器内）：

```bash
wp-family-admin create-admin 你的工号 --name 你的名字
# 名单文件从宿主机推进来：pct push CTID /路径/名单.xlsx /tmp/名单.xlsx
wp-family-admin import /tmp/名单.xlsx --out /tmp/初始密码.csv
# 把初始密码清单取出来发给学生，然后删掉（明文）：
#   宿主机： pct pull CTID /tmp/初始密码.csv ./初始密码.csv
#   容器内： rm /tmp/初始密码.csv /tmp/名单.xlsx
```

## 六、上线前检查，然后开 Funnel（容器内）

先对照 `部署说明.md` 第四节的检查清单，再加这几条容器特有的：

- [ ] `ss -ltnp` 里除了 tailscaled，只有 `127.0.0.1:8081`（nginx）和 `127.0.0.1:8766`（后端）在监听
- [ ] `curl http://127.0.0.1:8081/word-puzzle/api/banks` 返回 401
- [ ] 管理员已创建，能登录并看到「账号管理」
- [ ] Machines 页里 `lexica` 显示 **Key expiry disabled**

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
  `vzdump CTID --storage <备份存储> --mode snapshot --compress zstd`。
  备份里有学生的学号、姓名、成绩和密码哈希，**也包含这台机器在 Tailscale 里的身份**，要妥善保管；
  还原到别处时，不要让原容器和还原出来的副本同时在线（两个同身份的节点会互相抢）。
  数据库本身也可以在容器里 `sqlite3 /var/lib/word-puzzle-family/app.db ".backup '/tmp/app.db'"` 单独备份。
- **更新程序：** 宿主机 `git pull` → 重新打包推进去 → 容器里重新运行第五节的安装命令。数据库不会被覆盖。
- **更新系统和 Tailscale：** 容器里定期 `apt-get update && apt-get -y upgrade`。
- **日志：** `journalctl -u word-puzzle-family`；nginx 的在 `/var/log/nginx/word-puzzle-family.*.log`。
- **资源：** 100 多个学生，1 核 1 GB 足够；上课时同时在线的人多了再看 `top`。

## 九、常见问题

| 现象 | 可能原因和办法 |
|---|---|
| `tailscale up` 报 `/dev/net/tun` 打不开 | 第二节没生效：确认配置后**重启容器**（`pct reboot CTID`），再 `ls -l /dev/net/tun` |
| `tailscale up` 一直卡着不出网址 | 容器出不了网：`curl -I https://login.tailscale.com`；检查 `--net0` 的网关和 DNS |
| `tailscale funnel` 提示 Funnel 没开 | 按它给的网址在管理后台批准一次；或者 ACL 里缺 `funnel` 属性 |
| 提示要开 HTTPS | 管理后台 DNS 页开启 HTTPS Certificates |
| 手机打不开，容器里 `curl http://127.0.0.1:8081/...` 正常 | `tailscale funnel status` 看有没有在开；用没装 Tailscale 的设备、走流量测试；等一两分钟（证书和 DNS 刚生效） |
| 反复重装 / 反复开关 Funnel 后打不开 | 证书申请频率过高会被 Let's Encrypt 暂时限流（官方文档提到最长 34 小时），等一等，别再折腾 |
| 过了几个月突然全断 | 多半是密钥过期，回第四节 4.3 |

## 十、安全要点回顾

1. 容器是**非特权**的，里面只有本程序和 Tailscale，没有 SSH，也没有别的网页服务。
2. 对外只有 Funnel 指向的 `127.0.0.1:8081`；后端每个接口都要登录，nginx 挡掉扫描器常探的路径。
3. 宿主机不装本程序、不开 Funnel；PVE 管理界面和 SSH 不要映射到任何地方。
4. 不要在容器（或任何开着 Funnel 的机器）里用 `python3 -m http.server` 做临时测试：它会把当前目录里的所有文件都暴露出去。
5. 学生信息只存学号、姓名、班级、学院、院系和成绩；不存手机号。
