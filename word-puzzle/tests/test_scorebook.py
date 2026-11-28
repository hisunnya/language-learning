"""成绩汇总：每个学生 × 每套题一行（班级 / 学号 / 姓名 / 次数 / 完成 / 最高 / 最低 / 平均 / 平均用时），点开看每一次。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, ROOT.as_posix())

from server import scorebook                      # noqa: E402
from tests.test_auth import Client, HttpCase, multipart   # noqa: E402
from tests.test_release import csv_for            # noqa: E402


class TestIsComplete(unittest.TestCase):
    def play(self, **kw):
        return dict({"matched": 12, "total_pairs": 12, "level_count": 2}, **kw)

    def test_all_levels_cleared_is_complete(self):
        self.assertTrue(scorebook.is_complete(self.play(), 2))
        self.assertTrue(scorebook.is_complete(self.play(level_count=3), 2), "重玩过某一关，通关的次数可以比关数多")

    def test_leaving_after_clearing_only_the_first_level_is_not_complete(self):
        """上报的 matched / total_pairs 只是最后一关的状态：通了第 1 关就走人，看起来 12/12，但不算完成。"""
        self.assertFalse(scorebook.is_complete(self.play(level_count=1), 2))

    def test_unfinished_last_level_is_not_complete(self):
        self.assertFalse(scorebook.is_complete(self.play(matched=7), 2))
        self.assertFalse(scorebook.is_complete(self.play(matched=0, total_pairs=0), 2))

    def test_without_a_bank_only_the_last_level_counts(self):
        self.assertTrue(scorebook.is_complete(self.play(level_count=1), None))
        self.assertFalse(scorebook.is_complete(self.play(matched=5), None))


class TestOverHttp(HttpCase):
    counter = 0

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.svc.create_user("T001", "老师", password="Teach3r!pw", role="admin", must_change=False)

    def login(self, no, password):
        c = Client(self.port)
        self.assertEqual(c.json("POST", "/api/auth/login", {"student_no": no, "password": password})[0], 200)
        return c

    def admin(self):
        return self.login("T001", "Teach3r!pw")

    def student(self, name, class_name, no=None):
        type(self).counter += 1
        no = no or "S%04d" % type(self).counter
        user, _ = self.svc.create_user(no, name, password="Ready2026x", must_change=False, class_name=class_name)
        self.app.Handler.db.set_user_tags(user["id"], ["班"])
        return no, user["id"], self.login(no, "Ready2026x")

    def unit_bank(self, admin, units=2, title="新书"):
        body, headers = multipart({}, {"file": ("b.csv", csv_for(units, per=14))})   # 每单元 14 词 → 2 关
        mid = admin.json("POST", "/api/materials", raw=body, headers=headers)[1]["material"]["id"]
        status, res = admin.json("POST", "/api/banks", {
            "source": "material", "material_id": mid, "unit_mode": "per-unit", "level1": "大学", "level2": "英语",
            "level3": "一", "level4": "x", "title": title, "split_units": True, "tags": "班"})
        self.assertEqual(status, 201, res)
        return [b["id"] for b in res["banks"]]

    def play(self, client, bank_id, score, *, levels=2, matched=12, total=12, duration=60, wrong=0, combo=3):
        user = client.json("GET", "/api/auth/me")[1]["user"]
        self.app.Handler.db.insert_score({
            "bank_id": bank_id, "bank_title": "t", "score": score, "matched": matched, "total_pairs": total,
            "wrong": wrong, "best_combo": combo, "duration": duration, "level_count": levels, "detail": [],
            "rule_version": 0,
        }, user_id=user["id"])

    def summary(self, client, query=""):
        status, body = client.json("GET", "/api/scores/summary" + query)
        self.assertEqual(status, 200, body)
        return body

    def test_one_row_per_student_and_bank_with_the_numbers_the_teacher_wants(self):
        admin = self.admin()
        bank = self.unit_bank(admin, units=1)[0]
        no, uid, a = self.student("甲同学", "学前2601")
        self.play(a, bank, 900, levels=2, duration=100)                       # 完成
        self.play(a, bank, 300, levels=1, matched=3, duration=20)             # 中途退出
        self.play(a, bank, 600, levels=1, matched=12, duration=60)            # 通了第一关就走
        rows = [r for r in self.summary(admin)["rows"] if r["user_id"] == uid]
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual((r["class_name"], r["student_no"], r["name"]), ("学前2601", no, "甲同学"))
        self.assertEqual((r["plays"], r["completed"]), (3, 1))
        self.assertEqual((r["best"], r["worst"], r["avg_score"], r["total"]), (900, 300, 600.0, 1800))
        self.assertEqual(r["avg_duration"], 60)
        self.assertEqual(r["bank_id"], bank)
        self.assertTrue(r["bank_title"].endswith("Unit 1 Title"))
        self.assertTrue(r["last_at"])

    def test_the_same_student_on_two_banks_gets_two_rows(self):
        admin = self.admin()
        b1, b2 = self.unit_bank(admin, units=2, title="书二")
        _, uid, a = self.student("乙同学", "工商2601")
        self.play(a, b1, 100); self.play(a, b2, 200)
        rows = [r for r in self.summary(admin)["rows"] if r["user_id"] == uid]
        self.assertEqual(sorted(r["bank_id"] for r in rows), sorted([b1, b2]))

    def test_students_see_only_their_own_rows_and_cannot_ask_for_anyone_elses(self):
        admin = self.admin()
        bank = self.unit_bank(admin, units=1, title="书三")[0]
        _, uid_a, a = self.student("丙", "心理2601")
        _, uid_b, b = self.student("丁", "心理2602")
        self.play(a, bank, 111); self.play(b, bank, 222)
        mine = self.summary(a)["rows"]
        self.assertEqual({r["user_id"] for r in mine}, {uid_a})
        self.assertEqual({r["user_id"] for r in self.summary(a, "?class_name=%s" % "心理2602")["rows"]}, {uid_a}, "筛选参数不能让学生看到别人")
        status, body = a.json("GET", "/api/scores/plays?user_id=%d&bank_id=%d" % (uid_b, bank))
        self.assertEqual(status, 200)
        self.assertEqual([p["score"] for p in body["plays"]], [111], "传了别人的 user_id，拿到的还是自己的")

    def test_the_plays_behind_a_row_are_listed_newest_first_with_a_completed_flag(self):
        admin = self.admin()
        bank = self.unit_bank(admin, units=1, title="书四")[0]
        _, uid, a = self.student("戊", "管会2601")
        self.play(a, bank, 100, levels=1, matched=4, duration=15)
        self.play(a, bank, 800, levels=2, duration=90, wrong=2, combo=6)
        status, body = admin.json("GET", "/api/scores/plays?user_id=%d&bank_id=%d" % (uid, bank))
        plays = body["plays"]
        self.assertEqual([p["score"] for p in plays], [800, 100])
        self.assertEqual((plays[0]["completed"], plays[1]["completed"]), (True, False))
        self.assertEqual((plays[0]["wrong"], plays[0]["best_combo"], plays[0]["duration"], plays[0]["levels_total"]), (2, 6, 90, 2))

    def test_filters_by_class_bank_and_by_name_or_student_number(self):
        admin = self.admin()
        b1, b2 = self.unit_bank(admin, units=2, title="书五")
        no1, _, a = self.student("赵一", "法务会计2601"); no2, _, b = self.student("钱二", "人力2603")
        self.play(a, b1, 10); self.play(b, b2, 20)
        data = self.summary(admin)
        self.assertIn("法务会计2601", data["classes"]); self.assertIn("人力2603", data["classes"])
        self.assertIn(b1, [x["id"] for x in data["banks"]])
        self.assertEqual({r["name"] for r in self.summary(admin, "?class_name=人力2603")["rows"]}, {"钱二"})
        self.assertEqual({r["bank_id"] for r in self.summary(admin, "?bank_id=%d" % b1)["rows"]}, {b1})
        self.assertEqual({r["name"] for r in self.summary(admin, "?q=赵")["rows"]}, {"赵一"})
        self.assertEqual({r["name"] for r in self.summary(admin, "?q=%s" % no2)["rows"]}, {"钱二"})
        self.assertEqual(self.summary(admin, "?q=不存在的人")["rows"], [])

    def test_rows_are_sorted_by_class_then_student_number(self):
        admin = self.admin()
        bank = self.unit_bank(admin, units=1, title="书六")[0]
        for name, cls, no in (("乙", "排序2602", "Z9002"), ("甲", "排序2601", "Z9003"), ("丙", "排序2601", "Z9001")):
            _, _, c = self.student(name, cls, no)
            self.play(c, bank, 1)
        rows = [r for r in self.summary(admin)["rows"] if r["class_name"].startswith("排序")]
        self.assertEqual([r["student_no"] for r in rows], ["Z9001", "Z9003", "Z9002"])

    def test_a_deleted_bank_falls_back_to_the_last_level_rule(self):
        admin = self.admin()
        bank = self.unit_bank(admin, units=1, title="书七")[0]
        _, uid, a = self.student("己", "删除2601")
        self.play(a, bank, 500, levels=1, matched=12)                       # 有题库时：只通了第 1 关（共 2 关）→ 不算完成
        self.assertEqual([r for r in self.summary(admin)["rows"] if r["user_id"] == uid][0]["completed"], 0)
        admin.json("DELETE", "/api/banks/%d" % bank)                          # 软删除：题库还在，总关数照样查得到
        row = [r for r in self.summary(admin)["rows"] if r["user_id"] == uid][0]
        self.assertEqual((row["plays"], row["completed"]), (1, 0), "软删除的题库仍按真实的总关数算")
        self.app.Handler.db.delete_bank(bank)                                 # 真正没了（比如内置题库重建）
        row = [r for r in self.summary(admin)["rows"] if r["user_id"] == uid][0]
        self.assertEqual((row["plays"], row["completed"]), (1, 1), "题库没了查不到总关数，只看最后一关有没有通关")
        self.assertEqual(row["bank_title"], "t", "题库名退回到成绩里记下的名字")

    def test_a_request_must_say_whose_plays_it_wants(self):
        admin = self.admin()
        self.assertEqual(admin.json("GET", "/api/scores/plays")[0], 400)
        self.assertEqual(admin.json("GET", "/api/scores/plays?bank_id=1")[0], 400, "不能退化成「所有人的」")
        self.assertEqual(admin.json("GET", "/api/scores/plays?user_id=abc")[0], 400)

    def test_the_summary_csv_is_for_teachers_and_defuses_formulas(self):
        admin = self.admin()
        bank = self.unit_bank(admin, units=1, title="书八")[0]
        _, _, kid = self.student("=cmd|calc", "导出2601", "X0001")
        self.play(kid, bank, 77)
        status, data = admin.request("GET", "/api/admin/export/score-summary.csv?class_name=%s" % "导出2601")
        text = data.decode("utf-8")
        self.assertEqual(status, 200)
        self.assertTrue(text.startswith("﻿班级,学号,姓名,题库,次数,完成次数,最高分,最低分,平均分,平均用时(秒),最近一次"))
        self.assertIn("导出2601,X0001,'=cmd|calc,", text, "以 = 开头的姓名前面补单引号，免得 Excel 当公式执行")
        self.assertEqual(kid.request("GET", "/api/admin/export/score-summary.csv")[0], 403)

    def test_the_old_endpoints_still_work(self):
        admin = self.admin()
        status, body = admin.json("GET", "/api/scores?limit=5")
        self.assertEqual(status, 200); self.assertIn("stats", body)


class TestLanEdition(HttpCase):
    auth_options = False

    def test_without_accounts_scores_group_by_device_and_show_the_nickname(self):
        c = Client(self.port)
        db = self.app.Handler.db
        for score, level_count in ((100, 1), (300, 2)):
            db.insert_score({"bank_title": "老题库", "device": "d-abc", "nickname": "小明", "score": score,
                             "matched": 5, "total_pairs": 5, "duration": 30, "level_count": level_count,
                             "rule_version": 0}, user_id=None)
        rows = c.json("GET", "/api/scores/summary")[1]["rows"]
        row = [r for r in rows if r["device"] == "d-abc"][0]
        self.assertEqual((row["name"], row["class_name"], row["student_no"], row["plays"]), ("小明", "", "", 2))
        status, body = c.json("GET", "/api/scores/plays?device=d-abc&bank_title=%s" % "老题库")
        self.assertEqual((status, [p["score"] for p in body["plays"]]), (200, [300, 100]))


class TestStatsPage(unittest.TestCase):
    WEB = ROOT / "web"

    def page(self):
        return (self.WEB / "stats.html").read_text(encoding="utf-8")

    def js(self):
        return (self.WEB / "js" / "page-stats.js").read_text(encoding="utf-8")

    def test_the_summary_table_has_every_column_the_teacher_asked_for_in_order(self):
        html = self.page()
        head = html[html.index('id="sumTable"'):html.index("</thead>")]
        import re
        cols = re.findall(r'data-module-zh="([^"]+)"', head)
        self.assertEqual(cols, ["班级", "学号", "姓名", "题库", "次数", "完成", "最高分", "最低分", "平均分", "平均用时", "最近一次"])
        for col in ("班级", "学号", "姓名"):
            self.assertRegex(html, r'<th class="admin-only"[^>]*data-module-zh="%s"' % col, "学生只看自己，这三列对学生隐藏")

    def test_the_old_two_tables_are_gone_and_filters_exist_for_teachers_only(self):
        html = self.page()
        self.assertNotIn('id="byBankTable"', html)
        self.assertNotIn('id="scoreTable"', html)
        for needle in ('id="fClass"', 'id="fBank"', 'id="fSearch"', 'id="btnExport"'):
            self.assertIn(needle, html)
        self.assertRegex(html, r'<div class="admin-filters admin-only">')

    def test_rows_open_to_show_each_game_and_the_details_are_fetched_on_demand(self):
        code = self.js()
        self.assertIn("'/api/scores/summary'", code)
        self.assertIn("'/api/scores/plays?'", code)
        self.assertIn("aria-expanded", code)
        self.assertIn("ev.key !== 'Enter'", code, "键盘也能展开")
        self.assertIn("playsCache[key] = 'loading'", code)
        for column in ("stats_dTime", "stats_dScore", "stats_dMatched", "stats_dWrong", "stats_dCombo", "stats_dDuration", "stats_dLevels", "stats_dDone"):
            self.assertIn(column, code)

    def test_the_export_link_follows_the_filters_and_the_page_redraws_on_language_change(self):
        code = self.js()
        self.assertIn("/api/admin/export/score-summary.csv", code)
        for param in ("class_name=", "bank_id=", "q="):
            self.assertIn(param, code)
        self.assertIn("WPI18N.onChange", code)


if __name__ == "__main__":
    unittest.main()
