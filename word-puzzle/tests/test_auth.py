"""家庭版 / 班级版登录：密码、会话、锁定、名单导入、权限隔离、导出，以及局域网版不受影响。"""
from __future__ import annotations

import http.client
import io
import json
import os
import re
import sqlite3
import sys
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path
from unittest import mock
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server import admin as admin_cli          # noqa: E402
from server import auth as auth_mod            # noqa: E402
from server import roster                       # noqa: E402
from server.db import Database                  # noqa: E402


class FakeClock:
    def __init__(self, t=1_700_000_000.0):
        self.t = t

    def __call__(self):
        return self.t


def make_xlsx(rows):
    """手搓一个最小的 xlsx（共享字符串 + 数字单元格），用来测试名单解析。"""
    strings, sheet_rows = [], []
    for r, row in enumerate(rows, start=1):
        cells = []
        for c, value in enumerate(row):
            ref = "%s%d" % ("ABCDEFGH"[c], r)
            if isinstance(value, (int, float)):
                cells.append('<c r="%s"><v>%s</v></c>' % (ref, value))
            else:
                strings.append(str(value))
                cells.append('<c r="%s" t="s"><v>%d</v></c>' % (ref, len(strings) - 1))
        sheet_rows.append('<row r="%d">%s</row>' % (r, "".join(cells)))
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("xl/worksheets/sheet1.xml", '<worksheet %s><sheetData>%s</sheetData></worksheet>' % (ns, "".join(sheet_rows)))
        z.writestr("xl/sharedStrings.xml", '<sst %s>%s</sst>' % (ns, "".join("<si><t>%s</t></si>" % s for s in strings)))
    return buf.getvalue()


class TestPasswords(unittest.TestCase):
    def test_scrypt_roundtrip_and_salting(self):
        a, b = auth_mod.hash_password("Abc12345"), auth_mod.hash_password("Abc12345")
        self.assertNotEqual(a, b, "同一个密码每次的哈希必须不同（随机盐）")
        self.assertTrue(auth_mod.verify_password("Abc12345", a))
        self.assertFalse(auth_mod.verify_password("abc12345", a))
        self.assertFalse(auth_mod.verify_password("x", "garbage"))
        self.assertTrue(a.startswith("scrypt$"))
        self.assertNotIn("Abc12345", a)

    def test_password_policy(self):
        bad = {"short1A": "至少", "2026001Abc": "学号", "aaaaaaaa1": "简单", "password": "常见",
               "abcdefgh": "两种", "12345678": "常见"}
        for pw, hint in bad.items():
            self.assertIn(hint, auth_mod.password_problem(pw, "2026001"), pw)
        self.assertEqual(auth_mod.password_problem("Tr0ub4dor!", "2026001"), "")
        self.assertIn("一样", auth_mod.password_problem("Tr0ub4dor!", "2026001", old="Tr0ub4dor!"))
        self.assertIn("太长", auth_mod.password_problem("Aa1" * 50, ""))

    def test_generated_initial_passwords_are_readable_and_varied(self):
        seen = {auth_mod.generate_initial_password() for _ in range(200)}
        self.assertGreater(len(seen), 190)
        for pw in seen:
            self.assertEqual(len(pw), 8)
            self.assertTrue(set(pw) <= set(auth_mod.INITIAL_ALPHABET))
            self.assertTrue(any(c.isdigit() for c in pw) and any(c.isalpha() for c in pw))
            self.assertFalse(set(pw) & set("il0o1"), "不要出现容易看错的字符")


class TestRateLimiter(unittest.TestCase):
    def test_sliding_window(self):
        clock = FakeClock()
        limiter = auth_mod.RateLimiter(3, 60, clock)
        self.assertEqual([limiter.allow("a") for _ in range(4)], [True, True, True, False])
        self.assertTrue(limiter.allow("b"), "不同的 key 互不影响")
        clock.t += 61
        self.assertTrue(limiter.allow("a"), "窗口过去后恢复")


class ServiceCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "a.db")
        self.clock = FakeClock()
        self.svc = auth_mod.AuthService(self.db, clock=self.clock)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def student(self, no="2026001", name="张三", **kw):
        user, plain = self.svc.create_user(no, name, **kw)
        return user, plain


