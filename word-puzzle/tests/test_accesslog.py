"""访问记录：谁、IP、设备、浏览器、页面、停留；登录成功和失败；老师页面与导出；转发头不可伪造。"""
from __future__ import annotations

import csv
import http.server
import io
import json
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, ROOT.as_posix())

from server import accesslog                      # noqa: E402
from server.db import Database                    # noqa: E402
from tests.test_auth import Client, HttpCase      # noqa: E402

WEB = ROOT / "web"
FAMILY = ROOT / "deploy" / "family"
NGINX = shutil.which("nginx")

UA_CHROME_WIN = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
UA_IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
UA_WECHAT = ("Mozilla/5.0 (Linux; Android 13; SM-S918B Build/TP1A.220624.014; wv) AppleWebKit/537.36 (KHTML, like Gecko) "
             "Version/4.0 Chrome/116.0.0.0 Mobile Safari/537.36 XWEB/1160065 MicroMessenger/8.0.44.2502(0x28002C3B) WeChat/arm64 Weixin NetType/WIFI")


class TestUserAgent(unittest.TestCase):
    def test_desktop_chrome(self):
        r = accesslog.parse_user_agent(UA_CHROME_WIN)
        self.assertEqual((r["browser"], r["browser_version"], r["os"], r["device_type"]), ("Chrome", "130.0.0.0", "Windows", "desktop"))

    def test_edge_is_not_reported_as_chrome(self):
        ua = UA_CHROME_WIN + " Edg/130.0.2849.68"
        self.assertEqual(accesslog.parse_user_agent(ua)["browser"], "Edge")

    def test_iphone_safari(self):
        r = accesslog.parse_user_agent(UA_IPHONE)
        self.assertEqual((r["browser"], r["os"], r["os_version"], r["device_type"], r["device_model"]),
                         ("Safari", "iOS", "17.2", "mobile", "iPhone"))

    def test_wechat_on_android_gives_model_and_the_in_app_browser(self):
        r = accesslog.parse_user_agent(UA_WECHAT)
        self.assertEqual((r["os"], r["os_version"], r["device_model"], r["device_type"]), ("Android", "13", "SM-S918B", "mobile"))
        self.assertTrue(r["in_app"].startswith("WeChat 8.0.44"))

    def test_ipad_and_tablets(self):
        ua = "Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/119.0.6045.169 Mobile/15E148 Safari/604.1"
        r = accesslog.parse_user_agent(ua)
        self.assertEqual((r["os"], r["device_type"], r["browser"]), ("iPadOS", "tablet", "Chrome"))
        r = accesslog.parse_user_agent("Mozilla/5.0 (Linux; Android 12; SM-X700) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36")
        self.assertEqual(r["device_type"], "tablet")

    def test_scripts_are_marked_as_bots_and_empty_is_safe(self):
        self.assertEqual(accesslog.parse_user_agent("curl/8.4.0")["device_type"], "bot")
        self.assertEqual(accesslog.parse_user_agent("")["browser"], "")
        self.assertEqual(accesslog.parse_user_agent(None)["device_type"], "")

    def test_names_are_language_neutral(self):
        for ua in (UA_CHROME_WIN, UA_IPHONE, UA_WECHAT):
            for value in accesslog.parse_user_agent(ua).values():
                self.assertTrue(value.isascii(), value)


class _Headers(dict):
    def get(self, key, default=None):
        for k, v in self.items():
            if k.lower() == key.lower():
                return v
        return default


