"""上传资料的解析。

支持三种格式：

* **JSON** —— 本项目导出的结构，或任意含 ``en``/``english``/``word`` 与
  ``cn``/``chinese``/``meaning``/``translation`` 字段的对象数组；
  也接受 ``{"units": [{"unit": "...", "words": [...]}]}`` 这种带单元的写法。
* **CSV / TSV** —— 表头自动识别 ``unit / en / cn / ipa / pos``；
  没有表头时按「英文,中文」两列猜。
* **TXT** —— 每行一个词，英文与中文之间用制表符、``-``、``|``、``：`` 或连续空格分隔；
  单独一行且形如 ``Unit 3`` 的会当作单元标题。

解析结果统一成 ``[{"unit": str, "en": str, "cn": str, "ipa": str, "pos": str}]``。
"""
from __future__ import annotations

import csv
import io
import json
import re
from typing import Any

from . import docx as docx_mod
from . import pdf as pdf_mod
from . import wordlist
from .docx import doc_magic_check

EN_KEYS = ("en", "eng", "english", "word", "term", "vocabulary", "单词", "英文")
CN_KEYS = ("cn", "zh", "chinese", "meaning", "translation", "trans", "释义",
           "中文", "意思", "翻译")
UNIT_KEYS = ("unit", "unit_name", "section", "chapter", "模块", "单元", "章节")
IPA_KEYS = ("ipa", "phonetic", "pronunciation", "音标")
POS_KEYS = ("pos", "partofspeech", "part_of_speech", "词性")


class ParseError(Exception):
    """资料无法解析时抛出，message 直接展示给用户。"""


def _pick(d: dict, keys: tuple[str, ...]) -> str:
    low = {str(k).strip().lower(): v for k, v in d.items()}
    for k in keys:
        if k in low and str(low[k]).strip():
            return str(low[k]).strip()
    return ""


def _norm_words(raw: list[dict], default_unit: str = "Unit 1") -> list[dict]:
    out = []
    seen = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        en = _pick(item, EN_KEYS)
        cn = _pick(item, CN_KEYS)
        if not en or not cn:
            continue
        en = en.strip()
        cn = re.sub(r"\s+", " ", cn).strip()
        if not en or not cn:
            continue
        key = (en.lower(), cn)
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "unit": _pick(item, UNIT_KEYS) or default_unit,
            "en": en,
            "cn": cn,
            "ipa": _pick(item, IPA_KEYS),
            "pos": _pick(item, POS_KEYS),
        })
    return out


def parse_json(text: str) -> list[dict]:
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ParseError(f"JSON 解析失败：{exc}") from exc

    if isinstance(doc, dict):
        for key in ("units", "words", "data", "items", "list"):
            if isinstance(doc.get(key), list):
                doc = doc[key]
                break
        else:
            doc = [doc]

    if not isinstance(doc, list):
        raise ParseError("JSON 顶层需要是数组，或包含 units/words 数组的对象")

    # 带单元的写法
    if doc and isinstance(doc[0], dict) and isinstance(doc[0].get("words"), list):
        out: list[dict] = []
        for unit_obj in doc:
            unit = str(unit_obj.get("unit") or unit_obj.get("name") or "Unit 1")
            out.extend(_norm_words(unit_obj.get("words") or [], default_unit=unit))
        return out

    return _norm_words(doc)


def _sniff_dialect(sample: str, ext: str) -> str:
    if ext in ("tsv", "tab"):
        return "\t"
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
        return dialect.delimiter
    except csv.Error:
        return "," if "," in sample else "\t"


def _looks_like_unit(text: str) -> bool:
    """判断一列是不是单元名（Unit 1 / Module 2 / 第三单元 …）。"""
    s = str(text).strip()
    if not s:
        return False
    if _UNIT_RE.match(s):
        return True
    return bool(re.match(r"^(第\s*[0-9一二三四五六七八九十]+\s*[单元课章]|"
                         r"[单元课章]\s*[0-9一二三四五六七八九十]+)$", s))


def parse_csv(text: str, ext: str = "csv") -> list[dict]:
    sample = text[:4096]
    delimiter = _sniff_dialect(sample, ext)
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = [r for r in reader if any(str(c).strip() for c in r)]
    if not rows:
        raise ParseError("文件是空的")

    header = [str(c).strip().lower() for c in rows[0]]
    has_en = any(k in header for k in EN_KEYS)
    has_cn = any(k in header for k in CN_KEYS)

    if has_en or has_cn:
        # 有表头：按表头取列
        out = []
        for row in rows[1:]:
            item = {}
            for i, key in enumerate(header):
                item[key] = row[i] if i < len(row) else ""
            out.extend(_norm_words([item]))
        return out

    # 无表头
    width = max(len(r) for r in rows)
    unit_first = width >= 3 and all(_looks_like_unit(r[0]) for r in rows
                                    if len(r) >= 3)
    out = []
    for row in rows:
        if unit_first and len(row) >= 3:
            out.extend(_norm_words([{"unit": row[0], "en": row[1],
                                     "cn": row[2]}]))
        elif len(row) >= 2:
            out.extend(_norm_words([{"en": row[0], "cn": row[1]}]))
    return out