class TestAccounts(ServiceCase):
    def test_create_validates_and_rejects_duplicates(self):
        self.student()
        with self.assertRaises(auth_mod.AuthError) as ctx:
            self.student()
        self.assertEqual(ctx.exception.code, "exists")
        for bad_no in ("", "has space", "x" * 40, "学号一"):
            with self.assertRaises(auth_mod.AuthError):
                self.svc.create_user(bad_no, "名字")
        with self.assertRaises(auth_mod.AuthError):
            self.svc.create_user("2026009", "  ")

    def test_new_accounts_must_change_the_password_and_nothing_is_stored_in_clear(self):
        user, plain = self.student()
        self.assertEqual(user["must_change"], 1)
        raw = sqlite3.connect(str(self.db.path))
        dump = "\n".join(raw.iterdump())
        raw.close()
        self.assertNotIn(plain, dump, "库里不能有明文密码")

    def test_login_success_and_the_same_message_for_every_failure(self):
        user, plain = self.student()
        got, token = self.svc.login("2026001", plain)
        self.assertEqual(got["id"], user["id"])
        self.assertEqual(self.svc.user_for_token(token)["student_no"], "2026001")
        messages = set()
        for no, pw in (("2026001", "wrong"), ("nobody", plain), ("2026001", "")):
            with self.assertRaises(auth_mod.AuthError) as ctx:
                self.svc.login(no, pw)
            messages.add((ctx.exception.status, ctx.exception.message)) if pw else messages.add(("missing", ctx.exception.code))
        self.assertIn((401, auth_mod.MESSAGE_BAD_LOGIN), messages)
        self.assertEqual(len([m for m in messages if m[0] == 401]), 1, "账号不存在和密码错误必须是同一种回答")

    def test_student_number_is_normalised(self):
        _, plain = self.student("2026001")
        self.svc.login(" ２０２６００１ ", plain)           # 全角数字 + 空格

    def test_lock_after_five_failures_then_unlock_by_time(self):
        _, plain = self.student()
        for _ in range(5):
            with self.assertRaises(auth_mod.AuthError):
                self.svc.login("2026001", "wrong")
            self.clock.t += 40                       # 避开单学号速率限制
        with self.assertRaises(auth_mod.AuthError):
            self.svc.login("2026001", plain)         # 锁定期间连正确密码也进不去
        self.clock.t += 16 * 60
        self.svc.login("2026001", plain)

    def test_admin_unlock_and_disable(self):
        user, plain = self.student()
        for _ in range(5):
            with self.assertRaises(auth_mod.AuthError):
                self.svc.login("2026001", "wrong")
            self.clock.t += 40
        self.svc.unlock(user["id"])
        _, token = self.svc.login("2026001", plain)
        self.svc.set_disabled(user["id"], True)
        self.assertIsNone(self.svc.user_for_token(token), "停用后已登录的会话立刻失效")
        with self.assertRaises(auth_mod.AuthError):
            self.svc.login("2026001", plain)

    def test_per_student_and_overall_rate_limits(self):
        self.student()
        codes = []
        for _ in range(12):
            try:
                self.svc.login("2026001", "wrong")
            except auth_mod.AuthError as exc:
                codes.append(exc.code)
            self.svc.unlock(self.svc.get_by_student_no("2026001")["id"])   # 排除账号锁定的干扰
        self.assertEqual(codes.count("rate_limited"), 2)

    def test_sessions_expire_and_logout(self):
        _, plain = self.student()
        _, token = self.svc.login("2026001", plain)
        self.svc.logout(token)
        self.assertIsNone(self.svc.user_for_token(token))
        _, token = self.svc.login("2026001", plain)
        self.clock.t += 15 * 86400
        self.assertIsNone(self.svc.user_for_token(token), "会话 14 天后过期")

    def test_only_the_token_hash_is_stored(self):
        _, plain = self.student()
        _, token = self.svc.login("2026001", plain)
        rows = self.db.query("SELECT token_hash FROM sessions")
        self.assertEqual(len(rows), 1)
        self.assertNotEqual(rows[0]["token_hash"], token)

    def test_change_password_rules_and_it_signs_out_other_devices(self):
        user, plain = self.student()
        _, phone = self.svc.login("2026001", plain)
        _, laptop = self.svc.login("2026001", plain)
        current = self.svc.get_by_id(user["id"])
        with self.assertRaises(auth_mod.AuthError) as ctx:
            self.svc.change_password(current, "wrong", "Tr0ub4dor!", phone)
        self.assertEqual(ctx.exception.code, "wrong_old_password")
        with self.assertRaises(auth_mod.AuthError) as ctx:
            self.svc.change_password(current, plain, "abc", phone)
        self.assertEqual(ctx.exception.code, "weak_password")
        fresh = self.svc.change_password(current, plain, "Tr0ub4dor!", phone)
        self.assertEqual(self.svc.get_by_id(user["id"])["must_change"], 0)
        self.assertIsNone(self.svc.user_for_token(phone))
        self.assertIsNone(self.svc.user_for_token(laptop))
        self.assertIsNotNone(self.svc.user_for_token(fresh))
        self.svc.login("2026001", "Tr0ub4dor!")
        with self.assertRaises(auth_mod.AuthError):
            self.svc.login("2026001", plain)

    def test_reset_password_forces_a_change_again(self):
        user, plain = self.student()
        self.svc.change_password(self.svc.get_by_id(user["id"]), plain, "Tr0ub4dor!", None)
        new = self.svc.reset_password(user["id"])
        self.assertEqual(self.svc.get_by_id(user["id"])["must_change"], 1)
        self.svc.login("2026001", new)


