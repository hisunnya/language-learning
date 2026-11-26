#!/usr/bin/env python3
"""页面里引用的 JS / CSS 的版本号（?v=）= 文件内容的哈希前 8 位。

为什么：公网入口很慢，nginx 让带 ?v= 的文件在浏览器里留一小时（见 deploy/family/nginx）；微信里的浏览器缓存又特别积极。
文件改了而 ?v= 没改，学生就会一直用旧文件。所以版本号不靠人记，由内容算出来，测试检查两者是否一致。

    python3 tools/bump_assets.py          # 改了 JS / CSS 之后运行：把所有页面里的 ?v= 改成新的（没变的不动）
    python3 tools/bump_assets.py --check  # 只检查，有对不上的就列出来并以 1 退出（tests/test_asset_versions.py 用它）

范围：word-puzzle/web 下的页面（缺 ?v= 的会补上），以及用到共享页眉的其他页面（只改已有的 ?v=）。
/word-puzzle/xxx → word-puzzle/web/xxx；/shared/xxx → hub/shared/xxx。
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
# 缺 ?v= 的也补上
PAGES_ADD = sorted((REPO / "word-puzzle" / "web").glob("*.html")) + [
    REPO / "backends" / "index.html",
    REPO / "nvidia-exam" / "index.html",
]
# 只改已有的 ?v=
PAGES_UPDATE = [REPO / p for p in ("hub/index.html", "hub/privacy.html", "chemistry/index.html", "physics/index.html",
                                   "topic-app/topic-app/index.html", "ham-exam/index.html")]
REF = re.compile(r'(?P<attr>src|href)="(?P<url>(?:/(?:word-puzzle|shared)/)?[^"?#\s]+\.(?:js|css))(?:\?v=(?P<v>[^"]*))?"')
# JS 里自己拼的引用（module-header.js 在微信里才去加载 wechat.js）：(含引用的文件, 被引用的文件名, 被引用文件的路径)
EMBEDDED = [("hub/shared/module-header.js", "wechat.js", "hub/shared/wechat.js")]


def resolve(url: str, page: Path | None = None) -> Path | None:
    """/word-puzzle/xxx → word-puzzle/web/xxx；/shared/xxx → hub/shared/xxx；
    同一目录下的相对引用（css/x.css、js/x.js）按页面所在目录找。"""
    if url.startswith("/word-puzzle/"):
        return REPO / "word-puzzle" / "web" / url[len("/word-puzzle/"):]
    if url.startswith("/shared/"):
        return REPO / "hub" / "shared" / url[len("/shared/"):]
    if page is not None and not url.startswith(("/", "#", "http:", "https:")):
        target = (page.parent / url).resolve()
        try:                      # 别让 ../ 逃出仓库
            target.relative_to(REPO)
        except ValueError:
            return None
        return target
    return None


def tag(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:8]


def embedded_pass(write: bool) -> list[str]:
    problems = []
    for host, name, target in EMBEDDED:
        host_path, want = REPO / host, tag(REPO / target)
        text = host_path.read_text(encoding="utf-8")
        pattern = re.compile(re.escape(name) + r"\?v=([0-9A-Za-z-]+)")
        found = pattern.findall(text)
        if found != [want]:
            problems.append("%s 里 %s 的 ?v= 应为 %s（现在 %s）" % (host, name, want, ",".join(found) or "没有"))
            if write:
                host_path.write_text(pattern.sub(name + "?v=" + want, text), encoding="utf-8")
    return problems


def pages_pass(write: bool) -> list[str]:
    problems = []
    for page in PAGES_ADD + [p for p in PAGES_UPDATE if p.exists()]:
        add_missing = page in PAGES_ADD
        text = page.read_text(encoding="utf-8")
        rel = page.relative_to(REPO)

        def fix(m: re.Match) -> str:
            target = resolve(m.group("url"), page)
            if target is None or not target.exists():
                return m.group(0)
            want = tag(target)
            if m.group("v") is None and not add_missing:
                return m.group(0)
            if m.group("v") and "__" in m.group("v"):
                return m.group(0)          # 主页用 __ASSET_VERSION__ 占位（部署时换成时间戳）
            if m.group("v") != want:
                problems.append("%s：%s ?v=%s 应为 ?v=%s" % (rel, m.group("url"), m.group("v"), want))
            return '%s="%s?v=%s"' % (m.group("attr"), m.group("url"), want)

        new = REF.sub(fix, text)
        if write and new != text:
            page.write_text(new, encoding="utf-8")
    return problems


def main(argv: list[str]) -> int:
    check = "--check" in argv
    problems = embedded_pass(write=not check) + pages_pass(write=not check)       # 先改 JS 里拼的引用：它会改变 module-header.js 自己的哈希
    if check:
        for p in problems:
            print(p)
        if problems:
            print("\n改了 JS / CSS 之后要运行：python3 word-puzzle/tools/bump_assets.py")
        return 1 if problems else 0
    print("已更新 %d 处版本号" % len(problems) if problems else "版本号都是最新的")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
