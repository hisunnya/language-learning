"""排排坐的朗读录音：收下、存成 MP3、排队识别、给分；以及排排坐一局的总分（由服务器算，不信页面报的）。

计分（和 web/js/item-core.js 一致）：每句拼接 10 分（检查出错一次扣 2，最少 2）；有效朗读 30 分；
奖励 = 识别出的词和标准句子对上的比例 × 20（四舍五入）。

* 有效朗读：录音不短于 1 秒，而且（有识别时）识别出了至少一个词。没听到人声 → 不算，学生可以重录再交。
* 识别排队：一个后台线程一条一条地识别（2 核机器同时跑几个会把网站拖慢）。提交录音的请求最多等 WAIT 秒，
  等到了就当场给分，没等到先回 pending，识别完再把奖励分补进成绩（scores 里那一行重新算）。
* 文件：数据目录下的 recordings/YYYYMM/，统一转成单声道 32 kbps 的 MP3（各种手机都能播，一条十几秒约 50 KB）。
  服务器没有 ffmpeg 时原样保存。
"""
from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import tempfile
import threading
import time
import traceback
from pathlib import Path

from . import asr, items as items_mod
from .db import Database

ARRANGE, WRONG, FLOOR, RECORDING, BONUS_MAX = 10, 2, 2, 30, 20
MIN_MS, MAX_MS = 1000, 35000
MAX_BYTES = 4 * 1024 * 1024
WAIT = 12.0
EXT = {"audio/webm": "webm", "audio/ogg": "ogg", "audio/mp4": "m4a", "audio/aac": "aac", "audio/mpeg": "mp3", "audio/wav": "wav"}


def arrange_points(wrong: int) -> int:
    return max(FLOOR, ARRANGE - WRONG * max(0, int(wrong or 0)))


def bonus_for(accuracy: float) -> int:
    return int(round(max(0.0, min(1.0, accuracy)) * BONUS_MAX))


def root(db: Database) -> Path:
    return Path(os.environ.get("WP_RECORDINGS_DIR") or (Path(db.path).parent / "recordings"))


def ffmpeg() -> str | None:
    return shutil.which("ffmpeg")


