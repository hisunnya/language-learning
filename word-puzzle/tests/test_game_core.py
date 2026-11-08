"""game-core.js 的行为测试（用 node 跑，缺 node 时跳过）。

纯运算层 game-core.js 不碰 DOM，所以可以在 node 里直接跑：
``tests/js/game_core.test.js`` 用 ``vm`` 伪造一个 ``window`` 全局加载它。

服务器上没有 node（见 AGENTS.md §4），这时本用例整体跳过，
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
JS_TEST = ROOT / "tests" / "js" / "game_core.test.js"
PARITY_TEST = ROOT / "tests" / "js" / "core_parity.test.js"

NODE = shutil.which("node") or shutil.which("nodejs")


@unittest.skipUnless(NODE, "本机没有 node，跳过 game-core.js 的行为测试")
class TestGameCore(unittest.TestCase):
    def test_game_core_behaviour(self) -> None:
        proc = subprocess.run(
            [NODE, str(JS_TEST)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(
            proc.returncode, 0,
            "game-core.js 行为测试失败：\n" + proc.stdout + proc.stderr,
        )
        self.assertIn("通过", proc.stdout)


    def test_miniprogram_core_behaves_like_the_website_core(self) -> None:
        """小程序的 game-core.js 是网站版的移植，两份必须行为一致，不能各改各的。"""
        proc = subprocess.run(
            [NODE, str(PARITY_TEST)], capture_output=True, text=True, timeout=120)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("一致", proc.stdout)


if __name__ == "__main__":
    unittest.main()
