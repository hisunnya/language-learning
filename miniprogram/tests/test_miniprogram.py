"""小程序的静态规范校验 + 行为测试（node 缺失时跳过行为测试）。

没有微信开发者工具时，这里能守住的是：配置文件合法、页面文件齐全、WXML 标签配平、
所有文字都走语言表、五套配色定义完整一致、配色选择器的样式是规范里的方形对角切分。
WXML 的真实渲染仍需要在微信开发者工具里看一眼。

跑法::

    cd miniprogram && python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NODE = shutil.which("node") or shutil.which("nodejs")


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


PAGES = ("pages/index/index", "pages/game/game")
I18N = read("utils/i18n.js")
APP_WXSS = read("app.wxss")
PREFS = read("utils/prefs.js")


def i18n_keys(lang: str) -> set[str]:
    other = "en" if lang == "zh" else "zh"
    start = I18N.index("  %s: {" % lang)
    end = I18N.index("  %s: {" % other) if lang == "zh" else I18N.index("\nvar GRADE_EN")
    return set(re.findall(r"^    (\w+):", I18N[start:end], re.M))


def theme_blocks() -> dict[str, dict[str, str]]:
    blocks = {}
    for selector, body in re.findall(r"^(page|\.theme-\w+) \{\n(.*?)\n\}", APP_WXSS, re.M | re.S):
        blocks.setdefault(selector, {}).update(dict(re.findall(r"(--game-[\w-]+):\s*([^;]+);", body)))
    return blocks


class TestProjectFiles(unittest.TestCase):
    def test_json_files_are_valid_and_pages_are_complete(self):
        app = json.loads(read("app.json"))
        self.assertEqual(sorted(app["pages"]), sorted(PAGES))
        for rel in PAGES:
            for ext in ("js", "json", "wxml", "wxss"):
                self.assertTrue((ROOT / f"{rel}.{ext}").exists(), f"{rel}.{ext}")
            json.loads(read(f"{rel}.json"))
        json.loads(read("project.config.json"))
        self.assertNotIn("WorkBuddy", read("sitemap.json"))

    def test_wxml_tags_are_balanced(self):
        for rel in PAGES:
            text = re.sub(r"<!--.*?-->", "", read(f"{rel}.wxml"), flags=re.S)
            for tag in ("view", "text"):
                opened = len(re.findall(r"<%s[\s>]" % tag, text))
                closed = len(re.findall(r"</%s>" % tag, text))
                self.assertEqual(opened, closed, f"{rel}.wxml 的 <{tag}> 没有配平")


class TestLanguage(unittest.TestCase):
    def test_both_languages_have_the_same_keys(self):
        self.assertEqual(i18n_keys("zh"), i18n_keys("en"))
        self.assertGreater(len(i18n_keys("zh")), 30)

    def test_every_key_used_by_a_page_exists(self):
        keys = i18n_keys("zh")
        for rel in PAGES:
            for ext in ("wxml", "js"):
                used = set(re.findall(r"\bt\.(\w+)", read(f"{rel}.{ext}")))
                self.assertEqual(used - keys, set(), f"{rel}.{ext} 用了不存在的文字键")

    def test_wxml_has_no_hard_coded_visible_text(self):
        allowed = {"词", "EN", "CN", "中", "/", "→", "🔊", "LEXICA", "+"}
        for rel in PAGES:
            text = re.sub(r"<!--.*?-->", "", read(f"{rel}.wxml"), flags=re.S)
            text = re.sub(r"\{\{.*?\}\}", "", text, flags=re.S)
            for node in re.findall(r">([^<>]+)<", text):
                node = node.strip()
                if node and node not in allowed:
                    self.fail(f"{rel}.wxml 里有写死的文字：{node!r}，应放进 utils/i18n.js")

    def test_js_has_no_hard_coded_chinese_messages(self):
        for rel in ("pages/index/index.js", "pages/game/game.js"):
            code = re.sub(r"//.*|/\*.*?\*/", "", read(rel), flags=re.S)
            for literal in re.findall(r"'([^'\n]*)'", code):
                self.assertIsNone(re.search(r"[一-龥]", literal), f"{rel} 里有写死的中文：{literal!r}")

    def test_language_toggle_and_remembered_choice_exist(self):
        wxml = read("pages/index/index.wxml")
        self.assertIn('bindtap="onToggleLang"', wxml)
        self.assertIn("wp_lang", PREFS)
        self.assertIn("wp_theme", PREFS)


class TestPalettes(unittest.TestCase):
    def test_at_least_three_palettes_with_identical_variable_sets(self):
        blocks = theme_blocks()
        themes = {k: v for k, v in blocks.items() if k.startswith(".theme-")}
        self.assertGreaterEqual(len(themes), 3)
        reference = set(blocks["page"])
        self.assertGreater(len(reference), 25)
        for name, variables in themes.items():
            self.assertEqual(set(variables), reference, f"{name} 缺少或多出变量")

    def test_palette_keys_match_between_js_and_wxss(self):
        js_keys = set(re.findall(r"key: '(\w+)'", PREFS))
        css_keys = {k[len(".theme-"):] for k in theme_blocks() if k.startswith(".theme-")}
        self.assertEqual(js_keys, css_keys)

    def test_swatch_colours_are_the_palettes_own_accent_and_background(self):
        blocks = theme_blocks()
        for key, main, bg in re.findall(r"key: '(\w+)'.*?main: '(#\w+)', bg: '(#\w+)'", PREFS):
            css = blocks[".theme-" + key]
            self.assertEqual(css["--game-primary"].lower(), main.lower(), key)
            self.assertEqual(css["--game-page"].lower(), bg.lower(), key)

    def test_palette_names_read_as_two_colours_in_both_languages(self):
        for zh, en in re.findall(r"zh: '([^']+)', en: '([^']+)'", PREFS):
            self.assertIn(" · ", zh)
            self.assertIn(" · ", en)

    def test_pages_use_variables_not_hard_coded_colours(self):
        for rel in ("pages/index/index.wxss", "pages/game/game.wxss"):
            text = read(rel)
            self.assertEqual(re.findall(r"#[0-9a-fA-F]{3,8}\b", text), [], rel)
            # 唯一允许的固定色：弹窗的黑色投影，所有配色都一样
            self.assertEqual([c for c in re.findall(r"rgba\([^)]*\)", text) if c != "rgba(0, 0, 0, 0.25)"], [], rel)

    def test_every_root_and_overlay_carries_the_theme_class(self):
        self.assertIn('class="page theme-{{theme}}"', read("pages/index/index.wxml"))
        game = read("pages/game/game.wxml")
        self.assertIn('class="app theme-{{theme}}"', game)
        self.assertEqual(game.count('class="overlay theme-{{theme}}"'), 2, "遮罩层是根节点的兄弟，要各自带主题类")

    def test_picker_follows_the_house_style(self):
        wxml = read("pages/index/index.wxml")
        wxss = read("pages/index/index.wxss")
        self.assertIn('style="{{item.style}}"', wxml)
        self.assertIn('aria-label="{{item.name}}"', wxml)
        self.assertIn('bindtap="onPickTheme"', wxml)
        block = re.search(r"\.swatch \{(.*?)\n\}", wxss, re.S).group(1)
        self.assertIn("border-radius: 8rpx", block, "方块，不是圆")
        self.assertRegex(block, r"linear-gradient\(to top right, var\(--swatch-bg\) 50%, var\(--swatch-main\) 50%\)")
        self.assertIn("swatch-on", wxss)
        # 方块在顶部右侧，和语言切换并排
        self.assertLess(wxml.index('class="lang-btn"'), wxml.index('class="swatches"'))
        self.assertLess(wxml.index('class="swatches"'), wxml.index('class="title"'))


class TestAudioConfig(unittest.TestCase):
    def test_audio_is_off_by_default_and_hidden_in_the_ui(self):
        config = read("config.js")
        self.assertRegex(config, r"audioCloudPrefix:\s*''")
        self.assertRegex(config, r"audioBase:\s*''")
        self.assertIn("audioOn && item.t === 'en'", read("pages/game/game.wxml"))
        self.assertIn("audio.configure", read("app.js"))


class TestSharedCore(unittest.TestCase):
    def test_core_has_pause_resume_and_the_replay_fix(self):
        core = read("utils/game-core.js")
        self.assertIn("pause: function", core)
        self.assertIn("resume: function", core)
        self.assertIn("st.score = st.levelStartScore || 0;", core)
        # 与网站版的一致性由 word-puzzle/tests/js/core_parity.test.js 守着


@unittest.skipUnless(NODE, "本机没有 node，跳过小程序行为测试")
class TestBehaviour(unittest.TestCase):
    def test_utils_and_pages(self):
        proc = subprocess.run([NODE, str(ROOT / "tests" / "js" / "utils.test.js")],
                              capture_output=True, text=True, timeout=120)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("通过", proc.stdout)


if __name__ == "__main__":
    unittest.main()
