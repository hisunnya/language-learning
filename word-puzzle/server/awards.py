"""奖状和徽章：在周榜上累计 10 / 15 / 30 天是榜首，就发一张奖状（铜、银、金），学生的「我的」页面里有对应的徽章。

* 周榜：某一天的榜首 = 那一周（周一 00:00 起，北京时间）到这一天结束为止，积分最高的人。每周一重新开始，
  所以早期领先的人不会一直压着别人；并列第一都算。积分必须大于 0。
* 榜 = 学生自己在积分榜上看到的那个：超管设了总榜就是总榜（参加总榜的那些班）；否则是「同学」——
  和积分榜同一条规则（leaderboard.CLASSMATES：同一个班级名、并且至少有一位共同的老师），
  所以「我在积分榜上是第一」和「我当了一天榜首」永远是同一件事。没有班级或没有老师的学生不参加。
* 四个榜各算各的：总分，以及中英配对、单词大比拼、排排坐各自的积分。
* 累计天数：一个学生在某个榜上当过多少天榜首（不要求连续，跨周接着算）。正好到 10 / 15 / 30 天，
  发铜 / 银 / 金奖状；每个学生每个榜（总分或某个玩法）每个档次只发一次（换了班、规则重算也不重复发）。
* 一天 = 北京时间的一个自然日；一天结束后才结算那一天。
* 结算是「用到时补算」：有人打开积分榜或「我的」时，把还没结算的日子按顺序补上（最多往前 MAX_BACKFILL 天）。
  一天在一个事务里结算完（中途出错这一天整个不算，下次重来）；同时只有一个请求在补算，其他请求不等它、直接用现有结果。
* 规则版本记在 app_settings（awards_rules）：规则改了，旧规则算出的榜首记录作废、从头补算（已经发出的奖状不动）。
"""
from __future__ import annotations

import datetime
import threading
import time

from . import leaderboard, tenancy
from .db import Database

THRESHOLDS = (10, 15, 30)
RULES = "weekly-cumulative-10-15-30-classmates"   # 规则版本：改了规则就换一个名字，旧的榜首记录会作废重算


def tier_of(days: int) -> str:
    """档次：不到 15 天铜，不到 30 天银，30 天金（也兼容以前发过的别的天数）。"""
    return "gold" if days >= 30 else "silver" if days >= 15 else "bronze"

