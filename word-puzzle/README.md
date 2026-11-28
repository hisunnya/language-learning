# word-puzzle · 词境 Lexica（网站版）

一个**能部署到 Ubuntu + nginx** 的英语词汇练习网站。

* 内置**人教版 PEP 初中（5 册）+ 高中（7 册）**共 **4791 个词条 / 84 个单元**
* 四级层级选题：学段 → 年级 → 册别 → 单元，**每一级都能自定义名称**
* 能**上传自己的资料**做成题库
* 能把任意题库导出成**单个 HTML 的离线测试页**（双击就能在没网的电脑上玩）
* 界面和玩法沿用原来的 `Unit1单词消消乐.html`，**分数记录**从 localStorage 升级成后端数据库

> **线上现在只有一个实例**（2026-11-21 起）：`/word-puzzle/` 是要登录的版本，`/words/` 是免登录的公开版
> （只有内置初中、高中的中英配对，成绩按浏览器的匿名设备号记录）。四种玩法（中英配对、单词大比拼、翻译排排坐、动词猎手）、
> 积分榜、奖状、多位老师的规则见仓库根目录 `AGENTS.md` §9；接手先读 `docs/交接说明.md`。
> 下面「家庭版」的说明是早期不带登录的本地模式（`./run.sh` 默认就是它），线上已退役。
>
> **学生版**（`WP_AUTH=1`）带登录：学生用学号登录，成绩按人记录；没有自助注册，账号由管理员导入名单创建，
> 初始密码登录后必须先改；管理员可以重置密码、停用、解锁、按班级 / 学院 / 院系导出成绩。
> 通过 Tailscale Funnel 对外，不需要公网 IP、域名和证书。安装和上线检查清单见
> [`deploy/family/部署说明.md`](deploy/family/部署说明.md)，管理命令是 `python3 -m server.admin`
> （安装后用 `sudo wp-family-admin ...`）。两个版本是同一套代码，互不影响。

动词猎手的网站版和离线版每局限时为「12 秒 × 题数」（十题为 2 分钟，熟题另有递减），题序和五个选项随机。拖动或直接点击动词即可填空。
网站开始页只保留一张卡片和一份简要说明，「返回」与「开始游戏」并排显示。
题干在同一个大框内上下排列：英文在上、中文在下，英文使用更大字号，不显示语言标签。
点击「下一题」会自动判分，答错留在当前题，空题可跳过，不再提供单题「提交」或朗读按钮。
末题点「完成答题」，全部答对自动交卷；仍有空题时，可选「直接交卷」或「返回补答」（倒计时不暂停）。
只有进入补答后才显示「交卷」，会先判定当前选择，不必再走到末题；答错留在当前题，全部补答正确则自动交卷。
时间到立即交卷，只计已经判分答对的题。每题 10 分，每次答错扣 2 分，第五次尝试才答对也计 0 分。
结果页标题为「成绩」，英文短语中的正确填空词高亮显示，便于复习。

---

## 一、5 分钟跑起来

服务器上**不需要装任何依赖**，只用 Python 3.8+ 的标准库：

```bash
cd word-puzzle
./run.sh                # → http://127.0.0.1:8000
./run.sh 9000           # 换端口
```

首次运行会自动生成内置词库（`data/pep_curriculum.json`）。
也可以手动跑：

```bash
python3 tools/build_seed_data.py     # 从 data/raw/ 重新生成内置词库
python3 -m server.app --host 0.0.0.0 --port 8000
```

---

## 二、四个页面

