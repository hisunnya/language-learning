"""第 4 版在线计分：服务器签发每轮 token，并按经校验的明细结算。"""
from __future__ import annotations

import json
import math
import secrets
import time
from typing import Any

from . import bank as bank_mod, items as items_mod
from .db import Database

RULE_VERSION = 4
BASE_POINTS = {"match": 20, "verb": 10, "spell": 80, "order": 30}
TIME_BASE = {"match": 60, "verb": 12, "spell": 20, "order": 30}
COMBO_RATIOS = (0.0, 0.0, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0)
MAX_EVENTS = 500
MAX_COUNT = 1000


class PlayError(ValueError):
    def __init__(self, message: str, code: str = "invalid_play", status: int = 400):
        super().__init__(message)
        self.code = code
        self.status = status


def _round_js(value: float) -> int:
    """Math.round 的非负数行为；不使用 Python 的 ties-to-even。"""
    return math.floor(max(0.0, value) + 0.5)


def _strict_int(value: Any, name: str, low: int = 0, high: int = MAX_COUNT) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise PlayError("%s 不合法" % name, "invalid_detail")
    return value


def _actor_where(user_id: int | None, device: str, mode: str) -> tuple[str, tuple]:
    if user_id is not None:
        return "user_id=? AND mode='online'", (user_id,)
    return "user_id IS NULL AND device=? AND mode=?", (device, mode)


def _bank_groups(db: Database, bank: dict) -> list[dict]:
    return bank_mod.bank_payload(db, bank["id"])["groups"]


def _type_items(db: Database, bank: dict) -> list[dict]:
    return db.bank_items(bank["id"])


def _group_key(game_type: str, level: int, ords: list[int]) -> str:
    return "%s:%d:%s" % (game_type, level, ",".join(str(n) for n in ords))


