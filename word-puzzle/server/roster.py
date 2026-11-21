"""学生名单解析：CSV（UTF-8 / GBK 都行）和 xlsx，列名中英文都认。

只用标准库。手机号这类用不到的列会被识别出来**直接丢弃**（不进内存之外的任何地方），
并在结果里告诉调用方“忽略了哪些列”，避免无意中把学生的隐私信息存进服务器。
"""
from __future__ import annotations

import csv
import io
import re
import zipfile
from decimal import Decimal, InvalidOperation
from xml.etree import ElementTree

MAX_SHEET_BYTES = 20 * 1024 * 1024

# 规范列名 -> 表头里可能写的叫法（比较时去掉空格并转小写）
ALIASES = {
    "student_no": {"学号", "student_no", "studentno", "student_id", "studentid", "sno", "id"},
    "name": {"姓名", "名字", "name"},
    "class_name": {"班级", "班", "class", "class_name", "classname"},
    "college": {"学院", "college", "school"},
    "department": {"院系", "系", "系别", "department", "dept"},
    "password": {"初始密码", "密码", "password", "initial_password"},
    "tags": {"标签", "标签组", "tag", "tags"},
}
# 认识但不使用的列：识别出来是为了明确地丢弃，并提示调用方
DISCARDED = {
    "phone": {"手机号", "手机", "电话", "手机号码", "phone", "mobile", "tel"},
    "username": {"用户名", "username", "user", "账号"},
}


class RosterError(ValueError):
    """名单文件读不了或格式不对，message 直接展示给用户。"""


def _norm(header: str) -> str:
    return re.sub(r"\s+", "", str(header or "")).lower()


def decode_text(data: bytes) -> str:
    """Excel 在中文系统里另存为 CSV 往往是 GBK，所以 UTF-8 失败就退到 GB18030。"""
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise RosterError("文件编码无法识别，请另存为 UTF-8 的 CSV 或 xlsx")


def _read_csv(data: bytes) -> list[list[str]]:
    text = decode_text(data)
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    return [[cell.strip() for cell in row] for row in csv.reader(io.StringIO(text), dialect)]


# ---------------- xlsx ----------------

_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _col_index(ref: str) -> int:
    letters = re.match(r"[A-Z]+", ref or "")
    if not letters:
        return 0
    n = 0
    for ch in letters.group(0):
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def _number_text(raw: str) -> str:
    """Excel 里的学号常是数字：2021001 存成 2021001 或 2.021001E6，统一还原成整数文本。"""
    raw = raw.strip()
    try:
        value = Decimal(raw)
    except InvalidOperation:
        return raw
    if value == value.to_integral_value():
        return str(int(value))
    return raw


def _first_sheet(zf: zipfile.ZipFile) -> str:
    """工作簿里排第一的工作表（老师看到的第一个标签页）。

    按 workbook.xml 的顺序和它的关系文件找，而不是按文件名：文件名 sheet10 会排在 sheet2 前面，
    挪过顺序的工作簿里 sheet1.xml 也不一定是第一页。找不到时退回到编号最小的 sheetN.xml。"""
    names = set(zf.namelist())
    try:
        book = ElementTree.fromstring(zf.read("xl/workbook.xml"))
        rels = ElementTree.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        first = book.find("m:sheets/m:sheet", _NS)
        rid = first.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id") if first is not None else None
        for rel in rels:
            if rel.get("Id") == rid:
                target = rel.get("Target", "").lstrip("/")
                path = target if target.startswith("xl/") else "xl/" + target
                if path in names:
                    return path
    except (KeyError, ElementTree.ParseError):
        pass
    sheets = [n for n in names if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n)]
    if not sheets:
        raise RosterError("xlsx 里找不到工作表")
    return min(sheets, key=lambda n: int(re.search(r"(\d+)\.xml$", n).group(1)))


def _si_text(si) -> str:
    """共享字符串：纯文本 <t>，或者富文本的若干 <r><t>；不要日文注音 <rPh> 里的字。"""
    m = "{%s}" % _NS["m"]
    parts = [si.findtext(m + "t") or ""]
    parts += [r.findtext(m + "t") or "" for r in si.findall(m + "r")]
    return "".join(parts)


