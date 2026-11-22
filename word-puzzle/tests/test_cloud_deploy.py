"""云服务器（生产）部署文件的检查：公网入口只认自己的域名、没有证书不走明文、客户端自带的转发头不被信任、
SSH 加固不会把人锁在外面。render-nginx.sh 用假的 nginx / systemctl 真的跑一遍，看生成出来的配置。"""
from __future__ import annotations

import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLOUD = ROOT / "deploy" / "cloud"
FAMILY = ROOT / "deploy" / "family"
SCRIPTS = ("install.sh", "render-nginx.sh", "enable-tls.sh", "harden.sh")  # 加 migrate-data.sh / sync-from-home.sh 另见各自的测试
DOMAIN = "lexica.example.test"


def read(name: str) -> str:
    return (CLOUD / name).read_text(encoding="utf-8")


class TestScriptsParse(unittest.TestCase):
    def test_every_script_parses_and_is_executable(self):
        for name in SCRIPTS:
            path = CLOUD / name
            done = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, "%s: %s" % (name, done.stderr))
            self.assertTrue(path.stat().st_mode & stat.S_IXUSR, "%s 不可执行" % name)
            self.assertIn("set -euo pipefail", path.read_text(encoding="utf-8"))


class TestShellPitfalls(unittest.TestCase):
    def test_a_variable_is_never_directly_followed_by_a_non_ascii_character(self):
        """bash 把非 ASCII 字符的第一个字节当成变量名的一部分（macOS 自带的 bash、LANG=C 的环境），
        set -u 之下 "$SNAP（" 会变成 "SNAP\\xef: unbound variable"。紧挨着中文的变量一律写成 ${NAME}。"""
        pattern = re.compile(r"\$[A-Za-z_][A-Za-z0-9_]*(?=[^\x00-\x7f])")
        for name in SCRIPTS + ("migrate-data.sh", "sync-from-home.sh"):
            bad = [m.group(0) for line in read(name).splitlines() if not line.lstrip().startswith("#")
                   for m in pattern.finditer(line)]
            self.assertEqual(bad, [], "%s: 变量后面紧跟中文，要写成 ${NAME}" % name)


class TestInstall(unittest.TestCase):
    TEXT = read("install.sh")

    def test_domain_is_required_and_validated_and_never_written_in_the_repo(self):
        self.assertIn('DOMAIN="${WP_DOMAIN:-}"', self.TEXT)
        self.assertIn("请用 WP_DOMAIN", self.TEXT)
        for name in SCRIPTS:
            self.assertNotRegex(read(name), r"\b[a-z0-9-]+\.(cn|com|net|org)\b(?!\))", "%s 里不该写死域名" % name)

    def test_it_reuses_the_family_installer_in_cloud_mode_over_https(self):
        self.assertIn("WP_CLOUD=1", self.TEXT)
        self.assertIn('WP_PUBLIC_URL="https://$DOMAIN"', self.TEXT)
        self.assertIn("deploy/family/install.sh", self.TEXT)
        self.assertIn("render-nginx.sh", self.TEXT)

    def test_backups_go_to_a_directory_by_default(self):
        self.assertIn("/var/backups/lexica", self.TEXT)
        self.assertIn("WP_BACKUP_DIR", self.TEXT)

    def test_family_installer_stops_talking_about_funnel_in_cloud_mode(self):
        family = (FAMILY / "install.sh").read_text(encoding="utf-8")
        self.assertIn('"${WP_CLOUD:-}" == "1"', family)
        self.assertIn("tailscale funnel --bg", family, "家里的安装说明仍然要有 Funnel 这一步")


class TestHarden(unittest.TestCase):
    TEXT = read("harden.sh")

    def test_it_refuses_to_lock_you_out(self):
        self.assertIn("authorized_keys", self.TEXT)
        self.assertIn("没有公钥", self.TEXT)
        self.assertIn("sshd -t", self.TEXT)
        self.assertIn("保持当前终端", self.TEXT)

    def test_passwords_are_off_and_the_dropin_wins_over_cloud_init(self):
        self.assertIn("PasswordAuthentication no", self.TEXT)
        self.assertIn("KbdInteractiveAuthentication no", self.TEXT)
        self.assertIn("PermitRootLogin prohibit-password", self.TEXT)
        self.assertIn("00-lexica-hardening.conf", self.TEXT, "sshd 取第一次出现的值，文件名要排在 50-cloud-init 之前")
        self.assertIn("sshd -T", self.TEXT, "要读生效的值确认密码登录真的关了，而不是只看自己写的文件")

    def test_fail2ban_watches_sshd_through_the_journal(self):
        self.assertIn("fail2ban", self.TEXT)
        self.assertIn("backend = systemd", self.TEXT)
        self.assertIn("python3-systemd", self.TEXT)


