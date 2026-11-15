"""家庭版（WP_AUTH=guest）：不登录能用全部页面，管理功能要教师登录；账号由学生版核对。"""
from __future__ import annotations

import http.server
import json
import sys
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, ROOT.as_posix())

from server import auth as auth_mod                 # noqa: E402
from tests.test_auth import Client, HttpCase        # noqa: E402

WEB = ROOT / "web"


class FakeStudentEdition:
    """假的学生版：只实现 /api/auth/login，按学号返回事先设好的结果。"""

    def __init__(self):
        self.accounts = {}       # student_no -> (password, user dict)
        self.calls = []
        self.mode = "ok"         # ok | down | garbage
        outer = self

        class H(http.server.BaseHTTPRequestHandler):
            def do_POST(self):      # noqa: N802
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                outer.calls.append((self.path, body))
                if outer.mode == "garbage":
                    self._send(200, b"<html>not json</html>")
                    return
                entry = outer.accounts.get(body["student_no"])
                if entry and entry[0] == body["password"]:
                    self._send(200, json.dumps({"ok": True, "user": entry[1]}).encode())
                elif body["student_no"] == "LIMITED":
                    self._send(429, json.dumps({"ok": False, "code": "rate_limited", "error": "尝试太频繁了"}).encode())
                else:
                    self._send(401, json.dumps({"ok": False, "code": "invalid_credentials", "error": "学号或密码不对"}).encode())

            def _send(self, status, data):
                self.send_response(status)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *a):
                pass

        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.url = "http://127.0.0.1:%d/word-puzzle" % self.httpd.server_address[1]

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()


def teacher(no="T001", name="孙老师", role="admin", must_change=False):
    return {"id": 7, "student_no": no, "name": name, "class_name": "", "college": "", "department": "",
            "role": role, "must_change": must_change}


class GuestCase(HttpCase):
    remote = None

    @classmethod
    def setUpClass(cls):
        cls.remote = FakeStudentEdition()
        cls.remote.accounts = {"T001": ("Teach3r!pw", teacher()), "T002": ("Teach3r!pw", teacher("T002", "新老师", must_change=True)),
                               "S001": ("Ready2026x", teacher("S001", "学生", role="student"))}
        cls.auth_options = {"guest": True, "remote": cls.remote.url}
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.remote.stop()

    def setUp(self):
        self.remote.accounts = {"T001": ("Teach3r!pw", teacher()), "T002": ("Teach3r!pw", teacher("T002", "新老师", must_change=True)),
                                "S001": ("Ready2026x", teacher("S001", "学生", role="student"))}
        self.remote.mode = "ok"
        self.remote.calls.clear()

    def login(self, no="T001", pw="Teach3r!pw"):
        c = Client(self.port)
        status, body = c.json("POST", "/api/auth/login", {"student_no": no, "password": pw})
        return c, status, body


class TestAnonymous(GuestCase):
    def test_everything_a_visitor_needs_works_without_signing_in(self):
        c = Client(self.port)
        me = c.json("GET", "/api/auth/me")[1]
        self.assertEqual((me["auth_enabled"], me["guest_mode"], me["user"]), (True, True, None))
        for path in ("/api/banks", "/api/stats", "/api/scores", "/api/scores/summary", "/api/hierarchy"):
            status, _ = c.json("GET", path)
            self.assertIn(status, (200, 404), path)
        banks = c.json("GET", "/api/banks")[1]["banks"]
        self.assertGreater(len(banks), 0)                                  # 没标签的题库也看得到，和以前的家庭版一样
        self.assertEqual(c.json("GET", "/api/banks/%d" % banks[0]["id"])[0], 200)
        self.assertEqual(c.json("GET", "/api/scores/summary")[0], 200)

    def test_anonymous_can_record_a_score_by_device(self):
        c = Client(self.port)
        status, body = c.json("POST", "/api/scores", {"bank_title": "t", "score": 10, "matched": 1, "total_pairs": 1,
                                                       "wrong": 0, "best_combo": 1, "duration": 5, "level_count": 1,
                                                       "device": "dev-1", "detail": []})
        self.assertEqual(status, 201, body)

    def test_every_management_endpoint_asks_for_a_login_not_a_refusal(self):
        c = Client(self.port)
        for method, path in (("GET", "/api/admin/users"), ("GET", "/api/admin/visits"), ("GET", "/api/admin/logins"),
                             ("POST", "/api/materials"), ("GET", "/api/materials"), ("POST", "/api/banks")):
            status, body = c.json(method, path, {} if method == "POST" else None)
            self.assertEqual(status, 401, path)
            self.assertEqual(body["code"], "login_required", path)

    def test_tracking_works_for_visitors(self):
        c = Client(self.port)
        self.assertEqual(c.request("POST", "/api/track", {"event": "view", "vid": "v" * 16, "sid": "s" * 16, "path": "/"})[0], 204)
        row = self.app.Handler.db.one("SELECT user_id, role FROM page_views WHERE vid=?", ("v" * 16,))
        self.assertEqual((row["user_id"], row["role"]), (None, ""))


