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
import re
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
    pairs_per_level INTEGER DEFAULT 9,   -- 一关最多多少词
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

-- 学生版（WP_AUTH=1）才会用到的账号表；家庭版里这两张表是空的
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

-- 标签：学生和题库各自带一组标签，两边至少有一个相同，学生才能看到、打开这个题库。
-- 没打标签的题库学生看不到（老师始终看得到全部）。
-- 标签按老师分开（teacher_id）：A 老师的「一班」和 B 老师的「一班」互不相干。
-- 学生能看到题库 = 同一位老师给这个学生和这个题库打了同一个标签。teacher_id = 0 只出现在没有账号体系的家庭版里。
CREATE TABLE IF NOT EXISTS user_tags (
    user_id    INTEGER NOT NULL,
    tag        TEXT NOT NULL,
    teacher_id INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, tag, teacher_id)
);
CREATE TABLE IF NOT EXISTS bank_tags (
    bank_id    INTEGER NOT NULL,
    tag        TEXT NOT NULL,
    teacher_id INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (bank_id, tag, teacher_id)
);

-- 多位老师：底层的学生、题库、成绩都在一起，上层靠这两张表决定「哪位老师能看到 / 管理什么」。
-- 一个学生 / 题库可以挂在多位老师名下（共享）；超级管理员（role=admin）不受这两张表限制，什么都看得到。
CREATE TABLE IF NOT EXISTS teacher_students (
    teacher_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    added_at   INTEGER NOT NULL DEFAULT 0,       -- UTC 秒
    added_by   INTEGER,
    PRIMARY KEY (teacher_id, student_id)
);
CREATE INDEX IF NOT EXISTS ix_ts_student ON teacher_students(student_id);
-- 共享申请：导入名单时发现学号已属于别的老师，不再自动挂过去，而是提交申请，由负责这个学生的老师（或超管）批准。
CREATE TABLE IF NOT EXISTS share_requests (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id   INTEGER NOT NULL,
    requester_id INTEGER NOT NULL,
    status       TEXT NOT NULL DEFAULT 'pending',   -- pending / approved / rejected
    created_at   INTEGER NOT NULL DEFAULT 0,
    decided_at   INTEGER NOT NULL DEFAULT 0,
    decided_by   INTEGER
);
CREATE INDEX IF NOT EXISTS ix_sr_status ON share_requests(status, student_id);
CREATE TABLE IF NOT EXISTS teacher_banks (     -- 共享给这位老师的题库（自己建的题库看 banks.owner_id）
    teacher_id INTEGER NOT NULL,
    bank_id    INTEGER NOT NULL,
    added_at   INTEGER NOT NULL DEFAULT 0,
    added_by   INTEGER,
    PRIMARY KEY (teacher_id, bank_id)
);
CREATE INDEX IF NOT EXISTS ix_tb_bank ON teacher_banks(bank_id);

-- 审计记录：谁在什么时候建了老师、共享 / 分配了什么、删了 / 恢复了什么。只增不删。
CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          INTEGER NOT NULL,                -- UTC 秒
    actor_id    INTEGER,
    action      TEXT NOT NULL,                   -- teacher.create / bank.share / student.move / bank.delete / … / student.auto_share
    target_type TEXT NOT NULL DEFAULT '',        -- user / bank / material
    target_id   INTEGER,
    detail      TEXT NOT NULL DEFAULT '{}'       -- JSON
);
CREATE INDEX IF NOT EXISTS ix_audit_ts ON audit_log(ts);
CREATE INDEX IF NOT EXISTS ix_bank_tags_tag ON bank_tags(tag);

-- 每个账号最近打开过的题库（首页「最近玩过」，跨设备）：同一个题库一行，只留最近 8 个。
CREATE TABLE IF NOT EXISTS recent_banks (
    user_id INTEGER NOT NULL,
    bank_id INTEGER NOT NULL,
    last_at INTEGER NOT NULL,                        -- UTC 秒
    opens   INTEGER NOT NULL DEFAULT 1,
    seq     INTEGER NOT NULL DEFAULT 0,              -- 全表递增的顺序号：同一秒里先后打开的，也分得出谁更近
    PRIMARY KEY (user_id, bank_id)
);
CREATE INDEX IF NOT EXISTS ix_recent_user ON recent_banks(user_id, last_at);

