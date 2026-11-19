"""把家里的数据迁到云上：库检查、快照、migrate-data.sh 的换库与回滚、sync-from-home.sh 的保护。

migrate-data.sh 用假的 systemctl / runuser / curl 在临时目录里真的跑一遍（真的 SQLite 库、真的复制），
检查：默认不改东西、拿错文件拒绝、换完行数对得上、任何一步失败都把快照放回去。"""
from __future__ import annotations

import getpass
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, ROOT.as_posix())

from server import auth as auth_mod          # noqa: E402
from server.db import Database               # noqa: E402

CLOUD = ROOT / "deploy" / "cloud"
sys.path.insert(0, CLOUD.as_posix())
import dbcheck                               # noqa: E402


def make_db(path: Path, students: int = 2, scores: int = 3, admins: int = 1) -> Path:
    """一个像样的库：几个账号、几条成绩（用真的 Database 和 AuthService 建，和线上同一套表）。"""
    db = Database(path)
    svc = auth_mod.AuthService(db)
    for i in range(admins):
        svc.create_user("A%03d" % i, "管理员%d" % i, password="Ready2026x", role="admin", must_change=False)
    for i in range(students):
        svc.create_user("S%03d" % i, "学生%d" % i, password="Ready2026x")
    for i in range(scores):
        db.insert_score({"bank_title": "测试", "score": 10 * i, "nickname": "n%d" % i})
    db._conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    db._conn.close()
    return path


class TestDbcheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def test_inspect_counts_what_is_in_the_database(self):
        info = dbcheck.inspect(make_db(self.dir / "a.db", students=3, scores=4, admins=2))
        self.assertEqual(info["integrity"], "ok")
        self.assertEqual(info["counts"]["users"], 5)
        self.assertEqual(info["counts"]["scores"], 4)
        self.assertEqual(info["roles"], {"admin": 2, "student": 3})
        self.assertIsNotNone(info["newest"]["score"])

    def test_inspect_is_read_only(self):
        path = make_db(self.dir / "a.db")
        before = path.read_bytes()
        dbcheck.inspect(path)
        self.assertEqual(path.read_bytes(), before)

    def test_a_file_that_is_not_a_database_is_refused(self):
        junk = self.dir / "junk.db"
        junk.write_bytes(b"this is not sqlite" * 100)
        done = subprocess.run([sys.executable, str(CLOUD / "dbcheck.py"), "inspect", str(junk)], capture_output=True, text=True)
        self.assertNotEqual(done.returncode, 0)

    def test_the_app_can_open_it_and_the_original_is_untouched(self):
        path = make_db(self.dir / "a.db")
        before = path.read_bytes()
        result = dbcheck.open_with_app(path, ROOT)
        self.assertTrue(result["opens"])
        self.assertEqual(path.read_bytes(), before, "检查只能在临时副本上做")

    def test_an_old_database_is_upgraded_in_the_copy_without_losing_rows(self):
        path = make_db(self.dir / "old.db")
        con = sqlite3.connect(path)
        con.execute("PRAGMA user_version = 0")
        con.commit()
        con.close()
        result = dbcheck.open_with_app(path, ROOT)
        self.assertEqual(result["user_version_before"], 0)
        self.assertGreaterEqual(result["user_version_after"], 2)
        self.assertEqual(dbcheck.inspect(path)["user_version"], 0, "原文件不升级")

    def test_snapshot_is_a_consistent_copy_that_passes_the_integrity_check(self):
        src = make_db(self.dir / "a.db", students=4)
        out = dbcheck.snapshot(src, self.dir / "snap" / "s.db")
        self.assertEqual(out["counts"]["users"], 5)
        self.assertEqual(dbcheck.inspect(Path(out["snapshot"]))["integrity"], "ok")
        self.assertFalse(list((self.dir / "snap").glob("*.partial")))