| 页面 | 地址 | 干什么 |
| --- | --- | --- |
| 首页 | `/` | 看默认题库、按层级生成题库、列出已有题库 |
| 读音练习 | `/practice.html?bank=<id>` | 单词纵向排列，点哪个读哪个（美式女声，sb. / sth. 念成 somebody / something）；第二列中文默认藏着，点一下或手指 / 鼠标向右滑显示；老师能下载语音内嵌的离线版 |
| 题库工作台 | `/bank.html#banks` `#new` `#offline` | 三个标签页：**当前题库**（分类、标签、批量开放、删除）· **新建题库**（Step 1 词表从哪来 → Step 2 定义题库 → Step 3 开放给谁；含「快速上传并生成」）· **离线测试**（只导出，不新建题库；可选配对游戏或读音练习；离线页里也有五套配色可选，选择会记住）|
| 在线游玩 | `/play.html?bank=<id>` | 玩，成绩写回数据库 |
| 成绩记录 | `/stats.html` | 总览、按题库统计、逐条明细 |

---

## 三、四级层级

| 级 | 选项 | 说明 |
| --- | --- | --- |
| 1 学段 | 小学 / 初中 / 高中 / 大学 / **自定义…** | |
| 2 年级 | 随学段变化：小学 一~六年级、初中 七~九年级、高中 高一~高三、大学 大一~大四 / **自定义…** | |
| 3 册别 | 上册 / 下册 / **全年（上下册，默认）** / **自定义…** | 全年 = 该年级上册 + 下册 |
| 4 单元 | **全部单元** / **分单元** / **第 N 至第 M 单元** / **自定义…** | 「分单元」= 每个单元单独一关，可在首页挑单元开始 |
| — 每关词数 | 4 ~ 40，默认 **12** | 一关最多放多少个词，见下方说明 |

> **词多的单元会拆成多关**：一关最多 9 个词（手机竖屏 3×6 张卡正好一屏）（可在首页改成 4~40 任意整数），
> ``Unit 1`` 词多时会依词数拆成多关，
> 避免几十张卡片挤在一屏。
> 最后一关不足一关容量时，会从**前面出现过的词**里**随机**取词补满一整关（相当于复习），
> 每次生成取到的复习词都不一样；补进来的词在本关里不会重复；这类关卡名字后面会标上「含复习」。
> 同一关里中文或英文相同的词（如 rely / rely on）不会同时出现，多出来的顺延到本单元的下一关，
> 单元末尾还有剩的单独成「补充」关，一个词都不丢。
> 在线玩法和离线测试页用的是同一套拆分。
> 「每关词数」在**生成题库时**确定并存在题库里，以后进同一个题库玩，
> 关卡大小不会变；题库列表里会显示「每关 N 词」。

**每一级都可以自定义名称**：选「自定义…」后会多出一个输入框，填了就用自定义名显示
（取词仍然按原选项走，自定义只是改叫法）。自定义名会出现在题库标题和离线文件名里。

内置词库里：

| 学段 | 册 | 单元 | 词条 |
| --- | ---: | ---: | ---: |
| 初中 七年级 | 上册 / 下册 | 10 / 8 | 382 / 449 |
| 初中 八年级 | 上册 / 下册 | 8 / 8 | 423 / 570 |
| 初中 九年级 | 上册 / 下册 | 7 / 7 | 239 / 201 |
| 高中 高一 | 必修第一册 / 必修第二册 | 6 / 5 | 328 / 368 |
| 高中 高二 | 必修第三册 / 选择性必修第一册 | 5 / 5 | 444 / 370 |
| 高中 高三 | 选择性必修第二册 / 第三册 / 第四册 | 5 / 5 / 5 | 336 / 353 / 328 |

> **默认题库 = 人教版初中九年级上册**（239 词 / 7 单元）。服务启动时自动建好。
>
> 九年级官方教材是「全一册」，本仓库按 Unit 1–7 / Unit 8–14 拆成上下册；
> 划分写在 `data/pep_curriculum.json` 的 `split_note` 里，改 `tools/build_seed_data.py`
> 的 `GRADE9_SPLIT` 就能换一种拆法。

---

## 四、上传资料

题库工作台的「新建题库」标签页，Step 1 选「上传新词表」再选文件即可（或点「快速上传并生成」）。**不需要调用大模型**，全部是本地规则解析。
每次生成题库只使用当前选中的一份上传资料，生成的是独立快照；不同资料不会自动合并，
系统目前也不检查缺了哪些单元。要把上下册放进同一题库，请先整理到同一份文件并标好单元。

