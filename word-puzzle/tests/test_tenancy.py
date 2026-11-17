"""多位老师（租户）：底层一份数据，上层按老师隔离。

* 老师只看得到、只管得了自己名下的学生、题库、词表、成绩、访问记录；内置题库所有老师共用；
* 标签按老师分开：A 老师的「一班」和 B 老师的「一班」互不相干；
* 第二位老师导入已存在的学号 = 自动共享（按管理员的决定），并记进审计；
* 删除是软删除，超级管理员能看到并恢复；别人共享过来的，删除只是从自己名下移走；
* 超级管理员什么都看得到，能加老师、共享 / 分配题库和学生；
* 家庭版访客只看得到内置题库和超管的题库。
"""
from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, ROOT.as_posix())

from server import tenancy                                  # noqa: E402
from server.db import Database                              # noqa: E402
from tests.test_auth import Client, HttpCase, multipart     # noqa: E402

LAN = {"X-Wp-Entry": "lan"}
PW = "Ready2026x"


class TestMigrationFromTheSingleTeacherVersion(unittest.TestCase):
    """线上的老库：标签没有 teacher_id、账号没有 deleted_at、没有老师和学生的关系表。"""

    def make_old_db(self, path: Path):
        c = sqlite3.connect(path)
        c.executescript("""
            CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, student_no TEXT NOT NULL UNIQUE, name TEXT NOT NULL DEFAULT '',
                class_name TEXT NOT NULL DEFAULT '', college TEXT NOT NULL DEFAULT '', department TEXT NOT NULL DEFAULT '',
                role TEXT NOT NULL DEFAULT 'student', pw_hash TEXT NOT NULL, must_change INTEGER NOT NULL DEFAULT 1,
                disabled INTEGER NOT NULL DEFAULT 0, failed_count INTEGER NOT NULL DEFAULT 0, locked_until REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL, last_login_at TEXT NOT NULL DEFAULT '');
            CREATE TABLE user_tags (user_id INTEGER NOT NULL, tag TEXT NOT NULL, PRIMARY KEY (user_id, tag));
            CREATE TABLE bank_tags (bank_id INTEGER NOT NULL, tag TEXT NOT NULL, PRIMARY KEY (bank_id, tag));
            CREATE INDEX ix_bank_tags_tag ON bank_tags(tag);
            INSERT INTO users(id, student_no, name, role, pw_hash, created_at) VALUES (7, 'T001', '孙老师', 'admin', 'x', 'now');
            INSERT INTO users(id, student_no, name, role, pw_hash, created_at) VALUES (8, 'S001', '甲', 'student', 'x', 'now');
            INSERT INTO users(id, student_no, name, role, pw_hash, created_at) VALUES (9, 'S002', '乙', 'student', 'x', 'now');
            INSERT INTO user_tags VALUES (8, '一班'), (9, '二班');
            INSERT INTO bank_tags VALUES (1, '一班'), (2, '一班'), (2, '二班');
            PRAGMA user_version = 1;
        """)
        c.commit()
        c.close()

    def test_tags_go_to_the_first_admin_and_students_are_linked_to_her_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "old.db"
            self.make_old_db(path)
            db = Database(str(path))
            try:
                self.assertEqual(db.one("PRAGMA user_version")[0], 2)
                self.assertEqual(sorted(tuple(r) for r in db.query("SELECT user_id, tag, teacher_id FROM user_tags")),
                                 [(8, "一班", 7), (9, "二班", 7)])
                self.assertEqual(sorted(tuple(r) for r in db.query("SELECT bank_id, tag, teacher_id FROM bank_tags")),
                                 [(1, "一班", 7), (2, "一班", 7), (2, "二班", 7)])
                self.assertEqual(sorted(r["student_id"] for r in db.query("SELECT student_id FROM teacher_students WHERE teacher_id=7")), [8, 9])
                self.assertEqual(db.one("SELECT COUNT(*) n FROM users WHERE deleted_at<>0")["n"], 0)
                db.execute("DELETE FROM teacher_students")
            finally:
                db.close()
            db = Database(str(path))                         # 再打开一次：不会重复迁移
            try:
                self.assertEqual(db.one("SELECT COUNT(*) n FROM teacher_students")["n"], 0, "只做一次")
                self.assertEqual(db.one("SELECT COUNT(*) n FROM user_tags")["n"], 2)
            finally:
                db.close()