def begin_play(db: Database, *, bank: dict, user_id: int | None, device: str, mode: str,
               level: int, ords: Any = None, previous_play_token: str = "") -> dict:
    game_type = bank.get("game_type") or "match"
    if game_type not in BASE_POINTS:
        raise PlayError("题库游戏类型不支持", "bad_game_type")

    if game_type == "match":
        groups = _bank_groups(db, bank)
        if isinstance(level, bool) or not isinstance(level, int) or not 0 <= level < len(groups):
            raise PlayError("level 不合法", "bad_level")
        if ords not in (None, []):
            raise PlayError("中英配对不需要 ords", "bad_ords")
        expected = list(range(len(groups[level]["words"])))
        base_time = TIME_BASE[game_type]
    else:
        all_items = _type_items(db, bank)
        if isinstance(level, bool) or not isinstance(level, int) or level != 0:
            raise PlayError("spell / verb / order 每轮 level 必须为 0", "bad_level")
        if game_type == "order":
            if not isinstance(ords, list) or len(ords) != 1 or isinstance(ords[0], bool) or not isinstance(ords[0], int):
                raise PlayError("排排坐每轮需要一个 ord", "bad_ords")
            expected = ords
            if expected[0] < 0 or expected[0] >= len(all_items):
                raise PlayError("ord 不合法", "bad_ords")
            base_time = TIME_BASE[game_type]
        else:
            if not isinstance(ords, list) or not ords or any(isinstance(n, bool) or not isinstance(n, int) for n in ords):
                raise PlayError("spell / verb 每轮需要完整题库 ords", "bad_ords")
            expected = list(ords)
            full_bank_ords = list(range(len(all_items)))
            if len(set(expected)) != len(expected) or expected != full_bank_ords:
                raise PlayError("ords 必须是该题库的完整题目", "bad_ords")
            base_time = TIME_BASE[game_type] * len(expected)
    if not expected:
        raise PlayError("这一关没有题目", "empty_round")

    fixed_ords = [] if game_type == "match" else expected
    group_key = _group_key(game_type, level, fixed_ords)
    token = secrets.token_urlsafe(24)
    now = time.time()
    previous_play_token = str(previous_play_token or "").strip()
    with db._tx() as conn:
        seeded = 0
        if previous_play_token:
            prev = conn.execute("SELECT * FROM game_plays WHERE token=?", (previous_play_token,)).fetchone()
            adjacent = False
            if prev:
                try:
                    old_ords = json.loads(prev["ords"])
                except (TypeError, ValueError):
                    old_ords = []
                same_actor = (prev["user_id"] == user_id and
                              (user_id is not None or (prev["device"] == device and prev["mode"] == mode)))
                if game_type == "order":
                    adjacent = (prev["game_type"] == game_type and prev["bank_id"] == bank["id"]
                                and old_ords == [expected[0] - 1])
                elif game_type == "match":
                    adjacent = (prev["game_type"] == game_type and prev["bank_id"] == bank["id"]
                                and prev["level"] == level - 1)
                if not (same_actor and adjacent and prev["status"] == "scored" and not prev["seed_claimed"]):
                    raise PlayError("上一轮不能用于连击继承", "invalid_combo_seed", 409)
                seeded = max(0, min(MAX_COUNT, int(prev["terminal_combo"] or 0)))
                conn.execute("UPDATE game_plays SET seed_claimed=1 WHERE token=? AND seed_claimed=0",
                             (previous_play_token,))
                if conn.execute("SELECT changes()").fetchone()[0] != 1:
                    raise PlayError("上一轮连击已被使用", "combo_seed_used", 409)

        actor_sql, actor_args = _actor_where(user_id, device, mode)
        prior = conn.execute(
            "SELECT COUNT(*) FROM game_plays WHERE %s AND bank_id=? AND game_type=? AND group_key=? "
            "AND status='scored' AND final_score>0" % actor_sql,
            (*actor_args, bank["id"], game_type, group_key)).fetchone()[0]
        attempt = int(prior) + 1
        score_factor, time_factor = ((1.0, 1.0) if attempt <= 5 else
                                     (0.75, 0.8) if attempt <= 10 else
                                     (0.5, 0.6) if attempt <= 15 else (0.2, 0.4))
        time_limit = max(1, math.floor(base_time * time_factor))
        expires = now + time_limit
        conn.execute(
            "INSERT INTO game_plays(token,user_id,device,mode,bank_id,game_type,level,ords,group_key,attempt,"
            "score_factor,time_factor,time_limit,started_at,expires_at,phase,phase_started,seeded_from,terminal_combo) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (token, user_id, device, mode, bank["id"], game_type, level, json.dumps(fixed_ords), group_key,
             attempt, score_factor, time_factor, time_limit, now, expires,
             "arranging" if game_type == "order" else "playing", 0, previous_play_token or None, seeded))
    return {"ok": True, "play_token": token, "attempt": attempt, "score_factor": score_factor,
            "time_factor": time_factor, "time_limit": time_limit, "rule_version": RULE_VERSION,
            "started_at": now, "expires_at": expires, "combo_seed": seeded}


def get_owned_play(db: Database, token: str, *, user_id: int | None, device: str, mode: str) -> dict:
    if not isinstance(token, str) or not 24 <= len(token) <= 64:
        raise PlayError("play_token 不合法", "invalid_play_token")
    row = db.one("SELECT * FROM game_plays WHERE token=?", (token,))
    if not row:
        raise PlayError("找不到这局游戏", "play_not_found", 404)
    play = dict(row)
    same = play["user_id"] == user_id
    if user_id is None:
        same = play["user_id"] is None and play["device"] == device and play["mode"] == mode
    if not same:
        raise PlayError("这局游戏不属于当前账号", "play_forbidden", 404)
    return play


