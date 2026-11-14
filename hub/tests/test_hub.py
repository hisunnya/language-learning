"""总主页（hub/）的样式规范测试。

仓库根目录的 AGENTS.md §3 要求每个页面都做到：

* 中英双语可切换，文案全部走 ``data-i18n``；
* 至少三套配色，每套都是独立的 CSS 变量集；
* 配色选择器是对角切两半的小方块，右上主色、左下底色；
* 语言和配色都记在 localStorage 里。

这个文件就是这些约定的「守门员」——违反了必须**测试失败**，
不能悄悄发布。

跑法::

    python3 -m unittest discover -s hub/tests -v
"""
from __future__ import annotations

import re
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

HUB = Path(__file__).resolve().parent.parent
ROOT = HUB.parent

HTML = (HUB / "index.html").read_text(encoding="utf-8")
CSS = (HUB / "css" / "hub.css").read_text(encoding="utf-8")
JS = (HUB / "js" / "hub.js").read_text(encoding="utf-8")
CONFIG = (HUB / "js" / "config.js").read_text(encoding="utf-8")
NGINX = (HUB / "deploy" / "lingua-grove.conf").read_text(encoding="utf-8")
INSTALL_SCRIPT = (HUB / "deploy" / "install.sh").read_text(encoding="utf-8")

# i18n 表在 JS 里，形如  "key": "value",
_I18N_ENTRY_RE = re.compile(r'"([A-Za-z0-9_.]+)"\s*:\s*"((?:[^"\\]|\\.)*)"')

# 这些标签里出现的文字算「界面文案」，必须走 data-i18n
TEXT_TAGS = {"button", "a", "h1", "h2", "h3", "p", "li", "span", "b", "em", "label"}


