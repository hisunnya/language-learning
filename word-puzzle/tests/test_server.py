"""word-puzzle 后端测试。

跑法::

    python3 -m unittest discover -s tests -v
    # 或
    python3 tests/test_server.py
"""
from __future__ import annotations

import io
import http.client
import json
import os
import sys
import tempfile
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server import bank as bank_mod          # noqa: E402
from server import hierarchy, materials, offline  # noqa: E402
from server.db import Database               # noqa: E402


class TempDB(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "test.db")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()


# ---------------------------------------------------------------- 层级

class TestFrontendMount(unittest.TestCase):
    def test_pages_declare_word_puzzle_base_path(self):
        for page in ("index.html", "bank.html", "stats.html", "play.html"):
            source = (ROOT / "web" / page).read_text(encoding="utf-8")
            self.assertIn('<meta name="wp-base" content="/word-puzzle">', source, page)

    def test_api_helper_uses_base_for_requests_and_downloads(self):
        source = (ROOT / "web" / "js" / "api.js").read_text(encoding="utf-8")
        self.assertIn("base +", source)
        self.assertIn("function download(path, filename)", source)
        self.assertIn("return res.blob()", source)

class TestHierarchy(unittest.TestCase):
    def test_levels_present(self):
        self.assertIn("初中", [o["key"] for o in hierarchy.level1_options()])
        self.assertIn("高中", [o["key"] for o in hierarchy.level1_options()])
        self.assertIn("小学", [o["key"] for o in hierarchy.level1_options()])
        self.assertIn("大学", [o["key"] for o in hierarchy.level1_options()])

    def test_term_default_is_full_year(self):
        opts = hierarchy.level3_options("初中", "九年级")
        defaults = [o for o in opts if o["default"]]
        self.assertEqual(len(defaults), 1)
        self.assertEqual(defaults[0]["key"], "整学年")

    def test_unit_modes(self):
        modes = hierarchy.level4_options("初中", "九年级", "上册")
        keys = [m["key"] for m in modes]
        self.assertEqual(keys, ["all", "per-unit", "range"])

    def test_default_selection_is_grade9_up(self):
        d = hierarchy.DEFAULT_SELECTION
        self.assertEqual(d["level1"], "初中")
        self.assertEqual(d["level2"], "九年级")
        self.assertEqual(d["level3"], "上册")

    def test_units_for_grade9_up(self):
        units = hierarchy.CURRICULUM_OBJ.units_for("初中", "九年级", "上册")
        self.assertEqual(len(units), 7)
        self.assertTrue(all(u["count"] > 0 for u in units))

    def test_full_year_has_both_volumes(self):
        units = hierarchy.CURRICULUM_OBJ.units_for("初中", "九年级", "整学年")
        self.assertEqual(len(units), 14)

    def test_curriculum_loaded(self):
        meta = hierarchy.CURRICULUM_OBJ.meta
        self.assertGreater(meta.get("word_total", 0), 3000)
        self.assertGreater(meta.get("unit_total", 0), 50)


# ---------------------------------------------------------------- 资料解析