def _read_xlsx_numbered(data: bytes) -> list[tuple[int, list[str]]]:
    """第一张工作表的 [(Excel 里的行号, [单元格文本…])]，空行不出现，但行号保持原样（报错时老师能对上）。"""
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except (zipfile.BadZipFile, OSError) as exc:
        raise RosterError(f"不是有效的 xlsx 文件：{exc}") from exc
    sheet = _first_sheet(zf)
    if zf.getinfo(sheet).file_size > MAX_SHEET_BYTES:
        raise RosterError("工作表过大（解压后超过 20MB）")

    shared: list[str] = []
    if "xl/sharedStrings.xml" in zf.namelist():
        if zf.getinfo("xl/sharedStrings.xml").file_size > MAX_SHEET_BYTES:
            raise RosterError("共享字符串表过大")
        root = ElementTree.fromstring(zf.read("xl/sharedStrings.xml"))
        shared = [_si_text(si) for si in root.findall("m:si", _NS)]

    root = ElementTree.fromstring(zf.read(sheet))
    rows: list[tuple[int, list[str]]] = []
    row_no = 0
    for row in root.iter("{%s}row" % _NS["m"]):
        # 行号、列号优先看 r 属性；有的程序生成的文件不写 r，就按顺序数
        row_no = int(row.get("r")) if (row.get("r") or "").isdigit() else row_no + 1
        cells: dict[int, str] = {}
        col = -1
        for c in row.findall("m:c", _NS):
            col = _col_index(c.get("r")) if c.get("r") else col + 1
            kind = c.get("t")
            v = c.find("m:v", _NS)
            if kind == "inlineStr":
                text = "".join(t.text or "" for t in c.iter("{%s}t" % _NS["m"]))
            elif v is None or v.text is None:
                text = ""
            elif kind == "s":
                idx = int(v.text)
                text = shared[idx] if 0 <= idx < len(shared) else ""
            elif kind in ("str", "e", "b"):
                text = v.text
            else:
                text = _number_text(v.text)
            cells[col] = text.strip()
        if any(cells.values()):
            width = max(cells) + 1
            rows.append((row_no, [cells.get(i, "") for i in range(width)]))
    return rows


def _read_xlsx(data: bytes) -> list[list[str]]:
    """第一张工作表的行（空行去掉）。词表上传（materials.py）也用它。"""
    return [cells for _no, cells in _read_xlsx_numbered(data)]


# ---------------- 对外入口 ----------------

def parse_roster(filename: str, data: bytes) -> dict:
    """返回 {rows: [{_row, student_no, name, class_name, college, department, password}],
    ignored_columns: [...], errors: [...]}。errors 里是没法使用的行，其余行照常返回。"""
    name = (filename or "").lower()
    if name.endswith(".xlsx") or data[:2] == b"PK":
        numbered = _read_xlsx_numbered(data)
    elif name.endswith(".xls"):
        raise RosterError("不支持旧版 .xls，请另存为 .xlsx 或 CSV")
    else:
        numbered = list(enumerate(_read_csv(data), start=1))
    # 空行去掉，但每行记住它在文件里的行号：报错「第 N 行」要和老师在 Excel 里看到的一致
    numbered = [(no, row) for no, row in numbered if any(cell for cell in row)]
    if not numbered:
        raise RosterError("名单是空的")
    table = [row for _no, row in numbered]

    header = [_norm(h) for h in table[0]]
    mapping: dict[int, str] = {}
    ignored: list[str] = []
    for i, h in enumerate(header):
        for canonical, names in ALIASES.items():
            if h in {_norm(n) for n in names} and canonical not in mapping.values():
                mapping[i] = canonical
                break
        else:
            for names in DISCARDED.values():
                if h in {_norm(n) for n in names}:
                    ignored.append(table[0][i])
                    break
    missing = [c for c in ("student_no", "name") if c not in mapping.values()]
    if missing:
        raise RosterError("表头里必须有「学号」和「姓名」两列（可选：班级、学院、院系、初始密码、标签）")

    rows, errors = [], []
    for line_no, raw in numbered[1:]:
        rec = {"_row": line_no, "student_no": "", "name": "", "class_name": "",
               "college": "", "department": "", "password": ""}
        for i, canonical in mapping.items():
            rec[canonical] = raw[i].strip() if i < len(raw) else ""
        if not rec["student_no"] and not rec["name"]:
            continue
        rows.append(rec)
    return {"rows": rows, "ignored_columns": ignored, "errors": errors}
