"""模板：老师下载的词表模板、名单模板，填好上传必须一字不差地识别出来（用的就是上传时的解析器）。"""
from __future__ import annotations

import io
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, ROOT.as_posix())

from server import materials, roster, templates, xlsx      # noqa: E402
from tests.test_auth import Client, HttpCase               # noqa: E402


class TestWordListTemplate(unittest.TestCase):
    def test_both_languages_and_formats_parse_back_with_units_carried_down(self):
        for lang in ("zh", "en"):
            for fmt in ("xlsx", "csv"):
                name, data, _ctype = templates.build("wordlist", fmt, lang)
                kind, words = materials.parse_material(name, data)
                self.assertEqual(kind, fmt)
                self.assertEqual([(w["unit"], w["en"], w["cn"]) for w in words], [
                    ("Unit 1", "apple", "苹果"), ("Unit 1", "take care of", "照顾；照看"),
                    ("Unit 2", "eradicate", "根除；消灭"), ("Unit 2", "staple food", "主食")], (lang, fmt))
                self.assertEqual(words[0]["ipa"], "/ˈæpəl/")
                self.assertEqual(words[1]["pos"], "phr.")

    def test_the_excel_file_has_a_notes_sheet_that_is_not_read_as_words(self):
        _name, data, _ctype = templates.build("wordlist", "xlsx", "zh")
        z = zipfile.ZipFile(io.BytesIO(data))
        self.assertIn("xl/worksheets/sheet2.xml", z.namelist())
        self.assertIn("填写说明", z.read("xl/workbook.xml").decode("utf-8"))
        self.assertIn("ySplit=\"1\"", z.read("xl/worksheets/sheet1.xml").decode("utf-8"), "表头冻结")

    def test_a_teachers_excel_with_its_own_rows_and_errors(self):
        data = xlsx.build([("词表", [["单元", "英文", "中文"], ["Unit 3", "soar", "飞速上涨"], ["", "", ""], ["", "humble", "谦虚的"],
                                      ["", "only english", ""]])])
        _kind, words = materials.parse_material("我的词表.xlsx", data)
        self.assertEqual([(w["unit"], w["en"]) for w in words], [("Unit 3", "soar"), ("Unit 3", "humble")], "空行跳过，缺中文的行不要")
        with self.assertRaises(materials.ParseError):
            materials.parse_material("x.xlsx", xlsx.build([("s", [["a", "b"], ["c", "d"]])]))
        with self.assertRaises(materials.ParseError) as caught:
            materials.parse_material("old.xls", b"\xd0\xcf\x11\xe0")
        self.assertIn(".xlsx", str(caught.exception))


class TestRosterTemplate(unittest.TestCase):
    def test_both_languages_and_formats_import_cleanly(self):
        for lang in ("zh", "en"):
            for fmt in ("xlsx", "csv"):
                name, data, _ctype = templates.build("roster", fmt, lang)
                table = roster.parse_roster(name, data)
                self.assertEqual(table.get("errors") or [], [], (lang, fmt))
                self.assertEqual([r["student_no"] for r in table["rows"]], ["2026001", "2026002"], (lang, fmt))
                self.assertEqual(table["rows"][0]["class_name"], "一班" if lang == "zh" else "Class 1")
                self.assertEqual(table["ignored_columns"], [])

    def test_student_numbers_are_text_cells(self):
        _name, data, _ctype = templates.build("roster", "xlsx", "zh")
        sheet = zipfile.ZipFile(io.BytesIO(data)).read("xl/worksheets/sheet1.xml").decode("utf-8")
        self.assertIn('r="A2" t="inlineStr" s="3"', sheet, "学号一列是文本格式，长学号不会变成科学计数法")

    def test_rows_added_below_the_samples_are_text_too(self):
        _name, data, _ctype = templates.build("roster", "xlsx", "zh")
        sheet = zipfile.ZipFile(io.BytesIO(data)).read("xl/worksheets/sheet1.xml").decode("utf-8")
        self.assertRegex(sheet, r'<col min="1" max="1" [^>]*style="3"', "整列是文本格式，不只是示例那两格")
        empty = zipfile.ZipFile(io.BytesIO(xlsx.build([("空", [])]))).read("xl/worksheets/sheet1.xml").decode("utf-8")
        self.assertNotIn("<cols>", empty, "没有列就不写 <cols>（空的 <cols/> Excel 认为文件损坏）")