def phase(db: Database, play: dict, next_phase: str, now: float | None = None) -> dict:
    if play["game_type"] != "order":
        raise PlayError("只有排排坐有录音阶段", "bad_phase", 409)
    if next_phase not in ("recording", "scoring"):
        raise PlayError("phase 不合法", "bad_phase")
    now = time.time() if now is None else now
    if play["status"] != "started":
        raise PlayError("这一轮已经结算", "play_finished", 409)
    if next_phase == "recording":
        if play["phase"] != "arranging":
            raise PlayError("阶段切换不合法", "bad_phase", 409)
        if now > play["expires_at"] + int(play.get("checkpoint_bonus_seconds") or 0):
            raise PlayError("排句时间已结束", "play_expired", 409)
        deadline = now + 120
        db.execute("UPDATE game_plays SET phase='recording', phase_started=?, recording_deadline=? WHERE token=?",
                   (now, deadline, play["token"]))
    else:
        if play["phase"] not in ("arranging", "recording", "uploaded"):
            raise PlayError("阶段切换不合法", "bad_phase", 409)
        if play["phase"] == "recording":
            paused_until = min(now, float(play["recording_deadline"]))
            db.execute("UPDATE game_plays SET phase='scoring', paused_seconds=paused_seconds+? WHERE token=?",
                       (max(0.0, paused_until - play["phase_started"]), play["token"]))
        else:
            db.execute("UPDATE game_plays SET phase='scoring',phase_started=? WHERE token=?",
                       (now if play["phase"] == "arranging" else play["phase_started"], play["token"]))
    updated = db.one("SELECT phase, paused_seconds, expires_at FROM game_plays WHERE token=?", (play["token"],))
    return {"ok": True, "phase": updated["phase"]}


def check_upload(play: dict, item_ord: int, now: float | None = None) -> None:
    now = time.time() if now is None else now
    if play["game_type"] != "order" or play["phase"] != "recording" or play["status"] != "started":
        raise PlayError("当前轮次不在录音阶段", "bad_phase", 409)
    try:
        ords = json.loads(play["ords"])
    except (TypeError, ValueError):
        ords = []
    if ords != [item_ord]:
        raise PlayError("录音不属于这一轮", "recording_mismatch", 409)
    if now > play["recording_deadline"]:
        raise PlayError("录音时间已结束", "recording_expired", 409)


def accept_upload(db: Database, play: dict, item_ord: int, now: float | None = None) -> None:
    now = time.time() if now is None else now
    check_upload(play, item_ord, now)
    db.execute("UPDATE game_plays SET phase='uploaded', paused_seconds=paused_seconds+? WHERE token=?",
               (max(0.0, now - play["phase_started"]), play["token"]))


def _round_expected(db: Database, play: dict) -> list[int]:
    if play["game_type"] == "match":
        groups = bank_mod.bank_payload(db, int(play["bank_id"]))["groups"]
        return list(range(len(groups[int(play["level"])]["words"])))
    return list(json.loads(play["ords"]))


