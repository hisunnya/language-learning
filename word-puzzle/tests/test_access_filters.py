"""访问记录：记录用的题库和查询串；按页面 / 题库 / 设备 / 内置浏览器 / 系统 / 停留筛选；页面浏览列表；筛选选项；导出和老师的范围。"""
from __future__ import annotations

import csv
import io
import json
import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, ROOT.as_posix())
sys.path.insert(0, (ROOT / "tests").as_posix())

from test_accesslog import AccessCase, UA_CHROME_WIN, UA_IPHONE, UA_WECHAT      # noqa: E402
from server import accesslog                                                    # noqa: E402
from tests.test_auth import Client                                              # noqa: E402


def vid():
    return uuid.uuid4().hex[:24]


class FilterCase(AccessCase):
    def visit(self, conn, path, *, search="", sid=None, ua=UA_IPHONE, active=0, title="页"):
        v = vid()
        status = conn.request("POST", "/api/track", {"event": "view", "vid": v, "sid": sid or vid(), "path": path, "title": title,
                                                      "search": search, "client": {}},
                              headers={"User-Agent": ua, "X-Wp-Edge-Xff": "198.51.100.20"})[0]
        self.assertEqual(status, 204)
        if active:
            conn.request("POST", "/api/track", {"event": "leave", "vid": v, "active": active},
                         headers={"User-Agent": ua, "X-Wp-Edge-Xff": "198.51.100.20"})
        return v

    def bank(self, title):
        return self.db.insert_bank({"title": title, "level1": "a", "level2": "b", "level3": "c", "level4": "d", "source": "seed",
                                    "word_count": 0, "unit_count": 0}, [])

    def pv(self, admin, **params):
        q = "&".join("%s=%s" % kv for kv in params.items())
        status, body = admin.json("GET", "/api/admin/pageviews?limit=500" + ("&" + q if q else ""))
        self.assertEqual(status, 200, body)
        return body


class TestRecordingTheBank(FilterCase):
    def test_the_bank_in_the_address_is_recorded_with_its_title_at_that_time(self):
        no, c = self.student("题库生")
        bid = self.bank("人教版 七年级上册")
        v = self.visit(c, "/word-puzzle/practice.html", search="?bank=%d&x=1" % bid)
        r = self.db.one("SELECT query, bank_id, bank_title FROM page_views WHERE vid=?", (v,))
        self.assertEqual((r["bank_id"], r["bank_title"], r["query"]), (bid, "人教版 七年级上册", "?bank=%d&x=1" % bid))
        self.db.execute("UPDATE banks SET title='改名了' WHERE id=?", (bid,))
        self.assertEqual(self.db.one("SELECT bank_title FROM page_views WHERE vid=?", (v,))["bank_title"], "人教版 七年级上册",
                         "题库以后改名，记录还是当时的样子")

    def test_a_missing_bank_or_no_bank_leaves_the_fields_empty_and_nothing_breaks(self):
        no, c = self.student("无题库")
        for search in ("", "?bank=99999999", "?bank=abc", "?mybank=5", "?bank=1;drop"):
            v = self.visit(c, "/word-puzzle/play.html", search=search)
            r = self.db.one("SELECT bank_id, bank_title FROM page_views WHERE vid=?", (v,))
            self.assertEqual(r["bank_title"], "", search)
        v = self.visit(c, "/word-puzzle/play.html", search="?bank=99999999")
        self.assertEqual(self.db.one("SELECT bank_id FROM page_views WHERE vid=?", (v,))["bank_id"], 99999999,
                         "题库已被删掉时编号还留着，标题是空的")

    def test_the_query_string_is_cleaned_and_capped(self):
        no, c = self.student("长查询")
        v = self.visit(c, "/word-puzzle/", search="?a=" + "x" * 500 + "\n\x00")
        q = self.db.one("SELECT query FROM page_views WHERE vid=?", (v,))["query"]
        self.assertLessEqual(len(q), 300)
        self.assertNotRegex(q, r"[\x00-\x1f]")

    def test_page_names(self):
        self.assertEqual([accesslog.page_file(p) for p in ("/word-puzzle/", "/word-puzzle/practice.html", "", "/word-puzzle/index.html", "/")],
                         ["index.html", "practice.html", "index.html", "index.html", "index.html"])