class TenantCase(HttpCase):
    counter = 0

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.db = cls.app.Handler.db
        cls.svc.create_user("ROOT", "孙老师", password="Teach3r!pw", role="admin", must_change=False)
        cls.svc.create_user("TA", "甲老师", password="Teach3r!pw", role="teacher", must_change=False)
        cls.svc.create_user("TB", "乙老师", password="Teach3r!pw", role="teacher", must_change=False)
        cls.root, cls.ta, cls.tb = (cls.login_as(no, "Teach3r!pw") for no in ("ROOT", "TA", "TB"))
        cls.ids = {no: cls.svc.get_by_student_no(no)["id"] for no in ("ROOT", "TA", "TB")}

    @classmethod
    def login_as(cls, no, pw):
        c = Client(cls.port)
        status, body = c.json("POST", "/api/auth/login", {"student_no": no, "password": pw})
        assert status == 200, body
        return c

    def roster(self, teacher, rows):
        csv = "学号,姓名,班级\n" + "".join("%s,%s,%s\n" % r for r in rows)
        body, headers = multipart({}, {"file": ("名单.csv", csv.encode("utf-8"))})
        status, res = teacher.json("POST", "/api/admin/import", raw=body, headers=headers)
        self.assertEqual(status, 200, res)
        return res

    def new_no(self, prefix="S"):
        type(self).counter += 1
        return "%s%04d" % (prefix, type(self).counter)

    def student_of(self, teacher, name="学生"):
        no = self.new_no()
        self.roster(teacher, [(no, name, "一班")])
        self.svc.db.execute("UPDATE users SET must_change=0, pw_hash=(SELECT pw_hash FROM users WHERE student_no='TA') WHERE student_no=?", (no,))
        return no, self.svc.get_by_student_no(no)["id"]

    def bank(self, teacher, title, tags=None):
        body = {"source": "seed", "level1": "初中", "level2": "七年级", "level3": "上册", "level4": "all",
                "unit_mode": "all", "title": title}
        if tags is not None:
            body["tags"] = tags
        status, res = teacher.json("POST", "/api/banks", body)
        self.assertEqual(status, 201, res)
        return res["bank"]["id"]

    def seed_bank_id(self):
        return self.db.one("SELECT id FROM banks WHERE owner_id IS NULL AND deleted_at=0 ORDER BY id LIMIT 1")["id"]

    def bank_ids(self, client, headers=None):
        return {b["id"] for b in client.json("GET", "/api/banks", headers=headers)[1]["banks"]}

    def user_nos(self, client):
        return {u["student_no"] for u in client.json("GET", "/api/admin/users")[1]["users"]}