GAMES = ("all", "match", "spell", "order")
MAX_BACKFILL = 120
_lock = threading.Lock()          # 同一时间只让一个请求补算

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
    days        INTEGER NOT NULL,       -- 10 / 15 / 30（门槛天数）
    board       TEXT NOT NULL,          -- 哪个榜：overall（总榜），或 c|<班级名>（同学榜；早期的奖状是 t<老师>|<班级>）
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
    """建表、核对规则版本。每个 Database 只做一次（每个请求都会调到这里）。"""
    if getattr(db, "_awards_ready", False):
        return
    with db._tx() as conn:
        conn.executescript(SCHEMA)
        row = conn.execute("SELECT value FROM app_settings WHERE key='awards_rules'").fetchone()
        if not row or row["value"] != RULES:
            # 规则变了（或第一次）：旧规则算出的榜首记录和结算进度作废，从头补算；已经发出的奖状不动
            conn.execute("DELETE FROM board_leaders")
            conn.execute("DELETE FROM award_days")
            conn.execute("INSERT INTO app_settings(key, value, updated_at, updated_by) VALUES ('awards_rules', ?, ?, NULL) "
                         "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                         (RULES, int(time.time())))
    db._awards_ready = True


def _day(d: datetime.date) -> str:
    return d.strftime("%Y-%m-%d")


def _today(now: float | None = None) -> datetime.date:
    return datetime.date.fromtimestamp(now if now is not None else time.time())


def boards(db: Database) -> list[dict]:
    """现在要比的榜：[{key, label, members:set, candidates:set}]。

    members 是一起比积分的人，candidates 是这一组里能被记成榜首的人：
    * 设了总榜：只有一组，总榜上的人互相比，谁都能当榜首。
    * 没设总榜：每个学生一组——members 是他在积分榜上看到的同学（leaderboard.CLASSMATES 的同一条规则），
      candidates 只有他自己。「同学」不一定能分成互不相交的班（甲和乙共享一位老师、乙和丙共享另一位，
      甲丙互相看不到），所以按「每个人看到的那张榜」逐个判断，而不是硬分组。
    """
    cfg = leaderboard.get_config(db)
    # 和积分榜一样：被删除、被停用的学生不上榜，也不参加比较
    students = db.query("SELECT id, class_name FROM users WHERE role='student' AND deleted_at=0 AND disabled=0")
    if cfg["classes"]:
        wanted = set(cfg["classes"])
        members = {r["id"] for r in students if r["class_name"] in wanted}
        return [{"key": "overall", "label": cfg["title"] or "", "members": members, "candidates": members}]
    teachers: dict[int, set[int]] = {}
    for r in db.query("SELECT ts.student_id, ts.teacher_id FROM teacher_students ts JOIN users t ON t.id=ts.teacher_id "
                      "WHERE t.deleted_at=0"):
        teachers.setdefault(r["student_id"], set()).add(r["teacher_id"])
    by_class: dict[str, list[int]] = {}
    for r in students:
        if r["class_name"] and r["id"] in teachers:
            by_class.setdefault(r["class_name"], []).append(r["id"])
    out = []
    for class_name, ids in by_class.items():
        for me in ids:
            mates = {u for u in ids if u == me or teachers[u] & teachers[me]}
            out.append({"key": "c|" + class_name, "label": class_name, "members": mates, "candidates": {me}})
    return out


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


def settle_day(db: Database, day: datetime.date, groups: list[dict] | None = None) -> list[int]:
    """结算一天：记下每个榜这天的榜首（周榜），累计天数正好到 10 / 15 / 30 的发奖状。返回新发的奖状编号。
    整天在一个事务里：中途出错就整天回滚，award_days 里也不会有这一天，下次补算重来。"""
    ensure(db)
    groups = boards(db) if groups is None else groups
    points = {game: _week_points(db, day, game) for game in GAMES}
    today, now = _day(day), int(time.time())
    new: list[int] = []
    with db._tx() as conn:
        for game in GAMES:
            for g in groups:
                scored = {u: points[game].get(u, 0) for u in g["members"] if points[game].get(u, 0) > 0}
                if not scored:
                    continue
                top = max(scored.values())
                for user_id in sorted(u for u, p in scored.items() if p == top and u in g["candidates"]):
                    conn.execute("INSERT OR IGNORE INTO board_leaders(day, board, game, user_id, points) VALUES (?,?,?,?,?)",
                                 (today, g["key"], game, user_id, top))
                    row = conn.execute("SELECT COUNT(*) AS n, MIN(day) AS first FROM board_leaders "
                                       "WHERE board=? AND game=? AND user_id=? AND day<=?", (g["key"], game, user_id, today)).fetchone()
                    n = row["n"]
                    if n not in THRESHOLDS:
                        continue
                    # 同一个学生、同一个榜（总分或玩法）、同一档只发一次：换了班或者规则重算，起始日变了也不重复发
                    if conn.execute("SELECT 1 FROM awards WHERE user_id=? AND game=? AND days=?", (user_id, game, n)).fetchone():
                        continue
                    cur = conn.execute("INSERT INTO awards(user_id, game, days, board, board_label, start_day, end_day, created_at) "
                                       "VALUES (?,?,?,?,?,?,?,?)",
                                       (user_id, game, n, g["key"], g["label"], row["first"] or today, today, now))
                    new.append(cur.lastrowid)
        conn.execute("INSERT OR REPLACE INTO award_days(day, done_at) VALUES (?,?)", (today, now))
    return new


def catch_up(db: Database, now: float | None = None) -> int:
    """把还没结算的日子（到昨天为止）按顺序补上。返回新发的奖状数。很快：已经补过就直接返回。
    另一个请求正在补算时不等它（第一次补算可能要算上百天），直接返回 0，用现有的结果。"""
    ensure(db)
    yesterday = _today(now) - datetime.timedelta(days=1)
    last = db.one("SELECT MAX(day) AS d FROM award_days")["d"]
    if last and last >= _day(yesterday):
        return 0
    if not _lock.acquire(blocking=False):
        return 0
    try:
        last = db.one("SELECT MAX(day) AS d FROM award_days")["d"]     # 拿到锁之后再看一次：可能刚被别人补完
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
    finally:
        _lock.release()


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