class TestRosterImport(ServiceCase):
    def rows(self, *items):
        return [dict({"_row": i + 2, "name": "", "class_name": "", "college": "", "department": "",
                      "password": ""}, student_no=no, **extra) for i, (no, extra) in enumerate(items)]

    def test_creates_accounts_with_random_initial_passwords(self):
        report = self.svc.import_roster(self.rows(
            ("2026001", {"name": "张三", "class_name": "一班", "college": "信息学院", "department": "计算机系"}),
            ("2026002", {"name": "李四", "class_name": "一班"})))
        self.assertEqual((report["created"], report["updated"], report["skipped"]), (2, 0, 0))
        creds = {c["student_no"]: c["password"] for c in report["credentials"]}
        self.assertEqual(len(set(creds.values())), 2)
        for no, pw in creds.items():
            user, _ = self.svc.login(no, pw)
            self.assertEqual(user["must_change"], 1)
        self.assertEqual(self.svc.get_by_student_no("2026001")["college"], "信息学院")

    def test_reimport_updates_profile_but_keeps_passwords(self):
        first = self.svc.import_roster(self.rows(("2026001", {"name": "张三", "class_name": "一班"})))
        again = self.svc.import_roster(self.rows(("2026001", {"name": "张三丰", "class_name": "二班"})))
        self.assertEqual((again["created"], again["updated"]), (0, 1))
        self.assertEqual(again["credentials"], [], "没有重置就不会再给出密码")
        self.assertEqual(self.svc.get_by_student_no("2026001")["class_name"], "二班")
        self.svc.login("2026001", first["credentials"][0]["password"])

    def test_reset_existing_issues_new_passwords(self):
        first = self.svc.import_roster(self.rows(("2026001", {"name": "张三"})))
        again = self.svc.import_roster(self.rows(("2026001", {"name": "张三"})), reset_existing=True)
        self.assertNotEqual(first["credentials"][0]["password"], again["credentials"][0]["password"])
        with self.assertRaises(auth_mod.AuthError):
            self.svc.login("2026001", first["credentials"][0]["password"])

    def test_bad_rows_are_reported_not_fatal(self):
        report = self.svc.import_roster(self.rows(
            ("", {"name": "没学号"}), ("2026001", {"name": "张三"}), ("2026001", {"name": "重复"}),
            ("2026003", {"name": ""}), ("bad no", {"name": "含空格"})))
        self.assertEqual(report["created"], 1)
        self.assertEqual(report["skipped"], 4)
        reasons = " | ".join(e["reason"] for e in report["errors"])
        for hint in ("学号为空", "重复", "姓名", "学号只能"):
            self.assertIn(hint, reasons)

    def test_import_never_touches_an_admin(self):
        self.svc.create_user("A001", "老师", password="Tr0ub4dor!", role="admin", must_change=False)
        report = self.svc.import_roster(self.rows(("A001", {"name": "被改名"})), reset_existing=True)
        self.assertEqual(self.svc.get_by_student_no("A001")["name"], "老师")
        self.assertEqual(report["credentials"], [])
        self.assertEqual(report["skipped"], 1)

    def test_a_given_initial_password_is_honoured_but_must_be_changed(self):
        report = self.svc.import_roster(self.rows(("2026001", {"name": "张三", "password": "Init2026"})))
        self.svc.login("2026001", "Init2026")
        self.assertEqual(self.svc.get_by_student_no("2026001")["must_change"], 1)
        self.assertEqual(report["credentials"][0]["password"], "Init2026")


