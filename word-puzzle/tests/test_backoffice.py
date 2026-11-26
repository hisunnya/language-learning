"""总后台接口 /api/backoffice：老师在一个请求里看全六个模块的名下成绩。

要守住的三件事：
* 只有老师和超级管理员能用（学生 403、没登录 401）；
* 老师只看得到自己名下的学生（范围由 server/tenancy.py 决定，这里不另写过滤）；
* 模块概况、最近记录、名下学生三样都对得上。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, ROOT.as_posix())

from server import tenancy                                     # noqa: E402
from tests.test_auth import Client, HttpCase                   # noqa: E402


class BackOfficeCase(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.svc.create_user("BOSS", "超管", password="Boss2026pw", role="admin", must_change=False)
        cls.svc.create_user("T001", "王老师", password="Teach2026x", role="teacher", must_change=False)
        cls.svc.create_user("T002", "李老师", password="Teach2026x", role="teacher", must_change=False)
        for no, name in (("S001", "甲"), ("S002", "乙"), ("S003", "丙")):
            cls.svc.create_user(no, name, password="Ready2026x", must_change=False)
        db = cls.app.Handler.db
        cls.ids = {u["student_no"]: u["id"] for u in cls.svc.list_users()}
        # 王老师带甲、乙；李老师带丙
        tenancy.link_student(db, cls.ids["T001"], cls.ids["S001"], None)
        tenancy.link_student(db, cls.ids["T001"], cls.ids["S002"], None)
        tenancy.link_student(db, cls.ids["T002"], cls.ids["S003"], None)

    def login(self, no, pw):
        c = Client(self.port)
        status, body = c.json("POST", "/api/auth/login", {"student_no": no, "password": pw})
        self.assertEqual(status, 200, body)
        return c

    def post_record(self, client, subject, payload):
        status, body = client.json("POST", "/api/records", {"subject": subject, "kind": "practice", "payload": payload})
        self.assertEqual(status, 201, body)


class TestBackofficeAccess(BackOfficeCase):
    def test_a_guest_cannot_read_the_backoffice(self):
        status, body = Client(self.port).json("GET", "/api/backoffice")
        self.assertEqual(status, 401, body)
        self.assertEqual(body["code"], "login_required")

    def test_a_student_is_not_staff(self):
        student = self.login("S001", "Ready2026x")
        status, body = student.json("GET", "/api/backoffice")
        self.assertEqual(status, 403, body)
        self.assertEqual(body["code"], "forbidden")

    def test_a_teacher_and_the_super_admin_can_read_it(self):
        for no, pw in (("T001", "Teach2026x"), ("BOSS", "Boss2026pw")):
            client = self.login(no, pw)
            status, body = client.json("GET", "/api/backoffice")
            self.assertEqual(status, 200, body)
            self.assertTrue(body["ok"])
            self.assertEqual(body["me"]["student_no"], no)
            self.assertEqual(len(body["modules"]), 6, "六个模块都要在")


class TestBackofficeScope(BackOfficeCase):
    def test_a_teacher_only_sees_their_own_students(self):
        mine = self.login("S001", "Ready2026x")
        self.post_record(mine, "chemistry", {"score": 10})
        theirs = self.login("S003", "Ready2026x")
        self.post_record(theirs, "chemistry", {"score": 30})

        status, body = self.login("T001", "Teach2026x").json("GET", "/api/backoffice")
        self.assertEqual(status, 200, body)
        names = {r["name"] for r in body["recent"]}
        self.assertIn("甲", names)
        self.assertNotIn("丙", names, "李老师的学生不该出现在王老师的后台里")
        students = {s["student_no"] for s in body["students"]}
        self.assertIn("S001", students)
        self.assertNotIn("S003", students)

    def test_the_super_admin_sees_everybody(self):
        body = self.login("BOSS", "Boss2026pw").json("GET", "/api/backoffice")[1]
        names = {r["name"] for r in body["recent"]}
        self.assertIn("甲", names)
        self.assertIn("丙", names)
        students = {s["student_no"] for s in body["students"]}
        self.assertTrue({"S001", "S002", "S003"} <= students)

    def test_the_module_summary_counts_match_the_records(self):
        student = self.login("S002", "Ready2026x")
        self.post_record(student, "physics", {"score": 20})
        self.post_record(student, "physics", {"score": 40})
        body = self.login("T001", "Teach2026x").json("GET", "/api/backoffice")[1]
        physics = [m for m in body["modules"] if m["id"] == "physics"][0]
        self.assertEqual(physics["records"], 2)
        self.assertEqual(physics["students"], 1)
        self.assertTrue(physics["last_at"] > 0)

    def test_the_subject_filter_narrows_the_records(self):
        student = self.login("S002", "Ready2026x")
        self.post_record(student, "chemistry", {"score": 1})
        self.post_record(student, "physics", {"score": 2})
        client = self.login("T001", "Teach2026x")
        body = client.json("GET", "/api/backoffice?subject=physics")[1]
        self.assertTrue(body["recent"])
        self.assertEqual({r["subject"] for r in body["recent"]}, {"physics"})

    def test_the_payload_comes_back_as_a_json_object(self):
        student = self.login("S002", "Ready2026x")
        self.post_record(student, "chemistry", {"score": 7, "mode": "elements"})
        body = self.login("T001", "Teach2026x").json("GET", "/api/backoffice")[1]
        payloads = [r["payload"] for r in body["recent"] if r["subject"] == "chemistry"]
        self.assertIn({"score": 7, "mode": "elements"}, payloads)

    def test_the_records_are_newest_first(self):
        student = self.login("S002", "Ready2026x")
        self.post_record(student, "chemistry", {"n": 1})
        self.post_record(student, "chemistry", {"n": 2})
        body = self.login("T001", "Teach2026x").json("GET", "/api/backoffice")[1]
        ids = [r["id"] for r in body["recent"] if r["subject"] == "chemistry"]
        self.assertEqual(ids, sorted(ids, reverse=True))


if __name__ == "__main__":
    unittest.main()
