#!/usr/bin/env python3
"""把老师写的 Word 资料导入成新题型的题库（单词大比拼 spell / 排排坐 order）。

    # 先看解析结果，不写库
    python3 tools/import_items.py --type spell --file 资料.docx --dry-run
    # 写库（在服务器上用服务账号跑：runuser -u wpfamily -- env WP_DB=… python3 tools/import_items.py …）
    python3 tools/import_items.py --type spell --file 资料.docx --title "新视野大学英语 第一册 Unit 3 · 单词大比拼" \\
        --category "新视野大学英语读写教程 第一册" --level1 大学 --level2 大一 --level3 上册 --level4 "Unit 3" \\
        --owner 管理员账号 [--copy-tags-from 题库编号]

--copy-tags-from：把另一个题库上的标签（每位老师打的）照样打到新题库上，开放给同一批学生。
资料有问题（括号不成对、片段和参考答案对不上……）会列出来并退出，不写库。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server import items, tenancy        # noqa: E402
from server.db import Database           # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="导入新题型题库")
    ap.add_argument("--type", required=True, choices=items.ITEM_TYPES)
    ap.add_argument("--file", required=True)
    ap.add_argument("--db", default=os.environ.get("WP_DB", ""))
    ap.add_argument("--title", default="")
    ap.add_argument("--category", default="")
    ap.add_argument("--level1", default="大学")
    ap.add_argument("--level2", default="")
    ap.add_argument("--level3", default="")
    ap.add_argument("--level4", default="")
    ap.add_argument("--owner", default="", help="题库主人的登录名（学号 / 工号）；不写 = 内置题库（所有老师可用）")
    ap.add_argument("--copy-tags-from", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    found, problems, title = items.parse(args.type, Path(args.file).read_bytes())
    print("资料标题：%s；题目 %d 道" % (title or "（无）", len(found)))
    for item in found:
        print("  " + json.dumps(item, ensure_ascii=False))
    if problems:
        print("\n有问题，没有导入：\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1
    if args.dry_run:
        return 0
    if not args.db:
        print("请用 --db 或 WP_DB 指定数据库", file=sys.stderr)
        return 2
    db = Database(args.db)
    owner = None
    if args.owner:
        row = db.one("SELECT id FROM users WHERE student_no=? AND deleted_at=0 AND role IN ('admin','teacher')", (args.owner,))
        if not row:
            print("找不到老师账号 %s" % args.owner, file=sys.stderr)
            return 2
        owner = row["id"]
    meta = {"title": args.title or title or Path(args.file).stem, "level1": args.level1, "level2": args.level2,
            "level3": args.level3, "level4": args.level4, "source": "import", "owner_id": owner,
            "game_type": args.type, "pairs_per_level": items.PER_LEVEL[args.type]}
    bid = db.insert_item_bank(meta, found)
    if args.category:
        db.execute("UPDATE banks SET category=? WHERE id=?", (args.category, bid))
    copied = 0
    if args.copy_tags_from:
        for row in db.query("SELECT tag, teacher_id FROM bank_tags WHERE bank_id=?", (args.copy_tags_from,)):
            db.execute("INSERT OR IGNORE INTO bank_tags(bank_id, tag, teacher_id) VALUES (?,?,?)", (bid, row["tag"], row["teacher_id"]))
            copied += 1
    tenancy.audit(db, owner, "bank.import", "bank", bid, title=meta["title"], game_type=args.type, items=len(found))
    print("已导入：题库 #%d「%s」，%d 道题%s" % (bid, meta["title"], len(found), "，复制了 %d 个标签" % copied if copied else ""))
    db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
