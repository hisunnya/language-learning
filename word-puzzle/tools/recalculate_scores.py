#!/usr/bin/env python3
"""预览或一次性重算历史成绩；默认只读，--apply 会先做 SQLite 一致性备份。"""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MIGRATION = "scoring-v4"


def round_js(value: float) -> int:
    return math.floor(max(0.0, value) + 0.5)


def open_readonly(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    return conn


def _detail(value: str) -> list | None:
    try:
        parsed = json.loads(value or "[]")
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, list) else None


def _session_start(row: sqlite3.Row) -> datetime | None:
    try:
        duration = int(row["duration"])
        if not 0 <= duration <= 86400:
            return None
        created = datetime.fromisoformat(str(row["created_at"]))
    except (TypeError, ValueError, OverflowError):
        return None
    return created - timedelta(seconds=duration)


def _invalid_duration(row: sqlite3.Row) -> bool:
    try:
        duration = int(row["duration"])
    except (TypeError, ValueError, OverflowError):
        return True
    return not 0 <= duration <= 86400


def _cumulative_scores(detail: list | None) -> list[int] | None:
    if not detail:
        return None
    values = []
    for level in detail:
        if not isinstance(level, dict):
            return None
        value = level.get("score")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            return None
        values.append(round_js(float(value)))
    return values


