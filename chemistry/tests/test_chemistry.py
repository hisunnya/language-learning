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
        for reaction in DATA["balancedReactions"]:
            self.assertIn(reaction["answer"], reaction["choices"])
            self.assertGreaterEqual(len(reaction["choices"]), 4)

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
        """独立写一个解析器验算：标准系数必须让两边每种原子个数相等。"""
        def atoms(formula):
            counts = {}
            for symbol, n in re.findall(r"([A-Z][a-z]?)(\d*)", formula):
                counts[symbol] = counts.get(symbol, 0) + int(n or 1)
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
        values = sorted(item["ph"] for item in DATA["phScale"])
        self.assertGreaterEqual(len(values), 6)
        self.assertEqual(len(set(values)), len(values))
        for item in DATA["phScale"]:
            self.assertTrue(item["zh"] and item["en"])

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


if __name__ == "__main__":
    unittest.main()
