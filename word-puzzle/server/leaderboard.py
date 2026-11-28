"""积分榜：一个班里谁的积分最高。

积分 = 这个学生所有成绩（``scores.score``）之和；``period='week'`` 时只算本周（周一 00:00 起，服务器按北京时间）。
谁看得到什么：

* 学生：只有自己班的（同班同学 = 班级名相同、并且至少有一位共同的老师——不同学校的「一班」不会混在一起）；
  班级是服务器按账号定的，不听请求里的参数。没有班级的学生只看得到自己。
* 老师：自己名下学生的各个班，可以选班，也可以看全部；超管：所有学生。
* 只有名字和积分，不带学号；0 分的不上榜。
"""
from __future__ import annotations

import json
import time

from . import tenancy
from .db import Database

TOP = 10
MAX_CLASSES = 30
SETTING = "leaderboard"


def week_start(now: float | None = None) -> str:
    """本周一 00:00（服务器本地时间），和 scores.created_at 一样的字符串格式，直接比较。"""
    t = time.localtime(now if now is not None else time.time())
    monday = time.mktime((t.tm_year, t.tm_mon, t.tm_mday - t.tm_wday, 0, 0, 0, 0, 0, -1))
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(monday))


CLASSMATES = ("u.deleted_at=0 AND u.role='student' AND (u.id=? OR (u.class_name=? AND EXISTS ("
              "SELECT 1 FROM teacher_students a JOIN teacher_students b ON a.teacher_id=b.teacher_id "
              "JOIN users t ON t.id=a.teacher_id AND t.deleted_at=0 WHERE a.student_id=? AND b.student_id=u.id)))")
"""学生看到的同学（SQL 条件，表别名 u，参数 [自己, 自己的班级, 自己]）：同一个班级名、并且至少有一位共同的（没被删除的）老师；
自己总在里面（没有老师的学生也看得到自己）。被删除的学生不在里面。奖状（server/awards.py）用的也是这一条。"""


def _pool(db: Database, scope: tenancy.Scope, user: dict | None, class_name: str) -> tuple[str, list]:
    """参与排名的学生（SQL 条件，表别名 u）。"""
    if scope.kind == tenancy.STUDENT and user:
        if not user.get("class_name"):
            return "u.id=?", [user["id"]]
        return CLASSMATES, [user["id"], user["class_name"], user["id"]]
    cond, args = tenancy.student_where(scope)
    where, args = [cond, "u.role='student'"], list(args)
    if class_name:
        where.append("u.class_name=?")
        args.append(class_name)
    return " AND ".join(where), args


def get_config(db: Database) -> dict:
    """{"title": str, "classes": [班级名…]}；没设置过就是空。"""
    row = db.one("SELECT value FROM app_settings WHERE key=?", (SETTING,))
    try:
        data = json.loads(row["value"]) if row else {}
    except ValueError:
        data = {}
    classes = [c for c in (data.get("classes") or []) if isinstance(c, str) and c]
    return {"title": str(data.get("title") or "")[:40], "classes": classes}


def set_config(db: Database, title: str, classes: list, actor: int | None) -> dict:
    """保存设置。班级必须是现有学生的班级名；最多 MAX_CLASSES 个；返回保存后的设置。不合格抛 ValueError。"""
    known = {r["class_name"] for r in db.query(
        "SELECT DISTINCT class_name FROM users WHERE role='student' AND deleted_at=0 AND class_name<>''")}
    picked, seen = [], set()
    for c in classes if isinstance(classes, list) else []:
        if not isinstance(c, str):
            raise ValueError("班级名不对")
        if c not in known:
            raise ValueError("没有这个班级：%s" % c[:30])
        if c not in seen:
            seen.add(c)
            picked.append(c)
    if len(picked) > MAX_CLASSES:
        raise ValueError("最多选 %d 个班" % MAX_CLASSES)
    cfg = {"title": " ".join(str(title or "").split())[:40], "classes": picked}
    db.execute("INSERT INTO app_settings(key, value, updated_at, updated_by) VALUES (?,?,?,?) "
               "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at, updated_by=excluded.updated_by",
               (SETTING, json.dumps(cfg, ensure_ascii=False), int(time.time()), actor))
    return cfg


