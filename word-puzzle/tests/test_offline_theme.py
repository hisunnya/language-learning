"""离线单文件页（配对游戏、读音练习）也有五套配色可选，和网站一模一样。"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, ROOT.as_posix())

from server import offline                       # noqa: E402

WEB = ROOT / "web"
HUB_HEADER = (ROOT.parent / "hub" / "shared" / "module-header.js").read_text(encoding="utf-8")
NODE = shutil.which("node") or shutil.which("nodejs")
BANK = {"id": 1, "title": "t", "level1": "a", "level2": "b", "level3": "c", "level4": "d", "word_count": 2}
GROUPS = [{"unit": "U", "words": [{"en": "apple", "cn": "苹果", "ipa": ""}, {"en": "sth.", "cn": "某事", "ipa": ""}]}]
AUDIO = {"apple": b"ID3a", "sth.": b"ID3b"}


def palettes(js):
    """从脚本里读出 PALETTES 数组：{key, zh, en, main, bg}。"""
    block = re.search(r"var PALETTES = \[(.*?)\];", js, re.S).group(1)
    return re.findall(r"\{ key: '(\w+)', zh: '([^']+)', en: '([^']+)', main: '(#\w+)', bg: '(#\w+)' \}", block)


class TestSamePalettesAsTheSite(unittest.TestCase):
    def test_names_and_colours_match_the_site_header_exactly(self):
        site = palettes(HUB_HEADER)
        mine = palettes((WEB / "js" / "offline-theme.js").read_text(encoding="utf-8"))
        self.assertEqual(len(site), 5)
        self.assertEqual(mine, site, "离线页的配色和网站页眉里的必须一模一样（名字、两个颜色）")

    def test_every_palette_defines_the_variables_the_offline_pages_use(self):
        css = (WEB / "css" / "app.css").read_text(encoding="utf-8")
        lines = [l for l in css.splitlines() if l.startswith("html[data-theme=")]
        self.assertEqual(len(lines), 5)
        used = set(re.findall(r"var\((--[a-z0-9-]+)", (WEB / "css" / "practice.css").read_text(encoding="utf-8")))
        used |= {"--bg1", "--card", "--ink", "--ink2", "--heading", "--line", "--blue", "--on-primary"}
        for line in lines:
            defined = set(re.findall(r"(--[a-z0-9-]+):", line))
            self.assertEqual(used - defined, set(), line[:30])

    def test_game_css_has_the_five_palettes_too(self):
        css = (WEB / "css" / "game.css").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r'^html\[data-theme="(?:indigo|ink|amber|lotus|obsidian)"\]', css, re.M)), 5)


class TestPages(unittest.TestCase):
    def pages(self):
        return {"game": offline.build_offline_html(BANK, GROUPS, audio=AUDIO)[1],
                "practice": offline.build_practice_html(BANK, GROUPS, audio=AUDIO)[1]}

    def test_both_offline_pages_carry_the_picker(self):
        for kind, html in self.pages().items():
            self.assertIn('id="offline-theme"', html, kind)
            self.assertIn("WPTheme.init(document.getElementById('offline-theme'))", html, kind)
            self.assertIn("var PALETTES", html, kind)
            self.assertIn(".theme-chip .swatch", html, kind)
            self.assertEqual(len(re.findall(r'html\[data-theme="(?:indigo|ink|amber|lotus|obsidian)"\] ?\{', html)), 5, kind)

    def test_the_saved_palette_is_applied_before_the_page_is_painted(self):
        for kind, html in self.pages().items():
            head = html[:html.index("<body>")]
            self.assertIn("WPTheme.early();", head, kind)
            self.assertLess(head.index("var PALETTES"), head.index("WPTheme.early();"), kind)

    def test_the_inlined_palettes_are_real_css(self):
        html = self.pages()["practice"]
        head = html[:html.index("<body>")]
        self.assertNotIn("{{", head)
        self.assertNotIn("}}", head)
        self.assertRegex(head, r'html\[data-theme="obsidian"\] \{ --bg1:#08080a;')

    def test_pages_still_have_no_external_references_and_keep_the_audio(self):
        for kind, html in self.pages().items():
            self.assertIsNone(re.search(r"(src|href)=[\"']https?://", html), kind)
            self.assertIn("data:audio/mpeg;base64,", html, kind)

    def test_the_swatch_is_the_house_style_square_split_diagonally_with_a_hard_stop(self):
        css = (WEB / "css" / "offline-theme.css").read_text(encoding="utf-8")
        self.assertIn("border-radius: 4px", css)
        self.assertIn("linear-gradient(to top right, var(--swatch-bg) 0 50%, var(--swatch-main) 50% 100%)", css)
        self.assertIn("aria-pressed=\"true\"", css)


    def test_the_game_bar_wraps_so_the_picker_is_not_pushed_off_a_phone_screen(self):
        css = (WEB / "css" / "offline-theme.css").read_text(encoding="utf-8")
        self.assertIn(".bar { flex-wrap: wrap;", css)
        self.assertRegex(css, r"@media \(max-width: 560px\) \{ #offline-theme \{ flex: 1 1 0;")
        html = offline.build_offline_html(BANK, GROUPS, audio=AUDIO)[1]
        self.assertLess(html.index('id="btn-lang"'), html.index('id="offline-theme"'), "选择器在语言按钮后面，窄屏时一起占第二行")


@unittest.skipUnless(NODE, "本机没有 node，跳过离线页配色的行为测试")
class TestBehaviour(unittest.TestCase):
    def test_offline_theme(self):
        proc = subprocess.run([NODE, str(ROOT / "tests" / "js" / "offline_theme.test.js")], capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("项通过", proc.stdout)


if __name__ == "__main__":
    unittest.main()