class TestIsolation(TenantCase):
    def test_each_teacher_sees_only_their_students(self):
        a_no, _ = self.student_of(self.ta)
        b_no, _ = self.student_of(self.tb)
        self.assertIn(a_no, self.user_nos(self.ta))
        self.assertNotIn(b_no, self.user_nos(self.ta))
        self.assertIn(b_no, self.user_nos(self.tb))
        self.assertNotIn(a_no, self.user_nos(self.tb))
        self.assertTrue({a_no, b_no} <= self.user_nos(self.root), "超管看得到所有人")
        self.assertFalse({"TA", "TB", "ROOT"} & self.user_nos(self.ta), "老师的账号列表里没有老师")

    def test_each_teacher_sees_own_banks_plus_the_built_in_ones(self):
        a_bank, b_bank = self.bank(self.ta, "甲的书"), self.bank(self.tb, "乙的书")
        seed = self.seed_bank_id()
        self.assertTrue({a_bank, seed} <= self.bank_ids(self.ta))
        self.assertNotIn(b_bank, self.bank_ids(self.ta))
        self.assertTrue({b_bank, seed} <= self.bank_ids(self.tb))
        self.assertTrue({a_bank, b_bank, seed} <= self.bank_ids(self.root))
        for method, path, body in (("GET", "/api/banks/%d" % a_bank, None), ("DELETE", "/api/banks/%d" % a_bank, None),
                                   ("POST", "/api/banks/%d/meta" % a_bank, {"tags": "x"}),
                                   ("POST", "/api/banks/%d/offline" % a_bank, {})):
            self.assertEqual(self.tb.json(method, path, body)[0], 404, path + "：别人的题库一律当成不存在")

    def test_built_in_banks_can_be_tagged_but_not_deleted_or_renamed_by_a_teacher(self):
        seed = self.seed_bank_id()
        self.assertEqual(self.ta.json("DELETE", "/api/banks/%d" % seed)[0], 403)
        self.assertEqual(self.ta.json("POST", "/api/banks/%d/meta" % seed, {"category": "我的"})[0], 403)
        status, res = self.ta.json("POST", "/api/banks/%d/meta" % seed, {"tags": "甲班"})
        self.assertEqual((status, res["bank"]["tags"]), (200, ["甲班"]))
        self.assertEqual([b["tags"] for b in self.tb.json("GET", "/api/banks")[1]["banks"] if b["id"] == seed], [[]],
                         "乙老师看不到甲老师打的标签")
        self.ta.json("POST", "/api/banks/%d/meta" % seed, {"tags": ""})

    def test_same_tag_name_under_two_teachers_does_not_leak(self):
        a_no, a_id = self.student_of(self.ta)
        b_no, b_id = self.student_of(self.tb)
        self.ta.json("POST", "/api/admin/users/%d/tags" % a_id, {"tags": "一班"})
        self.tb.json("POST", "/api/admin/users/%d/tags" % b_id, {"tags": "一班"})
        x, y = self.bank(self.ta, "甲开放", tags="一班"), self.bank(self.tb, "乙开放", tags="一班")
        a, b = self.login_as(a_no, "Teach3r!pw"), self.login_as(b_no, "Teach3r!pw")
        self.assertIn(x, self.bank_ids(a))
        self.assertNotIn(y, self.bank_ids(a), "乙老师的「一班」不是甲老师的「一班」")
        self.assertIn(y, self.bank_ids(b))
        self.assertNotIn(x, self.bank_ids(b))
        self.assertEqual(b.json("GET", "/api/banks/%d" % x)[0], 404)

    def test_scores_visits_and_logins_follow_the_students(self):
        a_no, a_id = self.student_of(self.ta)
        self.ta.json("POST", "/api/admin/users/%d/tags" % a_id, {"tags": "成绩班"})
        x = self.bank(self.ta, "成绩书", tags="成绩班")
        a = self.login_as(a_no, "Teach3r!pw")
        self.assertEqual(a.json("POST", "/api/scores", {"bank_id": x, "bank_title": "t", "score": 77, "matched": 9, "total_pairs": 9,
                                                         "wrong": 0, "best_combo": 3, "duration": 30, "level_count": 1, "detail": []})[0], 201)
        a.request("POST", "/api/track", {"event": "view", "vid": "v" * 16 + a_no, "sid": "s" * 16, "path": "/word-puzzle/"})
        see = lambda c, path, key: [r for r in c.json("GET", path)[1][key] if r.get("user_id") == a_id]
        self.assertTrue(see(self.ta, "/api/scores/summary", "rows"))
        self.assertFalse(see(self.tb, "/api/scores/summary", "rows"))
        self.assertTrue(see(self.root, "/api/scores/summary", "rows"))
        self.assertFalse(see(self.tb, "/api/scores", "scores"))
        self.assertTrue(see(self.ta, "/api/admin/visits?limit=500", "sessions"))
        self.assertFalse(see(self.tb, "/api/admin/visits?limit=500", "sessions"))
        self.assertTrue(see(self.ta, "/api/admin/logins?limit=500", "logins"))
        self.assertFalse(see(self.tb, "/api/admin/logins?limit=500", "logins"))
        self.assertEqual(self.tb.json("GET", "/api/scores/plays?user_id=%d" % a_id)[1]["plays"], [])
        self.assertNotIn(a_no.encode(), self.tb.request("GET", "/api/admin/export/scores.csv")[1])
        self.assertNotIn(a_no.encode(), self.tb.request("GET", "/api/admin/export/page-views.csv")[1])

    def test_materials_are_private_to_whoever_uploaded_them(self):
        body, headers = multipart({}, {"file": ("w.csv", "unit,en,cn\nUnit 1,apple,苹果\nUnit 1,pear,梨\n".encode())})
        mid = self.ta.json("POST", "/api/materials", raw=body, headers=headers)[1]["material"]["id"]
        self.assertIn(mid, [m["id"] for m in self.ta.json("GET", "/api/materials")[1]["materials"]])
        self.assertNotIn(mid, [m["id"] for m in self.tb.json("GET", "/api/materials")[1]["materials"]])
        self.assertIn(mid, [m["id"] for m in self.root.json("GET", "/api/materials")[1]["materials"]])
        status, _ = self.tb.json("POST", "/api/banks", {"source": "material", "material_id": mid, "title": "偷来的", "level1": "a",
                                                         "level2": "b", "level3": "c", "level4": "d", "unit_mode": "all"})
        self.assertEqual(status, 400, "不能拿别人的词表建题库")
        self.assertEqual(self.tb.json("DELETE", "/api/materials/%d" % mid)[0], 404)

    def test_a_teacher_cannot_touch_other_teachers_students_or_accounts(self):
        a_no, a_id = self.student_of(self.ta)
        for action in ("reset-password", "disabled", "unlock", "tags"):
            self.assertEqual(self.tb.json("POST", "/api/admin/users/%d/%s" % (a_id, action), {"tags": "x"})[0], 404, action)
        self.assertEqual(self.ta.json("POST", "/api/admin/users/%d/reset-password" % self.ids["TB"], {})[0], 404,
                         "老师不能重置别的老师的密码")
        self.assertEqual(self.ta.json("POST", "/api/admin/users/%d/reset-password" % self.ids["ROOT"], {})[0], 404)
        self.assertEqual(self.ta.json("POST", "/api/admin/users/%d/reset-password" % a_id, {})[0], 200)

    def test_super_only_endpoints_refuse_teachers_and_students(self):
        a_no, _ = self.student_of(self.ta)
        a = self.login_as(a_no, "Teach3r!pw")
        for method, path in (("GET", "/api/admin/teachers"), ("POST", "/api/admin/teachers"), ("POST", "/api/admin/assign"),
                             ("GET", "/api/admin/deleted"), ("POST", "/api/admin/restore"), ("GET", "/api/admin/audit")):
            self.assertEqual(self.ta.json(method, path, {} if method == "POST" else None)[0], 403, path)
            self.assertEqual(a.json(method, path, {} if method == "POST" else None)[0], 403, path)

    def test_me_reports_the_teacher_role(self):
        self.assertEqual(self.ta.json("GET", "/api/auth/me")[1]["user"]["role"], "teacher")


