"""SQLite 数据层。

设计要点
--------
* 只用标准库 ``sqlite3``，不引入任何第三方依赖（服务器上没有 pip）。
* 单连接 + 可重入锁：SQLite 本身对写入是串行的，加锁保证多线程安全，
  同时避免每个请求都开关一次连接的开销。
* ``wal`` 模式：读不阻塞写。
* 数据库文件默认在 ``word-puzzle/var/app.db``，可用环境变量 ``WP_DB`` 覆盖。
"""
from __future__ import annotations

import contextlib
import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "var" / "app.db"

SCHEMA = """
PRAGMA journal_mode=WAL;

-- 上传的资料（词表文件）
CREATE TABLE IF NOT EXISTS materials (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    filename     TEXT,
    fmt          TEXT,
    size         INTEGER DEFAULT 0,
    note         TEXT DEFAULT '',
    word_count   INTEGER DEFAULT 0,
    unit_count   INTEGER DEFAULT 0,
    created_at   TEXT NOT NULL
);

-- 资料里的词条（一个资料 = 多个单元）
CREATE TABLE IF NOT EXISTS material_words (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    material_id  INTEGER NOT NULL,
    unit         TEXT NOT NULL,
    en           TEXT NOT NULL,
    cn           TEXT NOT NULL,
    ipa          TEXT DEFAULT '',
    pos          TEXT DEFAULT '',
    ord          INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_mw_material ON material_words(material_id, ord);

-- 生成的题库
CREATE TABLE IF NOT EXISTS banks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT NOT NULL,
    level1       TEXT NOT NULL,
    level2       TEXT NOT NULL,
    level3       TEXT NOT NULL,
    level4       TEXT NOT NULL,
    source       TEXT NOT NULL,          -- seed | material
    material_id  INTEGER,
    unit_mode    TEXT NOT NULL DEFAULT 'all',   -- all | per-unit | range
    unit_from    INTEGER DEFAULT 0,
    unit_to      INTEGER DEFAULT 0,
    pairs_per_level INTEGER DEFAULT 12,  -- 一关最多多少词
    word_count   INTEGER DEFAULT 0,
    unit_count   INTEGER DEFAULT 0,
    created_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bank_words (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_id      INTEGER NOT NULL,
    unit         TEXT NOT NULL,
    en           TEXT NOT NULL,
    cn           TEXT NOT NULL,
    ipa          TEXT DEFAULT '',
    pos          TEXT DEFAULT '',
    ord          INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_bw_bank ON bank_words(bank_id, ord);

-- 成绩记录（在线玩）
CREATE TABLE IF NOT EXISTS scores (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_id      INTEGER,
    bank_title   TEXT NOT NULL DEFAULT '',
    device       TEXT DEFAULT '',
    nickname     TEXT DEFAULT '',
    mode         TEXT DEFAULT 'online',    -- online | offline
    score        INTEGER DEFAULT 0,
    matched      INTEGER DEFAULT 0,
    total_pairs  INTEGER DEFAULT 0,
    wrong        INTEGER DEFAULT 0,
    best_combo   INTEGER DEFAULT 0,
    duration     INTEGER DEFAULT 0,
    level_count  INTEGER DEFAULT 0,
    detail       TEXT DEFAULT '[]',
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_scores_created ON scores(created_at DESC);

-- 家庭版（WP_AUTH=1）才会用到的账号表；局域网版里这两张表是空的
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    student_no    TEXT NOT NULL UNIQUE,      -- 学号，同时是登录名
    name          TEXT NOT NULL DEFAULT '',
    class_name    TEXT NOT NULL DEFAULT '',  -- 班级
    college       TEXT NOT NULL DEFAULT '',  -- 学院
    department    TEXT NOT NULL DEFAULT '',  -- 院系
    role          TEXT NOT NULL DEFAULT 'student',   -- student | admin
    pw_hash       TEXT NOT NULL,
    must_change   INTEGER NOT NULL DEFAULT 1,        -- 1 = 下次登录必须先改密码
    disabled      INTEGER NOT NULL DEFAULT 0,
    failed_count  INTEGER NOT NULL DEFAULT 0,
    locked_until  REAL NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL,
    last_login_at TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS ix_users_class ON users(class_name);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,             -- 只存令牌的哈希，库泄露也拿不到可用的令牌
    user_id    INTEGER NOT NULL,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL,
    last_seen  REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS ix_scores_bank ON scores(bank_id);
"""


def now_iso() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


