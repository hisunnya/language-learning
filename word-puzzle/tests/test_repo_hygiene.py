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
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
EMAIL_ALLOWED_DOMAINS = {"users.noreply.github.com", "example.com", "example.org", "anthropic.com"}
# 私有网段的地址（家里的内网、服务器、虚拟机）不能出现；下面是文档和测试里用的、明显是举例的几个
PRIVATE_IP = re.compile(r"(?<![0-9.])(10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3}|172\.(?:1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3})(?![0-9])")
IP_EXAMPLES = re.compile(r"192\.168\.1\.[0-9]{1,3}|192\.168\.0\.[0-9]{1,3}|10\.20\.30\.[0-9]{1,3}|172\.16\.0\.9|172\.31\.1\.1")
# Tailscale 的网址：真实的 tailnet 名（默认形如 tailXXXXXX）一律不能出现；示例用 example-net
TAILNET = re.compile(r"\b[a-z0-9-]+\.([a-z0-9-]+)\.ts\.net\b|\btail[0-9a-f]{6}\b")
TAILNET_EXAMPLES = {"example-net", "example", "cat-crocodile"}
LOCAL_PATTERNS = REPO / ".private-patterns"       # 不进 git：每行一个只有本机知道的私有字符串（真实地址、公司名、学号……）
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

    def test_no_email_addresses_other_than_the_noreply_one(self):
        problems = []
        for name in self.files:
            path = REPO / name
            if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file() or path.stat().st_size > 3_000_000 or "data/raw" in name:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for m in EMAIL.finditer(text):
                domain = m.group(0).rsplit("@", 1)[1].lower()
                if domain not in EMAIL_ALLOWED_DOMAINS and not domain.endswith((".png", ".jpg", ".svg", ".js", ".css", ".json")):
                    problems.append("%s: 邮箱地址（%s）" % (name, domain))
        self.assertEqual(problems, [], "仓库是公开的：邮箱只能用 GitHub 的 noreply 地址")

    def test_no_private_network_addresses_or_tailnet_names(self):
        problems = []
        for name in self.files:
            path = REPO / name
            if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file() or path.stat().st_size > 3_000_000 or "data/raw" in name:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for m in PRIVATE_IP.finditer(text):
                if not IP_EXAMPLES.fullmatch(m.group(1)):
                    problems.append("%s: 私有网段地址 %s…" % (name, m.group(1).split(".")[0] + ".x"))
            for m in TAILNET.finditer(text):
                label = m.group(1)
                if label is None or not (label in TAILNET_EXAMPLES or set(label) <= {"x", "-"}):
                    problems.append("%s: 真实的 tailnet / ts.net 名字（%s）" % (name, (m.group(0) or "")[:4] + "…"))
        self.assertEqual(problems, [], "内网地址、服务器、Funnel 网址是私有信息，放进 AGENTS.local.md 和 deploy.local.env，不要进仓库")

    def test_patterns_only_this_machine_knows_about(self):
        if not LOCAL_PATTERNS.is_file():
            self.skipTest("没有 .private-patterns（它不进 git，只在本机；里面写只有你知道的私有字符串）")
        patterns = [l.strip() for l in LOCAL_PATTERNS.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
        problems = []
        for name in self.files:
            path = REPO / name
            if not path.is_file() or path.stat().st_size > 3_000_000 or "data/raw" in name:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for pat in patterns:
                if re.search(pat, text):
                    problems.append("%s: 命中私有模式 #%d" % (name, patterns.index(pat) + 1))
        self.assertEqual(problems, [])

    def test_every_commit_is_authored_with_the_noreply_address(self):
        out = subprocess.run([GIT, "-C", str(REPO), "log", "--all", "--format=%ae%n%ce"], capture_output=True, text=True, check=True).stdout
        emails = {e.strip() for e in out.splitlines() if e.strip()}
        bad = {e for e in emails if not e.endswith("@users.noreply.github.com")}
        self.assertEqual(bad, set(), "提交作者 / 提交者邮箱必须是 GitHub noreply 地址（见 AGENTS.md「Identity」）")

    def test_gitignore_blocks_the_usual_leaks(self):
        ignore = (REPO / ".gitignore").read_text(encoding="utf-8")
        for pattern in ("*.db", "*名单*", "*初始密码*", ".env", "*.pem", "deploy.local.env", "AGENTS.local.md", ".private-patterns"):
            self.assertIn(pattern, ignore)


if __name__ == "__main__":
    unittest.main()