class TestDuplicateStudentNumbers(TenantCase):
    def test_a_second_teacher_importing_the_number_shares_the_student_and_it_is_audited(self):
        no, sid = self.student_of(self.ta, "原名")
        res = self.roster(self.tb, [(no, "改名", "乙的班")])
        self.assertEqual((res["created"], res["shared"], res["updated"]), (0, 1, 0))
        self.assertIn(no, self.user_nos(self.tb))
        self.assertIn(no, self.user_nos(self.ta))
        self.assertEqual(self.svc.get_by_id(sid)["name"], "原名", "共享的学生不改甲老师那边的资料")
        audit = self.root.json("GET", "/api/admin/audit")[1]["audit"]
        hit = [a for a in audit if a["action"] == "student.auto_share" and a["target_id"] == sid]
        self.assertEqual(len(hit), 1)
        self.assertEqual((hit[0]["detail"]["teacher_id"], hit[0]["detail"]["other_teachers"]), (self.ids["TB"], [self.ids["TA"]]))
        users = {u["student_no"]: u for u in self.root.json("GET", "/api/admin/users")[1]["users"]}
        self.assertEqual({t["name"] for t in users[no]["teachers"]}, {"甲老师", "乙老师"})

    def test_reimporting_my_own_student_still_updates_the_details(self):
        no, sid = self.student_of(self.ta, "旧名")
        res = self.roster(self.ta, [(no, "新名", "一班")])
        self.assertEqual((res["updated"], res["shared"]), (1, 0))
        self.assertEqual(self.svc.get_by_id(sid)["name"], "新名")

    def test_teacher_accounts_are_never_taken_over_by_a_roster(self):
        res = self.roster(self.tb, [("TA", "冒充", "一班")])
        self.assertEqual(res["skipped"], 1)
        self.assertEqual(self.svc.get_by_student_no("TA")["role"], "teacher")


