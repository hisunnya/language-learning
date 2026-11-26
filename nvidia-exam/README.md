# NVIDIA 认证 · AI 基础设施与运维模拟考试

一个**纯本地**的刷题网站：打开就能用，不联网、不登录、不需要数据库。

题库按 NVIDIA 官方公开考试大纲（exam blueprint）生成，当前覆盖 **NCA-AIIO**（NVIDIA Certified Associate: AI Infrastructure and Operations，60 分钟 / 50 题 / 及格线 70%）：

| 知识域 | 权重 | 题量（当前种子题库） |
|---|---:|---:|
| Essential AI Knowledge（AI 基础知识） | 38% | 23 |
| AI Infrastructure（AI 基础设施） | 40% | 24 |
| AI Operations（AI 运维） | 22% | 13 |

题目为中英双语：英文贴近真实考试语言，中文便于理解；每题附解析。

> 这是按大纲生成的种子题库，用于内网学习自测，**不是真题**。后续可直接往
> `data/bank.json` 里补题（格式见下），`bank.js` 由 `bank.json` 生成，两份必须一致
> （tests 会校验）。

---

## 一、怎么打开

### 方式 1：直接双击（最简单）

双击 `index.html` 即可。全部功能可用。

### 方式 2：起个本地服务（推荐）

```bash
cd nvidia-exam
python3 -m http.server 8084
# 浏览器打开 http://127.0.0.1:8084
```

## 二、四个模块

| 模块 | 说明 |
| --- | --- |
| **模拟考试** | 10 / 20 / 60 题可选，按知识域权重比例抽题；倒计时（每题 1.2 分钟，照正式考试节奏）、答题卡跳题、交卷后给分知识域正确率和逐题复盘；及格线 70% |
| **练习** | 按知识域（或全部）顺序 / 随机练习，每题即时反馈对错与解析，答错自动进错题本 |
| **题库** | 全量浏览，按知识域筛选 + 关键词搜索，展开可见答案与解析 |
| **统计** | 已答题数、总正确率、分知识域正确率、考试历史、错题本（支持错题重练） |

数据全部存在**自己浏览器的 localStorage**（键 `nx_state`），不上传、无服务端。
语言（中/英）与配色偏好与 hub 全站共享（`lg_lang` / `lg_theme`）。

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

## 三、怎么补题

编辑 `data/bank.json`，在 `questions` 数组里追加：

```json
{
  "id": 61,
  "domain": "ai-knowledge",
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
`domain` 必须是三个知识域 id 之一。改完重新生成 `bank.js`：

```bash
cd nvidia-exam/data
{ printf '/* 题库数据。由 bank.json 生成，两份内容必须一致（tests 校验）。 */\nwindow.NVIDIA_BANK = '; cat bank.json; printf ';\n'; } > bank.js
```

然后跑一遍测试：

```bash
cd nvidia-exam && python3 -m unittest discover -s tests -v
```

## 四、新增考试科目

`exams` 数组支持多门考试。复制现有条目，改 `id` / `name` / `domains` / `questions`
即可；页面会展示第一门考试。多科目切换 UI 有需要时再加。

## 五、测试

```bash
cd nvidia-exam && python3 -m unittest discover -s tests -v
```

覆盖：中英键一致、无硬编码文案、配色变量集完整一致、对角切色块取色器、
localStorage 持久化、题库数据完整性、bank.json / bank.js 一致、JS 语法体检
（复用 `word-puzzle/tools/check_js.py`），以及 `AGENTS.md` §3 / §9.6 的硬性要求：
全站页脚、共享页眉样式、画出来的品牌图标（不是表情符号）、主页入口、
容器里的 nginx 挂载点、版本号必须是文件内容哈希而不是手打的日期。
