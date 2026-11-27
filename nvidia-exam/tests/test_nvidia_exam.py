"""NVIDIA 认证模拟考试页（nvidia-exam/）的规范测试。

仓库根目录的 AGENTS.md §3 要求每个页面都做到：

* 中英双语可切换，文案全部走 ``data-i18n``，两种语言的键完全一致；
* 至少三套配色，每套都是**完整且相同**的 CSS 变量集；
* 配色选择器是对角切两半的小方块，右上主色、左下底色；
* 语言和配色都记在 localStorage 里（lg_lang / lg_theme，与 hub 共享）。

另外校验题库数据自身的完整性（bank.json 与 bank.js 必须一致、
答案下标合法、知识域权重合计 100%）。

跑法::

    python3 -m unittest discover -s nvidia-exam/tests -v
"""
from __future__ import annotations

import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ROOT = BASE.parent

HTML = (BASE / "index.html").read_text(encoding="utf-8")
CSS = (BASE / "css" / "style.css").read_text(encoding="utf-8")
JS = (BASE / "js" / "app.js").read_text(encoding="utf-8")
STORE = (BASE / "js" / "store.js").read_text(encoding="utf-8")
BANK_JSON = json.loads((BASE / "data" / "bank.json").read_text(encoding="utf-8"))

# 这些标签里的直接文字算「界面文案」，必须走 data-i18n
TEXT_TAGS = {"button", "h1", "h2", "h3", "p", "span", "b", "em", "label", "small"}

# 语言无关的特例：品牌图形、语言切换按钮自身的标签、运行时占位符
I18N_ALLOWLIST = {"NVIDIA EXAM", "中", "EN", "/", "--:--"}

# 每套配色都必须定义的完整变量集（少一个都不算配色）
REQUIRED_VARS = {
    "--bg", "--bg-soft", "--card", "--ink", "--ink-soft", "--ink-faint",
    "--accent", "--accent-ink", "--accent-soft", "--accent-2",
    "--ok", "--ok-soft", "--bad", "--bad-soft",
    "--line", "--line-soft", "--shadow",
}


