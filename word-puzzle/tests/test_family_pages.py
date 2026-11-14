"""家庭版 / 班级版页面的静态规范：双语、共用页眉与配色、不写死文字、权限相关的标记，
以及 auth-ui.js 里的跳转安全（用 node 跑，缺 node 时跳过）。"""
from __future__ import annotations

import re
import shutil
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
NODE = shutil.which("node") or shutil.which("nodejs")
NEW_PAGES = {"login.html": "public", "change-password.html": "change", "admin.html": "admin"}
BRAND = {"词", "LEXICA"}          # 品牌标志，不翻译
OLD_PAGES = ("index.html", "bank.html", "play.html", "stats.html")


def read(rel: str) -> str:
    return (WEB / rel).read_text(encoding="utf-8")


class TextNodes(HTMLParser):
    """收集每个可见文字节点，以及它最近的、带 data-module-zh 的祖先。"""

    def __init__(self):
        super().__init__()
        self.stack, self.bad = [], []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "title"):
            self.skip += 1
        if tag not in ("meta", "link", "br", "input", "img", "hr"):
            self.stack.append((tag, dict(attrs)))

    def handle_endtag(self, tag):
        if tag in ("script", "style", "title"):
            self.skip -= 1
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        text = data.strip()
        if not text or self.skip or text in BRAND:
            return
        if not any("data-module-zh" in attrs and "data-module-en" in attrs for _, attrs in self.stack):
            self.bad.append(text)


def dictionary(lang: str) -> str:
    js = read("js/auth-ui.js")
    start = js.index("    %s: {" % lang)
    end = js.index("    en: {") if lang == "zh" else js.index("  function lang()")
    return js[start:end]


def keys(lang: str) -> set[str]:
    return set(re.findall(r"^      (\w+):", dictionary(lang), re.M))