class TestClientAddress(unittest.TestCase):
    def addr(self, peer, **headers):
        return accesslog.client_address(_Headers(headers), peer)

    def test_a_direct_peer_is_taken_as_is_and_forwarded_headers_are_not_believed(self):
        ip, forwarded = self.addr("203.0.113.9", **{"X-Forwarded-For": "1.2.3.4", "X-Wp-Edge-Xff": "5.6.7.8"})
        self.assertEqual(ip, "203.0.113.9")
        self.assertEqual(forwarded["xff"], "1.2.3.4")           # 但原样存下来备查

    def test_behind_our_nginx_the_edge_chain_decides(self):
        self.assertEqual(self.addr("127.0.0.1", **{"X-Wp-Edge-Xff": "198.51.100.7"})[0], "198.51.100.7")

    def test_the_last_hop_wins_because_the_first_can_be_written_by_the_client(self):
        self.assertEqual(self.addr("127.0.0.1", **{"X-Wp-Edge-Xff": "6.6.6.6, 198.51.100.7"})[0], "198.51.100.7")

    def test_falls_back_to_other_headers_then_to_loopback(self):
        self.assertEqual(self.addr("127.0.0.1", **{"X-Wp-Edge-Real-Ip": "198.51.100.8"})[0], "198.51.100.8")
        self.assertEqual(self.addr("127.0.0.1")[0], "127.0.0.1")        # Funnel 不传的话就只能是本机——如实记
        self.assertEqual(self.addr("::1", **{"X-Wp-Edge-Xff": "2001:db8::5"})[0], "2001:db8::5")

    def test_garbage_in_the_header_is_ignored(self):
        self.assertEqual(self.addr("127.0.0.1", **{"X-Wp-Edge-Xff": "<script>, not-an-ip"})[0], "127.0.0.1")
        self.assertEqual(self.addr("127.0.0.1", **{"X-Wp-Edge-Xff": "198.51.100.7:51234"})[0], "198.51.100.7")

    def test_every_forwarding_header_received_is_kept(self):
        _, forwarded = self.addr("127.0.0.1", **{"X-Wp-Edge-Xff": "1.1.1.1", "X-Wp-Edge-Tailscale": "a@b", "Via": "1.1 x"})
        self.assertEqual((forwarded["edge_xff"], forwarded["edge_tailscale"], forwarded["via"], forwarded["peer"]),
                         ("1.1.1.1", "a@b", "1.1 x", "127.0.0.1"))


class TestThrottle(unittest.TestCase):
    def test_limit_and_window(self):
        now = [0.0]
        t = accesslog.Throttle(3, 10, clock=lambda: now[0])
        self.assertEqual([t.allow("a") for _ in range(4)], [True, True, True, False])
        self.assertTrue(t.allow("b"))
        now[0] = 11
        self.assertTrue(t.allow("a"))


def vid():
    import uuid
    return uuid.uuid4().hex[:24]


class AccessCase(HttpCase):
    counter = 0

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.svc.create_user("T001", "老师", password="Teach3r!pw", role="admin", must_change=False)
        cls.db = cls.app.Handler.db

    def login(self, no, password, ua=UA_CHROME_WIN, extra=None):
        c = Client(self.port)
        headers = {"User-Agent": ua, **(extra or {})}
        return c, c.json("POST", "/api/auth/login", {"student_no": no, "password": password}, headers=headers)[0]

    def admin(self):
        c, status = self.login("T001", "Teach3r!pw")
        self.assertEqual(status, 200)
        return c

    def student(self, name="张三", class_name="一班"):
        type(self).counter += 1
        no = "S%04d" % type(self).counter
        self.svc.create_user(no, name, password="Ready2026x", must_change=False, class_name=class_name)
        c, status = self.login(no, "Ready2026x", ua=UA_IPHONE, extra={"X-Wp-Edge-Xff": "198.51.100.20"})
        self.assertEqual(status, 200)
        return no, c

    def track(self, conn, **payload):
        ua = payload.pop("ua", UA_IPHONE)
        return conn.request("POST", "/api/track", payload, headers={"User-Agent": ua, "X-Wp-Edge-Xff": "198.51.100.20"})[0]


