"""每日话题分龄话题集的结构和覆盖范围。"""
from __future__ import annotations

import json
import re
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "topic-app"


def export_array(path: Path, export_name: str) -> list[dict]:
    source = path.read_text(encoding="utf-8")
    marker = f"export const {export_name} ="
    start = source.index(marker) + len(marker)
    while source[start].isspace():
        start += 1
    payload = source[start:source.index("];", start) + 1]
    payload = re.sub(r'([,{]\s*)(id|level|category|topic|hint)(\s*:)',
                     r'\1"\2"\3', payload)
    value = json.loads(payload)
    return value


class TestTopicSets(unittest.TestCase):
    def test_existing_and_supplemental_ids_are_unique(self):
        original = export_array(APP / "topics.js", "TOPICS")
        added = export_array(APP / "supplemental_topics.js", "SUPPLEMENTAL_TOPICS")
        ids = [topic["id"] for topic in original + added]
        self.assertEqual(len(ids), len(set(ids)))

    def test_supplemental_sets_cover_all_three_audiences(self):
        added = export_array(APP / "supplemental_topics.js", "SUPPLEMENTAL_TOPICS")
        counts = Counter(topic["level"] for topic in added)
        self.assertEqual(counts, {"middle": 30, "high": 30, "university": 30})

    def test_every_topic_has_a_category_and_useful_hints(self):
        original = export_array(APP / "topics.js", "TOPICS")
        added = export_array(APP / "supplemental_topics.js", "SUPPLEMENTAL_TOPICS")
        for topic in original + added:
            self.assertTrue(topic["category"].strip())
            self.assertTrue(topic["topic"].strip())
            self.assertTrue(topic["hint"].startswith("参考方向："))
            self.assertGreaterEqual(len(re.findall(r"(?m)^- ", topic["hint"])), 3)

    def test_middle_school_is_the_default_audience(self):
        html = (APP / "index.html").read_text(encoding="utf-8")
        js = (APP / "app.js").read_text(encoding="utf-8")
        self.assertIn('data-audience="middle" aria-pressed="true"', html)
        self.assertIn("storage.get(STORAGE_KEYS.level, 'middle')", js)


if __name__ == "__main__":
    unittest.main()