class TestRosterParsing(unittest.TestCase):
    CSV = "学号,姓名,班级,学院,院系,手机号,用户名\n2026001,张三,一班,信息学院,计算机系,13800000000,zs\n2026002,李四,一班,,,,\n"

    def test_csv_utf8_with_bom_and_gbk(self):
        for data in (self.CSV.encode("utf-8-sig"), self.CSV.encode("gbk")):
            table = roster.parse_roster("名单.csv", data)
            self.assertEqual([r["name"] for r in table["rows"]], ["张三", "李四"])
            self.assertEqual(table["rows"][0]["department"], "计算机系")

    def test_phone_and_username_columns_are_dropped_and_reported(self):
        table = roster.parse_roster("a.csv", self.CSV.encode("utf-8"))
        self.assertEqual(sorted(table["ignored_columns"]), ["手机号", "用户名"])
        flat = json.dumps(table["rows"], ensure_ascii=False)
        self.assertNotIn("13800000000", flat)
        self.assertNotIn("zs", flat)

    def test_xlsx_with_numeric_student_numbers(self):
        data = make_xlsx([["学号", "姓名", "班级"], [2026001, "张三", "一班"], [2026002.0, "李四", "二班"]])
        table = roster.parse_roster("名单.xlsx", data)
        self.assertEqual([r["student_no"] for r in table["rows"]], ["2026001", "2026002"])
        self.assertEqual(table["rows"][1]["class_name"], "二班")

    def test_english_headers_and_blank_lines(self):
        table = roster.parse_roster("a.csv", b"student_no,name,class\n\n2026001,Tom,A\n,,\n")
        self.assertEqual(len(table["rows"]), 1)
        self.assertEqual(table["rows"][0]["class_name"], "A")

    def test_missing_required_columns_and_unsupported_files(self):
        with self.assertRaises(roster.RosterError):
            roster.parse_roster("a.csv", "姓名,班级\n张三,一班\n".encode())
        with self.assertRaises(roster.RosterError):
            roster.parse_roster("a.xls", b"\xd0\xcf\x11\xe0")
        with self.assertRaises(roster.RosterError):
            roster.parse_roster("a.csv", b"")
        with self.assertRaises(roster.RosterError):
            roster.parse_roster("a.xlsx", b"PK-not-a-zip")


# ---------------------------------------------------------------- HTTP

class Client:
    def __init__(self, port):
        self.port, self.cookie, self.last = port, "", None

    def request(self, method, path, body=None, headers=None, raw=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=15)
        path = quote(path, safe="/?=&%:")          # 测试里直接写中文，这里统一转成百分号编码
        headers = dict(headers or {})
        if self.cookie:
            headers["Cookie"] = self.cookie
        data = raw
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        try:
            conn.request(method, path, body=data, headers=headers)
            resp = conn.getresponse()
            payload = resp.read()
            self.last = resp
            set_cookie = resp.getheader("Set-Cookie")
            if set_cookie:
                pair = set_cookie.split(";", 1)[0]
                self.cookie = "" if pair.endswith("=") else pair
            return resp.status, payload
        finally:
            conn.close()

    def json(self, method, path, body=None, **kw):
        status, payload = self.request(method, path, body, **kw)
        return status, (json.loads(payload) if payload[:1] in (b"{", b"[") else payload)


def multipart(fields, files):
    boundary = "----wpTest"
    out = b""
    for k, v in fields.items():
        out += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (boundary, k, v)).encode()
    for k, (name, data) in files.items():
        out += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\n"
                "Content-Type: application/octet-stream\r\n\r\n" % (boundary, k, name)).encode() + data + b"\r\n"
    out += ("--%s--\r\n" % boundary).encode()
    return out, {"Content-Type": "multipart/form-data; boundary=" + boundary}


class HttpCase(unittest.TestCase):
    auth_options = {}

    @classmethod
    def setUpClass(cls):
        from server import app as app_mod
        cls.app = app_mod
        cls.tmp = tempfile.TemporaryDirectory()
        cls.clock = FakeClock(__import__("time").time())
        if cls.auth_options is False:
            options = False
        else:
            options = dict(cls.auth_options)
            options.setdefault("clock", cls.clock)
        cls.httpd = app_mod.build_server("127.0.0.1", 0, str(Path(cls.tmp.name) / "h.db"), auth=options)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        cls.thread.start()
        cls.svc = app_mod.Handler.auth

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=5)
        cls.app.Handler.db.close()
        cls.app.Handler.auth = None
        cls.tmp.cleanup()


