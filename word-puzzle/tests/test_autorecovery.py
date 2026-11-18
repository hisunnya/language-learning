"""停电 / 重启后自动恢复：服务单元、数据目录保护、看门狗（用假的 curl / systemctl / tailscale 真跑一遍）、宿主机脚本。"""
from __future__ import annotations

import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAMILY = ROOT / "deploy" / "family"
UNIT = (FAMILY / "systemd" / "word-puzzle-family.service").read_text(encoding="utf-8")
INSTALL = (FAMILY / "install.sh").read_text(encoding="utf-8")
WATCHDOG = (FAMILY / "watchdog.sh").read_text(encoding="utf-8")
HOST = (FAMILY / "host-autostart.sh").read_text(encoding="utf-8")


class TestUnit(unittest.TestCase):
    def test_it_never_gives_up_and_waits_for_the_data_mount(self):
        self.assertIn("Restart=always", UNIT)
        self.assertIn("StartLimitIntervalSec=0", UNIT)
        self.assertIn("RequiresMountsFor=@DATA_DIR@", UNIT)

    def test_it_refuses_to_start_on_an_empty_data_directory(self):
        self.assertIn("ExecStartPre=/bin/sh -c 'test -e @DATA_DIR@/.lexica-data ||", UNIT)
        self.assertIn("拒绝启动", UNIT, "日志里要写明原因，回家的人一眼能看懂")

    def test_the_installer_places_the_marker_only_when_the_data_is_really_there(self):
        self.assertIn('if [[ -f "$DATA_DIR/app.db" || ! -e "/etc/systemd/system/$SITE_NAME.service" ]]; then', INSTALL)
        self.assertIn('touch "$DATA_DIR/.lexica-data"', INSTALL)
        self.assertLess(INSTALL.index('touch "$DATA_DIR/.lexica-data"'), INSTALL.index('systemctl restart "$SITE_NAME"'),
                        "标记要在重启服务之前放好，否则服务第一次启动就被自己拒绝")

    def test_the_installer_installs_and_enables_the_watchdog(self):
        self.assertIn("lexica-watchdog.timer", INSTALL)
        self.assertIn("systemctl enable --now lexica-watchdog.timer", INSTALL)
        self.assertIn('"${WP_FUNNEL_KEEP:-}" == "1"', INSTALL)
        self.assertTrue((FAMILY / "systemd" / "lexica-watchdog.timer").exists())

    def test_funnel_is_never_kept_open_unless_the_owner_asked_for_it(self):
        """公网入口是你明确开的：看门狗只在存在 funnel-keep 文件时才管它，安装时默认不创建这个文件。"""
        self.assertIn('[[ -e "$KEEP_FILE" ]] || exit 0', WATCHDOG)
        self.assertNotIn("touch /etc/lexica/funnel-keep\n", INSTALL.replace('  touch /etc/lexica/funnel-keep\n  echo', ''), "不能无条件创建")


class WatchdogCase(unittest.TestCase):
    """在一个临时目录里放假的命令，真的跑 watchdog.sh，看它调用了什么。"""

    def run_watchdog(self, *, healthy="yes", backend_healthy="yes", service_active="yes", nginx_active="yes",
                     funnel="", keep=False, tailscale_state="Running", tailscaled_active="yes"):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            bin_dir = tmp / "bin"
            bin_dir.mkdir()
            calls = tmp / "calls.log"
            (tmp / "funnel.txt").write_text(funnel, encoding="utf-8")

            def stub(name, body):
                path = bin_dir / name
                path.write_text("#!/usr/bin/env bash\n" + body, encoding="utf-8")
                path.chmod(path.stat().st_mode | stat.S_IEXEC)

            stub("curl", 'for a in "$@"; do case "$a" in *:8081/*) [[ "%s" == yes ]] && exit 0 || exit 22;; *:8766/*) [[ "%s" == yes ]] && exit 0 || exit 22;; esac; done; exit 22\n' % (healthy, backend_healthy))
            stub("systemctl", 'echo "systemctl $*" >> "%s"\n'
                 'if [[ "$1" == is-active ]]; then\n'
                 '  case "$3" in word-puzzle-family) [[ "%s" == yes ]];; nginx) [[ "%s" == yes ]];; tailscaled) [[ "%s" == yes ]];; esac\n'
                 '  exit $?\nfi\nexit 0\n' % (calls, service_active, nginx_active, tailscaled_active))
            stub("tailscale", 'echo "tailscale $*" >> "%s"\n'
                 'case "$1 $2" in\n'
                 '  "funnel status") cat "%s";;\n'
                 '  "status --json") echo \'{"BackendState": "%s"}\';;\n'
                 'esac\nexit 0\n' % (calls, tmp / "funnel.txt", tailscale_state))
            stub("sleep", "exit 0\n")
            script = tmp / "watchdog.sh"
            script.write_text(WATCHDOG.replace("@SITE_NAME@", "word-puzzle-family").replace("@NGINX_PORT@", "8081").replace("@PORT@", "8766"), encoding="utf-8")
            keep_file = tmp / "funnel-keep"
            if keep:
                keep_file.write_text("", encoding="utf-8")
            env = dict(os.environ, PATH=str(bin_dir) + ":" + os.environ["PATH"], LEXICA_FUNNEL_KEEP=str(keep_file))
            done = subprocess.run(["bash", str(script)], env=env, capture_output=True, text=True, timeout=60)
            log = calls.read_text(encoding="utf-8").splitlines() if calls.exists() else []
            return done, log


