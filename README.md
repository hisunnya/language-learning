# language-learning · 语林 Lingua Grove

家庭学习工具集。四个项目互相独立，各自都能单独跑起来，另有一个总主页把它们串起来。

| 项目 | 内容 | 技术栈 |
| --- | --- | --- |
| [`hub/`](hub/) | **语林 Lingua Grove** 总主页：五个工具的入口，中英双语 + 五套配色 | 纯静态 HTML/CSS/JS |
| [`word-puzzle/`](word-puzzle/) | **词境 Lexica**（网站版）：人教版 PEP 初中 + 高中英语词汇题库、四级层级选题、上传资料、导出单文件离线测试页、成绩入库；另有**带登录的家庭版 / 班级版**（学号登录、成绩按人记录、导入名单、按班级导出，经 Tailscale Funnel 对外，见 `word-puzzle/deploy/family/`） | Python 标准库 + SQLite + 原生 JS，nginx 部署 |
| [`topic-app/`](topic-app/) | **每日话题 Daily Topics**：适合初中水平的家庭话题讨论，随机抽题 + 参考方向 + 历史记录 | 纯前端，零依赖，localStorage |
| [`ham-exam/`](ham-exam/) | **无线电执照 Ham Exam**：业余无线电台操作技术能力验证 · 模拟考试系统（1375 道真题题库） | 纯前端，零依赖，localStorage |
| [`chemistry/`](chemistry/) | **化学探秘 Chem Quest**：初中元素配对、高中反应配平、大学溶液推理；选择、数值填空、配对、排序、找错七种题型 | 纯前端，零依赖，localStorage |
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
```

---

## 目录结构

```
language-learning/
├── README.md
├── AGENTS.md                               # 仓库级约定（给人和给 AI 看的）
├── .gitignore
├── hub/                                   # 总主页「语林 Lingua Grove」
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
  └── physics/                                # 物理探秘 Phys Quest（纯静态分龄练习）
```

---

# 一、hub · 语林 Lingua Grove（总主页）

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

## 生产服务器一键部署整站

在生产服务器执行 `git pull` 后，从仓库根目录运行：

```bash
sudo bash ./deploy-all-20261113_213646.sh
```

脚本默认部署到 `10.1.1.93`，会更新词境后端、语林门户、每日话题、无线电执照和 nginx 统一入口（配置写入 `/etc/nginx/conf.d/lingua-grove.conf`），并检查四个页面及词境 API。缺少 `conf.d` 时会自动创建；词境现有数据库会保留。目标地址不同时可覆盖：

```bash
sudo env LINGUA_SERVER_NAME=服务器IP或域名 bash ./deploy-all-20261113_213646.sh
```

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
| 每关限时 | 120 秒，上一关剩余时间越多下一关时间越长，最多 150 秒 |
| 每关词数 | 默认 15 个词，生成题库时可改成 4~40；词多的单元自动拆成多关（``Unit 1（1/3）``），不足的关用前面学过的词补齐 |
| 点卡顺序 | 中文先点、英文先点都行；连点同一侧只是换一张选，不算错并有提示 |
| 配对得分 | 每对 +100 分 |
| 连击奖励 | 连续配对每多一次 +20 分，最高 +100 分 |
| 配错惩罚 | 扣 3 秒、扣 20 分，连击清零 |
| 过关奖励 | 剩余每秒折算 10 分 |

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

## 四个模块

| 模块 | 说明 |
| --- | --- |
| **模拟考试** | 规则与正式考试一致：A 类 40 题/40 分钟、B 类 60 题/60 分钟、C 类 90 题/90 分钟；随机抽题、题序打乱、倒计时自动交卷、答题卡跳题、未答按错计、多选必须与标准答案完全一致才得分 |
| **练习模式** | 不限时，答完立即给答案 + 解析；题量 10/20/30/50/不限；范围可限定单选/多选/附图/错题/未做过/收藏/某知识点 |
| **题库** | 左侧知识点目录树（5 部分 / 29 二级 / 112 三级），右侧逐题浏览；全文搜索；逐题收藏 |
| **统计** | 总览、112 个知识点掌握度、模拟考试记录、错题本 |

数据全部在**自己浏览器的 localStorage**，键名 `ham_exam_data_v1`。不上传、不联网、无服务端。

完整文档见 [`ham-exam/README.md`](ham-exam/README.md)。

---

## 维护记录

### 2026-11-04 — 加了总主页，改了名字

* 新增 `hub/`：语林 Lingua Grove 总主页，中英双语 + 五套配色 + 对角切半色块，
  配 `hub/tests/test_hub.py` 守住样式约定
* 「单词消消乐」正式改名为「**词境 Lexica**」（目录名 `word-puzzle/` 不动）
* `AGENTS.md` 重写：删掉原来的网络/服务器章节，换成家庭网络 10.0.0.0/20
  和生产机 10.1.1.93（PVE + nginx）

### 2026-11-04 — word-puzzle 改造成网站

* 新增 `word-puzzle/server/`（Python 标准库 HTTP 服务 + SQLite）、`word-puzzle/web/`（四个页面）、
  `word-puzzle/deploy/`（nginx + systemd + 一键安装脚本）、`word-puzzle/tools/`、`word-puzzle/tests/`
* 内置人教版 PEP 初中 5 册 + 高中 7 册，共 4791 词条 / 84 单元
* 原单文件版拆成 `game-core.js`（运算）/ `game-ui.js`（界面）/ `game-adapter-*.js`（存储），
  在线页和离线页共用同一份代码
* 保留 `Unit1单词消消乐.html`、课堂投屏版 PPTX、使用说明 PDF 原样不动

### 2026-11-04 — 词表释义错误修复（ham-exam 同批）

第 1 关 `faulty` 词条的释义曾被误填成 faculty 的（"全体教员"），已修正为"有缺陷的；有毛病的；错误的"。