class TestHttpAuth(HttpCase):
    counter = 0

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.svc.create_user("T001", "老师", password="Teach3r!pw", role="admin", must_change=False)

    def make_student(self, no=None, name="学生", password="Init2026", must_change=True, **kw):
        type(self).counter += 1
        no = no or "S%04d" % type(self).counter
        self.svc.create_user(no, name, password=password, must_change=must_change, **kw)
        return no

    def login(self, no, password):
        c = Client(self.port)
        status, body = c.json("POST", "/api/auth/login", {"student_no": no, "password": password})
        return c, status, body

    def ready_student(self, **kw):
        """已经改过初始密码、可以正常使用的学生。"""
        no = self.make_student(must_change=False, password="Ready2026x", **kw)
        c, status, _ = self.login(no, "Ready2026x")
        self.assertEqual(status, 200)
        return no, c

    def admin(self):
        c, status, _ = self.login("T001", "Teach3r!pw")
        self.assertEqual(status, 200)
        return c

    # ---- 匿名 ----

    def test_anonymous_can_only_see_static_pages_health_and_login(self):
        c = Client(self.port)
        self.assertEqual(c.request("GET", "/")[0], 200)
        self.assertEqual(c.request("GET", "/api/health")[0], 200)
        status, body = c.json("GET", "/api/auth/me")
        self.assertEqual((status, body["auth_enabled"], body["user"]), (200, True, None))
        for path in ("/api/banks", "/api/meta", "/api/scores", "/api/stats", "/api/units?level1=a",
                     "/api/audio/apple", "/api/materials", "/api/offline", "/api/admin/users"):
            status, body = c.json("GET", path)
            self.assertEqual(status, 401, path)
            self.assertEqual(body["code"], "login_required", path)
        for method, path in (("POST", "/api/banks"), ("POST", "/api/scores"), ("DELETE", "/api/banks/1")):
            self.assertEqual(c.json(method, path, {})[0], 401, path)

    def test_responses_carry_security_headers_and_are_not_cached(self):
        c = Client(self.port)
        c.request("GET", "/api/auth/me")
        self.assertEqual(c.last.getheader("Cache-Control"), "no-store")
        self.assertEqual(c.last.getheader("X-Frame-Options"), "DENY")
        self.assertEqual(c.last.getheader("Referrer-Policy"), "same-origin")

    # ---- 登录 / 强制改密码 ----

    def test_login_cookie_flags(self):
        no = self.make_student()
        c, status, body = self.login(no, "Init2026")
        self.assertEqual(status, 200)
        self.assertTrue(body["user"]["must_change"])
        cookie = c.last.getheader("Set-Cookie")
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Lax", cookie)
        self.assertIn("Path=/", cookie)
        self.assertNotIn("Secure", cookie, "本测试没有打开 cookie_secure")

    def test_wrong_credentials_and_foreign_origin(self):
        no = self.make_student()
        c = Client(self.port)
        status, body = c.json("POST", "/api/auth/login", {"student_no": no, "password": "nope"})
        self.assertEqual((status, body["code"]), (401, "invalid_credentials"))
        self.assertEqual(c.cookie, "")
        status, _ = c.json("POST", "/api/auth/login", {"student_no": no, "password": "Init2026"},
                           headers={"Origin": "http://evil.example"})
        self.assertEqual(status, 403, "跨站的登录请求要被拒绝")

    def test_initial_password_must_be_changed_before_anything_else(self):
        no = self.make_student()
        c, _, _ = self.login(no, "Init2026")
        status, body = c.json("GET", "/api/banks")
        self.assertEqual((status, body["code"]), (403, "password_change_required"))
        self.assertEqual(c.json("GET", "/api/auth/me")[1]["user"]["student_no"], no)
        self.assertEqual(c.json("POST", "/api/scores", {"score": 1})[0], 403)
        status, body = c.json("POST", "/api/auth/change-password",
                              {"old_password": "Init2026", "new_password": "short"})
        self.assertEqual((status, body["code"]), (400, "weak_password"))
        old_cookie = c.cookie
        status, body = c.json("POST", "/api/auth/change-password",
                              {"old_password": "Init2026", "new_password": "Brand-new-2026"})
        self.assertEqual(status, 200)
        self.assertFalse(body["user"]["must_change"])
        self.assertNotEqual(c.cookie, old_cookie, "改完密码要换新的会话令牌")
        self.assertEqual(c.json("GET", "/api/banks")[0], 200)
        stale = Client(self.port)
        stale.cookie = old_cookie
        self.assertEqual(stale.json("GET", "/api/banks")[0], 401, "旧令牌必须失效")

    def test_logout_ends_the_session(self):
        _, c = self.ready_student()
        self.assertEqual(c.json("GET", "/api/banks")[0], 200)
        cookie = c.cookie
        self.assertEqual(c.json("POST", "/api/auth/logout", {})[0], 200)
        stale = Client(self.port)
        stale.cookie = cookie
        self.assertEqual(stale.json("GET", "/api/banks")[0], 401)

    def test_lockout_over_http_and_admin_unlock(self):
        no = self.make_student(must_change=False, password="Ready2026x")
        c = Client(self.port)
        for _ in range(5):
            self.assertEqual(c.json("POST", "/api/auth/login", {"student_no": no, "password": "bad"})[0], 401)
            type(self).clock.t += 40
        self.assertEqual(c.json("POST", "/api/auth/login", {"student_no": no, "password": "Ready2026x"})[0], 401)
        admin = self.admin()
        uid = self.svc.get_by_student_no(no)["id"]
        self.assertEqual(admin.json("POST", "/api/admin/users/%d/unlock" % uid, {})[0], 200)
        self.assertEqual(c.json("POST", "/api/auth/login", {"student_no": no, "password": "Ready2026x"})[0], 200)

    # ---- 学生与管理员的权限 ----

    def test_students_cannot_use_admin_features(self):
        _, c = self.ready_student()
        for method, path in (("GET", "/api/materials"), ("GET", "/api/offline"), ("GET", "/api/admin/users"),
                             ("POST", "/api/admin/import"), ("GET", "/api/admin/export/scores.csv"),
                             ("POST", "/api/banks/1/offline"), ("DELETE", "/api/materials/1")):
            status, body = c.json(method, path, {} if method == "POST" else None)
            self.assertEqual((status, body["code"]), (403, "forbidden"), path)
        status, body = c.json("POST", "/api/banks", {"source": "material", "material_id": 1})
        self.assertEqual(status, 403)

    def test_bank_ownership(self):
        _, alice = self.ready_student(name="甲")
        _, bob = self.ready_student(name="乙")
        admin = self.admin()
        spec = {"source": "seed", "level1": "初中", "level2": "九年级", "level3": "上册",
                "level4": "all", "unit_mode": "all"}
        status, body = alice.json("POST", "/api/banks", spec)
        self.assertEqual(status, 201)
        bid = body["bank"]["id"]
        ids = lambda cl: {b["id"] for b in cl.json("GET", "/api/banks")[1]["banks"]}
        self.assertIn(bid, ids(alice))
        self.assertNotIn(bid, ids(bob), "别人的题库不能出现在我的列表里")
        self.assertIn(bid, ids(admin))
        self.assertEqual(bob.json("GET", "/api/banks/%d" % bid)[0], 404)
        self.assertEqual(bob.json("DELETE", "/api/banks/%d" % bid)[0], 404)
        self.assertEqual(alice.json("GET", "/api/banks/%d" % bid)[0], 200)
        # 系统题库：所有人可见、可玩，但学生删不掉
        system = [b for b in admin.json("GET", "/api/banks")[1]["banks"] if b["owner_id"] is None][0]["id"]
        self.assertIn(system, ids(bob))
        self.assertEqual(bob.json("GET", "/api/banks/%d" % system)[0], 200)
        self.assertEqual(bob.json("DELETE", "/api/banks/%d" % system)[0], 403)
        self.assertEqual(alice.json("DELETE", "/api/banks/%d" % bid)[0], 200)

    def test_scores_are_tied_to_the_login_and_private(self):
        no1, alice = self.ready_student(name="甲", class_name="一班")
        no2, bob = self.ready_student(name="乙", class_name="二班")
        admin = self.admin()
        score = {"score": 777, "matched": 3, "total_pairs": 3, "bank_title": "t",
                 "device": "spoofed", "nickname": "冒充者", "user_id": 1}
        self.assertEqual(alice.json("POST", "/api/scores", score)[0], 201)
        self.assertEqual(bob.json("POST", "/api/scores", dict(score, score=111))[0], 201)
        mine = alice.json("GET", "/api/scores")[1]
        self.assertEqual([s["score"] for s in mine["scores"]], [777])
        self.assertEqual(mine["scores"][0]["nickname"], "甲", "昵称以登录信息为准")
        self.assertNotEqual(mine["scores"][0]["device"], "spoofed")
        self.assertEqual(mine["stats"]["count"], 1)
        self.assertEqual(alice.json("GET", "/api/stats")[1]["best"], 777)
        everyone = {s["score"] for s in admin.json("GET", "/api/scores?limit=500")[1]["scores"]}
        self.assertTrue({777, 111} <= everyone)

    # ---- 管理员功能 ----

    def test_admin_imports_a_roster_over_http_and_gets_credentials_once(self):
        admin = self.admin()
        csv_data = ("学号,姓名,班级,学院,院系,手机号\nH001,王一,甲班,理学院,物理系,13900000000\n"
                    "H002,王二,甲班,理学院,物理系,\nH001,重复,甲班,,,\n").encode()
        body, headers = multipart({}, {"file": ("名单.csv", csv_data)})
        status, report = admin.json("POST", "/api/admin/import", raw=body, headers=headers)
        self.assertEqual(status, 200)
        self.assertEqual((report["created"], report["skipped"]), (2, 1))
        self.assertEqual(report["ignored_columns"], ["手机号"])
        creds = {c["student_no"]: c["password"] for c in report["credentials"]}
        c, status, login = self.login("H001", creds["H001"])
        self.assertEqual(status, 200)
        self.assertTrue(login["user"]["must_change"])
        users = admin.json("GET", "/api/admin/users?class_name=甲班")[1]["users"]
        self.assertEqual({u["student_no"] for u in users}, {"H001", "H002"})
        self.assertNotIn("pw_hash", json.dumps(users), "接口永远不返回密码哈希")
        self.assertEqual(len(admin.json("GET", "/api/admin/users?q=王二")[1]["users"]), 1)
        self.assertEqual(admin.json("GET", "/api/admin/users?college=没有这个学院")[1]["users"], [])

    def test_import_rejects_non_multipart_and_garbage(self):
        admin = self.admin()
        self.assertEqual(admin.json("POST", "/api/admin/import", {"x": 1})[0], 400)
        body, headers = multipart({}, {"file": ("a.csv", "姓名\n张三\n".encode())})
        status, resp = admin.json("POST", "/api/admin/import", raw=body, headers=headers)
        self.assertEqual(status, 400)
        self.assertIn("学号", resp["error"])

    def test_admin_reset_disable_and_not_disabling_oneself(self):
        no, c = self.ready_student()
        admin = self.admin()
        uid = self.svc.get_by_student_no(no)["id"]
        status, body = admin.json("POST", "/api/admin/users/%d/reset-password" % uid, {})
        self.assertEqual(status, 200)
        self.assertEqual(c.json("GET", "/api/banks")[0], 401, "重置密码会让对方所有设备下线")
        c2, status, login = self.login(no, body["password"])
        self.assertEqual(status, 200)
        self.assertTrue(login["user"]["must_change"])
        self.assertEqual(admin.json("POST", "/api/admin/users/%d/disabled" % uid, {"disabled": True})[0], 200)
        self.assertEqual(self.login(no, body["password"])[1], 401)
        self.assertEqual(admin.json("POST", "/api/admin/users/%d/disabled" % uid, {"disabled": False})[0], 200)
        self.assertEqual(self.login(no, body["password"])[1], 200)
        me = self.svc.get_by_student_no("T001")["id"]
        self.assertEqual(admin.json("POST", "/api/admin/users/%d/disabled" % me, {"disabled": True})[0], 400)
        self.assertEqual(admin.json("POST", "/api/admin/users/99999/unlock", {})[0], 404)

    def test_score_export_csv_filters_and_is_safe_for_excel(self):
        no, c = self.ready_student(name="=SUM(A1)", class_name="导出班", college="导出学院")
        other, c2 = self.ready_student(name="别班", class_name="别的班")
        c.json("POST", "/api/scores", {"score": 500, "matched": 3, "total_pairs": 3, "bank_title": "题库A"})
        c2.json("POST", "/api/scores", {"score": 900, "matched": 3, "total_pairs": 3, "bank_title": "题库B"})
        admin = self.admin()
        status, data = admin.request("GET", "/api/admin/export/scores.csv?class_name=导出班")
        self.assertEqual(status, 200)
        self.assertTrue(data.startswith("﻿".encode("utf-8")), "要有 BOM，Excel 才不会乱码")
        text = data.decode("utf-8-sig")
        self.assertIn("学号,姓名,班级,学院,院系,题库,得分", text)
        self.assertIn("题库A", text)
        self.assertNotIn("题库B", text, "按班级筛选")
        self.assertIn("'=SUM(A1)", text, "以 = 开头的内容要加单引号，避免被当成公式")
        self.assertIn("attachment", admin.last.getheader("Content-Disposition"))

    def test_admin_page_data_includes_game_stats(self):
        no, c = self.ready_student(class_name="统计班")
        c.json("POST", "/api/scores", {"score": 321, "matched": 1, "total_pairs": 1})
        users = self.admin().json("GET", "/api/admin/users?class_name=统计班")[1]["users"]
        self.assertEqual((users[0]["games"], users[0]["best"]), (1, 321))


