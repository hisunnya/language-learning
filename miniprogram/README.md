# miniprogram · 词境 单词消消乐（微信小程序版）

把 `word-puzzle/`（网站版）的消消乐玩法搬到微信小程序上。**第一版只做单机可玩**：
题库打包在代码包里，离线能玩，成绩还没入库。

内置题库是**人教版九年级（初三）**：上下两册共 14 单元 / 438 词，含美式音标。

| 项目 | 说明 |
| --- | --- |
| 技术栈 | 原生小程序（WXML / WXSS / CommonJS），无 npm、无框架 |
| 数据 | 全部本地 `data/grade9.js`，无网络请求 |
| 玩法 | 与网站版共用同一套计分规则，逻辑从 `game-core.js` 原样移植 |
| 语音 | 播放器已写好，音频待生成后接云存储（见下） |

---

## 一、跑起来

1. 微信开发者工具 →「导入项目」→ 选这个 `miniprogram/` 目录
2. AppID 填你自己的；只想先看效果就选「测试号」
3. 编译后从首页选「全部单元」或某个单元开始

`project.config.json` 里的 `appid` 现在是 `touristappid`（测试号占位），换成真实
AppID 才能真机预览和上传。

---

## 二、目录

```
miniprogram/
├── app.js / app.json / app.wxss      # 入口与全局样式（主题变量在 app.wxss）
├── project.config.json               # 工程配置（appid 改这里）
├── pages/
│   ├── index/                        # 选册 → 选单元
│   └── game/                         # 棋盘、HUD、过关结算
├── utils/
│   ├── game-core.js                  # 纯运算：关卡 / 计分 / 计时 / 连击
│   ├── bank.js                       # 题库切关（12 词一关 + 复习补齐）
│   └── audio.js                      # 单词发音播放器（预取 + 缓存）
├── data/
│   └── grade9.js                     # 九年级题库（生成物，别手改）
├── tools/
│   └── build-data.js                 # 从网站版词库生成 data/grade9.js
└── design/
    └── icon.svg / icon-1024.png      # 小程序图标（上传到微信后台用）
```

---

## 三、和网站版的关系

| 网站版文件 | 小程序版 | 处理方式 |
| --- | --- | --- |
| `web/js/game-core.js` | `utils/game-core.js` | 直接移植，只改导出方式 |
| `web/js/game-ui.js` | `pages/game/*` | 重写：DOM 操作 → WXML/WXSS |
| `server/bank.py`（切关部分） | `utils/bank.js` | 直接移植 |
| `server/tts.py` | 不在小程序里跑 | 改成**离线批量生成**音频 |
| `server/*` 其余 | 不移植 | 上传解析、离线页导出等留在网站 |

计分规则一个字没改：每对 +100，连击每级 +20（上限 +100），配错扣 3 秒扣 20 分，
每关 120 秒，过关剩余每秒折算 10 分并按剩余时间给下一关加时，上限 150 秒。

比网站版多了一个 `wrongLog`：每次配错记下「哪个英文词配了哪个中文」，
以后接云端导出时可以直接做错词榜。

---

## 四、换题库

`data/grade9.js` 是生成物，不要手改。换年级：

```bash
cd miniprogram
node tools/build-data.js      # 默认九年级
```

改 `tools/build-data.js` 顶部的 `GRADE` 常量即可换七年级 / 八年级 / 高一 等。

大学英语这类外部教材，走网站版的「上传题库」解析成词表后，再按同样的
`{ books: [{ name, units: [{ name, words: [{ en, cn, ipa }] }] }] }` 结构
生成一份数据模块即可，页面和切关逻辑都不用动。

生成脚本会做两件事：同一单元里英文相同的词条合并成一条；同一关里中文相同的词条
只保留一个。否则一关会出现两张看起来都对的卡片，配对会变得含糊。

---

## 五、语音怎么接

音频是静态的，**不在运行时合成**。用网站版的 `server/tts.py` 批量生成
（Edge Neural `en-US-AriaNeural`，失败时整体回退 espeak-ng 美式女声，
不会混用两种音色），上传到云开发存储，然后：

```js
// pages/game/game.js 顶部
const audio = require('../../utils/audio.js');
audio.setBase('https://<你的云存储域名>/audio/');
```

之后 `audio.preload()` 会在进关时把本关 12 个词的 mp3 预取到本地，
点卡片是瞬发，不重复走 CDN。`audio.setBase` 没调用时全静音，不影响游戏。

文件名规则：`<云存储目录>/<编码后的英文>.mp3`，例如 `audio/apple.mp3`。

---

## 六、还没做

- 成绩入库与老师导出（计划走云开发 + 本地导出脚本，出多 sheet Excel）
- 语音音频的批量生成与上传
- 多套配色（网站版有 5 套，这里只带了 indigo）
- 大学英语三种教材的导入

---

> 内置词库来自人教版 PEP 课本，版权归人民教育出版社所有，仅供个人学习使用。