### 支持的格式

| 格式 | 写法 | 识别方式 |
| --- | --- | --- |
| **Word** `.docx` | 段落或表格都行；`Unit 3` 单独一行算单元标题 | Python 标准库直接解 zip + 解析 XML |
| **PDF**（文字版） | 文字版 PDF | `pdftotext`（poppler），没装则用内置解析器 |
| **PDF**（图片/扫描版） | 扫描件、截图版 PDF | `pdftoppm` + `tesseract` OCR |
| **TXT** | 每行 `english<TAB>中文`；单独一行 `Unit 3` 会被当作单元标题 | 自动 |
| **CSV / TSV** | 有表头就按表头取（`unit, english, chinese, ipa`）；没表头就按「英文,中文」或「单元,英文,中文」猜 | 自动 |
| **JSON** | `[{"english":"apple","chinese":"苹果"}]`，或 `{"units":[{"unit":"Unit 1","words":[...]}]}` | 自动 |

字段别名都认：`en / eng / english / word`、`cn / zh / chinese / meaning / translation`、
`unit / section / chapter`、`ipa / phonetic`、`pos / partOfSpeech`。

### Word / PDF 的几个注意点

| 情况 | 怎么办 |
| --- | --- |
| `.doc`（老格式） | **不支持**，请在 Word 里「另存为 .docx」再传 |
| `.pdf` 是扫描件 / 图片 | 会自动走 OCR（需要装 `tesseract-ocr`）；文字层有残留但找不到词条时也会强制 OCR，并比较多种版面模式 |
| `.pdf` 是两栏排版 | 内置解析器会按坐标还原列；`pdftotext -layout` 也保留列 |
| 中文释义 + 英文混排一行 | 支持，一行里能拆出多个词条（多列表格） |
| 音标列 | 认 `/.../` 和 `[...]` 两种写法；没写就自动补 |

**提取流程**：`Word/PDF → 纯文本行 → 词条解析 → 音标补全`。
前两步分别是 `server/docx.py` / `server/pdf.py`，第三步是 `server/wordlist.py`
（TXT/CSV/JSON 用的是同一个解析器），最后 `server/ipa.py` 自动补音标。

### 想装 OCR 和更好的 PDF 抽取

```bash
sudo apt install poppler-utils tesseract-ocr tesseract-ocr-eng tesseract-ocr-chi-sim
```

扫描件优先用 `eng+chi_sim`，会尝试常规、整块和稀疏文本版面模式；扫描件必须安装 OCR，
否则只能提示安装依赖。文字版 PDF 即使没有 Poppler，也会尝试内置解析器。

上传后这份资料就能在「题源」里选中，用来生成题库。

---

## 四·五、发音：**美式女声**

站里所有单词的音标和发音都固定为**美式英语**，不会出现英式读法。

### 音标

内置词库 **4791 / 4791 个词条全部带美式音标**（覆盖率 100%）。

数据源是 **CMU Pronouncing Dictionary**（`cmusphinx/cmudict`）——它记录的是**美国发音**，
由 ARPAbet 音素转换成本项目用的 IPA 格式。英式拼写会自动转成美式再查
（`colour → color`、`organise → organize`、`centre → center`），
教材里 CMUdict 没收录的专有名词（`Mount Huangshan`、`La Tomatina` 等）用一张手工表补齐。

```bash
# 重新生成音标表（需要先下载 cmudict）
python3 tools/build_ipa_table.py --cmudict /path/to/cmudict.dict
```

### 发音

| 阶段 | 用什么 | 说明 |
| --- | --- | --- |
| 1（首选） | **Edge Neural TTS**，`en-US-AriaNeural` | 自然度更高的美式神经网络女声；服务器缓存生成的 MP3，在线用户听到同一音色 |
| 2（服务端兜底） | **espeak-ng**，`en-us+f3` | Edge TTS 网络或安装失败时使用本地美式女声 WAV |
| 3（浏览器兜底） | 浏览器自带 TTS | 服务端没有可播放音频时，前端优先挑 `en-US` 女声音色 |

