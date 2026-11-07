"""解析 Word 文档（``.docx`` / ``.docm``）。

``.docx`` 本质是个 ZIP，里面是 OOXML。
只用标准库就能解析，**不需要 python-docx，也不需要装任何东西**：

* ``word/document.xml`` —— 正文（段落 + 表格）
* ``word/header*.xml`` / ``word/footer*.xml`` —— 页眉页脚（可选）

表格里的每一行会先拼成「制表符分隔」的一行，交给
:mod:`server.wordlist` 统一解析，这样 Word 里的
「单词 | 音标 | 词性 | 中文」表格也能直接用。

老式二进制 ``.doc`` 解析不了，会抛 :class:`ParseError`，
提示用户另存为 ``.docx``。
"""
from __future__ import annotations

import io
import re
import zipfile
from xml.etree import ElementTree

# OOXML 命名空间
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


MAX_DOCUMENT_BYTES = 20 * 1024 * 1024

class DocxError(Exception):
    """docx 解析失败。"""


def _text_of(node) -> str:
    """把一个 ``w:p`` 段落里的所有 ``w:t`` 文本拼起来（保留 tab / br）。"""
    parts: list[str] = []
    for child in node.iter():
        tag = child.tag
        if tag == W + "t":
            parts.append(child.text or "")
        elif tag == W + "tab":
            parts.append("\t")
        elif tag == W + "br" or tag == W + "cr":
            parts.append("\n")
    return "".join(parts)


def _paragraphs(container) -> list[str]:
    out: list[str] = []
    for p in container.iter(W + "p"):
        txt = _text_of(p).strip()
        if txt:
            out.append(txt)
    return out


def _tables(container) -> list[list[str]]:
    """每个表格返回一个「行列表」，行内用 ``\\t`` 连接各单元格。"""
    tables: list[list[str]] = []
    for tbl in container.iter(W + "tbl"):
        rows: list[str] = []
        for tr in tbl.iter(W + "tr"):
            cells: list[str] = []
            for tc in tr.findall(W + "tc"):
                cell = " ".join(x for x in _paragraphs(tc) if x)
                cells.append(cell.strip())
            # 整行都空就跳过
            if any(cells):
                rows.append("\t".join(cells))
        if rows:
            tables.append(rows)
    return tables


def docx_to_lines(data: bytes) -> list[str]:
    """把 docx 抽成一行一行的文本（表格行用 ``\\t`` 分隔列）。

    顺序按文档中的出现顺序，段落和表格交替。
    """
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except (zipfile.BadZipFile, OSError) as exc:
        raise DocxError(f"不是有效的 Word 文件（.docx）：{exc}") from exc

    names = set(zf.namelist())
    if "word/document.xml" not in names:
        if "word/document.xml" in names or not any(
                n.startswith("word/") for n in names):
            raise DocxError("Word 文件里找不到正文，可能已被加密")
        raise DocxError("Word 文件结构异常")

    # 防 zip 炸弹：压缩包本身受上传上限约束，但解压后的正文可以大得多。
    if zf.getinfo("word/document.xml").file_size > MAX_DOCUMENT_BYTES:
        raise DocxError("Word 正文过大（解压后超过 20MB），请拆分后再上传")

    try:
        raw = zf.read("word/document.xml")
    except KeyError as exc:
        raise DocxError("Word 文件结构异常") from exc

    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError as exc:
        raise DocxError(f"Word 正文解析失败：{exc}") from exc

    body = root.find(W + "body")
    if body is None:
        body = root

    lines: list[str] = []
    for child in body:
        if child.tag == W + "p":
            txt = _text_of(child).strip()
            if txt:
                lines.append(txt)
        elif child.tag == W + "tbl":
            for rows in _tables(child):
                lines.extend(rows)
    return lines


def is_docx(data: bytes) -> bool:
    """判断字节流是不是 zip（docx/xlsx/pptx 都是）。"""
    return data[:4] == b"PK\x03\x04"


def is_legacy_doc(data: bytes) -> bool:
    """判断是不是老式二进制 ``.doc``（OLE2 复合文档）。"""
    return data[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


def doc_magic_check(data: bytes) -> None:
    """在确定是 doc 之前先检查一下文件头，早点给出清晰报错。"""
    if is_legacy_doc(data):
        raise DocxError(
            "这是老式的 Word 97-2003 (.doc) 文件，无法直接解析。"
            "请在 Word 里「另存为」→「Word 文档 (*.docx)」后重新上传，"
            "或者导出成 PDF 上传。")


_CLEAN_RE = re.compile(r"\s+")


def tidy(text: str) -> str:
    """压缩多余空白，但保留制表符。"""
    lines = []
    for line in text.splitlines():
        line = _CLEAN_RE.sub(" ", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)
