"""奖状和徽章：在周榜上累计 10 / 15 / 30 天是榜首，就发一张奖状（铜、银、金），学生的「我的」页面里有对应的徽章。

* 周榜：某一天的榜首 = 那一周（周一 00:00 起，北京时间）到这一天结束为止，积分最高的人。每周一重新开始，
  所以早期领先的人不会一直压着别人；并列第一都算。积分必须大于 0。
* 榜 = 学生自己看到的那个：超管设了总榜就是总榜（参加总榜的那些班），否则是自己的班
  （班级名 + 负责他的老师，不同学校的「一班」不混在一起）。
* 四个榜各算各的：总分，以及中英配对、单词大比拼、排排坐各自的积分。
* 累计天数：一个学生在某个榜上当过多少天榜首（不要求连续，跨周接着算）。正好到 10 / 15 / 30 天，
  发铜 / 银 / 金奖状；每个档次在一个榜上只发一次。
* 一天 = 北京时间的一个自然日；一天结束后才结算那一天。
* 结算是「用到时补算」：有人打开积分榜或「我的」时，把还没结算的日子按顺序补上（最多往前 MAX_BACKFILL 天）。
* 规则版本记在 app_settings（awards_rules）：规则改了，旧规则算出的榜首记录作废、从头补算（已经发出的奖状不动）。
"""
from __future__ import annotations

import datetime
import threading
import time

from . import leaderboard, tenancy
from .db import Database

THRESHOLDS = (10, 15, 30)
RULES = "weekly-cumulative-10-15-30"          # 规则版本：改了规则就换一个名字，旧的榜首记录会作废重算


def tier_of(days: int) -> str:
    """档次：不到 15 天铜，不到 30 天银，30 天金（也兼容以前发过的别的天数）。"""
    return "gold" if days >= 30 else "silver" if days >= 15 else "bronze"

