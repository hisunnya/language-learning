"""chemistry.js 的行为测试（用 node 跑，缺 node 时跳过）。

出题逻辑碰 DOM，所以 ``tests/js/chemistry.test.js`` 用 ``vm`` 加一个极简 DOM 桩来跑。
服务器上没有 node（见 AGENTS.md §4），这时整体跳过，语法由 word-puzzle/tools/check_js.py 兜底。
"""
from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NODE = shutil.which("node") or shutil.which("nodejs")


@unittest.skipUnless(NODE, "本机没有 node，跳过 chemistry.js 的行为测试")
class TestChemistryJs(unittest.TestCase):
    def test_behaviour(self) -> None:
        proc = subprocess.run(
            [NODE, str(ROOT / "tests" / "js" / "chemistry.test.js")],
            capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("通过", proc.stdout)


if __name__ == "__main__":
    unittest.main()