class TestRemoteLogin(GuestCase):
    def test_a_teacher_is_checked_by_the_student_edition_and_gets_management_rights(self):
        c, status, body = self.login()
        self.assertEqual(status, 200, body)
        self.assertEqual((body["user"]["role"], body["user"]["student_no"], body["user"]["name"]), ("admin", "T001", "孙老师"))
        self.assertEqual(self.remote.calls, [("/word-puzzle/api/auth/login", {"student_no": "T001", "password": "Teach3r!pw"})])
        self.assertEqual(c.json("GET", "/api/admin/users")[0], 200)
        self.assertEqual(c.json("GET", "/api/admin/visits")[0], 200)

    def test_wrong_password_is_the_student_editions_answer(self):
        c, status, body = self.login(pw="wrong-password")
        self.assertEqual((status, body["code"]), (401, "invalid_credentials"))
        self.assertEqual(c.json("GET", "/api/admin/users")[0], 401)

    def test_rate_limit_answer_is_passed_through(self):
        _, status, body = self.login("LIMITED", "x" * 9)
        self.assertEqual((status, body["code"]), (429, "rate_limited"))

    def test_students_are_not_let_into_management_even_with_a_valid_password(self):
        c, status, body = self.login("S001", "Ready2026x")
        self.assertEqual((status, body["code"]), (403, "teacher_only"))
        self.assertEqual(c.json("GET", "/api/admin/users")[0], 401)

    def test_a_teacher_who_must_still_change_the_initial_password_is_sent_to_the_student_edition(self):
        _, status, body = self.login("T002", "Teach3r!pw")
        self.assertEqual((status, body["code"]), (403, "remote_must_change"))

    def test_student_edition_down_or_garbage_gives_a_clear_error_and_no_session(self):
        self.remote.mode = "garbage"
        c, status, body = self.login()
        self.assertEqual(status, 502)
        self.remote.stop()
        try:
            c, status, body = self.login()
            self.assertEqual((status, body["code"]), (503, "remote_unreachable"))
            self.assertEqual(c.json("GET", "/api/admin/users")[0], 401)
            self.assertEqual(c.json("GET", "/api/banks")[0], 200)              # 其他功能照常
        finally:
            type(self).remote = FakeStudentEdition()
            self.svc.remote = self.remote.url

    def test_the_local_password_of_the_shadow_account_never_works(self):
        self.login()
        user = self.svc.get_by_student_no("T001")
        self.assertEqual(user["role"], "admin")
        for guess in ("Teach3r!pw", "", "changeme"):
            self.assertFalse(auth_mod.verify_password(guess, user["pw_hash"]))
        remote_off = self.svc.remote
        try:
            self.svc.remote = ""          # 就算远程核对被关掉，本地也进不去
            self.assertEqual(self.login()[1], 401)
        finally:
            self.svc.remote = remote_off

    def test_login_is_logged_and_password_change_is_refused_here(self):
        c, status, _ = self.login()
        self.assertEqual(status, 200)
        e = self.app.Handler.db.one("SELECT success, student_no FROM login_events ORDER BY id DESC LIMIT 1")
        self.assertEqual((e["success"], e["student_no"]), (1, "T001"))
        status, body = c.json("POST", "/api/auth/change-password", {"old_password": "a", "new_password": "b"})
        self.assertEqual((status, body["code"]), (400, "remote_password"))

    def test_a_second_login_updates_the_same_shadow_account(self):
        self.login()
        self.remote.accounts["T001"] = ("Teach3r!pw", teacher(name="孙老师改名"))
        self.login()
        rows = self.app.Handler.db.query("SELECT name FROM users WHERE student_no='T001'")
        self.assertEqual([r["name"] for r in rows], ["孙老师改名"])


class TestNoRemote(unittest.TestCase):
    def test_a_guest_edition_without_a_remote_url_does_not_invent_logins(self):
        from server.db import Database
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            svc = auth_mod.AuthService(Database(str(Path(tmp) / "a.db")), guest=True)
            with self.assertRaises(auth_mod.AuthError):
                svc.login("T001", "whatever1")


class TestInstaller(unittest.TestCase):
    INSTALL = (ROOT / "deploy" / "install.sh").read_text(encoding="utf-8")
    DEPLOY_ALL = next(ROOT.parent.glob("deploy-all-*.sh")).read_text(encoding="utf-8")

    def test_remote_is_optional_validated_and_written_into_the_unit(self):
        self.assertIn("WP_AUTH_REMOTE", self.INSTALL)
        self.assertIn("WP_AUTH=guest", self.INSTALL)
        self.assertIn("格式无效", self.INSTALL)
        import subprocess
        self.assertEqual(subprocess.run(["bash", "-n", str(ROOT / "deploy" / "install.sh")]).returncode, 0)

    def test_deploy_all_points_the_home_edition_at_the_student_edition(self):
        self.assertIn('WP_AUTH_REMOTE="$STUDENT_URL"', self.DEPLOY_ALL)
        self.assertIn("LEXICA_STUDENT_URL", self.DEPLOY_ALL)
        self.assertIn("http://192.168.1.100:8082/word-puzzle", self.DEPLOY_ALL)      # 走内网入口，不绕公网


class TestPages(unittest.TestCase):
    ui = (WEB / "js" / "auth-ui.js").read_text(encoding="utf-8")

    def test_guest_visitors_get_every_menu_and_a_teacher_sign_in(self):
        self.assertIn("function decorateGuest()", self.ui)
        self.assertIn("teacherSignIn", self.ui)
        self.assertIn("info.guest && !info.user", self.ui)

    def test_management_pages_send_a_visitor_to_the_login_page(self):
        self.assertIn("mode === 'admin' || mode === 'visits' || mode === 'change') { setRole(''); go('login.html', true)", self.ui)

    def test_the_login_page_explains_the_home_edition(self):
        html = (WEB / "login.html").read_text(encoding="utf-8")
        self.assertIn('id="guestHint"', html)
        self.assertIn("相同", html)


if __name__ == "__main__":
    unittest.main()
