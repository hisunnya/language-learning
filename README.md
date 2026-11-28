# language-learning · 词境 Lexica

「词境 Lexica」学习网站：一个总主页 + 六个模块。模块互相独立，各自都能单独跑起来；线上整站由一个容器提供（见下文「生产部署」）。

> **接手这个仓库？先读 [`docs/交接说明.md`](docs/交接说明.md)**（架构、目录、怎么测试、怎么部署、私有文件、未完成的事），
> 再读 [`AGENTS.md`](AGENTS.md)（必须遵守的约定：双语、配色、测试、提交、隐私）。

| 项目 | 内容 | 技术栈 |
| --- | --- | --- |
| [`hub/`](hub/) | **词境 Lexica** 网站主页（原「语林」）：六个模块的入口、隐私说明、全站页脚（备案号），中英双语 + 五套配色 | 纯静态 HTML/CSS/JS |
| [`word-puzzle/`](word-puzzle/) | **词境 Lexica**：英语词汇游戏。四种玩法——中英配对、单词大比拼（拼写）、翻译排排坐（连词成句 + 朗读录音 + 本地语音识别）、动词猎手（拖动动词填空）；人教版 PEP 初中 + 高中内置词库；老师（多租户）管理学生、题库、标签；成绩、访问记录、积分榜（周榜）、奖状徽章；单文件离线页；`/word-puzzle/` 要登录，`/words/` 是免登录的公开版（只有初中、高中配对） | Python 标准库 + SQLite + 原生 JS（无构建），nginx |
| [`topic-app/`](topic-app/) | **每日话题 Daily Topics**：适合初中水平的家庭话题讨论，随机抽题 + 参考方向 + 历史记录 | 纯前端，零依赖，localStorage |
| [`ham-exam/`](ham-exam/) | **无线电执照 Ham Exam**：业余无线电台操作技术能力验证 · 模拟考试系统（1375 道真题题库） | 纯前端，零依赖，localStorage |
| [`chemistry/`](chemistry/) | **化学探秘 Chem Quest**：初中元素配对、高中反应配平、大学溶液推理；选择、数值填空、配对、排序、找错七种题型 | 纯前端，零依赖，localStorage |
| [`nvidia-exam/`](nvidia-exam/) | **NVIDIA 认证模拟考试 NVIDIA Exam**：NCA-AIIO（AI 基础设施与运维）模拟考试，按官方大纲三知识域比例组卷、计时答题卡、错题本；中英双语题库 | 纯前端，零依赖，localStorage |
| [`physics/`](physics/) | **物理探秘 Phys Quest**：初中量与单位、高中公式速算、大学概念辨析；公式题参数化出题，错误选项来自典型错误；选择、数值填空、配对、量级排序、找错七种题型，答完附解题步骤 | 纯前端，零依赖，localStorage |

> 产品现在叫**词境 Lexica**，目录名 `word-puzzle/` 保持不变（改了会打断服务器上
> 已经部署好的 systemd、nginx 和路径）。

---

## 快速开始

```bash
# hub（总主页，纯静态）
cd hub && python3 -m http.server 8080     # → http://127.0.0.1:8080

# word-puzzle · 词境 Lexica（网站版）
cd word-puzzle && ./run.sh                # → http://127.0.0.1:8000

# topic-app · 每日话题（纯前端）
cd topic-app/topic-app && python3 -m http.server 8081

# ham-exam（纯前端）
cd ham-exam && ./start.sh                 # → http://127.0.0.1:8080

cd chemistry && python3 -m http.server 8082 # → http://127.0.0.1:8082
cd physics   && python3 -m http.server 8083 # → http://127.0.0.1:8083
cd nvidia-exam && python3 -m http.server 8084 # → http://127.0.0.1:8084
```

---

## 目录结构

