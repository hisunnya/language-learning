"""家庭版部署文件的静态检查：只监听本机、请求头被覆盖、限速和请求体上限、
安装脚本的前置检查与自检；有 nginx 的机器上还会真的跑一遍 nginx -t。"""
from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import sys
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
CHECK_URL = FAMILY / "check-url.sh"


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
        for text in ("--unprivileged 1", "nesting=1,keyctl=1", "pct set $CTID --dev0 /dev/net/tun",
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


def code_blocks(markdown: str) -> list[str]:
    return re.findall(r"```[a-z]*\n(.*?)```", markdown, re.S)


class TestPveCommandsCanBePasted(unittest.TestCase):
    """第一次实际使用时，有人把占位符 CTID 原样粘进了命令（报 vmid type check failed）：
    文档里所有命令都必须能直接复制，不能留需要手工替换的字样。"""

    def test_no_code_block_contains_a_bare_placeholder(self):
        for block in code_blocks(PVE):
            for line in block.splitlines():
                code = line.split("#", 1)[0]
                self.assertIsNone(re.search(r"(?<![$A-Za-z_])CTID(?![A-Za-z_=])", code), line)
                self.assertNotRegex(code, r"<[^>\n]*(模板|文件名|备份存储|你的)[^>\n]*>", line)

    def test_the_variable_is_defined_before_its_first_use_and_the_id_is_checked_for_conflicts(self):
        commands = "\n".join(code_blocks(PVE))
        self.assertLess(commands.index("qm list; pct list"), commands.index("CTID=120"))
        self.assertLess(commands.index("CTID=120"), commands.index("$CTID"))

    def test_the_public_url_is_read_from_tailscale_instead_of_being_retyped(self):
        commands = "\n".join(code_blocks(PVE))
        self.assertIn('WP_PUBLIC_URL="https://$(tailscale status --json', commands)
        self.assertIn('env WP_PUBLIC_URL="$WP_PUBLIC_URL" bash word-puzzle/deploy/family/install.sh', commands)
        self.assertLess(commands.index('WP_PUBLIC_URL="https://$(tailscale'), commands.index('env WP_PUBLIC_URL="$WP_PUBLIC_URL"'))

    def test_the_static_network_for_this_house_is_written_out(self):
        self.assertIn("--net0 name=eth0,bridge=vmbr0,ip=10.1.1.100/20,gw=10.1.1.1", PVE)
        self.assertIn("pct config $CTID", PVE)
        self.assertIn("ping -c 2 10.1.1.100", PVE)
        self.assertIn("DHCP 地址池", PVE)

    def test_the_template_and_storage_steps_come_before_creation(self):
        self.assertLess(PVE.index("pveam download local"), PVE.index("pct create"))
        self.assertLess(PVE.index("pvesm status"), PVE.index("pct create"))

    def test_the_errors_people_actually_hit_are_in_the_troubleshooting_table(self):
        table = PVE[PVE.index("## 十、常见问题"):PVE.index("## 十一、")]
        for text in ("type check ('integer') failed", "编号已存在", "存储不存在", "ping 10.1.1.1",
                     "--nameserver", "/dev/net/tun"):
            self.assertIn(text, table)

    def test_the_container_is_checked_for_network_before_tailscale(self):
        self.assertLess(PVE.index("ping -c 2 debian.org"), PVE.index("## 三、"))


class TestUrlStability(unittest.TestCase):
    """check-url.sh：用一个假的 tailscale 命令模拟各种情形。"""

    def run_check(self, dns_name, *args, env_extra=None, with_tailscale=True, status_json=None):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            if with_tailscale:
                payload = status_json if status_json is not None else json.dumps({"Self": {"DNSName": dns_name}})
                fake = tmp / "tailscale"
                fake.write_text("#!/bin/sh\ncat <<'JSON'\n%s\nJSON\n" % payload, encoding="utf-8")
                fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
            env = {"PATH": "%s:%s:/usr/bin:/bin" % (tmp, os.path.dirname(sys.executable)),
                   "WP_FAMILY_PUBLIC_URL_FILE": str(tmp / "none")}
            env.update(env_extra or {})
            proc = subprocess.run(["bash", str(CHECK_URL), *args], capture_output=True, text=True, env=env)
            return proc.returncode, proc.stdout + proc.stderr

    def test_matching_url_passes_ignoring_case_trailing_dot_scheme_and_port(self):
        for expected in ("https://lexica.tail705ad2.ts.net", "https://LEXICA.tail705ad2.ts.net:8443/word-puzzle/",
                         "lexica.tail705ad2.ts.net"):
            code, out = self.run_check("lexica.tail705ad2.ts.net.", expected)
            self.assertEqual(code, 0, out)
            self.assertIn("OK 网址一致", out)

    def test_a_dash_one_suffix_is_diagnosed_as_a_leftover_machine_record(self):
        code, out = self.run_check("lexica-1.tail705ad2.ts.net.", "https://lexica.tail705ad2.ts.net")
        self.assertEqual(code, 1)
        self.assertIn("网址变了", out)
        self.assertIn("旧的「lexica」记录", out)
        self.assertIn("tailscale set --hostname=lexica", out)

    def test_a_renamed_machine_and_a_renamed_tailnet_are_told_apart(self):
        code, out = self.run_check("pve03.tail705ad2.ts.net.", "https://lexica.tail705ad2.ts.net")
        self.assertEqual(code, 1)
        self.assertIn("机器名变了", out)
        code, out = self.run_check("lexica.cat-crocodile.ts.net.", "https://lexica.tail705ad2.ts.net")
        self.assertEqual(code, 1)
        self.assertIn("tailnet 名变了", out)

    def test_the_recorded_url_is_used_when_no_argument_is_given(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = Path(tmp) / "public-url"
            record.write_text("https://lexica.tail705ad2.ts.net\n", encoding="utf-8")
            env = {"WP_FAMILY_PUBLIC_URL_FILE": str(record)}
            self.assertEqual(self.run_check("lexica.tail705ad2.ts.net.", env_extra=env)[0], 0)
            self.assertEqual(self.run_check("other.tail705ad2.ts.net.", env_extra=env)[0], 1)

    def test_it_says_so_when_it_cannot_find_out(self):
        code, out = self.run_check("", "https://lexica.x.ts.net", with_tailscale=False)
        self.assertEqual(code, 2)
        self.assertIn("没有 tailscale 命令", out)
        code, out = self.run_check("", "https://lexica.x.ts.net", status_json="not json at all")
        self.assertEqual(code, 2)
        code, out = self.run_check("", "https://lexica.x.ts.net", status_json=json.dumps({"BackendState": "NeedsLogin"}))
        self.assertEqual(code, 2)
        self.assertIn("查不到本机的 Tailscale 域名", out)
        code, out = self.run_check("lexica.x.ts.net.")                    # 既没参数也没有记录
        self.assertEqual(code, 2)

    def test_installer_records_the_url_and_runs_the_check_without_failing_the_install(self):
        self.assertIn('printf \'%s\\n\' "$PUBLIC_URL" > "$DATA_DIR/public-url"', INSTALL)
        self.assertIn('check-url.sh" "$PUBLIC_URL" \\', INSTALL)
        self.assertRegex(INSTALL, r'check-url\.sh" "\$PUBLIC_URL" \\\n\s+\|\| warn ')

    def test_script_is_valid_bash(self):
        self.assertEqual(subprocess.run(["bash", "-n", str(CHECK_URL)]).returncode, 0)


class TestUrlStabilityGuide(unittest.TestCase):
    def test_the_guide_explains_what_changes_the_url_and_how_to_avoid_it(self):
        for text in ("Auto-generate from OS hostname", "lexica-1", "check-url.sh", "tailscale funnel status",
                     "删除旧的 `lexica` 记录", "Rename tailnet", "/var/lib/tailscale", "不要先建新的",
                     "我没有实测", "重新登录"):
            self.assertIn(text, PVE)

    def test_rebuild_order_deletes_the_old_record_before_registering_the_new_node(self):
        order = PVE[PVE.index("**3. 必须重建容器时的顺序"):PVE.index("**4. 每次重启")]
        self.assertLess(order.index("删除旧的 `lexica` 记录"), order.index("tailscale up --hostname=lexica"))
        self.assertLess(order.index("tailscale up --hostname=lexica"), order.index("check-url.sh"))
        self.assertLess(order.index("check-url.sh"), order.index("销毁旧容器"))

    def test_the_checklist_before_opening_funnel_includes_the_url_record(self):
        checklist = PVE[PVE.index("## 六、上线前检查"):PVE.index("## 七、")]
        self.assertIn("check-url.sh", checklist)
        self.assertIn("Auto-generate from OS hostname", checklist)

    def test_section_numbers_are_in_order(self):
        numbers = re.findall(r"^## ([一二三四五六七八九十]+)、", PVE, re.M)
        self.assertEqual(numbers, ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一"])


if __name__ == "__main__":
    unittest.main()