class TestSoftDelete(TenantCase):
    def test_deleting_my_bank_hides_it_and_the_super_admin_can_restore_it(self):
        x = self.bank(self.ta, "要删的书")
        self.assertEqual(self.ta.json("DELETE", "/api/banks/%d" % x)[1]["done"], "deleted")
        self.assertNotIn(x, self.bank_ids(self.ta))
        self.assertNotIn(x, self.bank_ids(self.root), "超管的列表里也不出现，在「已删除」里")
        self.assertIsNotNone(self.db.get_bank(x), "数据还在")
        deleted = self.root.json("GET", "/api/admin/deleted")[1]
        self.assertIn(x, [b["id"] for b in deleted["banks"]])
        self.assertEqual([b["deleted_by_name"] for b in deleted["banks"] if b["id"] == x], ["甲老师"])
        self.assertEqual(self.root.json("POST", "/api/admin/restore", {"kind": "bank", "id": x})[0], 200)
        self.assertIn(x, self.bank_ids(self.ta))
        self.assertEqual(self.root.json("POST", "/api/admin/restore", {"kind": "bank", "id": x})[0], 404, "没删的不能恢复")

    def test_deleting_a_bank_someone_shared_with_me_only_removes_it_from_me(self):
        x = self.bank(self.root, "超管共享的书")
        self.root.json("POST", "/api/admin/assign", {"kind": "bank", "mode": "share", "ids": [x], "teacher_id": self.ids["TA"]})
        self.assertIn(x, self.bank_ids(self.ta))
        self.assertEqual(self.ta.json("DELETE", "/api/banks/%d" % x)[1]["done"], "unshared")
        self.assertNotIn(x, self.bank_ids(self.ta))
        self.assertIn(x, self.bank_ids(self.root))
        self.assertEqual(self.db.get_bank(x)["deleted_at"], 0)

    def test_deleting_students_and_a_whole_class(self):
        shared_no, shared_id = self.student_of(self.ta)
        self.roster(self.tb, [(shared_no, "x", "y")])                       # 也在乙老师名下
        only_no, only_id = self.student_of(self.ta)
        res = self.ta.json("POST", "/api/admin/users/delete", {"user_ids": [shared_id, only_id]})[1]
        self.assertEqual((res["deleted"], res["unlinked"]), (1, 1))
        self.assertNotIn(shared_no, self.user_nos(self.ta))
        self.assertIn(shared_no, self.user_nos(self.tb), "乙老师名下还在")
        self.assertNotIn(only_no, self.user_nos(self.ta))
        self.assertEqual(Client(self.port).json("POST", "/api/auth/login", {"student_no": only_no, "password": "Teach3r!pw"})[0], 401,
                         "删除的学生登不上")
        self.assertIn(only_id, [u["id"] for u in self.root.json("GET", "/api/admin/deleted")[1]["users"]])
        self.root.json("POST", "/api/admin/restore", {"kind": "user", "id": only_id})
        self.assertIn(only_no, self.user_nos(self.ta), "恢复后回到原来的老师名下")
        self.assertEqual(self.tb.json("POST", "/api/admin/users/delete", {"user_ids": [only_id]})[1]["deleted"], 0,
                         "不能删别的老师的学生")

    def test_deleted_materials_are_hidden_and_restorable(self):
        body, headers = multipart({}, {"file": ("d.csv", "unit,en,cn\nUnit 1,cat,猫\n".encode())})
        mid = self.ta.json("POST", "/api/materials", raw=body, headers=headers)[1]["material"]["id"]
        self.assertEqual(self.ta.json("DELETE", "/api/materials/%d" % mid)[0], 200)
        self.assertNotIn(mid, [m["id"] for m in self.ta.json("GET", "/api/materials")[1]["materials"]])
        self.assertIn(mid, [m["id"] for m in self.root.json("GET", "/api/admin/deleted")[1]["materials"]])
        self.root.json("POST", "/api/admin/restore", {"kind": "material", "id": mid})
        self.assertIn(mid, [m["id"] for m in self.ta.json("GET", "/api/materials")[1]["materials"]])


