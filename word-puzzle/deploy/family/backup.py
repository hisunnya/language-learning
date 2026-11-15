#!/usr/bin/env python3
"""数据库每日备份：用 SQLite 在线备份接口（不锁库、不会拷出半截的文件），备份完做完整性检查，只保留最近 N 份。

    python3 backup.py <数据库文件> <备份目录> [保留份数，默认 30]

由容器里的 systemd 定时器每天运行一次（lexica-backup.timer），备份目录是挂进容器的宿主机目录，
所以备份和数据库都在容器外面。只用标准库。出错一律以非 0 退出，让 systemd 记成失败。
"""
from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path

PREFIX = "app-"
SUFFIX = ".db"


def backup(db_path: Path, out_dir: Path, keep: int = 30, now: float | None = None) -> Path:
    if not db_path.is_file():
        raise SystemExit("数据库不存在：%s" % db_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S", time.localtime(now or time.time()))
    target = out_dir / (PREFIX + stamp + SUFFIX)
    partial = out_dir / (target.name + ".partial")
    src = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True, timeout=30)
    try:
        dst = sqlite3.connect(str(partial))
        try:
            src.backup(dst)
            dst.execute("PRAGMA journal_mode=DELETE")      # 备份是一个单独的文件，不带 -wal / -shm（否则复制、检查时会冒出旁路文件）
        finally:
            dst.close()
    finally:
        src.close()
    check = sqlite3.connect("file:%s?mode=ro" % partial, uri=True)
    try:
        result = check.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        check.close()
    if result != "ok":
        partial.unlink(missing_ok=True)
        raise SystemExit("备份没通过完整性检查：%s" % result)
    partial.replace(target)
    prune(out_dir, keep)
    return target


def prune(out_dir: Path, keep: int) -> list[Path]:
    """只删我们自己命名规则的备份（app-日期.db），别的文件不碰；最近的 keep 份留下。"""
    files = sorted(p for p in out_dir.iterdir() if p.is_file() and p.name.startswith(PREFIX) and p.name.endswith(SUFFIX))
    doomed = files[:-keep] if keep > 0 else []
    for p in doomed:
        p.unlink()
    return doomed


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    keep = int(argv[3]) if len(argv) > 3 else 30
    target = backup(Path(argv[1]), Path(argv[2]), keep)
    print("备份完成：%s（%d 字节）" % (target, target.stat().st_size))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
