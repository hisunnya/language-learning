# miniprogram · 词境 单词消消乐（微信小程序版）

把 `word-puzzle/`（网站版）的消消乐玩法搬到微信小程序上。**第一版只做单机可玩**：
题库打包在代码包里，离线能玩，成绩还没入库。

内置题库是**人教版九年级（初三）**：上下两册共 14 单元 / 438 词，含美式音标。

| 项目 | 说明 |
| --- | --- |
| 技术栈 | 原生小程序（WXML / WXSS / CommonJS），无 npm、无框架 |
| 数据 | 全部本地 `data/grade9.js`，无网络请求 |
| 玩法 | 与网站版共用同一套计分规则，逻辑从 `game-core.js` 原样移植 |
| 语言 / 配色 | 中文 / English 一键切换，五套配色（和网站版一致），选择会记住 |
| 语音 | 进关自动下载本关发音，下载失败只是没有声音，游戏照常（见第五节） |

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
├── app.js / app.json / app.wxss      # 入口与全局样式（五套配色的变量在 app.wxss）
├── config.js                         # 语音文件的位置（云存储前缀或 HTTPS 地址）
├── project.config.json               # 工程配置（appid 改这里）
├── pages/
│   ├── index/                        # 选册 → 选单元
│   └── game/                         # 棋盘、HUD、过关结算
├── utils/
│   ├── game-core.js                  # 纯运算：关卡 / 计分 / 计时 / 连击
│   ├── bank.js                       # 题库切关（12 词一关 + 随机复习补满）
│   ├── audio.js                      # 单词发音：自动下载、缓存，失败静默
│   ├── i18n.js                       # 界面文字（zh / en 两张表）
│   └── prefs.js                      # 语言和配色偏好（记在本机存储）
├── data/
│   └── grade9.js                     # 九年级题库（生成物，别手改）
├── tools/
│   └── build-data.js                 # 从网站版词库生成 data/grade9.js
├── tests/                            # 静态规范 + 行为测试（含一个假的 wx 运行环境）
└── design/
    ├── icon.svg                      # 图标（字形已转曲线，不依赖字体安装）
    ├── icon-param.svg                # 同款可调版，颜色走 CSS 变量
    ├── icon-144.png                  # 上传微信后台用（官方建议尺寸）
    ├── icon-1024.png                 # 母版，高分屏更清楚
    ├── make-icon.js                  # 图标生成器，参数都在文件顶部的 P 里
    ├── glyphs-cuan.js                # 「词」「境」的字形路径数据（生成物）
    └── ttf2path.py                   # 从 TTF 抽字形轮廓的工具
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

两份 `game-core.js` 用 `word-puzzle/tests/js/core_parity.test.js` 守着：同一个种子、同一串
随机操作（点牌、走时间、暂停、重玩……）同时驱动两份，每一步比较状态和事件，谁改偏谁失败。
`bank.js` 与网站版 `bank.py` 同理（`word-puzzle/tests/test_bank_levels.py`）。

这次一起修掉的三个计分问题（小程序版和网站版都有）：

* **重玩不能刷分**：重玩本关会收回这一关里已经拿到的分；以前「拿几分、认输、重玩」可以无限累积。
* **时长覆盖整局**：`duration` 以前每换一关就清零，导出的只是最后一关的时间。
* **切走暂停**：切到别的应用（或网站切标签页）时计时暂停，回来接着走，不扣切走的时间。

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

音频是静态文件，**不在运行时合成**。用网站版的 `server/tts.py` 批量生成
（Edge Neural `en-US-AriaNeural`，失败时整体回退 espeak-ng 美式女声，
不会混用两种音色），传到小程序云开发存储，文件名规则 `<目录>/<编码后的英文>.mp3`，
例如 `audio/apple.mp3`、`audio/ice%20cream.mp3`。

然后在 `config.js` 里填一项：

```js
module.exports = {
  audioCloudPrefix: 'cloud://<环境ID>.xxxx/audio/',   // 云存储（用 wx.cloud.downloadFile）
  audioBase: ''                                        // 或者 HTTPS 静态地址（域名要加进 downloadFile 合法域名）
};
```

行为：

* 学生点开某一关，进关就自动下载这一关的发音，同时顺手预取下一关的；点英文卡片播放本地文件。
* **声音永远是加分项，不能影响游戏**：没配置、没网络、文件不存在（云存储返回非 200）、
  下载超时、播放出错，全部静默跳过。失败的词 20 秒内不重试，之后再点会再试；
  同一个词同时只下载一次；点得太快只播最后一个。
* 两项都留空 = 不启用语音：卡片上不显示 🔊，游戏照常玩（`tests/` 里有「语音全部下载失败也能玩到过关」的用例）。

---

## 六、测试

```bash
cd miniprogram && python3 -m unittest discover -s tests -v
```

没有微信开发者工具也能跑：静态规范（配置合法、页面文件齐全、WXML 标签配平、文字全部走语言表、
五套配色变量完全一致、配色方块是方形对角切分）+ 行为测试（`tests/js/harness.js` 提供假的 `wx`、
可控的时钟和定时器，验证页面逻辑：语言配色切换、暂停恢复、卸载后不再 setData、语音失败照常过关）。
**WXML 的真实渲染没法在这里验证**，首次需要在微信开发者工具里看一眼。

---

## 七、图标

微信后台「小程序头像」的要求：**PNG / JPG / BMP / GIF，不超过 2MB，官方建议 144×144**。
每月可改 5 次，上传后会被自动裁切（后台预览是圆形，各端列表里多为圆角方形）。

| 文件 | 用途 |
| --- | --- |
| `icon-144.png` | 首选上传，正好是官方建议尺寸 |
| `icon-1024.png` | 母版；若后台上传不报错，用它更利于高分屏显示 |
| `icon.svg` | 矢量源文件，任意放大不失真 |

**字形已转曲线**（`ttf2path.py` 把 TTF 轮廓抽成 SVG path），所以 `icon.svg`
在任何没装方正爨宝子碑楷书的机器上打开都一致，不会掉回黑体。

改配色、字号、位置、倾斜角：编辑 `make-icon.js` 顶部的 `P`，然后

```bash
cd design && node make-icon.js
```

会重新生成 `icon.svg` / `icon-param.svg` / `icon-single.svg`。改完再用 Chrome 出 PNG：

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new \
  --disable-gpu --hide-scrollbars --window-size=1024,1024 \
  --screenshot="$PWD/icon-1024.png" "file://$PWD/icon.svg"
sips -z 144 144 icon-1024.png --out icon-144.png
```

`icon-param.svg` 是同一张图的可调版：颜色放在 `<style>` 的 `:root` 里当 CSS 变量，
改 5 个色值就能换配色，不用碰路径。兼容性最好的是 `icon.svg`（颜色写死）。

换字体：`python3 ttf2path.py --js <字体.ttf> glyphs-xxx.js 词 境`，再把
`make-icon.js` 里的 `require` 指过去。

---

## 八、还没做

- 成绩入库与老师导出（计划走云开发 + 本地导出脚本，出多 sheet Excel）
- 语音音频的批量生成与上传
- 大学英语三种教材的导入

---

> 内置词库来自人教版 PEP 课本，版权归人民教育出版社所有，仅供个人学习使用。
