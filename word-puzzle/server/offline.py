"""生成「单文件离线测试页」。

产物和老的 ``Unit1单词消消乐.html`` 一样：一个 HTML 文件，词表、样式、脚本
全部内联，双击就能用，不联网。

文件名规则：**层级 + 日期 + 时间.html**
    初中-九年级-上册-全部单元-20261104-153012.html

层级取自题库的 level1~level4（已经含自定义名称）。
"""
from __future__ import annotations

import json
import base64
import re
import time
from pathlib import Path
from typing import Any

from . import tts

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
CSS_FILE = WEB / "css" / "game.css"
CORE_FILE = WEB / "js" / "game-core.js"
I18N_FILE = WEB / "js" / "i18n.js"
I18N_TEXT_FILE = WEB / "js" / "i18n-lexica.js"
UI_FILE = WEB / "js" / "game-ui.js"
ADAPTER_FILE = WEB / "js" / "game-adapter-offline.js"
APP_CSS_FILE = WEB / "css" / "app.css"
THEME_JS_FILE = WEB / "js" / "offline-theme.js"
THEME_CSS_FILE = WEB / "css" / "offline-theme.css"
PRACTICE_CSS_FILE = WEB / "css" / "practice.css"
PRACTICE_UI_FILE = WEB / "js" / "practice-ui.js"
ITEMS_CSS_FILE = WEB / "css" / "items.css"
ITEM_CORE_FILE = WEB / "js" / "item-core.js"
ITEM_UI_FILES = {"spell": WEB / "js" / "spell-ui.js", "order": WEB / "js" / "order-ui.js",
                 "verb": WEB / "js" / "verb-ui.js"}
ITEM_KIND_NAMES = {"spell": "单词大比拼", "order": "翻译排排坐", "verb": "动词猎手"}

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="generator" content="word-puzzle offline generator">
<title>{title}</title>
<style>
{css}
{theme_css}
</style>
<script>
{theme_js}
WPTheme.early();
</script>
</head>
<body>
<div class="app">
  <div class="hud">
    <div class="hud-row">
      <div class="stat"><span class="k" data-module-zh="关卡" data-module-en="Level">关卡</span><span class="v" id="s-level">1/{levels}</span></div>
      <div class="stat time" id="s-timebox"><span class="k" data-module-zh="剩余" data-module-en="Time">剩余</span><span class="v" id="s-time">60</span></div>
      <div class="stat"><span class="k" data-module-zh="进度" data-module-en="Progress">进度</span><span class="v" id="s-prog">0/8</span></div>
      <div class="stat score"><span class="k" data-module-zh="得分" data-module-en="Score">得分</span><span class="v" id="s-score">0</span></div>
      <div class="stat"><span class="k" data-module-zh="连击" data-module-en="Combo">连击</span><span class="v" id="s-combo">0</span></div>
    </div>
    <div class="progress"><i id="s-bar"></i></div>
    <div class="ptext"><span id="s-tip" data-module-zh="点任意一张卡片，再点另一侧配对" data-module-en="Tap any card, then tap one on the other side to match">点任意一张卡片，再点另一侧配对</span><span id="s-total" data-module-zh="总分 0" data-module-en="Total 0">总分 0</span></div>
  </div>
  <div class="board" id="board"></div>
  <div class="bar">
    <button class="btn ghost sm" id="btn-help" data-module-zh="玩法" data-module-en="How to play">玩法</button>
    <button class="btn ghost sm" id="btn-full" data-module-zh="全屏" data-module-en="Full screen">全屏</button>
    <button class="btn warn" id="btn-replay" data-module-zh="重玩本关" data-module-en="Replay level">重玩本关</button>
    <button class="btn" id="btn-restart" data-module-zh="从头开始" data-module-en="Start over">从头开始</button>
    <button class="btn ghost sm" id="btn-lang" data-module-zh="English" data-module-en="中文">English</button>
    <span id="offline-theme"></span>
  </div>
