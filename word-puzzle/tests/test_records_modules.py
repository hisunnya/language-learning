"""模块登记表、通用成绩记录接口、权限判断集中在 policy.py（给以后接入其他学科和多老师权限留的接口）。"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, ROOT.as_posix())

from server import modules, policy                  # noqa: E402
from tests.test_auth import Client, HttpCase        # noqa: E402

LAN = {"X-Wp-Entry": "lan"}


class TestPolicy(unittest.TestCase):
    def test_admin_can_do_everything_students_only_their_own_things(self):
        admin, student = {"role": "admin"}, {"role": "student"}
        for action in policy.ADMIN_ONLY:
            self.assertTrue(policy.allow(admin, action), action)
            self.assertFalse(policy.allow(student, action), action)
            self.assertFalse(policy.allow(None, action), action)
        self.assertTrue(policy.allow(student, "records.write_own"))
        self.assertFalse(policy.allow(None, "records.write_own"))

    def test_resources_are_accepted_for_future_scoped_teachers(self):
        self.assertTrue(policy.allow({"role": "admin"}, "bank.edit", {"bank_id": 3, "class_name": "一班", "subject": "lexica"}))


class TestRegistry(unittest.TestCase):
    def test_lexica_is_enabled_and_the_other_subjects_are_planned(self):
        enabled = modules.enabled_ids()
        self.assertEqual(enabled, {"lexica"})
        self.assertTrue({"topics", "ham", "chemistry", "physics"} <= {m["id"] for m in modules.listing()})
        for m in modules.listing():
            self.assertTrue(m["zh"] and m["en"] and m["path"].startswith("/") and m["path"].endswith("/"), m)


class RecordsCase(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.svc.create_user("T001", "老师", password="Teach3r!pw", role="admin", must_change=False)
        cls.svc.create_user("S001", "甲", password="Ready2026x", must_change=False)
        cls.svc.create_user("S002", "乙", password="Ready2026x", must_change=False)

    def login(self, no, pw):
        c = Client(self.port)
        self.assertEqual(c.json("POST", "/api/auth/login", {"student_no": no, "password": pw})[0], 200)
        return c


class TestRecordsApi(RecordsCase):
    def setUp(self):
        patcher = mock.patch.dict(os.environ, {"WP_LAN_GUEST": "1"})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.enabled = mock.patch.object(modules, "enabled_ids", return_value={"lexica", "chemistry"})
        self.enabled.start()
        self.addCleanup(self.enabled.stop)

    def post(self, c, **body):
        return c.json("POST", "/api/records", body)

    def test_modules_list_needs_login_and_has_the_registry(self):
        self.assertEqual(Client(self.port).json("GET", "/api/modules")[0], 401)
        mods = self.login("S001", "Ready2026x").json("GET", "/api/modules")[1]["modules"]
        self.assertEqual(mods[0]["id"], "lexica")

    def test_a_student_stores_and_reads_back_only_their_own_records(self):
        a, b = self.login("S001", "Ready2026x"), self.login("S002", "Ready2026x")
        status, body = self.post(a, subject="chemistry", kind="own", payload={"score": 7, "of": 10})
        self.assertEqual(status, 201, body)
        self.post(b, subject="chemistry", kind="own", payload={"score": 9})
        mine = a.json("GET", "/api/records?subject=chemistry&kind=own")[1]["records"]
        self.assertEqual([r["payload"] for r in mine], [{"score": 7, "of": 10}])
        other_id = b.json("GET", "/api/records?subject=chemistry&kind=own")[1]["records"][0]["user_id"]
        again = a.json("GET", "/api/records?subject=chemistry&kind=own&user_id=%d" % other_id)[1]["records"]
        self.assertEqual([r["payload"] for r in again], [{"score": 7, "of": 10}])         # user_id 参数对学生无效，仍然只是自己的

    def test_the_teacher_sees_everyones_records_and_can_filter(self):
        a = self.login("S001", "Ready2026x")
        self.post(a, subject="chemistry", kind="all", payload={"n": 1})
        self.post(self.login("S002", "Ready2026x"), subject="chemistry", kind="all", payload={"n": 2})
        t = self.login("T001", "Teach3r!pw")
        records = t.json("GET", "/api/records?subject=chemistry&kind=all")[1]["records"]
        self.assertGreaterEqual(len({r["user_id"] for r in records}), 2)
        uid = records[0]["user_id"]
        only = t.json("GET", "/api/records?subject=chemistry&user_id=%d" % uid)[1]["records"]
        self.assertTrue(all(r["user_id"] == uid for r in only))

    def test_validation(self):
        a = self.login("S001", "Ready2026x")
        self.assertEqual(self.post(a, subject="nope", payload={})[1]["code"], "bad_subject")
        self.assertEqual(self.post(a, subject="physics", payload={})[1]["code"], "bad_subject")        # 登记了但还没启用
        self.assertEqual(self.post(a, subject="chemistry", payload=[1, 2])[1]["code"], "bad_payload")
        status, body = self.post(a, subject="chemistry", payload={"x": "y" * 30000})
        self.assertEqual((status, body["code"]), (413, "payload_too_large"))
        status, body = self.post(a, subject="chemistry", kind="a b/../c", payload={})
        self.assertEqual(status, 201)
        self.assertEqual(a.json("GET", "/api/records?subject=chemistry&limit=1")[1]["records"][0]["kind"], "ab..c")   # 空格和斜杠被清掉

    def test_anonymous_on_the_lan_entrance_uses_a_device_id_and_only_reads_its_own(self):
        c = Client(self.port)
        status, _ = c.json("POST", "/api/records", {"subject": "chemistry", "device": "dev-A", "payload": {"k": 1}}, headers=LAN)
        self.assertEqual(status, 201)
        c.json("POST", "/api/records", {"subject": "chemistry", "device": "dev-B", "payload": {"k": 2}}, headers=LAN)
        got = c.json("GET", "/api/records?subject=chemistry&device=dev-A", headers=LAN)[1]["records"]
        self.assertEqual([r["payload"] for r in got], [{"k": 1}])
        self.assertEqual(c.json("GET", "/api/records?subject=chemistry", headers=LAN)[1]["code"], "need_device")
        self.assertEqual(c.json("POST", "/api/records", {"subject": "chemistry", "payload": {}})[0], 401)      # 公网入口要登录

    def test_a_script_cannot_read_the_json_of_records_as_markup(self):
        a = self.login("S001", "Ready2026x")
        self.post(a, subject="chemistry", kind="xss", payload={"t": "<script>alert(1)</script>"})
        raw = a.request("GET", "/api/records?subject=chemistry&kind=xss&limit=1")[1]
        self.assertIn(b"application/json", a.last.getheader("Content-Type").encode())
        self.assertEqual(a.last.getheader("X-Content-Type-Options"), "nosniff")


if __name__ == "__main__":
    unittest.main()
