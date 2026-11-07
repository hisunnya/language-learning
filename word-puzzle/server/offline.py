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
UI_FILE = WEB / "js" / "game-ui.js"
ADAPTER_FILE = WEB / "js" / "game-adapter-offline.js"

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
</style>
</head>
<body>
<div class="app">
  <div class="hud">
    <div class="hud-row">
      <div class="stat"><span class="k">关卡</span><span class="v" id="s-level">1/{levels}</span></div>
      <div class="stat time" id="s-timebox"><span class="k">剩余</span><span class="v" id="s-time">60</span></div>
      <div class="stat"><span class="k">进度</span><span class="v" id="s-prog">0/8</span></div>
      <div class="stat score"><span class="k">得分</span><span class="v" id="s-score">0</span></div>
      <div class="stat"><span class="k">连击</span><span class="v" id="s-combo">0</span></div>
    </div>
    <div class="progress"><i id="s-bar"></i></div>
    <div class="ptext"><span id="s-tip">点任意一张卡片，再点另一侧配对</span><span id="s-total">总分 0</span></div>
  </div>
  <div class="board" id="board"></div>
  <div class="bar">
    <button class="btn ghost sm" id="btn-help">玩法</button>
    <button class="btn ghost sm" id="btn-full">全屏</button>
    <button class="btn warn" id="btn-replay">重玩本关</button>
    <button class="btn" id="btn-restart">从头开始</button>
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
{ui}
</script>
<script>
{adapter}
</script>
<script>
/* ---------------- 启动 ---------------- */
(function () {{
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


def build_filename(bank: dict, when: time.struct_time | None = None) -> str:
    """层级 + 日期 + 时间。例：初中-九年级-上册-全部单元-20261104-153012.html"""
    tm = when or time.localtime()
    parts = [
        safe_filename(bank.get("level1", ""), "层级1"),
        safe_filename(bank.get("level2", ""), "层级2"),
        safe_filename(bank.get("level3", ""), "层级3"),
        safe_filename(bank.get("level4", ""), "层级4"),
    ]
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
        core=_read(CORE_FILE),
        ui=_read(UI_FILE),
        adapter=_read(ADAPTER_FILE),
        data=json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        levels=len(levels),
    )
    return build_filename(bank, when), html


def _escape(text: str) -> str:
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _audio_slug(word: str) -> str:
    return word.strip().lower()