_SPLIT_RE = re.compile(r"\s*[\t|]|\s+[-–—:：]\s+|\s{2,}")
_UNIT_RE = re.compile(r"^\s*(unit|module|lesson|part)\s*\.?\s*([0-9]+)\s*"
                       r"(?:[：:]?\s*(.*))?$", re.I)


def parse_txt(text: str) -> list[dict]:
    out: list[dict] = []
    unit = "Unit 1"
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _UNIT_RE.match(line)
        if m:
            label = (m.group(3) or "").strip()
            unit = f"{m.group(1).title()} {m.group(2)}" + (f" {label}" if label else "")
            continue
        parts = [p for p in _SPLIT_RE.split(line) if p.strip()]
        if len(parts) < 2:
            continue
        out.extend(_norm_words([{"en": parts[0], "cn": " ".join(parts[1:]),
                                 "unit": unit}]))
    return out


def parse_material(filename: str, raw: bytes) -> tuple[str, list[dict]]:
    """返回 ``(格式, 词条列表)``。

    支持 ``.txt`` / ``.csv`` / ``.tsv`` / ``.json`` / ``.md`` / ``.docx`` / ``.pdf``。
    """
    name = (filename or "").lower()
    ext = name.rsplit(".", 1)[-1] if "." in name else ""

    # ---- Word / PDF：二进制，走各自的解析器 ----
    if ext in ("docx", "docm", "dotx"):
        return "docx", parse_docx(raw)
    if ext == "doc":
        try:
            doc_magic_check(raw)  # 一定抛错，给出「另存为 docx」的提示
        except docx_mod.DocxError as exc:
            raise ParseError(str(exc)) from exc
    if ext == "pdf":
        return "pdf", parse_pdf(raw)

    # ---- 文本类 ----
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = raw.decode("gb18030")
        except UnicodeDecodeError as exc:
            raise ParseError("文件编码无法识别（请用 UTF-8）") from exc

    if ext == "json":
        words = parse_json(text)
        fmt = "json"
    elif ext in ("csv", "tsv", "tab"):
        words = parse_csv(text, ext)
        fmt = ext
    elif ext in ("txt", "text", "md"):
        words = parse_txt(text)
        fmt = "txt"
    else:
        # 后缀不认识就按内容猜
        stripped = text.lstrip()
        if stripped.startswith("{") or stripped.startswith("["):
            words = parse_json(text)
            fmt = "json"
        elif "," in text[:2048] or "\t" in text[:2048]:
            words = parse_csv(text, "csv")
            fmt = "csv"
        else:
            words = parse_txt(text)
            fmt = "txt"

    if not words:
        raise ParseError("没有从文件里解析出任何词条")
    return fmt, words


def parse_docx(raw: bytes) -> list[dict]:
    """解析 Word（.docx）文件。

    走 :mod:`server.wordlist` 的通用规则，所以 Word 里的
    「单元标题 / 英文 / 音标 / 词性 / 中文」表格也能直接认出来。
    """
    try:
        lines = docx_mod.docx_to_lines(raw)
    except docx_mod.DocxError as exc:
        raise ParseError(str(exc)) from exc
    words = wordlist.parse_lines(lines)
    if not words:
        raise ParseError(
            "Word 文件里没找到「英文 + 中文释义」的词条。"
            "请确认表格里每一行都有英文单词和中文意思")
    return words


def parse_pdf(raw: bytes) -> list[dict]:
    """解析 PDF。

    文字版走 poppler / 内置解析器，扫描件走 OCR。
    多个引擎都试一遍，挑**解析出的词条最多**的那个——
    poppler 有时会因为字体元数据不全而漏字（``apple`` → ``aple``），
    这时候内置解析器反而是全的。
    """
    try:
        candidates = pdf_mod.pdf_candidates(raw)
    except pdf_mod.PdfError as exc:
        raise ParseError(str(exc)) from exc

    best: list[dict] = []
    for text, _engine in candidates:
        words = wordlist.parse_glossary_text(text)
        if not words:
            words = wordlist.parse_lines(text.splitlines())
        if len(words) > len(best):
            best = words

    if not best and pdf_mod.has_ocr():
        try:
            ocr_candidates = pdf_mod.pdf_candidates(raw, force_ocr=True)
        except pdf_mod.PdfError as exc:
            raise ParseError(str(exc)) from exc
        for text, _engine in ocr_candidates:
            words = wordlist.parse_glossary_text(text)
            if not words:
                words = wordlist.parse_lines(text.splitlines())
            if len(words) > len(best):
                best = words
        candidates.extend(ocr_candidates)
    if not best:
        engines = "/".join(e for _, e in candidates) or "无"
        raise ParseError(
            f"PDF 里没找到「英文 + 中文释义」的词条"
            f"（文本提取方式：{engines}）")
    return best


def summary(words: list[dict]) -> dict[str, Any]:
    units: dict[str, int] = {}
    for w in words:
        units[w["unit"]] = units.get(w["unit"], 0) + 1
    return {
        "word_count": len(words),
        "unit_count": len(units),
        "units": [{"name": u, "count": c} for u, c in units.items()],
    }