class Database:
    """线程安全的 SQLite 封装。"""

    def __init__(self, path: str | os.PathLike | None = None):
        self.path = Path(path or os.environ.get("WP_DB") or DEFAULT_DB)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(SCHEMA)
            self._conn.commit()
        self._migrate()

    def _migrate(self) -> None:
        """给老数据库补字段。

        ``CREATE TABLE IF NOT EXISTS`` 不会给已存在的表加列，
        所以新增字段必须在这里补。
        """
        columns = {row["name"] for row in self.query("PRAGMA table_info(banks)")}
        if "pairs_per_level" not in columns:
            self.execute("ALTER TABLE banks ADD COLUMN "
                         "pairs_per_level INTEGER DEFAULT 12")
        if "owner_id" not in columns:
            # NULL = 系统题库（所有人可见）；否则是创建者的用户 id
            self.execute("ALTER TABLE banks ADD COLUMN owner_id INTEGER")
        score_columns = {row["name"] for row in self.query("PRAGMA table_info(scores)")}
        if "user_id" not in score_columns:
            self.execute("ALTER TABLE scores ADD COLUMN user_id INTEGER")
            self.execute("CREATE INDEX IF NOT EXISTS ix_scores_user ON scores(user_id)")

    # ---------------- 基础操作 ----------------

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def query(self, sql: str, args: Iterable[Any] = ()) -> list[sqlite3.Row]:
        with self._lock:
            return list(self._conn.execute(sql, tuple(args)))

    def one(self, sql: str, args: Iterable[Any] = ()) -> sqlite3.Row | None:
        rows = self.query(sql, args)
        return rows[0] if rows else None

    @contextlib.contextmanager
    def _tx(self):
        """加锁的写事务：成功提交，失败回滚。

        不回滚的话，半截写入会留在打开的事务里，被之后任意请求的 commit 一并提交。
        """
        with self._lock:
            try:
                yield self._conn
            except BaseException:
                self._conn.rollback()
                raise
            self._conn.commit()

    def execute(self, sql: str, args: Iterable[Any] = ()) -> sqlite3.Cursor:
        with self._tx() as conn:
            return conn.execute(sql, tuple(args))

    def executemany(self, sql: str, rows: Iterable[Iterable[Any]]) -> None:
        with self._tx() as conn:
            conn.executemany(sql, [tuple(r) for r in rows])

    # ---------------- materials ----------------

    def insert_material(self, name: str, filename: str, fmt: str, size: int,
                        note: str, words: list[dict]) -> int:
        ts = now_iso()
        with self._tx() as conn:
            cur = conn.execute(
                "INSERT INTO materials(name, filename, fmt, size, note, "
                "word_count, unit_count, created_at) VALUES (?,?,?,?,?,?,?,?)",
                (name, filename, fmt, size, note, len(words),
                 len({w['unit'] for w in words}), ts),
            )
            mid = cur.lastrowid
            conn.executemany(
                "INSERT INTO material_words(material_id, unit, en, cn, ipa, pos, ord) "
                "VALUES (?,?,?,?,?,?,?)",
                [(mid, w["unit"], w["en"], w["cn"], w.get("ipa", ""),
                  w.get("pos", ""), i) for i, w in enumerate(words)],
            )
        return mid

    def list_materials(self) -> list[dict]:
        rows = self.query("SELECT * FROM materials ORDER BY id DESC")
        return [dict(r) for r in rows]

    def get_material(self, mid: int) -> dict | None:
        row = self.one("SELECT * FROM materials WHERE id=?", (mid,))
        return dict(row) if row else None

    def material_words(self, mid: int) -> list[dict]:
        rows = self.query(
            "SELECT unit, en, cn, ipa, pos FROM material_words "
            "WHERE material_id=? ORDER BY ord", (mid,))
        return [dict(r) for r in rows]

    def delete_material(self, mid: int) -> bool:
        if not self.get_material(mid):
            return False
        with self._tx() as conn:
            conn.execute("DELETE FROM material_words WHERE material_id=?", (mid,))
            conn.execute("DELETE FROM materials WHERE id=?", (mid,))
        return True

    # ---------------- banks ----------------

    def insert_bank(self, meta: dict, words: list[dict]) -> int:
        ts = now_iso()
        with self._tx() as conn:
            cur = conn.execute(
                "INSERT INTO banks(title, level1, level2, level3, level4, source, "
                "material_id, unit_mode, unit_from, unit_to, pairs_per_level, "
                "word_count, unit_count, created_at, owner_id) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (meta["title"], meta["level1"], meta["level2"], meta["level3"],
                 meta["level4"], meta["source"], meta.get("material_id"),
                 meta.get("unit_mode", "all"), meta.get("unit_from", 0),
                 meta.get("unit_to", 0),
                 int(meta.get("pairs_per_level") or 12), len(words),
                 len({w["unit"] for w in words}), ts, meta.get("owner_id")),
            )
            bid = cur.lastrowid
            conn.executemany(
                "INSERT INTO bank_words(bank_id, unit, en, cn, ipa, pos, ord) "
                "VALUES (?,?,?,?,?,?,?)",
                [(bid, w["unit"], w["en"], w["cn"], w.get("ipa", ""),
                  w.get("pos", ""), i) for i, w in enumerate(words)],
            )
        return bid

    def list_banks(self, visible_to: int | None = None) -> list[dict]:
        """visible_to=None 返回全部；给了用户 id 就只返回系统题库和他自己的。"""
        if visible_to is None:
            rows = self.query("SELECT * FROM banks ORDER BY id DESC")
        else:
            rows = self.query(
                "SELECT * FROM banks WHERE owner_id IS NULL OR owner_id=? ORDER BY id DESC",
                (visible_to,))
        return [dict(r) for r in rows]

    def get_bank(self, bid: int) -> dict | None:
        row = self.one("SELECT * FROM banks WHERE id=?", (bid,))
        return dict(row) if row else None

    def bank_words(self, bid: int) -> list[dict]:
        rows = self.query(
            "SELECT unit, en, cn, ipa, pos FROM bank_words WHERE bank_id=? ORDER BY ord",
            (bid,))
        return [dict(r) for r in rows]

    def delete_bank(self, bid: int) -> bool:
        if not self.get_bank(bid):
            return False
        with self._tx() as conn:
            conn.execute("DELETE FROM bank_words WHERE bank_id=?", (bid,))
            conn.execute("DELETE FROM banks WHERE id=?", (bid,))
        return True

    # ---------------- scores ----------------

    def insert_score(self, rec: dict, user_id: int | None = None) -> int:
        ts = now_iso()
        detail = rec.get("detail")
        if not isinstance(detail, str):
            detail = json.dumps(detail or [], ensure_ascii=False)
        with self._tx() as conn:
            cur = conn.execute(
                "INSERT INTO scores(bank_id, bank_title, device, nickname, mode, "
                "score, matched, total_pairs, wrong, best_combo, duration, "
                "level_count, detail, created_at, user_id) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (rec.get("bank_id"), rec.get("bank_title", ""),
                 rec.get("device", ""), rec.get("nickname", ""),
                 rec.get("mode", "online"), int(rec.get("score", 0)),
                 int(rec.get("matched", 0)), int(rec.get("total_pairs", 0)),
                 int(rec.get("wrong", 0)), int(rec.get("best_combo", 0)),
                 int(rec.get("duration", 0)), int(rec.get("level_count", 0)),
                 detail, ts, user_id),
            )
        return int(cur.lastrowid)

    def list_scores(self, limit: int = 200, bank_id: int | None = None,
                    user_id: int | None = None) -> list[dict]:
        where, args = [], []
        if bank_id is not None:
            where.append("bank_id=?")
            args.append(bank_id)
        if user_id is not None:
            where.append("user_id=?")
            args.append(user_id)
        sql = "SELECT * FROM scores"
        if where:
            sql += " WHERE " + " AND ".join(where)
        rows = self.query(sql + " ORDER BY id DESC LIMIT ?", (*args, limit))
        out = []
        for r in rows:
            d = dict(r)
            try:
                d["detail"] = json.loads(d.get("detail") or "[]")
            except (ValueError, TypeError):
                d["detail"] = []
            out.append(d)
        return out

    def score_stats(self, user_id: int | None = None) -> dict:
        cond, args = ("WHERE user_id=?", (user_id,)) if user_id is not None else ("", ())
        row = self.one(
            "SELECT COUNT(*) AS n, COALESCE(SUM(score),0) AS total, "
            "COALESCE(MAX(score),0) AS best, COALESCE(AVG(score),0) AS avg "
            "FROM scores " + cond, args)
        by_bank = self.query(
            "SELECT bank_title, COUNT(*) AS n, MAX(score) AS best, "
            "COALESCE(SUM(score),0) AS total FROM scores " + cond +
            " GROUP BY bank_title ORDER BY total DESC LIMIT 20", args)
        return {
            "count": row["n"] if row else 0,
            "total": row["total"] if row else 0,
            "best": row["best"] if row else 0,
            "avg": round(row["avg"], 1) if row else 0,
            "by_bank": [dict(r) for r in by_bank],
        }