def validate_report(db: Database, play: dict, report: dict) -> tuple[list[dict], list[dict], dict]:
    expected = _round_expected(db, play)
    expected_set = set(expected)
    game_type = play["game_type"]
    raw_detail = report.get("detail")
    if not isinstance(raw_detail, list):
        raise PlayError("detail 需要是数组", "invalid_detail")
    answers: list[dict] = []
    if game_type == "match":
        if len(raw_detail) != 1 or not isinstance(raw_detail[0], dict):
            raise PlayError("中英配对每轮必须只有一条关卡明细", "invalid_detail")
        outer = raw_detail[0]
        if outer.get("level") != play["level"]:
            raise PlayError("明细关卡与 play_token 不一致", "level_mismatch")
        answer_rows = outer.get("answers")
        if not isinstance(answer_rows, list):
            raise PlayError("配对明细缺少 answers", "invalid_detail")
    else:
        answer_rows = raw_detail

    seen: set[int] = set()
    for item in answer_rows:
        if not isinstance(item, dict):
            raise PlayError("题目明细格式不合法", "invalid_detail")
        ordinal = item.get("ord")
        if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal not in expected_set or ordinal in seen:
            raise PlayError("题目序号不合法或重复", "invalid_detail")
        seen.add(ordinal)
        wrong = _strict_int(item.get("wrong", 0), "wrong")
        hints = _strict_int(item.get("hints", 0), "hints")
        if game_type == "order":
            solved = item.get("arranged") is True
            gave_up = item.get("gave_up", item.get("gaveUp", False)) is True
        else:
            solved = item.get("solved") is True
            gave_up = item.get("gave_up", item.get("gaveUp", False)) is True
        if solved and gave_up:
            raise PlayError("已解答题目不能同时标记为放弃", "invalid_detail")
        answers.append({"ord": ordinal, "wrong": wrong, "hints": hints, "solved": solved,
                        "gave_up": gave_up, "skipped": item.get("skipped") is True,
                        "recording_id": item.get("recording_id")})

    events = report.get("combo_events")
    if not isinstance(events, list) or len(events) > MAX_EVENTS:
        raise PlayError("combo_events 不合法", "invalid_combo_events")
    answer_by_ord = {item["ord"]: item for item in answers}
    eligible_expected = {item["ord"] for item in answers
                         if item["solved"] and not item["gave_up"] and not item["wrong"] and not item["hints"]}
    eligible_seen: set[int] = set()
    normalized_events = []
    false_seen: set[int] = set()
    false_counts: dict[int, int] = {}
    for event in events:
        if not isinstance(event, dict):
            raise PlayError("连击事件格式不合法", "invalid_combo_events")
        ordinal, eligible = event.get("ord"), event.get("eligible")
        if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal not in expected_set or not isinstance(eligible, bool):
            raise PlayError("连击事件序号或资格不合法", "invalid_combo_events")
        if eligible:
            if ordinal not in eligible_expected or ordinal in eligible_seen:
                raise PlayError("连击事件与已解答明细不一致", "invalid_combo_events")
            eligible_seen.add(ordinal)
            normalized_events.append({"ord": ordinal, "eligible": True})
        else:
            if event.get("break", True) is not True:
                raise PlayError("未答对事件必须中断连击", "invalid_combo_events")
            false_seen.add(ordinal)
            false_counts[ordinal] = false_counts.get(ordinal, 0) + 1
            normalized_events.append({"ord": ordinal, "eligible": False, "break": True})
    if eligible_seen != eligible_expected:
        raise PlayError("每个无错解答都必须且只能出现一次", "invalid_combo_events")
    for item in answers:
        if (item["wrong"] or item["hints"] or item["gave_up"] or item["skipped"]) and item["ord"] not in false_seen:
            raise PlayError("错答、提示或跳过必须中断连击", "invalid_combo_events")
        if item["solved"] and item["ord"] not in eligible_seen and item["ord"] not in false_seen:
            raise PlayError("不符合连击条件的解答必须中断连击", "invalid_combo_events")
        if game_type == "match" and not item["solved"] and item["wrong"] > false_counts.get(item["ord"], 0):
            raise PlayError("每次配对错误都必须记录为连击中断事件", "invalid_combo_events")

    matched = sum(1 for item in answers if item["solved"])
    wrong = sum(item["wrong"] for item in answers)
    if game_type == "match":
        # 配对错答从含连击奖励的余额扣除并即时封底，不能只对基础分封底。
        answer_points = 0
        earned_combo = 0.0
        streak = max(0, min(MAX_COUNT, int(play["terminal_combo"] or 0)))
        false_seen_count: dict[int, int] = {}
        wrong_applied: dict[int, int] = {}
        awarded: set[int] = set()
        for event in normalized_events:
            ordinal = event["ord"]
            answer = answer_by_ord.get(ordinal)
            if event["eligible"]:
                streak += 1
                extra = 20 * COMBO_RATIOS[min(7, streak)]
                earned_combo += extra
                answer_points += 20 + extra
                awarded.add(ordinal)
                continue
            streak = 0
            false_seen_count[ordinal] = false_seen_count.get(ordinal, 0) + 1
            if not answer:
                continue
            if answer["solved"] and ordinal not in awarded:
                # 若有独立的错答事件，先逐次扣分；最后的非合格命中事件给基础分。
                # 若报告只含一个事件，则该事件承载本题的错答、封底及最终命中。
                total_false = false_counts.get(ordinal, 0)
                seen_false = false_seen_count[ordinal]
                if seen_false < total_false:
                    if wrong_applied.get(ordinal, 0) < answer["wrong"]:
                        answer_points = max(0, answer_points - 4)
                        wrong_applied[ordinal] = wrong_applied.get(ordinal, 0) + 1
                else:
                    remaining = answer["wrong"] - wrong_applied.get(ordinal, 0)
                    for _ in range(max(0, remaining)):
                        answer_points = max(0, answer_points - 4)
                    answer_points += 20
                    awarded.add(ordinal)
            elif wrong_applied.get(ordinal, 0) < answer["wrong"]:
                answer_points = max(0, answer_points - 4)
                wrong_applied[ordinal] = wrong_applied.get(ordinal, 0) + 1
        if any(item["solved"] and item["ord"] not in awarded for item in answers):
            raise PlayError("已完成配对必须有对应的命中事件", "invalid_combo_events")
        # 连击元数据仍保存完整奖励；这里抵消稍后单独入账的奖励，净基础分可为负，但总余额非负。
        answer_points -= earned_combo
        sanitized = [{"level": play["level"], "answers": answers}]
    elif game_type == "spell":
        answer_points = sum(max(8, 80 - 24 * item["hints"] - 16 * item["wrong"])
                            if item["solved"] and not item["gave_up"] else 0 for item in answers)
        sanitized = answers
    elif game_type == "verb":
        answer_points = sum((0 if item["wrong"] + 1 >= 5 else max(0, 10 - 2 * item["wrong"]))
                            if item["solved"] and not item["gave_up"] else 0 for item in answers)
        sanitized = answers
    else:
        answer_points = sum(max(6, 30 - 6 * item["wrong"])
                            if item["solved"] and not item["gave_up"] else 0 for item in answers)
        for item in answers:
            item["arranged"] = item["solved"]
        sanitized = answers
    return sanitized, normalized_events, {
        "expected": expected, "matched": matched, "wrong": wrong,
        "answer_points": answer_points, "game_type": game_type, "answer_by_ord": answer_by_ord,
    }


