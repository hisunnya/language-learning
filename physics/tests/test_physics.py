"""物理探秘的静态题库与双语内容校验。"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data" / "physics.json").read_text(encoding="utf-8"))
UI = (ROOT / "js" / "physics.js").read_text(encoding="utf-8")
CSS = (ROOT / "css" / "physics.css").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
STAGES = ("junior", "high", "university")


class TestPhysicsData(unittest.TestCase):
    def test_quantities_are_complete_and_unique(self):
        quantities = DATA["quantities"]
        for q in quantities:
            for key in ("stage", "zh", "en", "symbol", "unit", "unitZh", "unitEn", "base"):
                self.assertTrue(q.get(key), (q.get("zh"), key))
            self.assertIn(q["stage"], STAGES)
        # 出选项时靠单位 / 名称 / 基本单位表达式区分，所以它们不能重复
        for field in ("unit", "zh", "base"):
            values = [q[field] for q in quantities]
            self.assertEqual(len(values), len(set(values)), field)

    def test_every_stage_has_enough_material(self):
        for stage in STAGES:
            self.assertGreaterEqual(
                len([q for q in DATA["quantities"] if q["stage"] in STAGES[:STAGES.index(stage) + 1]]), 8)
            self.assertGreaterEqual(len([c for c in DATA["concepts"] if c["stage"] == stage]), 6, stage)

    def test_concepts_have_one_answer_three_distractors_in_both_languages(self):
        for item in DATA["concepts"]:
            self.assertIn(item["stage"], STAGES)
            self.assertEqual(len(item["wrongZh"]), 3, item["zh"])
            self.assertEqual(len(item["wrongEn"]), 3, item["zh"])
            options = [item["answerZh"]] + item["wrongZh"]
            self.assertEqual(len(set(options)), 4, item["zh"])
            self.assertTrue(all([item["zh"], item["en"], item["whyZh"], item["whyEn"],
                                 item["answerEn"]]), item["zh"])

    def test_magnitudes_can_be_ordered_unambiguously(self):
        categories = DATA["magnitudes"]
        self.assertTrue(any(c["stage"] == "junior" for c in categories))
        for cat in categories:
            self.assertIn(cat["stage"], STAGES)
            self.assertTrue(cat["zh"] and cat["en"] and cat["unit"])
            values = sorted(item["value"] for item in cat["items"])
            self.assertGreaterEqual(len(values), 4, cat["zh"])
            self.assertEqual(len(set(values)), len(values), cat["zh"])
            self.assertTrue(all(v > 0 for v in values))
            for item in cat["items"]:
                self.assertTrue(item["zh"] and item["en"], item)
            # 至少存在一种取 4 项、相邻相差 3 倍以上的组合，否则排序题没法出
            from itertools import combinations
            self.assertTrue(any(all(b / a >= 3 for a, b in zip(c, c[1:])) for c in combinations(values, 4)), cat["zh"])

    def test_dataset_cites_nist_and_bipm(self):
        urls = " ".join(source["url"] for source in DATA["sources"])
        self.assertIn("nist.gov", urls)
        self.assertIn("bipm.org", urls)


class TestPhysicsPage(unittest.TestCase):
    def test_page_strings_are_bilingual(self):
        nodes = re.findall(r"<[^>]+data-module-zh=\"[^\"]+\"[^>]*>", HTML)
        self.assertGreaterEqual(len(nodes), 12)
        self.assertTrue(all("data-module-en=" in node for node in nodes))

    def test_copy_has_matching_language_keys(self):
        block = re.search(r"var COPY = \{(.*?)\n  \};", UI, re.S)
        self.assertIsNotNone(block)
        sections = re.search(r"zh:\s*\{(.*?)\n    \},\s*en:\s*\{(.*?)\n    \}", block.group(1), re.S)
        self.assertIsNotNone(sections)
        keys = lambda s: set(re.findall(r"^\s{6}([A-Za-z][A-Za-z0-9]*):", s, re.M))
        self.assertEqual(keys(sections.group(1)), keys(sections.group(2)))

    def test_theme_blocks_share_complete_variable_sets(self):
        blocks = re.findall(r'html\[data-theme="([a-z]+)"\]\s*\{(.*?)\}', CSS, re.S)
        self.assertGreaterEqual(len(blocks), 3)
        sets = [set(re.findall(r"(--[a-z-]+):", body)) for _, body in blocks]
        self.assertTrue(all(variables == sets[0] for variables in sets))

    def test_palettes_match_the_shared_header(self):
        """配色名要和 hub/shared/module-header.js 里的调色板一一对应，否则选了没有效果。"""
        header = (ROOT.parent / "hub" / "shared" / "module-header.js").read_text(encoding="utf-8")
        shared = set(re.findall(r"key: '([a-z]+)'", header))
        mine = {name for name, _ in re.findall(r'html\[data-theme="([a-z]+)"\]\s*\{(.*?)\}', CSS, re.S)}
        self.assertEqual(shared, mine)

    def test_page_offers_every_practice_type(self):
        for mode in ("units", "calc", "input", "match", "order", "mistake", "concepts"):
            self.assertIn('data-mode="%s"' % mode, HTML)
        self.assertIn('id="answerExplain"', HTML)

    def test_paths_are_relative_to_the_module(self):
        self.assertIn("fetch('data/physics.json')", UI)
        self.assertIn('href="css/physics.css"', HTML)
        self.assertIn('src="js/physics-core.js"', HTML)
        self.assertLess(HTML.index("physics-core.js"), HTML.index("js/physics.js"))

    def test_page_uses_the_shared_header_and_has_no_hard_coded_colours(self):
        self.assertIn('id="portalHeaderControls"', HTML)
        body = re.sub(r'html\[data-theme="[a-z]+"\]\s*\{.*?\}', "", CSS, flags=re.S)
        self.assertEqual(re.findall(r"#[0-9a-fA-F]{3,8}\b", body), [],
                         "颜色应该写在 [data-theme] 变量里")


if __name__ == "__main__":
    unittest.main()
