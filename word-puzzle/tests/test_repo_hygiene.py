"""仓库在 GitHub 上是公开的：真实的名单、数据库、密码、手机号、密钥一个都不能被提交。"""
from __future__ import annotations

import re
import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GIT = shutil.which("git")

FORBIDDEN_NAME = re.compile(r"(\.(db|db-wal|db-shm|sqlite3?|pem|key|p12|env)$)|名单|初始密码|credential|(^|/)roster[^/]*\.(xlsx?|csv)$", re.I)
# 测试里用的假手机号（用来证明「手机号不会被保存」），不是真实号码
PHONE_ALLOWED = {"13800000000", "13900000000"}
PHONE = re.compile(r"(?<![0-9])1[3-9][0-9]{9}(?![0-9])")
SECRET = re.compile(r"ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY|tskey-[A-Za-z0-9-]{10,}|sk-[A-Za-z0-9]{32,}")
TEXT_SUFFIXES = {".py", ".js", ".json", ".md", ".sh", ".html", ".css", ".conf", ".inc", ".service", ".txt", ".csv", ".yml", ".yaml", ".wxml", ".wxss"}


@unittest.skipUnless(GIT and (REPO / ".git").exists(), "不在 git 检出里，跳过")
class TestTrackedFiles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        out = subprocess.run([GIT, "-C", str(REPO), "ls-files", "-z"], capture_output=True, text=True, check=True).stdout
        cls.files = [f for f in out.split("\0") if f]

    def test_no_data_files_are_tracked(self):
        bad = [f for f in self.files if FORBIDDEN_NAME.search(f)]
        self.assertEqual(bad, [], "这些文件看起来是真实数据 / 密钥，不能进公开仓库")

    def test_no_real_phone_numbers_or_secrets_in_text_files(self):
        problems = []
        for name in self.files:
            path = REPO / name
            if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file() or path.stat().st_size > 3_000_000:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for m in PHONE.finditer(text):
                if m.group(0) not in PHONE_ALLOWED:      # 前后紧挨着数字的（毫秒时间戳等更长的数字）正则已经排除
                    problems.append("%s: 像手机号 %s…" % (name, m.group(0)[:4]))
            if SECRET.search(text):
                problems.append("%s: 像密钥 / token" % name)
        self.assertEqual(problems, [])

    def test_gitignore_blocks_the_usual_leaks(self):
        ignore = (REPO / ".gitignore").read_text(encoding="utf-8")
        for pattern in ("*.db", "*名单*", "*初始密码*", ".env", "*.pem"):
            self.assertIn(pattern, ignore)


if __name__ == "__main__":
    unittest.main()