Edge Neural 使用在线语音服务。在线游玩只发送当前点击的英文词；生成离线测试页时，
会发送所选题库的全部英文词来合成音频，并将音频嵌入 HTML。生成后的离线页播放不联网。
在线合成文件按词缓存在 `var/audio/`，重复播放不重复请求。
如 Edge TTS 不可用，服务器自动回退到 `en-us+f3`；填入不支持的 `WP_TTS_VOICE`
会退回 `en-US-AriaNeural`。

```bash
sudo apt install espeak-ng python3-venv  # eSpeak 兜底及 Edge TTS 隔离环境
```

---

## 五、离线测试页

题库工作台的「离线测试」标签页选一个已有的题库，点「生成并下载」；也可以在「当前题库」里对某个题库点「离线页」。

产物是一个**完全自包含的 HTML 文件**：词表、样式、脚本和每个不同英文词的音频全部内嵌，
双击就能玩，播放时不请求网站或语音服务。生成时优先使用 Edge Neural MP3；没有 Edge 时整份使用 eSpeak WAV。
音频会增大文件体积：当前环境用 eSpeak 为九年级上册生成的示例约 **11.5 MB**（239 个词条、238 个不同发音键）；Edge MP3 的实际体积依单词和编码而变。文件名规则：

```
<层级>+<日期>+<时间>.html
例：初中-九年级-上册-全部单元-20261104-015833.html
    初中-九年级-上册-第1至3单元-20261104-015833.html
```

离线页的成绩存在浏览器 `localStorage`（key `wp_offline_scores_v1`），**不会**出现在网站的成绩记录里。

---

## 六、玩法与计分

| 玩法 | 基础分与限时 |
| --- | --- |
| 中英配对 | 每对 20 分，每关 60 秒；配错扣 4 分、3 秒，本轮最低 0 分 |
| 动词猎手 | 每题 10 分，整套限时 `12 × 题数` 秒；错一次扣 2 分，第五次才对得 0 分 |
| 单词大比拼 | 每题 80 分，整套限时 `20 × 题数` 秒、不再选分关；提示扣 24 分、错一次扣 16 分，拼对最低 8 分 |
| 翻译排排坐 | 每句排列 30 秒，排列 30 分（错一次扣 6 分，最低 6 分）；有效录音 20 分、识别准确度整数 0—35 分 |

四种玩法都有首次无提示连续答对的奖励：二至七连分别额外奖励当前题基础分的
10%、20%、40%、60%、80%、100%，更高连击仍封顶 100%。答错、提示或跳过会断连；
同题不能重复领奖。二至四连加 1 秒，五连以上加 2 秒，每轮累计最多
`min(10 秒, 初始时限的 20% 向下取整)`。完整完成本轮时，按剩余时间比例，
再奖励作答及连击分的最多 20%；未完成、白卷没有速度奖。

翻译排列正确后暂停答题计时，可以直接跳过录音；录音界面另有隐藏的 120 秒上限，
避免一直停留，单段录音仍最多 30 秒。上传成功后进入有进度条的「评分中」，
可不等评分先继续，后台准确度会补回原成绩，不另存一条。
评分完成后显示本句成绩，10 秒自动续题；播放标准音或自己的录音期间不跳题，
播放结束后重新等 10 秒。

熟题按同一学生、玩法与固定题组（配对按关、翻译按句）累计**已结算正分轮次**，
跨周不清零；白卷保留记录但不推进次数。第 1—5 / 6—10 / 11—15 / 16 次起，
积分倍率依次为 100% / 75% / 50% / 20%，时限倍率为 100% / 80% / 60% / 40%。
各项得分合计后统一乘积分倍率、只取整一次。开局会显示本轮档位；离线页只计算
当前浏览器的离线练习，不与在线次数合并。
在线熟题次数从新版服务器轮次开始累计；旧版累计快照无法可靠还原练习轮次，不据此追溯次数。

