"""内网入口（家庭版）：不登录就能做题并留下记录，点到管理功能才要老师登录；公网入口一律要登录。
同一个后端、同一个数据库、同一套账号。"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, ROOT.as_posix())

from tests.test_auth import Client, HttpCase        # noqa: E402

WEB = ROOT / "web"
LAN = {"X-Wp-Entry": "lan"}
SCORE = {"bank_title": "t", "score": 10, "matched": 1, "total_pairs": 1, "wrong": 0, "best_combo": 1,
         "duration": 5, "level_count": 1, "device": "dev-1", "detail": []}


class GuestCase(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.svc.create_user("T001", "老师", password="Teach3r!pw", role="admin", must_change=False)
        user, _ = cls.svc.create_user("S001", "学生", password="Ready2026x", must_change=False, class_name="一班")
        cls.student_id = user["id"]

    def setUp(self):
        patcher = mock.patch.dict(os.environ, {"WP_LAN_GUEST": "1"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def get(self, path, headers=None, c=None):
        return (c or Client(self.port)).json("GET", path, headers=headers)

    def login(self, no, pw, headers=None):
        c = Client(self.port)
        status, body = c.json("POST", "/api/auth/login", {"student_no": no, "password": pw}, headers=headers)
        return c, status, body


class TestAnonymousOnTheLanEntrance(GuestCase):
    def test_me_says_guest_only_through_the_lan_entrance(self):
        me = self.get("/api/auth/me", LAN)[1]
        self.assertEqual((me["auth_enabled"], me["guest_mode"], me["user"]), (True, True, None))
        self.assertFalse(self.get("/api/auth/me")[1]["guest_mode"])

    def test_the_public_entrance_still_requires_a_login_for_everything(self):
        for path in ("/api/banks", "/api/scores", "/api/stats", "/api/scores/summary"):
            self.assertEqual(self.get(path)[0], 401, path)
            self.assertEqual(self.get(path, {"X-Wp-Entry": "wan"})[0], 401, path)

    def test_switch_off_means_the_marker_is_ignored(self):
        with mock.patch.dict(os.environ, {"WP_LAN_GUEST": "0"}):
            self.assertEqual(self.get("/api/banks", LAN)[0], 401)
        with mock.patch.dict(os.environ):
            os.environ.pop("WP_LAN_GUEST", None)
            self.assertEqual(self.get("/api/banks", LAN)[0], 401)

    def test_everything_a_visitor_needs_works_without_signing_in(self):
        c = Client(self.port)
        banks = c.json("GET", "/api/banks", headers=LAN)[1]["banks"]
        self.assertGreater(len(banks), 0)                                  # 没标签的题库也看得到，和以前的家庭版一样
        self.assertEqual(c.json("GET", "/api/banks/%d" % banks[0]["id"], headers=LAN)[0], 200)
        for path in ("/api/stats", "/api/scores", "/api/scores/summary"):
            self.assertEqual(c.json("GET", path, headers=LAN)[0], 200, path)

    def test_anonymous_scores_are_kept_by_device(self):
        c = Client(self.port)
        status, body = c.json("POST", "/api/scores", SCORE, headers=LAN)
        self.assertEqual(status, 201, body)
        rows = c.json("GET", "/api/scores/summary", headers=LAN)[1]["rows"]
        self.assertTrue(any(r["user_id"] is None and r["device"] == "dev-1" for r in rows))

    def test_every_management_endpoint_asks_for_a_login(self):
        c = Client(self.port)
        for method, path in (("GET", "/api/admin/users"), ("GET", "/api/admin/visits"), ("GET", "/api/admin/logins"),
                             ("POST", "/api/materials"), ("GET", "/api/materials"), ("POST", "/api/banks")):
            status, body = c.json(method, path, {} if method == "POST" else None, headers=LAN)
            self.assertEqual((status, body["code"]), (401, "login_required"), path)

    def test_visits_and_logins_are_recorded(self):
        c = Client(self.port)
        self.assertEqual(c.request("POST", "/api/track", {"event": "view", "vid": "g" * 16, "sid": "h" * 16, "path": "/"},
                                   headers=LAN)[0], 204)
        row = self.app.Handler.db.one("SELECT user_id, role FROM page_views WHERE vid=?", ("g" * 16,))
        self.assertEqual((row["user_id"], row["role"]), (None, ""))
        self.login("T001", "wrong-pass-1", LAN)
        e = self.app.Handler.db.one("SELECT success, student_no FROM login_events ORDER BY id DESC LIMIT 1")
        self.assertEqual((e["success"], e["student_no"]), (0, "T001"))


class TestLoginOnTheLanEntrance(GuestCase):
    def test_a_teacher_logs_in_with_the_same_account_and_gets_management(self):
        c, status, body = self.login("T001", "Teach3r!pw", LAN)
        self.assertEqual((status, body["user"]["role"]), (200, "admin"))
        self.assertEqual(c.json("GET", "/api/admin/users", headers=LAN)[0], 200)
        self.assertEqual(c.json("GET", "/api/admin/visits", headers=LAN)[0], 200)

    def test_a_logged_in_student_is_a_student_not_a_guest(self):
        c, status, _ = self.login("S001", "Ready2026x", LAN)
        self.assertEqual(status, 200)
        self.assertEqual(c.json("GET", "/api/admin/users", headers=LAN)[0], 403)
        self.assertEqual(c.json("GET", "/api/banks", headers=LAN)[1]["banks"], [])          # 没有标签 = 看不到，规则不变

    def test_a_login_made_on_the_lan_entrance_does_not_work_for_the_public_one_without_the_cookie(self):
        _, status, _ = self.login("T001", "wrong-pass-1")
        self.assertEqual(status, 401)


class TestPeerCheck(unittest.TestCase):
    def test_the_marker_from_a_non_local_peer_is_ignored(self):
        from server import app as app_mod
        auth = object()
        for peer, expected in (("127.0.0.1", True), ("::1", True), ("192.168.1.7", False), ("203.0.113.5", False)):
            h = app_mod.Handler.__new__(app_mod.Handler)
            h.client_address = (peer, 5555)
            h.headers = {"X-Wp-Entry": "lan"}
            with mock.patch.object(app_mod.Handler, "auth", auth), mock.patch.dict(os.environ, {"WP_LAN_GUEST": "1"}):
                self.assertEqual(h._guest_entrance(), expected, peer)


class TestPages(unittest.TestCase):
    ui = (WEB / "js" / "auth-ui.js").read_text(encoding="utf-8")

    def test_guest_visitors_get_every_menu_and_a_teacher_sign_in(self):
        self.assertIn("function decorateGuest()", self.ui)
        self.assertIn("teacherSignIn", self.ui)
        self.assertIn("info.guest && !info.user", self.ui)

    def test_management_pages_send_a_visitor_to_the_login_page(self):
        self.assertIn("mode === 'admin' || mode === 'visits' || mode === 'super' || mode === 'change') { setRole(''); go('login.html', true)", self.ui)

    def test_the_login_page_explains_the_home_edition(self):
        html = (WEB / "login.html").read_text(encoding="utf-8")
        self.assertIn('id="guestHint"', html)


if __name__ == "__main__":
    unittest.main()