</div>
<div id="fx"></div>
<div class="toast" id="toast"></div>
<div class="overlay" id="overlay"><div class="panel" id="panel"></div></div>

<script>
/* ---------------- 词表数据 ---------------- */
var WP_DATA = {data};
</script>
<script>
{core}
</script>
<script>
{i18n}
</script>
<script>
{i18n_text}
</script>
<script>
{ui}
</script>
<script>
{adapter}
</script>
<script>
/* ---------------- 启动 ---------------- */
(function () {{
  var langButton = document.getElementById('btn-lang');
  if (langButton) langButton.onclick = function () {{
    WPI18N.setLang(WPI18N.lang() === 'en' ? 'zh' : 'en');
  }};
  WPTheme.init(document.getElementById('offline-theme'));
  var game = new WPGame.Game({{ levels: WP_DATA.levels }});
  WPGameUI.init({{
    game: game,
    title: WP_DATA.title,
    subtitle: WP_DATA.subtitle,
    pickUnit: WP_DATA.pickUnit,    wordTotal: WP_DATA.wordTotal,    homeExtra: WP_DATA.homeExtra,
    audio: WP_DATA.audio,
    backHref: WP_DATA.backHref,
    onFinish: function (report) {{
      WPAdapter.save(report, WP_DATA.meta);
    }}
  }});
}})();
</script>
</body>
</html>
"""


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def safe_filename(text: str, fallback: str = "题库") -> str:
    s = re.sub(r"[/\\:*?\"<>|\r\n\t]+", "-", str(text or "")).strip()
    s = re.sub(r"\s+", " ", s)
    s = s.replace(" ", "")
    return s or fallback


def build_filename(bank: dict, when: time.struct_time | None = None, kind: str = "game") -> str:
    """层级 + 日期 + 时间。例：初中-九年级-上册-全部单元-20261104-153012.html
    读音练习的文件名在层级后面多一段「读音练习」，和配对游戏的离线页一眼分得开。"""
    tm = when or time.localtime()
    parts = [
        safe_filename(bank.get("level1", ""), "层级1"),
        safe_filename(bank.get("level2", ""), "层级2"),
        safe_filename(bank.get("level3", ""), "层级3"),
        safe_filename(bank.get("level4", ""), "层级4"),
    ]
    if kind == "practice":
        parts.append("读音练习")
    elif kind in ITEM_KIND_NAMES:
        parts.append(ITEM_KIND_NAMES[kind])
    parts.append(time.strftime("%Y%m%d", tm))
    parts.append(time.strftime("%H%M%S", tm))
    return "-".join(parts) + ".html"


def build_levels(groups: list[dict]) -> list[dict]:
    """把后端的分组数据转成游戏需要的关卡结构。"""
    out = []
    for i, g in enumerate(groups):
        words = [{
            "en": w["en"],
            "cn": w["cn"],
            "ipa": w.get("ipa", ""),
        } for w in g.get("words", [])]
        if not words:
            continue
        out.append({
            "name": g.get("unit") or ("第 %d 关" % (i + 1)),
            "words": words,
        })
    return out


def build_offline_html(bank: dict, groups: list[dict],
                       when: time.struct_time | None = None,
                       audio: dict[str, bytes] | None = None,
                       back_href: str = "") -> tuple[str, str]:
    """返回 ``(文件名, HTML 内容)``。"""
    levels = build_levels(groups)
    if not levels:
        raise ValueError("题库里没有单词，无法生成离线测试页")

    total = bank.get("word_count") or sum(len(l["words"]) for l in levels)
    title = bank.get("title") or "词境 Lexica"
    subtitle = " · ".join([
        bank.get("level1", ""), bank.get("level2", ""),
        bank.get("level3", ""), bank.get("level4", ""),
    ]).strip(" ·")

    embedded_audio = {}
    for word, clip in (audio or {}).items():
        if clip:
            key = _audio_slug(word)
            mime = tts.content_type(clip)
            encoded = base64.b64encode(clip).decode("ascii")
            embedded_audio[key] = f"data:{mime};base64,{encoded}"

    data = {
        "title": title,
        "subtitle": subtitle or "离线测试题",
        "levels": levels,
        "pickUnit": bank.get("unit_mode") == "per-unit",
        "wordTotal": total,
        "homeExtra": "",
        "audio": embedded_audio,
        "backHref": back_href,
        "meta": {
            "title": title,
            "bank_id": bank.get("id"),
            "generated": time.strftime("%Y-%m-%d %H:%M:%S", when or time.localtime()),
            "word_count": total,
        },
    }

    html = TEMPLATE.format(
        title=_escape(title),
        css=_read(CSS_FILE),
        theme_css=_read(THEME_CSS_FILE),
        theme_js=_read(THEME_JS_FILE),
        core=_read(CORE_FILE),
        i18n=_read(I18N_FILE),
        i18n_text=_read(I18N_TEXT_FILE),
        ui=_read(UI_FILE),
        adapter=_read(ADAPTER_FILE),
        data=_json_for_script(data),
        levels=len(levels),
    )
    return build_filename(bank, when), html


PRACTICE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="generator" content="word-puzzle offline generator">
<title>{title}</title>
<style>
/* 默认值（靛蓝）；五套配色在下面 html[data-theme=…] 里，页面一打开按上次的选择设好 */
:root {{ --card:#fff; --bg1:#f4f6fb; --ink:#172033; --ink2:#68758a; --ink3:#8793a7; --heading:#1e1b4b; --line:#dce3ef; --soft-line:#e6ebf7;
  --blue:#4f46e5; --blue-l:#eef2ff; --orange:#d97706; --on-primary:#fff; }}
{themes}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--bg1); color: var(--ink); font: 15px/1.5 -apple-system, "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif; }}
.wrap {{ max-width: 760px; margin: 0 auto; padding: 14px 14px 40px; }}
h1 {{ font-size: 20px; margin: 6px 0 2px; color: var(--heading); }}
.sub {{ margin: 0 0 8px; color: var(--ink2); font-size: 13px; }}
.btn {{ appearance: none; border: 1px solid var(--blue); background: var(--blue); color: var(--on-primary); border-radius: 10px; padding: 8px 14px; font: inherit; font-weight: 700; cursor: pointer; }}
.btn.ghost {{ background: var(--card); color: var(--ink2); border-color: var(--line); }}
.hint {{ font-size: 12px; color: var(--ink2); margin: 6px 0 10px; line-height: 1.6; }}
.toast {{ position: fixed; left: 50%; bottom: 24px; transform: translateX(-50%); background: var(--heading); color: var(--card); padding: 8px 14px; border-radius: 10px; opacity: 0; pointer-events: none; transition: opacity .2s; }}
.toast.on {{ opacity: 1; }}
{css}
{theme_css}
</style>
<script>
{theme_js}
WPTheme.early();
</script>
</head>
<body>
<div class="wrap">
  <h1 id="pracTitle"></h1>
  <p class="sub" id="pracSub"></p>
  <div class="prac-toolbar">
    <button type="button" class="btn ghost" id="pracToggle"></button>
    <button type="button" class="btn ghost" id="btn-lang" data-module-zh="English" data-module-en="中文">English</button>
    <span id="offline-theme"></span>
  </div>
  <p class="hint" data-module-zh="点单词听发音；点右边一列、或在这一行上向右滑（手指、鼠标都行）显示中文意思，再点或向左滑藏起来。" data-module-en="Tap a word to hear it; tap the right column, or swipe right on the row (finger or mouse), to show the Chinese meaning; tap or swipe left to hide it again.">点单词听发音；点右边一列、或在这一行上向右滑（手指、鼠标都行）显示中文意思，再点或向左滑藏起来。</p>
  <div id="pracMount"></div>
</div>
<div class="toast" id="toast"></div>
<script>
/* ---------------- 词表和语音（全部内嵌，不联网） ---------------- */
var WP_DATA = {data};
</script>
<script>
{i18n}
</script>
<script>
{i18n_text}
</script>
<script>
{ui}
</script>
<script>
/* ---------------- 启动 ---------------- */
(function () {{
  function t(key, params) {{ return WPI18N.t(key, params); }}
  function toast(text) {{
    var el = document.getElementById('toast');
    el.textContent = text; el.classList.add('on');
    clearTimeout(toast.timer); toast.timer = setTimeout(function () {{ el.classList.remove('on'); }}, 2400);
  }}
  var player = WPPractice.createPlayer({{ audio: WP_DATA.audio, onError: function () {{ toast(t('prac_audioFail')); }} }});
  var view = WPPractice.init({{ mount: document.getElementById('pracMount'), groups: WP_DATA.groups, player: player }});
  function head() {{
    document.title = t('prac_title', {{ title: WP_DATA.title }});
    document.getElementById('pracTitle').textContent = t('prac_heading', {{ title: WP_DATA.title }});
    document.getElementById('pracSub').textContent = WP_DATA.subtitle;
    document.getElementById('pracToggle').textContent = t(view.allRevealed() ? 'prac_hideAll' : 'prac_showAll');
    document.documentElement.lang = WPI18N.lang() === 'en' ? 'en' : 'zh-CN';
    document.getElementById('btn-lang').textContent = WPI18N.lang() === 'en' ? '中文' : 'English';
    Array.prototype.forEach.call(document.querySelectorAll('[data-module-zh]'), function (el) {{
      if (el.id !== 'btn-lang') el.textContent = el.getAttribute(WPI18N.lang() === 'en' ? 'data-module-en' : 'data-module-zh');
    }});
  }}
  document.getElementById('pracToggle').onclick = function () {{ view.revealAll(!view.allRevealed()); head(); }};
  document.getElementById('pracMount').addEventListener('click', function () {{ setTimeout(head, 0); }});
  document.getElementById('pracMount').addEventListener('pointerup', function () {{ setTimeout(head, 0); }});
  document.getElementById('btn-lang').onclick = function () {{ WPI18N.setLang(WPI18N.lang() === 'en' ? 'zh' : 'en'); }};
  WPI18N.onChange(head);
  WPTheme.init(document.getElementById('offline-theme'));
  head();
}})();
</script>
</body>
</html>
"""


