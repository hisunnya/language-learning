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
