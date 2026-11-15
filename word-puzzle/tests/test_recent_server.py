"""首页「最近玩过」按账号存在服务器上：换设备也看得到；只给现在还看得到的题库；没登录的访客改用本机记录。"""
from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, ROOT.as_posix())

from server.db import Database                    # noqa: E402
from tests.test_auth import Client, HttpCase      # noqa: E402

LAN = {"X-Wp-Entry": "lan"}


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(str(Path(self.tmp.name) / "r.db"))
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.db.close)

    def test_one_row_per_bank_newest_first_and_only_the_latest_eight_are_kept(self):
        for i in range(1, 13):
            self.db.touch_recent(1, i, 1000 + i)
        rows = self.db.recent_rows(1)
        self.assertEqual([r["bank_id"] for r in rows], [12, 11, 10, 9, 8, 7, 6, 5])
        self.db.touch_recent(1, 5, 5000)                                   # 再打开一次：只更新时间，提到最前
        rows = self.db.recent_rows(1)
        self.assertEqual((rows[0]["bank_id"], rows[0]["last_at"], len(rows)), (5, 5000, 8))
        self.assertEqual(self.db.one("SELECT opens FROM recent_banks WHERE user_id=1 AND bank_id=5")["opens"], 2)

    def test_accounts_are_separate(self):
        self.db.touch_recent(1, 3, 10)
        self.db.touch_recent(2, 4, 20)
        self.assertEqual([r["bank_id"] for r in self.db.recent_rows(1)], [3])
        self.assertEqual([r["bank_id"] for r in self.db.recent_rows(2)], [4])
        for i in range(20):
            self.db.touch_recent(2, 100 + i, 30 + i)
        self.assertEqual(len(self.db.recent_rows(1)), 1, "别人的记录不会把我的挤掉")

    def test_deleting_a_bank_forgets_it(self):
        bid = self.db.insert_bank({"title": "t", "level1": "a", "level2": "b", "level3": "c", "level4": "d", "source": "seed",
                                   "material_id": None, "unit_mode": "all", "unit_from": 0, "unit_to": 0, "pairs_per_level": 9,
                                   "owner_id": None}, [{"unit": "U", "en": "a", "cn": "甲"}])
        self.db.touch_recent(1, bid, 10)
        self.db.delete_bank(bid)
        self.assertEqual(self.db.recent_rows(1), [])


class RecentCase(HttpCase):
    counter = 0

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.svc.create_user("T001", "老师", password="Teach3r!pw", role="admin", must_change=False)
        cls.db = cls.app.Handler.db
        cls.admin = Client(cls.port)             # 老师登录一次就够了（登录有每分钟次数限制）
        assert cls.admin.json("POST", "/api/auth/login", {"student_no": "T001", "password": "Teach3r!pw"})[0] == 200

    def login(self, no, pw):
        c = Client(self.port)
        self.assertEqual(c.json("POST", "/api/auth/login", {"student_no": no, "password": pw})[0], 200)
        return c

    def student(self, tags=("甲",)):
        type(self).counter += 1
        no = "R%04d" % type(self).counter
        user, _ = self.svc.create_user(no, "学生" + no, password="Ready2026x", must_change=False)
        self.db.set_user_tags(user["id"], list(tags))
        return no, self.login(no, "Ready2026x")

    def bank(self, tag="甲", title="题库"):
        res = self.admin.json("POST", "/api/banks", {"source": "seed", "level1": "初中", "level2": "七年级", "level3": "上册",
                                                 "level4": "all", "unit_mode": "all", "title": title, "tags": tag})[1]
        return res["bank"]["id"]


