#!/usr/bin/env python3
"""从 web/ 生成公开版 /words/ 的网页目录（安装时运行；仓库里只有 web/ 一份源码）。

公开版和要登录的 /word-puzzle/ 是同一套代码、同一个后端：
* 只拷学生玩得到的四个页面（首页、游戏、读音练习、我的成绩）和它们的样式、脚本、图片；
  管理页、登录页、积分榜不拷，打开就是 404。
* 页面里写死的 /word-puzzle/ 换成 /words/（wp-base 也是），接口就走 /words/api/ —— nginx 把它转给后端的公开入口，
  后端只开放白名单里的接口，只给内置题库里的初中、高中（server/app.py 的 handle_public、server/tenancy.py 的 PUBLIC）。

    python3 tools/build_public_web.py <web 目录> <输出目录>
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

PAGES = ("index.html", "play.html", "practice.html", "stats.html")
DIRS = ("css", "js", "img")
TEXT_SUFFIXES = (".html", ".js", ".css", ".svg", ".json")
SOURCE_PREFIX, PUBLIC_PREFIX = "/word-puzzle", "/words"


# 页面最前面那段脚本按 sessionStorage 里记的角色先设好视图，登录过的老师在首页还会被直接送去题库工作台。
# 公开版没有角色：一律学生视图，也不跳转（同一个标签页里刚在 /word-puzzle/ 登录过的老师打开 /words/ 也一样）。
ROLE_SCRIPT = re.compile(r"<script>\(function\(\)\{var h=document\.documentElement.*?\}\)\(\)</script>")
PUBLIC_HEAD = "<script>document.documentElement.classList.add('role-student')</script>"


def public_page(text: str) -> str:
    text, n = ROLE_SCRIPT.subn(PUBLIC_HEAD, text, count=1)
    if not n:
        raise SystemExit("页面开头没有设置角色的脚本，公开版不知道怎么改：先看一下页面是不是改过")
    return rewrite(text)


def rewrite(text: str) -> str:
    return (text.replace(SOURCE_PREFIX + "/", PUBLIC_PREFIX + "/")
                .replace('content="' + SOURCE_PREFIX + '"', 'content="' + PUBLIC_PREFIX + '"'))


def build(src: Path, dst: Path) -> list[str]:
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    written = []
    for page in PAGES:
        (dst / page).write_text(public_page((src / page).read_text(encoding="utf-8")), encoding="utf-8")
        written.append(page)
    for name in DIRS:
        for path in sorted((src / name).rglob("*")):
            if path.is_dir() or any(part.startswith(".") for part in path.relative_to(src).parts):
                continue
            out = dst / path.relative_to(src)
            out.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix in TEXT_SUFFIXES:
                out.write_text(rewrite(path.read_text(encoding="utf-8")), encoding="utf-8")
            else:
                shutil.copy2(path, out)
            written.append(str(path.relative_to(src)))
    return written


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__.strip().splitlines()[-1].strip(), file=sys.stderr)
        return 2
    files = build(Path(argv[1]), Path(argv[2]))
    print("公开版 /words/：%d 个文件" % len(files))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
