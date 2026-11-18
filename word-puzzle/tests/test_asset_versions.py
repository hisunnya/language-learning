"""页面里 JS / CSS 的 ?v= 必须等于文件内容的哈希前 8 位：改了文件忘了换版本号，这里就会失败。
（公网入口让带 ?v= 的文件在浏览器里留一小时，微信的缓存又很积极；版本号不换，学生会一直用旧文件。）"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import bump_assets                                   # noqa: E402


class TestAssetVersions(unittest.TestCase):
    def test_every_reference_carries_the_hash_of_the_file_it_points_to(self):
        proc = subprocess.run([sys.executable, str(ROOT / "tools" / "bump_assets.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, "\n" + proc.stdout)

    def test_pages_of_the_student_edition_reference_every_asset_with_a_version(self):
        missing = []
        for page in bump_assets.PAGES_ADD:
            for m in bump_assets.REF.finditer(page.read_text(encoding="utf-8")):
                target = bump_assets.resolve(m.group("url"))
                if target is not None and target.exists() and m.group("v") is None:
                    missing.append("%s: %s" % (page.name, m.group("url")))
        self.assertEqual(missing, [])

    def test_a_changed_file_is_detected(self):
        target = ROOT / "web" / "js" / "api.js"
        before = bump_assets.tag(target)
        original = target.read_bytes()
        try:
            target.write_bytes(original + b"\n// x\n")
            self.assertNotEqual(bump_assets.tag(target), before)
            proc = subprocess.run([sys.executable, str(ROOT / "tools" / "bump_assets.py"), "--check"], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("api.js", proc.stdout)
        finally:
            target.write_bytes(original)

    def test_the_wechat_script_loaded_by_the_header_is_versioned_too(self):
        header = (ROOT.parent / "hub" / "shared" / "module-header.js").read_text(encoding="utf-8")
        self.assertIn("wechat.js?v=" + bump_assets.tag(ROOT.parent / "hub" / "shared" / "wechat.js"), header)


if __name__ == "__main__":
    unittest.main()