class TestTrack(AccessCase):
    def view(self, conn, sid, v=None, path="/word-puzzle/", **extra):
        v = v or vid()
        self.assertEqual(self.track(conn, event="view", vid=v, sid=sid, path=path, title="首页",
                                    client={"screen": "390x844", "tz": "Asia/Shanghai", "cores": 6, "evil": "x"}, **extra), 204)
        return v

    def row(self, v):
        return self.db.one("SELECT * FROM page_views WHERE vid=?", (v,))

    def test_a_view_records_who_where_from_and_with_what(self):
        no, c = self.student()
        v = self.view(c, "s" * 16)
        r = self.row(v)
        self.assertEqual((r["student_no"], r["name"], r["class_name"], r["role"]), (no, "张三", "一班", "student"))
        self.assertEqual((r["ip"], r["browser"], r["os"], r["device_model"], r["device_type"]), ("198.51.100.20", "Safari", "iOS", "iPhone", "mobile"))
        self.assertEqual((r["path"], r["title"]), ("/word-puzzle/", "首页"))
        info = json.loads(r["client_info"])
        self.assertEqual((info["screen"], info["cores"]), ("390x844", 6))
        self.assertNotIn("evil", info)                       # 只收认识的字段
        self.assertIn("198.51.100.20", json.loads(r["forwarded"])["edge_xff"])
        self.assertAlmostEqual(r["started_at"], time.time(), delta=5)

    def test_not_signed_in_visits_are_recorded_too(self):
        c = Client(self.port)
        v = self.view(c, "a" * 16)
        r = self.row(v)
        self.assertEqual((r["user_id"], r["role"], r["student_no"]), (None, "", ""))

    def test_pings_and_leave_accumulate_the_foreground_seconds(self):
        no, c = self.student()
        v = self.view(c, "b" * 16)
        self.track(c, event="ping", vid=v, active=15)
        self.track(c, event="ping", vid=v, active=30)
        self.assertEqual(self.row(v)["active_seconds"], 30)
        self.track(c, event="ping", vid=v, active=20)             # 迟到的旧心跳不能把时间改小
        self.assertEqual(self.row(v)["active_seconds"], 30)
        self.track(c, event="leave", vid=v, active=41)
        r = self.row(v)
        self.assertEqual((r["active_seconds"], r["pings"], r["ended"]), (41, 4, 1))

    def test_dwell_cannot_exceed_how_long_the_page_has_been_open(self):
        no, c = self.student()
        v = self.view(c, "c" * 16)
        self.track(c, event="ping", vid=v, active=10 ** 9)
        self.assertLessEqual(self.row(v)["active_seconds"], 70)

    def test_someone_elses_page_id_cannot_be_changed(self):
        _, a = self.student("甲")
        _, b = self.student("乙")
        v = self.view(a, "d" * 16)
        self.track(b, event="ping", vid=v, active=50)
        self.assertEqual(self.row(v)["active_seconds"], 0)

    def test_invalid_reports_are_dropped_quietly(self):
        no, c = self.student()
        before = self.db.one("SELECT COUNT(*) n FROM page_views")["n"]
        for payload in ({}, {"event": "view"}, {"event": "view", "vid": "short", "sid": "s" * 16},
                        {"event": "view", "vid": vid()}, {"event": "bogus", "vid": vid(), "sid": "s" * 16},
                        {"event": "ping", "vid": vid(), "active": 5}, {"event": "view", "vid": "../../etc/passwd/xx", "sid": "s" * 16}):
            self.assertEqual(self.track(c, **payload), 204)
        self.assertEqual(self.db.one("SELECT COUNT(*) n FROM page_views")["n"], before)
        self.assertEqual(c.request("POST", "/api/track", raw=b"not json")[0], 400)

    def test_sql_and_markup_are_stored_as_plain_text(self):
        no, c = self.student()
        v = vid()
        self.track(c, event="view", vid=v, sid="e" * 16, path="/x'; DROP TABLE page_views;--", title="<script>alert(1)</script>\n\x00")
        r = self.row(v)
        self.assertEqual(r["title"], "<script>alert(1)</script>")
        self.assertEqual(self.db.one("SELECT COUNT(*) n FROM page_views")["n"] > 0, True)

    def test_a_second_report_with_the_same_page_id_does_not_duplicate(self):
        no, c = self.student()
        v = self.view(c, "f" * 16)
        self.view(c, "f" * 16, v=v)
        self.assertEqual(self.db.one("SELECT COUNT(*) n FROM page_views WHERE vid=?", (v,))["n"], 1)

    def test_env_report_fills_in_the_detailed_model(self):
        no, c = self.student()
        v = self.view(c, "g" * 16)
        self.track(c, event="env", vid=v, client={"ua_model": "Pixel 8", "ua_platform_version": "14.0.0"})
        r = self.row(v)
        self.assertEqual(r["device_model"], "Pixel 8")
        self.assertEqual(json.loads(r["client_info"])["ua_platform_version"], "14.0.0")
        self.assertEqual(json.loads(r["client_info"])["screen"], "390x844")        # 原来的没丢

    def test_rate_limit_per_source(self):
        no, c = self.student()
        old = self.app.Handler.track_throttle
        self.app.Handler.track_throttle = accesslog.Throttle(3, 60)
        try:
            v = vid()
            for _ in range(5):
                self.track(c, event="view", vid=v, sid="h" * 16, path="/")
            n = self.db.one("SELECT COUNT(*) n FROM page_views WHERE vid=?", (v,))["n"]
            self.assertEqual(n, 1)
            v2 = vid()
            self.track(c, event="view", vid=v2, sid="h" * 16, path="/")
            self.assertIsNone(self.row(v2))               # 超过上限，丢掉
        finally:
            self.app.Handler.track_throttle = old