class TestMaterials(unittest.TestCase):
    def test_json_flat(self):
        raw = json.dumps([
            {"english": "apple", "chinese": "苹果"},
            {"en": "banana", "cn": "香蕉"},
        ]).encode()
        fmt, words = materials.parse_material("x.json", raw)
        self.assertEqual(fmt, "json")
        self.assertEqual(len(words), 2)
        self.assertEqual(words[0]["en"], "apple")

    def test_json_units(self):
        raw = json.dumps({"units": [
            {"unit": "Unit 1", "words": [{"en": "a", "cn": "甲"}]},
            {"unit": "Unit 2", "words": [{"en": "b", "cn": "乙"}]},
        ]}).encode()
        _, words = materials.parse_material("x.json", raw)
        self.assertEqual([w["unit"] for w in words], ["Unit 1", "Unit 2"])

    def test_csv_with_header(self):
        raw = b"unit,english,chinese\nUnit 1,apple,\xe8\x8b\xb9\xe6\x9e\x9c\n"
        _, words = materials.parse_material("x.csv", raw)
        self.assertEqual(len(words), 1)
        self.assertEqual(words[0]["en"], "apple")
        self.assertEqual(words[0]["unit"], "Unit 1")

    def test_csv_unit_first_no_header(self):
        raw = ("Unit 1,apple,苹果\n"
               "Unit 1,banana,香蕉\n"
               "Unit 2,computer,电脑\n").encode()
        _, words = materials.parse_material("x.csv", raw)
        self.assertEqual(len(words), 3)
        self.assertEqual(words[0]["unit"], "Unit 1")
        self.assertEqual(words[0]["en"], "apple")
        self.assertEqual(words[2]["unit"], "Unit 2")
        self.assertEqual(words[2]["en"], "computer")

    def test_csv_two_columns(self):
        raw = "apple,苹果\nbanana,香蕉\n".encode()
        _, words = materials.parse_material("x.csv", raw)
        self.assertEqual(len(words), 2)
        self.assertEqual(words[1]["en"], "banana")

    def test_txt_with_unit_header(self):
        raw = "Unit 3\nhello\t你好\nworld\t世界\n".encode()
        _, words = materials.parse_material("x.txt", raw)
        self.assertEqual(len(words), 2)
        self.assertEqual(words[0]["unit"], "Unit 3")
        self.assertEqual(words[1]["cn"], "世界")

    def test_gb18030(self):
        raw = "apple\t苹果\n".encode("gb18030")
        _, words = materials.parse_material("x.txt", raw)
        self.assertEqual(words[0]["cn"], "苹果")

    def test_docx_upload(self):
        """Word 文档：段落和表格都能解析。"""
        import tempfile
        import zipfile
        W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
        body = (
            "<w:p><w:r><w:t>Unit 1</w:t></w:r></w:p>"
            "<w:p><w:r><w:t>apple\t苹果</w:t></w:r></w:p>"
            "<w:tbl><w:tr>"
            "<w:tc><w:p><w:r><w:t>banana</w:t></w:r></w:p></w:tc>"
            "<w:tc><w:p><w:r><w:t>香蕉</w:t></w:r></w:p></w:tc>"
            "</w:tr></w:tbl>"
        )
        doc = (f'<?xml version="1.0" encoding="UTF-8"?>'
               f"<w:document {W}><w:body>{body}</w:body></w:document>")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("word/document.xml", doc)
        fmt, words = materials.parse_material("x.docx", buf.getvalue())
        self.assertEqual(fmt, "docx")
        self.assertEqual(len(words), 2)
        self.assertEqual(words[0]["en"], "apple")
        self.assertEqual(words[0]["cn"], "苹果")
        self.assertEqual(words[0]["unit"], "Unit 1")
        self.assertEqual(words[1]["en"], "banana")
        self.assertEqual(words[1]["cn"], "香蕉")

    def test_legacy_doc_rejected_with_hint(self):
        """老式 .doc 要明确提示另存为 .docx。"""
        raw = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 64
        with self.assertRaises(materials.ParseError) as ctx:
            materials.parse_material("x.doc", raw)
        self.assertIn("docx", str(ctx.exception).lower())

    def test_pdf_rejects_non_pdf(self):
        with self.assertRaises(materials.ParseError):
            materials.parse_material("x.pdf", b"not a pdf at all")

    def test_empty_raises(self):
        with self.assertRaises(materials.ParseError):
            materials.parse_material("x.csv", b"")
        with self.assertRaises(materials.ParseError):
            materials.parse_material("x.txt", b"onlyonecolumn\n")

    def test_dedup(self):
        raw = json.dumps([
            {"en": "apple", "cn": "苹果"},
            {"en": "apple", "cn": "苹果"},
        ]).encode()
        _, words = materials.parse_material("x.json", raw)
        self.assertEqual(len(words), 1)


# ---------------------------------------------------------------- 题库

