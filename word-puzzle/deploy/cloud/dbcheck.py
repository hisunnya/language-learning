#!/usr/bin/env python3
"""迁移数据库时的检查和快照（migrate-data.sh 调用）。只用标准库。

    dbcheck.py inspect  <库文件>                  完整性检查 + 各表行数 + 最近一次活动（只读）
    dbcheck.py open     <库文件> <代码目录>        用要运行的这版代码，在一份临时副本上打开它（会做表结构升级），看能不能用
    dbcheck.py snapshot <库文件> <目标文件>        用 SQLite 在线备份接口存一份（库在使用中也能得到一致的副本）

出问题一律以非 0 退出并在 stderr 说原因；成功时 stdout 是一份 JSON，方便脚本和人看。
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

# 迁移前后要对得上的表（不存在的表跳过：老库可能没有后来加的表）
COUNTED = ("users", "banks", "scores", "page_views", "login_events", "teacher_students",
           "materials", "audit_log", "subject_records")


def _connect_ro(path: Path) -> sqlite3.Connection:
    return sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=30)


def inspect(path: Path) -> dict:
    """库本身有没有坏，里面有多少东西。只读，不改任何东西。"""
    if not path.is_file():
        raise SystemExit("文件不存在：%s" % path)
    con = _connect_ro(path)
    try:
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        counts = {t: con.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0] for t in COUNTED if t in tables}
        newest = {}
        for label, sql in (("score", "SELECT MAX(created_at) FROM scores"),
                           ("audit_ts", "SELECT MAX(ts) FROM audit_log")):
            try:
                newest[label] = con.execute(sql).fetchone()[0]
            except sqlite3.Error:
                newest[label] = None
        roles = {}
        if "users" in tables:
            # deleted_at 默认是 0（没删除）；老库可能还没有这一列
            where = " WHERE deleted_at=0" if _has_column(con, "users", "deleted_at") else ""
            roles = dict(con.execute("SELECT role, COUNT(*) FROM users%s GROUP BY role" % where).fetchall())
        return {"file": str(path), "bytes": path.stat().st_size, "integrity": integrity,
                "user_version": con.execute("PRAGMA user_version").fetchone()[0],
                "counts": counts, "roles": roles, "newest": newest}
    finally:
        con.close()


def _has_column(con: sqlite3.Connection, table: str, column: str) -> bool:
    return any(r[1] == column for r in con.execute('PRAGMA table_info("%s")' % table))


def open_with_app(path: Path, app_dir: Path) -> dict:
    """在一份临时副本上，用要运行的这版代码打开：能打开、表结构能升级、升级后行数不变，才算能用。
    原文件不动。库比这版代码还新（user_version 更大）也算不能用：降级会丢东西。"""
    sys_path = str(app_dir)
    if sys_path not in sys.path:
        sys.path.insert(0, sys_path)
    from server.db import Database  # noqa: WPS433（要用那版代码，不能写在文件顶部）

    before = inspect(path)
    with tempfile.TemporaryDirectory(prefix="lexica-open-") as tmp:
        copy = Path(tmp) / "app.db"
        shutil.copyfile(path, copy)
        try:
            db = Database(copy)
            after_version = db.one("PRAGMA user_version")[0]
            db._conn.close()
        except Exception as exc:  # noqa: BLE001（任何原因打不开都要拦下）
            raise SystemExit("这版代码打不开这个库：%s: %s" % (type(exc).__name__, exc))
        after = inspect(copy)
    if after["integrity"] != "ok":
        raise SystemExit("升级表结构之后完整性检查没通过：%s" % after["integrity"])
    for table, n in before["counts"].items():
        if after["counts"].get(table) != n:
            raise SystemExit("升级表结构之后 %s 的行数变了：%s → %s" % (table, n, after["counts"].get(table)))
    return {"opens": True, "user_version_before": before["user_version"], "user_version_after": after_version}


def snapshot(src: Path, dst: Path) -> dict:
    """SQLite 在线备份接口：库正在被使用也能得到一致的副本；做完检查完整性。"""
    if not src.is_file():
        raise SystemExit("文件不存在：%s" % src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    partial = dst.with_name(dst.name + ".partial")
    source = _connect_ro(src)
    try:
        target = sqlite3.connect(str(partial))
        try:
            source.backup(target)
            target.execute("PRAGMA journal_mode=DELETE")
        finally:
            target.close()
    finally:
        source.close()
    info = inspect(partial)
    if info["integrity"] != "ok":
        partial.unlink(missing_ok=True)
        raise SystemExit("快照没通过完整性检查：%s" % info["integrity"])
    partial.replace(dst)
    return {"snapshot": str(dst), "bytes": dst.stat().st_size, "counts": info["counts"]}


def main(argv: list[str]) -> int:
    try:
        if len(argv) == 3 and argv[1] == "inspect":
            result = inspect(Path(argv[2]))
        elif len(argv) == 4 and argv[1] == "open":
            result = open_with_app(Path(argv[2]), Path(argv[3]))
        elif len(argv) == 4 and argv[1] == "snapshot":
            result = snapshot(Path(argv[2]), Path(argv[3]))
        else:
            print(__doc__, file=sys.stderr)
            return 2
    except sqlite3.DatabaseError as exc:
        print("不是有效的 SQLite 库：%s" % exc, file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