def _recording_details(db: Database, play: dict, sanitized: list[dict], user_id: int | None) -> tuple[int, int, int | None]:
    if play["game_type"] != "order":
        return 0, 0, None
    item = sanitized[0] if sanitized else None
    if not item or not item["solved"]:
        return 0, 0, None
    try:
        rid = int(item["recording_id"]) if item.get("recording_id") else 0
    except (ValueError, TypeError):
        rid = 0
    if rid:
        row = db.one("SELECT * FROM recordings WHERE id=? AND bank_id=? AND item_ord=? AND user_id IS ? "
                     "AND play_token=?", (rid, play["bank_id"], item["ord"], user_id, play["token"]))
    else:
        # 上传请求已被接受但浏览器的等待超时：同 token 的唯一一句录音仍属于本轮。
        row = db.one("SELECT * FROM recordings WHERE bank_id=? AND item_ord=? AND user_id IS ? AND play_token=? "
                     "AND duration_ms>=1000 ORDER BY id DESC LIMIT 1",
                     (play["bank_id"], item["ord"], user_id, play["token"]))
        rid = int(row["id"]) if row else 0
    if not row or int(row["duration_ms"] or 0) < 1000:
        return 0, 0, None
    accuracy = row["accuracy"]
    try:
        ratio = float(accuracy)
    except (TypeError, ValueError):
        ratio = 0.0
    if not math.isfinite(ratio):
        ratio = 0.0
    return 20, _round_js(max(0.0, min(1.0, ratio)) * 35), rid


def _combo(points_per_hit: int, events: list[dict], combo_seed: int, time_limit: int) -> tuple[float, int, int, int]:
    streak = max(0, min(MAX_COUNT, combo_seed))
    best = streak
    extra_points, extra_seconds = 0.0, 0
    max_extra_seconds = min(10, math.floor(time_limit * 0.2))
    for event in events:
        if not event["eligible"]:
            streak = 0
            continue
        streak += 1
        best = max(best, streak)
        ratio = COMBO_RATIOS[min(7, streak)]
        extra_points += points_per_hit * ratio
        seconds = 2 if streak >= 5 else 1 if streak >= 2 else 0
        extra_seconds += min(seconds, max(0, max_extra_seconds - extra_seconds))
    return extra_points, best, extra_seconds, streak


def _elapsed(play: dict, now: float) -> float:
    if play["game_type"] == "order" and play["phase"] != "arranging":
        if play.get("checkpoint_at"):
            return max(0.0, float(play["checkpoint_elapsed"] or 0))
        if play.get("phase_started"):
            return max(0.0, float(play["phase_started"]) - float(play["started_at"]))
    paused = float(play.get("paused_seconds") or 0)
    if play["game_type"] == "order" and play["phase"] == "recording":
        paused += max(0.0, min(now, float(play["recording_deadline"])) - float(play["phase_started"] or now))
    return max(0.0, now - float(play["started_at"]) - paused)