-- 各学科（化学、物理、话题、无线电……）通用的成绩 / 进度记录：模块只管 POST，不用各建一张表。
CREATE TABLE IF NOT EXISTS subject_records (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER,                              -- 没登录（家庭版内网入口）为空，用 device 区分
    device     TEXT NOT NULL DEFAULT '',
    subject    TEXT NOT NULL,                        -- server/modules.py 里登记的模块 id
    kind       TEXT NOT NULL DEFAULT '',             -- 模块自己定义：quiz / exercise / progress …
    payload    TEXT NOT NULL DEFAULT '{}',           -- JSON，上限 20 KB
    created_at INTEGER NOT NULL                      -- UTC 秒
);
CREATE INDEX IF NOT EXISTS ix_records_subject ON subject_records(subject, created_at);
CREATE INDEX IF NOT EXISTS ix_records_user ON subject_records(user_id, created_at);

-- 访问记录：谁、从哪个 IP、用什么设备和浏览器、看了哪些页面、停留多久。永久保留，不自动删除。
-- 时间一律存 UTC 秒数（整数）：这几张表里的时间不受服务器时区影响，页面上由浏览器换成本地时间。
-- 一行 page_views = 一次页面打开（vid 是页面自己生成的随机号）；sid 是同一个浏览器标签页的会话号，
-- 把同一次访问里先后打开的页面串起来。
CREATE TABLE IF NOT EXISTS page_views (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    vid            TEXT NOT NULL UNIQUE,
    sid            TEXT NOT NULL,
    user_id        INTEGER,
    role           TEXT NOT NULL DEFAULT '',          -- student | admin | 空 = 没登录
    student_no     TEXT NOT NULL DEFAULT '',          -- 当时的学号 / 姓名 / 班级（以后账号改了，这里还是当时的样子）
    name           TEXT NOT NULL DEFAULT '',
    class_name     TEXT NOT NULL DEFAULT '',
    ip             TEXT NOT NULL DEFAULT '',
    forwarded      TEXT NOT NULL DEFAULT '{}',        -- 收到的转发头（JSON），查 IP 来源用
    user_agent     TEXT NOT NULL DEFAULT '',
    browser        TEXT NOT NULL DEFAULT '',
    browser_version TEXT NOT NULL DEFAULT '',
    os             TEXT NOT NULL DEFAULT '',
    os_version     TEXT NOT NULL DEFAULT '',
    device_type    TEXT NOT NULL DEFAULT '',          -- mobile | tablet | desktop | bot
    device_model   TEXT NOT NULL DEFAULT '',
    in_app         TEXT NOT NULL DEFAULT '',          -- 微信 / 钉钉 / QQ …（内置浏览器）
    accept_language TEXT NOT NULL DEFAULT '',
    path           TEXT NOT NULL DEFAULT '',
    title          TEXT NOT NULL DEFAULT '',
    referrer       TEXT NOT NULL DEFAULT '',
    client_info    TEXT NOT NULL DEFAULT '{}',        -- 页面报上来的屏幕、时区、语言、CPU 核数、网络类型 …（JSON）
    started_at     INTEGER NOT NULL,
    last_seen_at   INTEGER NOT NULL,
    active_seconds INTEGER NOT NULL DEFAULT 0,        -- 页面在前台的累计秒数（最能代表「停留多久」）
    pings          INTEGER NOT NULL DEFAULT 0,
    ended          INTEGER NOT NULL DEFAULT 0         -- 1 = 页面关闭 / 离开时报过
);
CREATE INDEX IF NOT EXISTS ix_pv_started ON page_views(started_at);
CREATE INDEX IF NOT EXISTS ix_pv_sid ON page_views(sid);
CREATE INDEX IF NOT EXISTS ix_pv_user ON page_views(user_id, started_at);

