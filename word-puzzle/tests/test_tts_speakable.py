"""教学缩写（sb. / sth. 等）要念成完整的词；离线页里每个词都有内嵌音频。"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, ROOT.as_posix())

from server import offline, tts          # noqa: E402


class TestSpeakable(unittest.TestCase):
    CASES = {
        "sb": "somebody", "sth": "something", "sb.": "somebody", "sth.": "something", "SB": "somebody", "Sth.": "something",
        "sb's": "somebody's", "work on sth.": "work on something", "help sb. with sth.": "help somebody with something",
        "turn one’s attention to sth. / sb.": "turn one’s attention to something or somebody",
        "speak for itself / themselves": "speak for itself or themselves",
        "lift … out of …": "lift out of", "lift...out of...": "lift out of",
        "etc.": "et cetera", "apples, oranges etc.": "apples, oranges et cetera", "e.g. apple": "for example apple",
        "i.e. a fruit": "that is a fruit", "vs": "versus",
    }
    UNCHANGED = ["apple", "absorb", "sixth", "stab", "sbs", "stuff", "something", "somebody", "take care of", "1/2 cup",
                 "( real ) estate agent", "U.S.A", "Mr. Green", "well-known"]

    def test_teaching_abbreviations_become_whole_words(self):
        for text, spoken in self.CASES.items():
            self.assertEqual(tts.speakable(text), spoken, text)

    def test_ordinary_words_are_left_alone_including_ones_that_merely_contain_the_letters(self):
        for text in self.UNCHANGED:
            self.assertEqual(tts.speakable(text), text, text)

    def test_something_that_would_be_empty_falls_back_to_the_original(self):
        self.assertEqual(tts.speakable("..."), "...")
        self.assertEqual(tts.speakable(""), "")


class TestSynthesisUsesTheSpokenText(unittest.TestCase):
    def setUp(self):
        self.said = []

        def fake_edge(text, exe):
            self.said.append(text)
            return ("audio:" + text).encode()
        self.patches = [mock.patch.object(tts, "find_edge_tts", return_value="edge"),
                        mock.patch.object(tts, "_synth_edge", side_effect=fake_edge)]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def test_single_word_is_spoken_in_full(self):
        self.assertEqual(tts.synth("work on sth."), b"audio:work on something")
        self.assertEqual(self.said, ["work on something"])

    def test_many_words_are_keyed_by_the_card_text_and_synthesised_once_per_spoken_text(self):
        out = tts.synth_many(["sth.", "something", "lift … out of …", "apple"])
        self.assertEqual(set(out), {"sth.", "something", "lift … out of …", "apple"})
        self.assertEqual(out["sth."], out["something"])
        self.assertEqual(sorted(self.said), ["apple", "lift out of", "something"], "sth. 和 something 只合成一次")

    def test_a_failure_names_the_card_text_not_the_spoken_text(self):
        with mock.patch.object(tts, "_synth_edge", return_value=None):
            with self.assertRaises(tts.SynthesisError) as ctx:
                tts.synth_many(["sth."])
        self.assertIn("sth.", str(ctx.exception))

    def test_cache_is_keyed_by_the_spoken_text_so_old_letter_by_letter_clips_are_not_reused(self):
        self.assertEqual(tts._cache_file("something", "edge-tts", "v", "mp3"), tts._cache_file(tts.speakable("sth."), "edge-tts", "v", "mp3"))
        self.assertNotEqual(tts._cache_file("sth.", "edge-tts", "v", "mp3"), tts._cache_file(tts.speakable("sth."), "edge-tts", "v", "mp3"))


class TestOfflinePageCarriesTheAudio(unittest.TestCase):
    """离线游戏页内置了语音文件：每个词都在内嵌的音频表里，键和游戏里查找的键（小写）一致。"""

    def test_every_word_has_an_embedded_clip_under_its_lowercase_key(self):
        words = ["Apple", "work on sth.", "lift … out of …", "speak for itself / themselves"]
        groups = [{"unit": "Unit 1", "words": [{"en": w, "cn": "释义%d" % i, "ipa": ""} for i, w in enumerate(words)]}]
        with mock.patch.object(tts, "find_edge_tts", return_value="edge"), \
                mock.patch.object(tts, "_synth_edge", side_effect=lambda t, e: ("ID3" + t).encode()):
            audio = tts.synth_many(words)
        bank = {"id": 1, "title": "t", "level1": "a", "level2": "b", "level3": "c", "level4": "d", "word_count": 4}
        _, html = offline.build_offline_html(bank, groups, audio=audio)
        data = re.search(r"var WP_DATA = (\{.*?\});\s*</script>", html, re.S).group(1)
        import json
        embedded = json.loads(data.replace("\\u0026", "&").replace("\\u003c", "<").replace("\\u003e", ">"))["audio"]
        for w in words:
            self.assertIn(w.strip().lower(), embedded, w)
            self.assertTrue(embedded[w.strip().lower()].startswith("data:audio/"), w)
        self.assertIn("var AUDIO", (ROOT / "web" / "js" / "game-ui.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
