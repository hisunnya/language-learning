"""词境所有页面的中英文切换：词条两边一致、脚本里没有漏掉的中文、每个页面（含离线单文件页）都能切。"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tests.test_family_pages import TextNodes   # noqa: E402

WEB = ROOT / "web"
JS = WEB / "js"
NODE = shutil.which("node") or shutil.which("nodejs")
CJK = re.compile(r"[一-鿿]")

# 这些页面的文字都要能切换（登录 / 改密码 / 账号管理用 auth-ui.js 自己的词表，由 test_family_pages 检查）
PAGES = ("index.html", "bank.html", "stats.html", "play.html")
# 带用户可见文字、必须走 t() 的脚本
SCRIPTS = ("page-home.js", "page-bank.js", "page-stats.js", "page-play.js", "game-ui.js", "selector.js", "api.js")

# 中文字符串字面量里，这些不是给人看的：和后端 / 教材数据约定好的值，翻译了反而会坏
DATA_LITERALS = {"自定义", "整学年", "初中", "九年级", "上册"}
# api.js 里给「没加载 i18n.js 的页面」留的中文退路（登录页、账号管理页用）
API_FALLBACKS = ("下载失败", "网络不通", "服务器返回了非 JSON", "请求失败")


def text(name: str) -> str:
    return (JS / name).read_text(encoding="utf-8")


def block(lang: str) -> str:
    src = text("i18n-lexica.js")
    start = src.index("WPI18N.add({")
    mid = src.index("}, {", start)
    end = src.index("  });", mid)
    return src[start:mid] if lang == "zh" else src[mid:end]


def entries(lang: str) -> dict[str, str]:
    return dict(re.findall(r"^    (\w+): '((?:[^'\\]|\\.)*)',$", block(lang), re.M))


def placeholders(value: str) -> set[str]:
    return set(re.findall(r"\{(\w+)\}", value))


def string_literals(source: str):
    """JS 里的字符串字面量（跳过注释、正则）。够用的小词法扫描，不是完整解析。"""
    i, n = 0, len(source)
    prev = ""        # 上一个有意义的字符，用来判断 / 是除号还是正则开头
    while i < n:
        c = source[i]
        if source.startswith("/*", i):
            i = source.index("*/", i) + 2
        elif source.startswith("//", i):
            i = source.find("\n", i)
            i = n if i < 0 else i
        elif c in "'\"":
            j = i + 1
            while source[j] != c:
                j += 2 if source[j] == "\\" else 1
            yield source[i + 1:j]
            i, prev = j + 1, c
        elif c == "/" and prev in "(,=:[!&|?{};\n" + "":
            j = i + 1
            while source[j] != "/" or source[j - 1] == "\\":
                j += 1
            i, prev = j + 1, "/"
        else:
            if not c.isspace():
                prev = c
            i += 1


class TestDictionary(unittest.TestCase):
    def test_both_languages_have_exactly_the_same_keys(self):
        zh, en = entries("zh"), entries("en")
        self.assertGreater(len(zh), 100)
        self.assertEqual(sorted(set(zh) - set(en)), [], "缺英文")
        self.assertEqual(sorted(set(en) - set(zh)), [], "缺中文")

    def test_placeholders_match_between_languages(self):
        zh, en = entries("zh"), entries("en")
        for key in zh:
            self.assertEqual(placeholders(zh[key]), placeholders(en[key]), key)

    def test_no_empty_text_and_no_chinese_in_the_english_table(self):
        for key, value in entries("en").items():
            self.assertTrue(value.strip(), key)
            self.assertIsNone(CJK.search(value), "英文词条里有中文：%s" % key)
        for key, value in entries("zh").items():
            self.assertTrue(value.strip(), key)

    def test_every_key_the_scripts_use_exists_and_every_key_is_used(self):
        defined = set(entries("zh"))
        pattern = re.compile(r"""['"]((?:home|sel|bank|stats|play|g|api)_[A-Za-z0-9_]+)['"]""")
        used = set()
        for name in SCRIPTS:
            used |= set(pattern.findall(text(name)))
        dynamic = {k for k in defined if k.startswith("sel_mode_")}    # selector.js 用 MODE_KEYS 间接引用，上面已经扫到
        for key in used:
            self.assertIn(key, defined, "脚本用了没有定义的词条：%s" % key)
        unused = sorted(defined - used - dynamic)
        self.assertEqual(unused, [], "这些词条没有被任何脚本使用（删掉或接上）")

    def test_the_dictionary_is_loaded_after_i18n_and_before_everything_that_uses_it(self):
        for page in PAGES:
            html = (WEB / page).read_text(encoding="utf-8")
            i18n, lexica = html.index("js/i18n.js"), html.index("js/i18n-lexica.js")
            self.assertLess(i18n, lexica, page)
            for script in re.findall(r'src="/word-puzzle/js/((?!i18n)[a-z0-9-]+\.js)', html):
                self.assertLess(lexica, html.index("js/" + script), "%s 里 %s 应该在词表之后加载" % (page, script))


