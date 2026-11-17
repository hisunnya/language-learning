"""微信内置浏览器的兼容：wechat.js 的行为（node，缺 node 时跳过）、不用旧内核不认的语法、移动端输入框字号。

学生大多从手机微信里直接点开链接，所以这些是站点的基本要求，不是锦上添花。
"""
from __future__ import annotations

import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
NODE = shutil.which("node") or shutil.which("nodejs")
PAGES = sorted((ROOT / "web").glob("*.html"))


def strip_comments(code: str) -> str:
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.S)
    return re.sub(r"(^|\s)//[^\n]*", r"\1", code)


@unittest.skipUnless(NODE, "本机没有 node，跳过 wechat.js 的行为测试")
class TestWeChatBehaviour(unittest.TestCase):
    def test_wechat_js_behaviour(self):
        proc = subprocess.run([NODE, str(ROOT / "tests" / "js" / "wechat.test.js")], capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("通过", proc.stdout)


class TestOldBrowserSyntax(unittest.TestCase):
    """旧一点的微信内核（安卓 X5 / 老 iOS）遇到不认的语法，整个脚本都不执行，页面就是白屏。所以线上脚本保持 ES5。"""
    FILES = sorted((ROOT / "web" / "js").glob("*.js")) + sorted((REPO / "hub" / "shared").glob("*.js"))
    FORBIDDEN = (
        (r"=>", "箭头函数"), (r"(?<![\w$.])(let|const)\s+[\w$\[{]", "let / const"), (r"\basync\s+function|\bawait\s", "async / await"),
        (r"\?\.[\w$\[(]", "可选链 ?."), (r"\?\?(?!=)", "空值合并 ??"), (r"`", "模板字符串"), (r"\bclass\s+\w+\s*[{ ]", "class"),
    )

    def test_scripts_stay_es5(self):
        problems = []
        for path in self.FILES:
            code = strip_comments(path.read_text(encoding="utf-8"))
            code = re.sub(r"(['\"])(?:\\.|(?!\1).)*\1", "''", code)           # 字符串里出现这些符号不算
            for pattern, label in self.FORBIDDEN:
                if re.search(pattern, code):
                    problems.append("%s 用了 %s" % (path.name, label))
        self.assertEqual(problems, [], "\n".join(problems))

    def test_there_are_scripts_to_check(self):
        self.assertGreater(len(self.FILES), 20)


class TestMobileInput(unittest.TestCase):
    def test_inputs_are_16px_on_phones_so_ios_does_not_zoom_in(self):
        css = (ROOT / "web" / "css" / "app.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"@media \(max-width: 820px\) \{\s*input:not")
        self.assertIn("font-size: 16px !important", css)

    def test_wechat_may_not_rescale_the_text(self):
        css = (ROOT / "web" / "css" / "app.css").read_text(encoding="utf-8")
        self.assertIn("-webkit-text-size-adjust: 100%", css)

    def test_every_page_loads_the_app_stylesheet_where_inputs_are(self):
        for page in PAGES:
            html = page.read_text(encoding="utf-8")
            if "<input" in html or "<select" in html:
                self.assertIn("css/app.css", html, page.name)


class TestWeChatHook(unittest.TestCase):
    def test_header_loads_wechat_js_only_inside_wechat(self):
        header = (REPO / "hub" / "shared" / "module-header.js").read_text(encoding="utf-8")
        self.assertIn("/MicroMessenger/i.test(navigator.userAgent", header)
        self.assertIn("wechat.js", header)
        self.assertTrue((REPO / "hub" / "shared" / "wechat.js").exists())

    def test_pages_with_downloads_declare_it(self):
        for name in ("admin.html", "bank.html"):
            self.assertIn("data-wx-download", (ROOT / "web" / name).read_text(encoding="utf-8"), name)

    def test_the_game_page_does_not_get_a_banner(self):
        self.assertNotIn("data-wx-download", (ROOT / "web" / "play.html").read_text(encoding="utf-8"))


class TestWideStaffPages(unittest.TestCase):
    def test_staff_pages_follow_the_window_width_on_desktop_but_students_keep_the_narrow_layout(self):
        css = (ROOT / "web" / "css" / "app.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"@media \(min-width: 1000px\) \{\s*html\.role-admin body\[data-wide\] \.wrap \{ max-width: 1\d{3}px")
        for name in ("admin.html", "visits.html", "tenants.html", "stats.html"):
            self.assertIn("data-wide", (ROOT / "web" / name).read_text(encoding="utf-8"), name)
        for name in ("index.html", "play.html", "login.html", "leaderboard.html"):
            self.assertNotIn("data-wide", (ROOT / "web" / name).read_text(encoding="utf-8"), name)


if __name__ == "__main__":
    unittest.main()