```
language-learning/
├── README.md
├── AGENTS.md                               # 仓库级约定（给人和给 AI 看的）
├── .gitignore
├── hub/                                   # 网站主页「词境 Lexica」（原「语林」）
│   ├── index.html                         # 三件工具的入口
│   ├── css/hub.css                        # 五套配色（[data-theme]）
│   ├── js/hub.js                          # 中英切换 + 配色切换
│   ├── js/config.js                       # 三个子站的地址（部署时改这里）
│   ├── deploy/                            # nginx 配置、整体部署脚本 + 部署说明
│   └── tests/test_hub.py                  # 样式规范测试
├── word-puzzle/                           # 词境 Lexica（网站版）
│   ├── README.md                          # 详细文档
│   ├── run.sh                              # 一键起本地服务
│   ├── deploy/                             # Ubuntu 部署
│   │   ├── install.sh
│   │   ├── nginx/word-puzzle.conf
│   │   └── systemd/word-puzzle.service
│   ├── server/                             # 后端（Python 标准库，无第三方依赖）
│   │   ├── app.py                          # HTTP 服务 + 路由
│   │   ├── db.py                           # SQLite 数据层
│   │   ├── hierarchy.py                    # 四级层级模型
│   │   ├── materials.py                    # 上传资料解析
│   │   ├── bank.py                         # 题库生成
│   │   ├── offline.py                      # 单文件离线页生成
│   │   ├── ipa.py                          # 美式音标（CMUdict ARPAbet → IPA）
│   │   ├── tts.py                          # 美式女声发音（espeak-ng en-us+f3）
│   │   ├── docx.py                         # Word 解析
│   │   ├── pdf.py                          # PDF 解析（文字版 + OCR）
│   │   └── wordlist.py                     # 通用词表解析
│   ├── web/                                # 前端（静态，nginx 直接托管）
│   │   ├── index.html  bank.html  play.html  stats.html
│   │   ├── css/{app,game}.css
│   │   └── js/*.js
│   ├── data/
│   │   ├── pep_curriculum.json             # 内置词库（4791 词 / 84 单元）
│   │   └── raw/                            # 原始词表 + us_ipa.tsv 美式音标表
│   ├── tools/{build_seed_data.py,build_ipa_table.py,check_js.py}
│   ├── tests/                              # 后端测试
│   ├── var/                                # 运行期数据（gitignore）
│   ├── Unit1单词消消乐.html                # 原始单文件版（保留，老文件名）
│   ├── Unit1单词消消乐-课堂投屏版 .pptx
│   └── Unit1单词消消乐-使用说明.pdf
├── topic-app/                              # 每日话题 Daily Topics
│   ├── topic-app/                          # 站点根目录
│   │   ├── index.html  app.js  styles.css  topics.js  favicon.svg
│   ├── 初中生每日话题.xlsx                  # 原始话题库
│   ├── make_topics.py                      # 从 Excel 生成 topics.js
│   └── 部署说明.md                          # nginx 配置
├── ham-exam/
    ├── README.md
    ├── index.html                          # 入口
    ├── start.sh / start.bat                # 一键起本地服务
    ├── css/style.css                       # 样式（含深色模式）
    ├── js/{app.js,store.js}                # 应用逻辑 / localStorage 数据层
    ├── data/{bank.js,bank.json}            # 题库（两份内容完全一致）
    ├── images/                             # 53 张电路附图
    └── tools/                              # 题库生成脚本（从官方 PDF 生成 bank.json）
  ├── chemistry/                              # 化学探秘 Chem Quest（纯静态分龄练习）
  ├── physics/                                # 物理探秘 Phys Quest（纯静态分龄练习）
  └── nvidia-exam/                            # NVIDIA 认证模拟考试（NCA-AIIO，纯静态）
```

---

# 一、hub · 词境 Lexica（网站主页，原「语林」）

## 是什么

五个工具的入口页。纯静态，没有任何后端依赖，扔进 nginx 就能用。

| 特性 | 说明 |
| --- | --- |
| 三件工具的入口 | 词境 Lexica / 每日话题 / 无线电执照 |
| 中英双语 | 右上角一键切换，选择记在 `localStorage` 里 |
| 五套配色 | 靛蓝·雪白 / 墨绿·玄夜 / 琥珀·米白 / 绯红·藕白 / 鎏金·曜黑 |
| 对角切半色块 | 配色选择器是小方块，右上主色、左下底色，硬边 `linear-gradient` |
| 样式有测试 | `hub/tests/test_hub.py` 守住双语和配色的约定 |

三个子站的地址写在 `hub/js/config.js` 里。默认 hub 在 80 端口，
词境 Lexica、每日话题和无线电执照分别挂在 `/word-puzzle/`、`/topics/`、`/ham/`。

部署说明见 [`hub/deploy/部署说明.md`](hub/deploy/部署说明.md)。

## 生产部署（整站）

线上整站（主页、四个静态模块、词境登录版和公开版）都在 PVE 宿主机上的一个 LXC 容器里，宿主机只做转发。
在宿主机的仓库检出目录里（root），按这个顺序：

```bash
bash ./pre-deploy.sh                 # 先备份：容器里已安装的代码和数据库，打印回滚命令（要在 git pull 之前）
git pull
bash ./deploy-all-<时间戳>.sh         # 仓库根目录下只有一个 deploy-all-*.sh，每次提交都会改名
```

