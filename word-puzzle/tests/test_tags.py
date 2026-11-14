"""标签与分类：学生只能打开和自己至少有一个相同标签的题库；题库管理只有老师。

规则（和老师商量定下的）：
  * 标签对标签：学生和题库各带一组标签，有一个相同就能看到、能打开、能记成绩；
  * 没打标签的题库学生看不到（老师始终看得到全部）；
  * 分类只用来整理，不参与权限；
  * 建题库、删题库、改分类和标签、上传、离线页：只有老师；
  * 局域网版没有账号，行为不变。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server import bank as bank_mod            # noqa: E402
from server import roster                       # noqa: E402
from server.auth import AuthService             # noqa: E402
from server.db import Database, TagError, normalize_category, normalize_tags   # noqa: E402
from tests.test_auth import Client, HttpCase    # noqa: E402

SEED_SPEC = {"source": "seed", "level1": "初中", "level2": "九年级", "level3": "上册",
             "level4": "all", "unit_mode": "all"}


class TestNormalize(unittest.TestCase):
    def test_splits_trims_and_dedupes_in_order(self):
        self.assertEqual(normalize_tags(" 初二 ,三班，初二、 雅思;\n"), ["初二", "三班", "雅思"])
        self.assertEqual(normalize_tags(["a", " a ", "", "b"]), ["a", "b"])
        self.assertEqual(normalize_tags(None), [])
        self.assertEqual(normalize_tags(""), [])

    def test_too_long_or_too_many_is_an_error_not_a_silent_cut(self):
        with self.assertRaises(TagError):
            normalize_tags("x" * 21)
        with self.assertRaises(TagError):
            normalize_tags(",".join("t%d" % i for i in range(11)))
        self.assertEqual(len(normalize_tags(",".join("t%d" % i for i in range(10)))), 10)
        with self.assertRaises(TagError):
            normalize_category("c" * 21)
        self.assertEqual(normalize_category("  教材  同步 "), "教材 同步")


class TestDatabaseTags(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.db")
        self.svc = AuthService(self.db)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def bank(self, title="b"):
        return self.db.insert_bank({"title": title, "level1": "a", "level2": "b", "level3": "c",
                                    "level4": "d", "source": "seed", "unit_mode": "all"},
                                   [{"unit": "u", "en": "apple", "cn": "苹果"}])

    def user(self, no, tags=()):
        user, _ = self.svc.create_user(no, no, password="Init2026x")
        self.db.set_user_tags(user["id"], list(tags))
        return user["id"]

    def test_visible_only_when_a_tag_is_shared(self):
        b1, b2, b3 = self.bank("1"), self.bank("2"), self.bank("3")
        self.db.set_bank_meta(b1, "", ["初二"])
        self.db.set_bank_meta(b2, "", ["初二", "三班"])
        # b3 没打标签
        alice = self.user("alice", ["三班"])
        bob = self.user("bob", ["初二", "雅思"])
        carol = self.user("carol", ["别的"])
        nobody = self.user("nobody")
        ids = lambda uid: sorted(b["id"] for b in self.db.list_banks(uid))
        self.assertEqual(ids(alice), [b2])
        self.assertEqual(ids(bob), [b1, b2])
        self.assertEqual(ids(carol), [])
        self.assertEqual(ids(nobody), [])
        self.assertEqual(len(self.db.list_banks()), 3, "老师（visible_to=None）看得到全部，包括没打标签的")
        self.assertTrue(self.db.bank_visible_to(b2, alice))
        self.assertFalse(self.db.bank_visible_to(b1, alice))
        self.assertFalse(self.db.bank_visible_to(b3, bob))
        self.assertFalse(self.db.bank_visible_to(b1, None))

    def test_list_carries_tags_and_category(self):
        b = self.bank()
        self.db.set_bank_meta(b, "教材同步", ["初二", "三班"])
        listed = self.db.list_banks()[0]
        self.assertEqual((listed["category"], listed["tags"]), ("教材同步", ["三班", "初二"]))

    def test_meta_none_means_unchanged_and_empty_list_clears(self):
        b = self.bank()
        self.db.set_bank_meta(b, "分类", ["x"])
        self.db.set_bank_meta(b, None, ["y"])
        self.assertEqual((self.db.get_bank(b)["category"], self.db.bank_tags(b)), ("分类", ["y"]))
        self.db.set_bank_meta(b, "新", None)
        self.assertEqual((self.db.get_bank(b)["category"], self.db.bank_tags(b)), ("新", ["y"]))
        self.db.set_bank_meta(b, None, [])
        self.assertEqual(self.db.bank_tags(b), [])
        self.assertFalse(self.db.set_bank_meta(9999, "x", ["x"]))

    def test_deleting_a_bank_removes_its_tags(self):
        b = self.bank()
        self.db.set_bank_meta(b, "", ["x"])
        self.db.delete_bank(b)
        self.assertEqual(self.db.query("SELECT * FROM bank_tags"), [])

    def test_bulk_add_and_remove(self):
        u1, u2 = self.user("u1", ["a"]), self.user("u2", ["a", "b"])
        self.db.change_user_tags([u1, u2], ["c"], [])
        self.assertEqual(self.db.user_tags_map([u1, u2]), {u1: ["a", "c"], u2: ["a", "b", "c"]})
        self.db.change_user_tags([u1, u2], [], ["a"])
        self.assertEqual(self.db.user_tags_map([u1, u2]), {u1: ["c"], u2: ["b", "c"]})
        self.db.change_user_tags([u1], ["c"], [])         # 已有的再加一次不报错
        self.assertEqual(self.db.user_tags_map([u1]), {u1: ["c"]})

    def test_an_old_database_without_the_category_column_is_upgraded(self):
        path = Path(self.tmp.name) / "old.db"
        db = Database(path)
        db.execute("ALTER TABLE banks DROP COLUMN category")
        db.close()
        db = Database(path)
        self.addCleanup(db.close)
        self.assertIn("category", {r["name"] for r in db.query("PRAGMA table_info(banks)")})


class TestSeedRebuildKeepsTags(unittest.TestCase):
    def test_a_rebuilt_builtin_bank_keeps_category_and_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "s.db")
            try:
                bank_mod.seed_curriculum_banks(db)
                target = db.list_banks()[0]
                db.set_bank_meta(target["id"], "教材同步", ["初二"])
                # 词库更新了：这个题库的词条指纹对不上，启动时会被删掉重建
                db.execute("UPDATE bank_words SET cn='被改过' WHERE id=(SELECT MIN(id) FROM bank_words WHERE bank_id=?)",
                           (target["id"],))
                bank_mod.seed_curriculum_banks(db)
                rebuilt = [b for b in db.list_banks() if b["title"] == target["title"]]
                self.assertEqual(len(rebuilt), 1)
                self.assertEqual((rebuilt[0]["category"], rebuilt[0]["tags"]), ("教材同步", ["初二"]))
            finally:
                db.close()


class TestRosterTags(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "r.db")
        self.svc = AuthService(self.db)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def import_csv(self, text):
        table = roster.parse_roster("r.csv", text.encode("utf-8"))
        self.assertNotIn("标签", table["ignored_columns"])
        return self.svc.import_roster(table["rows"])

    def tags(self, no):
        return self.db.user_tags_map().get(self.svc.get_by_student_no(no)["id"], [])

    def test_the_tag_column_sets_tags_on_new_and_existing_students(self):
        report = self.import_csv("学号,姓名,标签\ns1,甲,\"初二, 三班\"\ns2,乙,初二\ns3,丙,\n")
        self.assertEqual(report["created"], 3)
        self.assertEqual((self.tags("s1"), self.tags("s2"), self.tags("s3")), (["三班", "初二"], ["初二"], []))
        # 再导入一次：有内容的整组替换，空的保持原样
        self.import_csv("学号,姓名,标签\ns1,甲,雅思\ns2,乙,\n")
        self.assertEqual((self.tags("s1"), self.tags("s2")), (["雅思"], ["初二"]))

    def test_without_the_column_nothing_changes(self):
        self.import_csv("学号,姓名,标签\ns1,甲,初二\n")
        self.import_csv("学号,姓名\ns1,甲\n")
        self.assertEqual(self.tags("s1"), ["初二"])

    def test_a_bad_tag_skips_only_that_row(self):
        report = self.import_csv("学号,姓名,标签\ns1,甲,%s\ns2,乙,初二\n" % ("长" * 21))
        self.assertEqual((report["created"], report["skipped"]), (1, 1))
        self.assertIsNone(self.svc.get_by_student_no("s1"), "标签不合法的那一行不建号")
        self.assertEqual(self.tags("s2"), ["初二"])


class TestTagsOverHttp(HttpCase):
    counter = 0

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.svc.create_user("T001", "老师", password="Teach3r!pw", role="admin", must_change=False)

    def login(self, no, password):
        c = Client(self.port)
        status, _ = c.json("POST", "/api/auth/login", {"student_no": no, "password": password})
        self.assertEqual(status, 200)
        return c

    def admin(self):
        return self.login("T001", "Teach3r!pw")

    def student(self, tags=()):
        type(self).counter += 1
        no = "S%04d" % type(self).counter
        user, _ = self.svc.create_user(no, "学生" + no, password="Ready2026x", must_change=False)
        self.app.Handler.db.set_user_tags(user["id"], list(tags))
        return no, user["id"], self.login(no, "Ready2026x")

    def new_bank(self, admin, **meta):
        status, body = admin.json("POST", "/api/banks", dict(SEED_SPEC, **meta))
        self.assertEqual(status, 201, body)
        return body["bank"]["id"]

    def ids(self, client):
        return {b["id"] for b in client.json("GET", "/api/banks")[1]["banks"]}

    def test_students_see_exactly_the_banks_that_share_a_tag(self):
        admin = self.admin()
        _, _, mine = self.student(["初二"])
        _, _, other = self.student(["高一"])
        _, _, untagged = self.student()
        shared = self.new_bank(admin, tags="初二, 三班", category="教材同步")
        hidden = self.new_bank(admin, tags="高三")
        nobody = self.new_bank(admin)                               # 没打标签
        self.assertIn(shared, self.ids(mine))
        self.assertNotIn(hidden, self.ids(mine))
        self.assertNotIn(nobody, self.ids(mine))
        self.assertNotIn(shared, self.ids(other))
        self.assertEqual(self.ids(untagged), set(), "一个标签都没有的学生什么题库都看不到，包括系统内置题库")
        self.assertTrue({shared, hidden, nobody} <= self.ids(admin), "老师看得到全部")

    def test_opening_a_hidden_bank_is_a_404_not_a_403(self):
        """404 而不是 403：学生没法靠猜编号知道哪些题库存在。"""
        admin = self.admin()
        _, _, mine = self.student(["初二"])
        shared, hidden = self.new_bank(admin, tags="初二"), self.new_bank(admin, tags="高三")
        status, body = mine.json("GET", "/api/banks/%d" % shared)
        self.assertEqual(status, 200)
        self.assertEqual((body["bank"]["category"], body["bank"]["tags"]), ("", ["初二"]))
        self.assertEqual(mine.json("GET", "/api/banks/%d" % hidden)[0], 404)
        self.assertEqual(admin.json("GET", "/api/banks/%d" % hidden)[0], 200)

    def test_changing_the_tags_takes_effect_at_once(self):
        admin = self.admin()
        _, uid, mine = self.student(["初二"])
        bid = self.new_bank(admin, tags="高三")
        self.assertNotIn(bid, self.ids(mine))
        status, body = admin.json("POST", "/api/banks/%d/meta" % bid, {"category": "考试", "tags": ["高三", "初二"]})
        self.assertEqual((status, body["bank"]["category"], body["bank"]["tags"]), (200, "考试", ["初二", "高三"]))
        self.assertIn(bid, self.ids(mine))
        admin.json("POST", "/api/banks/%d/meta" % bid, {"tags": ""})
        self.assertNotIn(bid, self.ids(mine))
        self.assertEqual(admin.json("POST", "/api/banks/9999/meta", {"tags": "x"})[0], 404)

    def test_bad_tags_are_rejected_with_400(self):
        admin = self.admin()
        bid = self.new_bank(admin)
        status, body = admin.json("POST", "/api/banks/%d/meta" % bid, {"tags": "x" * 30})
        self.assertEqual((status, body["code"]), (400, "bad_tags"))
        self.assertEqual(admin.json("POST", "/api/banks", dict(SEED_SPEC, tags="x" * 30))[0], 400)
        _, uid, _ = self.student()
        self.assertEqual(admin.json("POST", "/api/admin/users/%d/tags" % uid, {"tags": "x" * 30})[0], 400)

    def test_scores_only_count_on_banks_the_student_can_open(self):
        admin = self.admin()
        _, _, mine = self.student(["初二"])
        shared, hidden = self.new_bank(admin, tags="初二"), self.new_bank(admin, tags="高三")
        score = {"score": 100, "matched": 1, "total_pairs": 1, "bank_title": "t"}
        self.assertEqual(mine.json("POST", "/api/scores", dict(score, bank_id=shared))[0], 201)
        self.assertEqual(mine.json("POST", "/api/scores", dict(score, bank_id=hidden))[0], 404)
        self.assertEqual(mine.json("POST", "/api/scores", dict(score, bank_id="abc"))[0], 400)
        self.assertEqual(mine.json("POST", "/api/scores", score)[0], 201, "离线页等没有 bank_id 的成绩照常保存")

    def test_admin_sets_tags_on_one_student_and_on_a_batch(self):
        admin = self.admin()
        _, u1, c1 = self.student()
        _, u2, c2 = self.student(["旧"])
        bid = self.new_bank(admin, tags="初二")
        self.assertEqual(admin.json("POST", "/api/admin/users/%d/tags" % u1, {"tags": "初二, 三班"})[1]["tags"],
                         ["初二", "三班"])
        self.assertIn(bid, self.ids(c1))
        status, body = admin.json("POST", "/api/admin/users/tags", {"user_ids": [u1, u2, 99999], "add": "初二", "remove": "旧"})
        self.assertEqual((status, body["changed"]), (200, 2), "不存在的编号被忽略")
        users = {u["id"]: u for u in admin.json("GET", "/api/admin/users")[1]["users"]}
        self.assertEqual((users[u1]["tags"], users[u2]["tags"]), (["三班", "初二"], ["初二"]))
        self.assertIn(bid, self.ids(c2))

    def test_the_batch_never_touches_admin_accounts_and_needs_something_to_do(self):
        admin = self.admin()
        t001 = self.svc.get_by_student_no("T001")["id"]
        self.assertEqual(admin.json("POST", "/api/admin/users/tags", {"user_ids": [t001], "add": "x"})[1]["changed"], 0)
        self.assertEqual(admin.json("POST", "/api/admin/users/tags", {"user_ids": [], "add": "x"})[0], 400)
        self.assertEqual(admin.json("POST", "/api/admin/users/tags", {"user_ids": [t001]})[0], 400)
        self.assertEqual(admin.json("POST", "/api/admin/users/tags", {"user_ids": ["1"], "add": "x"})[0], 400)

    def test_students_cannot_manage_banks_or_tags_at_all(self):
        admin = self.admin()
        _, uid, mine = self.student(["初二"])
        bid = self.new_bank(admin, tags="初二")
        for method, path, body in (("POST", "/api/banks", SEED_SPEC),
                                   ("DELETE", "/api/banks/%d" % bid, None),
                                   ("POST", "/api/banks/%d/meta" % bid, {"tags": "x"}),
                                   ("POST", "/api/admin/users/%d/tags" % uid, {"tags": "全部"}),
                                   ("POST", "/api/admin/users/tags", {"user_ids": [uid], "add": "全部"})):
            self.assertEqual(mine.json(method, path, body)[0], 403, (method, path))
        self.assertIn(bid, self.ids(admin), "被拒绝的删除没有生效")

    def test_a_teacher_can_still_delete_and_play_everything(self):
        admin = self.admin()
        bid = self.new_bank(admin)
        self.assertEqual(admin.json("GET", "/api/banks/%d" % bid)[0], 200)
        self.assertEqual(admin.json("DELETE", "/api/banks/%d" % bid)[0], 200)
        self.assertEqual(admin.json("GET", "/api/banks/%d" % bid)[0], 404)


class TestLanEditionTagsDoNothing(HttpCase):
    auth_options = False

    def test_everything_is_open_without_accounts(self):
        c = Client(self.port)
        status, body = c.json("POST", "/api/banks", SEED_SPEC)
        self.assertEqual(status, 201)
        bid = body["bank"]["id"]
        listed = c.json("GET", "/api/banks")[1]["banks"]
        self.assertIn(bid, {b["id"] for b in listed}, "局域网版没打标签的题库照样看得到")
        self.assertEqual(c.json("GET", "/api/banks/%d" % bid)[0], 200)
        self.assertEqual(c.json("DELETE", "/api/banks/%d" % bid)[0], 200)


if __name__ == "__main__":
    unittest.main()
