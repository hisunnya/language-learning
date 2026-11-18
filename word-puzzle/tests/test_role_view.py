"""换页面时不闪教师版：角色在页面画出来之前就定好。"""
from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
NODE = shutil.which("node") or shutil.which("nodejs")
PROTECTED = ("index.html", "bank.html", "stats.html", "play.html", "admin.html")


class TestHeadScript(unittest.TestCase):
    def test_every_protected_page_sets_the_role_class_before_anything_is_painted(self):
        for page in PROTECTED:
            html = (WEB / page).read_text(encoding="utf-8")
            self.assertEqual(html.count("sessionStorage.getItem('wp_role')"), 1, page)
            self.assertLess(html.index("wp_role"), html.index('rel="stylesheet"'), "%s：要在样式表之前" % page)
            self.assertLess(html.index("wp_role"), html.index("<body"), page)

    def test_the_login_pages_are_not_hidden_while_the_role_is_unknown(self):
        for page in ("login.html", "change-password.html"):
            self.assertNotIn("role-pending", (WEB / page).read_text(encoding="utf-8"), page)

    def test_the_styles_hide_teacher_controls_for_students_and_while_unknown(self):
        css = (WEB / "css" / "auth.css").read_text(encoding="utf-8")
        self.assertIn("html.role-student .admin-only, html.role-pending .admin-only { display: none !important; }", css)
        self.assertIn("html.role-pending body { visibility: hidden; }", css)

    def test_signing_out_forgets_the_role(self):
        code = (WEB / "js" / "auth-ui.js").read_text(encoding="utf-8")
        self.assertIn("setRole(''); go(info.guest ? '' : 'login.html', false)", code)

    def test_pages_load_versioned_styles_and_the_new_script(self):
        for page in PROTECTED:
            html = (WEB / page).read_text(encoding="utf-8")
            self.assertRegex(html, r"auth\.css\?v=[0-9a-f]{8}", page)        # 带版本号：改了样式，浏览器才会丢掉旧的
            self.assertRegex(html, r"auth-ui\.js\?v=[0-9a-f]{8}", page)


@unittest.skipUnless(NODE, "本机没有 node，跳过换页面不闪教师版的行为测试")
class TestBehaviour(unittest.TestCase):
    def test_behaviour(self):
        proc = subprocess.run([NODE, str(ROOT / "tests" / "js" / "role_view.test.js")],
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("全部通过", proc.stdout)


if __name__ == "__main__":
    unittest.main()