def theme_blocks() -> str:
    """网站样式里五套配色的变量块（html[data-theme=…] { … }），读练习页的离线版内嵌这几行，配色和网站完全一样。"""
    lines = [l for l in _read(APP_CSS_FILE).splitlines() if l.startswith("html[data-theme=")]
    if len(lines) < 5:
        raise ValueError("app.css 里没找到五套配色")
    return "\n".join(lines)


def build_practice_html(bank: dict, groups: list[dict],
                        when: time.struct_time | None = None,
                        audio: dict[str, bytes] | None = None) -> tuple[str, str]:
    """返回 ``(文件名, HTML 内容)``：读音练习的离线单文件版，词表和语音全部内嵌，双击就能用。"""
    levels = build_levels(groups)
    if not levels:
        raise ValueError("题库里没有单词，无法生成离线读音练习")
    title = bank.get("title") or "词境 Lexica"
    subtitle = " · ".join([bank.get("level1", ""), bank.get("level2", ""),
                           bank.get("level3", ""), bank.get("level4", "")]).strip(" ·")
    embedded_audio = {}
    for word, clip in (audio or {}).items():
        if clip:
            embedded_audio[_audio_slug(word)] = "data:%s;base64,%s" % (tts.content_type(clip), base64.b64encode(clip).decode("ascii"))
    data = {
        "title": title, "subtitle": subtitle,
        "groups": [{"unit": lv["name"], "words": lv["words"]} for lv in levels],
        "audio": embedded_audio,
        "generated": time.strftime("%Y-%m-%d %H:%M:%S", when or time.localtime()),
    }
    html = PRACTICE_TEMPLATE.format(
        title=_escape(title), css=_read(PRACTICE_CSS_FILE), themes=theme_blocks(), theme_css=_read(THEME_CSS_FILE),
        theme_js=_read(THEME_JS_FILE), i18n=_read(I18N_FILE), i18n_text=_read(I18N_TEXT_FILE),
        ui=_read(PRACTICE_UI_FILE), data=_json_for_script(data))
    return build_filename(bank, when, kind="practice"), html