网站每轮由服务器签发标识并校验结算，同标识重交不会重复入账。
配对的上一关、重试前的分数不再反复写入下一次成绩；未完成退出只计本轮已经取得的分，
未开始或超时白卷为 0 分。历史重算保留原记录、录音、时间及原始快照，不伪造旧连击序列，
也不把新的倒计时追溯用于旧成绩；新权重和重复记账修复可能改变名次。

### 历史积分重算

上线不会自动改历史积分。先使用服务账号在数据库副本上预览，确认异常与去重报告后，
再停服务并对实际数据库执行；不要用 root 打开运行中的数据库，以免产生错误属主的 WAL 文件。

```bash
cd word-puzzle
python3 tools/recalculate_scores.py --db /path/to/app.db
python3 tools/recalculate_scores.py --db /path/to/app.db --apply --backup /path/to/before-scoring-v4.db
```

默认只读；`--apply` 先生成一致性备份，再在一个事务中保存原分快照并重算。
规则版本 4 及以后的新成绩不参与转换，同一数据库不能重复应用。
只对证据充分的旧累计明细去重；无法解析的记录保留原分并列出，异常用时也保留并报告，
不猜测当时的真实时间。重算清除待重新结算的榜首日缓存，保留已经颁发的奖状。
应用后重启服务，核对成绩条数、积分汇总、录音和排行榜。

### 点卡顺序：中文先点也行

两种顺序都算数：

* 先点**英文**，再点对应中文 —— 配对成功
* 先点**中文**，再点对应英文 —— 同样配对成功

点英文卡片会朗读单词并高亮；中文卡片只选择，不播放语音。随后点**同一侧的另一张**卡片，
只是换一张选，不算错，并给出提示（“刚选的是中文，再点英文配对”）。
再次点同一张英文卡片会重新朗读。配错（点了另一侧但不是同一个词）仍然扣分扣时间。

底部四个按钮：**玩法** · **全屏** · **重玩本关** · **从头开始**。

---

## 七、架构：运算和存储是分开的

```
web/js/game-core.js        纯运算：关卡 / 计分 / 计时 / 连击。不碰 DOM、不碰网络
web/js/game-ui.js          纯界面：把 core 的状态画出来、播特效。不算分
web/js/game-adapter-*.js   存储适配：online 写后端 / offline 写 localStorage
web/js/selector.js         四级层级选择器
server/scoring.py          在线轮次、熟题倍率和服务端权威结算
```

同一份 `game-core.js` + `game-ui.js`：

* 在线页面用 `<script src>` 引用，先通过 `POST /api/plays/start` 申请轮次，
  每次作答通过 `POST /api/plays/progress` 保存截止前快照，再把最终明细交给
  `POST /api/scores`；进度、阶段切换及结算按顺序发送。服务器重算，不能直接采用页面报的总分
* 离线页面由 `server/offline.py` **把它们内联进单个 HTML**，成绩走 localStorage

离线页复用同一套玩法与计分公式；离线次数按本地浏览器累计，在线次数与成绩由服务器管理。

后端：

```
server/app.py        HTTP 服务（标准库 http.server）+ 路由
server/db.py         SQLite 数据层（materials / banks / bank_words / scores）
server/hierarchy.py  四级层级模型 + 内置词库读取
server/materials.py  上传资料解析（TXT / CSV / TSV / JSON）
server/bank.py       题库生成（层级 + 单元范围 + 自定义名）
server/offline.py    单文件离线测试页生成
```

---

## 八、数据库

SQLite（Python 标准库自带，**免费、开源、零运维**），默认在 `var/app.db`：

| 表 | 内容 |
| --- | --- |
| `materials` / `material_words` | 上传的资料及其词条 |
| `banks` / `bank_words` | 生成的题库及其词条 |
| `scores` | 成绩记录（含每关明细 JSON） |

> 用户建的题库是**快照**：内置词库更新后，已有的题库不会跟着变；
> 只有系统默认题库会在检测到词库指纹变化时自动重建。

---

## 九、部署到 Ubuntu + nginx

