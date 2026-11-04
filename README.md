# language-learning

《新视野大学英语 4th Edition》配套的课堂单词游戏。纯前端、零依赖、零联网，**一个 HTML 文件就是全部**。

---

## 目录结构

```
language-learning/
├── README.md
├── .gitignore
└── word-puzzle/
    ├── Unit1单词消消乐.html                    # 学生版网页游戏（主程序）
    ├── Unit1单词消消乐-课堂投屏版 .pptx        # 课堂投屏版（PowerPoint 超链接配对游戏，173 页）
    └── Unit1单词消消乐-使用说明.pdf             # 发给家长/学生的使用说明
```

---

## 一、学生版（网页版）

`word-puzzle/Unit1单词消消乐.html`

| 特性 | 说明 |
| --- | --- |
| 单文件 | 词表、发音（base64 内嵌 MP3）、CSS、JS 全部内联，**离线可用** |
| 无依赖 | 不加载任何 CDN / 字体 / 框架 |
| 依赖 | 浏览器需支持 ES5 + WebAudio + Fullscreen API（Chrome / Edge / Safari / 微信内置浏览器均可） |
| 适配 | 响应式栅格（2–6 列自动布局），手机、平板、投影大屏通用 |
| 发音 | 54 条真人朗读（美式女声，32 kHz 单声道 MP3），播放失败时自动回退到 `speechSynthesis` |

### 玩法

1. **点英文卡片** → 卡片高亮选中，同时朗读该词发音（右下角 🔊 可再听一遍）
2. **点对应中文卡片** → 配对成功，两张卡冒出星星特效并消失
3. **配错** → 卡片抖动，扣 3 秒、扣 20 分，连击清零
4. **全部配完** → 结算页显示本关得分与剩余时间奖励，可进入下一关

### 计分与时间

| 项目 | 规则 |
| --- | --- |
| 每关限时 | 120 秒（第 1 关）；上一关剩余时间越多，下一关时间越长，最多 150 秒 |
| 配对得分 | 每对 +100 分 |
| 连击奖励 | 连续配对成功，每多一次 +20 分，最高 +100 分 |
| 配错惩罚 | 扣 3 秒、扣 20 分，连击清零 |
| 过关奖励 | 剩余每秒折算 10 分，直接计入总分 |

底部四个按钮：**玩法**（规则说明）· **全屏**（投影用）· **重玩本关**（只重置当前关）· **从头开始**（回到首页重打全部）。

### 词表结构

共 **54 个词条 / 7 个关卡**，数据全部位于 `<script>` 顶部的 `var WORDS`：

```js
{ "en": "triumph", "ipa": "/ˈtraɪʌmf/", "cn": "胜利；成功；成就",
  "full": "an important victory or success after a difficult struggle", "lv": 1 }
```

- `lv` 决定关卡归属，关卡由 `LEVELS` 按 `lv` 自动分组、排序
- 第 1–5 关为**单词**，第 6–7 关为课本的**常用表达（短语）**
- 发音表 `var AUDIO` 的 key 是 `slugify(en)`，即小写 + 非字母数字替换为 `_`
- 改词表后需同步更新 `AUDIO`，否则该词会回退到浏览器 TTS 朗读

---

## 二、课堂投屏版（PowerPoint）

`word-puzzle/Unit1单词消消乐-课堂投屏版 .pptx`

173 页超链接配对游戏：每关一张棋盘（左侧英文、右侧打乱的中文），点任意一张卡片进入配对题，选对有庆祝页、选错有提示页。适合教师在教室大屏上演示。

> ⚠️ **词表是写死在 slide XML 里的。** 修改 `WORDS` 后，PPTX 不会自动同步，必须重新生成或手工改 `ppt/slides/slide*.xml` 中对应的文本。2026-11-04 修复 `faulty` 释义时即采用批量文本替换的方式同步了 11 张幻灯片。

---

## 三、使用说明（PDF）

`word-puzzle/Unit1单词消消乐-使用说明.pdf`

讲清楚「怎么把游戏发到微信 → 怎么打开 → 怎么玩」，可直接转发给同学和家长。内容为纯操作流程，**不含词表**，因此词表变更无需同步。

---

## 维护记录

### 2026-11-04 — 词表释义错误修复 + 逻辑缺陷清理

**数据错误（P0，会教错知识）**

第 1 关的 `faulty` 词条，其 `cn` / `full` 字段被误填成了 **faculty** 的释义：

```
错误：faulty → 全体教员 / (AmE) all the teachers in a university, college, or school
正确：faulty → 有缺陷的；有毛病的；错误的 / not working correctly; having a fault or defect
```

成因：生成词表时 `faulty` 与 `faculty` 两行合并，`faculty` 的释义覆盖了 `faulty`。
已修正 HTML 与 PPTX 两处（PPTX 同步替换 11 张幻灯片）。

> 教材中的 `faculty`（n. 全体教员）由此从词表中丢失。其释义已确认可复原为
> `{ "en": "faculty", "ipa": "/ˈfækəlti/", "cn": "全体教员", "full": "(AmE) all the teachers in a university, college, or school" }`，
> 但因 PPTX 投屏版每关按 8 对设计、新增词条需要重排版，暂未补入，留待后续版本处理。

**代码缺陷**

| # | 位置 | 问题 | 处理 |
| --- | --- | --- | --- |
| 1 | `sfx.combo()` | `beep([880*n>0?880:880, ...])` 三元表达式两边相同，连击音效音高永远不变 | 改为随连击数递增 |
| 2 | `levelClear()` | `st.lv = st.lv;` 空赋值 | 删除 |
| 3 | `gainOfLevel()` | 死代码，返回恒为 0 且无人调用 | 删除 |
| 4 | `levelClear()` | 结算面板有 520 ms 延迟，期间点「重玩本关」会弹出结算面板压在新棋盘上 | 引入 `st.gen` 代数计数器，面板弹出前校验 |
| 5 | `showPanel()` | `showList()` 绑定的 `$('panel').onclick` 不会被清理，跨面板泄漏 | `showPanel()` 内统一置空 |
| 6 | `st` 初始值 | `timeLeft/limit` 写死 60，与 `LEVEL_TIME = 120` 不一致 | 改用 `LEVEL_TIME` |

**验证**

- `node --check` 通过；浏览器实测无 console error
- 54 条发音全部解码校验通过（ID3 头合法，时长 0.86 s – 3 s），词表与音频 key 一一对应、无缺失、无孤儿
- PPTX 以 python-pptx 复读通过，173 页结构完整
