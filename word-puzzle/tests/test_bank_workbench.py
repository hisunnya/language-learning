"""题库工作台：三个标签页（当前题库 / 新建题库 / 离线测试）、新建题库的三步、首页只选题库和玩。"""
from __future__ import annotations

import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
NODE = shutil.which("node") or shutil.which("nodejs")
HTML = (WEB / "bank.html").read_text(encoding="utf-8")
CODE = (WEB / "js" / "page-bank.js").read_text(encoding="utf-8")


class TestStructure(unittest.TestCase):
    def test_three_tabs_with_matching_panels_and_aria(self):
        for name, label in (("Banks", "当前题库"), ("New", "新建题库"), ("Offline", "离线测试")):
            self.assertRegex(HTML, r'<button type="button" class="tab[^"]*" role="tab" id="tab%s"[^>]*aria-controls="panel%s"' % (name, name))
            self.assertRegex(HTML, r'<section id="panel%s" role="tabpanel" aria-labelledby="tab%s"' % (name, name))
            self.assertIn(label, HTML)
        self.assertEqual(HTML.count('role="tablist"'), 1)
        self.assertEqual(len(re.findall(r'role="tabpanel"', HTML)), 3)
        self.assertEqual(len(re.findall(r'aria-selected="true"', HTML)), 1, "一开始只有一个标签页选中")

    def test_the_tab_is_in_the_url_so_it_can_be_bookmarked_and_the_back_key_works(self):
        for needle in ("tabFromHash", "replaceState", "'hashchange'", "ArrowRight"):
            self.assertIn(needle, CODE)

    def test_new_bank_has_three_steps_in_order_each_with_a_band_and_a_bilingual_label(self):
        order = [HTML.index('data-step="%d"' % n) for n in (1, 2, 3)]
        self.assertEqual(order, sorted(order))
        for n in (1, 2, 3):
            self.assertRegex(HTML, r'<span class="step-no" data-module-zh="Step %d" data-module-en="Step %d">Step %d</span>' % (n, n, n))
        self.assertIn('class="step optional" data-step="3"', HTML, "第 3 步（开放给谁）是可选的")
        css = (WEB / "css" / "auth.css").read_text(encoding="utf-8")
        for needle in (".step-band", ".step-no", ".step.optional", ".item.flash"):
            self.assertIn(needle, css)
        self.assertNotRegex(css[css.index(".step {"):css.index(".item.flash")], r"#[0-9a-fA-F]{3,6}\b", "步骤色块用配色变量，不写死颜色")

    def test_there_is_one_way_to_choose_the_source_and_the_old_duplicates_are_gone(self):
        self.assertEqual(len(re.findall(r'name="source"', HTML)), 3)
        for gone in ('id="sourceSel"', 'id="btnUpload"', 'id="btnOffline"', "bank_useMat"):
            self.assertNotIn(gone, HTML + CODE, gone)
        self.assertIn('id="btnQuick"', HTML)                      # 快速上传并生成先留着
        self.assertIn('id="btnMake"', HTML)

    def test_only_two_places_create_banks_and_offline_export_is_not_one_of_them(self):
        self.assertEqual(len(re.findall(r"API\.post\('/api/banks',", CODE)), 2, "只有 make() 和 quick() 会新建题库")
        body = CODE[CODE.index("function makeOffline("):CODE.index("/* ---------------- 新建题库：Step 1")]
        self.assertIn("'/offline'", body)
        self.assertNotIn("'/api/banks',", body)

    def test_after_creating_the_page_goes_to_the_banks_tab_and_reminds_about_tags(self):
        body = CODE[CODE.index("function afterMade("):CODE.index("function make()")]
        for needle in ("highlight[b.id] = true", "noTags", "showTab('banks')", "scrollIntoView"):
            self.assertIn(needle, body)
        self.assertIn("bank_noTagsNotice", CODE)

    def test_the_home_page_only_picks_and_plays_and_links_teachers_to_the_workbench(self):
        home = (WEB / "js" / "page-home.js").read_text(encoding="utf-8")
        for gone in ("API.post", "API.del", "Selector", "editField", "editRelease"):
            self.assertNotIn(gone, home, gone)
        index = (WEB / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="/word-puzzle/bank.html#banks"', index)
        for gone in ("selector.js", "release-presets.js"):
            self.assertNotIn(gone, index)

    def test_the_extracted_panels_are_loaded_by_the_workbench_only(self):
        self.assertIn("js/bank-panels.js", HTML)
        self.assertNotIn("bank-panels.js", (WEB / "index.html").read_text(encoding="utf-8"))


class TestTeacherLandingPage(unittest.TestCase):
    """老师登录后没有「首页」：首页和题库工作台内容重复，工作台就是首页。学生和家庭版里没登录的访客仍然用首页。"""

    def read(self, name):
        return (WEB / name).read_text(encoding="utf-8")

    def test_the_home_page_redirects_a_logged_in_teacher_before_painting(self):
        html = self.read("index.html")
        self.assertIn('<body data-page="home">', html)
        head = html[:html.index("</head>")]
        self.assertIn("sessionStorage.getItem('wp_teacher')==='1'", head)
        self.assertIn("/word-puzzle/bank.html#banks", head)
        self.assertLess(html.index("wp_teacher"), html.index('rel="stylesheet"'), "要在样式表之前")

    def test_login_lands_teachers_on_the_workbench(self):
        self.assertIn("AuthUI.landing(res.user)", self.read("js/page-login.js"))
        ui = self.read("js/auth-ui.js")
        self.assertIn("landing: landing", ui)
        self.assertIn("location.replace(workbench())", ui)

    def test_the_teacher_only_pages_have_no_home_link(self):
        for page in ("bank.html", "admin.html", "visits.html"):
            self.assertNotIn('<a href="/word-puzzle/" data-module-zh="首页"', self.read(page), page)

    def test_the_other_pages_hide_it_for_teachers_only(self):
        ui = self.read("js/auth-ui.js")
        self.assertIn("function hideHomeLink()", ui)
        self.assertIn("if (user.role === 'admin') { hideHomeLink(); addNavLinks(); }", ui)
        for page in ("stats.html", "index.html"):
            self.assertIn('href="/word-puzzle/" ', self.read(page).replace('class="active" ', ""), page + "：学生和访客仍然有首页链接")


class TestHeaderAndEnglishWording(unittest.TestCase):
    def test_account_link_is_highlighted_only_on_the_account_page(self):
        ui = (WEB / "js" / "auth-ui.js").read_text(encoding="utf-8")
        self.assertIn("location.pathname.slice(-10) === 'admin.html'", ui)
        self.assertNotIn("getAttribute('data-auth') === 'admin') link.className", ui, "题库工作台也是 data-auth=admin，不能拿它判断")

    def test_the_english_brand_does_not_repeat_itself_and_the_tagline_is_short(self):
        css = (ROOT.parent / "hub" / "shared" / "module-header.css").read_text(encoding="utf-8")
        self.assertIn('html[lang="en"] .portal-brand-copy em { display: none; }', css)
        for page in WEB.glob("*.html"):
            self.assertNotIn("English vocabulary practice", page.read_text(encoding="utf-8"), page.name)

    def test_english_never_calls_a_question_bank_just_a_bank(self):
        """题库的英文是 word bank：单独一个 bank 容易被读成银行。"""
        pattern = re.compile(r"(?<![Ww]ord )(?<![Ww]ord-)\b[Bb]anks?\b")
        problems = []
        for page in WEB.glob("*.html"):
            for value in re.findall(r'data-module-en="([^"]*)"', page.read_text(encoding="utf-8")):
                if pattern.search(value):
                    problems.append("%s: %s" % (page.name, value[:50]))
        text = (WEB / "js" / "i18n-lexica.js").read_text(encoding="utf-8")
        en = text[text.index("}, {"):]
        for key, value in re.findall(r"    ([a-zA-Z_0-9]+): '((?:[^'\\]|\\.)*)',\n", en):
            if pattern.search(value):
                problems.append("%s: %s" % (key, value[:50]))
        self.assertEqual(problems, [])


@unittest.skipUnless(NODE, "本机没有 node，跳过题库工作台的行为测试")
class TestBehaviour(unittest.TestCase):
    def test_behaviour(self):
        proc = subprocess.run([NODE, str(ROOT / "tests" / "js" / "bank_workbench.test.js")], capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("项通过", proc.stdout)


if __name__ == "__main__":
    unittest.main()