deploy-all 把整站打包推进容器、在容器里运行 `word-puzzle/deploy/family/install.sh`（装依赖、同步代码、
systemd、nginx、健康检查），再更新宿主机的转发；数据库在容器外的目录里，部署不会动它。
服务器地址、容器编号、对外网址这些私有值不进仓库（仓库是公开的），写在检出目录里不进 git 的
`deploy.local.env`（从 `deploy.local.env.example` 复制）：`LINGUA_SERVER_NAME`、`LEXICA_UPSTREAM`、
`LEXICA_CTID`、`LEXICA_PUBLIC_URL`。细节见 `AGENTS.md` §5.2 和 [`docs/交接说明.md`](docs/交接说明.md)。

---

# 二、word-puzzle · 词境 Lexica（网站版）

## 是什么

一个能部署到 **Ubuntu + nginx** 的英语词汇练习网站。

内置**人教版 PEP 初中（5 本教材，九年级拆分上下册）+ 高中（7 册）**，
共 **4791 个词条 / 84 个单元**；四级选题为**学段 → 年级 → 册别 → 单元**。
这里收集的是教材词汇表，不是整本课文正文；来源数据已随仓库提供，部署时不联网抓取。

| 特性 | 说明 |
| --- | --- |
| 四级层级 | 学段（小学/初中/高中/大学）→ 年级 → 册别（上册 / 下册 / 全年〔上下册〕）→ 单元 |
| 自定义命名 | 每一级都能填自己的名字，自定义名会进题库标题和离线文件名 |
| 上传资料 | TXT / CSV / TSV / JSON / **Word (.docx)** / **PDF（含扫描件 OCR）**，自动识别表头、单元列、中英文列 |
| 美式女声发音 | 音标来自 CMUdict（美式），朗读用 espeak-ng `en-us+f3`（女声） |
| 默认题库 | **人教版初中九年级上册**（239 词 / 7 单元），启动时自动建好 |
| 离线测试页 | 任意题库一键导出成**单个自包含 HTML**，文件名 `层级+日期+时间.html` |
| 分数入库 | 在线成绩写 SQLite；离线页成绩写浏览器 localStorage |
| 零依赖 | 后端只用 Python 标准库，数据库用 SQLite，服务器上不用 `pip install` |

完整文档见 [`word-puzzle/README.md`](word-puzzle/README.md)。

## 界面

沿用原来的 `Unit1单词消消乐.html` 的样式和玩法：点一张卡片听发音 → 点另一侧的对应卡片配对成功。

| 项目 | 规则 |
| --- | --- |
| 每关限时 | 60 秒，上一关剩余时间越多下一关时间越长，最多 80 秒 |
| 每关词数 | 默认 9 个词，生成题库时可改成 4~40；词多的单元自动拆成多关（``Unit 1（1/3）``），不足的关用前面学过的词补齐 |
| 点卡顺序 | 中文先点、英文先点都行；连点同一侧只是换一张选，不算错并有提示 |
| 配对得分 | 每对 +50 分（2026-11-21 起减半，历史成绩也按比例减半） |
| 连击奖励 | 连续配对每多一次 +10 分，最高 +50 分 |
| 配错惩罚 | 扣 3 秒、扣 10 分，连击清零 |
| 过关奖励 | 剩余每秒折算 5 分 |

另外两种玩法（单词大比拼、排排坐）的规则和计分见 `AGENTS.md` §9.3。

## 运算与存储分离

```
game-core.js        纯运算（关卡/计分/计时/连击），不碰 DOM、不碰网络
game-ui.js          纯界面，只把 core 的状态画出来
game-adapter-*.js   存储适配：online 走后端 / offline 写 localStorage
```

在线页面用 `<script src>` 引用这两个文件，离线页由 `server/offline.py` 把它们**内联进单个 HTML**，
所以离线页和在线页玩法、分数完全一致。

---

# 三、topic-app · 每日话题 Daily Topics

## 是什么

一个按**初中、高中、大学**分龄的话题讨论工具：选择适合的集合，随机抽题并沿「参考方向」展开交流。默认选中初中生话题集；纯前端，数据在浏览器 localStorage 里。

| 特性 | 说明 |
| --- | --- |
| 分类抽题 | 个人与自我 / 学习与成长 / 家庭与朋友 / 社会与未来 等分类 |
| 参考方向 | 每个话题附带几个追问方向，攒积分可以看 |
| 历史记录 | 已经聊过哪些话题一目了然，不会重复 |
| 积分 | 结束讨论加分，看提示扣分 |
| 零依赖 | 没有后端，任意静态服务器都能跑 |

共 303 个话题：原有 213 条初中话题、补充 30 条初中话题，以及高中和大学各 30 条。原始初中话题库是 `初中生每日话题.xlsx`，补充分龄话题在 `topic-app/supplemental_topics.js`。
部署说明见 [`topic-app/部署说明.md`](topic-app/部署说明.md)。

---

# 四、ham-exam · 无线电执照 Ham Exam

## 是什么

