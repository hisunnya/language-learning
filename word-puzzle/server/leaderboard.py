"""积分榜：一个班里谁的积分最高。

积分 = 这个学生所有成绩（``scores.score``）之和；``period='week'`` 时只算本周（周一 00:00 起，服务器按北京时间）。
谁看得到什么：

* 学生：只有自己班的（同班同学 = 班级名相同、并且至少有一位共同的老师——不同学校的「一班」不会混在一起）；
  班级是服务器按账号定的，不听请求里的参数。没有班级的学生只看得到自己。
* 老师：自己名下学生的各个班，可以选班，也可以看全部；超管：所有学生。
* 只有名字和积分，不带学号；0 分的不上榜。
"""
from __future__ import annotations

import time

from . import tenancy
from .db import Database

TOP = 10


def week_start(now: float | None = None) -> str:
    """本周一 00:00（服务器本地时间），和 scores.created_at 一样的字符串格式，直接比较。"""
    t = time.localtime(now if now is not None else time.time())
    monday = time.mktime((t.tm_year, t.tm_mon, t.tm_mday - t.tm_wday, 0, 0, 0, 0, 0, -1))
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(monday))


def _pool(db: Database, scope: tenancy.Scope, user: dict | None, class_name: str) -> tuple[str, list]:
    """参与排名的学生（SQL 条件，表别名 u）。"""
    if scope.kind == tenancy.STUDENT and user:
        if not user.get("class_name"):
            return "u.id=?", [user["id"]]
        return ("u.class_name=? AND EXISTS (SELECT 1 FROM teacher_students a JOIN teacher_students b "
                "ON a.teacher_id=b.teacher_id WHERE a.student_id=? AND b.student_id=u.id)",
                [user["class_name"], user["id"]])
    cond, args = tenancy.student_where(scope)
    where, args = [cond, "u.role='student'"], list(args)
    if class_name:
        where.append("u.class_name=?")
        args.append(class_name)
    return " AND ".join(where), args


def classes_of(db: Database, scope: tenancy.Scope) -> list[str]:
    cond, args = tenancy.student_where(scope)
    rows = db.query("SELECT DISTINCT u.class_name FROM users u WHERE %s AND u.role='student' AND u.class_name<>'' "
                    "ORDER BY u.class_name" % cond, args)
    return [r["class_name"] for r in rows]


def board(db: Database, scope: tenancy.Scope, user: dict | None, class_name: str = "", period: str = "all",
          now: float | None = None) -> dict:
    period = "week" if period == "week" else "all"
    where, args = _pool(db, scope, user, class_name)
    join = "JOIN scores s ON s.user_id=u.id"
    if period == "week":
        join += " AND s.created_at>=?"
        args = [week_start(now)] + args
    rows = db.query("SELECT u.id, u.name, u.class_name, SUM(s.score) AS points, COUNT(s.id) AS games "
                    "FROM users u %s WHERE %s AND u.disabled=0 GROUP BY u.id HAVING SUM(s.score)>0 "
                    "ORDER BY points DESC, games ASC, u.name" % (join, where), args)
    ranked, rank, last = [], 0, None
    for i, r in enumerate(rows, start=1):
        if r["points"] != last:
            rank, last = i, r["points"]
        ranked.append({"rank": rank, "name": r["name"], "points": r["points"], "class_name": r["class_name"],
                       "me": bool(user and r["id"] == user["id"])})
    staff = scope.staff
    out = {
        "period": period,
        "scope": "staff" if staff else "class",
        "class_name": class_name if staff else ((user or {}).get("class_name") or ""),
        "entries": [dict(e, **({} if staff else {"class_name": ""})) for e in ranked[:TOP]],
        "total": len(ranked),
        "me": next((e for e in ranked if e["me"]), None),
    }
    if not staff:
        out["me"] = dict(out["me"], class_name="") if out["me"] else None
    out["classes"] = classes_of(db, scope) if staff else []
    return out
