"""极简的 xlsx 生成（只用标准库）：给老师下载的模板用。

每个工作表是一组行（字符串）；第一行是表头（加粗、浅色底、冻结），列宽按内容估算。
文字一律写成 inlineStr，不用共享字符串表，Excel / WPS / Numbers 都能打开，roster.py 的读取也认。
"""
from __future__ import annotations

import io
import zipfile
from xml.sax.saxutils import escape

_CT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
{sheets}
</Types>"""
_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""
_STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="3"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font>
<font><i/><sz val="11"/><color rgb="FF6B7280"/><name val="Calibri"/></font></fonts>
<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFE8EEFF"/><bgColor indexed="64"/></patternFill></fill></fills>
<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="4"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/>
<xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/>
<xf numFmtId="49" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/></cellXfs>
</styleSheet>"""


def _col(i: int) -> str:
    name = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        name = chr(65 + r) + name
    return name


def _width(text: str) -> float:
    return sum(2.0 if ord(ch) > 0x2E80 else 1.1 for ch in text) + 2


def _sheet(rows: list[list[str]], text_columns: int, notes: bool) -> str:
    widths: dict[int, float] = {}
    body = []
    for r, row in enumerate(rows, start=1):
        cells = []
        for c, value in enumerate(row):
            value = "" if value is None else str(value)
            widths[c] = min(60.0, max(widths.get(c, 8.0), _width(value)))
            style = 1 if r == 1 else (3 if c < text_columns else 0)
            cells.append('<c r="%s%d" t="inlineStr" s="%d"><is><t xml:space="preserve">%s</t></is></c>'
                         % (_col(c), r, style, escape(value)))
        body.append('<row r="%d">%s</row>' % (r, "".join(cells)))
    # 文本列的格式也写在 <col> 上：老师在示例行下面新加的行同样是文本，长学号不会变成 2.026E+06
    cols = "".join('<col min="%d" max="%d" width="%.1f" customWidth="1"%s/>'
                   % (c + 1, c + 1, w, ' style="3"' if c < text_columns else "") for c, w in sorted(widths.items()))
    cols = "<cols>%s</cols>" % cols if cols else ""          # 空的 <cols/> 不合规范，Excel 会报文件损坏
    freeze = ("" if notes else '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" '
              'activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>')
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">%s%s'
            '<sheetData>%s</sheetData></worksheet>' % (freeze, cols, "".join(body)))


def build(sheets: list[tuple[str, list[list[str]]]], text_columns: int = 0) -> bytes:
    """sheets：[(工作表名, 行)]。第一个是要填的表（表头加粗、冻结）；名字里带「说明」/ Notes 的是说明页。
    text_columns：前几列设成「文本」格式（学号、单元号不会被 Excel 改成数字或日期）。"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CT.format(sheets="".join(
            '<Override PartName="/xl/worksheets/sheet%d.xml" ContentType="application/vnd.openxmlformats-officedocument.'
            'spreadsheetml.worksheet+xml"/>' % (i + 1) for i in range(len(sheets)))))
        z.writestr("_rels/.rels", _RELS)
        z.writestr("xl/workbook.xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>%s</sheets></workbook>'
                   % "".join('<sheet name="%s" sheetId="%d" r:id="rId%d"/>' % (escape(name[:31]), i + 1, i + 1)
                             for i, (name, _rows) in enumerate(sheets)))
        z.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">%s'
                   '<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
                   'Target="styles.xml"/></Relationships>'
                   % ("".join('<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                              'relationships/worksheet" Target="worksheets/sheet%d.xml"/>' % (i + 1, i + 1)
                              for i in range(len(sheets))), len(sheets) + 1))
        z.writestr("xl/styles.xml", _STYLES)
        for i, (name, rows) in enumerate(sheets):
            notes = "说明" in name or "notes" in name.lower()
            z.writestr("xl/worksheets/sheet%d.xml" % (i + 1), _sheet(rows, 0 if notes else text_columns, notes))
    return buf.getvalue()