def _extract_i18n(js: str) -> dict[str, dict[str, str]]:
    """从 I18N = { zh: {...}, en: {...} } 里抽出两种语言的键值表。

    手写一个小状态机：逐字符扫描，跟踪字符串字面量与花括号深度。
    值里允许出现 {r} 这类占位符花括号，所以不能天真地按 } 截断。
    """
    start = js.index("var I18N")
    obj_start = js.index("{", start)

    # 找到与 obj_start 配对的右花括号
    depth = 0
    in_str = False
    esc = False
    obj_end = None
    for i in range(obj_start, len(js)):
        c = js[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                obj_end = i
                break
    if obj_end is None:
        raise AssertionError("I18N 表没有闭合")

    body = js[obj_start : obj_end + 1]

    # 逐 token 扫描：字符串字面量或标点
    tokens: list[tuple[str, str]] = []
    in_str = False
    esc = False
    buf = ""
    for c in body:
        if in_str:
            buf += c
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
                tokens.append(("str", buf[1:-1]))
                buf = ""
            continue
        if c == '"':
            in_str = True
            buf = c
        elif c in "{}:,":
            if buf.strip():
                tokens.append(("sym", buf.strip()))
                buf = ""
            tokens.append(("p", c))
        else:
            buf += c

    tables: dict[str, dict[str, str]] = {}
    depth = 0
    lang = None
    k = 0
    while k < len(tokens):
        typ, val = tokens[k]
        if typ == "p":
            if val == "{":
                depth += 1
            elif val == "}":
                depth -= 1
                if depth == 1:
                    lang = None  # 离开某种语言的块
            k += 1
            continue
        # sym / str 后面跟 : 的是键
        if k + 1 < len(tokens) and tokens[k + 1] == ("p", ":"):
            key = val
            if depth == 1 and k + 2 < len(tokens) and tokens[k + 2] == ("p", "{"):
                lang = key  # zh: / en: 开启语言块
                depth += 1  # 这个 "{" 已被消费，深度要补上
                k += 3
                continue
            if depth == 2 and lang and k + 2 < len(tokens) and tokens[k + 2][0] == "str":
                tables.setdefault(lang, {})[key] = tokens[k + 2][1]
                k += 3
                continue
        k += 1
    return tables


class _Collector(HTMLParser):
    """收集带直接文字的元素与所有按钮，供 data-i18n 覆盖检查用。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[dict] = []
        self.records: list[tuple[str, str]] = []   # (tag, direct text)
        self.buttons: list[dict] = []              # 所有 button 的属性

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        d = {k: (v or "") for k, v in attrs}
        entry = {"tag": tag, "attrs": d, "text": ""}
        self.stack.append(entry)
        if tag == "button":
            self.buttons.append(entry)

    def handle_endtag(self, tag: str) -> None:
        if self.stack and self.stack[-1]["tag"] == tag:
            entry = self.stack.pop()
            text = entry["text"].strip()
            if text and tag in TEXT_TAGS and "data-i18n" not in entry["attrs"]:
                self.records.append((tag, text))

    def handle_data(self, data: str) -> None:
        if self.stack:
            self.stack[-1]["text"] += data


class TestI18N(unittest.TestCase):
    """§3.1 中英双语。"""

    def setUp(self) -> None:
        self.collector = _Collector()
        self.collector.feed(HTML)
        self.tables = _extract_i18n(JS)

    def test_both_languages_present(self) -> None:
        self.assertIn("zh", self.tables, "I18N 表缺 zh")
        self.assertIn("en", self.tables, "I18N 表缺 en")

    def test_same_key_sets(self) -> None:
        zh = set(self.tables["zh"])
        en = set(self.tables["en"])
        self.assertEqual(zh, en, "两种语言的 i18n 键必须完全一致")

    def test_every_data_i18n_key_in_both_tables(self) -> None:
        keys = set(re.findall(r'data-i18n="([A-Za-z0-9_.]+)"', HTML))
        keys |= set(re.findall(r'data-i18n-ph="([A-Za-z0-9_.]+)"', HTML))
        zh = set(self.tables["zh"])
        en = set(self.tables["en"])
        missing_zh = keys - zh
        missing_en = keys - en
        self.assertFalse(missing_zh, f"缺中文键: {sorted(missing_zh)}")
        self.assertFalse(missing_en, f"缺英文键: {sorted(missing_en)}")

    def test_no_hardcoded_visible_text(self) -> None:
        bad = [(t, s) for t, s in self.collector.records if s not in I18N_ALLOWLIST]
        self.assertFalse(
            bad,
            f"这些元素有硬编码文案，必须改用 data-i18n: {bad}",
        )

    def test_buttons_have_text(self) -> None:
        for btn in self.collector.buttons:
            # 有 data-i18n、有 id（运行时填字）、或有直接文字，三者占其一即可
            ok = (
                "data-i18n" in btn["attrs"]
                or "id" in btn["attrs"]
                or btn["text"].strip()
            )
            self.assertTrue(ok, f"按钮没有可见文字且无法被填充: {btn['attrs']}")

    def test_lang_attr_follows_toggle(self) -> None:
        self.assertIn("document.documentElement.lang", JS)
        self.assertIn('lang === "en" ? "en" : "zh-CN"', JS)

    def test_every_key_used_in_javascript_exists(self) -> None:
        """脚本里 t("…") 用到的键，两种语言都得有：漏一个，页面上就会出现键名本身。"""
        tables = _extract_i18n(JS)
        used = set(re.findall(r'\bt\(\s*"([A-Za-z0-9_.]+)"', JS))
        self.assertTrue(used, "没在脚本里找到任何 t() 调用")
        for lang in ("zh", "en"):
            missing = used - set(tables[lang])
            self.assertFalse(missing, f"{lang} 缺这些 i18n 键: {sorted(missing)}")


class TestPalettes(unittest.TestCase):
    """§3.2 配色变量集。"""

    def test_the_five_house_palettes(self) -> None:
        """全站就是这五套配色（AGENTS.md §3.2）：靛蓝 / 墨绿 / 琥珀 / 绯红 / 鎏金。"""
        blocks = re.findall(r'html\[data-theme="([a-z]+)"\]\s*\{([^}]*)\}', CSS)
        self.assertEqual(
            sorted(k for k, _ in blocks),
            ["amber", "indigo", "ink", "lotus", "obsidian"],
            "配色必须是全站统一的这五套",
        )

    def test_complete_identical_var_sets(self) -> None:
        blocks = re.findall(r'html\[data-theme="([a-z]+)"\]\s*\{([^}]*)\}', CSS)
        per_palette = {}
        for key, body in blocks:
            names = set(re.findall(r"(--[\w-]+)\s*:", body))
            names -= {"--swatch-main", "--swatch-bg"}   # 选择器自带的内联变量不算
            per_palette[key] = names
        for key, names in per_palette.items():
            self.assertTrue(
                REQUIRED_VARS <= names,
                f"配色 {key} 缺变量: {sorted(REQUIRED_VARS - names)}",
            )
        sets = list(per_palette.values())
        self.assertTrue(
            all(s == sets[0] for s in sets),
            "所有配色必须定义完全相同的变量集",
        )

    def test_theme_persisted(self) -> None:
        self.assertIn("lg_theme", JS)

    def test_palette_keys_match_hub(self) -> None:
        """与 hub 共用同一组配色键，全站切换偏好才能互通。"""
        shared = (ROOT / "hub" / "shared" / "module-header.js").read_text(encoding="utf-8")
        hub_keys = set(re.findall(r"key:\s*'([a-z]+)'", shared))
        ours = set(re.findall(r'\{ key: "([a-z]+)"', JS))
        self.assertEqual(ours, hub_keys, f"配色键与 hub 不一致: {sorted(ours ^ hub_keys)}")

    def test_palette_colours_match_the_shared_header(self) -> None:
        """连主色和底色都要一样：两个取色器显示不同的颜色，用户会以为换了一个配色。"""
        shared = (ROOT / "hub" / "shared" / "module-header.js").read_text(encoding="utf-8")
        theirs = {
            key: (zh, en, main.lower(), bg.lower())
            for key, zh, en, main, bg in re.findall(
                r"\{ key: '([a-z]+)', zh: '([^']+)', en: '([^']+)', main: '(#[0-9A-Fa-f]+)', bg: '(#[0-9A-Fa-f]+)'",
                shared,
            )
        }
        ours = {
            key: (zh, en, main.lower(), bg.lower())
            for key, zh, en, main, bg in re.findall(
                r'\{ key: "([a-z]+)",\s*zh: "([^"]+)",\s*en: "([^"]+)",\s*main: "(#[0-9A-Fa-f]+)",\s*bg: "(#[0-9A-Fa-f]+)"',
                JS,
            )
        }
        self.assertEqual(ours, theirs, "配色表与共享页眉不一致")
        for key, (_, _, main, _) in ours.items():
            self.assertRegex(main, r"^#[0-9a-f]{6}$", f"配色 {key} 的主色不是合法的六位十六进制")


class TestHouseStyle(unittest.TestCase):
    """§3 与 §9.6：页脚、共享页眉、主页入口和部署路径。"""

    def test_the_page_loads_the_site_footer(self) -> None:
        self.assertRegex(
            HTML, r'<script src="/shared/site-footer\.js\?v=[0-9a-f]{8}"></script>',
            "每个对外页面都要有全站页脚（备案号 + 隐私说明）",
        )

    def test_the_page_uses_the_shared_header_stylesheet(self) -> None:
        self.assertRegex(HTML, r'<link rel="stylesheet" href="/shared/module-header\.css\?v=[0-9a-f]{8}">')

    def test_the_brand_mark_is_a_drawn_icon_and_names_the_site(self) -> None:
        """§9.6：模块页眉的图标是画出来的线稿图标，不是表情符号；品牌名是「词境 Lexica」。"""
        mark = re.search(r'<span class="portal-brand-mark"[^>]*>(.*?)</span>', HTML, re.S)
        self.assertIsNotNone(mark, "缺少 .portal-brand-mark")
        self.assertIn("<svg", mark.group(1), "品牌图标必须是画出来的 SVG，不是表情符号")
        self.assertNotRegex(mark.group(1), r"[⚡🚀🎯]", "不要用表情符号当图标")
        self.assertRegex(HTML, r'<a class="portal-brand" href="/" aria-label="词境 Lexica">')

    def test_the_module_is_on_the_homepage(self) -> None:
        hub_html = (ROOT / "hub" / "index.html").read_text(encoding="utf-8")
        self.assertIn('data-project-link="nvidia"', hub_html, "主页上要有 NVIDIA 认证模拟考试的入口")
        config = (ROOT / "hub" / "js" / "config.js").read_text(encoding="utf-8")
        self.assertRegex(config, r"nvidia\s*:\s*[\"']/nvidia-exam/[\"']", "config.js 里少了 nvidia 的地址")

    def test_the_module_is_served_by_the_live_container(self) -> None:
        """真正上线的是容器里的 family 配置，不是宿主机那份旧安装脚本。"""
        conf = (ROOT / "word-puzzle" / "deploy" / "family" / "nginx" / "word-puzzle-family.conf").read_text(encoding="utf-8")
        self.assertIn("location ^~ /nvidia-exam/", conf)
        self.assertIn("alias @INSTALL_DIR@/site/nvidia-exam/;", conf)
        install = (ROOT / "word-puzzle" / "deploy" / "family" / "install.sh").read_text(encoding="utf-8")
        self.assertIn("$SITE_NEW/nvidia-exam", install)
        self.assertIn("nvidia-exam/index.html", install, "缺文件时安装脚本要停，不要上线一个残缺的网站")

    def test_the_module_is_registered_for_the_back_office(self) -> None:
        modules = (ROOT / "word-puzzle" / "server" / "modules.py").read_text(encoding="utf-8")
        self.assertIn('"id": "nvidia"', modules, "总后台要知道这个模块，成绩才有地方显示")

    def test_the_reporting_script_comes_before_the_page_script(self) -> None:
        """/shared/module-progress.js 定义 window.WPModule：它要排在 app.js 前面，
        否则 app.js 初始化时这个对象还不存在，上报的小结永远注册不上。"""
        self.assertLess(
            HTML.index("/shared/module-progress.js"),
            HTML.index("js/app.js"),
            "module-progress.js 必须排在 app.js 前面",
        )

    def test_every_asset_carries_a_computed_version(self) -> None:
        """§4：版本号是文件内容的哈希，不是手打的日期。"""
        for url, version in re.findall(r'(?:src|href)="([^"?#]+\.(?:js|css))(?:\?v=([^"]*))?"', HTML):
            if url.startswith("data:"):
                continue
            self.assertRegex(version, r"^[0-9a-f]{8}$", f"{url} 的 ?v= 不是内容哈希")


class TestPalettePicker(unittest.TestCase):
    """§3.3 对角双色方块取色器（色块由 buildPicker() 注入）。"""

    def test_swatches_have_both_colours(self) -> None:
        entries = re.findall(r'\{ key: "([a-z]+)",[^}]*main: "(#[0-9A-Fa-f]+)",\s*bg: "(#[0-9A-Fa-f]+)"', JS)
        self.assertGreaterEqual(len(entries), 3, "至少要三个色块")
        for key, main, bg in entries:
            self.assertTrue(main and bg, f"色块 {key} 缺主色或底色")

    def test_picker_host_exists(self) -> None:
        self.assertIn('id="themePicker"', HTML)

    def test_hard_stop_diagonal(self) -> None:
        shared = (ROOT / "hub" / "shared" / "module-header.css").read_text(encoding="utf-8")
        self.assertIn(
            "linear-gradient(to top right, var(--swatch-bg) 0 50%, var(--swatch-main) 50% 100%)",
            shared,
            "色块对角切分必须是硬边 50% 渐变（来自共享 module-header.css）",
        )

    def test_active_state_marked(self) -> None:
        self.assertIn("aria-pressed", JS)  # applyTheme 会标记当前配色

    def test_bilingual_tooltips(self) -> None:
        for key, zh, en in re.findall(
            r'\{ key: "([a-z]+)",\s*zh: "([^"]+)",\s*en: "([^"]+)"', JS
        ):
            self.assertTrue(zh and en, f"配色 {key} 的名字必须中英双语")


class TestBankData(unittest.TestCase):
    """题库数据完整性，以及 bank.json / bank.js 一致。"""

    def setUp(self) -> None:
        self.exams = BANK_JSON["exams"]
        js = (BASE / "data" / "bank.js").read_text(encoding="utf-8")
        self.assertIn("window.NVIDIA_BANK", js, "bank.js 必须定义 window.NVIDIA_BANK")
        start = js.index("{")
        end = js.rindex("}")
        self.bank_js = json.loads(js[start : end + 1])

    def test_bank_js_equals_json(self) -> None:
        self.assertEqual(self.bank_js, BANK_JSON, "bank.js 与 bank.json 内容不一致")

    def test_all_eight_certifications_are_there(self) -> None:
        """采集到的 8 项认证都要在题库里，不能只剩一门。"""
        codes = [e["code"] for e in self.exams]
        self.assertEqual(
            sorted(codes),
            ["NCA-AIIO", "NCA-GENL", "NCA-GENM", "NCP-AAI", "NCP-AII",
             "NCP-AIN", "NCP-AIO", "NCP-OUSD"],
            "认证科目不对",
        )
        for exam in self.exams:
            for field in ("id", "code", "name", "nameZh", "shortZh", "shortEn", "level"):
                self.assertTrue(exam.get(field), f"{exam.get('code')} 缺字段 {field}")
            self.assertTrue(exam.get("official"), f"{exam['code']} 缺官方考试信息")
            self.assertGreater(exam["official"].get("questions", 0), 0)
            self.assertGreater(exam["official"].get("durationMin", 0), 0)
            self.assertEqual(exam["passPct"], exam["official"]["passPct"])

    def test_weights_sum_to_100(self) -> None:
        for exam in self.exams:
            self.assertEqual(
                sum(d["weight"] for d in exam["domains"]), 100,
                f"{exam['code']} 的知识域权重合计必须是 100%",
            )

    def test_question_integrity(self) -> None:
        for exam in self.exams:
            domain_ids = {d["id"] for d in exam["domains"]}
            ids = set()
            for q in exam["questions"]:
                self.assertNotIn(q["id"], ids, f"{exam['code']} 题目 id 重复: {q['id']}")
                ids.add(q["id"])
                self.assertIn(q["domain"], domain_ids, f"{exam['code']} 未知知识域: {q['domain']}")
                n = len(q["o"])
                self.assertEqual(len(q["oZh"]), n, f"{exam['code']} 题 {q['id']} 选项中英文数量不一致")
                self.assertTrue(0 < len(q["a"]) <= n, f"{exam['code']} 题 {q['id']} 答案下标越界")
                for a in q["a"]:
                    self.assertTrue(0 <= a < n, f"{exam['code']} 题 {q['id']} 答案下标越界: {a}")
                self.assertEqual(bool(q["multi"]), len(q["a"]) > 1,
                                 f"{exam['code']} 题 {q['id']} multi 标记与答案数不符")
                for field in ("q", "qZh", "e", "eZh"):
                    self.assertTrue(q.get(field), f"{exam['code']} 题 {q['id']} 缺字段 {field}")
                self.assertTrue(q.get("src"), f"{exam['code']} 题 {q['id']} 缺来源")

    def test_every_source_has_a_bilingual_name(self) -> None:
        """题目上的来源标签是界面文案，两种语言都要有。"""
        sources = {s["id"]: s for s in BANK_JSON["sources"]}
        used = {q["src"] for exam in self.exams for q in exam["questions"]}
        for src in used:
            self.assertIn(src, sources, f"来源 {src} 没有在 sources 表里")
            self.assertTrue(sources[src].get("zh") and sources[src].get("en"),
                            f"来源 {src} 的名字没有中英双语")

    def test_the_collected_bank_is_big_enough(self) -> None:
        """采集到的题目量（1224 道）不能因为整理脚本出错而缩水。"""
        total = sum(len(e["questions"]) for e in self.exams)
        self.assertGreaterEqual(total, 1200, f"题库只有 {total} 道题")
        for exam in self.exams:
            self.assertGreaterEqual(len(exam["questions"]), 80, f"{exam['code']} 题量太少")


class TestStudyGuides(unittest.TestCase):
    """学习指南：索引数据、按科目拆分的正文，以及页面上的指南视图。"""

    def setUp(self) -> None:
        self.guides = json.loads((BASE / "data" / "guides.json").read_text(encoding="utf-8"))

    def test_guides_js_equals_json(self) -> None:
        js = (BASE / "data" / "guides.js").read_text(encoding="utf-8")
        self.assertIn("window.NVIDIA_GUIDES", js)
        start = js.index("{")
        end = js.rindex("}")
        self.assertEqual(json.loads(js[start:end + 1]), self.guides)

    def test_every_certification_has_guides(self) -> None:
        codes = {c["code"] for c in self.guides["certs"]}
        self.assertEqual(len(codes), 8, "指南索引里的科目数不对")
        total = 0
        for cert in self.guides["certs"]:
            self.assertTrue(cert["guides"], f"{cert['code']} 没有指南")
            total += len(cert["guides"])
            for g in cert["guides"]:
                self.assertTrue(g["title"], f"{cert['code']} 有指南没有标题")
                self.assertTrue(g["repo"], f"{cert['code']} 的指南《{g['title']}》没有来源仓库")
                self.assertTrue(g["url"].startswith("https://"), "指南原文链接不是 https")
        self.assertGreaterEqual(total, 500, f"只有 {total} 篇指南")

    def test_the_split_documents_exist(self) -> None:
        """按科目拆开的正文要在仓库里，页面上的「读正文」链接才不会点空。"""
        for cert in self.guides["certs"]:
            path = BASE / "docs" / "guides" / f"{cert['code']}.md"
            self.assertTrue(path.is_file(), f"缺少 {path.name}")
            text = path.read_text(encoding="utf-8")
            self.assertIn(cert["code"], text, f"{path.name} 里没有科目代码")
            self.assertGreater(len(text), 1000, f"{path.name} 太短了")
            self.assertNotIn("[邮箱已隐去]", text, f"{path.name} 留有邮箱占位文字")
            self.assertNotIn("[号码已隐去]", text, f"{path.name} 留有号码占位文字")

    def test_the_page_has_a_guide_view(self) -> None:
        self.assertIn('id="view-guides"', HTML, "页面缺少指南视图")
        self.assertIn('id="guideList"', HTML, "页面缺少指南列表")
        self.assertIn("data/guides.js", HTML, "页面没有加载指南数据")
        self.assertIn("renderGuides", JS, "app.js 里没有渲染指南的函数")

    def test_the_collection_notes_are_shipped(self) -> None:
        """采集过程与口径要留在仓库里，别人才知道这些题是从哪来的。"""
        notes = BASE / "docs" / "采集说明.md"
        self.assertTrue(notes.is_file(), "缺少 docs/采集说明.md")
        text = notes.read_text(encoding="utf-8")
        self.assertIn("ExamTopics", text)
        self.assertNotRegex(text, r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9-]+",
                            "采集说明里有邮箱地址：仓库是公开的")


class TestRawFiles(unittest.TestCase):
    """原始采集产物：留着才能重跑整理脚本，也能核对出处。"""

    def test_the_collected_files_are_in_the_repository(self) -> None:
        for name in ("nvidia_cert_data.json", "学习指南汇总.md", "采集说明.md",
                     "NVIDIA认证备考资料.xlsx", "nvidia-cert-study-hub.html"):
            path = BASE / "raw-files" / name
            self.assertTrue(path.is_file(), f"raw-files/{name} 不在仓库里")
            self.assertGreater(path.stat().st_size, 1000, f"raw-files/{name} 是空的")

    def test_no_email_addresses_in_the_raw_copies(self) -> None:
        """原始副本不含邮箱地址或替代占位文字。"""
        for name in ("学习指南汇总.md", "采集说明.md"):
            text = (BASE / "raw-files" / name).read_text(encoding="utf-8")
            self.assertNotRegex(text, r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9-]+",
                                f"raw-files/{name} 里有邮箱地址")
            self.assertNotIn("[邮箱已隐去]", text, f"raw-files/{name} 留有邮箱占位文字")
            self.assertNotIn("[号码已隐去]", text, f"raw-files/{name} 留有号码占位文字")


class TestBuildScript(unittest.TestCase):
    """整理脚本要能重跑，而且重跑的结果与仓库里的一样。"""

    def test_rebuilding_reproduces_the_bank(self) -> None:
        import subprocess
        before = {
            name: (BASE / "data" / name).read_text(encoding="utf-8")
            for name in ("bank.json", "bank.js", "guides.json", "guides.js")
        }
        proc = subprocess.run(
            ["python3", str(BASE / "tools" / "build_data.py")],
            capture_output=True, text=True, cwd=BASE, timeout=300,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        for name, text in before.items():
            self.assertEqual((BASE / "data" / name).read_text(encoding="utf-8"), text,
                             f"重跑 tools/build_data.py 后 {name} 变了")


class TestMultiExamUi(unittest.TestCase):
    """页面上的科目切换与本地存储的隔离。"""

    def test_the_page_has_an_exam_picker(self) -> None:
        self.assertIn('id="examPicker"', HTML, "页面缺少科目切换")
        self.assertIn("exam.pick", JS, "app.js 里没有科目切换的文案")

    def test_question_ids_are_namespaced_by_exam(self) -> None:
        """不同科目的题号会重复，本地存储的键必须带上科目。"""
        self.assertIn('EXAM.id + ":" + q.id', JS, "作答记录的键没有带上科目")

    def test_the_chosen_exam_is_remembered(self) -> None:
        self.assertIn("nx_exam", JS, "选中的科目没有记在 localStorage 里")

    def test_the_browse_view_shows_the_source(self) -> None:
        """题目来自公开题库，答完要能点回原页核对。"""
        self.assertIn("sourceLabel", JS)
        self.assertIn("q.source", JS)


class TestPersistenceAndLint(unittest.TestCase):
    """§3.6 本地存储与 JS 语法体检。"""

    def test_lang_persisted(self) -> None:
        self.assertIn("lg_lang", JS)

    def test_state_persisted(self) -> None:
        self.assertIn("localStorage.setItem", STORE)

    def test_js_syntax_check(self) -> None:
        import subprocess
        r = subprocess.run(
            ["python3", str(ROOT / "word-puzzle" / "tools" / "check_js.py")],
            capture_output=True, text=True, cwd=ROOT,
        )
        self.assertEqual(r.returncode, 0, "check_js.py 语法体检未通过:\n" + r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