GAMES = ("all", "match", "spell", "order")
MAX_BACKFILL = 120
_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS award_days (day TEXT PRIMARY KEY, done_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS board_leaders (
    day TEXT NOT NULL, board TEXT NOT NULL, game TEXT NOT NULL, user_id INTEGER NOT NULL, points INTEGER NOT NULL,
    PRIMARY KEY (day, board, game, user_id)
);
CREATE TABLE IF NOT EXISTS awards (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    game        TEXT NOT NULL,          -- all / match / spell / order
    days        INTEGER NOT NULL,       -- 5 / 15 / 30
    board       TEXT NOT NULL,          -- 哪个榜（overall，或 t<老师>|<班级>）
    board_label TEXT NOT NULL,          -- 发奖状时这个榜的名字（总榜标题或班级名）
    start_day   TEXT NOT NULL,
    end_day     TEXT NOT NULL,
    created_at  INTEGER NOT NULL,
    seen        INTEGER NOT NULL DEFAULT 0,
    UNIQUE (user_id, game, days, board, start_day)
);
CREATE INDEX IF NOT EXISTS ix_awards_user ON awards(user_id, created_at);
"""


def ensure(db: Database) -> None:
    with db._lock:
        db._conn.executescript(SCHEMA)
        db._conn.commit()
    row = db.one("SELECT value FROM app_settings WHERE key='awards_rules'")
    if not row or row["value"] != RULES:
        # 规则变了（或第一次）：旧规则算出的榜首记录和结算进度作废，从头补算；已经发出的奖状不动
        db.execute("DELETE FROM board_leaders")
        db.execute("DELETE FROM award_days")
        db.execute("INSERT INTO app_settings(key, value, updated_at, updated_by) VALUES ('awards_rules', ?, ?, NULL) "
                   "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at", (RULES, int(time.time())))


def _day(d: datetime.date) -> str:
    return d.strftime("%Y-%m-%d")


def _today(now: float | None = None) -> datetime.date:
    return datetime.date.fromtimestamp(now if now is not None else time.time())


def boards(db: Database) -> list[dict]:
    """现在有哪些榜：[{key, label, members:set}]。设了总榜就只有总榜（学生看到的就是它）。"""
    cfg = leaderboard.get_config(db)
    students = db.query("SELECT id, class_name FROM users WHERE role='student' AND deleted_at=0 AND disabled=0")
    if cfg["classes"]:
        wanted = set(cfg["classes"])
        return [{"key": "overall", "label": cfg["title"] or "", "members": {r["id"] for r in students if r["class_name"] in wanted}}]
    primary = tenancy.primary_map(db)
    groups: dict[str, dict] = {}
    for r in students:
        if not r["class_name"] or r["id"] not in primary:
            continue
        teacher = primary[r["id"]][0]
        key = "t%d|%s" % (teacher, r["class_name"])
        groups.setdefault(key, {"key": key, "label": r["class_name"], "members": set()})["members"].add(r["id"])
    return list(groups.values())


def _week_points(db: Database, day: datetime.date, game: str) -> dict[int, int]:
    """这一天所在那一周（周一 00:00 起）到这一天结束，每个学生的积分（scores.created_at 是北京时间的字符串，直接比较）。"""
    monday = day - datetime.timedelta(days=day.weekday())
    start = _day(monday) + " 00:00:00"
    end = _day(day + datetime.timedelta(days=1)) + " 00:00:00"
    sql = "SELECT user_id, SUM(score) AS p FROM scores WHERE user_id IS NOT NULL AND created_at >= ? AND created_at < ?"
    args: list = [start, end]
    if game != "all":
        sql += " AND game_type=?"
        args.append(game)
    return {r["user_id"]: r["p"] or 0 for r in db.query(sql + " GROUP BY user_id", args)}


def _top_days(db: Database, board: str, game: str, user_id: int, day: datetime.date) -> tuple[int, str]:
    """到这一天（含）为止，这个学生在这个榜上当了多少天榜首，以及第一次是哪天。"""
    row = db.one("SELECT COUNT(*) AS n, MIN(day) AS first FROM board_leaders WHERE board=? AND game=? AND user_id=? AND day<=?",
                 (board, game, user_id, _day(day)))
    return row["n"], row["first"] or _day(day)


def settle_day(db: Database, day: datetime.date, groups: list[dict] | None = None) -> list[int]:
    """结算一天：记下每个榜这天的榜首（周榜），累计天数正好到 10 / 15 / 30 的发奖状。返回新发的奖状编号。"""
    groups = boards(db) if groups is None else groups
    new: list[int] = []
    for game in GAMES:
        points = _week_points(db, day, game)
        for g in groups:
            scored = {u: points.get(u, 0) for u in g["members"] if points.get(u, 0) > 0}
            if not scored:
                continue
            top = max(scored.values())
            for user_id in sorted(u for u, p in scored.items() if p == top):
                db.execute("INSERT OR IGNORE INTO board_leaders(day, board, game, user_id, points) VALUES (?,?,?,?,?)",
                           (_day(day), g["key"], game, user_id, top))
                n, first = _top_days(db, g["key"], game, user_id, day)
                if n in THRESHOLDS:
                    cur = db.execute("INSERT OR IGNORE INTO awards(user_id, game, days, board, board_label, start_day, end_day, created_at) "
                                     "VALUES (?,?,?,?,?,?,?,?)",
                                     (user_id, game, n, g["key"], g["label"], first, _day(day), int(time.time())))
                    if cur.rowcount:
                        new.append(cur.lastrowid)
    db.execute("INSERT OR REPLACE INTO award_days(day, done_at) VALUES (?,?)", (_day(day), int(time.time())))
    return new


def catch_up(db: Database, now: float | None = None) -> int:
    """把还没结算的日子（到昨天为止）按顺序补上。返回新发的奖状数。很快：已经补过就直接返回。"""
    ensure(db)
    yesterday = _today(now) - datetime.timedelta(days=1)
    with _lock:
        last = db.one("SELECT MAX(day) AS d FROM award_days")["d"]
        if last and last >= _day(yesterday):
            return 0
        first = db.one("SELECT MIN(created_at) AS c FROM scores WHERE user_id IS NOT NULL")["c"]
        if not first:
            db.execute("INSERT OR REPLACE INTO award_days(day, done_at) VALUES (?,?)", (_day(yesterday), int(time.time())))
            return 0
        start = datetime.date.fromisoformat(first[:10])
        if last:
            start = max(start, datetime.date.fromisoformat(last) + datetime.timedelta(days=1))
        start = max(start, yesterday - datetime.timedelta(days=MAX_BACKFILL - 1))
        groups = boards(db)
        made, d = 0, start
        while d <= yesterday:
            made += len(settle_day(db, d, groups))
            d += datetime.timedelta(days=1)
        return made


def of_user(db: Database, user_id: int) -> list[dict]:
    """某个学生的奖状（新的在前），带上姓名、班级、负责老师（奖状上用）。"""
    ensure(db)
    user = db.one("SELECT name, class_name FROM users WHERE id=?", (user_id,))
    teacher = (tenancy.primary_map(db).get(user_id) or (0, ""))[1]
    out = []
    for r in db.query("SELECT * FROM awards WHERE user_id=? ORDER BY end_day DESC, days DESC, id DESC", (user_id,)):
        d = dict(r)
        d.update(tier=tier_of(d["days"]), serial="LX-%s-%06d" % (d["end_day"][:4], d["id"]),
                 name=user["name"] if user else "", class_name=user["class_name"] if user else "", teacher=teacher,
                 seen=bool(d["seen"]))
        out.append(d)
    return out


def of_scope(db: Database, scope: "tenancy.Scope", class_name: str = "") -> list[dict]:
    """老师看得到的学生（自己名下的；超管所有人）得过的所有奖状，新的在前。奖状上的学生姓名、班级、负责老师都带上。"""
    ensure(db)
    cond, args = tenancy.student_where(scope)
    where, args = [cond, "u.role='student'"], list(args)
    if class_name:
        where.append("u.class_name=?")
        args.append(class_name)
    primary = tenancy.primary_map(db)
    out = []
    for r in db.query("SELECT a.*, u.name, u.class_name FROM awards a JOIN users u ON u.id=a.user_id WHERE " + " AND ".join(where) +
                      " ORDER BY a.end_day DESC, u.class_name, u.name, a.days DESC", args):
        d = dict(r)
        d.update(tier=tier_of(d["days"]), serial="LX-%s-%06d" % (d["end_day"][:4], d["id"]),
                 teacher=(primary.get(d["user_id"]) or (0, ""))[1], seen=bool(d["seen"]))
        out.append(d)
    return out


def mark_seen(db: Database, user_id: int) -> None:
    ensure(db)
    db.execute("UPDATE awards SET seen=1 WHERE user_id=? AND seen=0", (user_id,))


def badges(db: Database, user_ids: list[int]) -> dict[int, list[dict]]:
    """积分榜上名字旁边的小徽章：每个人每个榜最好的那一档。"""
    ensure(db)
    if not user_ids:
        return {}
    marks = ",".join("?" * len(user_ids))
    out: dict[int, list[dict]] = {}
    for r in db.query("SELECT user_id, game, MAX(days) AS days FROM awards WHERE user_id IN (%s) GROUP BY user_id, game" % marks,
                      tuple(user_ids)):
        out.setdefault(r["user_id"], []).append({"game": r["game"], "days": r["days"], "tier": tier_of(r["days"])})
    return out
