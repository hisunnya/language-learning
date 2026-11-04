"""解析 PDF。

三种情况，三条路
----------------
1. **文字版 PDF** —— 首选 ``pdftotext``（poppler-utils，Ubuntu 装
   ``poppler-utils`` 就有）。它能正确处理字体编码、双栏布局。
2. **poppler 没装** —— 走内置的纯 Python 提取器：自己解压 PDF 的
   FlateDecode 流，扫描文本操作符，把字符串抠出来。
   质量不如 poppler，但零依赖，够用来认出「英文 + 中文」的行。
3. **扫描件 / 图片版 PDF**（每个字都是图片）—— 上面两条都提不出文字。
   这时用 ``pdftoppm`` 把页面转成 PNG，再交给 ``tesseract`` OCR
   （``tesseract-ocr`` + ``tesseract-ocr-chi-sim``）。

全部是**本地开源工具**，不调用任何大模型、不联网。

识别出来是图片版但机器上没装 tesseract 时，会明确提示安装命令，
而不是丢一句「解析失败」。
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import zlib
from pathlib import Path

MAX_PAGES = 60          # 最多处理多少页
MAX_CHARS = 400_000     # 提取出来的文本上限
MAX_BYTES = 20_000_000  # 输入文件大小上限（20MB），防止超大文件把线程卡死


class PdfError(Exception):
    """PDF 解析失败。"""


# ------------------------------------------------------------------ 外部工具

def _tool(name: str) -> str | None:
    return shutil.which(name)


def has_poppler() -> bool:
    return _tool("pdftotext") is not None


def has_ocr() -> bool:
    return _tool("tesseract") is not None and _tool("pdftoppm") is not None


def describe() -> dict:
    return {
        "pdf_text_tool": "pdftotext" if has_poppler() else "builtin",
        "pdf_ocr_available": has_ocr(),
    }


# ------------------------------------------------------------------ poppler

def _run(cmd: list[str], timeout: int = 120) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as exc:
        raise PdfError(f"执行 {cmd[0]} 失败：{exc}") from exc
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def _pdftotext(path: str) -> str:
    """用 poppler 提取文字（保留大致列位置）。"""
    rc, out = _run(["pdftotext", "-layout", "-enc", "UTF-8", path, "-"])
    if rc != 0:
        rc, out = _run(["pdftotext", "-enc", "UTF-8", path, "-"])
        if rc != 0:
            raise PdfError("pdftotext 解析失败")
    return out


# ------------------------------------------------------------------ 纯 Python 提取

_STREAM_RE = re.compile(rb"stream\r?\n(.*?)\r?\nendstream", re.S)
_OBJ_RE = re.compile(rb"(\d+)\s+(\d+)\s+obj\b(.*?)\bendobj", re.S)
_OBJ_NUM_RE = re.compile(rb"(\d+)\s+(\d+)\s*$")
_OBJSTM_RE = re.compile(rb"/ObjStm")


def _inflate(data: bytes) -> bytes:
    """解开 FlateDecode；失败就原样返回。"""
    try:
        return zlib.decompress(data)
    except zlib.error:
        try:
            return zlib.decompressobj().decompress(data)
        except zlib.error:
            return b""


def _stream_of(body: bytes) -> bytes:
    """取出对象体里的流数据（解压 FlateDecode）。"""
    m = _STREAM_RE.search(body)
    if not m:
        return b""
    raw = m.group(1)
    out = _inflate(raw)
    return out if out else raw


def _parse_objects(data: bytes) -> dict[int, bytes]:
    """把 PDF 里所有间接对象抓出来：``{对象号: 对象体}``。

    先用 ``find`` 定位 ``obj`` 关键字，再**往前**看几十字节取对象号——
    不要直接用一个大正则去全文扫描，PDF 里的长数字串（图像数据）会让
    正则回溯成平方级复杂度，几百 KB 的坏文件就能把请求线程卡死。
    """
    objs: dict[int, bytes] = {}
    if b"obj" not in data:
        return objs
    pos = 0
    while True:
        idx = data.find(b"obj", pos)
        if idx < 0:
            break
        pos = idx + 3
        # 跳过 ``endobj``
        if data[max(0, idx - 3):idx] == b"end":
            continue
        # 往前找 ``<num> <gen> obj``
        head = data[max(0, idx - 40):idx]
        m = _OBJ_NUM_RE.search(head)
        if not m:
            continue
        try:
            num = int(m.group(1))
        except ValueError:
            continue
        # 对象体到下一个 ``endobj`` 为止
        end = data.find(b"endobj", idx)
        if end < 0:
            end = len(data)
        body = data[idx + 3:end]
        # 对象流（PDF 1.5+）里还藏着别的对象
        if _OBJSTM_RE.search(body[:400]):
            objs.update(_expand_objstm(body))
        objs[num] = body
    return objs


def _expand_objstm(body: bytes) -> dict[int, bytes]:
    """展开 ``/Type /ObjStm`` 对象流里的对象。"""
    out: dict[int, bytes] = {}
    payload = _stream_of(body)
    if not payload:
        return out
    m_n = re.search(rb"/N\s+(\d+)", body)
    m_first = re.search(rb"/First\s+(\d+)", body)
    if not (m_n and m_first):
        return out
    n = int(m_n.group(1))
    first = int(m_first.group(1))
    header = payload[:first].split()
    pairs = []
    for i in range(n):
        try:
            num = int(header[2 * i])
            off = int(header[2 * i + 1])
        except (IndexError, ValueError):
            break
        pairs.append((num, off))
    for i, (num, off) in enumerate(pairs):
        end = pairs[i + 1][1] if i + 1 < len(pairs) else len(payload) - first
        out[num] = payload[first + off:first + end]
    return out


# ------------------------------------------------------------------ ToUnicode CMap

def _parse_cmap(data: bytes) -> tuple[dict[int, str], int]:
    """解析 ToUnicode CMap，返回 ``({码位: 字符}, 每字符字节数)``。

    支持 ``beginbfchar`` 和 ``beginbfrange`` 两种写法。
    字节数从 ``begincodespacerange`` 推断（``<0000> <FFFF>`` → 2 字节）。
    """
    text = data.decode("latin-1", "ignore")
    mapping: dict[int, str] = {}

    # 码位宽度：<0000> <FFFF> 说明是 2 字节码
    width = 1
    m = re.search(r"begincodespacerange(.*?)endcodespacerange", text, re.S)
    if m:
        ranges = re.findall(r"<([0-9A-Fa-f]+)>", m.group(1))
        if ranges:
            width = max(1, len(ranges[0]) // 2)

    def _hex_to_str(h: str) -> str:
        h = h.strip()
        try:
            raw = bytes.fromhex(h)
        except ValueError:
            return ""
        if len(raw) >= 2:
            try:
                return raw.decode("utf-16-be", "ignore")
            except UnicodeDecodeError:
                pass
        return raw.decode("latin-1", "ignore")

    # bfchar: <01> <0041>
    for block in re.findall(r"beginbfchar(.*?)endbfchar", text, re.S):
        for src, dst in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
            try:
                code = int(src, 16)
            except ValueError:
                continue
            ch = _hex_to_str(dst)
            if ch:
                mapping[code] = ch

    # bfrange: <01> <02> <0041>
    for block in re.findall(r"beginbfrange(.*?)endbfrange", text, re.S):
        for lo, hi, dst in re.findall(
                r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
            try:
                start, end = int(lo, 16), int(hi, 16)
                base = int(dst, 16)
            except ValueError:
                continue
            if end < start or end - start > 65535:
                continue
            for k in range(start, end + 1):
                try:
                    mapping[k] = chr(base + (k - start))
                except ValueError:
                    break

    return mapping, width


def _pdf_strings_from_content(content: bytes) -> str:
    """从 PDF 内容流里抠出可读文本（拉丁字体的简易路径，不保留排版）。"""
    chunks: list[str] = []
    for m in re.finditer(rb"<([0-9A-Fa-f\s]+)>", content):
        hexs = re.sub(rb"\s", b"", m.group(1))
        if len(hexs) % 2:
            continue
        try:
            raw = bytes.fromhex(hexs.decode("ascii"))
        except ValueError:
            continue
        if len(raw) >= 2 and raw[0] == 0:
            chunks.append(raw.decode("utf-16-be", "ignore"))
        else:
            chunks.append(raw.decode("latin-1", "ignore"))
    for m in re.finditer(rb"\((?:\\.|[^()\\])*\)", content, re.S):
        raw = m.group(0)[1:-1]
        raw = re.sub(rb"\\([()\\])", rb"\1", raw)
        raw = re.sub(rb"\\([0-7]{1,3})",
                     lambda mm: bytes([int(mm.group(1), 8) & 0xFF]), raw)
        chunks.append(raw.decode("latin-1", "ignore"))
    return "".join(chunks)


def _builtin_extract(data: bytes) -> str:
    """不依赖 poppler 的纯 Python PDF 文字提取（尽力而为）。

    能处理：
    * FlateDecode 内容流
    * 字面量字符串 ``(text)`` 和十六进制字符串 ``<hex>``
    * **ToUnicode CMap**（中文 PDF 靠它把码位还原成汉字）
    * 定位操作符（``Td`` / ``Tm`` / ``T*``）——用来还原换行和分栏
    """
    objs = _parse_objects(data)

    # 收集所有 ToUnicode 映射（按字体区分，找不到归属时用并集兜底）
    cmaps: list[tuple[dict[int, str], int]] = []
    for body in objs.values():
        payload = _stream_of(body)
        if not payload:
            continue
        if b"beginbfchar" in payload or b"beginbfrange" in payload:
            cm = _parse_cmap(payload)
            if cm[0]:
                cmaps.append(cm)
    union: dict[int, str] = {}
    union_width = 1
    for cm, width in cmaps:
        for k, v in cm.items():
            union.setdefault(k, v)
        union_width = max(union_width, width)

    fonts = _font_cmaps(objs, union_width)

    parts: list[str] = []
    for body in objs.values():
        content = _stream_of(body)
        if not content:
            continue
        if b"Tj" not in content and b"TJ" not in content:
            continue
        text = _content_stream_text(content, fonts, union, union_width)
        if text.strip():
            parts.append(text)

    if not parts:
        raise PdfError("这个 PDF 里没找到可提取的文字")
    return "\n".join(parts)


def _decode_with_cmap(content: bytes, cmap: dict[int, str]) -> str:
    """用 ToUnicode 表把内容流里的十六进制串解码成文字。"""
    out: list[str] = []
    for m in re.finditer(rb"<([0-9A-Fa-f\s]+)>", content):
        hexs = re.sub(rb"\s", b"", m.group(1))
        if len(hexs) % 4 == 0:
            step = 4          # 2 字节码位（Identity-H / Type0）
        elif len(hexs) % 2 == 0:
            step = 2          # 1 字节码位（简单字体）
        else:
            continue
        s = []
        for i in range(0, len(hexs) - step + 1, step):
            try:
                code = int(hexs[i:i + step], 16)
            except ValueError:
                continue
            s.append(cmap.get(code, ""))
        out.append("".join(s))
    # 简单字体的字面量串也一起带上
    for m in re.finditer(rb"\((?:\\.|[^()\\])*\)", content, re.S):
        raw = m.group(0)[1:-1]
        raw = re.sub(rb"\\([()\\])", rb"\1", raw)
        out.append(raw.decode("latin-1", "ignore"))
    return "".join(out)


# ------------------------------------------------------------------ 内容流解析

# 内容流里的 token：字符串、十六进制串、数字、名字、操作符
_TOKEN_RE = re.compile(
    rb"\((?:\\.|[^()\\])*\)"      # (literal)
    rb"|<[0-9A-Fa-f\s]*>"         # <hex>
    rb"|/[^\s/\[\]<>()]+"         # /Name
    rb"|\[[^\]]*\]"               # [array]
    rb"|[-+]?[0-9]*\.?[0-9]+"     # number
    rb"|[A-Za-z'\"*]+"            # operator
    rb"|\s+",
    re.S)


def _decode_literal(raw: bytes) -> bytes:
    """解析 PDF 字面量字符串里的转义。"""
    body = raw[1:-1]
    body = re.sub(rb"\\([()\\])", rb"\1", body)
    body = re.sub(rb"\\([0-7]{1,3})",
                  lambda mm: bytes([int(mm.group(1), 8) & 0xFF]), body)
    body = body.replace(b"\r", b"\n").replace(b"\n", b"\n")
    return body


def _font_cmaps(objs: dict[int, bytes],
                union_width: int = 1) -> dict[str, tuple[dict[int, str], int]]:
    """解析出 ``{字体名: (ToUnicode 表, 每字符字节数)}``。

    只在页面里出现多个字体时才需要精确对应；
    找不到对应关系时用并集兜底。
    """
    # 先找页面对象
    fonts: dict[str, tuple[dict[int, str], int]] = {}
    for body in objs.values():
        if b"/Type" not in body or b"/Page" not in body:
            continue
        res = _resolve_dict(body, b"/Resources", objs)
        if not res:
            continue
        fdict = _resolve_dict(res, b"/Font", objs)
        if not fdict:
            continue
        for name, ref in _dict_entries(fdict):
            fobj = _resolve_obj(body, ref, objs)
            if not fobj:
                continue
            cmap: dict[int, str] = {}
            width = union_width
            tu = re.search(rb"/ToUnicode\s+(\d+)\s+\d+\s+R", fobj)
            if tu:
                payload = _stream_of(objs.get(int(tu.group(1)), b""))
                if payload:
                    cmap, width = _parse_cmap(payload)
            if cmap:
                fonts[name] = (cmap, width)
    return fonts


def _dict_entries(data: bytes) -> list[tuple[str, bytes]]:
    """把 PDF 字典里的 ``/Name <value>`` 对取出来。"""
    out: list[tuple[str, bytes]] = []
    for m in re.finditer(rb"/([^\s/\[\]<>()]+)\s*(\d+\s+\d+\s+R|<<|[\w.+-]+)",
                         data):
        out.append((m.group(1).decode("latin-1"), m.group(2)))
    return out


def _resolve_dict(body: bytes, key: bytes, objs: dict[int, bytes]) -> bytes:
    """取 ``body`` 里某个键对应的字典（可能是指向别的对象）。"""
    m = re.search(re.escape(key) + rb"\s*<<", body)
    if m:
        # 找到配对的 >>
        i = m.end() - 2
        depth = 0
        for j in range(i, len(body) - 1):
            if body[j:j + 2] == b"<<":
                depth += 1
                j += 1
            elif body[j:j + 2] == b">>":
                depth -= 1
                if depth == 0:
                    return body[i:j + 2]
        return body[i:]
    m = re.search(re.escape(key) + rb"\s+(\d+)\s+\d+\s+R", body)
    if m:
        return objs.get(int(m.group(1)), b"")
    return b""


def _resolve_obj(body: bytes, ref: bytes, objs: dict[int, bytes]) -> bytes:
    m = re.match(rb"(\d+)\s+\d+\s+R", ref.strip())
    if not m:
        return b""
    return objs.get(int(m.group(1)), b"")


def _content_stream_text(content: bytes,
                         fonts: dict[str, tuple[dict[int, str], int]],
                         union: dict[int, str],
                         union_width: int = 1) -> str:
    """按内容流的操作符顺序提取文字，并**保留行列结构**。

    PDF 里真正的排版信息在 ``Td`` / ``TD`` / ``Tm`` / ``T*`` 这些
    定位操作符上。只按顺序抠字符串的话，双栏表格会被拼成一行，
    这里按 Y 坐标换行、按 X 坐标补空格。
    """
    out: list[str] = []
    operands: list[bytes] = []
    cur_font = ""
    cur_cmap: dict[int, str] = union
    cur_width = 1
    x = y = 0.0
    last_y: float | None = None
    last_x = 0.0
    leading = 0.0

    def decode(raw: bytes) -> str:
        if raw.startswith(b"<"):
            hexs = re.sub(rb"\s", b"", raw[1:-1])
            step = cur_width if cur_width > 0 else 1
            if len(hexs) % step:
                # 长度对不上就退一步用单字节
                step = 1
            s = []
            for i in range(0, len(hexs) - step + 1, step):
                try:
                    code = int(hexs[i:i + step], 16)
                except ValueError:
                    continue
                s.append(cur_cmap.get(code, ""))
            return "".join(s)
        body = _decode_literal(raw)
        if cur_width == 2:
            try:
                return body.decode("utf-16-be", "ignore")
            except UnicodeDecodeError:
                return ""
        return body.decode("latin-1", "ignore")

    for m in _TOKEN_RE.finditer(content):
        tok = m.group(0)
        if not tok.strip():
            continue
        if tok[:1] in (b"(", b"<", b"[", b"/") or re.fullmatch(rb"[-+]?[0-9]*\.?[0-9]+", tok):
            operands.append(tok)
            continue
        op = tok
        if op == b"Tf":
            if len(operands) >= 2:
                name = operands[-2].decode("latin-1", "ignore").lstrip("/")
                cur_font = name
                if name in fonts:
                    cur_cmap, cur_width = fonts[name]
                else:
                    cur_cmap, cur_width = union, union_width
            operands = []
        elif op in (b"Td", b"TD"):
            if len(operands) >= 2:
                try:
                    dx = float(operands[-2])
                    dy = float(operands[-1])
                except ValueError:
                    dx = dy = 0.0
                if op == b"TD":
                    leading = -dy
                x += dx
                y += dy
            operands = []
        elif op == b"Tm":
            if len(operands) >= 6:
                try:
                    x = float(operands[-2])
                    y = float(operands[-1])
                except ValueError:
                    pass
            operands = []
        elif op == b"TL":
            if operands:
                try:
                    leading = float(operands[-1])
                except ValueError:
                    pass
            operands = []
        elif op == b"T*":
            y -= leading
            operands = []
        elif op == b"Tj":
            if operands:
                text = decode(operands[-1])
                if text:
                    if last_y is not None and abs(y - last_y) > 0.5:
                        out.append("\n")
                    elif last_y is not None and x - last_x > 6:
                        out.append("   ")
                    out.append(text)
                    last_y = y
                    last_x = x + len(text) * 6
            operands = []
        elif op == b"TJ":
            if operands:
                arr = operands[-1]
                if arr.startswith(b"["):
                    inner = arr[1:-1]
                    parts = []
                    for sm in re.finditer(rb"<[0-9A-Fa-f\s]*>|\((?:\\.|[^()\\])*\)",
                                          inner, re.S):
                        parts.append(decode(sm.group(0)))
                    text = "".join(parts)
                    if text:
                        if last_y is not None and abs(y - last_y) > 0.5:
                            out.append("\n")
                        elif last_y is not None and x - last_x > 6:
                            out.append("   ")
                        out.append(text)
                        last_y = y
                        last_x = x + len(text) * 6
            operands = []
        elif op in (b"'", b'"'):
            y -= leading
            if operands:
                text = decode(operands[-1])
                if text:
                    if last_y is not None and abs(y - last_y) > 0.5:
                        out.append("\n")
                    out.append(text)
                    last_y = y
            operands = []
        else:
            operands = []

    return "".join(out)


# ------------------------------------------------------------------ OCR

def _ocr(path: str) -> str:
    """扫描件 → OCR 文字。

    用 tesseract 的 TSV 输出（带每个词的坐标）**按行重建**版面：
    普通的文本输出会把「英文列」和「中文列」分成两块，
    词表就配不上了；按 y 坐标聚成行、按 x 坐标分列才还原得出来。
    """
    if not has_ocr():
        raise PdfError(
            "这个 PDF 是图片版（扫描件），需要 OCR 才能识别文字。"
            "请在服务器上安装：sudo apt install poppler-utils tesseract-ocr "
            "tesseract-ocr-chi-sim")

    with tempfile.TemporaryDirectory(prefix="wp-ocr-") as tmp:
        prefix = os.path.join(tmp, "page")
        rc, _ = _run(["pdftoppm", "-r", "300", "-png", "-f", "1",
                      "-l", str(MAX_PAGES), path, prefix], timeout=300)
        if rc != 0:
            raise PdfError("PDF 转图片失败")
        pages = sorted(Path(tmp).glob("page*.png"))
        if not pages:
            raise PdfError("PDF 转图片失败")

        texts: list[str] = []
        for img in pages[:MAX_PAGES]:
            langs = "eng+chi_sim" if _has_lang("chi_sim") else "eng"
            text = _ocr_page_tsv(img, langs)
            if not text:
                text = _ocr_page_plain(img, langs)
            if text.strip():
                texts.append(text)
        if not texts:
            raise PdfError("OCR 没识别出文字")
        return "\n".join(texts)


def _ocr_page_plain(img: Path, langs: str) -> str:
    """普通文本模式（TSV 解析失败时的兜底）。"""
    try:
        proc = subprocess.run(
            ["tesseract", str(img), "stdout", "-l", langs],
            capture_output=True, timeout=180)
    except (OSError, subprocess.SubprocessError):
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout.decode("utf-8", "replace")


# TSV 列：level page block par line word left top width height conf text
_TSV_HEADER = ("level", "page_num", "block_num", "par_num", "line_num",
               "word_num", "left", "top", "width", "height", "conf", "text")


def _ocr_page_tsv(img: Path, langs: str) -> str:
    """用 TSV 输出按坐标重建行/列。

    * 先按 y 坐标把词聚成**行**（同一水平线上的词）；
    * 行内按 x 坐标分**列**（间隔明显的地方算换列）；
    * 列之间用制表符隔开，同列内用空格隔开。
    """
    try:
        proc = subprocess.run(
            ["tesseract", str(img), "stdout", "-l", langs, "tsv"],
            capture_output=True, timeout=180)
    except (OSError, subprocess.SubprocessError):
        return ""
    if proc.returncode != 0:
        return ""

    try:
        text = proc.stdout.decode("utf-8", "replace")
    except UnicodeDecodeError:
        return ""

    lines = text.splitlines()
    if not lines or lines[0].split("\t") != list(_TSV_HEADER):
        return ""

    words: list[tuple[int, int, int, int, str]] = []  # (top, bottom, left, right, 词)
    for raw in lines[1:]:
        cols = raw.split("\t")
        if len(cols) < 12:
            continue
        try:
            level = int(cols[0])
            left = int(cols[6])
            top = int(cols[7])
            width = int(cols[8])
            height = int(cols[9])
            conf = float(cols[10])
        except ValueError:
            continue
        if level != 5:              # 5 = word
            continue
        word = cols[11].strip()
        if not word or conf < 30:
            continue
        words.append((top, top + height, left, left + width, word))

    if not words:
        return ""

    avg_h = sum(b - t for t, b, _, _, _ in words) / len(words)
    tol = max(8.0, avg_h * 0.6)
    words.sort(key=lambda w: (w[0], w[2]))

    # 聚成行：按**竖直重叠**判断，而不是比较中心点。
    # 英文和中文的字号不一样时，中心点会差一截，但两行的竖直范围是重叠的。
    rows: list[list[tuple[int, int, int, int, str]]] = []
    row_spans: list[tuple[int, int]] = []
    for w in words:
        wtop, wbot = w[0], w[1]
        if rows:
            rtop, rbot = row_spans[-1]
            overlap = min(rbot, wbot) - max(rtop, wtop)
            smaller = min(rbot - rtop, wbot - wtop)
            if overlap > smaller * 0.45:
                rows[-1].append(w)
                row_spans[-1] = (min(rtop, wtop), max(rbot, wbot))
                continue
        rows.append([w])
        row_spans.append((wtop, wbot))

    return "\n".join(_reconstruct_rows(rows, tol))


def _reconstruct_rows(rows: list[list[tuple[int, int, int, int, str]]],
                      tol: float) -> list[str]:
    """把「词 + 坐标」还原成「行」，行内用制表符分列。

    单独拆出来是为了能直接测——这是 OCR 结果好不好用的关键一步。
    """
    out_lines: list[str] = []
    for row in rows:
        row = sorted(row, key=lambda w: w[2])
        if not row:
            continue
        cells: list[list[str]] = [[row[0][4]]]
        prev_right = row[0][3]
        for w in row[1:]:
            gap = w[2] - prev_right
            if gap > tol * 3:
                cells.append([w[4]])
            else:
                cells[-1].append(w[4])
            prev_right = w[3]
        out_lines.append("\t".join(" ".join(c) for c in cells))
    return out_lines


def _has_lang(lang: str) -> bool:
    try:
        proc = subprocess.run(["tesseract", "--list-langs"],
                              capture_output=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return False
    return lang in proc.stdout.decode("utf-8", "replace").split()


# ------------------------------------------------------------------ 入口

def pdf_candidates(data: bytes) -> list[tuple[str, str]]:
    """把 PDF 抽成文字，返回**按优先级排好的候选列表** ``[(文本, 引擎名), ...]``。

    有时候 poppler 会因为字体子集缺 ``CIDSystemInfo`` 之类的元数据而**漏字**
    （比如 ``apple`` 被截成 ``aple``），而内置解析器反而是全的。
    所以这里把能用的引擎都跑一遍，让上层挑产出词条最多的那个，
    而不是死认第一个有输出的引擎。
    """
    if not data.startswith(b"%PDF"):
        raise PdfError("不是有效的 PDF 文件")
    if len(data) > MAX_BYTES:
        raise PdfError(f"PDF 文件太大（{len(data) // 1024 // 1024}MB），"
                       f"上限 {MAX_BYTES // 1024 // 1024}MB")

    with tempfile.NamedTemporaryFile(prefix="wp-", suffix=".pdf",
                                     delete=False) as fh:
        fh.write(data)
        path = fh.name
    out: list[tuple[str, str]] = []
    try:
        if has_poppler():
            try:
                text = _pdftotext(path)
                if text.strip():
                    out.append((text, "pdftotext"))
            except PdfError:
                pass
        try:
            text = _builtin_extract(data)
            if text.strip():
                out.append((text, "builtin"))
        except PdfError:
            pass
        if not out:
            # 一个文字都没抽到 → 大概率是扫描件，走 OCR
            out.append((_ocr(path), "ocr"))
        return [(t[:MAX_CHARS], e) for t, e in out]
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def pdf_to_text(data: bytes) -> tuple[str, str]:
    """把 PDF 抽成文字，返回 ``(文本, 用到的引擎名)``。

    引擎名可能是 ``pdftotext`` / ``builtin`` / ``ocr``。
    """
    cands = pdf_candidates(data)
    if not cands:
        raise PdfError("这个 PDF 里没提取到任何文字")
    return cands[0]
