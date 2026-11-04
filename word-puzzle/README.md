# word-puzzle · 单词消消乐（网站版）

一个**能部署到 Ubuntu + nginx** 的英语单词消消乐网站。

* 内置**人教版 PEP 初中（5 册）+ 高中（7 册）**共 **4791 个词条 / 84 个单元**
* 四级层级选题：学段 → 年级 → 学期 → 单元，**每一级都能自定义名称**
* 能**上传自己的资料**做成题库
* 能把任意题库导出成**单个 HTML 的离线测试页**（双击就能在没网的电脑上玩）
* 界面和玩法沿用原来的 `Unit1单词消消乐.html`，**分数记录**从 localStorage 升级成后端数据库

> 暂时不含登录/注册。成绩按浏览器生成的匿名设备号（`localStorage` 里的随机 id）记录。

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
| 题库工作台 | `/bank.html` | **上传题库** + **生成离线测试**（两个主按钮），管理资料/题库/离线文件 |
| 在线消消乐 | `/play.html?bank=<id>` | 玩，成绩写回数据库 |
| 成绩记录 | `/stats.html` | 总览、按题库统计、逐条明细 |

---

## 三、四级层级

| 级 | 选项 | 说明 |
| --- | --- | --- |
| 1 学段 | 小学 / 初中 / 高中 / 大学 / **自定义…** | |
| 2 年级 | 随学段变化：小学 一~六年级、初中 七~九年级、高中 高一~高三、大学 大一~大四 / **自定义…** | |
| 3 学期 | 上册 / 下册 / **整学年（默认）** / **自定义…** | 「整学年」= 该年级上册 + 下册 |
| 4 单元 | **全部单元** / **分单元** / **第 N 至第 M 单元** / **自定义…** | 「分单元」= 每个单元单独一关，可在首页挑单元开始 |

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

> **默认题库 = 人教版初中三年级上学期**（239 词 / 7 单元）。服务启动时自动建好。
>
> 九年级官方教材是「全一册」，本仓库按 Unit 1–7 / Unit 8–14 拆成上下册；
> 划分写在 `data/pep_curriculum.json` 的 `split_note` 里，改 `tools/build_seed_data.py`
> 的 `GRADE9_SPLIT` 就能换一种拆法。

---

## 四、上传资料

题库工作台点「📁 上传题库」选文件即可。支持三种格式：

| 格式 | 写法 | 识别方式 |
| --- | --- | --- |
| **TXT** | 每行 `english<TAB>中文`；单独一行 `Unit 3` 会被当作单元标题 | 自动 |
| **CSV / TSV** | 有表头就按表头取（`unit, english, chinese, ipa`）；没表头就按「英文,中文」或「单元,英文,中文」猜 | 自动 |
| **JSON** | `[{"english":"apple","chinese":"苹果"}]`，或 `{"units":[{"unit":"Unit 1","words":[...]}]}` | 自动 |

字段别名都认：`en / eng / english / word`、`cn / zh / chinese / meaning / translation`、
`unit / section / chapter`、`ipa / phonetic`、`pos / partOfSpeech`。

上传后这份资料就能在「题源」里选中，用来生成题库。

---

## 五、离线测试页

题库工作台点「🧪 生成离线测试」，或者在题库列表里对某个题库点同名按钮。

产物是一个**完全自包含的 HTML 文件**：词表、样式、脚本全部内嵌，不请求任何外部资源，
双击就能玩（发音用浏览器自带的 TTS）。文件名规则：

```
<层级>+<日期>+<时间>.html
例：初中-九年级-上册-全部单元-20261104-015833.html
    初中-九年级-上册-第1至3单元-20261104-015833.html
```

离线页的成绩存在浏览器 `localStorage`（key `wp_offline_scores_v1`），**不会**出现在网站的成绩记录里。

---

## 六、玩法与计分（沿用原版）

| 项目 | 规则 |
| --- | --- |
| 每关限时 | 120 秒；上一关剩余时间越多，下一关时间越长，最多 150 秒 |
| 配对得分 | 每对 +100 分 |
| 连击奖励 | 连续配对每多一次 +20 分，最高 +100 分 |
| 配错惩罚 | 扣 3 秒、扣 20 分，连击清零 |
| 过关奖励 | 剩余每秒折算 10 分，直接计入总分 |

底部四个按钮：**玩法** · **全屏** · **重玩本关** · **从头开始**。

---

## 七、架构：运算和存储是分开的

```
web/js/game-core.js        纯运算：关卡 / 计分 / 计时 / 连击。不碰 DOM、不碰网络
web/js/game-ui.js          纯界面：把 core 的状态画出来、播特效。不算分
web/js/game-adapter-*.js   存储适配：online 写后端 / offline 写 localStorage
web/js/selector.js         四级层级选择器
```