class TestSuperAdmin(TenantCase):
    def test_add_a_teacher_who_must_change_the_initial_password(self):
        status, res = self.root.json("POST", "/api/admin/teachers", {"student_no": "TC", "name": "丙老师"})
        self.assertEqual(status, 201, res)
        self.assertTrue(res["password"])
        self.assertEqual((res["teacher"]["role"], res["teacher"]["must_change"]), ("teacher", True))
        teachers = {t["student_no"]: t for t in self.root.json("GET", "/api/admin/teachers")[1]["teachers"]}
        self.assertIn("TC", teachers)
        self.assertEqual(self.root.json("POST", "/api/admin/teachers", {"student_no": "TC", "name": "重复"})[0], 409)
        self.assertEqual(self.root.json("POST", "/api/admin/teachers", {"student_no": "TD", "name": "短密码", "password": "123"})[0], 400)

    def test_share_unshare_and_move_banks(self):
        x = self.bank(self.ta, "甲的分配书")
        assign = lambda mode, teacher: self.root.json("POST", "/api/admin/assign",
                                                       {"kind": "bank", "mode": mode, "ids": [x], "teacher_id": self.ids[teacher]})
        assign("share", "TB")
        self.assertIn(x, self.bank_ids(self.tb))
        self.assertIn(x, self.bank_ids(self.ta))
        b_no, b_id = self.student_of(self.tb)
        self.tb.json("POST", "/api/admin/users/%d/tags" % b_id, {"tags": "乙班"})
        self.tb.json("POST", "/api/banks/%d/meta" % x, {"tags": "乙班"})
        b = self.login_as(b_no, "Teach3r!pw")
        self.assertIn(x, self.bank_ids(b))
        assign("unshare", "TB")
        self.assertNotIn(x, self.bank_ids(self.tb))
        self.assertNotIn(x, self.bank_ids(b), "不再共享：乙老师在这个题库上的标签一起去掉，他的学生也看不到了")
        assign("move", "TB")
        self.assertEqual(self.db.get_bank(x)["owner_id"], self.ids["TB"])
        self.assertIn(x, self.bank_ids(self.tb))
        self.assertNotIn(x, self.bank_ids(self.ta), "转给乙老师之后甲老师就没有了")

    def test_share_and_move_students(self):
        no, sid = self.student_of(self.ta)
        assign = lambda mode, teacher: self.root.json("POST", "/api/admin/assign",
                                                       {"kind": "student", "mode": mode, "ids": [sid], "teacher_id": self.ids[teacher]})
        self.ta.json("POST", "/api/admin/users/%d/tags" % sid, {"tags": "甲班"})
        assign("share", "TB")
        self.assertTrue({no} <= self.user_nos(self.ta) & self.user_nos(self.tb))
        assign("move", "TB")
        self.assertNotIn(no, self.user_nos(self.ta))
        self.assertIn(no, self.user_nos(self.tb))
        self.assertEqual(self.db.query("SELECT tag FROM user_tags WHERE user_id=? AND teacher_id=?", (sid, self.ids["TA"])), [],
                         "转走之后甲老师打的标签一起去掉")
        audit = [a["action"] for a in self.root.json("GET", "/api/admin/audit")[1]["audit"] if a["target_id"] == sid]
        self.assertIn("student.share", audit)
        self.assertIn("student.move", audit)

    def test_assign_validates_its_input(self):
        for body in ({}, {"kind": "bank", "mode": "steal", "ids": [1], "teacher_id": self.ids["TA"]},
                     {"kind": "bank", "mode": "share", "ids": [], "teacher_id": self.ids["TA"]},
                     {"kind": "bank", "mode": "share", "ids": [1], "teacher_id": 999999}):
            self.assertEqual(self.root.json("POST", "/api/admin/assign", body)[0], 400, body)

    def test_the_super_admin_can_delete_any_bank_including_built_in_ones(self):
        x = self.bank(self.tb, "乙的被超管删")
        self.assertEqual(self.root.json("DELETE", "/api/banks/%d" % x)[1]["done"], "deleted")
        self.assertNotIn(x, self.bank_ids(self.tb))
        self.root.json("POST", "/api/admin/restore", {"kind": "bank", "id": x})