class TestBank(TempDB):
    def test_create_from_seed(self):
        b = bank_mod.create_bank(self.db, {
            "source": "seed", "level1": "初中", "level2": "九年级",
            "level3": "上册", "level4": "all", "unit_mode": "all",
        })
        self.assertEqual(b["word_count"], 239)
        self.assertEqual(b["unit_count"], 7)
        self.assertIn("初中", b["title"])

    def test_custom_names_override(self):
        b = bank_mod.create_bank(self.db, {
            "source": "seed", "level1": "初中", "level2": "九年级",
            "level3": "上册", "level4": "all", "unit_mode": "all",
            "custom": {"level1": "我班", "level2": "九", "level3": "上", "level4": ""},
        })
        self.assertEqual(b["level1"], "我班")
        self.assertEqual(b["level2"], "九")
        self.assertEqual(b["level3"], "上")
        self.assertTrue(b["title"].startswith("我班-九-上"))

    def test_unit_mode_range(self):
        b = bank_mod.create_bank(self.db, {
            "source": "seed", "level1": "初中", "level2": "九年级",
            "level3": "上册", "level4": "range", "unit_mode": "range",
            "unit_from": 2, "unit_to": 3,
        })
        self.assertEqual(b["unit_count"], 2)
        self.assertEqual(b["level4"], "第2至第3单元")
        self.assertIn("第2至第3单元", b["title"])

    def test_unit_mode_per_unit(self):
        b = bank_mod.create_bank(self.db, {
            "source": "seed", "level1": "初中", "level2": "九年级",
            "level3": "上册", "level4": "per-unit", "unit_mode": "per-unit",
        })
        self.assertEqual(b["unit_mode"], "per-unit")
        self.assertEqual(b["word_count"], 239)

    def test_missing_material_raises(self):
        with self.assertRaises(bank_mod.BankError):
            bank_mod.create_bank(self.db, {"source": "material"})

    def test_bank_from_material(self):
        mid = self.db.insert_material("t", "t.csv", "csv", 10, "", [
            {"unit": "Unit 1", "en": "a", "cn": "甲", "ipa": "", "pos": ""},
            {"unit": "Unit 2", "en": "b", "cn": "乙", "ipa": "", "pos": ""},
        ])
        b = bank_mod.create_bank(self.db, {
            "source": "material", "material_id": mid,
            "level1": "初中", "level2": "九年级", "level3": "上册",
            "level4": "all", "unit_mode": "all",
        })
        self.assertEqual(b["word_count"], 2)
        self.assertEqual(b["unit_count"], 2)

    def test_material_bank_uses_only_the_selected_upload(self):
        first = self.db.insert_material("上册", "up.txt", "txt", 1, "", [
            {"unit": "Unit 1", "en": "apple", "cn": "苹果", "ipa": "", "pos": ""},
        ])
        self.db.insert_material("下册", "down.txt", "txt", 1, "", [
            {"unit": "Unit 1", "en": "book", "cn": "书", "ipa": "", "pos": ""},
        ])
        bank = bank_mod.create_bank(self.db, {
            "source": "material", "material_id": first,
            "level1": "初中", "level2": "九年级", "level3": "上册",
            "unit_mode": "all",
        })
        words = self.db.bank_words(bank["id"])
        self.assertEqual([word["en"] for word in words], ["apple"])

    def test_bank_payload_groups(self):
        b = bank_mod.create_bank(self.db, {
            "source": "seed", "level1": "初中", "level2": "九年级",
            "level3": "上册", "level4": "all", "unit_mode": "all",
        })
        payload = bank_mod.bank_payload(self.db, b["id"])
        groups = payload["groups"]
        self.assertEqual(sum(len(g["words"]) for g in groups), 239)
        for group in groups:
            self.assertLessEqual(len(group["words"]), bank_mod.MAX_PAIRS_PER_LEVEL)
        # 九年级上册每个单元都有三十几个词，应该被拆成多关
        self.assertGreater(len(groups), 7)
        self.assertTrue(any("（1/" in g["unit"] for g in groups))

    def test_chunk_groups_splits_large_units(self):
        words = [{"en": "w%d" % i, "cn": "词", "ipa": ""} for i in range(20)]
        chunks = bank_mod.chunk_groups([{"unit": "Unit 1", "words": words}],
                                       max_pairs=8)
        # 均分：20 个词分成 3 关，每关 7/7/6，不会剩一个只有 1 个词的空关
        self.assertEqual([len(c["words"]) for c in chunks], [7, 7, 6])
        self.assertEqual([c["unit"] for c in chunks],
                         ["Unit 1（1/3）", "Unit 1（2/3）", "Unit 1（3/3）"])
        self.assertEqual([w["en"] for c in chunks for w in c["words"]],
                         [w["en"] for w in words])

    def test_chunk_groups_keeps_small_units_untouched(self):
        words = [{"en": "a", "cn": "甲", "ipa": ""}]
        chunks = bank_mod.chunk_groups([{"unit": "Unit 1", "words": words}])
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["unit"], "Unit 1")

    def test_seed_default_bank_idempotent(self):
        a = bank_mod.seed_default_bank(self.db)
        b = bank_mod.seed_default_bank(self.db)
        self.assertEqual(a, b)
        bank = self.db.get_bank(a)
        self.assertEqual(bank["title"], "人教版初中九年级上册")
        self.assertEqual(bank["word_count"], 239)

    def test_seed_default_bank_renames_legacy_title_in_place(self):
        bid = bank_mod.seed_default_bank(self.db)
        self.db.execute("UPDATE banks SET title=? WHERE id=?",
                        ("人教版初中三年级上学期", bid))
        self.assertEqual(bank_mod.seed_default_bank(self.db), bid)
        self.assertEqual(self.db.get_bank(bid)["title"], "人教版初中九年级上册")

    def test_seed_migrates_all_legacy_titles_and_keeps_duplicate_history(self):
        default_id = bank_mod.seed_default_bank(self.db)
        duplicate = bank_mod.create_bank(self.db, {
            "source": "seed", "level1": "初中", "level2": "九年级",
            "level3": "上册", "unit_mode": "all", "title": "人教版初中三年级上学期",
        })
        full_year = bank_mod.create_bank(self.db, {
            "source": "seed", "level1": "初中", "level2": "九年级",
            "level3": "整学年", "level4": "all", "unit_mode": "all",
        })
        self.db.execute("UPDATE banks SET title=? WHERE id=?",
                        ("初中-九年级-整学年-全部单元", full_year["id"]))
        self.db.execute("UPDATE banks SET level3=? WHERE id=?",
                ("整学年", full_year["id"]))

        self.assertEqual(bank_mod.seed_default_bank(self.db), default_id)
        self.assertEqual(self.db.get_bank(duplicate["id"])["title"],
                         "人教版初中九年级上册（历史副本）")
        self.assertEqual(self.db.get_bank(full_year["id"])["title"],
                         "初中-九年级-全年（上下册）-全部单元")

    def test_full_year_bank_uses_consistent_volume_label(self):
        names = bank_mod.resolve_levels({
            "level1": "初中", "level2": "九年级", "level3": "整学年",
            "level4": "all", "unit_mode": "all",
        })
        self.assertEqual(names["level3"], "全年（上下册）")