def _score_from_snapshot(play: dict, snapshot: dict, accuracy_points: int = 0) -> int:
    raw = (snapshot["answer_points"] + snapshot["recording_points"] + accuracy_points
           + snapshot["combo_points"] + snapshot["speed_points"])
    return _round_js(raw * float(play["score_factor"]))


def _time_budget(play: dict, bonus_seconds: int, wrong: int) -> int:
    penalty = 3 * wrong if play["game_type"] == "match" else 0
    return max(0, int(play["time_limit"]) + bonus_seconds - penalty)


def _update_late_score(db: Database, token: str) -> None:
    row = db.one("SELECT * FROM game_plays WHERE token=? AND status='scored'", (token,))
    if not row or not row["score_id"]:
        return
    try:
        snapshot = json.loads(row["score_snapshot"] or "{}")
    except (TypeError, ValueError):
        return
    acc = 0
    rid = snapshot.get("recording_id")
    if rid:
        recording = db.one("SELECT accuracy,duration_ms FROM recordings WHERE id=? AND play_token=?", (rid, token))
        if recording and recording["duration_ms"] >= 1000:
            try:
                ratio = float(recording["accuracy"] or 0)
            except (TypeError, ValueError):
                ratio = 0.0
            if math.isfinite(ratio):
                acc = _round_js(max(0.0, min(1.0, ratio)) * 35)
    final_score = _score_from_snapshot(dict(row), snapshot, acc)
    with db._tx() as conn:
        conn.execute("UPDATE scores SET score=? WHERE id=? AND play_token=?",
                     (final_score, row["score_id"], token))
        conn.execute("UPDATE game_plays SET final_score=? WHERE token=? AND status='scored'",
                     (final_score, token))