-- 登录记录：成功和失败都记（失败的也记下试的是哪个学号、从哪来）。
CREATE TABLE IF NOT EXISTS login_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          INTEGER NOT NULL,
    student_no  TEXT NOT NULL DEFAULT '',             -- 输入的学号
    user_id     INTEGER,                              -- 学号存在才有
    name        TEXT NOT NULL DEFAULT '',
    class_name  TEXT NOT NULL DEFAULT '',
    success     INTEGER NOT NULL DEFAULT 0,
    code        TEXT NOT NULL DEFAULT '',             -- 失败原因（invalid_credentials / rate_limited / 账号锁定 …）
    ip          TEXT NOT NULL DEFAULT '',
    forwarded   TEXT NOT NULL DEFAULT '{}',
    user_agent  TEXT NOT NULL DEFAULT '',
    browser     TEXT NOT NULL DEFAULT '',
    browser_version TEXT NOT NULL DEFAULT '',
    os          TEXT NOT NULL DEFAULT '',
    os_version  TEXT NOT NULL DEFAULT '',
    device_type TEXT NOT NULL DEFAULT '',
    device_model TEXT NOT NULL DEFAULT '',
    in_app      TEXT NOT NULL DEFAULT '',
    accept_language TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS ix_login_ts ON login_events(ts);
CREATE INDEX IF NOT EXISTS ix_login_user ON login_events(user_id, ts);

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


MAX_TAGS = 10
MAX_TAG_LENGTH = 20
MAX_CATEGORY_LENGTH = 20
_TAG_SPLIT = re.compile(r"[,，、;；\n]+")


class TagError(ValueError):
    """标签或分类不合法，message 直接展示给用户。"""


def normalize_tags(value: Any) -> list[str]:
    """把「初二, 三班」或 ["初二", "三班"] 整理成去重、去空白的标签列表（保持先后顺序）。

    不合法（太长、太多）就抛 TagError，而不是悄悄截断：悄悄丢掉一个标签，
    学生就会莫名其妙看不到题库。
    """
    if value is None:
        return []
    items = _TAG_SPLIT.split(value) if isinstance(value, str) else list(value)
    out: list[str] = []
    for item in items:
        tag = re.sub(r"\s+", " ", str(item or "")).strip()
        if not tag or tag in out:
            continue
        if len(tag) > MAX_TAG_LENGTH:
            raise TagError("标签太长了（最多 %d 个字）：%s" % (MAX_TAG_LENGTH, tag[:12] + "…"))
        out.append(tag)
    if len(out) > MAX_TAGS:
        raise TagError("标签太多了（最多 %d 个）" % MAX_TAGS)
    return out