# ---------------------------------------------------------------- 离线产物

class TestOffline(TempDB):
    def make(self):
        b = bank_mod.create_bank(self.db, {
            "source": "seed", "level1": "初中", "level2": "九年级",
            "level3": "上册", "level4": "all", "unit_mode": "all",
        })
        payload = bank_mod.bank_payload(self.db, b["id"])
        groups = payload["groups"]
        return b, groups

    def test_filename_pattern(self):
        b, groups = self.make()
        name = offline.build_filename(b)
        self.assertTrue(name.endswith(".html"))
        self.assertIn("初中-九年级-上册", name)
        # 日期 + 时间
        self.assertRegex(name, r"-\d{8}-\d{6}\.html$")

    def test_html_is_self_contained(self):
        b, groups = self.make()
        name, html = offline.build_offline_html(b, groups)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("var WP_DATA", html)
        self.assertIn("WPGame.Game", html)
        self.assertIn("game-core", html)  # 注释里带文件名，确认脚本被内联
        self.assertNotIn("<script src=", html)
        self.assertNotIn("<link rel=\"stylesheet\"", html)

    def test_html_contains_words(self):
        b, groups = self.make()
        _, html = offline.build_offline_html(b, groups)
        self.assertIn("textbook", html)

    def test_empty_bank_raises(self):
        b, _ = self.make()
        with self.assertRaises(ValueError):
            offline.build_offline_html(b, [])

    def test_safe_filename(self):
        self.assertEqual(offline.safe_filename("a/b:c*d"), "a-b-c-d")
        self.assertEqual(offline.safe_filename("   "), "题库")


# ---------------------------------------------------------------- HTTP 接口

class TestHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import threading
        cls.tmp = tempfile.TemporaryDirectory()
        os.environ["WP_DB"] = str(Path(cls.tmp.name) / "http.db")
        from server import app as app_mod
        cls.httpd = app_mod.build_server("127.0.0.1", 0, str(Path(cls.tmp.name) / "http.db"))
        cls.port = cls.httpd.server_address[1]
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.httpd.serve_forever,
                                      kwargs={"poll_interval": 0.05}, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        from server.app import Handler
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=5)
        Handler.db.close()
        cls.tmp.cleanup()
        os.environ.pop("WP_DB", None)

    def get(self, path):
        with urllib.request.urlopen(self.base + urllib.parse.quote(path, safe="/?=&"),
                                    timeout=10) as r:
            return json.loads(r.read().decode())

    def post(self, path, payload=None):
        data = json.dumps(payload or {}).encode()
        req = urllib.request.Request(self.base + path, data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())

    def test_health(self):
        self.assertTrue(self.get("/api/health")["ok"])

    def test_meta(self):
        meta = self.get("/api/meta")
        self.assertEqual(meta["default_term"], "整学年")
        self.assertEqual(meta["default_selection"]["level2"], "九年级")

    def test_terms_and_units(self):
        terms = self.get("/api/terms?level1=初中&level2=九年级")
        keys = [o["key"] for o in terms["options"]]
        self.assertEqual(keys, ["上册", "下册", "整学年"])
        labels = {o["key"]: o["name"] for o in terms["options"]}
        self.assertEqual(labels["整学年"], "全年（上下册）")
        units = self.get("/api/units?level1=初中&level2=九年级&level3=上册")
        self.assertEqual(len(units["units"]), 7)

    def test_default_bank_seeded(self):
        banks = self.get("/api/banks")["banks"]
        titles = [b["title"] for b in banks]
        self.assertIn("人教版初中九年级上册", titles)

    def test_create_bank_and_play(self):
        res = self.post("/api/banks", {
            "source": "seed", "level1": "初中", "level2": "九年级",
            "level3": "上册", "level4": "all", "unit_mode": "all",
        })
        bid = res["bank"]["id"]
        payload = self.get(f"/api/banks/{bid}")
        self.assertEqual(sum(len(g["words"]) for g in payload["groups"]), 239)

    def test_offline_generation_and_download(self):
        res = self.post("/api/banks", {
            "source": "seed", "level1": "初中", "level2": "九年级",
            "level3": "上册", "level4": "all", "unit_mode": "all",
        })
        bid = res["bank"]["id"]
        off = self.post(f"/api/banks/{bid}/offline")
        self.assertTrue(off["filename"].endswith(".html"))
        with urllib.request.urlopen(self.base + off["url"], timeout=10) as r:
            disposition = r.headers.get("Content-Disposition", "")
            self.assertIn('filename="lexica-offline-', disposition)
            self.assertIn("filename*=UTF-8''", disposition)
            html = r.read().decode()
        self.assertIn("var WP_DATA", html)

    def test_offline_post_body_does_not_corrupt_keep_alive_connection(self):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            connection.request("GET", "/api/banks")
            banks = json.loads(connection.getresponse().read())["banks"]
            bank_id = banks[0]["id"]

            connection.request("POST", f"/api/banks/{bank_id}/offline", body=b"{}",
                               headers={"Content-Type": "application/json"})
            generated = json.loads(connection.getresponse().read())

            connection.request("GET", "/api/offline")
            files = json.loads(connection.getresponse().read())["files"]
            self.assertIn(generated["filename"], [item["name"] for item in files])

            connection.request("GET", generated["url"])
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertIn(b"<!DOCTYPE html>", response.read()[:100])
        finally:
            connection.close()

    def test_scores(self):
        self.post("/api/scores", {
            "bank_id": 1, "bank_title": "测试", "device": "d-test",
            "score": 1234, "matched": 10, "total_pairs": 20,
            "wrong": 2, "best_combo": 5, "duration": 30, "level_count": 1,
            "detail": [{"level": 0, "score": 1234}],
        })
        res = self.get("/api/scores?limit=10")
        self.assertGreaterEqual(res["stats"]["best"], 1234)
        self.assertTrue(any(s["bank_title"] == "测试" for s in res["scores"]))

    def test_unknown_api_404(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.get("/api/nope")
        self.assertEqual(ctx.exception.code, 404)

    def test_static_index(self):
        with urllib.request.urlopen(self.base + "/", timeout=10) as r:
            body = r.read().decode()
        self.assertIn("词境 Lexica", body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
