"""数据库每日备份：在线备份、完整性检查、只保留最近 N 份、不碰别的文件。"""
from __future__ import annotations

import re
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAMILY = ROOT / "deploy" / "family"
sys.path.insert(0, str(FAMILY))

import backup                                  # noqa: E402


def make_db(path: Path, rows: int = 5):
    c = sqlite3.connect(path)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("CREATE TABLE t(id INTEGER PRIMARY KEY, v TEXT)")
    c.executemany("INSERT INTO t(v) VALUES (?)", [("行%d" % i,) for i in range(rows)])
    c.commit()
    return c          # 保持打开：模拟服务正在用（WAL 里还有没合并回主文件的数据）


class TestBackup(unittest.TestCase):
    def test_backup_contains_the_live_data_including_the_wal(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            live = make_db(tmp / "app.db")
            out = backup.backup(tmp / "app.db", tmp / "bk", keep=30, now=1_800_000_000)
            live.close()
            self.assertTrue(re.fullmatch(r"app-\d{8}_\d{6}\.db", out.name), out.name)
            rows = sqlite3.connect(out).execute("SELECT COUNT(*) FROM t").fetchone()[0]
            self.assertEqual(rows, 5)
            self.assertEqual([p.name for p in (tmp / "bk").iterdir()], [out.name])      # 没有残留的 .partial

    def test_only_the_newest_n_are_kept_and_foreign_files_are_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            make_db(tmp / "app.db").close()
            out = tmp / "bk"
            out.mkdir()
            (out / "notes.txt").write_text("别删我")
            (out / "app-old.sql").write_text("别删我")
            for i in range(5):
                backup.backup(tmp / "app.db", out, keep=3, now=1_800_000_000 + i * 86400)
            kept = sorted(p.name for p in out.glob("app-*.db"))
            self.assertEqual(len(kept), 3)
            self.assertEqual(kept, sorted(kept))
            self.assertTrue((out / "notes.txt").exists() and (out / "app-old.sql").exists())

    def test_missing_database_fails_loudly(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                backup.backup(Path(tmp) / "nope.db", Path(tmp) / "bk")

    def test_a_corrupt_source_never_leaves_a_bad_backup_behind(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            bad = tmp / "app.db"
            bad.write_bytes(b"this is not a database" * 100)
            with self.assertRaises(Exception):
                backup.backup(bad, tmp / "bk")
            self.assertEqual([p.name for p in (tmp / "bk").glob("app-*.db")], [])

    def test_command_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            make_db(tmp / "app.db").close()
            proc = subprocess.run([sys.executable, str(FAMILY / "backup.py"), str(tmp / "app.db"), str(tmp / "bk"), "2"],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("备份完成", proc.stdout)
            self.assertEqual(subprocess.run([sys.executable, str(FAMILY / "backup.py")], capture_output=True).returncode, 2)


class TestUnits(unittest.TestCase):
    INSTALL = (FAMILY / "install.sh").read_text(encoding="utf-8")

    def test_every_placeholder_in_the_backup_units_is_substituted_by_the_installer(self):
        for name in ("lexica-backup.service", "lexica-backup.timer"):
            text = (FAMILY / "systemd" / name).read_text(encoding="utf-8")
            for ph in set(re.findall(r"@([A-Z_]+)@", text)):
                self.assertIn("@%s@" % ph, self.INSTALL, "%s: 安装脚本没有替换 @%s@" % (name, ph))
        self.assertEqual(subprocess.run(["bash", "-n", str(FAMILY / "install.sh")]).returncode, 0)

    def test_the_service_writes_only_the_backup_and_data_directories(self):
        unit = (FAMILY / "systemd" / "lexica-backup.service").read_text(encoding="utf-8")
        self.assertIn("ProtectSystem=strict", unit)
        self.assertIn("ReadWritePaths=@BACKUP_DIR@ @DATA_DIR@", unit, "数据目录可写：WAL 库在后端没运行时只读打开也要建 -shm")

    def test_recordings_are_mirrored_and_only_new_files_are_copied(self):
        with tempfile.TemporaryDirectory() as tmp:
            data, out = Path(tmp) / "data", Path(tmp) / "backup"
            (data / "recordings" / "202611").mkdir(parents=True)
            (data / "recordings" / "202611" / "a.mp3").write_bytes(b"ID3" + b"a" * 100)
            (data / "recordings" / "202611" / ".hidden").write_bytes(b"x")
            self.assertEqual(backup.mirror_recordings(data, out), 1)
            self.assertEqual((out / "recordings" / "202611" / "a.mp3").read_bytes()[:3], b"ID3")
            self.assertFalse((out / "recordings" / "202611" / ".hidden").exists())
            self.assertEqual(backup.mirror_recordings(data, out), 0, "已经有的不再拷")
            (data / "recordings" / "202611" / "b.mp3").write_bytes(b"ID3b")
            self.assertEqual(backup.mirror_recordings(data, out), 1)
            self.assertEqual(backup.mirror_recordings(Path(tmp) / "nothing", out), 0, "没有录音目录也不出错")

    def test_the_timer_runs_in_beijing_time_not_container_utc(self):
        timer = (FAMILY / "systemd" / "lexica-backup.timer").read_text(encoding="utf-8")
        self.assertIn("OnCalendar=*-*-* 03:00:00 Asia/Shanghai", timer)

    def test_backup_is_opt_in_and_the_path_is_validated(self):
        self.assertIn("WP_BACKUP_DIR", self.INSTALL)
        self.assertIn("WP_BACKUP_DIR 必须是绝对路径", self.INSTALL)


if __name__ == "__main__":
    unittest.main()