FUNNEL_ON = "https://lexica.example.ts.net (Funnel on)\n|-- / proxy http://127.0.0.1:8081\n"


class TestWatchdog(WatchdogCase):
    def test_a_healthy_site_is_left_alone(self):
        done, log = self.run_watchdog(funnel=FUNNEL_ON, keep=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual([c for c in log if "start" in c or "restart" in c or "--bg" in c], [])

    def test_a_stopped_backend_is_started(self):
        done, log = self.run_watchdog(healthy="no", backend_healthy="no", service_active="no")
        self.assertIn("systemctl start word-puzzle-family", log)
        self.assertNotIn("systemctl restart word-puzzle-family", log)

    def test_a_backend_that_runs_but_does_not_answer_is_restarted(self):
        done, log = self.run_watchdog(healthy="no", backend_healthy="no", service_active="yes")
        self.assertIn("systemctl restart word-puzzle-family", log)

    def test_a_stopped_nginx_is_started(self):
        done, log = self.run_watchdog(healthy="no", backend_healthy="yes", nginx_active="no")
        self.assertIn("systemctl start nginx", log)
        self.assertNotIn("systemctl restart word-puzzle-family", log, "后端是好的就不要动它")

    def test_funnel_is_reopened_when_it_is_off_and_the_owner_wants_it_kept(self):
        done, log = self.run_watchdog(funnel="No serve config\n", keep=True)
        self.assertIn("tailscale funnel --bg 8081", log)

    def test_funnel_is_not_touched_when_the_owner_did_not_ask_for_it(self):
        done, log = self.run_watchdog(funnel="No serve config\n", keep=False)
        self.assertFalse([c for c in log if "funnel --bg" in c], log)
        self.assertFalse([c for c in log if c.startswith("tailscale")], "连 tailscale 都不该碰")

    def test_funnel_that_is_already_on_is_not_reapplied(self):
        done, log = self.run_watchdog(funnel=FUNNEL_ON, keep=True)
        self.assertFalse([c for c in log if "funnel --bg" in c])

    def test_it_waits_for_tailscale_and_does_not_open_funnel_while_offline(self):
        done, log = self.run_watchdog(funnel="No serve config\n", keep=True, tailscale_state="NeedsLogin")
        self.assertEqual(done.returncode, 0)
        self.assertFalse([c for c in log if "funnel --bg" in c], "没连上（或要重新登录）时不要硬开")
        self.assertIn("还没连上", done.stdout)

    def test_a_stopped_tailscaled_is_started_first(self):
        done, log = self.run_watchdog(funnel="No serve config\n", keep=True, tailscaled_active="no")
        self.assertIn("systemctl start tailscaled", log)
        self.assertLess(log.index("systemctl start tailscaled"), log.index("tailscale funnel --bg 8081"))


class TestHostScript(unittest.TestCase):
    def test_it_sets_autostart_order_and_delay_and_checks_the_data_disks(self):
        self.assertIn("pct set \"$CTID\" --onboot 1 --startup order=2,up=45", HOST)
        self.assertIn("pve-guests", HOST)
        self.assertIn("nofail", HOST)
        self.assertIn("mountpoint -q", HOST)

    def test_it_takes_the_container_id_from_the_argument_or_the_private_env_file(self):
        self.assertIn("LEXICA_CTID", HOST)
        self.assertNotRegex(HOST, r"CTID=\"?\d")

    def test_both_scripts_parse(self):
        for name in ("watchdog.sh", "host-autostart.sh", "install.sh"):
            done = subprocess.run(["bash", "-n", str(FAMILY / name)], capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, name + done.stderr)


if __name__ == "__main__":
    unittest.main()
