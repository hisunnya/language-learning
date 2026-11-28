"""成绩汇总：老师最关心的「谁（班级 / 学号 / 姓名）把哪套题玩了几次、完成几次、最高最低分、平均用时」。

* 一行 = 一个学生 × 一套题。点开一行才看每一次的明细（``plays``）。
* 「完成」= 这一次把整套题的所有关都通关了：最后一关通关（配对数 = 总对数），并且通关的关数不少于
  这套题的总关数。游戏上报的 matched / total_pairs 只是**最后一关**的状态，不能单独拿来判断。
  题库已经被删掉（查不到总关数）时，退而只看最后一关有没有通关。
* 总关数是现算的（按题库当前的词和「每关词数」切关），所以题库被改过以后，旧成绩的「完成」会按新的关数重新判断。
* 没有账号体系的家庭版：成绩没有学生，按设备号分组，姓名栏显示昵称。
"""
from __future__ import annotations

from . import bank as bank_mod
from .db import Database

SCORE_COLUMNS = ("s.id, s.user_id, s.device, s.nickname, s.bank_id, s.bank_title, s.score, s.matched, "
                 "s.total_pairs, s.wrong, s.best_combo, s.duration, s.level_count, s.created_at, s.game_type, "
                 "s.rule_version, u.student_no, u.name, u.class_name")


def levels_in_bank(db: Database, bank_id: int | None, cache: dict) -> int | None:
    """这套题一共多少关；题库不存在返回 None。同一次请求里每个题库只算一次。"""
    if bank_id is None:
        return None
    if bank_id not in cache:
        try:
            cache[bank_id] = len(bank_mod.bank_payload(db, int(bank_id))["groups"])
        except bank_mod.BankError:
            cache[bank_id] = None
    return cache[bank_id]


def is_complete(play: dict, levels: int | None) -> bool:
    if int(play.get("total_pairs") or 0) <= 0 or int(play.get("matched") or 0) < int(play["total_pairs"]):
        return False
    if int(play.get("rule_version") or 0) >= 4:
        return True
    return levels is None or int(play.get("level_count") or 0) >= levels


def _who(row: dict):
    return ("u", row["user_id"]) if row["user_id"] is not None else ("d", row["device"] or "")


def _key(row: dict):
    return _who(row) + (("b", row["bank_id"]) if row["bank_id"] is not None else ("t", row["bank_title"] or ""))


def _fetch(db: Database, *, user_id=None, device=None, bank_id=None, bank_title=None, class_name="",
           people: tuple[str, tuple] | None = None) -> list[dict]:
    """people：按人过滤的 SQL 片段（server/tenancy.py 的 people_where，列名 s.user_id）——老师只看自己名下学生的成绩。"""
    where, args = [], []
    if people is not None:
        where.append(people[0]); args += list(people[1])
    if user_id is not None:
        where.append("s.user_id=?"); args.append(user_id)
    elif device is not None:
        where.append("s.user_id IS NULL AND s.device=?"); args.append(device)
    if bank_id is not None:
        where.append("s.bank_id=?"); args.append(bank_id)
    elif bank_title is not None:
        where.append("s.bank_id IS NULL AND s.bank_title=?"); args.append(bank_title)
    if class_name:
        where.append("u.class_name=?"); args.append(class_name)
    sql = "SELECT %s FROM scores s LEFT JOIN users u ON u.id=s.user_id" % SCORE_COLUMNS
    if where:
        sql += " WHERE " + " AND ".join(where)
    return [dict(r) for r in db.query(sql + " ORDER BY s.id", args)]


def summarize(db: Database, *, only_user_id: int | None = None, class_name: str = "", bank_id: int | None = None,
              q: str = "", people: tuple[str, tuple] | None = None) -> dict:
    """返回 {"rows": [...], "classes": [...], "banks": [{"id", "title"}]}，行按 班级 / 学号 / 题库 排好。"""
    rows = _fetch(db, user_id=only_user_id, bank_id=bank_id, class_name=class_name, people=people)
    cache: dict = {}
    titles = {b["id"]: b["title"] for b in db.list_banks()}
    groups: dict = {}
    for r in rows:
        groups.setdefault(_key(r), []).append(r)
    needle = q.strip().lower()
    out = []
    for plays in groups.values():
        first, last = plays[0], plays[-1]
        name = first["name"] or first["nickname"] or first["device"] or ""
        if needle and needle not in (first["student_no"] or "").lower() and needle not in name.lower():
            continue
        levels = levels_in_bank(db, first["bank_id"], cache)
        scores = [p["score"] for p in plays]
        out.append({
            "user_id": first["user_id"], "device": first["device"] if first["user_id"] is None else "",
            "student_no": first["student_no"] or "", "name": name, "class_name": first["class_name"] or "",
            "bank_id": first["bank_id"], "bank_title": titles.get(first["bank_id"]) or last["bank_title"] or "",
            "plays": len(plays), "completed": sum(1 for p in plays if is_complete(p, levels)),
            "best": max(scores), "worst": min(scores), "total": sum(scores),
            "avg_score": round(sum(scores) / len(plays), 1),
            "avg_duration": round(sum(p["duration"] for p in plays) / len(plays)),
            "last_at": last["created_at"], "game_type": last.get("game_type") or "match",
        })
    out.sort(key=lambda r: (r["class_name"], r["student_no"], r["name"], r["bank_title"]))
    banks = sorted({(r["bank_id"], r["bank_title"]) for r in out if r["bank_id"] is not None}, key=lambda b: b[1])
    return {"rows": out,
            "classes": sorted({r["class_name"] for r in out if r["class_name"]}),
            "banks": [{"id": i, "title": t} for i, t in banks]}


def plays_of(db: Database, *, user_id=None, device=None, bank_id=None, bank_title=None,
             people: tuple[str, tuple] | None = None) -> list[dict]:
    """某个学生在某套题上的每一次：最新的在最前面。至少要指明是谁（user_id 或 device）。"""
    if user_id is None and device is None:
        return []                       # 没指明是谁就什么都不给，不能退化成「全部人的全部成绩」
    rows = _fetch(db, user_id=user_id, device=device if user_id is None else None, bank_id=bank_id,
                  bank_title=bank_title if bank_id is None else None, people=people)
    cache: dict = {}
    out = []
    for r in reversed(rows):
        levels = levels_in_bank(db, r["bank_id"], cache)
        out.append({"id": r["id"], "created_at": r["created_at"], "score": r["score"], "matched": r["matched"],
                    "total_pairs": r["total_pairs"], "wrong": r["wrong"], "best_combo": r["best_combo"],
                    "duration": r["duration"], "level_count": r["level_count"], "levels_total": levels,
                    "completed": is_complete(r, levels), "game_type": r["game_type"],
                    "rule_version": r.get("rule_version", 0)})
    return out