class TestEnableTls(unittest.TestCase):
    TEXT = read("enable-tls.sh")

    def test_uses_webroot_validation_and_renews_with_a_reload_hook(self):
        self.assertIn("--webroot", self.TEXT)
        self.assertIn("renewal-hooks/deploy", self.TEXT)
        self.assertIn("systemctl reload nginx", self.TEXT)
        self.assertIn("certbot.timer", self.TEXT)

    def test_it_can_dry_run_against_staging_and_gives_the_reason_when_it_fails(self):
        self.assertIn("WP_ACME_STAGING", self.TEXT)
        self.assertIn("--staging", self.TEXT)
        self.assertIn("是否已备案", self.TEXT)

    def test_self_check_requires_the_api_to_reject_anonymous_requests(self):
        self.assertIn('"401"', self.TEXT)
        self.assertIn('"301"', self.TEXT)

    def test_email_is_optional_and_comes_from_the_environment(self):
        self.assertIn("WP_ACME_EMAIL", self.TEXT)
        self.assertIn("--register-unsafely-without-email", self.TEXT)
        self.assertNotRegex(self.TEXT, r"[A-Za-z0-9._-]+@[A-Za-z0-9-]+\.[a-z]{2,}")


class TestRenderNginx(unittest.TestCase):
    """用假的 nginx / systemctl 跑 render-nginx.sh，检查生成的文件。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.install_dir = base / "srv"
        nginx_dir = self.install_dir / "deploy" / "family" / "nginx"
        nginx_dir.mkdir(parents=True)
        for name in ("word-puzzle-family.conf", "proxy.inc"):
            (nginx_dir / name).write_text((FAMILY / "nginx" / name).read_text(encoding="utf-8"), encoding="utf-8")
        self.conf_dir = base / "etc-nginx" / "conf.d"
        self.etc_dir = base / "etc-nginx"
        (self.etc_dir / "sites-enabled").mkdir(parents=True)
        (self.etc_dir / "sites-enabled" / "default").write_text("server { listen 80 default_server; }", encoding="utf-8")
        self.cert_dir = base / "live"
        self.webroot = base / "webroot"
        shims = base / "bin"
        shims.mkdir()
        self.calls = base / "calls.log"
        for name in ("nginx", "systemctl"):
            shim = shims / name
            shim.write_text('#!/bin/sh\necho "%s $*" >> "%s"\nexit 0\n' % (name, self.calls), encoding="utf-8")
            shim.chmod(0o755)
        self.env = dict(
            os.environ,
            PATH="%s:%s" % (shims, os.environ["PATH"]),
            WP_DOMAIN=DOMAIN,
            WP_FAMILY_INSTALL_DIR=str(self.install_dir),
            WP_FAMILY_PORT="8766",
            WP_ACME_WEBROOT=str(self.webroot),
            WP_CERT_DIR=str(self.cert_dir),
            WP_NGINX_CONF_DIR=str(self.conf_dir),
            WP_NGINX_ETC_DIR=str(self.etc_dir),
        )

    def render(self, **env):
        done = subprocess.run(["bash", str(CLOUD / "render-nginx.sh")], env=dict(self.env, **env),
                              capture_output=True, text=True)
        return done

    def add_certificate(self):
        live = self.cert_dir / DOMAIN
        live.mkdir(parents=True)
        (live / "fullchain.pem").write_text("cert", encoding="utf-8")
        (live / "privkey.pem").write_text("key", encoding="utf-8")

    def conf(self) -> str:
        return (self.conf_dir / "lexica-cloud.conf").read_text(encoding="utf-8")

    def proxy(self) -> str:
        return (self.etc_dir / "lexica-cloud-proxy.inc").read_text(encoding="utf-8")

    def test_without_a_certificate_the_site_is_not_served_in_clear_text(self):
        done = self.render()
        self.assertEqual(done.returncode, 0, done.stderr)
        conf = self.conf()
        self.assertIn("listen 80 default_server;", conf)
        self.assertIn("return 444;", conf, "别的域名和直接用 IP 访问要被断开")
        self.assertIn("location ^~ /.well-known/acme-challenge/", conf)
        self.assertIn("return 404;", conf)
        self.assertNotIn("proxy_pass", conf, "没有证书时，应用不能挂在明文 80 上（登录 Cookie 带 Secure，账号密码也不该明文走公网）")
        self.assertNotIn("listen 443", conf)
        self.assertIn("没有证书", done.stdout)

    def test_with_a_certificate_it_serves_https_and_redirects_to_the_fixed_domain(self):
        self.add_certificate()
        done = self.render()
        self.assertEqual(done.returncode, 0, done.stderr)
        conf = self.conf()
        self.assertIn("listen 443 ssl;", conf)
        self.assertIn("http2 on;", conf)
        self.assertIn("ssl_certificate %s/%s/fullchain.pem;" % (self.cert_dir, DOMAIN), conf)
        self.assertIn("ssl_protocols TLSv1.2 TLSv1.3;", conf)
        self.assertIn("ssl_reject_handshake on;", conf, "直接用 IP 访问 443 要在握手阶段被拒绝")
        self.assertIn("server_name %s;" % DOMAIN, conf)
        self.assertIn("return 301 https://%s$request_uri;" % DOMAIN, conf, "跳转用固定域名，不用客户端发来的 Host")
        self.assertNotIn("$host", conf)
        self.assertNotIn("127.0.0.1:@", conf)
        self.assertEqual(re.findall(r"@[A-Z_]+@", conf), [], "占位符没有替换干净")

    def test_the_site_part_comes_from_the_family_config_so_both_stay_in_step(self):
        self.add_certificate()
        self.render()
        conf = self.conf()
        for needle in ("location ~ /\\.(?!well-known/) { return 404; }",
                       "location = /word-puzzle/api/auth/login",
                       "limit_req zone=wp_family_login",
                       "client_max_body_size 2m;",
                       "proxy_pass http://127.0.0.1:8766/api/;",
                       "alias %s/web/;" % self.install_dir):
            self.assertIn(needle, conf)
        self.assertIn("include %s/lexica-cloud-proxy.inc;" % self.etc_dir, conf)
        self.assertIn("word-puzzle-cloud.access.log", conf)
        self.assertNotIn("word-puzzle-family.access.log", conf)

    def test_forwarding_headers_from_the_client_are_not_trusted(self):
        self.render()
        proxy = self.proxy()
        self.assertIn("proxy_set_header X-Wp-Edge-Xff $remote_addr;", proxy)
        self.assertIn("proxy_set_header X-Wp-Edge-Real-Ip $remote_addr;", proxy)
        self.assertIn('proxy_set_header X-Wp-Edge-Forwarded "";', proxy)
        self.assertIn('proxy_set_header X-Wp-Edge-Tailscale "";', proxy)
        for client_controlled in ("$http_x_forwarded_for", "$http_x_real_ip", "$http_forwarded",
                                  "$http_tailscale_user_login", "$proxy_add_x_forwarded_for"):
            self.assertNotIn(client_controlled, proxy)
        self.assertIn('proxy_set_header X-Wp-Entry "";', proxy, "公网入口不能被当成内网入口")

    def test_debian_default_site_is_removed_and_nginx_is_checked_before_reload(self):
        self.render()
        self.assertFalse((self.etc_dir / "sites-enabled" / "default").exists())
        calls = self.calls.read_text(encoding="utf-8").splitlines()
        self.assertIn("nginx -t", calls)
        self.assertLess(calls.index("nginx -t"), calls.index("systemctl reload nginx"))

    def test_a_failing_nginx_check_restores_the_previous_config(self):
        self.render()
        before = self.conf()
        failing = Path(self.tmp.name) / "bin" / "nginx"
        failing.write_text('#!/bin/sh\nexit 1\n', encoding="utf-8")
        self.add_certificate()
        done = self.render()
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("已恢复原样", done.stderr)
        self.assertEqual(self.conf(), before)

    def test_bad_domains_are_rejected(self):
        for bad in ("", "a b", "x;rm -rf /", "a/b"):
            done = self.render(WP_DOMAIN=bad)
            self.assertNotEqual(done.returncode, 0, repr(bad))


class TestTunnelEntrance(unittest.TestCase):
    """SSH 隧道入口（127.0.0.1:8081）：浏览器看到的是明文 http，会话 Cookie 不能带 Secure。

    带 Secure 的 Cookie 浏览器只在「安全来源」（https，或者 localhost）下才保存。
    用隧道从本机的局域网 IP 打开时（例如 http://192.168.x.x:8081）不是安全来源，
    浏览器会把 Cookie 丢掉 —— 表现是「登录成功，刷新一下又要求登录」。
    所以云服务器上这个入口要告诉后端「这条是明文 http」。
    """

    INSTALL = (FAMILY / "install.sh").read_text(encoding="utf-8")
    PROXY = (FAMILY / "nginx" / "proxy.inc").read_text(encoding="utf-8")

    def test_the_cloud_tunnel_entry_is_installed_as_plain_http(self):
        self.assertIn('"${WP_CLOUD:-}" == "1"', self.INSTALL)
        self.assertIn("TUNNEL_PROXY_INC", self.INSTALL)
        self.assertIn("proxy_set_header X-Forwarded-Proto http;", self.INSTALL)

    def test_the_home_machine_keeps_https_for_its_funnel(self):
        """家里这台机器前面是 Funnel（浏览器看到 https），不能跟着改成明文。"""
        self.assertIn('CONTAINER_PROXY_INC="$PROXY_INC"', self.INSTALL)
        self.assertIn('CONTAINER_PROXY_INC="$TUNNEL_PROXY_INC"', self.INSTALL)
        self.assertIn("proxy_set_header X-Forwarded-Proto https;", self.PROXY)

    def test_the_tunnel_forwards_the_real_connection_address(self):
        """客户端自己写的 X-Forwarded-For 不能算数：nginx 把自己看到的连接地址补在最后。"""
        self.assertIn("proxy_set_header X-Wp-Edge-Xff $proxy_add_x_forwarded_for;", self.INSTALL)

    def test_the_rendered_tunnel_headers_reach_the_backend_as_plain_http(self):
        """把安装脚本里那段变换真跑一遍，看看后端会收到什么头。"""
        tunnel = re.sub(r"(?m)^proxy_set_header X-Forwarded-Proto .*$",
                        "proxy_set_header X-Forwarded-Proto http;", self.PROXY)
        tunnel = re.sub(r"(?m)^proxy_set_header X-Wp-Edge-Xff .*$",
                        "proxy_set_header X-Wp-Edge-Xff $proxy_add_x_forwarded_for;", tunnel)
        self.assertIn("proxy_set_header X-Forwarded-Proto http;", tunnel)
        self.assertIn("$proxy_add_x_forwarded_for", tunnel)
        # 入口标记仍然清空：隧道不是「内网免登录入口」
        self.assertRegex(tunnel, r'(?m)^proxy_set_header X-Wp-Entry "";$')

    def test_the_backend_then_leaves_the_secure_flag_off(self):
        """后端看到「明文 http + 本机 nginx」时，会话 Cookie 不带 Secure，浏览器才留得住。

        这里用真实的后端跑一次登录（请求带 X-Forwarded-Proto: http，和隧道进来的一样）。
        """
        sys.path.insert(0, str(ROOT))
        from tests.test_auth import Client, HttpCase

        class TunnelCase(HttpCase):
            auth_options = {"cookie_secure": True}

            @classmethod
            def setUpClass(cls):
                super().setUpClass()
                cls.svc.create_user("TUNNEL01", "隧道老师", password="Tunnel2026x", role="teacher", must_change=False)

        TunnelCase.setUpClass()
        try:
            c = Client(TunnelCase.port)
            status, _ = c.json("POST", "/api/auth/login",
                               {"student_no": "TUNNEL01", "password": "Tunnel2026x"},
                               headers={"X-Forwarded-Proto": "http"})
            self.assertEqual(status, 200)
            cookie = c.last.getheader("Set-Cookie")
            self.assertNotIn("Secure", cookie, "隧道进来的是明文 http，Cookie 不该带 Secure")
            self.assertIn("HttpOnly", cookie)
            # 登录态要真的能用：刷新一下还是登录着
            status, body = c.json("GET", "/api/auth/me", {}, headers={"X-Forwarded-Proto": "http"})
            self.assertEqual(status, 200)
            self.assertEqual(body.get("user", {}).get("student_no"), "TUNNEL01")
        finally:
            TunnelCase.tearDownClass()


class TestGuide(unittest.TestCase):
    TEXT = (CLOUD / "部署说明.md").read_text(encoding="utf-8") if (CLOUD / "部署说明.md").exists() else ""

    def test_the_guide_covers_the_steps_and_the_rules_around_them(self):
        for needle in ("install.sh", "harden.sh", "enable-tls.sh",
                       "LocalForward", "~/.ssh/config",
                       "备案", "流量穿透", "快照", "WP_ACME_STAGING",
                       "migrate-data.sh", "sync-from-home.sh", "rehearse", "cutover --yes", "自动把快照放回去"):
            self.assertIn(needle, self.TEXT)

    def test_the_guide_says_the_tunnel_comes_from_the_ssh_config(self):
        """转发是写在 ~/.ssh/config 里的：说明里不能只教手动 -L 那一种写法。"""
        self.assertIn("LocalForward 127.0.0.1:8081 127.0.0.1:8081", self.TEXT)
        self.assertIn("ExitOnForwardFailure no", self.TEXT)
        # 手动那条路也留着（没有 ssh config 的人还能用）
        self.assertIn("ssh -N -L 127.0.0.1:8081:127.0.0.1:8081", self.TEXT)


if __name__ == "__main__":
    unittest.main()
