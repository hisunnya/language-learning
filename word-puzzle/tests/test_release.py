"""一个单元一个题库 + 批量开放。

模型：一本书按单元拆成多个题库（分类 = 书名，seq = 第几单元）；谁能看到哪个单元由标签决定。
老师不用逐个单元点：选好班级标签，再选预设范围（整本书 / 上半部分 / 下半部分 / 前 N 个）一次开放或收回。
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server import bank as bank_mod            # noqa: E402
from server.auth import AuthService             # noqa: E402
from server.db import Database                  # noqa: E402
from tests.test_auth import Client, HttpCase, multipart   # noqa: E402

NODE = shutil.which("node") or shutil.which("nodejs")


def csv_for(units, per=14):
    """每个单元 per 个词：词数故意多于 12，保证一个单元会被切成两关并补复习词。"""
    lines = ["unit,en,cn"]
    for u in range(1, units + 1):
        for i in range(per):
            lines.append("Unit %d Title,u%dword%d,单元%d释义%d" % (u, u, i, u, i))
    return ("\n".join(lines) + "\n").encode("utf-8")


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "r.db")
        self.svc = AuthService(self.db)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def bank(self, title="b", seq=0):
        return self.db.insert_bank({"title": title, "level1": "a", "level2": "b", "level3": "c", "level4": "d",
                                    "source": "seed", "unit_mode": "all", "seq": seq},
                                   [{"unit": "u", "en": title + "w", "cn": title + "义"}])

    def test_bulk_add_and_remove_tags_on_banks(self):
        a, b = self.bank("a"), self.bank("b")
        self.assertEqual(self.db.change_bank_tags([a, b], ["一班"], []), 2)
        self.assertEqual((self.db.bank_tags(a), self.db.bank_tags(b)), (["一班"], ["一班"]))
        self.assertEqual(self.db.change_bank_tags([a], ["一班", "二班"], []), 1, "已有的标签再加一次不报错")
        self.assertEqual(self.db.bank_tags(a), ["一班", "二班"])
        self.db.change_bank_tags([a, b], [], ["一班"])
        self.assertEqual((self.db.bank_tags(a), self.db.bank_tags(b)), (["二班"], []))

    def test_missing_banks_are_skipped_and_not_counted(self):
        a = self.bank("a")
        self.assertEqual(self.db.change_bank_tags([a, 9999], ["x"], []), 1)
        self.assertEqual(self.db.query("SELECT COUNT(*) AS n FROM bank_tags")[0]["n"], 1)

    def test_all_tags_counts_students_and_banks(self):
        a = self.bank("a")
        self.db.set_bank_meta(a, "", ["一班", "只有题库"])
        for no, tags in (("s1", ["一班"]), ("s2", ["一班", "二班"])):
            user, _ = self.svc.create_user(no, no, password="Init2026x")
            self.db.set_user_tags(user["id"], tags)
        self.assertEqual(self.db.all_tags(), [
            {"tag": "一班", "students": 2, "banks": 1},
            {"tag": "二班", "students": 1, "banks": 0},
            {"tag": "只有题库", "students": 0, "banks": 1}])

    def test_seq_is_stored_listed_and_old_databases_are_upgraded(self):
        a = self.bank("a", seq=3)
        self.assertEqual(self.db.list_banks()[0]["seq"], 3)
        self.assertEqual(self.bank("b") and self.db.get_bank(a + 1)["seq"], 0)
        path = Path(self.tmp.name) / "old.db"
        db = Database(path)
        db.execute("ALTER TABLE banks DROP COLUMN seq")
        db.close()
        db = Database(path)
        self.addCleanup(db.close)
        self.assertIn("seq", {r["name"] for r in db.query("PRAGMA table_info(banks)")})


class TestSplitByUnit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "s.db")
        from server import materials
        _, words = materials.parse_material("book.csv", csv_for(4))
        self.mid = self.db.insert_material("book", "book.csv", "csv", 1, "", words)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def spec(self, **extra):
        return dict({"source": "material", "material_id": self.mid, "level1": "大学", "level2": "大学英语",
                     "level3": "读写1", "level4": "x", "unit_mode": "per-unit", "title": "新视野读写1"}, **extra)

    def test_one_bank_per_unit_in_book_order(self):
        banks = bank_mod.create_bank_per_unit(self.db, self.spec())
        self.assertEqual([b["seq"] for b in banks], [1, 2, 3, 4])
        self.assertEqual([b["title"] for b in banks][:2], ["新视野读写1 · Unit 1 Title", "新视野读写1 · Unit 2 Title"])
        self.assertEqual([b["level4"] for b in banks][0], "Unit 1 Title")
        self.assertTrue(all(b["unit_count"] == 1 and b["word_count"] == 14 for b in banks))
        self.assertTrue(all(b["unit_mode"] == "all" and b["source"] == "material" for b in banks))

    def test_each_bank_only_contains_its_own_unit_even_in_the_review_words(self):
        banks = bank_mod.create_bank_per_unit(self.db, self.spec(pairs_per_level=12))
        for number, bank in enumerate(banks, start=1):
            payload = bank_mod.bank_payload(self.db, bank["id"])
            self.assertGreaterEqual(len(payload["groups"]), 2, "14 个词 / 每关 12 个 → 两关，第二关补复习词")
            seen = {w["en"] for g in payload["groups"] for w in g["words"]}
            self.assertTrue(all(en.startswith("u%dword" % number) for en in seen), (number, sorted(seen)[:3]))

    def test_the_unit_range_is_respected(self):
        banks = bank_mod.create_bank_per_unit(self.db, self.spec(unit_mode="range", unit_from=2, unit_to=3))
        self.assertEqual([b["level4"] for b in banks], ["Unit 2 Title", "Unit 3 Title"])
        self.assertEqual([b["seq"] for b in banks], [1, 2], "seq 是这一批里的顺序")

    def test_the_title_defaults_to_the_levels_and_nothing_to_split_is_an_error(self):
        banks = bank_mod.create_bank_per_unit(self.db, self.spec(title=""))
        self.assertTrue(banks[0]["title"].startswith("大学-大学英语-读写1 · "))
        with self.assertRaises(bank_mod.BankError):
            bank_mod.create_bank_per_unit(self.db, self.spec(unit_mode="range", unit_from=9, unit_to=9))
        with self.assertRaises(bank_mod.BankError):
            bank_mod.create_bank_per_unit(self.db, self.spec(unit_mode="nope"))

    def test_the_built_in_curriculum_splits_the_same_way(self):
        banks = bank_mod.create_bank_per_unit(self.db, {"source": "seed", "level1": "初中", "level2": "九年级",
                                                        "level3": "上册", "unit_mode": "all"})
        self.assertGreaterEqual(len(banks), 3)
        self.assertEqual([b["seq"] for b in banks], list(range(1, len(banks) + 1)))


class TestOverHttp(HttpCase):
    counter = 0

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.svc.create_user("T001", "老师", password="Teach3r!pw", role="admin", must_change=False)

    def login(self, no, password):
        c = Client(self.port)
        self.assertEqual(c.json("POST", "/api/auth/login", {"student_no": no, "password": password})[0], 200)
        return c

    def admin(self):
        return self.login("T001", "Teach3r!pw")

    def student(self, tags=("一班",)):
        type(self).counter += 1
        no = "S%04d" % type(self).counter
        user, _ = self.svc.create_user(no, "学生" + no, password="Ready2026x", must_change=False)
        self.app.Handler.db.set_user_tags(user["id"], list(tags))
        return self.login(no, "Ready2026x")

    def split_book(self, admin, units=6, **extra):
        body, headers = multipart({}, {"file": ("book.csv", csv_for(units))})
        mid = admin.json("POST", "/api/materials", raw=body, headers=headers)[1]["material"]["id"]
        status, res = admin.json("POST", "/api/banks", dict({
            "source": "material", "material_id": mid, "unit_mode": "per-unit", "level1": "大学", "level2": "大学英语",
            "level3": "读写1", "level4": "x", "title": "新视野读写1", "split_units": True}, **extra))
        self.assertEqual(status, 201, res)
        return [b["id"] for b in res["banks"]], res

    def visible(self, client):
        return {b["id"] for b in client.json("GET", "/api/banks")[1]["banks"]}

    def test_splitting_returns_the_units_with_category_and_tags_and_stays_closed(self):
        admin, kid = self.admin(), self.student()
        ids, res = self.split_book(admin)
        self.assertEqual(len(ids), 6)
        self.assertEqual(res["bank"]["id"], ids[0])
        self.assertEqual([b["seq"] for b in res["banks"]], [1, 2, 3, 4, 5, 6])
        self.assertTrue(all(b["category"] == "新视野读写1" and b["tags"] == [] for b in res["banks"]), "分类默认就是书名，没打标签 = 学生看不到")
        self.assertEqual(self.visible(kid) & set(ids), set())

    def test_a_tag_given_at_creation_applies_to_every_unit(self):
        admin, kid = self.admin(), self.student()
        ids, res = self.split_book(admin, tags="一班", category="读写教程")
        self.assertTrue(all(b["tags"] == ["一班"] and b["category"] == "读写教程" for b in res["banks"]))
        self.assertTrue(set(ids) <= self.visible(kid))

    def test_a_normal_creation_still_returns_one_bank_in_both_fields(self):
        admin = self.admin()
        status, res = admin.json("POST", "/api/banks", {"source": "seed", "level1": "初中", "level2": "九年级",
                                                         "level3": "上册", "level4": "all", "unit_mode": "all"})
        self.assertEqual((status, len(res["banks"]), res["bank"]["id"]), (201, 1, res["banks"][0]["id"]))

    def test_opening_with_presets_changes_what_students_see_and_withdrawing_undoes_it(self):
        admin, mine, other = self.admin(), self.student(["一班"]), self.student(["二班"])
        ids, _ = self.split_book(admin)
        first_half, second_half = ids[:3], ids[3:]
        status, res = admin.json("POST", "/api/banks/tags", {"bank_ids": first_half, "add": "一班"})
        self.assertEqual((status, res["changed"]), (200, 3))
        self.assertEqual(self.visible(mine) & set(ids), set(first_half), "上半部分开放给一班")
        self.assertEqual(self.visible(other) & set(ids), set(), "二班没有这个标签，看不到")
        admin.json("POST", "/api/banks/tags", {"bank_ids": ids, "add": "一班"})
        self.assertEqual(self.visible(mine) & set(ids), set(ids), "整本书")
        admin.json("POST", "/api/banks/tags", {"bank_ids": second_half, "remove": "一班"})
        self.assertEqual(self.visible(mine) & set(ids), set(first_half), "收回下半部分")
        admin.json("POST", "/api/banks/tags", {"bank_ids": ids, "remove": "一班"})
        self.assertEqual(self.visible(mine) & set(ids), set())

    def test_one_unit_never_shows_words_of_another(self):
        admin, mine = self.admin(), self.student()
        ids, _ = self.split_book(admin)
        admin.json("POST", "/api/banks/tags", {"bank_ids": ids[:1], "add": "一班"})
        payload = mine.json("GET", "/api/banks/%d" % ids[0])[1]
        self.assertTrue(all(w["en"].startswith("u1word") for g in payload["groups"] for w in g["words"]))
        self.assertEqual(mine.json("GET", "/api/banks/%d" % ids[1])[0], 404)

    def test_bad_bulk_requests_are_rejected(self):
        admin = self.admin()
        ids, _ = self.split_book(admin, units=2)
        for body in ({"add": "一班"}, {"bank_ids": [], "add": "一班"}, {"bank_ids": "1", "add": "一班"},
                     {"bank_ids": ["1"], "add": "一班"}, {"bank_ids": ids}, {"bank_ids": ids, "add": "x" * 30}):
            self.assertEqual(admin.json("POST", "/api/banks/tags", body)[0], 400, body)
        status, body = admin.json("POST", "/api/banks/tags", {"bank_ids": ids, "add": "x" * 30})
        self.assertEqual(body["code"], "bad_tags")
        status, res = admin.json("POST", "/api/banks/tags", {"bank_ids": ids + [999999], "add": "一班"})
        self.assertEqual((status, res["changed"]), (200, 2), "不存在的编号被忽略")

    def test_students_cannot_release_or_list_tags(self):
        admin, kid = self.admin(), self.student()
        ids, _ = self.split_book(admin, units=2)
        self.assertEqual(kid.json("POST", "/api/banks/tags", {"bank_ids": ids, "add": "一班"})[0], 403)
        self.assertEqual(kid.json("GET", "/api/admin/tags")[0], 403)
        self.assertEqual(kid.json("POST", "/api/banks", {"source": "seed", "split_units": True})[0], 403)
        self.assertEqual(self.visible(kid) & set(ids), set(), "被拒绝的请求没有生效")

    def test_the_teacher_can_list_every_tag_with_counts(self):
        admin = self.admin()
        self.student(["班甲"]); self.student(["班甲", "班乙"])
        tags = {t["tag"]: t for t in admin.json("GET", "/api/admin/tags")[1]["tags"]}
        self.assertEqual(tags["班甲"]["students"], 2)
        self.assertEqual(tags["班乙"]["students"], 1)


class TestLanEdition(HttpCase):
    auth_options = False

    def test_splitting_works_without_accounts(self):
        c = Client(self.port)
        status, res = c.json("POST", "/api/banks", {"source": "seed", "level1": "初中", "level2": "九年级",
                                                     "level3": "上册", "unit_mode": "all", "split_units": True})
        self.assertEqual(status, 201)
        self.assertGreaterEqual(len(res["banks"]), 3)
        self.assertEqual(c.json("POST", "/api/banks/tags", {"bank_ids": [res["bank"]["id"]], "add": "x"})[0], 200)


class TestPages(unittest.TestCase):
    WEB = ROOT / "web"

    def js(self, name):
        return (self.WEB / "js" / name).read_text(encoding="utf-8")

    def test_the_release_button_is_on_each_book_for_teachers_only_and_needs_accounts(self):
        code = self.js("page-home.js")
        i = code.index("var canRelease")
        self.assertIn("!student && tagsEnabled() && g.name && g.banks.length > 1", code[i:i + 120])
        self.assertIn("function editRelease(", code)
        self.assertIn("'/api/banks/tags'", code)
        self.assertIn("'/api/admin/tags'", code)

    def test_presets_come_from_the_tested_module_and_it_loads_before_the_page_script(self):
        html = (self.WEB / "index.html").read_text(encoding="utf-8")
        self.assertLess(html.index("js/release-presets.js"), html.index("js/page-home.js"))
        self.assertIn("WPRelease.indexes(kind, units.length, state.n)", self.js("page-home.js"))

    def test_open_and_withdraw_use_the_tag_and_both_need_a_tag_and_a_selection(self):
        code = self.js("page-home.js")
        self.assertIn("body[act === 'open' ? 'add' : 'remove'] = tag", code)
        self.assertIn("rel_noTag", code)
        self.assertIn("rel_noneTicked", code)
        self.assertIn("rel_nothing", code, "没有要改动的单元时提示，不发请求")
        self.assertIn("act === 'open' ? !hasTag(b) : hasTag(b)", code, "提示的数量按真正会变的算")

    def test_units_are_listed_in_book_order_for_teachers_and_students(self):
        code = self.js("page-home.js")
        i = code.index("function groupByCategory")
        self.assertIn("b.seq > 0", code[i:i + 900])

    def test_the_panel_follows_the_language_switch_and_cleans_up(self):
        code = self.js("page-home.js")
        self.assertIn("window.addEventListener('portal-lang-change', draw)", code)
        self.assertIn("window.removeEventListener('portal-lang-change', draw)", code)

    def test_the_workbench_can_split_into_one_bank_per_unit(self):
        html = (self.WEB / "bank.html").read_text(encoding="utf-8")
        self.assertRegex(html, r'<input type="checkbox" id="splitNew">\s*<span data-module-zh="[^"]+" data-module-en="[^"]+">')
        code = self.js("page-bank.js")
        self.assertIn("getElementById('splitNew').checked) p.split_units = true", code)
        self.assertIn("bank_madeMany", code)

    def test_styles_exist_and_pages_load_the_new_versions(self):
        css = (self.WEB / "css" / "auth.css").read_text(encoding="utf-8")
        for needle in (".modal-back", ".presets", ".chip", ".unit-row"):
            self.assertIn(needle, css)
        for page in ("index.html", "bank.html"):
            self.assertIn("auth.css?v=20261114-release", (self.WEB / page).read_text(encoding="utf-8"), page)


@unittest.skipUnless(NODE, "本机没有 node，跳过预设范围的行为测试")
class TestPresetBehaviour(unittest.TestCase):
    def test_behaviour(self):
        proc = subprocess.run([NODE, str(ROOT / "tests" / "js" / "release_presets.test.js")],
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("全部通过", proc.stdout)


if __name__ == "__main__":
    unittest.main()