同一份 `game-core.js` + `game-ui.js`：

* 在线页面用 `<script src>` 引用，成绩走 `POST /api/scores`
* 离线页面由 `server/offline.py` **把它们内联进单个 HTML**，成绩走 localStorage

所以离线页和在线页的玩法、分数完全一致，只有落库方式不同。

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
sudo ./deploy/install.sh
```

脚本会：建 `wordpuzzle` 系统用户 → 代码放到 `/srv/word-puzzle` → 数据目录
`/var/lib/word-puzzle` → 生成内置词库 → 装并启动 systemd 服务 → 装 nginx 站点配置。

手动部署的话：

```bash
# 1. 后端
sudo cp -r word-puzzle /srv/word-puzzle
sudo useradd --system wordpuzzle
sudo mkdir -p /var/lib/word-puzzle && sudo chown wordpuzzle /var/lib/word-puzzle
sudo cp deploy/systemd/word-puzzle.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now word-puzzle

# 2. nginx
sudo cp deploy/nginx/word-puzzle.conf /etc/nginx/sites-available/word-puzzle
sudo sed -i 's/word-puzzle.example.com/你的域名/' /etc/nginx/sites-available/word-puzzle
sudo ln -s /etc/nginx/sites-available/word-puzzle /etc/nginx/sites-enabled/
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
| GET | `/api/meta` | 层级元数据 + 内置词库统计 |
| GET | `/api/terms?level1=&level2=` | 某年级的学期选项 |
| GET | `/api/units?level1=&level2=&level3=` | 某学期的单元列表 |
| GET | `/api/materials` | 资料列表 |
| POST | `/api/materials` | 上传资料（multipart，字段名 `file`） |
| DELETE | `/api/materials/<id>` | 删除资料 |
| GET | `/api/banks` | 题库列表 |
| POST | `/api/banks` | 生成题库（body 是层级选择） |
| GET | `/api/banks/<id>` | 题库内容（游戏用） |
| DELETE | `/api/banks/<id>` | 删除题库 |
| POST | `/api/banks/<id>/offline` | 生成离线测试页 |
| GET | `/api/offline` | 已生成的离线文件列表 |
| GET | `/api/offline/<文件名>` | 下载（加 `?inline=1` 直接在浏览器里预览） |
| GET | `/api/scores?limit=&bank_id=` | 成绩列表 + 统计 |
| POST | `/api/scores` | 写成绩 |
| GET | `/api/stats` | 成绩统计 |

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
├── web/                          # 前端（静态，nginx 直接托管）
│   ├── index.html  bank.html  play.html  stats.html
│   ├── css/{app,game}.css
│   └── js/{api,selector,game-core,game-ui,game-adapter-online,game-adapter-offline,page-*}.js
├── data/
│   ├── pep_curriculum.json       # 内置词库（生成物，已入库）
│   └── raw/                      # 原始词表（脚本输入）
├── tools/
│   ├── build_seed_data.py        # 生成内置词库
│   └── check_js.py               # JS 语法体检
├── tests/test_server.py          # 后端测试（38 个）
├── var/                          # 运行期数据（已 gitignore）
│   ├── app.db
│   └── offline/                  # 生成的离线测试页
└── Unit1单词消消乐.html           # 原始单文件版（保留）
```

---

## 十二、内置词库的来源

| 学段 | 来源仓库 | 备注 |
| --- | --- | --- |
| 初中 | [`henry1786580051-lang/english-test`](https://github.com/henry1786580051-lang/english-test) `src/data/grade*.json` | 整理自人教版课本，参考 [`TapXWorld/ChinaTextbook`](https://github.com/TapXWorld/ChinaTextbook) 的教材数据 |
| 高中 | [`lfcypo/pep-senior-eng-vocab-json`](https://github.com/lfcypo/pep-senior-eng-vocab-json) `vocabulary.json` | 人教版普通高中英语新教材七册 |
| 音标（可选） | [`skywind3000/ECDICT`](https://github.com/skywind3000/ECDICT) `ecdict.csv` | 覆盖 3984/4791 词条 |

原始文件都放在 `data/raw/` 里，`tools/build_seed_data.py` 只做整理、不联网。
想补音标：

```bash
curl -sSL https://raw.githubusercontent.com/skywind3000/ECDICT/master/ecdict.csv \
     -o data/raw/ecdict.csv
python3 tools/build_seed_data.py --ecdict data/raw/ecdict.csv
rm data/raw/ecdict.csv      # 66MB，别入库
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

现在网站版的界面和玩法是从它拆出来的（`web/css/game.css` 就是它的样式），
两边共用同一套 `game-core.js` / `game-ui.js`。