class TestLoginEvents(AccessCase):
    def events(self, no):
        return [dict(r) for r in self.db.query("SELECT * FROM login_events WHERE student_no=? ORDER BY id", (no,))]

    def test_success_is_recorded_with_everything(self):
        no, _ = self.student("李四", "二班")
        e = self.events(no)[-1]
        self.assertEqual((e["success"], e["name"], e["class_name"], e["ip"], e["browser"], e["os"], e["device_model"]),
                         (1, "李四", "二班", "198.51.100.20", "Safari", "iOS", "iPhone"))

    def test_failures_are_recorded_with_the_reason_and_who_was_tried(self):
        no, _ = self.student("王五", "三班")
        c, status = self.login(no, "wrong-password")
        self.assertEqual(status, 401)
        e = self.events(no)[-1]
        self.assertEqual((e["success"], e["code"], e["name"], e["class_name"]), (0, "invalid_credentials", "王五", "三班"))

    def test_an_unknown_number_is_recorded_too(self):
        c, status = self.login("NOBODY1", "whatever1")
        self.assertEqual(status, 401)
        e = self.events("NOBODY1")[-1]
        self.assertEqual((e["success"], e["user_id"], e["name"]), (0, None, ""))

    def test_the_password_is_never_stored_anywhere(self):
        no, _ = self.student()
        self.login(no, "Sup3r-Secret-Typo")
        dump = json.dumps([dict(r) for r in self.db.query("SELECT * FROM login_events")] +
                          [dict(r) for r in self.db.query("SELECT * FROM page_views")], ensure_ascii=False)
        self.assertNotIn("Sup3r-Secret-Typo", dump)
        self.assertNotIn("Ready2026x", dump)

    def test_recording_failure_never_breaks_login(self):
        from unittest import mock
        no = "S9999"
        self.svc.create_user(no, "赵六", password="Ready2026x", must_change=False)
        with mock.patch.object(accesslog, "record_login", side_effect=RuntimeError("disk full")):
            c, status = self.login(no, "Ready2026x")
        self.assertEqual(status, 200)


