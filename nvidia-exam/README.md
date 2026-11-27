# NVIDIA 认证模拟考试 · NVIDIA Exam

一个**纯本地**的刷题网站：打开就能用，不联网、不登录、不需要数据库。

覆盖 NVIDIA 官方的 **8 项认证**：

| 考试代码 | 认证 | 层级 | 官方题量 / 时长 | 本题库题量 | 学习指南 |
|---|---|---|---|---:|---:|
| NCA-AIIO | AI 基础设施与运维 | NCA | 50 题 / 60 分钟 | 453 | 94 篇 |
| NCA-GENL | 生成式 AI 大语言模型 | NCA | 50 题 / 60 分钟 | 85 | 81 篇 |
| NCA-GENM | 生成式 AI 多模态 | NCA | 60 题 / 60 分钟 | 156 | 86 篇 |
| NCP-AAI | 智能体 AI | NCP | 50 题 / 60 分钟 | 84 | 49 篇 |
| NCP-AII | AI 基础设施 | NCP | 75 题 / 120 分钟 | 95 | 38 篇 |
| NCP-AIN | AI 网络 | NCP | 75 题 / 120 分钟 | 85 | 71 篇 |
| NCP-AIO | AI 运维 | NCP | 30 题 + 3 场实操 / 120 分钟 | 120 | 90 篇 |
| NCP-OUSD | OpenUSD 开发 | NCP | 65 题 / 90 分钟 | 206 | 61 篇 |

合计 **1284 道题**（其中 60 道是按官方考纲自编的补充题）和 **570 篇学习指南**。
题目为中英双语：英文贴近真实考试语言，中文便于理解；每题附解析和题目来源链接。

> 题目来自 ExamTopics 等**公开免费题库**与 GitHub 开源备考仓库（采集过程与口径见
> [`docs/采集说明.md`](docs/采集说明.md)），**不是官方真题**，仅用于学习自测。

---

## 一、怎么打开

### 方式 1：直接双击（最简单）

双击 `index.html` 即可。全部功能可用（题库和指南数据以 `data/*.js` 的形式内嵌，
走 `file://` 协议也不会被浏览器拦截）。

### 方式 2：起个本地服务（推荐）

```bash
cd nvidia-exam
python3 -m http.server 8084
# 浏览器打开 http://127.0.0.1:8084
```

## 二、五个模块

| 模块 | 说明 |
| --- | --- |
| **模拟考试** | 10 / 20 / 60 题可选，按官方考纲的知识域权重比例抽题（题不够时从全库补齐）；倒计时（照正式考试的每题时长）、答题卡跳题、交卷后给分知识域正确率和逐题复盘；及格线 70% |
| **练习** | 按知识域（或全部）顺序 / 随机练习，每题即时反馈对错与解析，答错自动进错题本 |
| **题库** | 全量浏览，按知识域筛选 + 关键词搜索，展开可见答案、解析与来源 |
| **指南** | 当前科目的学习指南索引：速查表、记忆卡、实操、考纲要点等，每篇带来源仓库与原文链接，正文在 `docs/guides/<代码>.md` |
| **统计** | 已答题数、总正确率、分知识域正确率、考试历史、错题本（支持错题重练） |

数据全部存在**自己浏览器的 localStorage**（键 `nx_state`），不上传、无服务端。
语言（中/英）与配色偏好与 hub 全站共享（`lg_lang` / `lg_theme`），
选中的考试科目记在 `nx_exam`。

## 二之二、在网站上的样子

这个模块是「词境 Lexica」整站的一个模块，和其他模块一样遵守 `AGENTS.md` §3：

- 挂在 `/nvidia-exam/`（容器里的 nginx，`word-puzzle/deploy/family/nginx/word-puzzle-family.conf`）；
- 主页 `hub/` 上有一张卡片，入口在 `hub/js/config.js` 的 `LINGUA_PROJECTS.nvidia`；
- 页面最下面有全站页脚 `/shared/site-footer.js`（备案号 + 隐私说明）；
- 右上角有语言切换和取色器（对角切两半的小方块，五套配色与 hub 同键同色）；
- 登录后老师能在总后台 `/backends/` 看到这个模块的成绩小结（`/shared/module-progress.js`）。

改动这个目录里的 JS / CSS 之后要重新算版本号：