def class_counts(db: Database) -> list[dict]:
    """超管设置页用：所有班级和人数。"""
    return [dict(r) for r in db.query(
        "SELECT class_name, COUNT(*) AS students FROM users WHERE role='student' AND deleted_at=0 AND class_name<>'' "
        "GROUP BY class_name ORDER BY class_name")]


def classes_of(db: Database, scope: tenancy.Scope) -> list[str]:
    cond, args = tenancy.student_where(scope)
    rows = db.query("SELECT DISTINCT u.class_name FROM users u WHERE %s AND u.role='student' AND u.class_name<>'' "
                    "ORDER BY u.class_name" % cond, args)
    return [r["class_name"] for r in rows]


GAMES = ("all", "match", "spell", "order", "verb")


def board(db: Database, scope: tenancy.Scope, user: dict | None, class_name: str = "", period: str = "all",
          now: float | None = None, game: str = "all") -> dict:
    """game：all = 总分；其他值只算对应玩法的积分（奖状也按各玩法榜分别算）。"""
    period = "week" if period == "week" else "all"
    game = game if game in GAMES else "all"
    cfg = get_config(db)
    overall = bool(cfg["classes"]) and not (scope.staff and class_name)       # 老师选了某个班，就看那个班
    if overall:
        marks = ",".join("?" * len(cfg["classes"]))
        where, args = "u.role='student' AND u.deleted_at=0 AND u.class_name IN (%s)" % marks, list(cfg["classes"])
    else:
        where, args = _pool(db, scope, user, class_name)
    join = "JOIN scores s ON s.user_id=u.id"
    if period == "week":
        join += " AND s.created_at>=?"
        args = [week_start(now)] + args
    if game != "all":
        join += " AND s.game_type=?"
        args = args[:1] + [game] + args[1:] if period == "week" else [game] + args
    rows = db.query("SELECT u.id, u.name, u.class_name, SUM(s.score) AS points, COUNT(s.id) AS games "
                    "FROM users u %s WHERE %s AND u.disabled=0 GROUP BY u.id HAVING SUM(s.score)>0 "
                    "ORDER BY points DESC, games ASC, u.name" % (join, where), args)
    ranked, rank, last = [], 0, None
    for i, r in enumerate(rows, start=1):
        if r["points"] != last:
            rank, last = i, r["points"]
        ranked.append({"rank": rank, "name": r["name"], "points": r["points"], "class_name": r["class_name"],
                       "me": bool(user and r["id"] == user["id"]), "id": r["id"]})
    staff = scope.staff
    keep_class = staff or overall          # 总榜里每个人旁边标班级（学生也看得到别班同学是哪个班的）
    from . import awards                     # 名字旁边的小徽章（每个榜最好的那一档）
    medals = awards.badges(db, [e["id"] for e in ranked[:TOP]] + ([e["id"] for e in ranked if e["me"]][:1]))
    for e in ranked:
        e["badges"] = medals.get(e.pop("id"), [])
    out = {
        "period": period,
        "game": game,
        "scope": "overall" if overall else ("staff" if staff else "class"),
        "class_name": "" if overall else (class_name if staff else ((user or {}).get("class_name") or "")),
        "title": cfg["title"] if overall else "",
        "class_count": len(cfg["classes"]),
        "configured": bool(cfg["classes"]),
        "entries": [dict(e, **({} if keep_class else {"class_name": ""})) for e in ranked[:TOP]],
        "total": len(ranked),
        "me": next((e for e in ranked if e["me"]), None),
        "can_configure": scope.kind == tenancy.SUPER,
        "is_student": scope.kind == tenancy.STUDENT,
        "my_class_in_board": bool(overall and user and user.get("class_name") in cfg["classes"]),
    }
    if out["me"] and not keep_class:
        out["me"] = dict(out["me"], class_name="")
    out["classes"] = classes_of(db, scope) if staff else []
    return out

