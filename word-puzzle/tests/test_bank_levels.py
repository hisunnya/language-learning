"""切关规则：同一关里英文或中文不能重复，也不能因此丢词；网站版和小程序版的切关结果必须一致。"""
from __future__ import annotations

import json
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server import bank as bank_mod            # noqa: E402
from server.db import Database                  # noqa: E402

NODE = shutil.which("node") or shutil.which("nodejs")
MINI_BANK = ROOT.parent / "miniprogram" / "utils" / "bank.js"


def words(*pairs):
    return [{"en": en, "cn": cn} for en, cn in pairs]


class TestDuplicateMeanings(unittest.TestCase):
    def test_duplicate_chinese_is_carried_to_the_next_level_not_dropped(self):
        unit = words(("rely", "依赖"), ("rely on", "依赖"), ("a", "甲"), ("b", "乙"), ("c", "丙"))
        parts = bank_mod.chunk_groups([{"unit": "Unit 1", "words": unit}], 3)
        for part in parts:
            cn = [w["cn"] for w in part["words"]]
            en = [w["en"] for w in part["words"]]
            self.assertEqual(len(cn), len(set(cn)), part)
            self.assertEqual(len(en), len(set(en)), part)
            self.assertLessEqual(len(part["words"]), 3)
        # 原来的五个词都还在（复习补进来的重复词不算）
        got = {w["en"] for part in parts for w in part["words"]}
        self.assertEqual(got, {"rely", "rely on", "a", "b", "c"})

    def test_leftover_becomes_a_supplement_level_of_the_same_unit(self):
        unit = words(("x", "同"), ("y", "同"), ("z", "同"))
        parts = bank_mod.chunk_groups([{"unit": "Unit 9", "words": unit}], 12)
        self.assertEqual(len(parts), 3, "三个词的中文都一样，只能各占一关")
        self.assertEqual(parts[0]["unit"], "Unit 9")
        self.assertIn("补充", parts[1]["unit"])
        self.assertTrue(parts[1]["unit"].startswith("Unit 9"))

    def test_carried_word_stays_in_its_own_unit(self):
        groups = [
            {"unit": "Unit 1", "words": words(("a", "同"), ("b", "同"))},
            {"unit": "Unit 2", "words": words(("c", "丙"), ("d", "丁"))},
        ]
        parts = bank_mod.chunk_groups(groups, 12)
        home = [p["unit"] for p in parts if any(w["en"] == "b" and "补充" in p["unit"] for w in p["words"])]
        self.assertEqual(len(home), 1)
        self.assertTrue(home[0].startswith("Unit 1"), "被顺延的词要留在自己的单元：" + home[0])
        for part in parts:
            if part["unit"].startswith("Unit 2") and "含复习" not in part["unit"]:
                self.assertFalse({w["en"] for w in part["words"]} & {"a", "b"})

    def test_levels_without_duplicates_keep_their_names_and_sizes(self):
        unit = words(*[("w%d" % i, "词%d" % i) for i in range(30)])
        parts = bank_mod.chunk_groups([{"unit": "U", "words": unit}], 12)
        self.assertEqual([p["unit"] for p in parts][:2], ["U（1/3）", "U（2/3）"])
        self.assertTrue(parts[2]["unit"].startswith("U（3/3）"))
        self.assertEqual([len(p["words"]) for p in parts], [12, 12, 12])


class TestRealCurriculum(unittest.TestCase):
    def test_no_level_has_a_repeated_card_and_no_word_is_lost(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "t.db")
            try:
                bank_mod.seed_default_bank(db)
                bank_mod.seed_curriculum_banks(db)
                for bank in db.list_banks():
                    groups = bank_mod.bank_payload(db, bank["id"])["groups"]
                    seen = set()
                    for group in groups:
                        en = [w["en"] for w in group["words"]]
                        cn = [w["cn"] for w in group["words"]]
                        self.assertEqual(len(en), len(set(en)), (bank["title"], group["unit"]))
                        self.assertEqual(len(cn), len(set(cn)), (bank["title"], group["unit"]))
                        seen.update((w["en"], w["cn"]) for w in group["words"])
                    wanted = {(w["en"], w["cn"]) for w in db.bank_words(bank["id"])}
                    self.assertEqual(wanted - seen, set(), "题库里的词不能因去重而不出现：" + bank["title"])
            finally:
                db.close()


@unittest.skipUnless(NODE, "本机没有 node，跳过小程序切关一致性测试")
class TestMiniprogramBankParity(unittest.TestCase):
    def test_same_levels_as_the_website_for_random_units(self):
        rng = random.Random(7)
        cases = []
        for _ in range(150):
            pool = [("e%d" % i, "中%d" % rng.randrange(14)) for i in range(40)]
            groups = []
            for u in range(rng.randrange(1, 4)):
                size = rng.randrange(1, 30)
                chosen = rng.sample(pool, size)
                groups.append({"unit": "Unit %d" % (u + 1), "words": words(*chosen)})
            cases.append({"groups": groups, "max": rng.choice([4, 6, 12, 12, 20])})
        script = (
            "const bank=require(%s);const input=JSON.parse(require('fs').readFileSync(0,'utf8'));"
            "const out=input.map(c=>bank.chunkGroups(c.groups.map(g=>({name:g.unit,words:g.words})),c.max)"
            ".map(p=>({unit:p.unit,words:p.words.map(w=>[w.en,w.cn])})));"
            "process.stdout.write(JSON.stringify(out));" % json.dumps(str(MINI_BANK)))
        proc = subprocess.run([NODE, "-e", script], input=json.dumps(cases), capture_output=True,
                              text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        mini = json.loads(proc.stdout)
        for case, got in zip(cases, mini):
            groups = [{"unit": g["unit"], "words": [dict(w) for w in g["words"]]} for g in case["groups"]]
            want = [{"unit": p["unit"], "words": [[w["en"], w["cn"]] for w in p["words"]]}
                    for p in bank_mod.chunk_groups(groups, case["max"])]
            self.assertEqual(got, want)


if __name__ == "__main__":
    unittest.main()