def _same_prefix(short: list | None, long: list | None) -> bool:
    if not short or not long or len(short) >= len(long):
        return False
    return json.dumps(short, ensure_ascii=False, sort_keys=True, separators=(",", ":")) == \
        json.dumps(long[:len(short)], ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _order_score(conn: sqlite3.Connection, row: sqlite3.Row, detail: list | None) -> tuple[int | None, str]:
    if not detail:
        return None, "缺少逐题明细"
    answer, recording, accuracy = 0, 0, 0
    seen: set[int] = set()
    for item in detail:
        if not isinstance(item, dict):
            return None, "题目明细格式无效"
        ordinal = item.get("ord")
        if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 0 or ordinal in seen:
            return None, "题目序号缺失、无效或重复"
        seen.add(ordinal)
        wrong = item.get("wrong", 0)
        if isinstance(wrong, bool) or not isinstance(wrong, int) or not 0 <= wrong <= 1000:
            return None, "错答次数无效"
        if item.get("arranged") is not True:
            continue
        answer += max(6, 30 - 6 * wrong)
        rid = item.get("recording_id")
        if not rid:
            continue
        if isinstance(rid, bool) or not isinstance(rid, int):
            return None, "录音编号无效"
        rec = conn.execute("SELECT duration_ms, accuracy FROM recordings WHERE id=? AND score_id=?",
                           (rid, row["id"])).fetchone()
        if not rec:
            return None, "明细引用的录音不存在或不属于此成绩"
        if int(rec["duration_ms"] or 0) >= 1000:
            recording += 20
            try:
                ratio = float(rec["accuracy"] or 0)
            except (TypeError, ValueError):
                return None, "录音识别准确率无效"
            if not math.isfinite(ratio):
                return None, "录音识别准确率无效"
            accuracy += round_js(max(0.0, min(1.0, ratio)) * 35)
    return answer + recording + accuracy, ""


def build_plan(conn: sqlite3.Connection) -> dict:
    tables = {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "scores" not in tables:
        raise ValueError("数据库缺少 scores 表")
    columns = {r["name"] for r in conn.execute("PRAGMA table_info(scores)")}
    required = {"id", "bank_id", "user_id", "device", "mode", "score", "game_type",
                "detail", "duration", "created_at"}
    if not required <= columns:
        raise ValueError("scores 表缺少所需字段：" + ", ".join(sorted(required - columns)))
    version_filter = " WHERE COALESCE(rule_version,0)<4" if "rule_version" in columns else ""
    rows = list(conn.execute("SELECT * FROM scores" + version_filter + " ORDER BY created_at,id"))
    originals = {int(row["id"]): int(row["score"] or 0) for row in rows}
    details = {int(row["id"]): _detail(row["detail"]) for row in rows}
    ambiguous_duplicates = []
    duplicate_deductions: dict[int, int] = {}
    candidates: dict[tuple, list[sqlite3.Row]] = {}
    for row in rows:
        if (row["game_type"] or "match") != "match" or row["bank_id"] is None:
            continue
        actor = ("u", row["user_id"]) if row["user_id"] is not None else ("d", row["device"] or "")
        candidates.setdefault((actor, row["bank_id"], row["mode"]), []).append(row)
    for related in candidates.values():
        for later in related:
            later_detail = details[int(later["id"])]
            later_parts = _cumulative_scores(later_detail)
            if not later_detail:
                continue
            matches = []
            uncertain = False
            later_start = _session_start(later)
            for earlier in related:
                if int(earlier["id"]) >= int(later["id"]):
                    break
                earlier_detail = details[int(earlier["id"])]
                if not _same_prefix(earlier_detail, later_detail):
                    continue
                early_start = _session_start(earlier)
                early_parts = _cumulative_scores(earlier_detail)
                if later_start is None or early_start is None:
                    uncertain = True
                    continue
                if abs((later_start - early_start).total_seconds()) > 2:
                    uncertain = True
                    continue
                if not later_parts or not early_parts or later_parts[:len(early_parts)] != early_parts:
                    uncertain = True
                    continue
                if sum(early_parts) != originals[int(earlier["id"])] or sum(later_parts) != originals[int(later["id"])]:
                    uncertain = True
                    continue
                matches.append((len(early_parts), sum(early_parts)))
            if matches:
                duplicate_deductions[int(later["id"])] = max(matches)[1]
            elif uncertain:
                ambiguous_duplicates.append(int(later["id"]))

    changes, unchanged, preserved_invalid = [], [], []
    invalid_duration_rows = [{"id": int(row["id"]), "duration": row["duration"]}
                             for row in rows if _invalid_duration(row)]
    for row in rows:
        score_id = int(row["id"])
        game_type = row["game_type"] or "match"
        source_score = originals[score_id]
        detail = details[score_id]
        if source_score < 0:
            preserved_invalid.append({"id": score_id, "reason": "原始分数为负数"})
            unchanged.append({"id": score_id, "score": source_score})
            continue
        if game_type == "match":
            adjusted = max(0, source_score - duplicate_deductions.get(score_id, 0))
            new_score = round_js(adjusted * 0.4)
        elif game_type == "spell":
            new_score = round_js(source_score * 8)
        elif game_type == "verb":
            new_score = source_score
        elif game_type == "order":
            if "recordings" not in tables:
                preserved_invalid.append({"id": score_id, "reason": "缺少录音表"})
                unchanged.append({"id": score_id, "score": source_score})
                continue
            calculated, reason = _order_score(conn, row, detail)
            if calculated is None:
                preserved_invalid.append({"id": score_id, "reason": reason})
                unchanged.append({"id": score_id, "score": source_score})
                continue
            new_score = calculated
        else:
            preserved_invalid.append({"id": score_id, "reason": "未知游戏类型：" + str(game_type)})
            unchanged.append({"id": score_id, "score": source_score})
            continue
        changes.append({"id": score_id, "old_score": source_score, "new_score": new_score,
                        "duplicate_prefix_deduction": duplicate_deductions.get(score_id, 0)})
    return {"rows": len(rows), "changes": changes, "unchanged": unchanged,
            "duplicate_prefix_rows": sorted(duplicate_deductions),
            "ambiguous_duplicate_rows": sorted(set(ambiguous_duplicates)),
            "preserved_invalid": preserved_invalid, "invalid_duration_rows": invalid_duration_rows}


def make_backup(source: Path, backup: Path) -> None:
    if source.resolve() == backup.resolve():
        raise ValueError("备份路径不能与数据库相同")
    if backup.exists():
        raise FileExistsError("备份文件已存在，拒绝覆盖：" + str(backup))
    backup.parent.mkdir(parents=True, exist_ok=True)
    src = sqlite3.connect(source)
    dst = sqlite3.connect(backup)
    try:
        src.backup(dst)
        result = dst.execute("PRAGMA integrity_check").fetchone()
        if not result or result[0] != "ok":
            raise sqlite3.DatabaseError("备份 integrity_check 失败：" + str(result[0] if result else "无结果"))
        dst.commit()
    finally:
        dst.close()
        src.close()


def apply_plan(db_path: Path, backup_path: Path) -> dict:
    make_backup(db_path, backup_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("CREATE TABLE IF NOT EXISTS score_migration_markers("
                     "migration TEXT PRIMARY KEY, applied_at TEXT NOT NULL, report TEXT NOT NULL)")
        if conn.execute("SELECT 1 FROM score_migration_markers WHERE migration=?", (MIGRATION,)).fetchone():
            conn.rollback()
            raise ValueError("scoring-v4 已应用；未改写数据库，备份已保留")
        plan = build_plan(conn)
        conn.execute("CREATE TABLE IF NOT EXISTS score_recalc_v4_snapshots("
                     "score_id INTEGER PRIMARY KEY, original_score INTEGER NOT NULL, original_detail TEXT NOT NULL, "
                     "snapshot_at TEXT NOT NULL)")
        conn.executemany("INSERT INTO score_recalc_v4_snapshots(score_id,original_score,original_detail,snapshot_at) "
                         "VALUES(?,?,?,?)",
                         [(int(row["id"]), int(row["score"] or 0), row["detail"] or "[]",
                           time.strftime("%Y-%m-%d %H:%M:%S")) for row in conn.execute("SELECT id,score,detail FROM scores")])
        for item in plan["changes"]:
            conn.execute("UPDATE scores SET score=? WHERE id=?", (item["new_score"], item["id"]))
        # 成绩权重改变后榜首和结算进度失效；与规则变更相同，保留已经颁发的奖状，随后按新成绩惰性补算。
        plan["invalidated_award_cache_rows"] = {}
        for table in ("board_leaders", "award_days"):
            exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
            if exists:
                count = conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]
                conn.execute("DELETE FROM " + table)
                plan["invalidated_award_cache_rows"][table] = count
        report = json.dumps(plan, ensure_ascii=False, separators=(",", ":"))
        conn.execute("INSERT INTO score_migration_markers(migration,applied_at,report) VALUES(?,?,?)",
                     (MIGRATION, time.strftime("%Y-%m-%d %H:%M:%S"), report))
        conn.commit()
        plan["backup"] = str(backup_path)
        plan["applied"] = True
        return plan
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=ROOT / "var" / "app.db", help="SQLite 成绩数据库")
    parser.add_argument("--apply", action="store_true", help="先备份，再事务式应用（默认仅预览）")
    parser.add_argument("--backup", type=Path, help="--apply 时的 SQLite backup API 备份路径")
    args = parser.parse_args(argv)
    try:
        if args.apply:
            backup = args.backup or args.db.with_name(
                args.db.stem + ".before-scoring-v4-" + time.strftime("%Y%m%d_%H%M%S") + args.db.suffix)
            report = apply_plan(args.db, backup)
        else:
            with open_readonly(args.db) as conn:
                report = build_plan(conn)
                report["applied"] = False
                report["note"] = "只读预览；未写入数据库"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (OSError, sqlite3.Error, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