def _json_for_script(data) -> str:
    """JSON 放进 <script> 前要转义，否则词表里的 ``</script>`` 会提前结束脚本块。"""
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return (text.replace("&", "\\u0026").replace("<", "\\u003c")
            .replace(">", "\\u003e").replace("\u2028", "\\u2028")
            .replace("\u2029", "\\u2029"))


def _escape(text: str) -> str:
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _audio_slug(word: str) -> str:
    return word.strip().lower()


ITEM_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="generator" content="word-puzzle offline generator">
<title>{title}</title>
<style>
{app_css}
{items_css}
{theme_css}
.off-bar {{ display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin: 6px 0 12px; }}
</style>
<script>
{theme_js}
WPTheme.early();
</script>
</head>
<body>
<div class="wrap">
  <h1 class="page" id="offTitle"></h1>
  <p class="lead" id="offSub"></p>
  <div class="off-bar">
    <button type="button" class="btn ghost sm" id="btn-lang" data-module-zh="English" data-module-en="中文">English</button>
    <span id="offline-theme"></span>
  </div>
  <p class="hint" id="offRules"></p>
  <div id="igMount"></div>
</div>
<div class="toast" id="toast"></div>
<script>
/* ---------------- 题目和读音（全部内嵌，不联网） ---------------- */
var WP_DATA = {data};
</script>
<script>
{i18n}
</script>
<script>
{i18n_text}
</script>
<script>
{core}
</script>
<script>
{ui}
</script>
<script>
{adapter}
</script>
<script>
/* ---------------- 启动 ---------------- */
(function () {{
  function t(key, params) {{ return WPI18N.t(key, params); }}
  var game = null, prefix = {{ spell: 'sp', order: 'or', verb: 'vh' }}[WP_DATA.game];
  function head() {{
    document.title = t(prefix + '_docTitle', {{ title: WP_DATA.title }});
    document.getElementById('offTitle').textContent = WP_DATA.title;
    document.getElementById('offSub').textContent = WP_DATA.subtitle;
    document.getElementById('offRules').textContent = t(prefix + '_rules');
    document.documentElement.lang = WPI18N.lang() === 'en' ? 'en' : 'zh-CN';
    document.getElementById('btn-lang').textContent = WPI18N.lang() === 'en' ? '中文' : 'English';
  }}
  function start(k) {{
    var group = WP_DATA.groups[k];
    var cfg = {{
      items: group.items, ords: group.ords,
      save: function (report) {{ WPAdapter.save(report, WP_DATA.meta); }},
      playToken: function () {{ return ''; }}
    }};
    if (WP_DATA.game === 'verb') {{
      cfg.items = [];
      cfg.ords = [];
      WP_DATA.groups.forEach(function (level) {{
        cfg.items = cfg.items.concat(level.items);
        cfg.ords = cfg.ords.concat(level.ords);
      }});
      cfg.choices = cfg.items[0].choices || [];
      cfg.levelCount = WP_DATA.groups.length;
      game = WPVerbUI.start(document.getElementById('igMount'), cfg);
      return;
    }}
    cfg.audioUrl = function (i) {{ return WP_DATA.audio[String(group.ords[i])] || ''; }};
    var ui = WP_DATA.game === 'spell' ? WPSpellUI : WPOrderUI;
    game = ui.start(document.getElementById('igMount'), cfg);
  }}
  function pick() {{
    var mount = document.getElementById('igMount');
    if (WP_DATA.game === 'verb') {{
      var total = WP_DATA.groups.reduce(function (sum, group) {{ return sum + group.items.length; }}, 0);
      mount.innerHTML = '<div class="card"><h2>' + t('vh_startTitle') + '</h2><p class="sub">' +
        t('vh_startInfo', {{ n: total }}) +
        '</p><div class="ig-actions"><button type="button" class="btn" data-verb-start>' +
        t('home_play') + '</button></div></div>';
      mount.onclick = function (ev) {{
        if (!ev.target.closest('[data-verb-start]')) return;
        mount.onclick = null;
        start(0);
      }};
      return;
    }}
    mount.innerHTML = '<div class="card"><h2>' + t('ig_pickLevel') + '</h2><div class="list">' + WP_DATA.groups.map(function (g, k) {{
      return '<div class="item"><div class="main"><b>' + WPItemCore.levelName(g, k, t).replace(/</g, '&lt;') + '</b> <small>' + t('ig_levelCount', {{ n: g.items.length }}) +
        '</small></div><div class="ops"><button type="button" class="btn sm" data-level="' + k + '">' + t('home_play') + '</button></div></div>';
    }}).join('') + '</div></div>';
    mount.onclick = function (ev) {{
      var b = ev.target.closest('[data-level]');
      if (b) {{ mount.onclick = null; start(parseInt(b.getAttribute('data-level'), 10)); }}
    }};
  }}
  document.getElementById('btn-lang').onclick = function () {{ WPI18N.setLang(WPI18N.lang() === 'en' ? 'zh' : 'en'); }};
  WPI18N.onChange(function () {{
    head();
    if (!game && (WP_DATA.game === 'verb' || WP_DATA.groups.length > 1)) pick();
  }});
  WPTheme.init(document.getElementById('offline-theme'));
  head();
  if (WP_DATA.game === 'verb' || WP_DATA.groups.length > 1) pick(); else start(0);
}})();
</script>
</body>
</html>
"""


def build_items_html(bank: dict, groups: list[dict], audio: dict[int, bytes] | None = None,
                     when: time.struct_time | None = None) -> tuple[str, str]:
    """新题型（单词大比拼 / 排排坐 / 动词猎手）的离线单文件页：题目和每道题的读音全部内嵌。排排坐可以录音、自己回放，但不评分。"""
    game = bank.get("game_type")
    if game not in ITEM_UI_FILES:
        raise ValueError("不是新题型的题库")
    out_groups, start = [], 0
    for g in groups:
        n = len(g.get("items") or [])
        if n:
            out_groups.append({"unit": g.get("unit") or "", "part": g.get("part") or 1, "parts": g.get("parts") or 1,
                               "items": g["items"], "ords": list(range(start, start + n))})
        start += n
    if not out_groups:
        raise ValueError("题库里没有题目，无法生成离线页")
    title = bank.get("title") or "词境 Lexica"
    subtitle = " · ".join([bank.get("level1", ""), bank.get("level2", ""), bank.get("level3", ""), bank.get("level4", "")]).strip(" ·")
    embedded = {str(k): "data:%s;base64,%s" % (tts.content_type(clip), base64.b64encode(clip).decode("ascii"))
                for k, clip in (audio or {}).items() if clip}
    data = {"game": game, "title": title, "subtitle": subtitle, "groups": out_groups, "audio": embedded,
            "meta": {"title": title, "bank_id": bank.get("id"), "game_type": game,
                     "generated": time.strftime("%Y-%m-%d %H:%M:%S", when or time.localtime())}}
    html = ITEM_TEMPLATE.format(
        title=_escape(title), app_css=_read(APP_CSS_FILE), items_css=_read(ITEMS_CSS_FILE), theme_css=_read(THEME_CSS_FILE),
        theme_js=_read(THEME_JS_FILE), i18n=_read(I18N_FILE), i18n_text=_read(I18N_TEXT_FILE), core=_read(ITEM_CORE_FILE),
        ui=_read(ITEM_UI_FILES[game]), adapter=_read(ADAPTER_FILE), data=_json_for_script(data))
    return build_filename(bank, when, kind=game), html