class TestNewPages(unittest.TestCase):
    def test_pages_use_the_shared_header_theme_and_declare_their_access_level(self):
        for page, mode in NEW_PAGES.items():
            html = read(page)
            self.assertIn('<body data-auth="%s">' % mode, html, page)
            self.assertIn('id="portalHeaderControls"', html, page)
            self.assertIn("/shared/module-header.js", html, page)
            self.assertIn("/shared/module-header.css", html, page)
            self.assertIn('name="wp-base"', html, page)
            self.assertIn("css/app.css", html, page)
            self.assertIn("css/auth.css", html, page)
            self.assertLess(html.index("js/api.js"), html.index("js/auth-ui.js"), page)
            self.assertLess(html.index("js/auth-ui.js"), html.index("js/page-"), page)
            self.assertIn('name="robots" content="noindex"', html, page)

    def test_every_visible_string_is_bilingual(self):
        for page in NEW_PAGES:
            parser = TextNodes()
            parser.feed(read(page))
            self.assertEqual(parser.bad, [], "%s 里有没带中英文属性的文字" % page)

    def test_both_languages_have_the_same_keys_and_placeholders(self):
        zh, en = dictionary("zh"), dictionary("en")
        self.assertEqual(keys("zh"), keys("en"))
        self.assertGreater(len(keys("zh")), 40)
        for key in keys("zh"):
            def text(block):
                return re.search(r"^      %s:\s*'(.*)',?$" % key, block, re.M).group(1)
            self.assertEqual(sorted(re.findall(r"\{\w+\}", text(zh))),
                             sorted(re.findall(r"\{\w+\}", text(en))), key)

    def test_every_key_the_scripts_use_exists(self):
        known = keys("zh")
        for js in ("page-login.js", "page-password.js", "page-admin.js", "auth-ui.js"):
            code = re.sub(r"//.*", "", read("js/" + js))
            used = set(re.findall(r"\bt\('(\w+)'", code)) | set(re.findall(r"'(pw[A-Z]\w+)'", code))
            used.discard("err_")                     # t('err_' + code) 是按错误码拼出来的，下面单独检查
            self.assertEqual(used - known, set(), js)
        # 服务端可能返回的错误码都要有译文
        server = (ROOT / "server" / "auth.py").read_text(encoding="utf-8")
        codes = set(re.findall(r'AuthError\(\d+, "(\w+)"', server))
        for code in codes - {"bad_student_no", "bad_name", "bad_field", "exists", "bad_password",
                              "is_admin", "no_user"}:
            self.assertIn("err_" + code, known, "错误码 %s 没有对应译文" % code)

    def test_page_scripts_have_no_hard_coded_chinese_messages(self):
        for js in ("page-login.js", "page-password.js", "page-admin.js"):
            code = re.sub(r"/\*.*?\*/|//.*", "", read("js/" + js), flags=re.S)
            for literal in re.findall(r"'([^'\n]*)'", code):
                self.assertIsNone(re.search(r"[一-龥]", literal), "%s 里有写死的中文：%r" % (js, literal))

    def test_admin_page_escapes_everything_that_comes_from_the_roster(self):
        code = read("js/page-admin.js")
        self.assertIn("var esc = API.esc;", code)
        for field in ("u.student_no", "u.name", "u.class_name", "u.college", "u.department",
                      "u.last_login_at", "res.password", "e.reason", "e.student_no"):
            for hit in re.finditer(re.escape(field), code):
                line = code[code.rfind("\n", 0, hit.start()) + 1: code.find("\n", hit.end())]
                if "innerHTML" in line or "'<" in line or "+ esc(" in line or "esc(" in line:
                    self.assertIn("esc(", line, "%s 进 HTML 之前必须转义：%s" % (field, line.strip()))

    def test_every_input_type_the_new_pages_use_is_styled(self):
        """密码框曾经漏了样式（app.css 只列了 text / number / file），在手机上显示成浏览器默认的小框。"""
        rule = re.search(r"\n(input\[type=text\][^{]*)\{", read("css/app.css")).group(1)
        for page in NEW_PAGES:
            for kind in set(re.findall(r'<input[^>]*type="(\w+)"', read(page))):
                if kind in ("checkbox", "hidden"):
                    continue
                self.assertIn("input[type=%s]" % kind, rule, "%s 里用了 type=%s，但 app.css 没有给它样式" % (page, kind))

    def test_csv_download_guards_against_excel_formulas(self):
        code = read("js/page-admin.js")
        self.assertIn("var FORMULA_PREFIXES = '=+-@';", code)
        self.assertIn("String.fromCharCode(39) + value", code)


class TestExistingPages(unittest.TestCase):
    def test_every_page_loads_auth_ui_after_api(self):
        for page in OLD_PAGES:
            html = read(page)
            self.assertIn("css/auth.css", html, page)
            self.assertLess(html.index("js/api.js"), html.index("js/auth-ui.js"), page)
            self.assertLess(html.index("js/auth-ui.js"), html.index("js/page-") if "js/page-" in html else len(html), page)

    def test_features_students_must_not_see_are_marked(self):
        index, bank = read("index.html"), read("bank.html")
        for needle in ('class="btn lg ghost admin-only" id="btnUpload"', 'class="btn lg ghost admin-only" id="btnOffline"'):
            self.assertIn(needle, index)
        for heading in ("主要操作", "已上传的资料", "已生成的离线测试页"):
            self.assertRegex(bank, r'<div class="card admin-only">\s*<h2[^>]*>%s</h2>' % heading)
        self.assertRegex(bank, r'<div class="field admin-only">\s*<label[^>]*>题源</label>')
        self.assertIn("body.role-student .admin-only", read("css/auth.css"))

    def test_bank_page_only_loads_admin_data_for_admins(self):
        code = read("js/page-bank.js")
        self.assertRegex(code, r"AuthUI\.isAdmin\(\)\)\s*\{\s*loadMaterials\(\);\s*loadFiles\(\);")

    def test_api_wrapper_redirects_instead_of_showing_errors_for_login_problems(self):
        code = read("js/api.js")
        self.assertIn("login_required", code)
        self.assertIn("password_change_required", code)
        self.assertIn("err.code", code)


