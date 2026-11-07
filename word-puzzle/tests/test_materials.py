"""音标 / 发音 / Word / PDF / 词表解析的测试。

跑法::

    python3 -m unittest discover -s tests -v

依赖外部工具的用例（poppler / tesseract / espeak-ng）在工具缺失时自动跳过。
"""
from __future__ import annotations

import io
import shutil
import struct
import sys
import unittest
import wave
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server import docx, ipa, pdf, tts, wordlist   # noqa: E402


# ---------------------------------------------------------------- 音标

class TestIPA(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.table = ipa.load_table()

    def test_table_loaded(self):
        self.assertGreater(len(self.table), 100_000)

    def test_arpabet_to_ipa(self):
        # 重音标记
        self.assertEqual(ipa.arpabet_to_ipa("HH AH0 L OW1"), "həlˈoʊ")
        # r 音
        self.assertEqual(ipa.arpabet_to_ipa("T IY1 CH ER0"), "tˈitʃɚ")
        # 长元音不写成英式的 ɑː
        self.assertEqual(ipa.arpabet_to_ipa("B AA1 R"), "bˈɑɹ")

    def test_british_to_american(self):
        self.assertEqual(ipa.to_american_spelling("colour"), "color")
        self.assertEqual(ipa.to_american_spelling("organise"), "organize")
        self.assertEqual(ipa.to_american_spelling("centre"), "center")
        # 已经是美式的词不受影响
        self.assertEqual(ipa.to_american_spelling("color"), "color")

    def test_lookup_american_discriminators(self):
        """典型英美分歧词必须是美式读音。"""
        cases = {
            "ask": "ˈæsk",         # 英式 /ɑːsk/
            "schedule": "skˈɛdʒʊl",  # 英式 /ˈʃɛdjuːl/
            "teacher": "tˈitʃɚ",   # 美式 r 音，英式 /ˈtiːtʃə/
            "orange": "ˈɔɹəndʒ",   # 英式 /ˈɒrɪndʒ/
            "class": "klˈæs",
            "water": "wˈɔtɚ",
            "hello": "həlˈoʊ",
            "bird": "bˈɝd",
            "want": "wˈɑnt",
        }
        for word, expected in cases.items():
            got = ipa.lookup(word, self.table)
            self.assertTrue(got, f"{word} 没有查到音标")
            self.assertEqual(got, f"/{expected}/", f"{word} 的音标不是美式")

    def test_lookup_no_british_length_marks(self):
        """生成的音标里不应出现英式的长音符号 ``:``。"""
        for word in ("ask", "teacher", "class", "water", "schedule", "about"):
            got = ipa.lookup(word, self.table)
            self.assertNotIn(":", got, f"{word} 的音标里有英式长音符号")

    def test_lookup_compound(self):
        got = ipa.lookup("schoolbag", self.table)
        self.assertTrue(got.startswith("/") and got.endswith("/"))

    def test_lookup_placeholder(self):
        got = ipa.lookup("sb", self.table)
        self.assertTrue(got, "占位符 sb 应该有音标")
        got = ipa.lookup("sth", self.table)
        self.assertTrue(got, "占位符 sth 应该有音标")

    def test_lookup_manual_proper_noun(self):
        got = ipa.lookup("Mount Huangshan", self.table)
        self.assertTrue(got, "专有名词应该有音标")

    def test_lookup_unknown_returns_empty(self):
        self.assertEqual(ipa.lookup("zzzqqqxxx", self.table), "")


# ---------------------------------------------------------------- 发音

class TestTTS(unittest.TestCase):
    def test_voice_is_american_neural_female(self):
        self.assertEqual(tts.voice(), "en-US-AriaNeural")

    def test_invalid_voice_falls_back(self):
        """配置被改坏时必须退回美式女声，不能读成别的语言。"""
        original = tts.DEFAULT_VOICE
        try:
            for bad in ("zh", "en-gb", "en-gb+f2", "en-us+f3", "de", ""):
                tts.DEFAULT_VOICE = bad
                self.assertEqual(tts.voice(), "en-US-AriaNeural")
        finally:
            tts.DEFAULT_VOICE = original

    def test_describe(self):
        d = tts.describe()
        self.assertIn("tts_voice", d)
        self.assertIn("tts_available", d)
        self.assertIn("tts_error", d)
        self.assertIn("tts_remote", d)

    def test_audio_content_type_detects_mp3_and_wav(self):
        self.assertEqual(tts.content_type(b"RIFF....WAVE"), "audio/wav")
        self.assertEqual(tts.content_type(b"ID3...."), "audio/mpeg")

    def test_synth_prefers_edge_then_falls_back(self):
        with (mock.patch.object(tts, "find_edge_tts", return_value="edge-tts"),
              mock.patch.object(tts, "_synth_edge", return_value=b"ID3 neural")
              as edge,
              mock.patch.object(tts, "_synth_espeak", return_value=b"RIFF local")
              as espeak):
            self.assertEqual(tts.synth("apple"), b"ID3 neural")
            edge.assert_called_once()
            espeak.assert_not_called()

        with (mock.patch.object(tts, "find_edge_tts", return_value="edge-tts"),
              mock.patch.object(tts, "_synth_edge", return_value=None),
              mock.patch.object(tts, "_synth_espeak", return_value=b"RIFF local")
              as espeak):
            self.assertEqual(tts.synth("apple"), b"RIFF local")
            espeak.assert_called_once()

    @unittest.skipUnless(tts.find_espeak(), "没装 espeak-ng")
    def test_espeak_fallback_returns_wav(self):
        data = tts._synth_espeak("apple")
        self.assertTrue(data, "espeak-ng 应该能合成音频")
        self.assertEqual(data[:4], b"RIFF")
        self.assertEqual(data[8:12], b"WAVE")

    @unittest.skipUnless(tts.find_espeak(), "没装 espeak-ng")
    def test_espeak_fallback_is_female_by_pitch(self):
        f0 = _measure_f0(tts._synth_espeak(
            "the quick brown fox jumps over the lazy dog"))
        self.assertIsNotNone(f0, "测不出基频")
        # 女声通常在 160~250 Hz，男声在 80~130 Hz
        self.assertGreater(f0, 145, f"基频 {f0:.0f} Hz 偏低，可能不是女声")


def _measure_f0(wav_bytes: bytes) -> float | None:
    """粗略测一下 WAV 的基频（自相关法），只用来判断高/低。"""
    if not wav_bytes:
        return None
    with wave.open(io.BytesIO(wav_bytes)) as w:
        sr = w.getframerate()
        raw = w.readframes(w.getnframes())
        channels = w.getnchannels()
    samples = struct.unpack("<%dh" % (len(raw) // 2), raw)
    if channels > 1:
        samples = samples[::channels]
    frame = int(sr * 0.04)
    values = []
    for off in range(0, len(samples) - frame, frame):
        seg = samples[off:off + frame]
        rms = (sum(x * x for x in seg) / len(seg)) ** 0.5
        if rms < 1200:
            continue
        best, best_lag = 0.0, 0
        for lag in range(int(sr / 350), int(sr / 70)):
            acc = 0
            for i in range(0, frame - lag, 2):
                acc += seg[i] * seg[i + lag]
            if acc > best:
                best, best_lag = acc, lag
        if best_lag:
            values.append(sr / best_lag)
    if not values:
        return None
    values.sort()
    return values[len(values) // 2]


# ---------------------------------------------------------------- 词表解析

class TestWordlist(unittest.TestCase):
    def test_tab_separated(self):
        entries = wordlist.parse_lines(["apple\t苹果", "banana\t香蕉"])
        self.assertEqual([e["en"] for e in entries], ["apple", "banana"])
        self.assertEqual([e["cn"] for e in entries], ["苹果", "香蕉"])

    def test_unit_header(self):
        entries = wordlist.parse_lines([
            "Unit 1",
            "apple\t苹果",
            "Unit 2",
            "banana\t香蕉",
        ])
        self.assertEqual(entries[0]["unit"], "Unit 1")
        self.assertEqual(entries[1]["unit"], "Unit 2")

    def test_chinese_unit_header(self):
        entries = wordlist.parse_lines([
            "第一单元",
            "apple 苹果",
            "第二单元",
            "banana 香蕉",
        ])
        self.assertEqual(entries[0]["unit"], "第一单元")
        self.assertEqual(entries[1]["unit"], "第二单元")

    def test_ipa_and_pos(self):
        entries = wordlist.parse_lines(["apple /ˈæpl/ n. 苹果"])
        self.assertEqual(entries[0]["en"], "apple")
        self.assertEqual(entries[0]["ipa"], "/ˈæpl/")
        self.assertEqual(entries[0]["pos"], "n.")
        self.assertEqual(entries[0]["cn"], "苹果")

    def test_bracket_ipa(self):
        entries = wordlist.parse_lines(["apple [ˈæpl] 苹果"])
        self.assertEqual(entries[0]["ipa"], "/ˈæpl/")

    def test_no_english_leak_into_chinese(self):
        """``苹果apple`` 这种写法中文里不能混进英文。"""
        entries = wordlist.parse_lines(["苹果apple", "香蕉banana"])
        self.assertEqual(entries[0]["cn"], "苹果")
        self.assertEqual(entries[0]["en"], "apple")

    def test_pos_not_treated_as_english(self):
        """``n.`` / ``v.`` 是词性，不是单词。"""
        entries = wordlist.parse_lines(["apple n. 苹果", "run v. 跑"])
        self.assertEqual([e["en"] for e in entries], ["apple", "run"])

    def test_two_column_fallback(self):
        """英文列和中文列分开时按顺序配对。"""
        entries = wordlist.parse_lines([
            "apple", "banana", "orange",
            "苹果", "香蕉", "橙子",
        ])
        self.assertEqual([e["en"] for e in entries], ["apple", "banana", "orange"])
        self.assertEqual([e["cn"] for e in entries], ["苹果", "香蕉", "橙子"])

    def test_empty_input(self):
        self.assertEqual(wordlist.parse_lines([]), [])
        self.assertEqual(wordlist.parse_lines(["", "   "]), [])


# ---------------------------------------------------------------- Word

def _make_docx(path: Path, paragraphs: list[str], tables: list[list[list[str]]]) -> None:
    """造一个最小可用的 .docx（OOXML 是 zip + xml）。"""
    W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    body = []
    for p in paragraphs:
        body.append(
            f"<w:p><w:r><w:t xml:space=\"preserve\">{p}</w:t></w:r></w:p>"
        )
    for rows in tables:
        cells = []
        for row in rows:
            tcs = "".join(
                f"<w:tc><w:p><w:r><w:t>{c}</w:t></w:r></w:p></w:tc>"
                for c in row
            )
            cells.append(f"<w:tr>{tcs}</w:tr>")
        body.append(f"<w:tbl>{''.join(cells)}</w:tbl>")
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f"<w:document {W}><w:body>{''.join(body)}</w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/>'
        "</Relationships>"
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", document)


class TestDocx(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "test.docx"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_paragraphs(self):
        _make_docx(self.path, ["Unit 1", "apple\t苹果", "banana\t香蕉"], [])
        self.assertTrue(docx.is_docx(self.path.read_bytes()))
        lines = docx.docx_to_lines(self.path.read_bytes())
        self.assertIn("apple\t苹果", lines)

    def test_tables(self):
        _make_docx(self.path, [], [[["apple", "苹果"], ["banana", "香蕉"]]])
        lines = docx.docx_to_lines(self.path.read_bytes())
        self.assertIn("apple\t苹果", lines)
        self.assertIn("banana\t香蕉", lines)

    def test_parse_to_entries(self):
        _make_docx(self.path, ["Unit 1", "apple\t苹果"], [])
        entries = wordlist.parse_lines(docx.docx_to_lines(self.path.read_bytes()))
        self.assertEqual(entries[0]["en"], "apple")
        self.assertEqual(entries[0]["cn"], "苹果")
        self.assertEqual(entries[0]["unit"], "Unit 1")

    def test_legacy_doc_rejected(self):
        """老式 .doc 是 OLE2 复合文档，要明确提示另存为 .docx。"""
        self.assertTrue(docx.is_legacy_doc(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 64))
        with self.assertRaises(Exception) as ctx:
            docx.doc_magic_check(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 64)
        self.assertIn("docx", str(ctx.exception).lower())


# ---------------------------------------------------------------- PDF

class TestPDF(unittest.TestCase):
    def test_describe(self):
        d = pdf.describe()
        self.assertIn("pdf_text_tool", d)
        self.assertIn("pdf_ocr_available", d)

    def test_too_large_rejected(self):
        with self.assertRaises(Exception):
            pdf.pdf_to_text(b"%PDF-1.7\n" + b"0" * (pdf.MAX_BYTES + 1))

    def test_garbage_does_not_hang(self):
        """坏文件不能把解析线程卡死（以前正则回溯是平方级）。"""
        import time
        data = b"%PDF-1.7\n" + b"0" * 800_000
        t0 = time.time()
        try:
            pdf.pdf_to_text(data)
        except Exception:
            pass
        self.assertLess(time.time() - t0, 10, "解析坏 PDF 太慢了")

    def test_reconstruct_rows_pairs_columns(self):
        """OCR 的词 + 坐标 → 同一行的英文和中文要配成一对。"""
        #            top, bottom, left, right, text
        rows = [
            [(100, 140, 200, 260, "apple"), (104, 144, 700, 760, "苹果")],
            [(200, 240, 200, 300, "banana"), (204, 244, 700, 760, "香蕉")],
        ]
        out = pdf._reconstruct_rows(rows, tol=40.0)
        self.assertEqual(out[0], "apple\t苹果")
        self.assertEqual(out[1], "banana\t香蕉")

    def test_reconstruct_rows_keeps_same_line_together(self):
        """同一行里挨得近的词用空格隔开，不拆列。"""
        rows = [
            [(100, 140, 200, 260, "Unit"), (100, 140, 270, 300, "1")],
        ]
        out = pdf._reconstruct_rows(rows, tol=40.0)
        self.assertEqual(out[0], "Unit 1")


@unittest.skipUnless(shutil.which("pdftotext"), "没装 poppler-utils")
class TestPDFWithPoppler(unittest.TestCase):
    def test_text_pdf(self):
        """用 poppler 抽取文字版 PDF。"""
        import subprocess
        import tempfile
        tmp = Path(tempfile.mkdtemp())
        try:
            # 用 python 生成一个最小 PDF（内容流未压缩）
            content = b"BT /F1 12 Tf 72 720 Td (Unit 1) Tj ET"
            objs = []
            objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
            objs.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
            objs.append(
                b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
            )
            objs.append(b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n"
                        + content + b"\nendstream")
            objs.append(
                b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
            )
            out = bytearray(b"%PDF-1.4\n")
            offsets = []
            for i, body in enumerate(objs, start=1):
                offsets.append(len(out))
                out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
            xref = len(out)
            out += f"xref\n0 {len(objs) + 1}\n".encode()
            out += b"0000000000 65535 f \n"
            for off in offsets:
                out += f"{off:010d} 00000 n \n".encode()
            out += (f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\n"
                    f"startxref\n{xref}\n%%EOF\n").encode()
            pdf_path = tmp / "t.pdf"
            pdf_path.write_bytes(bytes(out))

            data = pdf_path.read_bytes()
            text, engine = pdf.pdf_to_text(data)
            self.assertIn("Unit 1", text)
            self.assertIn(engine, ("pdftotext", "builtin", "ocr"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