class TestSecureCookie(HttpCase):
    auth_options = {"cookie_secure": True, "session_days": 1}

    def test_secure_flag_and_session_length(self):
        self.svc.create_user("C001", "安全", password="Ready2026x", must_change=False)
        c = Client(self.port)
        c.json("POST", "/api/auth/login", {"student_no": "C001", "password": "Ready2026x"})
        cookie = c.last.getheader("Set-Cookie")
        self.assertIn("Secure", cookie)
        self.assertIn("Max-Age=86400", cookie)
        c.json("POST", "/api/auth/logout", {})
        cleared = c.last.getheader("Set-Cookie")
        self.assertIn("Max-Age=0", cleared)
        self.assertIn("Secure", cleared)


class TestLanEditionIsUnchanged(HttpCase):
    auth_options = False

    def test_no_login_needed_and_no_account_endpoints(self):
        c = Client(self.port)
        status, body = c.json("GET", "/api/auth/me")
        self.assertEqual((status, body["auth_enabled"], body["user"]), (200, False, None))
        self.assertEqual(c.json("GET", "/api/banks")[0], 200)
        self.assertEqual(c.json("GET", "/api/materials")[0], 200)
        self.assertEqual(c.json("POST", "/api/scores", {"score": 5, "bank_title": "lan"})[0], 201)
        self.assertEqual(c.json("POST", "/api/auth/login", {"student_no": "a", "password": "b"})[0], 404)
        self.assertEqual(c.json("GET", "/api/admin/users")[0], 404)
        self.assertIsNone(c.last.getheader("Set-Cookie"))
        self.assertNotEqual(c.last.getheader("Cache-Control"), "no-store", "局域网版的响应头保持原样")