```bash
python3 word-puzzle/tools/bump_assets.py
```

## 三、数据是怎么来的

```
raw-files/                     采集到的原始资料（2026-11-27）
├── nvidia_cert_data.json      8 项认证的题目、选项、答案、解析、讨论帖与指南索引
├── 学习指南汇总.md             570 篇学习指南正文
├── 采集说明.md                采集过程、来源清单与口径
├── NVIDIA认证备考资料.xlsx     同一批数据的表格版（给老师用 Excel 筛选）
└── nvidia-cert-study-hub.html 采集方生成的离线资料中心（单文件）
        │
        │  python3 tools/build_data.py
        ▼
data/bank.json / bank.js       网站用的题库（8 项认证 / 1284 道题）
data/guides.json / guides.js   学习指南索引（570 篇）
data/seed.json                 按官方考纲自编的补充题（手写，60 道）
docs/采集说明.md                采集记录（从 raw-files 复制，删除个人联系方式）
docs/guides/<代码>.md           按科目拆开的学习指南正文
```

### 重跑整理脚本

```bash
cd nvidia-exam && python3 tools/build_data.py
```

脚本做三件事：

1. 把 `raw-files/nvidia_cert_data.json` 里的题目整理成网站用的格式：
   中英对照、答案下标、多选题标记、来源标签与原文链接；
   原站没有解析的题，用社区讨论帖里赞数最高的那条回答补上；
   采集数据里没写知识域的题归到「综合练习」，抽题时用来补齐考纲配额。
2. 把 `raw-files/学习指南汇总.md` 拆成 `docs/guides/<代码>.md`，
   并生成页面上用的指南索引。
3. 生成 `data/bank.js`、`data/guides.js`（`bank.json` / `guides.json` 的 JS 版本，
   两份内容必须一致，测试会校验）。

整理脚本会直接删除输出文档里的邮箱和手机号，不留下占位文字；题目与指南保留必要的来源信息。

### 自己加题

想补自编题就改 `data/seed.json`（只放 NCA-AIIO 的补充题），改完重跑脚本：

```json
{
  "id": 61,
  "domain": "essential-ai-knowledge",
  "q": "English question text",
  "qZh": "中文题干",
  "o": ["opt A", "opt B", "opt C", "opt D"],
  "oZh": ["选项 A", "选项 B", "选项 C", "选项 D"],
  "a": [1],
  "multi": false,
  "e": "English explanation",
  "eZh": "中文解析"
}
```

规则：`a` 是正确选项的下标数组（多选给多个下标并置 `multi: true`）；
`domain` 必须是该科目 `domains` 里的 id。

## 四、新增考试科目

在 `tools/build_data.py` 的 `BLUEPRINTS` 里加一项（代码、中英文名、官方题量与时长、
考纲知识域与权重），再重跑脚本即可。`DOMAIN_ALIASES` 用来把采集数据里的
知识域写法对上考纲里的 id。

考纲权重有三种来源，页面上不显示，但写代码时要知道：

| `blueprint` | 含义 |
|---|---|
| `official` | NVIDIA 公开考纲上的权重 |
| `partial` | 采集到的考纲只列了一部分域（合计不到 100%），按最大余数法归一 |
| `bank` | NVIDIA 没公布权重，按题库里各域的题量折算（NCP-OUSD） |

## 五、测试

```bash
cd nvidia-exam && python3 -m unittest discover -s tests -v
```

覆盖：中英键一致、无硬编码文案、配色变量集完整一致、对角切色块取色器、
localStorage 持久化、题库数据完整性（8 项认证逐项校验）、bank.json / bank.js 一致、
指南索引与正文文件对得上、重跑整理脚本的结果与仓库里的一样、
JS 语法体检（复用 `word-puzzle/tools/check_js.py`），
以及 `node tests/js/app_smoke.test.js` 里把页面真的点一遍
（换科目 → 组卷 → 作答 → 交卷 → 题库 → 指南 → 统计；本机没有 node 时跳过），
还有 `AGENTS.md` §3 / §9.6 的硬性要求：全站页脚、共享页眉样式、
画出来的品牌图标（不是表情符号）、主页入口、容器里的 nginx 挂载点、
版本号必须是文件内容哈希而不是手打的日期。