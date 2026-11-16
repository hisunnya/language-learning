"""读音练习：入口按钮在「开始游戏」前面、页面结构、离线版、node 行为测试。"""
from __future__ import annotations

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
NODE = shutil.which("node") or shutil.which("nodejs")


def read(name):
    return (WEB / name).read_text(encoding="utf-8")


class TestEntryPoints(unittest.TestCase):
    def test_the_practice_button_comes_right_before_play_in_every_bank_list(self):
        for script in ("js/page-home.js", "js/page-bank.js"):
            code = read(script)
            practice, play = code.index("/practice.html?bank="), code.index("/play.html?bank=")
            self.assertLess(practice, play, script + "：读音练习在开始游戏前面")
            self.assertIn("bank_practice", code)

    def test_the_recent_card_uses_the_same_row_so_it_has_the_button_too(self):
        home = read("js/page-home.js")
        self.assertIn("return bankItem(x.bank,", home)

    def test_the_offline_tab_lets_the_teacher_choose_the_type(self):
        html = read("bank.html")
        self.assertEqual(len(re.findall(r'name="offKind"', html)), 2)
        self.assertIn('value="practice"', html)
        code = read("js/page-bank.js")
        self.assertIn("{ kind: offlineKind() }", code)
        self.assertIn("input[name=\"offKind\"]:checked", code)


class TestPage(unittest.TestCase):
    def test_structure_and_script_order(self):
        html = read("practice.html")
        for needle in ('id="pracMount"', 'id="pracToggle"', 'id="pracOffline"', 'id="pracBack"', 'id="pracGame"', "css/practice.css"):
            self.assertIn(needle, html, needle)
        order = [html.index(s) for s in ("js/i18n.js", "js/api.js", "js/auth-ui.js", "js/recent.js", "js/practice-ui.js", "js/page-practice.js")]
        self.assertEqual(order, sorted(order))
        self.assertRegex(html, r'<button type="button" class="btn ghost admin-only" id="pracOffline"', "离线下载只给老师")
        self.assertIn("sessionStorage.getItem('wp_role')", html, "和别的页面一样，先按缓存的角色设好样式")

    def test_audio_comes_from_the_backend_and_the_open_is_recorded_like_a_game(self):
        code = read("js/page-practice.js")
        self.assertIn("base: API.path('/api/audio/')", code)
        self.assertIn("API.post('/api/recent', { bank_id: id })", code)
        self.assertIn("API.post('/api/banks/' + bank.id + '/offline', { kind: 'practice' })", code)
        self.assertIn("player.prefetch(flat, 30)", code)

    def test_styles_use_the_palette_variables_not_fixed_colours(self):
        css = read("css/practice.css")
        for needle in (".prac-row", ".prac-cn-text", "touch-action: pan-y", ".prac-row.on .prac-cn-text"):
            self.assertIn(needle, css)
        self.assertRegex(css, r"\.prac-cn-text \{[^}]*display: none", "中文默认藏着")
        self.assertRegex(css, r"\.prac-row\.on \.prac-cn-text \{ display: block; \}", "点开之后才显示")
        self.assertNotRegex(re.sub(r"var\(--[a-z0-9-]+,\s*#[0-9a-fA-F]{3,6}\)", "", css), r"#[0-9a-fA-F]{3,6}\b", "颜色都走配色变量（括号里的只是默认值）")


class TestOfflineBuilder(unittest.TestCase):
    BANK = {"id": 1, "title": "t<b>", "level1": "初中", "level2": "七年级", "level3": "上册", "level4": "全部"}
    GROUPS = [{"unit": "Unit 1", "words": [{"en": "sth.", "cn": "某事", "ipa": ""}, {"en": "apple", "cn": "苹果", "ipa": "/x/"}]}]

    def test_filename_marks_the_practice_page(self):
        name, _ = offline.build_practice_html(self.BANK, self.GROUPS, audio={"sth.": b"ID3x"})
        self.assertIn("-读音练习-", name)
        self.assertNotIn("读音练习", offline.build_filename(self.BANK))

    def test_page_has_no_game_and_no_external_references_and_escapes_the_title(self):
        _, html = offline.build_practice_html(self.BANK, self.GROUPS, audio={"sth.": b"ID3x", "apple": b"ID3y"})
        self.assertNotIn("WPGame", html)
        self.assertNotIn("t<b>", html)
        self.assertIsNone(re.search(r"(src|href)=[\"']https?://", html))
        self.assertIn("data:audio/mpeg;base64,", html)

    def test_a_bank_without_words_is_refused(self):
        with self.assertRaises(ValueError):
            offline.build_practice_html(self.BANK, [])

    def test_words_that_could_close_the_script_block_are_escaped(self):
        groups = [{"unit": "U", "words": [{"en": "</script><script>alert(1)", "cn": "x", "ipa": ""}]}]
        _, html = offline.build_practice_html(self.BANK, groups, audio={})
        self.assertNotIn("</script><script>alert(1)", html)


@unittest.skipUnless(NODE, "本机没有 node，跳过读音练习的行为测试")
class TestBehaviour(unittest.TestCase):
    def test_practice_ui(self):
        proc = subprocess.run([NODE, str(ROOT / "tests" / "js" / "practice.test.js")], capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("项通过", proc.stdout)


if __name__ == "__main__":
    unittest.main()