def _workbook(sheet_xml: str, first: str = "sheet1.xml", extra: dict | None = None) -> bytes:
    """手写一个最小的 xlsx：工作簿的第一页指向 first。"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("xl/workbook.xml", '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                   '<sheets><sheet name="名单" sheetId="1" r:id="rId9"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId9" Type="x" Target="worksheets/%s"/></Relationships>' % first)
        z.writestr("xl/worksheets/" + first, '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                   "<sheetData>%s</sheetData></worksheet>" % sheet_xml)
        for name, body in (extra or {}).items():
            z.writestr(name, body)
    return buf.getvalue()


def _row(r, *values, refs=True):
    cells = "".join('<c%s t="inlineStr"><is><t>%s</t></is></c>' % (' r="%s%s"' % (chr(65 + i), r) if refs else "", v)
                    for i, v in enumerate(values))
    return '<row%s>%s</row>' % (' r="%d"' % r if refs else "", cells)


class TestRosterXlsxReading(unittest.TestCase):
    def test_row_numbers_survive_blank_rows(self):
        data = _workbook(_row(1, "学号", "姓名") + _row(4, "2026009", "王五"))
        self.assertEqual([(r["_row"], r["student_no"]) for r in roster.parse_roster("a.xlsx", data)["rows"]], [(4, "2026009")],
                         "报错里的「第 N 行」和 Excel 里一致")

    def test_cells_without_references_are_read_in_order(self):
        data = _workbook(_row(1, "学号", "姓名", "班级", refs=False) + _row(2, "2026010", "赵六", "二班", refs=False))
        row = roster.parse_roster("a.xlsx", data)["rows"][0]
        self.assertEqual((row["student_no"], row["name"], row["class_name"], row["_row"]), ("2026010", "赵六", "二班", 2))

    def test_the_first_tab_is_read_even_when_its_file_is_not_sheet1(self):
        decoy = '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>%s</sheetData></worksheet>' % (
            _row(1, "学号", "姓名") + _row(2, "999", "错的"))
        data = _workbook(_row(1, "学号", "姓名") + _row(2, "2026011", "对的"), first="sheet3.xml",
                         extra={"xl/worksheets/sheet1.xml": decoy})
        self.assertEqual(roster.parse_roster("a.xlsx", data)["rows"][0]["name"], "对的")

    def test_csv_row_numbers_survive_blank_lines(self):
        data = "学号,姓名\r\n\r\n2026012,孙七\r\n".encode("utf-8")
        self.assertEqual(roster.parse_roster("a.csv", data)["rows"][0]["_row"], 3)


class TestTemplateDownload(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.svc.create_user("T001", "孙老师", password="Teach3r!pw", role="admin", must_change=False)
        cls.svc.create_user("S001", "学生", password="Ready2026x", must_change=False)

    def login(self, no, pw):
        c = Client(self.port)
        c.json("POST", "/api/auth/login", {"student_no": no, "password": pw})
        return c

    def test_teachers_download_and_students_cannot(self):
        c = self.login("T001", "Teach3r!pw")
        status, data = c.request("GET", "/api/templates/wordlist.xlsx")
        self.assertEqual(status, 200)
        self.assertEqual(data[:2], b"PK")
        self.assertIn("attachment", c.last.getheader("Content-Disposition"))
        self.assertIn("UTF-8''", c.last.getheader("Content-Disposition"), "中文文件名")
        status, data = c.request("GET", "/api/templates/roster.csv?lang=en")
        self.assertEqual(status, 200)
        self.assertTrue(data.decode("utf-8-sig").startswith("student_no,name,class"))
        self.assertEqual(c.request("GET", "/api/templates/other.xlsx")[0], 404)
        self.assertEqual(self.login("S001", "Ready2026x").request("GET", "/api/templates/wordlist.xlsx")[0], 403)

    def test_pages_link_the_templates(self):
        web = ROOT / "web"
        self.assertIn('data-template="wordlist.xlsx"', (web / "bank.html").read_text(encoding="utf-8"))
        self.assertIn('data-template="roster.xlsx"', (web / "admin.html").read_text(encoding="utf-8"))
        self.assertIn('accept=".xlsx,', (web / "bank.html").read_text(encoding="utf-8"))
        self.assertIn("templateLinks:", (web / "js" / "api.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