一个**纯本地**的刷题网站：打开就能用，不联网、不登录、不需要数据库。题库来自《业余无线电台操作技术能力验证题库（2025 年版）》，题量与官方完全一致。

| 类别 | 题量 | 其中单选 | 其中多选 | 附图题 | 知识点 |
|---|---:|---:|---:|---:|---:|
| A 类 | 683 | 547 | 136 | 1 | 51 |
| B 类 | 1143 | 947 | 196 | 24 | 95 |
| C 类 | 1282 | 1072 | 210 | 53 | 104 |

合并去重后共 **1375** 道题、**112** 个知识点。

## 四个视图

| 模块 | 说明 |
| --- | --- |
| **模拟考试** | 规则与正式考试一致：A 类 40 题/40 分钟、B 类 60 题/60 分钟、C 类 90 题/90 分钟；随机抽题、题序打乱、倒计时自动交卷、答题卡跳题、未答按错计、多选必须与标准答案完全一致才得分 |
| **练习模式** | 不限时，答完立即给答案 + 解析；题量 10/20/30/50/不限；范围可限定单选/多选/附图/错题/未做过/收藏/某知识点 |
| **题库** | 左侧知识点目录树（5 部分 / 29 二级 / 112 三级），右侧逐题浏览；全文搜索；逐题收藏 |
| **统计** | 总览、112 个知识点掌握度、模拟考试记录、错题本 |

数据全部在**自己浏览器的 localStorage**，键名 `ham_exam_data_v1`。不上传、不联网、无服务端。

完整文档见 [`ham-exam/README.md`](ham-exam/README.md)。
---

# 五、nvidia-exam · NVIDIA 认证模拟考试

## 是什么

NCA-AIIO（NVIDIA Certified Associate: AI Infrastructure and Operations）模拟考试，纯本地刷题网站。题库按 NVIDIA 官方公开考试大纲生成（当前 60 道种子题，可随时补充，**不是真题**），三个知识域按权重出题：

| 知识域 | 权重 | 种子题量 |
|---|---:|---:|
| Essential AI Knowledge | 38% | 23 |
| AI Infrastructure | 40% | 24 |
| AI Operations | 22% | 13 |

四个视图：**模拟考试**（10/20/60 题可选，倒计时、答题卡、及格线 70%、逐题复盘）、**练习**（即时反馈 + 解析）、**题库**（筛选 + 搜索）、**统计**（分知识域正确率 + 错题本）。题目中英双语，语言与配色偏好和 hub 全站共享。

数据在自己浏览器的 localStorage（`nx_state`），不上传、无服务端。

完整文档见 [`nvidia-exam/README.md`](nvidia-exam/README.md)。

---

## 维护记录

### 2026-11-25 — 新增 nvidia-exam

* 新增 `nvidia-exam/`：NCA-AIIO 模拟考试，60 道按官方大纲生成的双语种子题，
  模拟考试 / 练习 / 题库 / 统计四模块，错题本与考试历史存 localStorage；
* 中英双语 + 五套配色（与 hub 同键），色块取色器沿用 house style；
* `nvidia-exam/tests/test_nvidia_exam.py` 守住 §3 约定与题库完整性，
  `word-puzzle/tools/check_js.py` 纳入 `nvidia-exam/js` 与 `nvidia-exam/data`。

### 2026-11-04 — 加了总主页，改了名字

* 新增 `hub/`：语林 Lingua Grove 总主页，中英双语 + 五套配色 + 对角切半色块，
  配 `hub/tests/test_hub.py` 守住样式约定
* 「单词消消乐」正式改名为「**词境 Lexica**」（目录名 `word-puzzle/` 不动）
* `AGENTS.md` 重写：删掉原来的网络/服务器章节，换成家庭网络和生产机（PVE + nginx）的说明

### 2026-11-04 — word-puzzle 改造成网站

* 新增 `word-puzzle/server/`（Python 标准库 HTTP 服务 + SQLite）、`word-puzzle/web/`（四个页面）、
  `word-puzzle/deploy/`（nginx + systemd + 一键安装脚本）、`word-puzzle/tools/`、`word-puzzle/tests/`
* 内置人教版 PEP 初中 5 册 + 高中 7 册，共 4791 词条 / 84 单元
* 原单文件版拆成 `game-core.js`（运算）/ `game-ui.js`（界面）/ `game-adapter-*.js`（存储），
  在线页和离线页共用同一份代码
* 保留 `Unit1单词消消乐.html`、课堂投屏版 PPTX、使用说明 PDF 原样不动

### 2026-11-04 — 词表释义错误修复（ham-exam 同批）

第 1 关 `faulty` 词条的释义曾被误填成 faculty 的（"全体教员"），已修正为"有缺陷的；有毛病的；错误的"。
