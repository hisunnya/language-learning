"""云服务器（生产）部署文件的检查：公网入口只认自己的域名、没有证书不走明文、客户端自带的转发头不被信任、
SSH 加固不会把人锁在外面。render-nginx.sh 用假的 nginx / systemctl 真的跑一遍，看生成出来的配置。"""
from __future__ import annotations

import os
import re
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLOUD = ROOT / "deploy" / "cloud"
FAMILY = ROOT / "deploy" / "family"
SCRIPTS = ("install.sh", "render-nginx.sh", "enable-tls.sh", "harden.sh")
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


class TestGuide(unittest.TestCase):
    TEXT = (CLOUD / "部署说明.md").read_text(encoding="utf-8") if (CLOUD / "部署说明.md").exists() else ""

    def test_the_guide_covers_the_steps_and_the_rules_around_them(self):
        for needle in ("install.sh", "harden.sh", "enable-tls.sh", "ssh -L 8081:127.0.0.1:8081",
                       "备案", "流量穿透", "快照", "WP_ACME_STAGING"):
            self.assertIn(needle, self.TEXT)


if __name__ == "__main__":
    unittest.main()