def finalize(db: Database, play: dict, report: dict, *, nickname: str = "", now: float | None = None) -> tuple[int, int, bool]:
    """一次性写入本轮成绩；返回 (id, score, was_already_finalized)。"""
    now = time.time() if now is None else now
    with db._lock:
        current = db.one("SELECT * FROM game_plays WHERE token=?", (play["token"],))
        if current and current["status"] == "scored":
            return int(current["score_id"]), int(current["final_score"]), True
        if not current or current["status"] != "started":
            raise PlayError("这一轮已结束", "play_finished", 409)
        play = dict(current)

        if play["game_type"] == "order" and play["phase"] not in ("scoring", "uploaded"):
            raise PlayError("排排坐需要先结束录音阶段", "phase_required", 409)
        sanitized, events, details = validate_report(db, play, report)
        elapsed = _elapsed(play, now)
        settlement_elapsed = elapsed
        combo_points, best_combo, bonus_seconds, terminal_combo = _combo(
            BASE_POINTS[play["game_type"]], events, int(play["terminal_combo"] or 0), int(play["time_limit"]))
        total_limit = int(play["time_limit"]) + bonus_seconds
        if elapsed > int(play["time_limit"]):
            # 首个时限之后只能采用服务器在时限内收到的快照；不能由迟到报告自证连击加时。
            used_checkpoint = False
            try:
                if not play["checkpoint_at"]:
                    raise ValueError("no timely checkpoint")
                checkpoint = {"detail": json.loads(play["detail"]), "combo_events": json.loads(play["combo_events"])}
                checkpoint_elapsed = float(play["checkpoint_elapsed"] or 0)
                sanitized, events, details = validate_report(db, play, checkpoint)
                combo_points, best_combo, bonus_seconds, terminal_combo = _combo(
                    BASE_POINTS[play["game_type"]], events, int(play["terminal_combo"] or 0), int(play["time_limit"]))
                total_limit = int(play["time_limit"]) + bonus_seconds
                if checkpoint_elapsed > total_limit:
                    raise ValueError("checkpoint arrived after its deadline")
                elapsed = checkpoint_elapsed
                used_checkpoint = True
            except (TypeError, ValueError):
                pass
            if not used_checkpoint:
                empty_report = {"detail": [], "combo_events": []}
                if play["game_type"] == "match":
                    empty_report["detail"] = [{"level": play["level"], "answers": []}]
                sanitized, events, details = validate_report(db, play, empty_report)
                combo_points, best_combo, bonus_seconds, terminal_combo = _combo(
                    BASE_POINTS[play["game_type"]], events, int(play["terminal_combo"] or 0), int(play["time_limit"]))
                total_limit = int(play["time_limit"]) + bonus_seconds
                elapsed = total_limit

        rec_points, accuracy_points, recording_id = _recording_details(db, play, sanitized, play["user_id"])
        complete = details["matched"] == len(details["expected"])
        if not complete:
            elapsed = min(settlement_elapsed, total_limit)
        time_left = max(0.0, _time_budget(play, bonus_seconds, details["wrong"]) - elapsed)
        speed_points = ((details["answer_points"] + combo_points) * 0.2 *
                        min(1.0, time_left / max(1, int(play["time_limit"])))) if complete else 0.0
        snapshot = {"answer_points": details["answer_points"], "recording_points": rec_points,
                    "combo_points": combo_points, "speed_points": speed_points,
                    "recording_id": recording_id, "bonus_seconds": bonus_seconds,
                    "elapsed": min(elapsed, total_limit)}
        final_score = _score_from_snapshot(play, snapshot, accuracy_points)
        sanitized_detail = sanitized
        if play["game_type"] == "match":
            sanitized_detail[0].update({"matched": details["matched"], "total": len(details["expected"]),
                                        "wrong": details["wrong"], "score": final_score})
        else:
            for item in sanitized_detail:
                if item.get("ord") == (recording_id and item.get("ord")):
                    item["recording_id"] = recording_id
            if sanitized_detail and play["game_type"] == "order":
                sanitized_detail[0]["recording_id"] = recording_id
        detail_json = json.dumps(sanitized_detail, ensure_ascii=False, allow_nan=False)
        record = {"bank_id": play["bank_id"], "bank_title": (db.get_bank(play["bank_id"]) or {}).get("title", ""),
                  "device": play["device"], "nickname": nickname, "mode": play["mode"], "score": final_score,
                  "matched": details["matched"], "total_pairs": len(details["expected"]), "wrong": details["wrong"],
                  "best_combo": best_combo, "duration": int(round(min(elapsed, total_limit))),
                  "level_count": 1, "detail": detail_json, "game_type": play["game_type"],
                  "rule_version": RULE_VERSION, "play_token": play["token"], "score_factor": play["score_factor"]}
        sid = db.insert_score(record, user_id=play["user_id"])
        if recording_id:
            db.execute("UPDATE recordings SET score_id=? WHERE id=? AND score_id IS NULL", (sid, recording_id))
        db.execute(
            "UPDATE game_plays SET status='scored',score_id=?,final_score=?,terminal_combo=?,detail=?,combo_events=?,"
            "score_snapshot=?,checkpoint_at=? WHERE token=? AND status='started'",
            (sid, final_score, terminal_combo, detail_json,
             json.dumps(events), json.dumps(snapshot), now, play["token"]))
        return sid, final_score, False


def checkpoint(db: Database, play: dict, report: dict, now: float | None = None) -> None:
    now = time.time() if now is None else now
    if play["status"] != "started":
        raise PlayError("这一轮已结束", "play_finished", 409)
    sanitized, events, details = validate_report(db, play, report)
    elapsed = _elapsed(play, now)
    _extra, _best, bonus_seconds, _terminal = _combo(
        BASE_POINTS[play["game_type"]], events, int(play["terminal_combo"] or 0), int(play["time_limit"]))
    if elapsed > int(play["time_limit"]) + bonus_seconds:
        raise PlayError("本轮已超时", "play_expired", 409)
    db.execute("UPDATE game_plays SET detail=?,combo_events=?,checkpoint_at=?,checkpoint_elapsed=?,"
               "checkpoint_bonus_seconds=? WHERE token=? AND status='started'",
               (json.dumps(sanitized, ensure_ascii=False), json.dumps(events), now, elapsed,
                bonus_seconds, play["token"]))


def recording_arrived(db: Database, token: str) -> None:
    """ASR 完成后只更新原成绩行；已冻结的衰减与速度分保持不变。"""
    with db._lock:
        _update_late_score(db, token)
