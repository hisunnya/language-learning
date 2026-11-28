"""新题型：单词大比拼（spell）和排排坐（order）。资料解析、导入、接口、录音、识别评分、服务器算分、权限。"""
from __future__ import annotations

import contextlib
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, ROOT.as_posix())

from server import asr, items, recordings as rec_mod          # noqa: E402
from server.db import Database                                # noqa: E402
from tests.test_auth import Client, HttpCase, multipart       # noqa: E402

NODE = shutil.which("node") or shutil.which("nodejs")
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def docx(paragraphs) -> bytes:
    """paragraphs：每段一个 [(文字, 高亮)] 列表（或直接一个字符串）。"""
    body = []
    for p in paragraphs:
        runs = [(p, "")] if isinstance(p, str) else p
        xml = "".join('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (
            '<w:rPr><w:highlight w:val="%s"/></w:rPr>' % hl if hl else "", t.replace("&", "&amp;").replace("<", "&lt;")) for t, hl in runs)
        body.append("<w:p>%s</w:p>" % xml)
    doc = '<?xml version="1.0"?><w:document xmlns:w="%s"><w:body>%s</w:body></w:document>' % (W, "".join(body))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", doc)
    return buf.getvalue()


SPELL_DOC = docx([[("Unit3-单词大比“拼”", "yellow")], "（domestic）economy 国内经济", "( nutritious)   food  营养丰富的",
                  "(lift)…out of… 使…摆脱，免受…", "Incredibly (humble) 十分谦虚", "yields( soar) 产量飞速上涨"])
ORDER_DOC = docx([
    "Unit3-翻译练习---“排排坐”",
    "1. 为了改善你的身体状况，你应该每天坚持运动。",
    "To improve", " your physical well-being, ", [("you should ", ""), ("keep on", "yellow"), (" ", "")], " exercising ", "every single day.",
    [("To improve your physical well-being, you should keep ", "green"), ("on  exercising", "green"), (" every single day.", "green")],
    "",
    "2. 杭州被称为“人间天堂”，是热门的旅游胜地。",
    "Hangzhou,", [(" ", ""), ("known as", "yellow"), (" “Paradise on Earth”,", "")], " is ", "a popular tourist attraction.",
    [("Hangzhou, known as “Paradise on Earth”, is a popular tourist attraction.", "green")],
])
VERB_FILE = ROOT / "seed-data" / "Unit3 - verb hunter.docx"