class TestFilters(FilterCase):
    def setUp(self):
        self.admin_client = self.admin()
        self.cls = "筛选%d班" % (type(self).counter + 1)
        self.no, self.c = self.student("筛选甲", self.cls)
        self.bank_a, self.bank_b = self.bank("词库甲%s" % self.cls), self.bank("词库乙%s" % self.cls)
        self.visit(self.c, "/word-puzzle/practice.html", search="?bank=%d" % self.bank_a, active=40, title="读音练习")
        self.visit(self.c, "/word-puzzle/play.html", search="?bank=%d" % self.bank_b, active=5, title="游戏")
        self.visit(self.c, "/word-puzzle/", title="首页")
        self.visit(self.c, "/word-puzzle/leaderboard.html", ua=UA_WECHAT, title="积分榜")
        self.visit(self.c, "/word-puzzle/stats.html", ua=UA_CHROME_WIN, title="成绩")

    def titles(self, **params):
        return sorted(r["title"] for r in self.pv(self.admin_client, class_name=self.cls, **params)["pageviews"])

    def test_by_page_including_the_home_page(self):
        self.assertEqual(self.titles(page="practice.html"), ["读音练习"])
        self.assertEqual(self.titles(page="index.html"), ["首页"])
        self.assertEqual(len(self.titles()), 5)

    def test_by_bank_id_or_a_word_of_its_title(self):
        self.assertEqual(self.titles(bank=self.bank_a), ["读音练习"])
        self.assertEqual(self.titles(bank="词库乙"), ["游戏"])
        self.assertEqual(self.titles(bank="不存在的词"), [])

    def test_by_device_in_app_browser_and_system(self):
        self.assertEqual(self.titles(app="any"), ["积分榜"])
        self.assertEqual(self.titles(app="WeChat"), ["积分榜"], "按内置浏览器的名字筛，不管版本号")
        self.assertEqual(sorted(self.titles(app="none")), ["成绩", "游戏", "读音练习", "首页"])
        self.assertEqual(self.titles(device="desktop"), ["成绩"])
        self.assertEqual(self.titles(os="Windows"), ["成绩"])
        self.assertEqual(self.titles(device="bogus"), sorted(["成绩", "游戏", "积分榜", "读音练习", "首页"]), "不认识的值忽略，不会查出空")

    def test_minimum_stay(self):
        self.assertEqual(self.titles(min_seconds=30), ["读音练习"])
        self.assertEqual(len(self.titles(min_seconds="abc")), 5)

    def test_the_search_box_also_finds_page_titles_and_bank_titles(self):
        self.assertEqual(self.titles(q="读音"), ["读音练习"])
        self.assertEqual(self.titles(q="词库甲"), ["读音练习"])

    def test_filters_are_combined_and_user_input_never_reaches_the_sql(self):
        self.assertEqual(self.titles(page="practice.html", bank=self.bank_b), [])
        self.assertEqual(self.titles(page="practice.html", min_seconds=30, device="mobile"), ["读音练习"])
        evil = "' OR 1=1 --"
        for key in ("page", "bank", "os", "app", "q"):
            self.assertEqual(self.pv(self.admin_client, **{key: evil.replace(" ", "%20"), "class_name": self.cls})["total"], 0, key)

    def test_the_sessions_tab_uses_the_same_filters_and_lists_pages_and_banks(self):
        status, body = self.admin_client.json("GET", "/api/admin/visits?class_name=%s&bank=%d" % (self.cls, self.bank_a))
        self.assertEqual(status, 200)
        self.assertEqual(body["total"], 1)
        row = body["sessions"][0]
        self.assertEqual(row["pages_seen"], ["practice.html"])
        self.assertEqual(row["banks"], ["词库甲%s" % self.cls])

    def test_the_export_follows_the_filters_and_has_the_new_columns(self):
        status, raw = self.admin_client.request("GET", "/api/admin/export/page-views.csv?class_name=%s&page=practice.html" % self.cls)
        self.assertEqual(status, 200)
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8") if isinstance(raw, bytes) else raw)))
        self.assertEqual([r["title"] for r in rows], ["读音练习"])
        self.assertEqual((rows[0]["bank_title"], rows[0]["bank_id"]), ("词库甲%s" % self.cls, str(self.bank_a)))
        self.assertIn("query", rows[0])


class TestPageMatchIsExact(FilterCase):
    def test_a_page_filter_matches_the_file_name_not_a_part_of_it(self):
        cls = "精确%d班" % (type(self).counter + 1)
        no, c = self.student("精确生", cls)
        self.visit(c, "/word-puzzle/play.html", title="游戏")
        self.visit(c, "/word-puzzle/replay.html", title="重玩")
        self.visit(c, "/word-puzzle/play.html.bak", title="备份")
        a = self.admin()
        self.assertEqual([r["title"] for r in self.pv(a, class_name=cls, page="play.html")["pageviews"]], ["游戏"])


