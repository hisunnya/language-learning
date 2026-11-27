"""app.js 的冒烟测试（用 node 跑，缺 node 时跳过）。

app.js 是一段 IIFE，只通过 DOM 说话；``tests/js/app_smoke.test.js`` 用一个
够用的假 DOM 把页面真的点一遍：换考试科目、组卷、作答、交卷、看题库、看指南、
看统计。服务器上没有 node（见 AGENTS.md §4），这时本用例整体跳过，
前端逻辑仍由 ``tools/check_js.py`` 做语法体检兜底。

跑法::

    python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JS_TEST = ROOT / "tests" / "js" / "app_smoke.test.js"

NODE = shutil.which("node") or shutil.which("nodejs")


@unittest.skipUnless(NODE, "本机没有 node，跳过 app.js 的冒烟测试")
class TestAppSmoke(unittest.TestCase):
    def test_the_page_runs_end_to_end(self) -> None:
        proc = subprocess.run(
            [NODE, str(JS_TEST)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("全部通过", proc.stdout)


if __name__ == "__main__":
    unittest.main()