class TestAdminCli(unittest.TestCase):
    def run_cli(self, db, *args):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch("sys.stdout", out), mock.patch("sys.stderr", err):
            code = admin_cli.main(["--db", db, *args])
        return code, out.getvalue(), err.getvalue()

    def test_create_admin_import_reset_and_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / "c.db")
            code, out, _ = self.run_cli(db, "create-admin", "A001", "--name", "老师", "--password", "Tr0ub4dor!")
            self.assertEqual(code, 0, out)
            code, _, err = self.run_cli(db, "create-admin", "A002", "--name", "弱", "--password", "123")
            self.assertEqual(code, 1)
            self.assertIn("至少", err)
            roster_file = Path(tmp) / "名单.csv"
            roster_file.write_text("学号,姓名,班级,手机号\n2026001,张三,一班,13800000000\n,无学号,一班,\n", encoding="utf-8-sig")
            creds = Path(tmp) / "creds.csv"
            code, out, _ = self.run_cli(db, "import", str(roster_file), "--out", str(creds))
            self.assertEqual(code, 2, "有错误的行时退出码为 2")
            self.assertIn("手机号", out)
            self.assertIn("新建 1", out)
            rows = creds.read_text(encoding="utf-8-sig").splitlines()
            self.assertEqual(rows[0], "学号,姓名,班级,初始密码")
            self.assertTrue(rows[1].startswith("2026001,张三,一班,"))
            self.assertEqual(oct(creds.stat().st_mode & 0o777), "0o600")
            self.assertNotIn("13800000000", creds.read_text(encoding="utf-8-sig"))
            hostile = Path(tmp) / "恶意.csv"
            hostile.write_text("学号,姓名\n2026009,=HYPERLINK(\"http://evil.example\")\n", encoding="utf-8")
            creds2 = Path(tmp) / "creds2.csv"
            self.run_cli(db, "import", str(hostile), "--out", str(creds2))
            self.assertIn("'=HYPERLINK", creds2.read_text(encoding="utf-8-sig"),
                          "初始密码清单里的姓名不能以 = 开头，否则 Excel 会把它当公式")
            code, out, _ = self.run_cli(db, "reset-password", "2026001")
            self.assertIn("新的初始密码", out)
            code, out, _ = self.run_cli(db, "list")
            self.assertIn("A001", out)
            self.assertIn("[管理员]", out)
            self.assertIn("[待改密码]", out)
            code, _, err = self.run_cli(db, "unlock", "nobody")
            self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