class TestParsing(unittest.TestCase):
    def test_spell_lines_become_phrase_gaps(self):
        found, problems, title = items.parse("spell", SPELL_DOC)
        self.assertEqual(problems, [])
        self.assertEqual(title, "Unit3-单词大比“拼”")
        self.assertEqual([(i["before"], i["answer"], i["after"], i["cn"]) for i in found], [
            ("", "domestic", "economy", "国内经济"), ("", "nutritious", "food", "营养丰富的"),
            ("", "lift", "…out of…", "使…摆脱，免受…"), ("Incredibly", "humble", "", "十分谦虚"), ("yields", "soar", "", "产量飞速上涨")])
        self.assertEqual(found[1]["text"], "nutritious food")

    def test_spell_problems_are_reported(self):
        _, problems, _ = items.parse("spell", docx(["(word) 没有问题", "(missing 中文缺括号", "(abc) no chinese here", "(中文) 括号里是中文"]))
        self.assertEqual(len(problems), 3, problems)

    def test_order_keeps_key_phrases_inside_fragments_and_checks_the_answer(self):
        found, problems, title = items.parse("order", ORDER_DOC)
        self.assertEqual(problems, [])
        self.assertEqual(title, "Unit3-翻译练习---“排排坐”")
        first = found[0]
        self.assertEqual(first["cn"], "为了改善你的身体状况，你应该每天坚持运动。")
        self.assertEqual([items.fragment_text(f) for f in first["fragments"]],
                         ["To improve", "your physical well-being,", "you should keep on", "exercising", "every single day."])
        self.assertEqual(first["fragments"][2]["segs"], [["you should ", 0], ["keep on", 1]])
        self.assertEqual(first["answer"], "To improve your physical well-being, you should keep on exercising every single day.")
        self.assertEqual(found[1]["fragments"][1]["segs"], [["known as", 1], [" “Paradise on Earth”,", 0]])

    def test_order_mismatch_between_fragments_and_answer_is_refused(self):
        bad = docx(["1. 中文", "Hello", "world.", [("Hello there world.", "green")]])
        found, problems, _ = items.parse("order", bad)
        self.assertEqual(found, [])
        self.assertIn("不一样", problems[0])

    def test_verb_hunter_source_has_ten_questions_and_two_five_question_levels(self):
        found, problems, _ = items.parse("verb", VERB_FILE.read_bytes())
        self.assertEqual(problems, [])
        self.assertEqual(len(found), 10)
        self.assertEqual(len(items.levels("verb", found)), 2)
        self.assertEqual([len(g["items"]) for g in items.levels("verb", found)], [5, 5])
        choices = found[0]["choices"]
        self.assertEqual(len(choices), 14)
        self.assertEqual(len({items.answer_key(word) for word in choices}), 14)
        self.assertTrue(all(item["choices"] == choices for item in found))
        self.assertTrue(all(items.answer_key(item["answer"]) in {items.answer_key(w) for w in choices} for item in found))

    def test_soft_line_breaks_split_fragments_and_punctuation_may_start_a_fragment(self):
        """Shift+Enter（<w:br/>）在 Word 里看起来是另起一行，就当一个新片段；片段以逗号开头时，拼起来和答案比较不受空格影响。"""
        para = ('<w:p><w:r><w:t>The city</w:t><w:br/><w:t>, famous for its tea</w:t><w:tab/><w:t>,</w:t></w:r></w:p>')
        doc = ('<?xml version="1.0"?><w:document xmlns:w="%s"><w:body><w:p><w:r><w:t>1. 这座城市以茶闻名。</w:t></w:r></w:p>%s'
               '<w:p><w:r><w:t>is lovely.</w:t></w:r></w:p>'
               '<w:p><w:r><w:rPr><w:highlight w:val="green"/></w:rPr><w:t>The city, famous for its tea , is lovely.</w:t></w:r></w:p>'
               '</w:body></w:document>') % (W, para)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("word/document.xml", doc)
        found, problems, _ = items.parse("order", buf.getvalue())
        self.assertEqual(problems, [])
        self.assertEqual([items.fragment_text(f) for f in found[0]["fragments"]], ["The city", ", famous for its tea ,", "is lovely."])

    def test_not_a_docx(self):
        with self.assertRaises(items.ItemError):
            items.parse("spell", b"hello")

    def test_levels(self):
        self.assertEqual(len(items.levels("order", [{}] * 13, "Unit 3")), 3)
        self.assertEqual(items.levels("spell", [{}] * 12, "Unit 3")[0]["unit"], "Unit 3")
        parts = items.levels("order", [{}] * 13, "Unit 3")
        self.assertEqual([(g["unit"], g["part"], g["parts"]) for g in parts], [("Unit 3", 1, 3), ("Unit 3", 2, 3), ("Unit 3", 3, 3)],
                         "关名由页面按语言拼，服务器不写中文括号")


class TestAccuracy(unittest.TestCase):
    REF = "Hangzhou, known as “Paradise on Earth”, is a popular tourist attraction."

    def test_matching_words_in_order(self):
        self.assertEqual(asr.accuracy(self.REF, "Hangzhou known as paradise on earth is a popular tourist attraction"), 1.0)
        self.assertAlmostEqual(asr.accuracy(self.REF, "Hangzhou known as paradise is a popular attraction"), 0.727, places=3)
        self.assertEqual(asr.accuracy(self.REF, ""), 0.0)
        self.assertEqual(asr.accuracy("I have 3 cats.", "I have three cats"), 1.0, "单个数字和英文写法算同一个词")

    def test_bonus(self):
        self.assertEqual([rec_mod.bonus_for(x) for x in (0, 0.5, 0.727, 1, 1.4)], [0, 10, 15, 20, 20])
        self.assertEqual([rec_mod.arrange_points(w) for w in (0, 1, 4, 10)], [10, 8, 2, 2])


