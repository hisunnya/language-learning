"""词境后端的加固用例：XSS、命令行参数注入、连接复用、跨站写请求、事务回滚、部署脚本。

跑法::

    python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import http.client
import io
import json
import os
import sys
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server import bank as bank_mod            # noqa: E402
from server import docx, materials, offline, tts  # noqa: E402
from server.db import Database                  # noqa: E402

ATTACK = "</script><script>alert(1)</script>"


class TestOfflineEscaping(unittest.TestCase):
    def test_json_for_script_has_no_markup_characters(self):
        text = offline._json_for_script({"w": ATTACK + "&  "})
        for bad in ("<", ">", "&", " ", " "):
            self.assertNotIn(bad, text)
        self.assertEqual(json.loads(text)["w"], ATTACK + "&  ")

    def test_word_cannot_close_the_script_block(self):
        bank = {"id": 1, "title": "t", "level1": "a", "level2": "b", "level3": "c",
                "level4": "d", "pairs_per_level": 12}
        groups = [{"name": "Unit 1", "words": [
            {"en": ATTACK, "cn": "x", "ipa": "", "pos": ""}]}]
        _, html = offline.build_offline_html(bank, groups)
        self.assertNotIn(ATTACK, html)
        self.assertNotIn("<script>alert(1)", html)


class TestTtsArguments(unittest.TestCase):
    def test_option_like_and_control_words_are_rejected(self):
        for word in ("-x", "--stdin", "-f/etc/passwd", "", "a\nb", "x" * 81):
            self.assertFalse(tts.is_valid_word(word), word)
        for word in ("apple", "ice cream", "don't", "well-known", "3D",
                     "( real ) estate agent", "（at）first hand"):
            self.assertTrue(tts.is_valid_word(word), word)

    def test_every_built_in_word_can_be_synthesised(self):
        """词库里的词一个都不能被校验误伤，否则含它的离线题库整个生成失败。"""
        import glob
        rejected = []

        def walk(node):
            if isinstance(node, dict):
                if isinstance(node.get("en"), str) and not tts.is_valid_word(node["en"].strip()):
                    rejected.append(node["en"])
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        for name in glob.glob(str(ROOT / "data" / "*.json")):
            walk(json.loads(Path(name).read_text(encoding="utf-8")))
        self.assertEqual(rejected, [])

    def test_invalid_word_never_reaches_a_subprocess(self):
        with mock.patch.object(tts.subprocess, "run") as run:
            self.assertIsNone(tts.synth("-x"))
            run.assert_not_called()

    def test_synth_many_rejects_option_like_words(self):
        with self.assertRaises(tts.SynthesisError):
            tts.synth_many(["apple", "-x"])

    def test_edge_gets_text_as_one_argument(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(tts, "AUDIO_DIR", Path(tmp)), \
                mock.patch.object(tts.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=1, stderr=b"")
            tts._edge_retry_after = 0.0
            tts._synth_edge("apple", "/bin/edge-tts")
            tts._edge_retry_after = 0.0
        argv = run.call_args[0][0]
        self.assertIn("--text=apple", argv)
        self.assertNotIn("--text", argv)

    def test_espeak_gets_double_dash_before_the_word(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(tts, "AUDIO_DIR", Path(tmp)), \
                mock.patch.object(tts, "_run_espeak") as run:
            run.return_value = mock.Mock(returncode=1, stderr=b"")
            tts._synth_espeak("apple", "/bin/espeak-ng")
            leftovers = list(Path(tmp).iterdir())
        argv = run.call_args[0][0]
        self.assertEqual(argv[-2:], ["--", "apple"])
        self.assertEqual(leftovers, [], "失败后不能留下半截文件")

    def test_cache_is_pruned_to_the_limit(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(tts, "AUDIO_DIR", Path(tmp)), \
                mock.patch.object(tts, "MAX_CACHE_FILES", 10):
            for i in range(30):
                (Path(tmp) / f"w{i}.mp3").write_bytes(b"x")
            tts._prune_cache()
            self.assertLess(len(list(Path(tmp).iterdir())), 30)


class TestDatabaseRollback(unittest.TestCase):
    def test_failed_material_insert_leaves_nothing_behind(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "t.db")
            try:
                bad = [{"unit": "U1", "en": "a", "cn": "甲"}, {"en": "b", "cn": "乙"}]
                with self.assertRaises(KeyError):
                    db.insert_material("m", "m.txt", "txt", 1, "", bad)
                db.execute("INSERT INTO scores(bank_title, created_at) VALUES ('x','t')")
                self.assertEqual(db.list_materials(), [])
            finally:
                db.close()


class TestInputLimits(unittest.TestCase):
    def test_bank_range_rejects_non_numbers(self):
        units = [{"label": "U1", "words": []}]
        with self.assertRaises(bank_mod.BankError):
            bank_mod.apply_unit_mode(units, "range", "abc", 2)

    def test_docx_body_size_is_capped(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("word/document.xml", "<w:document/>" + " " * 2048)
        with mock.patch.object(docx, "MAX_DOCUMENT_BYTES", 1024):
            with self.assertRaises(docx.DocxError):
                docx.docx_to_lines(buf.getvalue())


class TestHttpHardening(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        from server import app as app_mod
        cls.app = app_mod
        cls.httpd = app_mod.build_server(
            "127.0.0.1", 0, str(Path(cls.tmp.name) / "h.db"))
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever,
                                      kwargs={"poll_interval": 0.05}, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=5)
        cls.app.Handler.db.close()
        cls.tmp.cleanup()

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            conn.request(method, path, body=body, headers=headers or {})
            resp = conn.getresponse()
            return resp.status, resp.getheader("Connection"), resp.read()
        finally:
            conn.close()

    def test_option_like_audio_word_is_400(self):
        with mock.patch.object(tts, "synth") as synth:
            status, _, _ = self.request("GET", "/api/audio/-x")
            self.assertEqual(status, 400)
            synth.assert_not_called()

    def test_bad_query_numbers_are_400_not_500(self):
        for query in ("limit=abc", "limit=-1", "bank_id=zz"):
            status, _, _ = self.request("GET", "/api/scores?" + query)
            self.assertEqual(status, 400, query)

    def test_bad_content_length_is_400(self):
        status, _, _ = self.request("POST", "/api/scores", headers={"Content-Length": "abc"})
        self.assertEqual(status, 400)

    def test_unread_body_closes_the_connection(self):
        """404 之前没读请求体：必须关连接，否则残留字节会变成下一个请求。"""
        status, connection, _ = self.request(
            "POST", "/api/nope", body=b'{"a":1}',
            headers={"Content-Type": "application/json"})
        self.assertEqual(status, 404)
        self.assertEqual((connection or "").lower(), "close")

    def test_smuggled_second_request_is_not_executed(self):
        import socket
        smuggled = b"GET /api/health HTTP/1.1\r\nHost: x\r\n\r\n"
        raw = (b"POST /api/nope HTTP/1.1\r\nHost: x\r\nContent-Length: "
               + str(len(smuggled)).encode() + b"\r\n\r\n" + smuggled)
        with socket.create_connection(("127.0.0.1", self.port), timeout=5) as sock:
            sock.sendall(raw)
            data = b""
            while True:          # 服务端应在第一个响应后关闭连接，读到 EOF 为止
                chunk = sock.recv(65536)
                if not chunk:
                    break
                data += chunk
        self.assertEqual(data.count(b"HTTP/1.1 "), 1, "残留请求体不能被当成第二个请求执行")
        self.assertIn(b"404", data.split(b"\r\n", 1)[0])

    def test_normal_post_keeps_the_connection_alive(self):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            body = json.dumps({"score": 1}).encode()
            conn.request("POST", "/api/scores", body=body,
                         headers={"Content-Type": "application/json"})
            first = conn.getresponse()
            first.read()
            self.assertEqual(first.status, 201)
            self.assertNotEqual((first.getheader("Connection") or "").lower(), "close")
            conn.request("GET", "/api/health")
            self.assertEqual(conn.getresponse().status, 200)
        finally:
            conn.close()

    def test_cross_site_write_is_rejected(self):
        body = json.dumps({"score": 1}).encode()
        status, _, _ = self.request("POST", "/api/scores", body=body, headers={
            "Content-Type": "application/json", "Origin": "http://evil.example"})
        self.assertEqual(status, 403)

    def test_same_origin_write_is_allowed(self):
        body = json.dumps({"score": 1}).encode()
        status, _, _ = self.request("POST", "/api/scores", body=body, headers={
            "Content-Type": "application/json",
            "Origin": f"http://127.0.0.1:{self.port}"})
        self.assertEqual(status, 201)

    def test_heavy_jobs_are_limited(self):
        held = []
        try:
            while self.app.HEAVY_JOBS.acquire(blocking=False):
                held.append(1)
            status, _, _ = self.request("POST", "/api/banks/1/offline", body=b"{}",
                                        headers={"Content-Type": "application/json"})
            self.assertEqual(status, 503)
        finally:
            for _ in held:
                self.app.HEAVY_JOBS.release()


class TestDeployFiles(unittest.TestCase):
    def read(self, rel):
        return (ROOT / rel).read_text(encoding="utf-8")

    def test_installer_writes_the_chosen_port_into_the_unit(self):
        self.assertIn("^Environment=WP_PORT=", self.read("deploy/install.sh"))

    def test_fallback_copy_never_deletes_var(self):
        script = self.read("deploy/install.sh")
        self.assertNotIn('rm -rf "$INSTALL_DIR/var"', script)
        self.assertIn("! -name var", script)

    def test_rsync_is_a_declared_dependency(self):
        self.assertIn("\n  rsync\n", self.read("deploy/check-deps.sh"))

    def test_offline_location_beats_the_html_regex(self):
        self.assertIn("location ^~ /offline/", self.read("deploy/nginx/word-puzzle.conf"))

    def test_nginx_forwards_the_port_in_host(self):
        self.assertIn("Host $http_host;", self.read("deploy/nginx/word-puzzle.conf"))
        hub = (ROOT.parent / "hub" / "deploy" / "lingua-grove.conf").read_text(encoding="utf-8")
        self.assertIn("Host $http_host;", hub)


if __name__ == "__main__":
    unittest.main()