class FakeHost:
    """假的 systemctl / runuser / curl：记下调用；health 和 banks 的结果可以改。"""

    def __init__(self, base: Path):
        self.bin = base / "bin"
        self.bin.mkdir()
        self.calls = base / "calls.log"
        self.state = base / "state"
        self.state.mkdir()
        self.write("systemctl", 'echo "systemctl $*" >> "%s"\n'
                                'case "$1" in stop) echo stopped > "%s/service";; start) '
                                '[ -e "%s/start-fails" ] && exit 1; echo running > "%s/service";; esac\nexit 0'
                   % (self.calls, self.state, self.state, self.state))
        self.write("runuser", 'while [ "$1" != "--" ]; do shift; done; shift; exec "$@"')
        self.write("curl", 'url=""; for a in "$@"; do case "$a" in http*) url="$a";; esac; done\n'
                           'echo "curl $url" >> "%s"\n'
                           'case "$url" in\n'
                           '  */api/health) [ -e "%s/unhealthy" ] && exit 22; [ "$(cat "%s/service" 2>/dev/null)" = running ] || exit 22; echo "{}"; exit 0;;\n'
                           '  */api/banks) printf "%%s" "$(cat "%s/banks-code" 2>/dev/null || echo 401)"; exit 0;;\n'
                           'esac\nexit 0' % (self.calls, self.state, self.state, self.state))

    def write(self, name: str, body: str):
        path = self.bin / name
        path.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8")
        path.chmod(0o755)

    def log(self) -> list[str]:
        return self.calls.read_text(encoding="utf-8").splitlines() if self.calls.exists() else []