class TestImportTool(unittest.TestCase):
    def test_dry_run_and_import_with_copied_tags(self):
        sys.path.insert(0, (ROOT / "tools").as_posix())
        import import_items
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "spell.docx"
            src.write_bytes(SPELL_DOC)
            db_path = str(Path(tmp) / "a.db")
            db = Database(db_path)
            db.execute("INSERT INTO users(student_no, name, role, pw_hash, created_at) VALUES ('T9','孙老师','admin','x','0')")
            tid = db.one("SELECT id FROM users WHERE student_no='T9'")["id"]
            old = db.insert_bank({"title": "Unit 1", "level1": "大学", "level2": "", "level3": "", "level4": "", "source": "seed"}, [])
            db.execute("INSERT INTO bank_tags(bank_id, tag, teacher_id) VALUES (?, '一班', ?)", (old, tid))
            db.close()
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(import_items.main(["--type", "spell", "--file", str(src), "--dry-run"]), 0)
                self.assertEqual(import_items.main(["--type", "spell", "--file", str(src), "--db", db_path, "--title", "U3 拼",
                                                    "--owner", "T9", "--copy-tags-from", str(old), "--category", "新视野"]), 0)
            db = Database(db_path)
            bank = db.one("SELECT * FROM banks WHERE title='U3 拼'")
            self.assertEqual((bank["game_type"], bank["word_count"], bank["owner_id"], bank["category"]), ("spell", 5, tid, "新视野"))
            self.assertEqual(db.bank_tags(bank["id"]), ["一班"])
            self.assertEqual(len(db.bank_items(bank["id"])), 5)
            self.assertEqual(db.one("SELECT action FROM audit_log ORDER BY id DESC")["action"], "bank.import")
            db.close()

    def test_problems_stop_the_import(self):
        sys.path.insert(0, (ROOT / "tools").as_posix())
        import import_items
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "bad.docx"
            src.write_bytes(docx(["1. 中文", "Hello", "world.", [("Hello there world.", "green")]]))
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(import_items.main(["--type", "order", "--file", str(src), "--db", str(Path(tmp) / "a.db")]), 1)

    def test_category_from_copies_only_category_for_verb_bank(self):
        sys.path.insert(0, (ROOT / "tools").as_posix())
        import import_items
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "a.db")
            db = Database(db_path)
            db.execute("INSERT INTO users(student_no, name, role, pw_hash, created_at) VALUES ('T9','孙老师','admin','x','0')")
            tid = db.one("SELECT id FROM users WHERE student_no='T9'")["id"]
            source = db.insert_bank({"title": "Spell source", "level1": "大学", "level2": "", "level3": "", "level4": "",
                                     "source": "seed"}, [])
            db.set_bank_meta(source, "同一本书", ["原有班级"], teacher_id=tid)
            db.close()
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(import_items.main(["--type", "verb", "--file", str(VERB_FILE), "--db", db_path,
                                                    "--title", "U3 Verb", "--category-from", str(source)]), 0)
            db = Database(db_path)
            imported = db.one("SELECT * FROM banks WHERE title='U3 Verb'")
            self.assertEqual((imported["game_type"], imported["category"]), ("verb", "同一本书"))
            self.assertEqual(db.bank_tags(imported["id"]), [], "标签不从分类来源复制")
            db.close()