def _run(args: list[str], timeout: int = 60) -> bool:
    try:
        return subprocess.run(args, capture_output=True, timeout=timeout).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def probe_ms(path: Path) -> int | None:
    exe = shutil.which("ffprobe")
    if not exe:
        return None
    try:
        out = subprocess.run([exe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                             capture_output=True, timeout=30).stdout.decode().strip()
        return int(float(out) * 1000)
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


# ------------------------------------------------------------------ 收录音

def store(db: Database, *, user_id: int | None, bank: dict, item_ord: int, play_token: str, data: bytes,
          mime: str, client_ms: int) -> dict:
    """存文件、建一行 recordings，返回这一行。有识别时 status=pending（交给队列），没有时当场判有效。"""
    base = root(db) / time.strftime("%Y%m")
    base.mkdir(parents=True, exist_ok=True)
    stem = "u%s-b%d-i%d-%d-%s" % (user_id or 0, bank["id"], item_ord, int(time.time()), os.urandom(3).hex())
    raw_ext = EXT.get(mime.split(";")[0].strip().lower(), "bin")
    fd, raw = tempfile.mkstemp(prefix="rec-", suffix="." + raw_ext, dir=str(base))
    with os.fdopen(fd, "wb") as fh:
        fh.write(data)
    raw = Path(raw)
    target = base / (stem + ".mp3")
    exe = ffmpeg()
    if exe and _run([exe, "-y", "-v", "error", "-i", str(raw), "-ac", "1", "-ar", "22050", "-b:a", "32k", str(target)]):
        raw.unlink(missing_ok=True)
    else:                                   # 没有 ffmpeg（或转不了）：原样留着
        target = base / (stem + "." + raw_ext)
        os.replace(raw, target)
    ms = probe_ms(target) or max(0, min(int(client_ms or 0), MAX_MS))
    rel = str(target.relative_to(root(db)))
    status = "pending" if asr.available() else "noasr"
    valid = 1 if (status == "noasr" and ms >= MIN_MS) else 0
    rid = db.execute(
        "INSERT INTO recordings(user_id, bank_id, item_ord, play_token, file, bytes, duration_ms, status, valid, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        (user_id, bank["id"], item_ord, play_token[:64], rel, target.stat().st_size, ms, status, valid, int(time.time()))).lastrowid
    return get(db, rid)


def get(db: Database, rid: int) -> dict | None:
    row = db.one("SELECT * FROM recordings WHERE id=?", (rid,))
    return dict(row) if row else None


def public(rec: dict) -> dict:
    """给页面的样子（不含文件路径）。"""
    return {k: rec[k] for k in ("id", "item_ord", "status", "valid", "bonus", "accuracy", "transcript", "duration_ms", "created_at")} | {
        "valid": bool(rec["valid"])}


def file_path(db: Database, rec: dict) -> Path | None:
    path = (root(db) / rec["file"]).resolve()
    try:
        path.relative_to(root(db).resolve())
    except ValueError:
        return None
    return path if path.is_file() else None


# ------------------------------------------------------------------ 识别

def score_one(db: Database, rid: int) -> dict | None:
    """识别一条录音，写回结果；如果它已经连到某一局成绩，重算那一局的总分。"""
    rec = get(db, rid)
    if not rec or rec["status"] != "pending":
        return rec
    bank = db.get_bank(rec["bank_id"])
    found = db.bank_items(rec["bank_id"]) if bank else []
    reference = found[rec["item_ord"]]["answer"] if rec["item_ord"] < len(found) else ""
    path = file_path(db, rec)
    text = None
    if path is not None:
        exe = ffmpeg()
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "in.wav"
            source = wav if exe and _run([exe, "-y", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "16000", str(wav)]) else path
            text = asr.transcribe(source)
    long_enough = rec["duration_ms"] >= MIN_MS
    if text is None:                         # 识别本身出错：不怪学生，按时长算有效，没有奖励
        db.execute("UPDATE recordings SET status='failed', valid=?, scored_at=? WHERE id=?",
                   (1 if long_enough else 0, int(time.time()), rid))
    else:
        acc = asr.accuracy(reference, text)
        valid = 1 if (long_enough and asr.words(text)) else 0
        db.execute("UPDATE recordings SET status='done', transcript=?, accuracy=?, valid=?, bonus=?, scored_at=? WHERE id=?",
                   (text[:500], acc, valid, bonus_for(acc) if valid else 0, int(time.time()), rid))
    rec = get(db, rid)
    if rec and rec["score_id"]:
        rescore(db, rec["score_id"])
    return rec


class Worker:
    """后台识别队列：一条一条来。提交录音的请求可以等某一条的结果（最多 WAIT 秒）。"""

    def __init__(self, db: Database):
        self.db = db
        self.q: "queue.Queue[int]" = queue.Queue()
        self.done: dict[int, threading.Event] = {}
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._loop, name="asr-worker", daemon=True)
        self.thread.start()
        try:                                  # 上次没识别完的（服务重启）接着识别
            for row in db.query("SELECT id FROM recordings WHERE status='pending' ORDER BY id"):
                self.submit(row["id"])
        except Exception:                     # pragma: no cover
            traceback.print_exc()

    def submit(self, rid: int) -> threading.Event:
        with self.lock:
            event = self.done.setdefault(rid, threading.Event())
        self.q.put(rid)
        return event

    def wait(self, rid: int, seconds: float = WAIT) -> dict | None:
        with self.lock:
            event = self.done.get(rid)
        if event:
            event.wait(seconds)
        return get(self.db, rid)

    def _loop(self) -> None:
        while True:
            rid = self.q.get()
            try:
                score_one(self.db, rid)
            except Exception:                 # pragma: no cover - 一条出错不影响后面的
                traceback.print_exc()
                self.db.execute("UPDATE recordings SET status='failed', scored_at=? WHERE id=? AND status='pending'",
                                (int(time.time()), rid))
            finally:
                with self.lock:
                    event = self.done.pop(rid, None)
                if event:
                    event.set()


# ------------------------------------------------------------------ 一局的总分

def order_score(db: Database, bank_id: int, user_id: int | None, detail: list) -> tuple[int, int, list]:
    """排排坐一局：按页面报的每句「拼接出错几次、排对没有、用的哪条录音」，由服务器算分。
    录音必须是这个人、这个题库、这道题的；返回 (总分, 排对的句数, 整理后的明细)。"""
    total, arranged, clean = 0, 0, []
    for entry in detail if isinstance(detail, list) else []:
        if not isinstance(entry, dict):
            continue
        try:
            ordinal = int(entry.get("ord"))
            wrong = max(0, min(50, int(entry.get("wrong") or 0)))
        except (TypeError, ValueError):
            continue
        ok = bool(entry.get("arranged"))
        rec = None
        try:
            rid = int(entry.get("recording_id") or 0)
        except (TypeError, ValueError):
            rid = 0
        if rid:
            row = db.one("SELECT * FROM recordings WHERE id=? AND bank_id=? AND item_ord=? AND user_id IS ?",
                         (rid, bank_id, ordinal, user_id))
            rec = dict(row) if row else None
        points = (arrange_points(wrong) if ok else 0) + ((RECORDING + rec["bonus"]) if (ok and rec and rec["valid"]) else 0)
        total += points
        arranged += 1 if ok else 0
        clean.append({"ord": ordinal, "wrong": wrong, "arranged": ok, "recording_id": rec["id"] if rec else None,
                      "skipped": bool(entry.get("skipped")), "points": points})
    return total, arranged, clean


def attach(db: Database, score_id: int, detail: list) -> None:
    ids = [d["recording_id"] for d in detail if d.get("recording_id")]
    for rid in ids:
        db.execute("UPDATE recordings SET score_id=? WHERE id=?", (score_id, rid))


def rescore(db: Database, score_id: int) -> None:
    """有录音识别完了：按存着的明细重算这一局的总分。"""
    row = db.one("SELECT bank_id, user_id, detail FROM scores WHERE id=?", (score_id,))
    if not row:
        return
    try:
        detail = json.loads(row["detail"] or "[]")
    except ValueError:
        return
    total, _arranged, clean = order_score(db, row["bank_id"], row["user_id"], detail)
    db.execute("UPDATE scores SET score=?, detail=? WHERE id=?", (total, json.dumps(clean, ensure_ascii=False), score_id))


def for_scores(db: Database, score_ids: list[int]) -> dict[int, list[dict]]:
    """成绩明细里要显示的录音：score_id → [录音]。"""
    out: dict[int, list[dict]] = {}
    if not score_ids:
        return out
    marks = ",".join("?" * len(score_ids))
    for row in db.query("SELECT * FROM recordings WHERE score_id IN (%s) ORDER BY item_ord, id" % marks, tuple(score_ids)):
        out.setdefault(row["score_id"], []).append(public(dict(row)))
    return out


def speech_reference(db: Database, bank_id: int, item_ord: int) -> str:
    bank = db.get_bank(bank_id)
    found = db.bank_items(bank_id) if bank else []
    return items_mod.speech_text("order", found[item_ord]) if item_ord < len(found) else ""