class TestMigrateData(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.data = self.base / "data"
        self.data.mkdir()
        self.snaps = self.base / "snaps"
        self.host = FakeHost(self.base)
        (self.host.state / "service").write_text("running", encoding="utf-8")
        (self.data / ".lexica-data").write_text("", encoding="utf-8")
        # 云上现在：新装的，只有一个临时管理员
        self.cloud_db = make_db(self.data / "app.db", students=0, scores=0, admins=1)
        # 家里的备份：有学生有成绩
        self.home = make_db(self.base / "app-home.db", students=5, scores=7, admins=1)
        self.env = dict(os.environ,
                        PATH="%s:%s" % (self.host.bin, os.environ["PATH"]),
                        WP_FAMILY_DATA_DIR=str(self.data), WP_FAMILY_INSTALL_DIR=str(ROOT),
                        WP_FAMILY_USER=getpass.getuser(), WP_MIGRATION_DIR=str(self.snaps))

    def run_script(self, *args, check_root=False):
        # 脚本要求 root；测试里用一个只改掉 id 检查的副本，其余逻辑原样
        text = (CLOUD / "migrate-data.sh").read_text(encoding="utf-8")
        patched = self.base / "migrate-data.sh"
        patched.write_text(text.replace("[[ $(id -u) -eq 0 ]] ||", "true ||") if not check_root else text, encoding="utf-8")
        (self.base / "dbcheck.py").write_text((CLOUD / "dbcheck.py").read_text(encoding="utf-8"), encoding="utf-8")
        return subprocess.run(["bash", str(patched), *map(str, args)], env=self.env, capture_output=True, text=True)

    def counts(self, path: Path) -> dict:
        return dbcheck.inspect(path)["counts"]

    def test_by_default_nothing_is_changed(self):
        before = self.cloud_db.read_bytes()
        done = self.run_script(self.home)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("只是检查", done.stdout)
        self.assertEqual(self.cloud_db.read_bytes(), before)
        self.assertFalse(any(c.startswith("systemctl stop") for c in self.host.log()), "检查不能停服务")
        self.assertFalse(self.snaps.exists())

    def test_the_check_shows_what_would_be_lost_and_gained(self):
        done = self.run_script(self.home)
        self.assertIn("云上现在", done.stdout)
        self.assertIn("备份", done.stdout)
        self.assertIn("会被备份里的替换", done.stderr + done.stdout)

    def test_apply_replaces_the_database_and_keeps_a_snapshot_of_the_old_one(self):
        done = self.run_script(self.home, "--apply")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual(self.counts(self.cloud_db)["users"], 6)
        self.assertEqual(self.counts(self.cloud_db)["scores"], 7)
        snaps = list(self.snaps.glob("before-migration-*.db"))
        self.assertEqual(len(snaps), 1)
        self.assertEqual(self.counts(snaps[0])["users"], 1, "快照是换之前云上的库")
        self.assertEqual((self.host.state / "service").read_text(encoding="utf-8").strip(), "running")
        log = self.host.log()
        self.assertLess(log.index("systemctl stop word-puzzle-family"), log.index("systemctl start word-puzzle-family"))
        self.assertFalse((self.data / "app.db.incoming").exists())

    def test_stale_wal_files_of_the_old_database_are_removed(self):
        (self.data / "app.db-wal").write_bytes(b"stale")
        (self.data / "app.db-shm").write_bytes(b"stale")
        self.assertEqual(self.run_script(self.home, "--apply").returncode, 0)
        self.assertFalse((self.data / "app.db-wal").exists() and (self.data / "app.db-wal").read_bytes() == b"stale")
        self.assertFalse((self.data / "app.db-shm").exists() and (self.data / "app.db-shm").read_bytes() == b"stale")

    def test_builtin_banks_added_by_the_app_on_start_are_not_a_mismatch(self):
        """备份里缺内置题库时，后端启动会补上；这不是数据对不上。人产生的数据（账号、成绩……）才必须一行不差。"""
        script = (CLOUD / "migrate-data.sh").read_text(encoding="utf-8")
        self.assertIn('if t == "banks" else got != want', script)
        self.assertIn("got < want", script, "题库变少才是出了问题")

    def test_the_data_directory_marker_survives(self):
        self.run_script(self.home, "--apply")
        self.assertTrue((self.data / ".lexica-data").exists())

    def test_an_empty_database_is_refused_because_it_is_probably_the_wrong_file(self):
        empty = make_db(self.base / "empty.db", students=0, scores=0, admins=0)
        before = self.cloud_db.read_bytes()
        done = self.run_script(empty, "--apply")
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("一个账号也没有", done.stderr)
        self.assertEqual(self.cloud_db.read_bytes(), before)

    def test_a_file_that_is_not_a_database_is_refused_before_anything_stops(self):
        junk = self.base / "junk.db"
        junk.write_bytes(b"not a database" * 50)
        done = self.run_script(junk, "--apply")
        self.assertNotEqual(done.returncode, 0)
        self.assertFalse(any(c.startswith("systemctl stop") for c in self.host.log()))

    def test_a_missing_file_and_unknown_flags_are_refused(self):
        self.assertNotEqual(self.run_script(self.base / "nope.db").returncode, 0)
        self.assertNotEqual(self.run_script(self.home, "--force").returncode, 0)
        self.assertNotEqual(self.run_script().returncode, 0)

    def test_it_refuses_a_directory_that_is_not_a_lexica_data_directory(self):
        (self.data / ".lexica-data").unlink()
        done = self.run_script(self.home, "--apply")
        self.assertNotEqual(done.returncode, 0)
        self.assertIn(".lexica-data", done.stderr)

    def test_if_the_service_does_not_come_back_the_old_database_is_put_back(self):
        old = self.counts(self.cloud_db)
        (self.host.state / "banks-code").write_text("200", encoding="utf-8")   # 换完之后未登录竟然能读题库
        done = self.run_script(self.home, "--apply")
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("已回滚", done.stderr)
        self.assertEqual(self.counts(self.cloud_db), old, "回滚之后应该是换之前的库")

    def test_if_the_health_check_never_passes_it_rolls_back(self):
        # 起服务之后一直不健康：把等待时间缩短，别让测试真的等 30 秒
        text = (CLOUD / "migrate-data.sh").read_text(encoding="utf-8").replace("seq 1 30", "seq 1 2")
        patched = self.base / "migrate-data.sh"
        patched.write_text(text.replace("[[ $(id -u) -eq 0 ]] ||", "true ||"), encoding="utf-8")
        (self.base / "dbcheck.py").write_text((CLOUD / "dbcheck.py").read_text(encoding="utf-8"), encoding="utf-8")
        old = self.counts(self.cloud_db)
        (self.host.state / "unhealthy").write_text("", encoding="utf-8")
        done = subprocess.run(["bash", str(patched), str(self.home), "--apply"], env=self.env, capture_output=True, text=True)
        self.assertNotEqual(done.returncode, 0)
        self.assertEqual(self.counts(self.cloud_db), old)

    def test_if_the_service_cannot_start_it_rolls_back(self):
        old = self.counts(self.cloud_db)
        (self.host.state / "start-fails").write_text("", encoding="utf-8")
        done = self.run_script(self.home, "--apply")
        self.assertNotEqual(done.returncode, 0)
        self.assertEqual(self.counts(self.cloud_db), old)

    def test_it_insists_on_root_in_real_use(self):
        text = (CLOUD / "migrate-data.sh").read_text(encoding="utf-8")
        self.assertIn("[[ $(id -u) -eq 0 ]]", text)
        if os.geteuid() != 0:
            done = self.run_script(self.home, check_root=True)
            self.assertNotEqual(done.returncode, 0)
            self.assertIn("root", done.stderr)


class TestSyncFromHome(unittest.TestCase):
    TEXT = (CLOUD / "sync-from-home.sh").read_text(encoding="utf-8")

    def run_script(self, *args, **env):
        base = {k: v for k, v in os.environ.items() if k not in ("HOME_SSH", "HOME_CTID", "HOME_BACKUP_DIR", "CLOUD_SSH")}
        return subprocess.run(["bash", str(CLOUD / "sync-from-home.sh"), *args], env=dict(base, **env), capture_output=True, text=True)

    def test_it_parses(self):
        done = subprocess.run(["bash", "-n", str(CLOUD / "sync-from-home.sh")], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_private_values_come_from_the_environment_not_the_repo(self):
        for name in ("HOME_SSH", "HOME_CTID", "HOME_BACKUP_DIR", "CLOUD_SSH"):
            self.assertIn(name, self.TEXT)
        self.assertNotRegex(self.TEXT, r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
        self.assertNotRegex(self.TEXT, r"CTID=\d")

    def test_cutover_needs_an_explicit_yes_and_rehearse_never_accepts_it(self):
        env = dict(HOME_SSH="root@x", HOME_CTID="1", HOME_BACKUP_DIR="/b", CLOUD_SSH="c")
        self.assertIn("--yes", self.run_script("cutover", **env).stderr)
        self.assertIn("只用于 cutover", self.run_script("rehearse", "--yes", **env).stderr)

    def test_missing_settings_and_bad_values_are_refused_before_any_connection(self):
        self.assertNotEqual(self.run_script("rehearse").returncode, 0)
        self.assertNotEqual(self.run_script().returncode, 0)
        bad = dict(HOME_SSH="root@x", HOME_CTID="1;rm", HOME_BACKUP_DIR="/b", CLOUD_SSH="c")
        self.assertIn("HOME_CTID", self.run_script("rehearse", **bad).stderr)
        bad = dict(HOME_SSH="root@x", HOME_CTID="1", HOME_BACKUP_DIR="b d", CLOUD_SSH="c")
        self.assertIn("HOME_BACKUP_DIR", self.run_script("rehearse", **bad).stderr)

    def test_the_home_service_is_restarted_when_a_cutover_fails_and_stays_stopped_when_it_works(self):
        self.assertIn("HOME_STOPPED=1", self.TEXT)
        self.assertIn("HOME_STOPPED=0", self.TEXT)
        self.assertIn("systemctl start $SERVICE", self.TEXT)
        self.assertIn("trap cleanup EXIT", self.TEXT)

    def test_the_data_does_not_land_on_the_workstation_and_the_copy_on_the_cloud_is_removed(self):
        self.assertIn("scp -3", self.TEXT)
        self.assertIn("rm -f $REMOTE_COPY", self.TEXT)
        self.assertIn("is-active", self.TEXT, "停服务之后要确认真的停了，再备份")

    def test_the_backup_is_taken_after_the_service_is_stopped_in_a_cutover(self):
        self.assertLess(self.TEXT.index("systemctl stop $SERVICE"), self.TEXT.index("backup.py"))


if __name__ == "__main__":
    unittest.main()
