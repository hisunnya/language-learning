#!/usr/bin/env python3
"""对 web/js 下的 JavaScript 做语法体检。

服务器上没有 node，所以用一个小词法扫描器检查：
括号配对、字符串/模板串闭合、正则字面量、注释闭合。

这不是完整的 JS 解析器，但足以抓住「多一个右括号」这类手写事故
（2026-11-04 就因为 ``d.getMinutes())`` 少了个 ``p(`` 踩过一次）。

用法::

    python3 tools/check_js.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JS_DIR = ROOT / "web" / "js"

PAIRS = {")": "(", "]": "[", "}": "{"}
OPEN = set("([{")


class JsError(Exception):
    def __init__(self, line: int, col: int, msg: str):
        super().__init__(f"第 {line} 行第 {col} 列：{msg}")
        self.line = line
        self.col = col
        self.msg = msg


def check(source: str) -> None:
    stack = []
    i = 0
    line = 1
    col = 1
    n = len(source)

    def adv(k: int = 1) -> None:
        nonlocal i, line, col
        for _ in range(k):
            if source[i] == "\n":
                line += 1
                col = 1
            else:
                col += 1
            i += 1

    while i < n:
        ch = source[i]
        nxt = source[i + 1] if i + 1 < n else ""

        # 注释
        if ch == "/" and nxt == "/":
            while i < n and source[i] != "\n":
                adv()
            continue
        if ch == "/" and nxt == "*":
            start_line, start_col = line, col
            adv(2)
            while i < n and not (source[i] == "*" and i + 1 < n and source[i + 1] == "/"):
                adv()
            if i >= n:
                raise JsError(start_line, start_col, "块注释没有闭合")
            adv(2)
            continue

        # 字符串
        if ch in "\"'":
            quote = ch
            start_line, start_col = line, col
            adv()
            while i < n:
                if source[i] == "\\":
                    adv(2)
                    continue
                if source[i] == quote:
                    adv()
                    break
                if source[i] == "\n":
                    raise JsError(start_line, start_col, "字符串没有闭合")
                adv()
            else:
                raise JsError(start_line, start_col, "字符串没有闭合")
            continue

        # 模板串
        if ch == "`":
            start_line, start_col = line, col
            adv()
            depth = 0
            while i < n:
                if source[i] == "\\":
                    adv(2)
                    continue
                if source[i] == "$" and i + 1 < n and source[i + 1] == "{":
                    depth += 1
                    adv(2)
                    continue
                if source[i] == "}" and depth > 0:
                    depth -= 1
                    adv()
                    continue
                if source[i] == "`" and depth == 0:
                    adv()
                    break
                adv()
            else:
                raise JsError(start_line, start_col, "模板串没有闭合")
            continue

        # 正则字面量：前一个 token 若是标识符/数字/右括号 → 是除号，否则是正则
        if ch == "/":
            prev = _prev_significant(source, i)
            is_value_end = (prev is not None and
                            (prev.isalnum() or prev in "_$)]'\""))
            if is_value_end:
                pass  # 除号
            else:
                start_line, start_col = line, col
                adv()
                in_class = False
                closed = False
                while i < n:
                    c = source[i]
                    if c == "\\":
                        adv(2)
                        continue
                    if c == "\n":
                        break
                    if c == "[":
                        in_class = True
                    elif c == "]":
                        in_class = False
                    elif c == "/" and not in_class:
                        adv()
                        closed = True
                        break
                    adv()
                if not closed:
                    raise JsError(start_line, start_col, "正则字面量没有闭合")

        if ch in OPEN:
            stack.append((ch, line, col))
            adv()
            continue
        if ch in PAIRS:
            if not stack:
                raise JsError(line, col, f"多出来的 {ch}")
            op, ol, oc = stack.pop()
            if op != PAIRS[ch]:
                raise JsError(line, col,
                              f"{ch} 与第 {ol} 行的 {op} 不匹配")
            adv()
            continue

        adv()

    if stack:
        op, ol, oc = stack[-1]
        raise JsError(ol, oc, f"{op} 没有闭合")


def _prev_significant(source: str, i: int) -> str | None:
    j = i - 1
    while j >= 0 and source[j] in " \t\r\n":
        j -= 1
    return source[j] if j >= 0 else None


def main() -> int:
    files = sorted(JS_DIR.glob("*.js"))
    if not files:
        print("没有找到 JS 文件")
        return 1
    failed = 0
    for f in files:
        src = f.read_text(encoding="utf-8")
        try:
            check(src)
            print(f"  OK   {f.relative_to(ROOT)}")
        except JsError as exc:
            failed += 1
            print(f"  FAIL {f.relative_to(ROOT)}  →  {exc}")
    print(f"\n{len(files) - failed}/{len(files)} 个文件通过")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
