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
I18N_ALLOWLIST = {"⚡", "NVIDIA EXAM", "中", "EN", "/", "--:--"}

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


class TestPalettes(unittest.TestCase):
    """§3.2 配色变量集。"""

    def test_at_least_three_palettes(self) -> None:
        blocks = re.findall(r'html\[data-theme="([a-z]+)"\]\s*\{([^}]*)\}', CSS)
        self.assertGreaterEqual(len(blocks), 3, "至少要三套配色")

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
        shared = open(ROOT / "hub" / "shared" / "module-header.js", encoding="utf-8").read()
        hub_keys = set(re.findall(r"key:\s*'([a-z]+)'", shared))
        ours = set(re.findall(r'\{ key: "([a-z]+)"', JS))
        self.assertEqual(ours, hub_keys, f"配色键与 hub 不一致: {sorted(ours ^ hub_keys)}")


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
        shared = open(ROOT / "hub" / "shared" / "module-header.css", encoding="utf-8").read()
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
        self.exam = BANK_JSON["exams"][0]
        js = (BASE / "data" / "bank.js").read_text(encoding="utf-8")
        self.assertIn("window.NVIDIA_BANK", js, "bank.js 必须定义 window.NVIDIA_BANK")
        start = js.index("{")
        end = js.rindex("}")
        self.bank_js = json.loads(js[start : end + 1])

    def test_bank_js_equals_json(self) -> None:
        self.assertEqual(self.bank_js, BANK_JSON, "bank.js 与 bank.json 内容不一致")

    def test_weights_sum_to_100(self) -> None:
        self.assertEqual(
            sum(d["weight"] for d in self.exam["domains"]), 100,
            "知识域权重合计必须是 100%",
        )

    def test_question_integrity(self) -> None:
        domain_ids = {d["id"] for d in self.exam["domains"]}
        ids = set()
        for q in self.exam["questions"]:
            self.assertNotIn(q["id"], ids, f"题目 id 重复: {q['id']}")
            ids.add(q["id"])
            self.assertIn(q["domain"], domain_ids, f"未知知识域: {q['domain']}")
            n = len(q["o"])
            self.assertEqual(len(q["oZh"]), n, f"题 {q['id']} 选项中英文数量不一致")
            self.assertTrue(0 < len(q["a"]) <= n, f"题 {q['id']} 答案下标越界")
            for a in q["a"]:
                self.assertTrue(0 <= a < n, f"题 {q['id']} 答案下标越界: {a}")
            self.assertEqual(bool(q["multi"]), len(q["a"]) > 1, f"题 {q['id']} multi 标记与答案数不符")
            for field in ("q", "qZh", "e", "eZh"):
                self.assertTrue(q.get(field), f"题 {q['id']} 缺字段 {field}")


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
