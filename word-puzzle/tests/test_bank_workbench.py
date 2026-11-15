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


@unittest.skipUnless(NODE, "本机没有 node，跳过题库工作台的行为测试")
class TestBehaviour(unittest.TestCase):
    def test_behaviour(self):
        proc = subprocess.run([NODE, str(ROOT / "tests" / "js" / "bank_workbench.test.js")], capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("项通过", proc.stdout)


if __name__ == "__main__":
    unittest.main()