def normalize_category(value: Any) -> str:
    category = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(category) > MAX_CATEGORY_LENGTH:
        raise TagError("分类名太长了（最多 %d 个字）" % MAX_CATEGORY_LENGTH)
    return category


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
                         "pairs_per_level INTEGER DEFAULT 9")
        if "owner_id" not in columns:
            # NULL = 系统题库（所有人可见）；否则是创建者的用户 id
            self.execute("ALTER TABLE banks ADD COLUMN owner_id INTEGER")
        if "seq" not in columns:
            # 同一分类（一本书）里的顺序：把一本书按单元拆成多个题库时，第几单元就是几
            self.execute("ALTER TABLE banks ADD COLUMN seq INTEGER NOT NULL DEFAULT 0")
        if "category" not in columns:
            # 分类：只用来整理和浏览，不参与权限（权限只看标签）
            self.execute("ALTER TABLE banks ADD COLUMN category TEXT NOT NULL DEFAULT ''")
        # 软删除：只打标记（UTC 秒），老师和学生看不到，超级管理员能看到并恢复
        for table in ("banks", "users", "materials"):
            cols = {row["name"] for row in self.query("PRAGMA table_info(%s)" % table)}
            if "deleted_at" not in cols:
                self.execute("ALTER TABLE %s ADD COLUMN deleted_at INTEGER NOT NULL DEFAULT 0" % table)
            if "deleted_by" not in cols:
                self.execute("ALTER TABLE %s ADD COLUMN deleted_by INTEGER" % table)
        if "teacher_group" not in {row["name"] for row in self.query("PRAGMA table_info(users)")}:
            # 教研组：同一组的老师之间导入同一个学号时自动共享（不用逐个批准）；空 = 不在任何组
            self.execute("ALTER TABLE users ADD COLUMN teacher_group TEXT NOT NULL DEFAULT ''")
        if "owner_id" not in {row["name"] for row in self.query("PRAGMA table_info(materials)")}:
            self.execute("ALTER TABLE materials ADD COLUMN owner_id INTEGER")     # 谁上传的；老师只看得到自己的
        # 老库的标签表没有 teacher_id：重建成带 teacher_id 的，原有标签归第一位超级管理员
        for table, key in (("user_tags", "user_id"), ("bank_tags", "bank_id")):
            if "teacher_id" not in {row["name"] for row in self.query("PRAGMA table_info(%s)" % table)}:
                owner = self.default_teacher_id()
                with self._tx() as conn:
                    conn.execute("ALTER TABLE %s RENAME TO %s_old" % (table, table))
                    conn.execute("CREATE TABLE %s (%s INTEGER NOT NULL, tag TEXT NOT NULL, "
                                 "teacher_id INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (%s, tag, teacher_id))" % (table, key, key))
                    conn.execute("INSERT INTO %s(%s, tag, teacher_id) SELECT %s, tag, ? FROM %s_old" % (table, key, key, table), (owner,))
                    conn.execute("DROP TABLE %s_old" % table)
        self.execute("CREATE INDEX IF NOT EXISTS ix_bank_tags_tag ON bank_tags(tag)")
        self.execute("CREATE INDEX IF NOT EXISTS ix_user_tags_teacher ON user_tags(teacher_id, tag)")
        self.execute("CREATE INDEX IF NOT EXISTS ix_bank_tags_teacher ON bank_tags(teacher_id, tag)")
        score_columns = {row["name"] for row in self.query("PRAGMA table_info(scores)")}
        if "user_id" not in score_columns:
            self.execute("ALTER TABLE scores ADD COLUMN user_id INTEGER")
            self.execute("CREATE INDEX IF NOT EXISTS ix_scores_user ON scores(user_id)")
        # v1（2026-11）：每关默认词数 12 → 9（手机竖屏一屏正好放下 3×6 张卡）。
        # 只改还是旧默认值 12 的题库；老师特意设成别的数的不动；只做一次（user_version 记着）。
        if self.one("PRAGMA user_version")[0] < 1:
            self.execute("UPDATE banks SET pairs_per_level=9 WHERE pairs_per_level=12")
            self.execute("PRAGMA user_version = 1")
        # v2（2026-11）：多位老师。已有的学生都挂到第一位超级管理员名下（她原来就管着所有学生），只做一次。
        if self.one("PRAGMA user_version")[0] < 2:
            owner = self.default_teacher_id()
            if owner:
                self.execute("INSERT OR IGNORE INTO teacher_students(teacher_id, student_id, added_at) "
                             "SELECT ?, id, ? FROM users WHERE role='student'", (owner, int(time.time())))
            self.execute("PRAGMA user_version = 2")

    def default_teacher_id(self) -> int:
        """第一位（编号最小的）没被删除的超级管理员；没有就是 0（家庭版、或者还没建管理员）。
        没指明是哪位老师的标签（命令行导入、老接口）都算在她名下。"""
        try:
            row = self.one("SELECT MIN(id) AS id FROM users WHERE role='admin' AND deleted_at=0")
        except sqlite3.OperationalError:          # 迁移到一半：users 还没有 deleted_at
            row = self.one("SELECT MIN(id) AS id FROM users WHERE role='admin'")
        return int(row["id"]) if row and row["id"] else 0

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
                        note: str, words: list[dict], owner_id: int | None = None) -> int:
        ts = now_iso()
        with self._tx() as conn:
            cur = conn.execute(
                "INSERT INTO materials(name, filename, fmt, size, note, "
                "word_count, unit_count, created_at, owner_id) VALUES (?,?,?,?,?,?,?,?,?)",
                (name, filename, fmt, size, note, len(words),
                 len({w['unit'] for w in words}), ts, owner_id),
            )
            mid = cur.lastrowid
            conn.executemany(
                "INSERT INTO material_words(material_id, unit, en, cn, ipa, pos, ord) "
                "VALUES (?,?,?,?,?,?,?)",
                [(mid, w["unit"], w["en"], w["cn"], w.get("ipa", ""),
                  w.get("pos", ""), i) for i, w in enumerate(words)],
            )
        return mid

    def list_materials(self, where: str = "", args: Iterable[Any] = ()) -> list[dict]:
        sql = "SELECT * FROM materials" + (" WHERE " + where if where else "")
        return [dict(r) for r in self.query(sql + " ORDER BY id DESC", tuple(args))]

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
                "word_count, unit_count, created_at, owner_id, seq) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (meta["title"], meta["level1"], meta["level2"], meta["level3"],
                 meta["level4"], meta["source"], meta.get("material_id"),
                 meta.get("unit_mode", "all"), meta.get("unit_from", 0),
                 meta.get("unit_to", 0),
                 int(meta.get("pairs_per_level") or 9), len(words),
                 len({w["unit"] for w in words}), ts, meta.get("owner_id"), int(meta.get("seq") or 0)),
            )
            bid = cur.lastrowid
            conn.executemany(
                "INSERT INTO bank_words(bank_id, unit, en, cn, ipa, pos, ord) "
                "VALUES (?,?,?,?,?,?,?)",
                [(bid, w["unit"], w["en"], w["cn"], w.get("ipa", ""),
                  w.get("pos", ""), i) for i, w in enumerate(words)],
            )
        return bid

    def list_banks(self, where: str = "", args: Iterable[Any] = (), tag_teacher: int | None = None) -> list[dict]:
        """题库列表（含软删除的，谁能看到由调用方传进来的 where 决定，见 server/tenancy.py）。

        每个题库带上 ``tags``：tag_teacher 给了就只是这位老师打的标签（老师只看得到自己的），
        不给就是所有老师打的标签合在一起（内部用，比如重建内置题库时带走标签）。"""
        sql = "SELECT b.* FROM banks b"
        if where:
            sql += " WHERE " + where
        banks = [dict(r) for r in self.query(sql + " ORDER BY b.id DESC", tuple(args))]
        by_bank: dict[int, list[str]] = {}
        if tag_teacher is None:
            rows = self.query("SELECT DISTINCT bank_id, tag FROM bank_tags ORDER BY tag")
        else:
            rows = self.query("SELECT bank_id, tag FROM bank_tags WHERE teacher_id=? ORDER BY tag", (tag_teacher,))
        for row in rows:
            by_bank.setdefault(row["bank_id"], []).append(row["tag"])
        for bank in banks:
            bank["tags"] = by_bank.get(bank["id"], [])
        return banks

    def list_banks_by_id(self, bid: int, tag_teacher: int | None = None) -> dict | None:
        """单个题库（带标签），给改完分类 / 标签后回传用。"""
        found = self.list_banks("b.id=?", (bid,), tag_teacher=tag_teacher)
        return found[0] if found else None

    # ---------------- 标签 ----------------

    def bank_tags(self, bid: int, teacher_id: int | None = None) -> list[str]:
        if teacher_id is None:
            return [r["tag"] for r in self.query("SELECT DISTINCT tag FROM bank_tags WHERE bank_id=? ORDER BY tag", (bid,))]
        return [r["tag"] for r in self.query(
            "SELECT tag FROM bank_tags WHERE bank_id=? AND teacher_id=? ORDER BY tag", (bid, teacher_id))]

    def bank_tag_rows(self, bid: int) -> list[tuple[str, int]]:
        """所有老师在这个题库上的标签（重建内置题库时原样带过去）。"""
        return [(r["tag"], r["teacher_id"]) for r in self.query(
            "SELECT tag, teacher_id FROM bank_tags WHERE bank_id=?", (bid,))]

    def put_bank_tag_rows(self, bid: int, rows: list[tuple[str, int]]) -> None:
        self.executemany("INSERT OR IGNORE INTO bank_tags(bank_id, tag, teacher_id) VALUES (?,?,?)",
                         [(bid, tag, teacher) for tag, teacher in rows])

    def _teacher(self, teacher_id: int | None) -> int:
        return self.default_teacher_id() if teacher_id is None else int(teacher_id)

    def set_bank_meta(self, bid: int, category: str | None, tags: list[str] | None,
                      teacher_id: int | None = None) -> bool:
        """改题库的分类和标签；传 None 的那一项保持不变。标签只改这位老师自己的（别的老师打的不动）。"""
        if not self.get_bank(bid):
            return False
        teacher = self._teacher(teacher_id)
        with self._tx() as conn:
            if category is not None:
                conn.execute("UPDATE banks SET category=? WHERE id=?", (category, bid))
            if tags is not None:
                conn.execute("DELETE FROM bank_tags WHERE bank_id=? AND teacher_id=?", (bid, teacher))
                conn.executemany("INSERT INTO bank_tags(bank_id, tag, teacher_id) VALUES (?, ?, ?)",
                                 [(bid, t, teacher) for t in tags])
        return True

    def change_bank_tags(self, bank_ids: Iterable[int], add: list[str], remove: list[str],
                         teacher_id: int | None = None) -> int:
        """批量给一批题库加 / 去这位老师的标签（「批量开放」用）。返回实际存在的题库数。"""
        teacher = self._teacher(teacher_id)
        ids = [i for i in bank_ids if self.get_bank(i)]
        with self._tx() as conn:
            conn.executemany("INSERT OR IGNORE INTO bank_tags(bank_id, tag, teacher_id) VALUES (?, ?, ?)",
                             [(b, t, teacher) for b in ids for t in add])
            conn.executemany("DELETE FROM bank_tags WHERE bank_id=? AND tag=? AND teacher_id=?",
                             [(b, t, teacher) for b in ids for t in remove])
        return len(ids)

    def all_tags(self, teacher_id: int | None = None) -> list[dict]:
        """这位老师用过的标签，以及有多少学生 / 多少题库带着它（老师挑「开放给谁」时用）。
        只数还在的学生和题库（软删除的不算）。"""
        teacher = self._teacher(teacher_id)
        out: dict[str, dict] = {}
        for row in self.query("SELECT ut.tag, COUNT(*) AS n FROM user_tags ut JOIN users u ON u.id=ut.user_id "
                              "WHERE ut.teacher_id=? AND u.deleted_at=0 GROUP BY ut.tag", (teacher,)):
            out.setdefault(row["tag"], {"tag": row["tag"], "students": 0, "banks": 0})["students"] = row["n"]
        for row in self.query("SELECT bt.tag, COUNT(*) AS n FROM bank_tags bt JOIN banks b ON b.id=bt.bank_id "
                              "WHERE bt.teacher_id=? AND b.deleted_at=0 GROUP BY bt.tag", (teacher,)):
            out.setdefault(row["tag"], {"tag": row["tag"], "students": 0, "banks": 0})["banks"] = row["n"]
        return sorted(out.values(), key=lambda t: (-t["students"], t["tag"]))

    def user_tags_map(self, user_ids: Iterable[int] | None = None, teacher_id: int | None = None) -> dict[int, list[str]]:
        teacher = self._teacher(teacher_id)
        rows = self.query("SELECT user_id, tag FROM user_tags WHERE teacher_id=? ORDER BY tag", (teacher,))
        wanted = None if user_ids is None else set(user_ids)
        out: dict[int, list[str]] = {}
        for row in rows:
            if wanted is None or row["user_id"] in wanted:
                out.setdefault(row["user_id"], []).append(row["tag"])
        return out

    def set_user_tags(self, user_id: int, tags: list[str], teacher_id: int | None = None) -> None:
        """整组替换这位老师给这个学生打的标签（别的老师打的不动）。teacher_id 不给 = 第一位超级管理员。"""
        teacher = self._teacher(teacher_id)
        with self._tx() as conn:
            conn.execute("DELETE FROM user_tags WHERE user_id=? AND teacher_id=?", (user_id, teacher))
            conn.executemany("INSERT INTO user_tags(user_id, tag, teacher_id) VALUES (?, ?, ?)",
                             [(user_id, t, teacher) for t in tags])

    def change_user_tags(self, user_ids: Iterable[int], add: list[str], remove: list[str],
                         teacher_id: int | None = None) -> None:
        """批量给一批用户加 / 去这位老师的标签。"""
        teacher = self._teacher(teacher_id)
        ids = list(user_ids)
        with self._tx() as conn:
            conn.executemany("INSERT OR IGNORE INTO user_tags(user_id, tag, teacher_id) VALUES (?, ?, ?)",
                             [(u, t, teacher) for u in ids for t in add])
            conn.executemany("DELETE FROM user_tags WHERE user_id=? AND tag=? AND teacher_id=?",
                             [(u, t, teacher) for u in ids for t in remove])

    def get_bank(self, bid: int) -> dict | None:
        row = self.one("SELECT * FROM banks WHERE id=?", (bid,))
        return dict(row) if row else None

    def bank_words(self, bid: int) -> list[dict]:
        rows = self.query(
            "SELECT unit, en, cn, ipa, pos FROM bank_words WHERE bank_id=? ORDER BY ord",
            (bid,))
        return [dict(r) for r in rows]

    def delete_bank(self, bid: int) -> bool:
        """真正删掉（只在内部重建内置题库时用）。老师和管理员的「删除」是软删除，见 server/tenancy.py。"""
        if not self.get_bank(bid):
            return False
        with self._tx() as conn:
            conn.execute("DELETE FROM bank_words WHERE bank_id=?", (bid,))
            conn.execute("DELETE FROM bank_tags WHERE bank_id=?", (bid,))
            conn.execute("DELETE FROM teacher_banks WHERE bank_id=?", (bid,))
            conn.execute("DELETE FROM recent_banks WHERE bank_id=?", (bid,))
            conn.execute("DELETE FROM banks WHERE id=?", (bid,))
        return True

    # ---------------- 最近打开过的题库 ----------------

    RECENT_KEEP = 8

    def touch_recent(self, user_id: int, bank_id: int, now: int) -> None:
        """记一笔：这个账号刚打开了这个题库。同一个题库只有一行；每个账号只留最近 RECENT_KEEP 个。"""
        with self._tx() as conn:
            conn.execute(
                "INSERT INTO recent_banks(user_id, bank_id, last_at, opens, seq) "
                "VALUES (?,?,?,1,(SELECT COALESCE(MAX(seq),0)+1 FROM recent_banks)) "
                "ON CONFLICT(user_id, bank_id) DO UPDATE SET last_at=excluded.last_at, opens=opens+1, seq=excluded.seq",
                (user_id, bank_id, now))
            conn.execute(
                "DELETE FROM recent_banks WHERE user_id=? AND bank_id NOT IN "
                "(SELECT bank_id FROM recent_banks WHERE user_id=? ORDER BY last_at DESC, seq DESC LIMIT ?)",
                (user_id, user_id, self.RECENT_KEEP))

    def recent_rows(self, user_id: int) -> list[dict]:
        rows = self.query("SELECT bank_id, last_at FROM recent_banks WHERE user_id=? ORDER BY last_at DESC, seq DESC",
                          (user_id,))
        return [dict(r) for r in rows]

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
                    user_id: int | None = None, people: tuple[str, tuple] | None = None) -> list[dict]:
        """people：按人过滤的 SQL 片段（server/tenancy.py 的 people_where，列名 user_id）。"""
        where, args = [], []
        if people is not None:
            where.append(people[0]); args += list(people[1])
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

    def score_stats(self, user_id: int | None = None, people: tuple[str, tuple] | None = None) -> dict:
        parts, args = [], []
        if user_id is not None:
            parts.append("user_id=?"); args.append(user_id)
        if people is not None:
            parts.append(people[0]); args += list(people[1])
        cond, args = ("WHERE " + " AND ".join(parts) if parts else ""), tuple(args)
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