class _Collector(HTMLParser):
    """收集每个元素的**直接文字**（不含子元素里的）。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[dict] = []
        self.records: list[dict] = []   # {tag, attrs, text, depth}
        self.buttons: list[dict] = []  # {attrs, inner_html}

    def handle_starttag(self, tag, attrs):
        attrd = {k: (v or "") for k, v in attrs}
        self.stack.append({"tag": tag, "attrs": attrd, "text": []})
        if tag == "button":
            self.buttons.append({"attrs": attrd, "inner": []})

    def handle_startendtag(self, tag, attrs):
        attrd = {k: (v or "") for k, v in attrs}
        if tag == "button":
            self.buttons.append({"attrs": attrd, "inner": []})

    def handle_endtag(self, tag):
        while self.stack:
            item = self.stack.pop()
            self.records.append({
                "tag": item["tag"],
                "attrs": item["attrs"],
                "text": "".join(item["text"]).strip(),
            })
            if item["tag"] == "button" and self.buttons:
                self.buttons[-1]["inner"].append("")
            if not self.stack:
                break

    def handle_data(self, data):
        if self.stack:
            self.stack[-1]["text"].append(data)
        if self.buttons:
            self.buttons[-1]["inner"].append(data)


def _parse() -> _Collector:
    c = _Collector()
    c.feed(HTML)
    c.close()
    return c


def _i18n_block(lang: str) -> str:
    """截出 i18n 表里某个语言的那一段。"""
    start = JS.find("%s: {" % lang)
    if start < 0:
        return ""
    depth = 0
    for i in range(start, len(JS)):
        if JS[i] == "{":
            depth += 1
        elif JS[i] == "}":
            depth -= 1
            if depth == 0:
                return JS[start:i + 1]
    return ""


def _i18n_keys(lang: str) -> set[str]:
    block = _i18n_block(lang)
    return {m.group(1) for m in _I18N_ENTRY_RE.finditer(block)}


def _is_real_text(text: str) -> bool:
    """是不是「界面文案」——至少两个字母或汉字。"""
    return bool(re.search(r"[一-鿿A-Za-z]{2,}", text))


class TestBilingual(unittest.TestCase):
    """§3.1 中英双语。"""

    def test_both_dictionaries_exist(self):
        self.assertTrue(_i18n_keys("zh"), "找不到中文词表")
        self.assertTrue(_i18n_keys("en"), "找不到英文词表")

    def test_dictionaries_have_the_same_keys(self):
        zh = _i18n_keys("zh")
        en = _i18n_keys("en")
        self.assertEqual(zh - en, set(), "中文有、英文缺的键：%s" % (zh - en))
        self.assertEqual(en - zh, set(), "英文有、中文缺的键：%s" % (en - zh))

    def test_every_data_i18n_key_is_translated(self):
        """HTML 里用到的每个 data-i18n 键，中英文都要有。"""
        used = set(re.findall(r'data-i18n="([^"]+)"', HTML))
        self.assertTrue(used, "页面里一个 data-i18n 都没有")
        for lang in ("zh", "en"):
            missing = used - _i18n_keys(lang)
            self.assertEqual(missing, set(),
                             "%s 缺少这些文案：%s" % (lang, sorted(missing)))

    def test_no_hardcoded_user_visible_text(self):
        """标签里的直接可见文字必须带 data-i18n，否则切了语言还是中文。"""
        offenders = []
        for rec in _parse().records:
            if rec["tag"] not in TEXT_TAGS:
                continue
            text = rec["text"]
            if not _is_real_text(text):
                continue
            attrs = rec["attrs"]
            if "data-i18n" in attrs:
                continue
            # 纯装饰（aria-hidden）不算文案
            if attrs.get("aria-hidden") == "true":
                continue
            # 语言切换里的「中 / EN」是刻意的两语文案
            if attrs.get("class", "") in ("lang-btn-zh", "lang-btn-en"):
                continue
            offenders.append("%s: %r" % (rec["tag"], text))
        self.assertEqual(offenders, [],
                         "这些文字没有走 data-i18n：%s" % offenders)

    def test_controls_have_visible_text(self):
        """每个按钮都要有可见文字或有可访问名称，不能是个空盒子。"""
        empty = []
        for btn in _parse().buttons:
            attrs = btn["attrs"]
            inner = "".join(btn["inner"]).strip()
            has_text = _is_real_text(inner)
            has_i18n = "data-i18n" in attrs
            has_label = bool(attrs.get("aria-label", "").strip())
            # 色块按钮是纯图标，靠 aria-label 认
            if not (has_text or has_i18n or has_label):
                empty.append(str(attrs))
        self.assertEqual(empty, [], "这些按钮没有可见文字：%s" % empty)

    def test_language_reflected_on_html_element(self):
        self.assertRegex(HTML, r'<html[^>]*\slang="[^"]+"')

    def test_lang_is_persisted(self):
        self.assertIn("localStorage", JS)
        self.assertIn("lg_lang", JS)


class TestPalettes(unittest.TestCase):
    """§3.2 多套配色。"""

    def _theme_blocks(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for m in re.finditer(r'\[data-theme="([a-z0-9_-]+)"\]\s*\{(.*?)\}', CSS, re.S):
            out[m.group(1)] = m.group(2)
        return out

    def test_at_least_three_palettes(self):
        blocks = self._theme_blocks()
        self.assertGreaterEqual(len(blocks), 3,
                                "至少要有三套配色，现在只有 %d 套" % len(blocks))

    def test_every_palette_defines_the_same_variable_set(self):
        """每套配色都必须有完整的一套变量，缺一个就不算一套配色。"""
        blocks = self._theme_blocks()
        sets = {}
        for name, body in blocks.items():
            sets[name] = set(re.findall(r"(--[a-z0-9-]+)\s*:", body))
        self.assertTrue(sets)
        reference = set(sets[next(iter(sets))])
        self.assertGreaterEqual(len(reference), 10,
                                "配色变量太少：%s" % sorted(reference))
        for name, vars_ in sets.items():
            missing = reference - vars_
            self.assertEqual(missing, set(),
                             "配色 %s 少了这些变量：%s" % (name, sorted(missing)))

    def test_palettes_are_actually_different(self):
        """五套配色的主色不能是同一个 —— 否则换了个寂寞。"""
        blocks = self._theme_blocks()
        accents = {}
        for name, body in blocks.items():
            m = re.search(r"--accent:\s*(#[0-9a-fA-F]{3,8})", body)
            self.assertIsNotNone(m, "配色 %s 没有 --accent" % name)
            accents[name] = m.group(1).lower()
        self.assertEqual(len(set(accents.values())), len(accents),
                         "有配色共用同一个主色：%s" % accents)

    def test_theme_is_persisted(self):
        self.assertIn("localStorage", JS)
        self.assertIn("lg_theme", JS)


class TestPalettePicker(unittest.TestCase):
    """§3.3 配色选择器的样式。"""

    def _swatches(self) -> list[str]:
        return re.findall(r'<span class="swatch"[^>]*>', HTML)

    def test_picker_exists_in_header(self):
        head = HTML.split("</header>")[0]
        self.assertIn("theme-picker", head, "配色选择器要在 header 里")
        self.assertIn("langBtn", head, "语言切换要和配色选择器挨着")

    def test_every_chip_has_its_own_two_colours(self):
        """每个色块都要带自己那套配色��主色和底色。"""
        chips = re.findall(r'<button[^>]*class="theme-chip"[^>]*>.*?</button>', HTML, re.S)
        self.assertGreaterEqual(len(chips), 3)
        for chip in chips:
            self.assertIn("--swatch-main", chip, "色块缺主色：%s" % chip[:80])
            self.assertIn("--swatch-bg", chip, "色块缺底色：%s" % chip[:80])

    def test_swatches_are_not_identical(self):
        """两个色块的主色不能一样，否则分不清。"""
        mains = re.findall(r"--swatch-main:\s*(#[0-9a-fA-F]{3,8})", HTML)
        self.assertGreaterEqual(len(mains), 3)
        self.assertEqual(len(set(m.lower() for m in mains)), len(mains),
                         "有重复的色块主色：%s" % mains)

    def test_split_is_a_hard_stop_diagonal(self):
        """对角切两半必须是硬边渐变：0 50% → 50% 100%。"""
        m = re.search(r"\.swatch\s*\{(.*?)\}", CSS, re.S)
        self.assertIsNotNone(m, "CSS 里找不到 .swatch")
        body = m.group(1)
        self.assertIn("linear-gradient", body)
        self.assertIn("to top right", body)
        self.assertRegex(body, r"0\s+50%")
        self.assertRegex(body, r"50%\s+100%")

    def test_swatch_is_a_square_not_a_circle(self):
        m = re.search(r"\.swatch\s*\{(.*?)\}", CSS, re.S)
        body = m.group(1)
        w = re.search(r"width:\s*(\d+)px", body)
        h = re.search(r"height:\s*(\d+)px", body)
        self.assertIsNotNone(w) and self.assertIsNotNone(h)
        self.assertEqual(w.group(1), h.group(1), "色块必须是正方形")
        radius = re.search(r"border-radius:\s*([^;]+);", body)
        self.assertIsNotNone(radius)
        self.assertNotIn("50%", radius.group(1), "色块不能是圆的")
        self.assertIn("4px", radius.group(1), "色块圆角用 4px")

    def test_chips_have_bilingual_tooltips(self):
        for chip in re.findall(r'<button[^>]*class="theme-chip"[^>]*>', HTML):
            self.assertIn("data-tooltip-zh", chip)
            self.assertIn("data-tooltip-en", chip)
            self.assertIn("aria-pressed", chip, "色块要标出当前选中项")


class TestProjectLinks(unittest.TestCase):
    """三个项目的入口都要在。"""

    def test_homepage_hides_explanatory_notes(self):
        self.assertNotIn('<section class="notes">', HTML)

    def test_project_entry_buttons_are_large(self):
        m = re.search(r"\.btn\s*\{(.*?)\n\}", CSS, re.S)
        self.assertIsNotNone(m)
        self.assertIn("min-height: 72px", m.group(1))
        self.assertIn("font-size: 21px", m.group(1))

    def test_english_chemistry_and_physics_come_first(self):
        order = re.findall(r'<article class="project" data-project="(\w+)"', HTML)
        self.assertEqual(order[:3], ["lexica", "chemistry", "physics"])
        self.assertEqual(sorted(order), sorted(["lexica", "topics", "ham", "chemistry", "physics"]))

    def test_five_projects_present(self):
        for key in ("lexica", "topics", "ham", "chemistry", "physics"):
            self.assertIn('data-project-link="%s"' % key, HTML)

    def test_config_has_all_five(self):
        for key in ("lexica", "topics", "ham", "chemistry", "physics"):
            self.assertRegex(CONFIG, r"%s\s*:" % key,
                             "config.js 里少了 %s 的地址" % key)

    def test_links_are_overridable(self):
        """地址写在 config.js 里，而不是写死在 HTML 里。"""
        self.assertIn("LINGUA_PROJECTS", CONFIG)
        self.assertIn("LINGUA_PROJECTS", JS)


class TestDeployment(unittest.TestCase):
    """The portal is the port-80 entry point for all three projects."""

    def test_other_projects_can_add_locations_through_tv_inc_files(self):
        """tv-m3u 这类独立项目把自己的 location 放在 conf.d/tv-*.inc 里，由这个入口 include。
        这一行如果不在仓库模板里，下次 deploy-all 会把生产上手工加的那行覆盖掉，/tv/ 就失效了。"""
        self.assertEqual(NGINX.count("include /etc/nginx/conf.d/tv-*.inc;"), 1)
        server = NGINX[NGINX.index("\nserver {"):]
        self.assertLess(server.index("server_name"), server.index("tv-*.inc"), "include 要在 server 块里、server_name 之后")
        self.assertLess(server.index("tv-*.inc"), server.index("location "), "include 要在第一个 location 之前")

    def test_the_installer_never_deletes_inc_files_from_conf_d(self):
        install = (HUB / "deploy" / "install.sh").read_text(encoding="utf-8")
        for line in install.splitlines():
            if re.search(r"\brm\b", line):
                self.assertNotIn("*.inc", line, line)
                self.assertNotIn("conf.d/*", line, line)
                self.assertNotIn("tv-", line, line)

    def test_nginx_accepts_the_include_when_no_tv_file_exists(self):
        import shutil, subprocess, tempfile
        nginx = shutil.which("nginx")
        if not nginx:
            self.skipTest("本机没有 nginx")
        with tempfile.TemporaryDirectory() as tmp:
            conf = Path(tmp) / "nginx.conf"
            conf.write_text("pid %s/n.pid;\nerror_log %s/e.log;\nevents {}\nhttp {\n"
                            "  client_body_temp_path %s/b; proxy_temp_path %s/p; fastcgi_temp_path %s/f;\n"
                            "  uwsgi_temp_path %s/u; scgi_temp_path %s/s;\n  access_log off;\n"
                            "  server {\n    listen 127.0.0.1:18099;\n    include %s/no-such-dir/tv-*.inc;\n"
                            "    location / { return 200 ok; }\n  }\n}\n" % ((tmp,) * 8), encoding="utf-8")
            proc = subprocess.run([nginx, "-t", "-c", str(conf), "-p", tmp], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_port_80_serves_the_hub_for_a_configured_host(self):
        self.assertIn("listen 80;", NGINX)
        self.assertIn("server_name __LINGUA_SERVER_NAME__;", NGINX)
        self.assertIn("root /var/www/lingua-grove;", NGINX)

    def test_static_apps_are_mounted_under_the_hub(self):
        self.assertIn("location ^~ /topics/", NGINX)
        self.assertIn("alias /var/www/topic-app/;", NGINX)
        self.assertIn("location ^~ /ham/", NGINX)
        self.assertIn("alias /var/www/ham-exam/;", NGINX)
        self.assertIn("location ^~ /chemistry/", NGINX)
        self.assertIn("alias /var/www/chemistry/;", NGINX)
        self.assertIn("location ^~ /physics/", NGINX)
        self.assertIn("alias /var/www/physics/;", NGINX)

    def test_mounts_without_trailing_slash_redirect(self):
        for name in ("topics", "ham", "chemistry", "physics", "word-puzzle"):
            self.assertIn("location = /%s {\n        return 301 /%s/;" % (name, name), NGINX)

    def test_whole_site_script_retries_smoke_checks_and_covers_every_module(self):
        scripts = sorted(HUB.parent.glob("deploy-all-*.sh"))
        self.assertEqual(len(scripts), 1, "根目录只保留一份带时间戳的整站部署脚本")
        text = scripts[0].read_text(encoding="utf-8")
        self.assertIn("retry ", text)   # nginx reload 是异步的，冒烟检查要重试
        for path in ("/chemistry/", "/chemistry/data/chemistry.json", "/physics/",
                     "/physics/data/physics.json", "/physics/js/physics-core.js", "/ham/",
                     "/topics/", "/word-puzzle/api/health"):
            self.assertIn(path, text)

    def test_assets_are_not_cached_for_days(self):
        """改了样式部署后必须立刻看得到：不能再缓存 7 天。"""
        self.assertNotIn("expires 7d", NGINX)
        self.assertNotIn("max-age=604800", NGINX)
        for mount in ("/topics/", "/ham/", "/chemistry/", "/physics/", "/shared/"):
            block = re.search(r"location \^~ %s \{(.*?)\n    \}" % re.escape(mount), NGINX, re.S)
            self.assertIsNotNone(block, mount)
            self.assertIn('Cache-Control "no-cache"', block.group(1), mount)
        self.assertRegex(NGINX, r"location ~\* \\\.\(css\|js\)\$ \{[^}]*no-cache")

    def test_hub_assets_carry_a_per_deploy_version(self):
        for asset in ("css/hub.css", "js/config.js", "js/hub.js"):
            self.assertIn(asset + "?v=__ASSET_VERSION__", HTML)
        script = (HUB / "deploy" / "install.sh").read_text(encoding="utf-8")
        self.assertIn("__ASSET_VERSION__", script)
        self.assertIn('"$HUB_ROOT/index.html"', script)

    def test_installer_does_not_publish_physics_tests(self):
        script = (HUB / "deploy" / "install.sh").read_text(encoding="utf-8")
        self.assertNotIn('physics/." ', script)
        self.assertIn('physics/js"', script)
        self.assertIn('physics/data"', script)

    def test_installer_does_not_publish_chemistry_tests(self):
        script = (HUB / "deploy" / "install.sh").read_text(encoding="utf-8")
        self.assertNotIn('chemistry/." ', script)
        self.assertIn('chemistry/js"', script)
        self.assertIn('LINGUA_SERVER_NAME:-10.1.1.93', script)

    def test_shared_module_header_assets_have_a_common_url(self):
        self.assertIn("location ^~ /shared/", NGINX)
        self.assertTrue((HUB / "shared" / "module-header.css").exists())
        self.assertTrue((HUB / "shared" / "module-header.js").exists())

    def test_lexica_is_mounted_under_word_puzzle_with_api_proxy(self):
        self.assertIn("location ^~ /word-puzzle/", NGINX)
        self.assertIn("alias /srv/word-puzzle/web/;", NGINX)
        self.assertIn("location ^~ /word-puzzle/api/", NGINX)
        self.assertIn("proxy_pass http://lexica_api/api/;", NGINX)
        self.assertIn("client_max_body_size 32m;", NGINX)
        self.assertIn('lexica: "/word-puzzle/"', CONFIG)

    def test_installer_replaces_the_standalone_port_80_site(self):
        self.assertIn("sites-enabled/word-puzzle.conf", INSTALL_SCRIPT)
        self.assertIn("__LINGUA_SERVER_NAME__", INSTALL_SCRIPT)
        self.assertIn("nginx -t", INSTALL_SCRIPT)

    def test_lexica_copy_uses_volume_terminology_without_fixed_server_ip(self):
        self.assertIn("册别", JS)
        self.assertIn("volume", JS)
        self.assertNotIn("10.1.1.93", JS)


if __name__ == "__main__":
    unittest.main()
