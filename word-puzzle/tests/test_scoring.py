"""第 4 版在线每轮计分、身份绑定、衰减、计时及历史重算工具。"""
from __future__ import annotations

import json
import sqlite3
import shutil
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, ROOT.as_posix())
sys.path.insert(0, (ROOT / "tools").as_posix())

from server import recordings, scoring, scorebook
from tests.test_auth import Client, HttpCase
from recalculate_scores import apply_plan, build_plan, open_readonly


class ScoringCase(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.db = cls.app.Handler.db
        cls.admin_user, _ = cls.svc.create_user("T001", "老师", password="Teach3r!pw",
                                                role="admin", must_change=False)
        cls.student_user, _ = cls.svc.create_user("S001", "学生", password="Ready2026x",
                                                  must_change=False, class_name="一班")
        cls.db.execute("INSERT OR IGNORE INTO teacher_students(teacher_id,student_id,added_at) VALUES(?,?,0)",
                       (cls.admin_user["id"], cls.student_user["id"]))
        cls.db.execute("INSERT OR IGNORE INTO user_tags(user_id,tag,teacher_id) VALUES(?, '一班', ?)",
                       (cls.student_user["id"], cls.admin_user["id"]))
        cls.match = cls.db.insert_bank({
            "title": "配对测试", "level1": "初中", "level2": "一", "level3": "上", "level4": "全部",
            "source": "seed", "owner_id": cls.admin_user["id"], "pairs_per_level": 3,
        }, [{"unit": "U", "en": "word%d" % n, "cn": "词%d" % n} for n in range(6)])
        cls.db.execute("INSERT INTO bank_tags(bank_id,tag,teacher_id) VALUES(?, '一班', ?)",
                       (cls.match, cls.admin_user["id"]))
        cls.spell = cls.db.insert_item_bank({
            "title": "拼写测试", "level1": "大学", "level2": "一", "level3": "上", "level4": "U1",
            "source": "import", "game_type": "spell", "owner_id": cls.admin_user["id"],
        }, [{"before": "", "answer": "word%d" % n, "after": "", "cn": "词", "text": "word%d" % n}
            for n in range(8)])
        cls.verb = cls.db.insert_item_bank({
            "title": "动词测试", "level1": "大学", "level2": "一", "level3": "上", "level4": "U1",
            "source": "import", "game_type": "verb", "owner_id": cls.admin_user["id"],
        }, [{"before": "", "answer": "go%d" % n, "after": "", "cn": "走", "text": "go%d" % n}
            for n in range(5)])
        cls.order = cls.db.insert_item_bank({
            "title": "排句测试", "level1": "大学", "level2": "一", "level3": "上", "level4": "U1",
            "source": "import", "game_type": "order", "owner_id": cls.admin_user["id"],
        }, [{"cn": "你好", "fragments": [{"segs": [["hello", 0]]}], "answer": "hello"},
            {"cn": "再见", "fragments": [{"segs": [["goodbye", 0]]}], "answer": "goodbye"}])
        for bid in (cls.spell, cls.verb, cls.order):
            cls.db.execute("INSERT INTO bank_tags(bank_id,tag,teacher_id) VALUES(?, '一班', ?)",
                           (bid, cls.admin_user["id"]))

    def setUp(self):
        super().setUp()
        self.db.execute("DELETE FROM scores")
        self.db.execute("DELETE FROM game_plays")
        self.db.execute("DELETE FROM recordings")

    def login(self, no):
        c = Client(self.port)
        pw = "Teach3r!pw" if no == "T001" else "Ready2026x"
        self.assertEqual(c.json("POST", "/api/auth/login", {"student_no": no, "password": pw})[0], 200)
        return c

    def begin(self, bid, *, level=0, ords=None, previous=""):
        bank = self.db.get_bank(bid)
        return scoring.begin_play(
            self.db, bank=bank, user_id=self.student_user["id"], device="u%d" % self.student_user["id"],
            mode="online", level=level, ords=ords, previous_play_token=previous)

    def finish_at_limit(self, started, report):
        play = scoring.get_owned_play(
            self.db, started["play_token"], user_id=self.student_user["id"],
            device="u%d" % self.student_user["id"], mode="online")
        return scoring.finalize(self.db, play, report, now=started["started_at"] + started["time_limit"])

    def match_report(self, answers, events=None, level=0):
        return {"level": level, "detail": [{"level": level, "name": "round", "score": 999999,
                "matched": 999, "total": 999, "wrong": 0, "bestCombo": 99, "duration": 1,
                "answers": answers}], "combo_events": events or []}


class TestScoringAPI(ScoringCase):
    def test_missing_token_is_explicitly_rejected_and_tokens_are_owner_bound(self):
        c = self.login("S001")
        status, body = c.json("POST", "/api/scores", {"bank_id": self.match, "score": 100})
        self.assertEqual((status, body["code"]), (409, "play_required"))
        start = c.json("POST", "/api/plays/start", {"bank_id": self.match, "level": 0})
        self.assertEqual(start[0], 201, start[1])
        token = start[1]["play_token"]
        stranger = self.svc.create_user("S002", "另一人", password="Ready2026x",
                                        must_change=False, class_name="一班")[0]
        self.db.execute("INSERT OR IGNORE INTO teacher_students(teacher_id,student_id,added_at) VALUES(?,?,0)",
                        (self.admin_user["id"], stranger["id"]))
        self.db.execute("INSERT INTO user_tags(user_id,tag,teacher_id) VALUES(?, '一班', ?)",
                        (stranger["id"], self.admin_user["id"]))
        other = self.login("S002")
        status, body = other.json("POST", "/api/scores", {
            "bank_id": self.match, "play_token": token, "level": 0, "detail": [], "combo_events": [],
        })
        self.assertEqual((status, body["code"]), (404, "play_forbidden"))

    def test_http_start_accepts_complete_spell_and_verb_rounds(self):
        c = self.login("S001")
        for bank_id, count, seconds_per_item in ((self.spell, 8, 20), (self.verb, 5, 12)):
            status, started = c.json("POST", "/api/plays/start", {
                "bank_id": bank_id, "level": 0, "ords": list(range(count)),
            })
            self.assertEqual(status, 201, started)
            self.assertEqual(started["time_limit"], count * seconds_per_item)

    def test_duplicate_finalize_returns_the_same_score_row(self):
        c = self.login("S001")
        token = c.json("POST", "/api/plays/start", {"bank_id": self.match, "level": 0})[1]["play_token"]
        report = self.match_report(
            [{"ord": i, "solved": True, "wrong": 0} for i in range(3)],
            [{"ord": i, "eligible": True} for i in range(3)])
        payload = {"bank_id": self.match, "play_token": token, **report}
        first_status, first = c.json("POST", "/api/scores", payload)
        second_status, second = c.json("POST", "/api/scores", payload)
        self.assertEqual(first_status, 201)
        self.assertEqual(second_status, 200)
        self.assertEqual((first["id"], first["score"]), (second["id"], second["score"]))
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM scores WHERE play_token=?", (token,))["n"], 1)

    def test_http_timeout_settlement_persists_zero_with_capped_duration(self):
        import time
        c = self.login("S001")
        started = c.json("POST", "/api/plays/start", {"bank_id": self.match, "level": 1})[1]
        token = started["play_token"]
        late_start = time.time() - started["time_limit"] - 2
        self.db.execute("UPDATE game_plays SET started_at=?, expires_at=? WHERE token=?",
                        (late_start, late_start + started["time_limit"], token))
        report = {
            "level": 1,
            "detail": [{
                "level": 1, "name": "1（2/2）", "score": 0, "matched": 0, "total": 3,
                "wrong": 0, "bestCombo": 0, "duration": 60,
                "answers": [{"ord": i, "solved": False, "wrong": 0} for i in range(3)],
            }],
            "combo_events": [],
        }
        status, result = c.json("POST", "/api/scores", {
            "bank_id": self.match, "play_token": token, **report,
            "score": 0, "matched": 0, "total_pairs": 3, "wrong": 0,
            "best_combo": 0, "duration": 60, "level_count": 1, "time_left": 0,
            "initial_seconds": 60, "bonus_seconds": 0, "rule_version": 4,
        })
        self.assertEqual(status, 201, result)
        self.assertEqual(result["score"], 0, "超时后到达的答案不能获分")
        row = self.db.one("SELECT score,duration FROM scores WHERE play_token=?", (token,))
        self.assertEqual((row["score"], row["duration"]), (0, started["time_limit"]))
        self.assertEqual(self.db.one("SELECT status FROM game_plays WHERE token=?", (token,))["status"], "scored")

    def test_one_round_never_accepts_a_prior_level_and_is_complete_on_its_own(self):
        c = self.login("S001")
        started = c.json("POST", "/api/plays/start", {"bank_id": self.match, "level": 0})[1]
        report = self.match_report(
            [{"ord": i, "solved": True, "wrong": 0} for i in range(3)],
            [{"ord": i, "eligible": True} for i in range(3)], level=0)
        status, result = c.json("POST", "/api/scores", {"bank_id": self.match,
            "play_token": started["play_token"], **report, "level_count": 99, "matched": 9999, "score": 999999})
        self.assertEqual(status, 201, result)
        row = dict(self.db.one("SELECT * FROM scores WHERE id=?", (result["id"],)))
        self.assertEqual((row["matched"], row["total_pairs"], row["level_count"], row["rule_version"]), (3, 3, 1, 4))
        self.assertTrue(scorebook.is_complete(row, levels=99))


class TestRoundRules(ScoringCase):
    def test_match_weight_and_round_local_wrong_floor(self):
        started = self.begin(self.match)
        report = self.match_report(
            [{"ord": 0, "solved": True, "wrong": 1}, {"ord": 1, "solved": True, "wrong": 1}],
            [{"ord": 0, "eligible": False, "break": True},
             {"ord": 1, "eligible": False, "break": True}])
        _sid, score, _duplicate = self.finish_at_limit(started, report)
        self.assertEqual(score, 36, "first miss floors at zero; a later miss reduces the running score")

        floor = self.begin(self.match)
        report = self.match_report(
            [{"ord": 0, "solved": False, "wrong": 7}],
            [{"ord": 0, "eligible": False, "break": True} for _ in range(7)])
        self.assertEqual(self.finish_at_limit(floor, report)[1], 0)

    def test_match_misses_can_wipe_previously_earned_combo_balance(self):
        for misses, expected in ((10, 2), (11, 0), (12, 0)):
            with self.subTest(misses=misses):
                started = self.begin(self.match)
                report = self.match_report(
                    [{"ord": 0, "solved": True, "wrong": 0},
                     {"ord": 1, "solved": True, "wrong": 0},
                     {"ord": 2, "solved": False, "wrong": misses}],
                    [{"ord": 0, "eligible": True}, {"ord": 1, "eligible": True}]
                    + [{"ord": 2, "eligible": False, "break": True} for _ in range(misses)])
                sid, score, _ = self.finish_at_limit(started, report)
                self.assertEqual(score, expected)
                row = self.db.one("SELECT score_snapshot FROM game_plays WHERE score_id=?", (sid,))
                snapshot = json.loads(row["score_snapshot"])
                self.assertEqual(snapshot["combo_points"], 2, "奖励元数据仍保留完整连击分")
                self.assertEqual(snapshot["answer_points"] + snapshot["combo_points"], expected)

    def test_match_miss_reduces_speed_budget_without_rejecting_final_legal_action(self):
        started = self.begin(self.match)
        token = started["play_token"]
        report = self.match_report(
            [{"ord": i, "solved": True, "wrong": 1 if i == 0 else 0} for i in range(3)],
            [{"ord": 0, "eligible": False, "break": True},
             {"ord": 0, "eligible": False, "break": True},
             {"ord": 1, "eligible": True}, {"ord": 2, "eligible": True}])
        play = dict(self.db.one("SELECT * FROM game_plays WHERE token=?", (token,)))
        sid, result, _ = scoring.finalize(self.db, play, report, now=started["started_at"] + 24)
        snapshot = json.loads(self.db.one("SELECT score_snapshot FROM game_plays WHERE token=?", (token,))["score_snapshot"])
        self.assertAlmostEqual(snapshot["speed_points"], 62 * .2 * ((60 + 1 - 3 - 24) / 60))
        self.assertEqual(result, 69)
        self.assertEqual(self.db.one("SELECT duration FROM scores WHERE id=?", (sid,))["duration"], 24)
        late = self.begin(self.match)
        late_play = dict(self.db.one("SELECT * FROM game_plays WHERE token=?", (late["play_token"],)))
        final_miss = self.match_report(
            [{"ord": 0, "solved": True, "wrong": 0},
             {"ord": 1, "solved": False, "wrong": 1}],
            [{"ord": 0, "eligible": True}, {"ord": 1, "eligible": False, "break": True}])
        scoring.checkpoint(self.db, late_play, final_miss, now=late["started_at"] + 58)
        sid, result, _ = scoring.finalize(self.db, late_play, final_miss, now=late["started_at"] + 58)
        self.assertEqual(result, 16, "最后一次合法错答扣分，但不因扣时倒退拒收")
        self.assertEqual(self.db.one("SELECT duration FROM scores WHERE id=?", (sid,))["duration"], 58)

    def test_spell_80_hint24_wrong16_floor8_and_verb_fifth_try_zero(self):
        spell = self.begin(self.spell, ords=list(range(8)))
        self.assertEqual(spell["time_limit"], 160)
        spell_report = {"detail": [{"ord": 0, "solved": True, "hints": 1, "wrong": 1},
                                  {"ord": 1, "solved": True, "hints": 9, "wrong": 9}],
                        "combo_events": [{"ord": 0, "eligible": False, "break": True},
                                         {"ord": 1, "eligible": False, "break": True}]}
        self.assertEqual(self.finish_at_limit(spell, spell_report)[1], 48,
                         "第 0 题 40 分，第 1 题保底 8 分")

        verb = self.begin(self.verb, ords=list(range(5)))
        verb_report = {"detail": [{"ord": 0, "solved": True, "wrong": 3},
                                  {"ord": 1, "solved": True, "wrong": 4}],
                       "combo_events": [{"ord": 0, "eligible": False, "break": True},
                                        {"ord": 1, "eligible": False, "break": True}]}
        self.assertEqual(self.finish_at_limit(verb, verb_report)[1], 4)

    def test_combo_hit_fractions_and_extra_time(self):
        started = self.begin(self.spell, ords=list(range(8)))
        report = {"detail": [{"ord": i, "solved": True, "hints": 0, "wrong": 0} for i in range(8)],
                  "combo_events": [{"ord": i, "eligible": True} for i in range(8)]}
        sid, score, _ = self.finish_at_limit(started, report)
        expected_combo = 80 * sum((0.1, 0.2, 0.4, 0.6, 0.8, 1, 1))
        raw = 640 + expected_combo
        expected_speed = raw * 0.2 * (10 / started["time_limit"])
        self.assertEqual(score, int(raw + expected_speed + 0.5))
        row = self.db.one("SELECT best_combo,score FROM scores WHERE id=?", (sid,))
        self.assertEqual(row["best_combo"], 8)

    def test_attempt_factors_thresholds_and_zero_score_does_not_advance(self):
        blank = self.begin(self.match)
        self.assertEqual(blank["attempt"], 1)
        report = self.match_report([], [])
        self.assertEqual(self.finish_at_limit(blank, report)[1], 0)
        self.assertEqual(self.begin(self.match)["attempt"], 1)

        factors = {1: (1.0, 1.0), 5: (1.0, 1.0), 6: (0.75, 0.8), 10: (0.75, 0.8),
                   11: (0.5, 0.6), 15: (0.5, 0.6), 16: (0.2, 0.4), 20: (0.2, 0.4)}
        for attempt in range(1, 21):
            started = self.begin(self.match)
            self.assertEqual(started["attempt"], attempt)
            if attempt in factors:
                self.assertEqual((started["score_factor"], started["time_factor"]), factors[attempt])
            report = self.match_report([{"ord": 0, "solved": True, "wrong": 0}],
                                       [{"ord": 0, "eligible": True}])
            self.finish_at_limit(started, report)

    def test_order_upload_and_late_accuracy_are_scored_once_with_original_decay(self):
        started = self.begin(self.order, ords=[0])
        play = scoring.get_owned_play(self.db, started["play_token"], user_id=self.student_user["id"],
                                      device="u%d" % self.student_user["id"], mode="online")
        self.db.execute("UPDATE game_plays SET score_factor=.75,phase='scoring' WHERE token=?",
                        (started["play_token"],))
        rec_id = self.db.execute(
            "INSERT INTO recordings(user_id,bank_id,item_ord,play_token,duration_ms,status,valid,created_at) "
            "VALUES(?,?,0,?,1000,'pending',1,1)",
            (self.student_user["id"], self.order, started["play_token"])).lastrowid
        report = {"detail": [{"ord": 0, "wrong": 1, "arranged": True, "recording_id": rec_id}],
                  "combo_events": [{"ord": 0, "eligible": False, "break": True}]}
        sid, initial, _ = scoring.finalize(self.db, play, report, now=started["started_at"] + started["time_limit"])
        self.assertEqual(initial, 33, "arrangement 24 + upload 20 = 44, then 0.75")
        self.db.execute("UPDATE recordings SET status='done',accuracy=.5 WHERE id=?", (rec_id,))
        recordings.rescore(self.db, sid)
        after = self.db.one("SELECT score FROM scores WHERE id=?", (sid,))["score"]
        self.assertEqual(after, 47, "accuracy 18 × .75 is rounded only after the combined total")
        self.assertEqual(self.db.one("SELECT score_id FROM recordings WHERE id=?", (rec_id,))["score_id"], sid)
        self.assertEqual(self.db.one("SELECT final_score FROM game_plays WHERE token=?",
                                    (started["play_token"],))["final_score"], after)
        retry_id, retry_score, duplicate = scoring.finalize(self.db, play, report)
        self.assertEqual((retry_id, retry_score, duplicate), (sid, after, True))

    def test_order_speed_excludes_recording_and_accuracy_before_single_rounding(self):
        started = self.begin(self.order, ords=[0])
        token = started["play_token"]
        self.db.execute("UPDATE game_plays SET score_factor=.75,phase='scoring' WHERE token=?", (token,))
        play = dict(self.db.one("SELECT * FROM game_plays WHERE token=?", (token,)))
        rec_id = self.db.execute(
            "INSERT INTO recordings(user_id,bank_id,item_ord,play_token,duration_ms,status,valid,accuracy,created_at) "
            "VALUES(?,?,0,?,1000,'done',1,.5,1)",
            (self.student_user["id"], self.order, token)).lastrowid
        report = {"detail": [{"ord": 0, "wrong": 1, "arranged": True, "recording_id": rec_id}],
                  "combo_events": [{"ord": 0, "eligible": False, "break": True}]}
        sid, result, _ = scoring.finalize(self.db, play, report, now=started["started_at"] + 15)
        snapshot = json.loads(self.db.one("SELECT score_snapshot FROM game_plays WHERE token=?", (token,))["score_snapshot"])
        self.assertAlmostEqual(snapshot["speed_points"], 2.4)
        self.assertEqual(result, 48, "仅排列分 24 获得速度奖 2.4；(24+2.4+20+18)*.75 最后取整")
        self.assertEqual(self.db.one("SELECT score FROM scores WHERE id=?", (sid,))["score"], 48)

    def test_combo_seed_is_adjacent_and_one_use(self):
        first = self.begin(self.order, ords=[0])
        p1 = scoring.get_owned_play(self.db, first["play_token"], user_id=self.student_user["id"],
                                    device="u%d" % self.student_user["id"], mode="online")
        self.db.execute("UPDATE game_plays SET phase='scoring' WHERE token=?", (first["play_token"],))
        scoring.finalize(self.db, p1, {"detail": [{"ord": 0, "arranged": True, "wrong": 0}],
                                      "combo_events": [{"ord": 0, "eligible": True}]},
                         now=first["started_at"] + first["time_limit"])
        second = self.begin(self.order, ords=[1], previous=first["play_token"])
        self.assertEqual(second["combo_seed"], 1)
        with self.assertRaises(scoring.PlayError) as err:
            self.begin(self.order, ords=[1], previous=first["play_token"])
        self.assertEqual(err.exception.code, "invalid_combo_seed")

    def test_order_recording_phase_pauses_arrangement_clock_for_at_most_120_seconds(self):
        started = self.begin(self.order, ords=[0])
        play = scoring.get_owned_play(self.db, started["play_token"], user_id=self.student_user["id"],
                                      device="u%d" % self.student_user["id"], mode="online")
        recording_start = started["started_at"] + 29
        scoring.phase(self.db, play, "recording", now=recording_start)
        play = scoring.get_owned_play(self.db, started["play_token"], user_id=self.student_user["id"],
                                      device="u%d" % self.student_user["id"], mode="online")
        scoring.check_upload(play, 0, now=recording_start + 120)
        with self.assertRaises(scoring.PlayError) as err:
            scoring.check_upload(play, 0, now=recording_start + 121)
        self.assertEqual(err.exception.code, "recording_expired")
        scoring.accept_upload(self.db, play, 0, now=recording_start + 120)
        play = scoring.get_owned_play(self.db, started["play_token"], user_id=self.student_user["id"],
                                      device="u%d" % self.student_user["id"], mode="online")
        scoring.phase(self.db, play, "scoring", now=recording_start + 120)
        updated = scoring.get_owned_play(self.db, started["play_token"], user_id=self.student_user["id"],
                                         device="u%d" % self.student_user["id"], mode="online")
        self.assertEqual(updated["paused_seconds"], 120)
        self.assertEqual(scoring._elapsed(updated, recording_start + 120), 29)
        self.assertEqual(scoring._elapsed(updated, recording_start + 900), 29)

    def test_order_checkpoint_freezes_time_through_recording_and_optional_skip(self):
        started = self.begin(self.order, ords=[0])
        token = started["play_token"]
        report = {"detail": [{"ord": 0, "arranged": True, "wrong": 0}],
                  "combo_events": [{"ord": 0, "eligible": True}]}
        play = dict(self.db.one("SELECT * FROM game_plays WHERE token=?", (token,)))
        scoring.checkpoint(self.db, play, report, now=started["started_at"] + 15)
        play = dict(self.db.one("SELECT * FROM game_plays WHERE token=?", (token,)))
        scoring.phase(self.db, play, "recording", now=started["started_at"] + 16)
        play = dict(self.db.one("SELECT * FROM game_plays WHERE token=?", (token,)))
        scoring.phase(self.db, play, "scoring", now=started["started_at"] + 25)
        play = dict(self.db.one("SELECT * FROM game_plays WHERE token=?", (token,)))
        self.assertEqual(scoring._elapsed(play, started["started_at"] + 900), 15)
        sid, result, _ = scoring.finalize(self.db, play, report, now=started["started_at"] + 900)
        self.assertEqual(result, 33, "跳过录音仍有排列速度奖：30+30*.2*.5")
        self.assertEqual(self.db.one("SELECT duration FROM scores WHERE id=?", (sid,))["duration"], 15)

    def test_order_checkpoint_roundtrip_preserves_arrangement_for_optional_recording(self):
        started = self.begin(self.order, ords=[0])
        token = started["play_token"]
        report = {"detail": [{"ord": 0, "arranged": True, "wrong": 0}],
                  "combo_events": [{"ord": 0, "eligible": True}]}
        play = dict(self.db.one("SELECT * FROM game_plays WHERE token=?", (token,)))
        scoring.checkpoint(self.db, play, report, now=started["started_at"])
        play = dict(self.db.one("SELECT * FROM game_plays WHERE token=?", (token,)))
        stored = {"detail": json.loads(play["detail"]), "combo_events": json.loads(play["combo_events"])}
        sanitized, events, details = scoring.validate_report(self.db, play, stored)
        self.assertTrue(sanitized[0]["arranged"])
        self.assertEqual((details["matched"], details["answer_points"]), (1, 30))
        self.assertEqual(events, report["combo_events"])
        scoring.phase(self.db, play, "recording", now=started["started_at"] + 1)
        play = dict(self.db.one("SELECT * FROM game_plays WHERE token=?", (token,)))
        scoring.phase(self.db, play, "scoring", now=started["started_at"] + 2)
        play = dict(self.db.one("SELECT * FROM game_plays WHERE token=?", (token,)))
        sid, result, duplicate = scoring.finalize(self.db, play, stored, now=started["started_at"] + 900)
        self.assertEqual((result, duplicate), (36, False))
        self.assertEqual(self.db.one("SELECT matched FROM scores WHERE id=?", (sid,))["matched"], 1)

    def test_progress_snapshot_blocks_answers_arriving_after_timeout(self):
        started = self.begin(self.match)
        play = scoring.get_owned_play(self.db, started["play_token"], user_id=self.student_user["id"],
                                      device="u%d" % self.student_user["id"], mode="online")
        checkpoint = self.match_report([{"ord": 0, "solved": True, "wrong": 0}],
                                       [{"ord": 0, "eligible": True}])
        scoring.checkpoint(self.db, play, checkpoint, now=started["started_at"] + started["time_limit"] - 1)
        malicious_late = self.match_report(
            [{"ord": i, "solved": True, "wrong": 0} for i in range(3)],
            [{"ord": i, "eligible": True} for i in range(3)])
        sid, score, _ = scoring.finalize(
            self.db, play, malicious_late, now=started["started_at"] + started["time_limit"] + 2)
        self.assertEqual(score, 20)
        self.assertEqual(self.db.one("SELECT matched FROM scores WHERE id=?", (sid,))["matched"], 1)
        self.assertEqual(self.db.one("SELECT duration FROM scores WHERE id=?", (sid,))["duration"],
                         started["time_limit"])

    def test_completion_checkpoint_during_bonus_time_keeps_earned_score(self):
        started = self.begin(self.match)
        token = started["play_token"]
        report = self.match_report(
            [{"ord": i, "solved": True, "wrong": 0} for i in range(3)],
            [{"ord": i, "eligible": True} for i in range(3)])
        play = dict(self.db.one("SELECT * FROM game_plays WHERE token=?", (token,)))
        scoring.checkpoint(self.db, play, report, now=started["started_at"] + 60.5)
        play = dict(self.db.one("SELECT * FROM game_plays WHERE token=?", (token,)))
        sid, result, _ = scoring.finalize(self.db, play, report, now=started["started_at"] + 65)
        self.assertEqual(result, 66)
        self.assertEqual(self.db.one("SELECT matched FROM scores WHERE id=?", (sid,))["matched"], 3)


class TestHistoryRecalculation(unittest.TestCase):
    def _database(self, path: Path):
        from server.db import Database
        return Database(path)

    def test_preview_is_read_only_and_apply_backups_once_preserving_snapshots(self):
        td = ROOT / "tests" / ".score-recalc-test"
        shutil.rmtree(td, ignore_errors=True)
        td.mkdir()
        try:
            path = td / "scores.db"
            db = self._database(path)
            sid = db.insert_score({"bank_id": 1, "score": 25, "matched": 1, "total_pairs": 1,
                                   "game_type": "match", "detail": []}, user_id=7)
            order_id = db.insert_score({
                "bank_id": 2, "score": 999, "game_type": "order", "duration": 1795000000,
                "detail": [{"ord": 0, "arranged": True, "wrong": 1}],
            }, user_id=7)
            new_id = db.insert_score({"bank_id": 1, "score": 200, "game_type": "match",
                                      "rule_version": 4, "detail": [{"score": 200}]}, user_id=7)
            from server import awards
            awards.ensure(db)
            db.execute("INSERT INTO board_leaders(day,board,game,user_id,points) VALUES('2025-01-01','overall','all',7,999)")
            db.execute("INSERT INTO award_days(day,done_at) VALUES('2025-01-01',1)")
            db.execute("INSERT INTO awards(user_id,game,days,board,board_label,start_day,end_day,created_at) "
                       "VALUES(7,'all',10,'overall','总榜','2024-12-01','2025-01-01',1)")
            issued_awards = [dict(row) for row in db.query("SELECT * FROM awards")]
            db.close()
            with open_readonly(path) as conn:
                preview = build_plan(conn)
                self.assertEqual(preview["changes"][0]["new_score"], 10)
                self.assertEqual(preview["changes"][1]["new_score"], 24)
                self.assertEqual(preview["invalid_duration_rows"], [{"id": order_id, "duration": 1795000000}])
                self.assertNotIn(new_id, [item["id"] for item in preview["changes"]])
                self.assertNotIn(new_id, preview["duplicate_prefix_rows"])
                self.assertNotIn(new_id, preview["ambiguous_duplicate_rows"])
            conn = sqlite3.connect(path)
            self.assertEqual(conn.execute("SELECT score FROM scores WHERE id=?", (sid,)).fetchone()[0], 25)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM board_leaders").fetchone()[0], 1)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM award_days").fetchone()[0], 1)
            conn.close()
            backup = td / "backup.db"
            result = apply_plan(path, backup)
            self.assertTrue(backup.exists())
            self.assertEqual(result["changes"][0]["new_score"], 10)
            self.assertEqual(result["changes"][1]["new_score"], 24)
            self.assertEqual(result["invalidated_award_cache_rows"], {"board_leaders": 1, "award_days": 1})
            conn = sqlite3.connect(path)
            conn.row_factory = sqlite3.Row
            self.assertEqual(conn.execute("SELECT score FROM scores WHERE id=?", (sid,)).fetchone()[0], 10)
            self.assertEqual(conn.execute("SELECT score FROM scores WHERE id=?", (new_id,)).fetchone()[0], 200)
            self.assertEqual(conn.execute("SELECT original_score FROM score_recalc_v4_snapshots WHERE score_id=?",
                                          (sid,)).fetchone()[0], 25)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM board_leaders").fetchone()[0], 0)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM award_days").fetchone()[0], 0)
            self.assertEqual([dict(row) for row in conn.execute("SELECT * FROM awards")], issued_awards)
            conn.close()
            with sqlite3.connect(backup) as original:
                self.assertEqual(original.execute("SELECT COUNT(*) FROM board_leaders").fetchone()[0], 1)
                self.assertEqual(original.execute("SELECT COUNT(*) FROM award_days").fetchone()[0], 1)
                self.assertEqual(original.execute("SELECT COUNT(*) FROM awards").fetchone()[0], 1)
            with self.assertRaises(ValueError):
                apply_plan(path, td / "backup-again.db")
        finally:
            shutil.rmtree(td, ignore_errors=True)

    def test_only_exact_cumulative_prefix_with_matching_session_start_is_deducted(self):
        test_dir = ROOT / "tests" / ".score-prefix-test"
        shutil.rmtree(test_dir, ignore_errors=True)
        test_dir.mkdir()
        try:
            path = test_dir / "scores.db"
            db = self._database(path)
            first = db.insert_score({"bank_id": 1, "score": 10, "game_type": "match", "duration": 30,
                                     "detail": [{"score": 10}]}, user_id=7)
            later = db.insert_score({"bank_id": 1, "score": 30, "game_type": "match", "duration": 60,
                                     "detail": [{"score": 10}, {"score": 20}]}, user_id=7)
            ambiguous = db.insert_score({"bank_id": 1, "score": 40, "game_type": "match", "duration": 60,
                                         "detail": [{"score": 10}, {"score": 30}, {"score": 0}]}, user_id=7)
            db.execute("UPDATE scores SET created_at='2025-01-01 00:00:30' WHERE id=?", (first,))
            db.execute("UPDATE scores SET created_at='2025-01-01 00:01:00' WHERE id=?", (later,))
            db.execute("UPDATE scores SET created_at='2025-01-01 00:03:00' WHERE id=?", (ambiguous,))
            db.close()
            with open_readonly(path) as conn:
                plan = build_plan(conn)
            changes = {row["id"]: row for row in plan["changes"]}
            self.assertEqual(changes[first]["new_score"], 4)
            self.assertEqual(changes[later]["duplicate_prefix_deduction"], 10)
            self.assertEqual(changes[later]["new_score"], 8)
            self.assertEqual(changes[ambiguous]["duplicate_prefix_deduction"], 0)
            self.assertIn(ambiguous, plan["ambiguous_duplicate_rows"])
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)