```bash
sudo bash ./deploy/check-deps.sh
sudo env WP_SERVER_NAME=<开发机IP> ./deploy/install.sh
```

依赖检查会逐个核对 Python、nginx、systemd、PDF/OCR 和语音组件；已安装的包会跳过，
缺少的包才通过 apt 安装。部署脚本也会自动先跑同一个检查。

部署脚本会：建 `wordpuzzle` 系统用户
→ 代码放到 `/srv/word-puzzle` → 数据目录 `/var/lib/word-puzzle` → 生成内置词库
→ 装并启动 systemd 服务 → 将 nginx 配置写入 `/etc/nginx/conf.d/word-puzzle.conf`。

`WP_SERVER_NAME` 用于指定 nginx 主机名；上例让首页通过 `http://<开发机IP>/` 访问。
如果词境要作为语林总主页的子项目，完成后再运行 `sudo env LINGUA_SERVER_NAME=<开发机IP> bash hub/deploy/install.sh`，
由总主页在 `/word-puzzle/` 提供词境前端并转发 API。

可选工具装不上（离线机器）也不影响网站运行，只是：
PDF 走内置解析器、扫描件读不了、发音走浏览器自带 TTS。

手动部署的话：

```bash
# 1. 后端
sudo cp -r word-puzzle /srv/word-puzzle
sudo useradd --system wordpuzzle
sudo mkdir -p /var/lib/word-puzzle && sudo chown wordpuzzle /var/lib/word-puzzle
sudo cp deploy/systemd/word-puzzle.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now word-puzzle

# 2. nginx
sudo install -d /etc/nginx/conf.d
sudo sed 's/word-puzzle.example.com/你的域名/' deploy/nginx/word-puzzle.conf \
    | sudo tee /etc/nginx/conf.d/word-puzzle.conf >/dev/null
sudo nginx -t && sudo systemctl reload nginx
```

nginx 做的事：**静态文件直接托管**，`/api/` 反代给后端（默认 `127.0.0.1:8765`）。
生产环境记得：

* `server_name` 换成真实域名或 IP
* 上 HTTPS（`certbot --nginx`）
* `client_max_body_size` 已设 32m，够上传词表

---

## 十、API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查 |
| GET | `/api/meta` | 层级元数据 + 内置词库统计 + 音标/OCR/语音能力自检 |
| GET | `/api/terms?level1=&level2=` | 某年级的册别选项 |
| GET | `/api/units?level1=&level2=&level3=` | 某册别的单元列表 |
| GET | `/api/materials` | 资料列表 |
| POST | `/api/materials` | 上传资料（multipart，字段名 `file`） |
| DELETE | `/api/materials/<id>` | 删除资料 |
| GET | `/api/banks` | 题库列表 |
| POST | `/api/banks` | 生成题库（body 是层级选择） |
| GET | `/api/banks/<id>` | 题库内容（游戏用） |
| DELETE | `/api/banks/<id>` | 删除题库 |
| POST | `/api/banks/<id>/offline` | 生成离线单文件页：`{"kind":"game"}`（默认，配对游戏）或 `{"kind":"practice"}`（读音练习）；语音都内嵌 |
| GET / POST | `/api/recent` | 首页「最近玩过」：按账号存在服务器上（换设备也看得到），只给现在还看得到的题库；没登录的访客返回 `device_only`，页面改用本机记录 |
| GET | `/api/offline` | 已生成的离线文件列表 |
| GET | `/api/offline/<文件名>` | 下载（加 `?inline=1` 直接在浏览器里预览） |
| GET | `/api/scores?limit=&bank_id=` | 成绩列表 + 统计 |
| POST | `/api/scores` | 写成绩 |
| GET | `/api/stats` | 成绩统计 |
| GET | `/api/audio/<word>` | 单词发音（WAV，美式女声 espeak-ng 渲染） |

---

## 十一、目录结构