class TestHomeEditionVisitors(TenantCase):
    def setUp(self):
        patcher = mock.patch.dict(os.environ, {"WP_LAN_GUEST": "1"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_visitors_see_built_in_and_super_admin_banks_only(self):
        mine, theirs = self.bank(self.root, "超管的书"), self.bank(self.ta, "甲老师的书")
        seen = self.bank_ids(Client(self.port), headers=LAN)
        self.assertIn(self.seed_bank_id(), seen)
        self.assertIn(mine, seen)
        self.assertNotIn(theirs, seen)
        self.assertEqual(Client(self.port).json("GET", "/api/banks/%d" % theirs, headers=LAN)[0], 404)

    def test_visitors_only_see_anonymous_scores(self):
        a_no, a_id = self.student_of(self.ta)
        self.ta.json("POST", "/api/admin/users/%d/tags" % a_id, {"tags": "访客班"})
        x = self.bank(self.ta, "访客成绩书", tags="访客班")
        self.login_as(a_no, "Teach3r!pw").json("POST", "/api/scores", {"bank_id": x, "bank_title": "t", "score": 5, "matched": 1,
                                                                        "total_pairs": 1, "wrong": 0, "best_combo": 1, "duration": 3,
                                                                        "level_count": 1, "detail": []})
        rows = Client(self.port).json("GET", "/api/scores/summary", headers=LAN)[1]["rows"]
        self.assertFalse([r for r in rows if r["user_id"] is not None], "访客看不到任何学生的成绩")


class TestScopeUnits(unittest.TestCase):
    def test_scope_for(self):
        self.assertEqual(tenancy.scope_for(False, None, False).kind, tenancy.ALL)
        self.assertEqual(tenancy.scope_for(True, {"id": 1, "role": "admin"}, False).kind, tenancy.SUPER)
        self.assertEqual(tenancy.scope_for(True, {"id": 2, "role": "teacher"}, False).kind, tenancy.TEACHER)
        self.assertEqual(tenancy.scope_for(True, {"id": 3, "role": "student"}, True).kind, tenancy.STUDENT)
        self.assertEqual(tenancy.scope_for(True, None, True).kind, tenancy.GUEST)
        self.assertEqual(tenancy.scope_for(True, None, False).kind, tenancy.NOBODY)

    def test_tag_owner(self):
        self.assertEqual(tenancy.Scope(tenancy.TEACHER, 5).tag_teacher, 5)
        self.assertEqual(tenancy.Scope(tenancy.SUPER, 1).tag_teacher, 1)
        self.assertEqual(tenancy.Scope(tenancy.ALL).tag_teacher, 0)
        self.assertEqual(tenancy.Scope(tenancy.STUDENT, 9).tag_teacher, 0)

    def test_nobody_sees_nothing(self):
        for fn in (tenancy.bank_where, tenancy.student_where, tenancy.material_where):
            self.assertEqual(fn(tenancy.Scope(tenancy.NOBODY))[0], "0")
        self.assertEqual(tenancy.people_where(tenancy.Scope(tenancy.NOBODY), "user_id")[0], "0")


if __name__ == "__main__":
    unittest.main()
