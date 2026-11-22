"""Chem Quest 的静态题库与双语内容校验。"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data" / "chemistry.json").read_text(encoding="utf-8"))
SCRIPT = (ROOT / "js" / "chemistry.js").read_text(encoding="utf-8")
CSS = (ROOT / "css" / "chemistry.css").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class TestChemistryData(unittest.TestCase):
    def test_elements_are_unique_and_ordered(self):
        elements = DATA["elements"]
        self.assertEqual(len(elements), 30)
        self.assertEqual([item["number"] for item in elements], list(range(1, 31)))
        self.assertEqual(len({item["symbol"] for item in elements}), len(elements))
        self.assertTrue(all(item["mass"] > 0 for item in elements))

    def test_formula_atoms_reference_known_elements(self):
        symbols = {item["symbol"] for item in DATA["elements"]}
        for formula in DATA["formulas"]:
            self.assertTrue(formula["zh"] and formula["en"])
            self.assertTrue(formula["atoms"])
            self.assertTrue(set(formula["atoms"]).issubset(symbols))
            self.assertTrue(all(count > 0 for count in formula["atoms"].values()))

    def test_reaction_answers_are_present_in_choices(self):
        """配平题的选项是现算的（Core.balanceChoices），题库里只存标准答案。

        所以这里检查的是「标准答案的系数个数和方程式两边的物质个数对得上」，
        选项的正确性由 tests/js/chemistry.test.js 在 node 里逐题验算。
        """
        for reaction in DATA["balancedReactions"]:
            sides = reaction["prompt"].split("→")
            count = sum(len(side.split("+")) for side in sides)
            coefficients = [c.strip() for c in reaction["answer"].split(",")]
            self.assertEqual(len(coefficients), count, reaction["prompt"])
            self.assertTrue(all(c.isdigit() and int(c) >= 1 for c in coefficients), reaction["prompt"])

    def test_junior_changes_can_build_one_right_three_wrong(self):
        kinds = [item["type"] for item in DATA["changes"]]
        self.assertGreaterEqual(kinds.count("chemical"), 1)
        self.assertGreaterEqual(kinds.count("physical"), 3)

    def test_ph_answers_match_the_molarity(self):
        import math
        for item in DATA["phQuestions"]:
            self.assertTrue(item["zh"] and item["en"])
            p = -math.log10(item["molarity"])
            expected = round(p) if item["kind"] == "acid" else 14 - round(p)
            self.assertEqual(item["answer"], expected, item["en"])

    def test_script_has_no_second_copy_of_formula_atoms(self):
        self.assertNotIn("FORMULA_ATOMS", SCRIPT)

    def test_page_offers_every_practice_type(self):
        for mode in ("elements", "formulas", "reactions", "input", "match", "order", "mistake"):
            self.assertIn('data-mode="%s"' % mode, HTML)
        self.assertIn('id="answerExplain"', HTML)
        self.assertLess(HTML.index("chemistry-core.js"), HTML.index("js/chemistry.js"))

    def test_page_uses_paths_relative_to_the_module(self):
        self.assertIn("fetch('data/chemistry.json')", SCRIPT)
        self.assertIn('href="css/chemistry.css"', HTML)
        self.assertIn('src="js/chemistry.js"', HTML)

    def test_every_reaction_is_really_balanced(self):
        """独立写一个解析器验算：标准系数必须让两边每种原子个数相等。

        解析器要认得括号（Ca(OH)2 是 1 个钙、2 个氧、2 个氢），
        否则带括号的方程式会被算成不平。
        """
        def atoms(formula):
            def group(text, i):
                counts = {}
                while i < len(text) and text[i] != ")":
                    if text[i] == "(":
                        inner, i = group(text, i + 1)
                        i += 1  # 跳过 ')'
                        mult = re.match(r"\d*", text[i:])
                        factor = int(mult.group() or 1)
                        i += len(mult.group())
                        for symbol, n in inner.items():
                            counts[symbol] = counts.get(symbol, 0) + n * factor
                    else:
                        m = re.match(r"([A-Z][a-z]?)(\d*)", text[i:])
                        if not m:
                            raise AssertionError("化学式无法解析：%s" % formula)
                        counts[m.group(1)] = counts.get(m.group(1), 0) + int(m.group(2) or 1)
                        i += m.end()
                return counts, i
            counts, _ = group(formula, 0)
            return counts

        for entry in DATA["balancedReactions"]:
            left, right = (side.split("+") for side in entry["prompt"].split("→"))
            coefficients = [int(c) for c in entry["answer"].split(",")]
            self.assertEqual(len(coefficients), len(left) + len(right), entry["prompt"])
            totals = {}
            for sign, formulas, offset in ((1, left, 0), (-1, right, len(left))):
                for i, formula in enumerate(formulas):
                    for symbol, n in atoms(formula.strip()).items():
                        totals[symbol] = totals.get(symbol, 0) + sign * n * coefficients[offset + i]
            self.assertEqual({k: v for k, v in totals.items() if v}, {}, entry["prompt"])

    def test_wrong_formulas_are_curated_and_never_valid(self):
        valid = {f["formula"] for f in DATA["formulas"]}
        for item in DATA["wrongFormulas"]:
            for key in ("zh", "en", "wrong", "right", "whyZh", "whyEn"):
                self.assertTrue(item[key], item)
            self.assertNotIn(item["wrong"], valid, "写错的化学式不能恰好是题库里的有效化学式")
            self.assertNotEqual(item["wrong"], item["right"])
        self.assertGreaterEqual(len(DATA["wrongFormulas"]), 6)

    def test_ph_scale_has_room_to_order(self):
        """pH 排序题要挑得出四项。

        同一种 pH 可以出现在几种溶液上（柠檬汁和胃液都是 2.0），所以不比 pH 本身是否唯一，
        而是看**不同的** pH 够不够多、排序时相邻两项能不能拉开 1.0 的差距。
        """
        values = sorted(item["ph"] for item in DATA["phSubstances"])
        self.assertGreaterEqual(len(set(values)), 6)
        self.assertGreaterEqual(len(DATA["phSubstances"]), 12)
        for item in DATA["phSubstances"]:
            self.assertTrue(item["zh"] and item["en"])
            self.assertTrue(0 < item["ph"] <= 14, item["zh"])
            self.assertIn(item["kind"], ("acid", "base", "neutral"), item["zh"])
        # 相邻的四个不同 pH 之间至少差 1.0，排序题才不会出「几乎一样」的两项
        spaced = [v for v in values if all(abs(v - other) >= 1.0 for other in values if other != v)]
        self.assertGreaterEqual(len(spaced), 4)

    def test_element_dataset_cites_iupac(self):
        self.assertTrue(any("iupac.org" in source["url"] for source in DATA["sources"]))


class TestChemistryCopy(unittest.TestCase):
    def test_dynamic_copy_has_matching_language_keys(self):
        block = re.search(r"var COPY = \{(.*?)\n  \};", SCRIPT, re.S)
        self.assertIsNotNone(block)
        sections = re.search(
            r"zh:\s*\{(.*?)\n    \},\s*en:\s*\{(.*?)\n    \}",
            block.group(1), re.S)
        self.assertIsNotNone(sections)
        zh, en = sections.groups()
        keys = lambda section: set(re.findall(r"^\s{6}([A-Za-z][A-Za-z0-9]*):", section, re.M))
        self.assertEqual(keys(zh), keys(en))

    def test_page_strings_are_bilingual(self):
        nodes = re.findall(r"<[^>]+data-module-zh=\"[^\"]+\"[^>]*>", HTML)
        self.assertGreaterEqual(len(nodes), 12)
        self.assertTrue(all("data-module-en=" in node for node in nodes))

    def test_theme_blocks_share_complete_variable_sets(self):
        blocks = re.findall(
            r'html\[data-theme="([a-z]+)"\]\s*\{(.*?)\}', CSS, re.S)
        self.assertGreaterEqual(len(blocks), 3)
        sets = [set(re.findall(r"(--[a-z-]+):", body)) for _, body in blocks]
        self.assertTrue(all(variables == sets[0] for variables in sets))

    def test_formula_stage_is_readable_when_it_shows_a_formula(self):
        """大舞台里有化学式或解题步骤时，读屏必须能读到（AGENTS.md：这里只放解题要用的内容）。"""
        self.assertNotIn('id="formulaStage" aria-hidden="true"', HTML,
                         "大舞台不能对读屏永久隐藏：化学式和解题步骤是解题要用的信息")
        self.assertIn("setAttribute('aria-hidden'", SCRIPT)
        # 每一处写内容的地方，都要同步设置 aria-hidden
        writes = re.findall(r"\$\('formulaStage'\)\.textContent = [^;]+;", SCRIPT)
        self.assertTrue(writes)
        for write in writes:
            tail = SCRIPT[SCRIPT.index(write):SCRIPT.index(write) + 400]
            self.assertIn("aria-hidden", tail, write)

    def test_load_failure_message_is_bilingual(self):
        """加载失败时的提示要走语言表：error.message 是英文的技术信息，不能直接上屏。"""
        self.assertIn("loadFailed", SCRIPT)
        self.assertNotIn("textContent = error.message", SCRIPT)
        block = re.search(r"var COPY = \{(.*?)\n  \};", SCRIPT, re.S)
        sections = re.search(r"zh:\s*\{(.*?)\n    \},\s*en:\s*\{(.*?)\n    \}", block.group(1), re.S)
        self.assertIsNotNone(sections)
        for part in sections.groups():
            self.assertIn("loadFailed", part)


if __name__ == "__main__":
    unittest.main()
