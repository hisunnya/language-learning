# language-learning

个人学习工具集。两个项目互相独立，各自都能单独跑起来。

| 项目 | 内容 | 技术栈 |
| --- | --- | --- |
| [`word-puzzle/`](word-puzzle/) | **单词消消乐**（网站版）：人教版 PEP 初中 + 高中英语词汇题库、四级层级选题、上传资料、导出单文件离线测试页、成绩入库 | Python 标准库 + SQLite + 原生 JS，nginx 部署 |
| [`ham-exam/`](ham-exam/) | 业余无线电台操作技术能力验证 · 模拟考试系统（1375 道真题题库） | 纯前端，零依赖，localStorage |

---

## 快速开始

```bash
# word-puzzle（网站版）
cd word-puzzle && ./run.sh        # → http://127.0.0.1:8000

# ham-exam（纯前端）
cd ham-exam && ./start.sh         # → http://127.0.0.1:8080
```

---

## 目录结构

```
language-learning/
├── README.md
├── .gitignore
├── word-puzzle/                            # 单词消消乐（网站版）
│   ├── README.md                           # 详细文档
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
│   │   └── offline.py                      # 单文件离线页生成
│   ├── web/                                # 前端（静态，nginx 直接托管）
│   │   ├── index.html  bank.html  play.html  stats.html
│   │   ├── css/{app,game}.css
│   │   └── js/*.js
│   ├── data/
│   │   ├── pep_curriculum.json             # 内置词库（4791 词 / 84 单元）
│   │   └── raw/                            # 原始词表（脚本输入）
│   ├── tools/{build_seed_data.py,check_js.py}
│   ├── tests/test_server.py                # 后端测试（38 个用例）
│   ├── var/                                # 运行期数据（gitignore）
│   ├── Unit1单词消消乐.html                # 原始单文件版（保留）
│   ├── Unit1单词消消乐-课堂投屏版 .pptx
│   └── Unit1单词消消乐-使用说明.pdf
└── ham-exam/
    ├── README.md
    ├── index.html                          # 入口
    ├── start.sh / start.bat                # 一键起本地服务
    ├── css/style.css                       # 样式（含深色模式）
    ├── js/{app.js,store.js}                # 应用逻辑 / localStorage 数据层
    ├── data/{bank.js,bank.json}            # 题库（两份内容完全一致）
    ├── images/                             # 53 张电路附图
    └── tools/                              # 题库生成脚本（从官方 PDF 生成 bank.json）
```

---

# 一、word-puzzle · 单词消消乐（网站版）

## 是什么

一个能部署到 **Ubuntu + nginx** 的英语单词消消乐网站。

内置**人教版 PEP 初中（5 册）+ 高中（7 册）**共 **4791 个词条 / 84 个单元**，
用四级层级选题：**学段 → 年级 → 学期 → 单元**，每一级都能自定义名称。

| 特性 | 说明 |
| --- | --- |
| 四级层级 | 学段（小学/初中/高中/大学）→ 年级 → 学期（默认「整学年」）→ 单元（全部单元 / 分单元 / 第 N 至第 M 单元） |
| 自定义命名 | 每一级都能填自己的名字，自定义名会进题库标题和离线文件名 |
| 上传资料 | TXT / CSV / TSV / JSON，自动识别表头、单元列、中英文列 |
| 默认题库 | **人教版初中三年级上学期**（239 词 / 7 单元），启动时自动建好 |
| 离线测试页 | 任意题库一键导出成**单个自包含 HTML**，文件名 `层级+日期+时间.html` |
| 分数入库 | 在线成绩写 SQLite；离线页成绩写浏览器 localStorage |
| 零依赖 | 后端只用 Python 标准库，数据库用 SQLite，服务器上不用 `pip install` |

完整文档见 [`word-puzzle/README.md`](word-puzzle/README.md)。

## 界面

沿用原来的 `Unit1单词消消乐.html` 的样式和玩法：点英文卡片听发音 → 点对应中文卡片配对成功。

| 项目 | 规则 |
| --- | --- |
| 每关限时 | 120 秒，上一关剩余时间越多下一关时间越长，最多 150 秒 |
| 配对得分 | 每对 +100 分 |
| 连击奖励 | 连续配对每多一次 +20 分，最高 +100 分 |
| 配错惩罚 | 扣 3 秒、扣 20 分，连击清零 |
| 过关奖励 | 剩余每秒折算 10 分 |

## 运算与存储分离

```
game-core.js        纯运算（关卡/计分/计时/连击），不碰 DOM、不碰网络
game-ui.js          纯界面，只把 core 的状态画出来
game-adapter-*.js   存储适配：online 走后端 / offline 走 localStorage
```

在线页面用 `<script src>` 引用这两个文件，离线页由 `server/offline.py` 把它们**内联进单个 HTML**，
所以离线页和在线页玩法、分数完全一致。

---

# 二、ham-exam · 业余无线电操作证模拟考试

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

### 2026-11-04 — word-puzzle 改造成网站

* 新增 `word-puzzle/server/`（Python 标准库 HTTP 服务 + SQLite）、`word-puzzle/web/`（四个页面）、
  `word-puzzle/deploy/`（nginx + systemd + 一键安装脚本）、`word-puzzle/tools/`、`word-puzzle/tests/`
* 内置人教版 PEP 初中 5 册 + 高中 7 册，共 4791 词条 / 84 单元，附带 3984 条 ECDICT 音标
* 原单文件版拆成 `game-core.js`（运算）/ `game-ui.js`（界面）/ `game-adapter-*.js`（存储），
  在线页和离线页共用同一份代码
* 保留 `Unit1单词消消乐.html`、课堂投屏版 PPTX、使用说明 PDF 原样不动

### 2026-11-04 — 词表释义错误修复（ham-exam 同批）

第 1 关 `faulty` 词条的释义曾被误填成 faculty 的（"全体教员"），已修正为"有缺陷的；有毛病的；错误的"。