class TestApi(RecentCase):
    def test_play_two_banks_and_the_newest_comes_first_on_any_device(self):
        no, phone = self.student()
        a, b = self.bank(title="A"), self.bank(title="B")
        for bid, delta in ((a, 0), (b, 5)):
            with mock.patch("time.time", return_value=time.time() + delta):
                self.assertEqual(phone.json("POST", "/api/recent", {"bank_id": bid})[0], 200)
        got = phone.json("GET", "/api/recent")[1]["recent"]
        self.assertEqual([x["bank"]["id"] for x in got], [b, a])
        self.assertGreater(got[0]["last_at"], got[1]["last_at"])
        laptop = self.login(no, "Ready2026x")                       # 另一台设备、另一个会话：同一个账号
        self.assertEqual([x["bank"]["id"] for x in laptop.json("GET", "/api/recent")[1]["recent"]], [b, a])

    def test_limit_and_dedupe(self):
        no, c = self.student()
        ids = [self.bank(title="L%d" % i) for i in range(6)]
        for i in ids:
            c.json("POST", "/api/recent", {"bank_id": i})
        c.json("POST", "/api/recent", {"bank_id": ids[0]})
        got = [x["bank"]["id"] for x in c.json("GET", "/api/recent")[1]["recent"]]
        self.assertEqual((len(got), got[0]), (4, ids[0]))                     # 默认 4 个，刚又玩过的在最前
        self.assertEqual(len(c.json("GET", "/api/recent?limit=8")[1]["recent"]), 6)
        self.assertEqual(len(c.json("GET", "/api/recent?limit=999")[1]["recent"]), 6)
        self.assertEqual(c.json("GET", "/api/recent?limit=abc")[0], 400)

    def test_banks_the_student_cannot_see_are_neither_stored_nor_listed(self):
        no, c = self.student(("甲",))
        mine, other = self.bank("甲", "甲班的"), self.bank("乙", "乙班的")
        self.assertEqual(c.json("POST", "/api/recent", {"bank_id": other})[0], 404)
        c.json("POST", "/api/recent", {"bank_id": mine})
        admin = self.admin
        admin.json("POST", "/api/banks/%d/meta" % mine, {"tags": "丙"})              # 老师收回
        self.assertEqual(c.json("GET", "/api/recent")[1]["recent"], [])
        admin.json("POST", "/api/banks/%d/meta" % mine, {"tags": "甲"})              # 又开放：记录还在
        self.assertEqual([x["bank"]["id"] for x in c.json("GET", "/api/recent")[1]["recent"]], [mine])

    def test_validation_and_isolation(self):
        no, c = self.student()
        for body in ({}, {"bank_id": "x"}, {"bank_id": None}):
            self.assertEqual(c.json("POST", "/api/recent", body)[0], 400)
        self.assertEqual(c.json("POST", "/api/recent", {"bank_id": 999999})[0], 404)
        bid = self.bank()
        c.json("POST", "/api/recent", {"bank_id": bid})
        other_no, other = self.student()
        self.assertEqual(other.json("GET", "/api/recent")[1]["recent"], [])           # 别人的记录看不到
        self.assertEqual(Client(self.port).json("GET", "/api/recent")[0], 401)           # 公网入口要登录

    def test_a_deleted_bank_disappears(self):
        no, c = self.student()
        bid = self.bank()
        c.json("POST", "/api/recent", {"bank_id": bid})
        self.admin.json("DELETE", "/api/banks/%d" % bid)
        self.assertEqual(c.json("GET", "/api/recent")[1]["recent"], [])
        self.assertIsNone(self.db.one("SELECT 1 FROM recent_banks WHERE bank_id=?", (bid,)))

    def test_anonymous_visitors_of_the_lan_entrance_are_told_to_use_this_device(self):
        with mock.patch.dict(os.environ, {"WP_LAN_GUEST": "1"}):
            bid = self.bank()
            anon = Client(self.port)
            res = anon.json("GET", "/api/recent", headers=LAN)
            self.assertEqual((res[0], res[1]["recent"], res[1]["device_only"]), (200, [], True))
            res = anon.json("POST", "/api/recent", {"bank_id": bid}, headers=LAN)
            self.assertEqual((res[0], res[1]["stored"]), (200, False))
            self.assertEqual(self.db.one("SELECT COUNT(*) n FROM recent_banks WHERE user_id IS NULL")["n"], 0)

    def test_the_teacher_has_a_list_too(self):
        admin = self.admin
        bid = self.bank(title="老师玩的")
        self.assertEqual(admin.json("POST", "/api/recent", {"bank_id": bid})[0], 200)
        self.assertIn(bid, [x["bank"]["id"] for x in admin.json("GET", "/api/recent")[1]["recent"]])


if __name__ == "__main__":
    unittest.main()