class ItemsCase(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user, _ = cls.svc.create_user("T001", "孙老师", password="Teach3r!pw", role="admin", must_change=False)
        db = cls.db = cls.app.Handler.db
        cls.spell = db.insert_item_bank({"title": "U3 拼", "level1": "大学", "level2": "大一", "level3": "上册", "level4": "Unit 3",
                                         "source": "import", "game_type": "spell", "owner_id": cls.admin_user["id"]},
                                        items.parse("spell", SPELL_DOC)[0])
        cls.order = db.insert_item_bank({"title": "U3 排", "level1": "大学", "level2": "大一", "level3": "上册", "level4": "Unit 3",
                                         "source": "import", "game_type": "order", "owner_id": cls.admin_user["id"]},
                                        items.parse("order", ORDER_DOC)[0])
        cls.verb = db.insert_item_bank({"title": "U3 动词", "level1": "大学", "level2": "大一", "level3": "上册", "level4": "Unit 3",
                                        "source": "import", "game_type": "verb", "owner_id": cls.admin_user["id"]},
                                       items.parse("verb", VERB_FILE.read_bytes())[0])
        for bid in (cls.spell, cls.order, cls.verb):
            db.execute("INSERT INTO bank_tags(bank_id, tag, teacher_id) VALUES (?, '一班', ?)", (bid, cls.admin_user["id"]))
        cls.rec_dir = tempfile.TemporaryDirectory()
        cls.env = mock.patch.dict("os.environ", {"WP_RECORDINGS_DIR": cls.rec_dir.name})
        cls.env.start()

    @classmethod
    def tearDownClass(cls):
        cls.env.stop()
        cls.rec_dir.cleanup()
        super().tearDownClass()

    counter = 0

    def student(self, tag="一班"):
        type(self).counter += 1
        no = "S%03d" % type(self).counter
        user, _ = self.svc.create_user(no, "学生%d" % self.counter, password="Ready2026x", must_change=False, class_name="一班")
        self.db.execute("INSERT INTO user_tags(user_id, tag, teacher_id) VALUES (?,?,?)", (user["id"], tag, self.admin_user["id"]))
        self.db.execute("INSERT OR IGNORE INTO teacher_students(teacher_id, student_id, added_at) VALUES (?,?,0)", (self.admin_user["id"], user["id"]))
        c = Client(self.port)
        self.assertEqual(c.json("POST", "/api/auth/login", {"student_no": no, "password": "Ready2026x"})[0], 200)
        return user, c

    def admin(self):
        c = Client(self.port)
        c.json("POST", "/api/auth/login", {"student_no": "T001", "password": "Teach3r!pw"})
        return c

    def upload(self, c, ordinal=0, data=b"\x1aE\xdf\xa3" + b"0" * 4000, ms=4200, token="ptest1"):
        body, headers = multipart({"bank_id": str(self.order), "item_ord": str(ordinal), "play_token": token, "duration_ms": str(ms)},
                                  {"file": ("reading.webm", data)})
        return c.json("POST", "/api/recordings", raw=body, headers=headers)


class TestItemBanksOverHttp(ItemsCase):
    def test_banks_carry_their_type_and_items_come_in_levels(self):
        _, c = self.student()
        banks = {b["id"]: b for b in c.json("GET", "/api/banks")[1]["banks"]}
        self.assertEqual((banks[self.spell]["game_type"], banks[self.order]["game_type"], banks[self.verb]["game_type"]),
                         ("spell", "order", "verb"))
        body = c.json("GET", "/api/banks/%d" % self.order)[1]
        self.assertEqual(body["bank"]["game_type"], "order")
        self.assertEqual(len(body["groups"]), 1)
        self.assertEqual(body["groups"][0]["items"][1]["answer"], "Hangzhou, known as “Paradise on Earth”, is a popular tourist attraction.")
        verb = c.json("GET", "/api/banks/%d" % self.verb)[1]
        self.assertEqual([len(g["items"]) for g in verb["groups"]], [5, 5])
        self.assertEqual(len(verb["groups"][0]["items"][0]["choices"]), 14)

    def test_item_audio_reads_the_text_of_the_bank_only(self):
        _, c = self.student()
        with mock.patch("server.tts.synth", return_value=b"ID3audio") as synth:
            self.assertEqual(c.request("GET", "/api/banks/%d/items/1/audio" % self.order)[0], 200)
            self.assertEqual(c.request("GET", "/api/banks/%d/items/0/audio" % self.spell)[0], 200)
            self.assertEqual(c.request("GET", "/api/banks/%d/items/0/audio" % self.verb)[0], 200)
            self.assertEqual(c.request("GET", "/api/banks/%d/items/9/audio" % self.order)[0], 404)
        self.assertEqual(synth.call_args_list[0].args[0], "Hangzhou, known as “Paradise on Earth”, is a popular tourist attraction.")
        self.assertEqual(synth.call_args_list[1].args[0], "domestic economy")
        self.assertEqual(synth.call_args_list[2].args[0], items.speech_text("verb", self.db.bank_items(self.verb)[0]))
        _, other = self.student(tag="二班")
        self.assertEqual(other.request("GET", "/api/banks/%d/items/0/audio" % self.order)[0], 404, "没开放给他的题库听不到")

    def test_spell_score_takes_its_type_from_the_bank(self):
        user, c = self.student()
        status, body = c.json("POST", "/api/scores", {"bank_id": self.spell, "game_type": "match", "score": 41, "matched": 4,
                                                     "total_pairs": 5, "level_count": 1, "detail": []})
        self.assertEqual(status, 201, body)
        self.assertEqual(self.db.one("SELECT game_type, score FROM scores WHERE id=?", (body["id"],))["game_type"], "spell")

    def test_verb_score_takes_its_type_from_the_bank(self):
        _, c = self.student()
        status, body = c.json("POST", "/api/scores", {"bank_id": self.verb, "game_type": "match", "score": 17,
                                                     "matched": 5, "total_pairs": 5, "level_count": 1, "detail": []})
        self.assertEqual(status, 201, body)
        self.assertEqual(self.db.one("SELECT game_type FROM scores WHERE id=?", (body["id"],))["game_type"], "verb")


class TestRecordings(ItemsCase):
    def test_without_speech_recognition_a_long_enough_recording_is_valid_without_bonus(self):
        _, c = self.student()
        with mock.patch.object(asr, "available", return_value=False), mock.patch.object(rec_mod, "ffmpeg", return_value=None), \
                mock.patch.object(rec_mod, "probe_ms", return_value=None):
            status, body = self.upload(c)
            short = self.upload(c, ms=600)[1]["recording"]
        self.assertEqual(status, 201, body)
        rec = body["recording"]
        self.assertEqual((rec["status"], rec["valid"], rec["bonus"]), ("noasr", True, 0))
        self.assertFalse(short["valid"], "不到 1 秒不算")

    def test_recognised_reading_gets_a_bonus_by_accuracy(self):
        _, c = self.student()
        with mock.patch.object(asr, "available", return_value=True), mock.patch.object(rec_mod, "ffmpeg", return_value=None), \
                mock.patch.object(rec_mod, "probe_ms", return_value=None), \
                mock.patch.object(asr, "transcribe", return_value="Hangzhou known as paradise on earth is a popular tourist attraction"):
            rec = self.upload(c, ordinal=1)[1]["recording"]
        self.assertEqual((rec["status"], rec["valid"], rec["accuracy"], rec["bonus"]), ("done", True, 1.0, 20))

    def test_silence_is_not_a_valid_reading_and_a_broken_recogniser_does_not_punish(self):
        _, c = self.student()
        with mock.patch.object(asr, "available", return_value=True), mock.patch.object(rec_mod, "ffmpeg", return_value=None), \
                mock.patch.object(rec_mod, "probe_ms", return_value=None):
            with mock.patch.object(asr, "transcribe", return_value=""):
                silent = self.upload(c)[1]["recording"]
            with mock.patch.object(asr, "transcribe", return_value=None):
                broken = self.upload(c)[1]["recording"]
        self.assertEqual((silent["status"], silent["valid"]), ("done", False))
        self.assertEqual((broken["status"], broken["valid"], broken["bonus"]), ("failed", True, 0))

    def test_upload_checks(self):
        _, c = self.student()
        body, headers = multipart({"bank_id": str(self.spell), "item_ord": "0"}, {"file": ("r.webm", b"0" * 3000)})
        self.assertEqual(c.json("POST", "/api/recordings", raw=body, headers=headers)[0], 404, "只有翻译排排坐能交录音")
        self.assertEqual(self.upload(c, ordinal=7)[0], 404)
        self.assertEqual(self.upload(c, data=b"x")[0], 400)
        self.assertEqual(Client(self.port).request("POST", "/api/recordings", raw=b"", headers={"Content-Type": "multipart/form-data; boundary=x"})[0], 401)

    def test_a_recording_longer_than_the_limit_is_refused(self):
        user, c = self.student()
        with mock.patch.object(asr, "available", return_value=False), mock.patch.object(rec_mod, "ffmpeg", return_value=None), \
                mock.patch.object(rec_mod, "probe_ms", return_value=rec_mod.MAX_MS + 5000):
            status, body = self.upload(c)
        self.assertEqual((status, body.get("code")), (400, "too_long"), body)
        self.assertIsNone(self.db.one("SELECT id FROM recordings WHERE user_id=?", (user["id"],)), "太长的录音不入库（文件也删掉）")

    def test_playback_for_the_student_and_their_teacher_only(self):
        _, c = self.student()
        with mock.patch.object(asr, "available", return_value=False), mock.patch.object(rec_mod, "ffmpeg", return_value=None):
            rid = self.upload(c)[1]["recording"]["id"]
        self.assertEqual(c.request("GET", "/api/recordings/%d/audio" % rid)[0], 200)
        self.assertEqual(self.admin().request("GET", "/api/recordings/%d/audio" % rid)[0], 200)
        _, stranger = self.student(tag="二班")
        self.db.execute("DELETE FROM teacher_students WHERE student_id=(SELECT id FROM users WHERE student_no='S%03d')" % self.counter)
        self.assertEqual(stranger.request("GET", "/api/recordings/%d/audio" % rid)[0], 404)


class TestOrderScoreIsComputedByTheServer(ItemsCase):
    def test_the_server_ignores_the_reported_score_and_counts_only_own_valid_recordings(self):
        user, c = self.student()
        _, other = self.student()
        with mock.patch.object(asr, "available", return_value=True), mock.patch.object(rec_mod, "ffmpeg", return_value=None), \
                mock.patch.object(rec_mod, "probe_ms", return_value=None), \
                mock.patch.object(asr, "transcribe", return_value="Hangzhou known as paradise is a popular attraction"):
            mine = self.upload(c, ordinal=1, token="pgame")[1]["recording"]
            theirs = self.upload(other, ordinal=0)[1]["recording"]
        detail = [{"ord": 0, "wrong": 1, "arranged": True, "recording_id": theirs["id"]},
                  {"ord": 1, "wrong": 0, "arranged": True, "recording_id": mine["id"]}]
        status, body = c.json("POST", "/api/scores", {"bank_id": self.order, "score": 9999, "matched": 2, "total_pairs": 2,
                                                     "level_count": 1, "detail": detail, "play_token": "pgame"})
        self.assertEqual(status, 201, body)
        self.assertEqual(body["score"], 8 + (10 + 30 + 15), "别人的录音不算；奖励按对上的比例（8/11 → 15）")
        self.assertEqual(self.db.one("SELECT score_id FROM recordings WHERE id=?", (mine["id"],))["score_id"], body["id"])
        plays = c.json("GET", "/api/scores/plays?user_id=%d&bank_id=%d" % (user["id"], self.order))[1]["plays"]
        self.assertEqual([r["id"] for r in plays[0]["recordings"]], [mine["id"]])

    def test_one_recording_counts_once_and_only_for_one_play(self):
        """同一条录音在 detail 里写好几遍、写到不存在的题号、或者拿到下一局再用一次，都只算一次。"""
        _, c = self.student()
        with mock.patch.object(asr, "available", return_value=False), mock.patch.object(rec_mod, "ffmpeg", return_value=None), \
                mock.patch.object(rec_mod, "probe_ms", return_value=None):
            rid = self.upload(c, ordinal=0, token="pdup")[1]["recording"]["id"]
        entry = {"ord": 0, "wrong": 0, "arranged": True, "recording_id": rid}
        detail = [entry, dict(entry), dict(entry, ord=1), dict(entry, ord=99), dict(entry, ord=-1)]
        status, first = c.json("POST", "/api/scores", {"bank_id": self.order, "score": 0, "matched": 2, "total_pairs": 2,
                                                      "level_count": 1, "detail": detail, "play_token": "pdup"})
        self.assertEqual(status, 201, first)
        self.assertEqual(first["score"], 10 + 30 + 10, "第 0 题拼接 + 录音各一次；第 1 题只有拼接分（录音不是这题的）；越界的题号不算")
        status, second = c.json("POST", "/api/scores", {"bank_id": self.order, "score": 0, "matched": 1, "total_pairs": 2,
                                                       "level_count": 1, "detail": [entry], "play_token": "pdup2"})
        self.assertEqual(second["score"], 10, "录音已经属于上一局，这一局只有拼接分")

    def test_a_bonus_that_arrives_later_is_added_to_the_score(self):
        user, c = self.student()
        with mock.patch.object(asr, "available", return_value=True), mock.patch.object(rec_mod, "ffmpeg", return_value=None), \
                mock.patch.object(rec_mod, "probe_ms", return_value=None), \
                mock.patch.object(self.app.Handler, "rec_worker", None):              # 没有队列：录音停在 pending
            rec = self.upload(c, ordinal=0)[1]["recording"]
        self.assertEqual(rec["status"], "pending")
        sid = c.json("POST", "/api/scores", {"bank_id": self.order, "detail": [{"ord": 0, "wrong": 0, "arranged": True,
                                                                                 "recording_id": rec["id"]}]})[1]["id"]
        self.assertEqual(self.db.one("SELECT score FROM scores WHERE id=?", (sid,))["score"], 10)
        with mock.patch.object(asr, "available", return_value=True), mock.patch.object(rec_mod, "ffmpeg", return_value=None), \
                mock.patch.object(asr, "transcribe", return_value="To improve your physical well-being you should keep on exercising every single day"):
            rec_mod.score_one(self.db, rec["id"])
        self.assertEqual(self.db.one("SELECT score FROM scores WHERE id=?", (sid,))["score"], 10 + 30 + 20)


@unittest.skipUnless(NODE, "本机没有 node，跳过 item-core.js 的行为测试")
class TestItemCoreJs(unittest.TestCase):
    def test_behaviour(self):
        proc = subprocess.run([NODE, str(ROOT / "tests" / "js" / "item_core.test.js")], capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("全部通过", proc.stdout)

    def test_order_ui_recording_stages(self):
        proc = subprocess.run([NODE, str(ROOT / "tests" / "js" / "order_ui.test.js")], capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("全部通过", proc.stdout)

    def test_verb_ui_drag_and_scoring(self):
        proc = subprocess.run([NODE, str(ROOT / "tests" / "js" / "verb_ui.test.js")], capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("全部通过", proc.stdout)

    def test_page_items_starts_verb_game_without_other_game_uis(self):
        proc = subprocess.run([NODE, str(ROOT / "tests" / "js" / "page_items.test.js")], capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("全部通过", proc.stdout)


class TestPages(unittest.TestCase):
    WEB = ROOT / "web"

    def test_pages_exist_and_load_what_they_need(self):
        for page, ui in (("spell.html", "spell-ui.js"), ("order.html", "order-ui.js"), ("verb.html", "verb-ui.js")):
            html = (self.WEB / page).read_text(encoding="utf-8")
            for needle in ("item-core.js", ui, "page-items.js", "items.css", "site-footer.js", 'id="portalHeaderControls"',
                           'data-game="%s"' % page[:-5]):
                self.assertIn(needle, html, page + " " + needle)

    def test_line_up_pieces_can_be_dragged_with_finger_or_mouse(self):
        ui = (self.WEB / "js" / "order-ui.js").read_text(encoding="utf-8")
        for needle in ("addEventListener('pointerdown'", "'pointermove'", "'pointercancel'", "C.placeAt(", "self.justDragged"):
            self.assertIn(needle, ui)
        css = (self.WEB / "css" / "items.css").read_text(encoding="utf-8")
        self.assertIn("touch-action: none", css, "手指拖片段时页面不跟着滚")
        for needle in (".ig-ghost", ".ig-hole"):
            self.assertIn(needle, css)

    def test_verb_prompts_stack_and_prioritize_english(self):
        css = (self.WEB / "css" / "items.css").read_text(encoding="utf-8")
        layout = re.search(r"\.verb-bilingual\s*\{([^}]*)\}", css)
        english = re.search(r"\.verb-phrase\s*\{([^}]*)\}", css)
        chinese = re.search(r"\.verb-cn\s*\{([^}]*)\}", css)
        self.assertIsNotNone(layout)
        self.assertIn("grid-template-columns: minmax(0, 1fr)", layout.group(1))
        self.assertIn("border: 1px solid var(--blue)", layout.group(1))
        self.assertNotIn(".verb-prompt", css, "中英文共用外框，不再各自分框")
        self.assertIsNotNone(english)
        self.assertIsNotNone(chinese)
        english_size = re.search(r"font-size:\s*(\d+(?:\.\d+)?)px", english.group(1))
        chinese_size = re.search(r"font-size:\s*(\d+(?:\.\d+)?)px", chinese.group(1))
        self.assertIsNotNone(english_size)
        self.assertIsNotNone(chinese_size)
        self.assertGreater(float(english_size.group(1)), float(chinese_size.group(1)))
        ui = (self.WEB / "js" / "verb-ui.js").read_text(encoding="utf-8")
        self.assertLess(ui.index('lang="en"'), ui.index('lang="zh-CN"'))

    def test_spell_input_does_not_let_the_phone_autocorrect(self):
        ui = (self.WEB / "js" / "spell-ui.js").read_text(encoding="utf-8")
        for attr in ('autocorrect="off"', 'autocapitalize="none"', 'spellcheck="false"', 'autocomplete="off"'):
            self.assertIn(attr, ui)

    def test_every_palette_has_a_key_phrase_colour(self):
        css = (self.WEB / "css" / "app.css").read_text(encoding="utf-8")
        self.assertEqual(css.count("--mark-bg:"), 5)
        self.assertEqual(css.count("--mark-ink:"), 5)
        self.assertIn("var(--mark-bg)", (self.WEB / "css" / "items.css").read_text(encoding="utf-8"))

    def test_home_picks_a_game_type_first(self):
        home = (self.WEB / "js" / "page-home.js").read_text(encoding="utf-8")
        self.assertIn("renderTypes()", home)
        self.assertIn("'#type=' + chosen", home)
        self.assertIn("if (AuthUI.info().public) return TYPES.filter", home, "登录的学生四种玩法都看得到，公开版只显示有题库的")
        self.assertIn("type_none", home, "没开放题库的玩法也能点，提示暂未开放")
        index = (self.WEB / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="typeCards"', index)
        self.assertLess(index.index('id="bankList"'), index.index('id="recentCard"'), "最近玩过放在最下面")
        self.assertNotIn("练习英语词汇，听美式发音并完成中英配对", index)
        css = (self.WEB / "css" / "items.css").read_text(encoding="utf-8")
        for needle in (".type-card.t-spell { --tc: var(--orange); }", ".type-card.t-order { --tc: var(--green); }",
                       ".type-card.t-verb { --tc: var(--red); }", ".tc-go",
                       "order: var(--after, 99);", ".type-cards > .in-types"):
            self.assertIn(needle, css)
        self.assertIn("(on ? ' <span class=\"tc-arrow\"", home, "向下的箭头只在选中的那张上出现")
        self.assertIn("box.appendChild(list)", home, "题库列表放进卡片网格，手机上紧跟在选中的卡片下面")

    def test_order_game_uses_its_formal_bilingual_name(self):
        page = (self.WEB / "order.html").read_text(encoding="utf-8")
        lexica = (self.WEB / "js" / "i18n-lexica.js").read_text(encoding="utf-8")
        for value in ("翻译排排坐", "Translation Line-Up"):
            self.assertIn(value, page)
            self.assertIn(value, lexica)

    def test_the_notice_follows_the_palette(self):
        js = (ROOT.parent / "hub" / "shared" / "site-footer.js").read_text(encoding="utf-8")
        for theme in ("indigo", "ink", "amber", "lotus", "obsidian"):
            self.assertIn("['%s', " % theme, js)
        self.assertIn("html[data-theme=", js)


if __name__ == "__main__":
    unittest.main()


class TestOfflineAndDeployment(unittest.TestCase):
    def test_offline_pages_embed_items_audio_and_the_shared_ui(self):
        from server import offline
        for game, doc, ui_name in (("spell", SPELL_DOC, "WPSpellUI"), ("order", ORDER_DOC, "WPOrderUI"),
                                   ("verb", VERB_FILE.read_bytes(), "WPVerbUI")):
            found = items.parse(game, doc)[0]
            bank = {"id": 7, "title": "U3", "level1": "大学", "level2": "大一", "level3": "上册", "level4": "Unit 3", "game_type": game}
            name, html = offline.build_items_html(bank, items.levels(game, found, "Unit 3"), audio={0: b"ID3fake", 1: b"ID3more"})
            self.assertIn({"spell": "单词大比拼", "order": "翻译排排坐", "verb": "动词猎手"}[game], name)
            for needle in (ui_name, "WPItemCore", "WPAdapter", "WPI18N", "WPTheme", "data:audio/mpeg;base64,", '"game":"%s"' % game):
                self.assertIn(needle, html, game + " " + needle)
            self.assertNotIn("/api/", html.split("var WP_DATA")[1].split("</script>")[0], "离线页的数据里不能有接口地址")
            if game == "verb":
                for needle in ("cfg.items = cfg.items.concat(level.items)", "cfg.ords = cfg.ords.concat(level.ords)",
                               "cfg.levelCount = WP_DATA.groups.length", "vh_startInfo", "WPVerbUI.start"):
                    self.assertIn(needle, html)
                self.assertNotIn("choicesByLevel", html, "离线动词猎手不应再分关发题")
        with self.assertRaises(ValueError):
            offline.build_items_html({"game_type": "match"}, [])

    def test_installer_sets_up_ffmpeg_and_offline_speech_recognition(self):
        install = (ROOT / "deploy" / "family" / "install.sh").read_text(encoding="utf-8")
        unit = (ROOT / "deploy" / "family" / "systemd" / "word-puzzle-family.service").read_text(encoding="utf-8")
        conf = (ROOT / "deploy" / "family" / "nginx" / "word-puzzle-family.conf").read_text(encoding="utf-8")
        for needle in ("ffmpeg", "faster-whisper", "WhisperModel(", "@ASR_VENV@"):
            self.assertIn(needle, install)
        for needle in ("WP_ASR_PYTHON=@ASR_VENV@/bin/python", "WP_ASR_MODELS_DIR=@ASR_MODELS@", "WP_ASR_MODEL=@ASR_MODEL@"):
            self.assertIn(needle, unit)
        self.assertIn("location = /word-puzzle/api/recordings {", conf)
        worker = (ROOT / "tools" / "asr_worker.py").read_text(encoding="utf-8")
        self.assertIn("vad_filter=True", worker, "静音时得到空字符串，不让模型编句子")
        self.assertIn("local_files_only=args.offline", worker)
        self.assertNotIn("initial_prompt", worker, "不把标准答案当提示词，否则分数不真实")

    def test_asr_is_unavailable_without_a_downloaded_model(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict("os.environ", {"WP_ASR_PYTHON": sys.executable, "WP_ASR_MODELS_DIR": tmp}):
            self.assertFalse(asr.available())
            (Path(tmp) / "models--x").mkdir()
            self.assertTrue(asr.available())


class TestMatchScoresHalved(unittest.TestCase):
    def test_old_matching_scores_are_halved_once_and_new_types_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "old.db")
            db = Database(path)
            db.execute("PRAGMA user_version = 2")            # 假装是升级前的库
            for score, kind in ((1000, "match"), (125, "match"), (0, "match"), (200, "order"), (105, "spell")):
                db.insert_score({"score": score, "game_type": kind})
            db.close()
            db = Database(path)                               # 打开时升级
            self.assertEqual([r["score"] for r in db.query("SELECT score FROM scores ORDER BY id")], [500, 63, 0, 200, 105])
            self.assertEqual(db.one("PRAGMA user_version")[0], 3)
            db.close()
            db = Database(path)                               # 再打开不会再减一次
            self.assertEqual([r["score"] for r in db.query("SELECT score FROM scores ORDER BY id")], [500, 63, 0, 200, 105])
            db.close()

    def test_new_matching_points_are_half(self):
        core = (ROOT / "web" / "js" / "game-core.js").read_text(encoding="utf-8")
        for needle in ("PAIR_SCORE = 50;", "COMBO_STEP = 10;", "MISS_SCORE = 10;", "TIME_BONUS = 5;"):
            self.assertIn(needle, core)