@unittest.skipUnless(NODE, "本机没有 node，跳过 auth-ui.js 的行为测试")
class TestAuthUiBehaviour(unittest.TestCase):
    def test_safe_next_error_text_and_language(self):
        script = r"""
const fs = require('fs'), vm = require('vm');
const lang = { value: 'zh-CN' };
const sandbox = {
  document: { documentElement: { get lang() { return lang.value; } },
    querySelector: () => ({ content: '/word-puzzle' }), body: { getAttribute: () => 'public', classList: { add() {} } },
    getElementById: () => null },
  API: { get: () => new Promise(() => {}) }, location: { search: '' },
};
sandbox.window = sandbox;
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(process.argv[1], 'utf8'), sandbox);
const A = sandbox.AuthUI, bad = [];
const check = (name, ok) => { if (!ok) bad.push(name); };
// 登录后的跳转：只允许本站路径
const home = '/word-puzzle/';
for (const evil of ['//evil.com', 'https://evil.com/word-puzzle/', '/\\evil.com', 'javascript:alert(1)', '/word-puzzle/../admin',
                    '/word-puzzle//evil.com', '/other/page', '', null, undefined, '/word-puzzle/x"onload="y'])
  check('拒绝 ' + evil, A.safeNext(evil) === home);
for (const good of ['/word-puzzle/bank.html', '/word-puzzle/play.html?bank=12', '/word-puzzle/stats.html'])
  check('放行 ' + good, A.safeNext(good) === good);
// 文字：随页面语言切换，缺的键退回中文再退回键名
check('zh', A.t('signOut') === '退出');
lang.value = 'en';
check('en', A.t('signOut') === 'Sign out');
check('vars', A.t('importDone', { created: 3, updated: 1, skipped: 2 }) === 'Created 3, updated 1, skipped 2');
check('missing key', A.t('no_such_key') === 'no_such_key');
// 服务端错误按 code 翻译
check('code en', A.errorText({ code: 'invalid_credentials' }).startsWith('Wrong student number'));
lang.value = 'zh-CN';
check('code zh', A.errorText({ code: 'invalid_credentials' }).startsWith('学号或密码不对'));
check('unknown code falls back to message', A.errorText({ code: 'zzz', message: '原文' }) === '原文');
check('network', A.errorText({ network: true }) === A.t('err_network'));
check('empty', A.errorText(null) === A.t('err_generic'));
if (bad.length) { console.error(bad.join('\n')); process.exit(1); }
console.log('ok');
"""
        proc = subprocess.run([NODE, "-e", script, str(WEB / "js" / "auth-ui.js")],
                              capture_output=True, text=True, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


@unittest.skipUnless(NODE, "本机没有 node，跳过 CSV 单元格函数的行为测试")
class TestCredentialsCsvCell(unittest.TestCase):
    JS = r'''
const fs = require('fs');
const src = fs.readFileSync(process.argv[1], 'utf8');
eval(src.match(/var FORMULA_PREFIXES[\s\S]*?function csvCell[\s\S]*?\n  }\n/)[0] + ';globalThis.csvCell = csvCell');
const cases = [['=SUM(1)', "'=SUM(1)"], ['+1', "'+1"], ['-x', "'-x"], ['@a', "'@a"], ['张三', '张三'],
  ['a,b', '"a,b"'], ['say "hi"', '"say ""hi"""'], ['l1\nl2', '"l1\nl2"'], ['', ''], [null, ''], ['=a,b', '"\'=a,b"']];
const bad = cases.filter(([i, o]) => csvCell(i) !== o).map(([i]) => JSON.stringify(i));
if (bad.length) { console.error('FAIL ' + bad.join(' ')); process.exit(1); }
'''

    def test_csv_cell_quotes_and_defuses_formulas(self):
        proc = subprocess.run([NODE, "-e", self.JS, str(WEB / "js" / "page-admin.js")],
                              capture_output=True, text=True, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()


class TestFavicon(unittest.TestCase):
    """词境的 logo 来自 miniprogram/design/icon.svg；网站每个页面都要引用它，标签页和手机桌面才有图标。"""

    def test_every_page_links_the_icons_and_the_files_exist(self):
        web = WEB
        for page in sorted(p.name for p in web.glob("*.html")):
            html = read(page)
            for href in ("/word-puzzle/img/icon.svg", "/word-puzzle/img/icon-512.png",
                         "/word-puzzle/img/apple-touch-icon.png"):
                self.assertIn('href="%s"' % href, html, page)
        for name in ("icon.svg", "icon-512.png", "apple-touch-icon.png"):
            self.assertGreater((web / "img" / name).stat().st_size, 1000, name)

    def test_the_png_icons_have_the_expected_size(self):
        import struct
        for name, size in (("icon-512.png", 512), ("apple-touch-icon.png", 180)):
            head = (ROOT / "web" / "img" / name).read_bytes()[:24]
            self.assertEqual(head[:8], b"\x89PNG\r\n\x1a\n", name)
            self.assertEqual(struct.unpack(">II", head[16:24]), (size, size), name)


class TestBrandLogo(unittest.TestCase):
    """页头左上角的品牌方块用词境 logo 图片，不再是文字“词”。"""

    def test_every_page_header_uses_the_logo_image(self):
        for page in sorted(p.name for p in WEB.glob("*.html")):
            html = read(page)
            self.assertIn("portal-brand-mark--logo", html, page)
            self.assertIn('src="/word-puzzle/img/icon.svg"', html, page)
            self.assertNotIn('aria-hidden="true">词</span>', html, page)
            self.assertIn("module-header.css?v=20261113-logo", html, page)   # 改了共享样式，要换版本号绕开缓存

    def test_the_modifier_exists_in_the_shared_stylesheet(self):
        css = (ROOT.parent / "hub" / "shared" / "module-header.css").read_text(encoding="utf-8")
        self.assertIn(".portal-brand-mark--logo img", css)


class TestStudentViewIsWired(unittest.TestCase):
    """服务端会拒绝学生的管理操作；这里保证页面也不把用不了的入口摆给学生。"""

    def test_the_workbench_link_is_teacher_only_everywhere_and_the_page_is_an_admin_page(self):
        for page in sorted(p.name for p in WEB.glob("*.html")):
            html = read(page)
            for link in re.findall(r'<a [^>]*href="/word-puzzle/bank\.html"[^>]*>', html):
                self.assertIn("admin-only", link, page)
        self.assertIn('<body data-auth="admin">', read("bank.html"))

    def test_the_home_page_hides_generating_and_offline_from_students(self):
        html = read("index.html")
        self.assertIn('class="card admin-only" id="defaultCard"', html)
        self.assertRegex(html, r'<div class="card admin-only">\s*<h2[^>]*>按层级生成题库</h2>')
        self.assertIn('class="student-only"', html)
        self.assertRegex(html, r'<span class="admin-only"[^>]*>离线测试页是单个 HTML 文件')

    def test_a_student_login_switches_the_view_on(self):
        ui = (WEB / "js" / "auth-ui.js").read_text(encoding="utf-8")
        self.assertIn("document.body.classList.add('role-student')", ui)
        css = (WEB / "css" / "auth.css").read_text(encoding="utf-8")
        self.assertIn("body.role-student .admin-only { display: none !important; }", css)
        self.assertIn("body.role-student .student-only", css)

    def test_the_home_page_waits_for_the_role_and_groups_by_category(self):
        js = (WEB / "js" / "page-home.js").read_text(encoding="utf-8")
        self.assertIn("AuthUI.ready.then", js)
        self.assertIn("groupByCategory", js)
        self.assertIn("/meta", js)
        self.assertIn("home_emptyStudent", js)
        self.assertIn("老师还没有给你开放题库", (WEB / "js" / "i18n-lexica.js").read_text(encoding="utf-8"))

    def test_the_admin_page_has_a_tag_column_and_bulk_buttons(self):
        html = read("admin.html")
        for needle in ('id="bulkTags"', 'id="btnBulkAdd"', 'id="btnBulkRemove"', 'data-module-en="Tags"'):
            self.assertIn(needle, html)
        self.assertEqual(html.count("<th "), 11, "表头列数要和 page-admin.js 里的 colspan 一致")
        self.assertIn('colspan="11"', (WEB / "js" / "page-admin.js").read_text(encoding="utf-8"))
