"""学生版的内网入口：同一个网站、同一个数据库、同一套账号，老师在家直接访问；照样要登录。"""
from __future__ import annotations

import http.server
import re
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

from tests.test_auth import Client, HttpCase      # noqa: E402

FAMILY = ROOT / "deploy" / "family"
NGINX = shutil.which("nginx")


class TestCookieFollowsTheEntrance(HttpCase):
    auth_options = {"cookie_secure": True}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.svc.create_user("T001", "老师", password="Teach3r!pw", role="admin", must_change=False)

    def login(self, proto=None):
        c = Client(self.port)
        headers = {"X-Forwarded-Proto": proto} if proto else {}
        status, _ = c.json("POST", "/api/auth/login", {"student_no": "T001", "password": "Teach3r!pw"}, headers=headers)
        self.assertEqual(status, 200)
        return c, c.last.getheader("Set-Cookie"), c.last.getheader("Strict-Transport-Security")

    def test_public_entrance_keeps_secure_cookie_and_hsts(self):
        for proto in ("https", None, "garbage"):
            _, cookie, hsts = self.login(proto)
            self.assertIn("Secure", cookie, proto)
            self.assertIsNotNone(hsts, proto)

    def test_plain_http_lan_entrance_gets_a_cookie_the_browser_will_keep(self):
        c, cookie, hsts = self.login("http")
        self.assertNotIn("Secure", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIsNone(hsts)
        self.assertEqual(c.json("GET", "/api/admin/users", headers={"X-Forwarded-Proto": "http"})[0], 200)   # 登录态有效
        status, _ = c.json("POST", "/api/auth/logout", {}, headers={"X-Forwarded-Proto": "http"})
        self.assertNotIn("Secure", c.last.getheader("Set-Cookie"))


class TestStatic(unittest.TestCase):
    INSTALL = (FAMILY / "install.sh").read_text(encoding="utf-8")

    def test_opt_in_private_addresses_only(self):
        self.assertIn("WP_LAN_ADDR", self.INSTALL)
        self.assertIn("不能是公网地址", self.INSTALL)
        self.assertIn('rm -f "$LAN_CONF_FILE"', self.INSTALL)
        self.assertEqual(subprocess.run(["bash", "-n", str(FAMILY / "install.sh")]).returncode, 0)
        rx = re.search(r'LAN_ADDR" =~ (\^.*?\$) \]\]', self.INSTALL).group(1).replace("\\\\.", "\\.")
        rx = re.compile(rx)
        for ok in ("192.168.1.100", "192.168.1.5", "172.16.0.9", "172.31.1.1"):
            self.assertTrue(rx.match(ok), ok)
        for bad in ("8.8.8.8", "100.64.0.1", "172.32.0.1", "127.0.0.1", "lexica.ts.net", "0.0.0.0"):
            self.assertFalse(rx.match(bad), bad)

    def test_there_is_no_password_free_path(self):
        for name in ("install.sh", "nginx/proxy.inc", "nginx/word-puzzle-family.conf"):
            self.assertNotIn("Lan-Admin", (FAMILY / name).read_text(encoding="utf-8"))
        self.assertNotIn("WP_LAN_ADMIN", (ROOT / "server" / "app.py").read_text(encoding="utf-8"))


@unittest.skipUnless(NGINX, "本机没有 nginx，跳过真实入口测试")
class TestRealNginx(unittest.TestCase):
    def test_two_entrances_one_backend(self):
        seen = []

        class Backend(http.server.BaseHTTPRequestHandler):
            def do_GET(self):      # noqa: N802
                seen.append({k.lower(): v for k, v in self.headers.items()})
                self.send_response(200)
                self.send_header("Content-Length", "2")
                self.end_headers()
                self.wfile.write(b"ok")

            def log_message(self, *a):
                pass

        backend = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Backend)
        threading.Thread(target=backend.serve_forever, daemon=True).start()
        ports = []
        for _ in range(2):
            with socket.socket() as probe:
                probe.bind(("127.0.0.1", 0))
                ports.append(probe.getsockname()[1])
        pub, lan = ports
        conf_text = (FAMILY / "nginx" / "word-puzzle-family.conf").read_text(encoding="utf-8")
        proxy = (FAMILY / "nginx" / "proxy.inc").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            install = tmp / "srv"
            (install / "web").mkdir(parents=True)
            (install / "shared").mkdir()
            (tmp / "proxy.inc").write_text(proxy, encoding="utf-8")
            # 和 install.sh 里一模一样的变换
            lan_proxy = re.sub(r"(?m)^proxy_set_header X-Forwarded-Proto .*$", "proxy_set_header X-Forwarded-Proto http;", proxy)
            lan_proxy = re.sub(r"(?m)^proxy_set_header X-Wp-Edge-Xff .*$", "proxy_set_header X-Wp-Edge-Xff $remote_addr;", lan_proxy)
            (tmp / "proxy-lan.inc").write_text(lan_proxy, encoding="utf-8")

            def render(text, inc, port):
                return (text.replace("@INSTALL_DIR@", str(install)).replace("@PORT@", str(backend.server_address[1]))
                        .replace("@NGINX_PORT@", str(port)).replace("@PROXY_INC@", str(inc)).replace("/var/log/nginx/", str(tmp) + "/"))
            (tmp / "a.conf").write_text(render(conf_text, tmp / "proxy.inc", pub), encoding="utf-8")
            (tmp / "b.conf").write_text(render(conf_text[conf_text.index("server {"):], tmp / "proxy-lan.inc", lan)
                                        .replace("word-puzzle-family.", "word-puzzle-family-lan."), encoding="utf-8")
            (tmp / "nginx.conf").write_text(
                "pid %s/n.pid;\nerror_log %s/e.log;\nevents {}\nhttp {\n  client_body_temp_path %s/b; proxy_temp_path %s/p; "
                "fastcgi_temp_path %s/f;\n  uwsgi_temp_path %s/u; scgi_temp_path %s/s;\n  include %s/a.conf;\n  include %s/b.conf;\n}\n"
                % ((tmp,) * 9), encoding="utf-8")
            started = subprocess.run([NGINX, "-c", str(tmp / "nginx.conf"), "-p", str(tmp)], capture_output=True, text=True)
            self.assertEqual(started.returncode, 0, started.stderr)
            try:
                def hit(port, **headers):
                    req = urllib.request.Request("http://127.0.0.1:%d/word-puzzle/api/health" % port, headers=dict({"Host": "x"}, **headers))
                    for _ in range(30):
                        try:
                            urllib.request.urlopen(req, timeout=2).read()
                            return seen[-1]
                        except Exception:
                            time.sleep(0.1)
                    self.fail("nginx 没有响应")
                public = hit(pub, **{"X-Forwarded-For": "198.51.100.9", "X-Forwarded-Proto": "http"})
                inside = hit(lan, **{"X-Forwarded-For": "6.6.6.6"})
            finally:
                subprocess.run([NGINX, "-c", str(tmp / "nginx.conf"), "-p", str(tmp), "-s", "stop"], capture_output=True)
        backend.shutdown()
        self.assertEqual(public.get("x-forwarded-proto"), "https")                 # 公网入口：恒为 https，客户端写的 http 被覆盖
        self.assertEqual(public.get("x-wp-edge-xff"), "198.51.100.9")
        self.assertEqual(inside.get("x-forwarded-proto"), "http")                   # 内网入口：明文
        self.assertEqual(inside.get("x-wp-edge-xff"), "127.0.0.1")                  # 记真实连接地址，不信客户端写的 6.6.6.6


if __name__ == "__main__":
    unittest.main()