class TestOptionsAndScope(FilterCase):
    def test_options_list_only_what_exists_and_students_cannot_read_them(self):
        no, c = self.student("选项生", "选项班")
        bid = self.bank("选项词库")
        self.visit(c, "/word-puzzle/practice.html", search="?bank=%d" % bid, ua=UA_WECHAT)
        a = self.admin()
        status, body = a.json("GET", "/api/admin/visits/options")
        self.assertEqual(status, 200)
        pages = {p["page"]: p for p in body["pages"]}
        self.assertEqual((pages["practice.html"]["zh"], pages["practice.html"]["en"]), ("读音练习", "Pronunciation practice"))
        self.assertIn((bid, "选项词库"), [(b["id"], b["title"]) for b in body["banks"]])
        self.assertIn("WeChat", body["apps"])
        self.assertTrue(all(" " not in a for a in body["apps"]), "下拉框里只放名字，不带版本号")
        self.assertTrue(body["os"])
        self.assertEqual(c.request("GET", "/api/admin/visits/options")[0], 403)
        self.assertEqual(c.request("GET", "/api/admin/pageviews")[0], 403)
        self.assertEqual(Client(self.port).request("GET", "/api/admin/pageviews")[0], 401)

    def test_a_teacher_sees_only_the_page_views_of_their_own_students(self):
        self.svc.create_user("TX", "甲老师", password="Teach3r!pw", role="teacher", must_change=False)
        self.svc.create_user("TY", "乙老师", password="Teach3r!pw", role="teacher", must_change=False)
        tx, _ = self.login("TX", "Teach3r!pw"); ty, _ = self.login("TY", "Teach3r!pw")
        tx_id = self.svc.get_by_student_no("TX")["id"]
        no, c = self.student("甲的学生", "师甲班")
        sid = self.svc.get_by_student_no(no)["id"]
        from server import tenancy
        tenancy.unlink_student(self.db, self.db.default_teacher_id(), sid)
        tenancy.link_student(self.db, tx_id, sid, None)
        bid = self.bank("只有甲看得到的词库名")
        self.visit(c, "/word-puzzle/practice.html", search="?bank=%d" % bid, title="读音练习")
        mine = self.pv(tx, class_name="师甲班")
        self.assertEqual([r["title"] for r in mine["pageviews"]], ["读音练习"])
        self.assertEqual(self.pv(ty, class_name="师甲班")["pageviews"], [], "乙老师看不到甲老师学生的记录")
        self.assertNotIn(bid, [b["id"] for b in ty.json("GET", "/api/admin/visits/options")[1]["banks"]], "选项里也不泄露")
        status, raw = ty.request("GET", "/api/admin/export/page-views.csv?class_name=师甲班")
        self.assertNotIn("只有甲看得到的词库名", raw.decode("utf-8") if isinstance(raw, bytes) else raw)


if __name__ == "__main__":
    unittest.main()


class TestLongCellsInVisitsTable(unittest.TestCase):
    """访问记录里「看过的页面」「用到的题库」很长，不能把单元格撑宽：默认窄、可拖宽、悬浮显示全文。"""

    def test_long_cells_are_clipped_resizable_and_show_a_wrapping_tip(self):
        from pathlib import Path
        web = Path(__file__).resolve().parent.parent / "web"
        js = (web / "js" / "page-visits.js").read_text(encoding="utf-8")
        css = (web / "css" / "auth.css").read_text(encoding="utf-8")
        self.assertIn("clip((r.pages_seen", js)
        self.assertIn("clip((r.banks", js)
        self.assertIn("closest('.clip')) return", js, "点文字格不能展开行，否则没法选字")
        self.assertIn("scrollWidth", js, "只有被截断时才显示悬浮窗")
        self.assertRegex(css, r"\.sum-row \.clip \{[^}]*resize: horizontal[^}]*\}")
        self.assertRegex(css, r"\.sum-row \.clip \{[^}]*text-overflow: ellipsis[^}]*\}")
        self.assertRegex(css, r"\.sum-row \.clip \{[^}]*user-select: text[^}]*\}")
        self.assertRegex(css, r"\.clip-tip \{[^}]*white-space: normal[^}]*overflow-wrap: anywhere")