```
word-puzzle/
├── README.md
├── run.sh                        # 一键起本地服务
├── deploy/
│   ├── install.sh                # Ubuntu 一键部署
│   ├── nginx/word-puzzle.conf
│   └── systemd/word-puzzle.service
├── server/                       # 后端（纯标准库）
│   ├── app.py  db.py  hierarchy.py  materials.py  bank.py  offline.py
│   ├── ipa.py                    # 美式音标（CMUdict ARPAbet → IPA + 英式→美式 + 专名）
│   ├── tts.py                   # 美式女声发音（Edge Neural + eSpeak 兜底 + 缓存）
│   ├── docx.py                  # Word 解析（zipfile + ElementTree）
│   ├── pdf.py                   # PDF 解析（pdftotext / 内置解析器 / OCR）
│   └── wordlist.py              # 通用词表解析（TXT/CSV/JSON/DOCX/PDF 共用）
├── web/                          # 前端（静态，nginx 直接托管）
│   ├── index.html  bank.html  play.html  stats.html
│   ├── css/{app,game}.css
│   └── js/{api,selector,game-core,game-ui,game-adapter-online,game-adapter-offline,page-*}.js
├── data/
│   ├── pep_curriculum.json       # 内置词库（生成物，已入库）
│   └── raw/                      # 原始词表（脚本输入）+ us_ipa.tsv 美式音标表
├── tools/
│   ├── build_seed_data.py        # 生成内置词库
│   ├── build_ipa_table.py        # 从 cmudict 生成美式音标表
│   └── check_js.py               # JS 语法体检
├── tests/test_server.py          # 后端测试（38 个）
├── var/                          # 运行期数据（已 gitignore）
│   ├── app.db
│   ├── audio/                    # 缓存的发音 WAV
│   └── offline/                  # 生成的离线测试页
└── Unit1单词消消乐.html           # 原始单文件版（保留，这是改名之前的老文件名）
```

---

## 十二、内置词库的来源

| 学段 | 来源仓库 | 备注 |
| --- | --- | --- |
| 初中 | [`henry1786580051-lang/english-test`](https://github.com/henry1786580051-lang/english-test) `src/data/grade*.json` | 整理自人教版课本，参考 [`TapXWorld/ChinaTextbook`](https://github.com/TapXWorld/ChinaTextbook) 的教材数据 |
| 高中 | [`lfcypo/pep-senior-eng-vocab-json`](https://github.com/lfcypo/pep-senior-eng-vocab-json) `vocabulary.json` | 人教版普通高中英语新教材七册 |
| 音标 | [`cmusphinx/cmudict`](https://github.com/cmusphinx/cmudict) | **美式发音**（CMUdict 记录的是美国读音），ARPAbet → IPA 转换 |

原始文件都放在 `data/raw/` 里，`tools/build_seed_data.py` 只做整理、不联网。
音标表是生成物 `data/raw/us_ipa.tsv`（12.6 万条），已入库。

想重新生成音标表：

```bash
curl -sSL https://raw.githubusercontent.com/cmusphinx/cmudict/master/cmudict.dict \
     -o /tmp/cmudict.dict
python3 tools/build_ipa_table.py --cmudict /tmp/cmudict.dict
python3 tools/build_seed_data.py
```

> 课本原始内容版权归**人民教育出版社**所有；本仓库仅用于个人学习。

---

## 十三、测试

```bash
python3 -m unittest discover -s tests -v    # 后端 38 个用例
python3 tools/check_js.py                   # 前端 JS 语法体检
```

---

## 十四、原来的单文件版

`Unit1单词消消乐.html`（新视野大学英语 Unit 1，54 词）**保持原样保留**，依然可以双击直接玩，
配套的课堂投屏版 PPTX 和使用说明 PDF 也都在。

> 文件名里的「消消乐」是改名之前的老叫法。这个产品现在叫「**词境 Lexica**」，
> 但文件本身、PPTX 和 PDF 都是历史资料，保持原样不再改名。

现在网站版的界面和玩法是从它拆出来的（`web/css/game.css` 就是它的样式），
两边共用同一套 `game-core.js` / `game-ui.js`。