class TestAdminViews(AccessCase):
    def test_students_cannot_read_any_of_it(self):
        no, c = self.student()
        for path in ("/api/admin/visits", "/api/admin/logins", "/api/admin/visits/pages?sid=x",
                     "/api/admin/export/page-views.csv", "/api/admin/export/logins.csv"):
            self.assertEqual(c.request("GET", path)[0], 403, path)
        self.assertEqual(Client(self.port).request("GET", "/api/admin/visits")[0], 401)

    def test_one_visit_groups_the_pages_opened_in_one_tab(self):
        no, c = self.student("孙七", "四班")
        sid = "k" * 16
        for i, path in enumerate(("/word-puzzle/", "/word-puzzle/play.html", "/word-puzzle/stats.html")):
            v = vid()
            self.track(c, event="view", vid=v, sid=sid, path=path)
            self.track(c, event="leave", vid=v, active=10 * (i + 1))
        a = self.admin()
        status, body = a.json("GET", "/api/admin/visits?q=" + no)
        self.assertEqual(status, 200)
        self.assertEqual(body["total"], 1)
        s = body["sessions"][0]
        self.assertEqual((s["pages"], s["active_seconds"], s["name"], s["class_name"], s["ip"]), (3, 60, "孙七", "四班", "198.51.100.20"))
        status, detail = a.json("GET", "/api/admin/visits/pages?sid=%s&user_id=%d" % (sid, s["user_id"]))
        self.assertEqual([p["path"] for p in detail["pages"]], ["/word-puzzle/", "/word-puzzle/play.html", "/word-puzzle/stats.html"])
        self.assertEqual(detail["pages"][0]["forwarded"]["edge_xff"], "198.51.100.20")

    def test_filters(self):
        no, c = self.student("周八", "五班")
        self.track(c, event="view", vid=vid(), sid="m" * 16, path="/")
        anon = Client(self.port)
        self.track(anon, event="view", vid=vid(), sid="n" * 16, path="/word-puzzle/login.html")
        a = self.admin()
        by = lambda q: a.json("GET", "/api/admin/visits?" + q)[1]
        self.assertTrue(all(s["class_name"] == "五班" for s in by("class_name=五班")["sessions"]))
        self.assertTrue(all(s["user_id"] is None for s in by("role=anonymous")["sessions"]))
        self.assertTrue(all(s["role"] == "student" for s in by("role=student")["sessions"]))
        self.assertEqual(by("q=" + no)["total"], 1)
        self.assertEqual(by("q=198.51.100.20")["total"] >= 1, True)
        future = int(time.time()) + 3600
        self.assertEqual(by("since=%d" % future)["total"], 0)
        self.assertEqual(a.request("GET", "/api/admin/visits?since=abc")[0], 400)

    def test_login_list_and_failed_filter(self):
        no, _ = self.student("吴九", "六班")
        self.login(no, "bad-pass-1")
        a = self.admin()
        body = a.json("GET", "/api/admin/logins?q=" + no)[1]
        self.assertEqual([e["success"] for e in body["logins"]], [0, 1])            # 最近的在最前
        failed = a.json("GET", "/api/admin/logins?failed=1&q=" + no)[1]
        self.assertEqual([e["success"] for e in failed["logins"]], [0])

    def test_paging(self):
        no, c = self.student()
        for _ in range(5):
            self.login(no, "nope-nope-1")
        a = self.admin()
        first = a.json("GET", "/api/admin/logins?failed=1&q=%s&limit=2" % no)[1]
        second = a.json("GET", "/api/admin/logins?failed=1&q=%s&limit=2&offset=2" % no)[1]
        self.assertEqual((len(first["logins"]), len(second["logins"]), first["total"]), (2, 2, 5))
        self.assertFalse({e["id"] for e in first["logins"]} & {e["id"] for e in second["logins"]})

    def test_csv_exports_every_column_with_local_time_and_safe_cells(self):
        no, c = self.student("=HYPERLINK(\"x\")", "七班")
        self.track(c, event="view", vid=vid(), sid="p" * 16, path="/x")
        a = self.admin()
        status, raw = a.request("GET", "/api/admin/export/page-views.csv?q=198.51.100.20")
        self.assertEqual(status, 200)
        self.assertIn("text/csv", a.last.getheader("Content-Type"))
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
        rows = list(csv.reader(io.StringIO(raw.decode("utf-8-sig"))))
        head = rows[0]
        for col in ("ip", "forwarded", "user_agent", "browser", "os", "device_model", "client_info", "started_at", "active_seconds"):
            self.assertIn(col, head)
        mine = [r for r in rows[1:] if r[head.index("student_no")] == no][0]
        self.assertEqual(mine[head.index("name")], "'=HYPERLINK(\"x\")")
        self.assertRegex(mine[head.index("started_at")], r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d$")
        status, raw = a.request("GET", "/api/admin/export/logins.csv")
        self.assertEqual(status, 200)
        self.assertIn("success", raw.decode("utf-8-sig").splitlines()[0])


class TestLanEdition(HttpCase):
    auth_options = False

    def test_the_lan_edition_keeps_no_access_log_and_has_no_admin_views(self):
        c = Client(self.port)
        before = self.app.Handler.db.one("SELECT COUNT(*) n FROM page_views")["n"]
        self.assertEqual(c.request("POST", "/api/track", {"event": "view", "vid": vid(), "sid": "q" * 16, "path": "/"})[0], 204)
        self.assertEqual(self.app.Handler.db.one("SELECT COUNT(*) n FROM page_views")["n"], before)
        self.assertEqual(c.request("GET", "/api/admin/visits")[0], 404)


class TestSchema(unittest.TestCase):
    def test_times_are_integers_and_nothing_is_ever_deleted_automatically(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(str(Path(tmp) / "a.db"))
            cols = {r["name"]: r["type"] for r in db.query("PRAGMA table_info(page_views)")}
            self.assertEqual((cols["started_at"], cols["last_seen_at"], cols["active_seconds"]), ("INTEGER", "INTEGER", "INTEGER"))
            self.assertEqual({r["name"]: r["type"] for r in db.query("PRAGMA table_info(login_events)")}["ts"], "INTEGER")
            db.close()
        for name in ("db.py", "accesslog.py", "app.py"):
            text = (ROOT / "server" / name).read_text(encoding="utf-8").upper()
            self.assertNotIn("DELETE FROM PAGE_VIEWS", text, name)
            self.assertNotIn("DELETE FROM LOGIN_EVENTS", text, name)


class TestWiring(unittest.TestCase):
    PAGES = ("index", "bank", "stats", "play", "admin", "login", "change-password", "visits")

    def test_every_page_loads_the_tracker_after_the_auth_script(self):
        for page in self.PAGES:
            html = (WEB / (page + ".html")).read_text(encoding="utf-8")
            self.assertEqual(html.count("js/tracker.js"), 1, page)
            self.assertLess(html.index("js/auth-ui.js"), html.index("js/tracker.js"), page)

    def test_the_offline_page_does_not_track(self):
        from server import offline
        self.assertNotIn("/api/track", offline.ADAPTER_FILE.read_text(encoding="utf-8"))
        self.assertNotIn("tracker.js", (ROOT / "server" / "offline.py").read_text(encoding="utf-8"))

    def test_the_login_page_tells_people_what_is_recorded(self):
        html = (WEB / "login.html").read_text(encoding="utf-8")
        self.assertIn("IP 地址", html)
        self.assertIn("IP address", html)

    def test_service_runs_in_beijing_time_and_nginx_passes_the_edge_headers(self):
        self.assertIn("Environment=TZ=Asia/Shanghai", (FAMILY / "systemd" / "word-puzzle-family.service").read_text(encoding="utf-8"))
        proxy = (FAMILY / "nginx" / "proxy.inc").read_text(encoding="utf-8")
        for header in ("X-Wp-Edge-Xff $http_x_forwarded_for", "X-Wp-Edge-Real-Ip $http_x_real_ip",
                       "X-Wp-Edge-Forwarded $http_forwarded", "X-Wp-Edge-Tailscale $http_tailscale_user_login"):
            self.assertIn(header, proxy)

    def test_visits_page_is_teacher_only_and_linked_for_teachers(self):
        self.assertIn('data-auth="visits"', (WEB / "visits.html").read_text(encoding="utf-8"))
        ui = (WEB / "js" / "auth-ui.js").read_text(encoding="utf-8")
        self.assertIn("visitsNavLink", ui)
        self.assertIn("mode === 'visits'", ui)


@unittest.skipUnless(shutil.which("node"), "本机没有 node，跳过页面上报脚本的行为测试")
class TestTrackerScript(unittest.TestCase):
    def test_behaviour(self):
        proc = subprocess.run([shutil.which("node"), str(ROOT / "tests" / "js" / "tracker.test.js")],
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


@unittest.skipUnless(NGINX, "本机没有 nginx，跳过真实转发头测试")
class TestRealNginxHeaders(unittest.TestCase):
    def test_client_cannot_forge_the_edge_headers(self):
        seen = {}

        class Backend(http.server.BaseHTTPRequestHandler):
            def do_GET(self):      # noqa: N802
                seen.update({k.lower(): v for k, v in self.headers.items()})
                self.send_response(200)
                self.send_header("Content-Length", "2")
                self.end_headers()
                self.wfile.write(b"ok")

            def log_message(self, *a):
                pass

        backend = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Backend)
        threading.Thread(target=backend.serve_forever, daemon=True).start()
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        conf_text = (FAMILY / "nginx" / "word-puzzle-family.conf").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            install = tmp / "srv"
            (install / "web").mkdir(parents=True)
            (install / "shared").mkdir()
            inc = tmp / "proxy.inc"
            inc.write_text((FAMILY / "nginx" / "proxy.inc").read_text(encoding="utf-8"), encoding="utf-8")
            conf = (conf_text.replace("@INSTALL_DIR@", str(install)).replace("@PORT@", str(backend.server_address[1]))
                    .replace("@NGINX_PORT@", str(port)).replace("@PROXY_INC@", str(inc)).replace("/var/log/nginx/", str(tmp) + "/"))
            (tmp / "site.conf").write_text(conf, encoding="utf-8")
            (tmp / "nginx.conf").write_text(
                "pid %s/n.pid;\nerror_log %s/e.log;\nevents {}\nhttp {\n  client_body_temp_path %s/b; proxy_temp_path %s/p; "
                "fastcgi_temp_path %s/f;\n  uwsgi_temp_path %s/u; scgi_temp_path %s/s;\n  include %s/site.conf;\n}\n" % ((tmp,) * 8),
                encoding="utf-8")
            started = subprocess.run([NGINX, "-c", str(tmp / "nginx.conf"), "-p", str(tmp)], capture_output=True, text=True)
            self.assertEqual(started.returncode, 0, started.stderr)
            try:
                req = urllib.request.Request("http://127.0.0.1:%d/word-puzzle/api/health" % port, headers={
                    "Host": "lexica.example.ts.net", "X-Forwarded-For": "198.51.100.77", "X-Wp-Edge-Xff": "6.6.6.6",
                    "X-Wp-Edge-Real-Ip": "6.6.6.7", "X-Wp-Edge-Tailscale": "forged@evil"})
                for _ in range(30):
                    try:
                        urllib.request.urlopen(req, timeout=2).read()
                        break
                    except Exception:
                        time.sleep(0.1)
                else:
                    self.fail("nginx 没有响应")
            finally:
                subprocess.run([NGINX, "-c", str(tmp / "nginx.conf"), "-p", str(tmp), "-s", "stop"], capture_output=True)
        backend.shutdown()
        self.assertEqual(seen.get("x-wp-edge-xff"), "198.51.100.77")        # 是 nginx 收到的 X-Forwarded-For，不是客户端写的那个
        self.assertEqual(seen.get("x-wp-edge-real-ip", ""), "")
        self.assertEqual(seen.get("x-wp-edge-tailscale", ""), "")
        self.assertEqual(seen.get("x-forwarded-for"), "127.0.0.1")
        ip, _ = accesslog.client_address(_Headers(seen), "127.0.0.1")
        self.assertEqual(ip, "198.51.100.77")


if __name__ == "__main__":
    unittest.main()
