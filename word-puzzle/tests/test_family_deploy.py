"""家庭版部署文件的静态检查：只监听本机、请求头被覆盖、限速和请求体上限、
安装脚本的前置检查与自检；有 nginx 的机器上还会真的跑一遍 nginx -t。"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAMILY = ROOT / "deploy" / "family"
UNIT = (FAMILY / "systemd" / "word-puzzle-family.service").read_text(encoding="utf-8")
CONF = (FAMILY / "nginx" / "word-puzzle-family.conf").read_text(encoding="utf-8")
PROXY = (FAMILY / "nginx" / "proxy.inc").read_text(encoding="utf-8")
INSTALL = (FAMILY / "install.sh").read_text(encoding="utf-8")
GUIDE = (FAMILY / "部署说明.md").read_text(encoding="utf-8")
PVE = (FAMILY / "PVE容器部署.md").read_text(encoding="utf-8")
NGINX = shutil.which("nginx")


class TestSystemdUnit(unittest.TestCase):
    def test_login_is_on_and_cookies_are_secure(self):
        for line in ("Environment=WP_AUTH=1", "Environment=WP_COOKIE_SECURE=1",
                     "Environment=WP_HOST=127.0.0.1", "Environment=WP_PUBLIC_HOME_URL=@PUBLIC_URL@"):
            self.assertIn(line, UNIT)

    def test_hardening_is_kept_and_the_service_cannot_write_its_code(self):
        for line in ("NoNewPrivileges=true", "ProtectSystem=strict", "PrivateTmp=true", "ProtectHome=true"):
            self.assertIn(line, UNIT)
        self.assertIn("ReadWritePaths=@DATA_DIR@ @INSTALL_DIR@/var", UNIT)


class TestNginx(unittest.TestCase):
    def test_listens_on_loopback_only(self):
        listens = re.findall(r"^\s*listen\s+([^;]+);", CONF, re.M)
        self.assertEqual(listens, ["127.0.0.1:@NGINX_PORT@"])

    def test_request_headers_from_the_client_are_overridden(self):
        self.assertIn("proxy_set_header X-Forwarded-Host $http_host;", PROXY)
        self.assertIn("proxy_set_header X-Forwarded-Proto https;", PROXY)
        self.assertIn("proxy_set_header Host $http_host;", PROXY)
        self.assertNotIn("$host;", PROXY)
        self.assertNotIn("$proxy_add_x_forwarded_for", PROXY, "转发链里不要带上客户端自己填的 X-Forwarded-For")

    def test_every_proxied_location_uses_the_shared_headers(self):
        proxied = re.findall(r"location [^{]+\{[^}]*proxy_pass[^}]*\}", CONF, re.S)
        self.assertGreaterEqual(len(proxied), 4)
        for block in proxied:
            self.assertIn("include @PROXY_INC@;", block)

    def test_small_bodies_by_default_and_large_only_where_admins_upload(self):
        self.assertRegex(CONF, r"server \{[^{}]*client_max_body_size 2m;")
        for path in ("/word-puzzle/api/materials", "/word-puzzle/api/admin/import"):
            block = re.search(r"location = %s \{(.*?)\n    \}" % re.escape(path), CONF, re.S)
            self.assertIsNotNone(block, path)
            self.assertIn("client_max_body_size 32m;", block.group(1))

    def test_login_is_rate_limited(self):
        self.assertIn("limit_req_zone $server_name zone=wp_family_login", CONF)
        block = re.search(r"location = /word-puzzle/api/auth/login \{(.*?)\n    \}", CONF, re.S).group(1)
        self.assertIn("limit_req zone=wp_family_login", block)
        self.assertIn("limit_req_status 429;", block)

    def test_scanner_targets_are_refused_and_root_redirects(self):
        for needle in (r"location ~ /\.(?!well-known/) { return 404; }", "AGENTS|CLAUDE|README", "env)$",
                       "location = / { return 302 /word-puzzle/; }"):
            self.assertIn(needle, CONF)

    def test_no_regex_location_is_shadowed_by_a_caret_tilde_prefix(self):
        """有 ^~ 前缀的 location 会让同一路径下的正则 location 永远不生效，这类写法等于没写。"""
        for pattern in re.findall(r"location ~\*? (\S+) ", CONF):
            self.assertFalse(pattern.startswith("^/word-puzzle/") or pattern.startswith("^/shared/"), pattern)

    def test_static_files_are_revalidated_not_cached_for_days(self):
        self.assertNotIn("expires", CONF)
        self.assertNotIn("max-age", CONF)
        self.assertGreaterEqual(CONF.count('add_header Cache-Control "no-cache";'), 2)

    @unittest.skipUnless(NGINX, "本机没有 nginx，跳过 nginx -t")
    def test_the_rendered_config_passes_nginx_t(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            install = tmp / "srv"
            (install / "web").mkdir(parents=True)
            (install / "shared").mkdir()
            inc = tmp / "proxy.inc"
            inc.write_text(PROXY, encoding="utf-8")
            conf = (CONF.replace("@INSTALL_DIR@", str(install)).replace("@PORT@", "8766")
                    .replace("@NGINX_PORT@", "18081").replace("@PROXY_INC@", str(inc))
                    .replace("/var/log/nginx/", str(tmp) + "/"))
            site = tmp / "site.conf"
            site.write_text(conf, encoding="utf-8")
            main = tmp / "nginx.conf"
            main.write_text("pid %s/n.pid;\nerror_log %s/e.log;\nevents {}\nhttp {\n"
                            "  client_body_temp_path %s/b; proxy_temp_path %s/p; fastcgi_temp_path %s/f;\n"
                            "  uwsgi_temp_path %s/u; scgi_temp_path %s/s;\n  include %s;\n}\n"
                            % ((tmp,) * 7 + (site,)), encoding="utf-8")
            proc = subprocess.run([NGINX, "-t", "-c", str(main), "-p", str(tmp)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)


class TestInstaller(unittest.TestCase):
    def test_script_is_valid_bash(self):
        proc = subprocess.run(["bash", "-n", str(FAMILY / "install.sh")], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_public_url_is_mandatory_and_must_be_https(self):
        self.assertIn('[[ -n "$PUBLIC_URL" ]] || die', INSTALL)
        self.assertIn("^https://", INSTALL)

    def test_every_placeholder_in_the_templates_is_substituted(self):
        used = set(re.findall(r"@([A-Z_]+)@", UNIT + CONF))
        self.assertGreaterEqual(len(used), 6)
        for name in used:
            self.assertIn("@%s@" % name, INSTALL, "安装脚本没有替换 @%s@" % name)

    def test_the_installer_checks_that_anonymous_access_is_refused(self):
        self.assertIn('[[ "$code" == "401" ]]', INSTALL)
        self.assertIn("auth_enabled", INSTALL)

    def test_it_does_not_touch_tailscale_or_the_lan_edition(self):
        code = "\n".join(l for l in INSTALL.splitlines() if not l.lstrip().startswith("#"))
        self.assertNotIn("tailscale up", code)
        self.assertNotRegex(code, r"(?m)^\s*(sudo )?tailscale ")
        for lan in ("/srv/word-puzzle\n", "/srv/word-puzzle\"", "/var/lib/word-puzzle\n", "SITE_NAME=word-puzzle\n"):
            self.assertNotIn(lan, code)

    def test_dotfiles_are_never_copied_into_the_served_tree(self):
        self.assertIn("--exclude '.*'", INSTALL)
        self.assertIn("! -name '.*'", INSTALL)
        self.assertIn("--exclude 'var/'", INSTALL)

    def test_admin_wrapper_runs_as_the_service_user_not_root(self):
        self.assertIn("runuser -u $RUN_USER", INSTALL)
        self.assertIn("python3 -m server.admin", INSTALL)

    def test_existing_database_is_never_replaced(self):
        self.assertNotRegex(INSTALL, r"rm\s+-rf?\s+\S*DATA_DIR")
        self.assertIn("不会覆盖已有数据库", INSTALL)


class TestGuide(unittest.TestCase):
    def test_guide_covers_the_safety_points(self):
        for text in ("不要装在 PVE 宿主机上", "主机名别叫", "没装 Tailscale 的手机", "funnel reset",
                     "wp-family-admin", "/.env", "初始密码", "备份", "连续输错 5 次"):
            self.assertIn(text, GUIDE)


class TestPveContainerGuide(unittest.TestCase):
    def test_guide_is_linked_from_the_main_guide(self):
        self.assertIn("PVE容器部署.md", GUIDE)

    def test_the_container_is_unprivileged_and_has_the_tun_device(self):
        for text in ("--unprivileged 1", "nesting=1,keyctl=1", "pct set CTID --dev0 /dev/net/tun",
                     "lxc.cgroup2.devices.allow: c 10:200 rwm",
                     "lxc.mount.entry: /dev/net/tun dev/net/tun none bind,create=file"):
            self.assertIn(text, PVE)

    def test_the_operational_traps_are_covered(self):
        for text in ("Disable key expiry", "180 天", "Rename tailnet", "HTTPS Certificates",
                     "tailscale funnel reset", "vzdump", "pct push", "pct enter",
                     "没装 Tailscale 的手机", "python3 -m http.server", "不要给容器开 SSH"):
            self.assertIn(text, PVE)

    def test_it_is_ordered_so_the_public_url_is_known_before_installing(self):
        self.assertLess(PVE.index("四、先装 Tailscale"), PVE.index("五、把代码放进容器并安装"))
        self.assertLess(PVE.index("五、把代码放进容器并安装"), PVE.index("六、上线前检查，然后开 Funnel"))
        # 开 Funnel 的命令只出现在「开 Funnel」那一节之后
        self.assertGreater(PVE.index("tailscale funnel --bg 8081"), PVE.index("六、上线前检查"))

    def test_the_commands_match_the_installer(self):
        for text in ("word-puzzle/deploy/family/install.sh", "WP_PUBLIC_URL=", "wp-family-admin create-admin",
                     "wp-family-admin import", "127.0.0.1:8081", "127.0.0.1:8766"):
            self.assertIn(text, PVE)
        self.assertIn("wp-family-admin", INSTALL)


if __name__ == "__main__":
    unittest.main()