class TestNoChineseLeftInTheScripts(unittest.TestCase):
    def test_visible_strings_all_go_through_the_dictionary(self):
        for name in SCRIPTS:
            for literal in string_literals(text(name)):
                if not CJK.search(literal) or literal in DATA_LITERALS:
                    continue
                if name == "api.js" and literal.startswith(API_FALLBACKS):
                    continue
                self.fail("%s 里还有没走词条的中文：%r" % (name, literal[:40]))

    def test_the_scanner_itself_finds_chinese_and_skips_comments_and_regexes(self):
        sample = "var a = '你好'; /* 注释 '中' */ // 行注释 '文'\nvar r = /[\"']文/; var b = \"再见\";"
        self.assertEqual([s for s in string_literals(sample)], ["你好", "再见"])


class TestEveryPageCanSwitch(unittest.TestCase):
    def bare_text(self, html: str) -> list[str]:
        parser = TextNodes()
        parser.feed(html)
        # 数字、符号（比如统计里的「—」）不需要翻译；有汉字或英文字母的才算漏
        return [t for t in parser.bad if CJK.search(t) or re.search(r"[A-Za-z]{2,}", t)]

    def test_every_visible_text_on_the_four_pages_has_both_languages(self):
        for page in PAGES:
            html = (WEB / page).read_text(encoding="utf-8")
            self.assertEqual(self.bare_text(html), [], "%s 里有没带中英文属性的文字" % page)

    def test_page_titles_switch_too(self):
        for page in PAGES:
            html = (WEB / page).read_text(encoding="utf-8")
            self.assertRegex(html, r"<title data-module-zh=\"[^\"]+\" data-module-en=\"[^\"]+\">", page)

    def test_the_header_with_the_language_button_is_on_every_page(self):
        for page in PAGES:
            html = (WEB / page).read_text(encoding="utf-8")
            self.assertIn('id="portalHeaderControls"', html, page)
            self.assertIn("/shared/module-header.js", html, page)

    def test_the_header_announces_language_changes(self):
        header = (ROOT.parent / "hub" / "shared" / "module-header.js").read_text(encoding="utf-8")
        self.assertIn("portal-lang-change", header)

    def test_the_offline_page_is_bilingual_and_has_its_own_toggle(self):
        from server import offline
        _, html = offline.build_offline_html(
            {"title": "t", "level1": "a", "level2": "b", "level3": "c", "level4": "d", "word_count": 1},
            [{"unit": "U1", "words": [{"en": "apple", "cn": "苹果"}]}])
        self.assertEqual(self.bare_text(html), [], "离线页里有没带中英文属性的文字")
        for needle in ('id="btn-lang"', "WPI18N.setLang", "var LANG_KEY = 'lg_lang'", "home_play: "):
            self.assertIn(needle, html)
        self.assertLess(html.index("var LANG_KEY"), html.index("WPGameUI = UI") if "WPGameUI = UI" in html else len(html))
        self.assertIn("g_levelBtn", html, "游戏界面的词条要一起内嵌，离线页没有服务器可取")

    def test_the_lexica_name_in_the_page_title_uses_the_english_brand(self):
        self.assertIn("Lexica", (WEB / "index.html").read_text(encoding="utf-8"))


@unittest.skipUnless(NODE, "本机没有 node，跳过 i18n.js 的行为测试")
class TestI18nBehaviour(unittest.TestCase):
    def test_behaviour(self):
        proc = subprocess.run([NODE, str(ROOT / "tests" / "js" / "i18n.test.js")],
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, "中英文切换测试失败：\n" + proc.stdout + proc.stderr)
        self.assertIn("全部通过", proc.stdout)


if __name__ == "__main__":
    unittest.main()
