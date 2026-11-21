"""积分榜：谁看得到哪个班、怎么排名、0 分不上榜、本周榜、不泄露学号。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_auth import Client                      # noqa: E402
from test_tenancy import TenantCase               # noqa: E402
from server import leaderboard                    # noqa: E402


class LeaderboardCase(TenantCase):
    def pupil(self, teacher, name, class_name):
        no = self.new_no("L")
        self.roster(teacher, [(no, name, class_name)])
        self.svc.db.execute("UPDATE users SET must_change=0, pw_hash=(SELECT pw_hash FROM users WHERE student_no='TA') "
                            "WHERE student_no=?", (no,))
        return no, self.svc.get_by_student_no(no)["id"]

    def play(self, uid, *points, when=None):
        for p in points:
            sid = self.db.insert_score({"score": p, "bank_title": "x"}, user_id=uid)
            if when:
                self.db.execute("UPDATE scores SET created_at=? WHERE id=?", (when, sid))

    def board(self, client, **params):
        q = "&".join("%s=%s" % kv for kv in params.items())
        status, res = client.json("GET", "/api/leaderboard" + ("?" + q if q else ""))
        self.assertEqual(status, 200, res)
        return res

    def fresh_class(self, teacher, label):
        type(self).counter += 1
        return "%s%d班" % (label, self.counter)


class TestWhoSeesWhat(LeaderboardCase):
    def test_a_student_sees_only_their_own_class_and_only_names_and_points(self):
        cls, other = self.fresh_class(self.ta, "甲"), self.fresh_class(self.ta, "乙")
        me, me_id = self.pupil(self.ta, "小明", cls)
        _, mate_id = self.pupil(self.ta, "小红", cls)
        _, far_id = self.pupil(self.ta, "隔壁班", other)
        self.play(me_id, 50)
        self.play(mate_id, 80, 10)
        self.play(far_id, 999)
        res = self.board(self.login_as(me, "Teach3r!pw"))
        self.assertEqual([(e["name"], e["points"], e["rank"]) for e in res["entries"]], [("小红", 90, 1), ("小明", 50, 2)])
        self.assertEqual(res["class_name"], cls)
        self.assertEqual(res["scope"], "class")
        self.assertEqual(res["classes"], [], "学生拿不到班级清单")
        for e in res["entries"]:
            self.assertEqual(set(e) - {"rank", "name", "points", "me", "class_name", "badges"}, set(), "不带学号等多余字段（徽章只是档次和玩法）")
        self.assertTrue([e for e in res["entries"] if e["me"]][0]["name"] == "小明")

    def test_the_class_parameter_is_ignored_for_students(self):
        cls, other = self.fresh_class(self.ta, "甲"), self.fresh_class(self.ta, "乙")
        me, me_id = self.pupil(self.ta, "我", cls)
        _, far_id = self.pupil(self.ta, "别班的", other)
        self.play(me_id, 5)
        self.play(far_id, 500)
        res = self.board(self.login_as(me, "Teach3r!pw"), class_name=other)
        self.assertEqual([e["name"] for e in res["entries"]], ["我"])

    def test_same_class_name_under_a_different_teacher_is_not_a_classmate(self):
        """不同学校 / 不同老师的「一班」不能混在一起。"""
        cls = self.fresh_class(self.ta, "同名")
        me, me_id = self.pupil(self.ta, "甲的学生", cls)
        _, stranger = self.pupil(self.tb, "乙的学生", cls)
        self.play(me_id, 10)
        self.play(stranger, 300)
        res = self.board(self.login_as(me, "Teach3r!pw"))
        self.assertEqual([e["name"] for e in res["entries"]], ["甲的学生"])

    def test_a_student_does_not_see_deleted_or_disabled_classmates(self):
        cls = self.fresh_class(self.ta, "删")
        me, me_id = self.pupil(self.ta, "留下的", cls)
        _, gone = self.pupil(self.ta, "删掉的", cls)
        _, off = self.pupil(self.ta, "停用的", cls)
        for uid, pts in ((me_id, 5), (gone, 500), (off, 400)):
            self.play(uid, pts)
        self.ta.json("POST", "/api/admin/users/delete", {"user_ids": [gone]})
        self.svc.set_disabled(off, True)
        res = self.board(self.login_as(me, "Teach3r!pw"))
        self.assertEqual([e["name"] for e in res["entries"]], ["留下的"])

    def test_a_student_without_a_class_sees_only_themselves(self):
        me, me_id = self.pupil(self.ta, "无班", "")
        _, other = self.pupil(self.ta, "另一个无班", "")
        self.play(me_id, 7)
        self.play(other, 70)
        res = self.board(self.login_as(me, "Teach3r!pw"))
        self.assertEqual([e["name"] for e in res["entries"]], ["无班"])

    def test_a_teacher_sees_own_classes_only_and_can_pick_one(self):
        c1, c2, c3 = self.fresh_class(self.ta, "一"), self.fresh_class(self.ta, "二"), self.fresh_class(self.tb, "三")
        _, a = self.pupil(self.ta, "A同学", c1)
        _, b = self.pupil(self.ta, "B同学", c2)
        _, other = self.pupil(self.tb, "乙老师的学生", c3)
        self.play(a, 10)
        self.play(b, 20)
        self.play(other, 999)
        everything = self.board(self.ta)
        self.assertIn(c1, everything["classes"])
        self.assertIn(c2, everything["classes"])
        self.assertNotIn(c3, everything["classes"], "看不到别的老师的班")
        self.assertNotIn("乙老师的学生", str(everything))
        one = self.board(self.ta, class_name=c1)
        self.assertEqual([e["name"] for e in one["entries"]], ["A同学"])
        self.assertEqual((one["class_name"], one["scope"]), (c1, "staff"))
        self.assertEqual(self.board(self.ta, class_name=c3)["entries"], [], "直接指定别的老师的班也是空的")
        self.assertEqual([e["name"] for e in self.board(self.tb, class_name=c3)["entries"]], ["乙老师的学生"])

    def test_the_super_admin_sees_every_teachers_students(self):
        ca, cb = self.fresh_class(self.ta, "甲"), self.fresh_class(self.tb, "乙")
        _, a = self.pupil(self.ta, "甲生", ca)
        _, b = self.pupil(self.tb, "乙生", cb)
        self.play(a, 3)
        self.play(b, 4)
        self.assertEqual([e["name"] for e in self.board(self.root, class_name=ca)["entries"]], ["甲生"])
        self.assertEqual([e["name"] for e in self.board(self.root, class_name=cb)["entries"]], ["乙生"])
        self.assertTrue({ca, cb} <= set(self.board(self.root)["classes"]))

    def test_login_is_required(self):
        self.assertEqual(Client(self.port).json("GET", "/api/leaderboard")[0], 401)


class TestRanking(LeaderboardCase):
    def test_top_ten_ties_zero_points_and_my_own_rank_outside_the_top(self):
        cls = self.fresh_class(self.ta, "榜")
        ids = [self.pupil(self.ta, "同学%02d" % i, cls) for i in range(13)]
        for i, (_, uid) in enumerate(ids):
            self.play(uid, 100 - i * 5)              # 100, 95, … 40
        zero_no, _ = self.pupil(self.ta, "零分", cls)          # 一局没玩：不上榜
        self.play(ids[4][1], 0)                      # 玩了但得 0 分的也不增加积分
        tie_no, tie_id = self.pupil(self.ta, "并列", cls)
        self.play(tie_id, 95)                        # 和第 2 名同分
        res = self.board(self.login_as(ids[12][0], "Teach3r!pw"))
        self.assertEqual(len(res["entries"]), 10)
        self.assertNotIn("零分", [e["name"] for e in res["entries"]])
        ranks = [(e["name"], e["rank"]) for e in res["entries"][:4]]
        self.assertEqual(ranks, [("同学00", 1), ("同学01", 2), ("并列", 2), ("同学02", 4)], "同分并列，下一名顺延")
        self.assertEqual(res["total"], 14)
        self.assertEqual((res["me"]["name"], res["me"]["rank"], res["me"]["points"]), ("同学12", 14, 40),
                         "不在前十名也能看到自己排第几")
        self.assertFalse([e for e in res["entries"] if e["me"]])

    def test_the_week_board_ignores_older_games(self):
        cls = self.fresh_class(self.ta, "周")
        no, uid = self.pupil(self.ta, "周冠军", cls)
        _, old = self.pupil(self.ta, "上周的人", cls)
        self.play(uid, 10)
        self.play(old, 500, when="2000-01-01 08:00:00")
        client = self.login_as(no, "Teach3r!pw")
        weekly = self.board(client, period="week")
        self.assertEqual([(e["name"], e["points"]) for e in weekly["entries"]], [("周冠军", 10)])
        alltime = self.board(client, period="all")
        self.assertEqual(alltime["entries"][0]["name"], "上周的人")

    def test_week_start_is_a_monday_midnight(self):
        import time
        # 2026-11-18（周三）中午
        stamp = time.mktime((2026, 11, 18, 12, 30, 0, 0, 0, -1))
        self.assertEqual(leaderboard.week_start(stamp), "2026-11-16 00:00:00")
        self.assertEqual(leaderboard.week_start(time.mktime((2026, 11, 16, 0, 0, 1, 0, 0, -1))), "2026-11-16 00:00:00")
        self.assertEqual(leaderboard.week_start(time.mktime((2026, 11, 22, 23, 59, 0, 0, 0, -1))), "2026-11-16 00:00:00")

    def test_disabled_and_deleted_students_do_not_appear(self):
        cls = self.fresh_class(self.ta, "停")
        a_no, a = self.pupil(self.ta, "正常", cls)
        _, b = self.pupil(self.ta, "停用", cls)
        _, c = self.pupil(self.ta, "已删", cls)
        for uid in (a, b, c):
            self.play(uid, 10)
        self.svc.set_disabled(b, True)
        self.ta.json("POST", "/api/admin/users/delete", {"user_ids": [c]})
        res = self.board(self.ta, class_name=cls)
        self.assertEqual([e["name"] for e in res["entries"]], ["正常"])


class TestOverallBoard(LeaderboardCase):
    """超管设置「这几个班」以后，所有登录的人看到的是这几个班合在一起的总榜。"""

    def tearDown(self):
        leaderboard.set_config(self.db, "", [], None)

    def configure(self, classes, title=""):
        status, res = self.root.json("POST", "/api/admin/leaderboard-config", {"title": title, "classes": classes})
        self.assertEqual(status, 200, res)
        return res

    def test_only_the_super_admin_can_read_or_change_the_setting(self):
        for client in (self.ta, self.tb):
            self.assertEqual(client.json("GET", "/api/admin/leaderboard-config")[0], 403)
            self.assertEqual(client.json("POST", "/api/admin/leaderboard-config", {"classes": []})[0], 403)
        cls = self.fresh_class(self.ta, "设")
        no, uid = self.pupil(self.ta, "学生", cls)
        pupil = self.login_as(no, "Teach3r!pw")
        self.assertIn(pupil.json("POST", "/api/admin/leaderboard-config", {"classes": [cls]})[0], (401, 403))
        self.assertEqual(leaderboard.get_config(self.db)["classes"], [], "学生改不了")

    def test_the_setting_lists_real_classes_validates_and_is_audited(self):
        cls = self.fresh_class(self.ta, "真")
        self.pupil(self.ta, "某生", cls)
        listing = self.root.json("GET", "/api/admin/leaderboard-config")[1]
        self.assertIn(cls, [c["class_name"] for c in listing["classes"]])
        self.assertEqual(self.root.json("POST", "/api/admin/leaderboard-config", {"classes": ["没有这个班"]})[0], 400)
        self.assertEqual(self.root.json("POST", "/api/admin/leaderboard-config", {"classes": "一班"})[1]["config"]["classes"], [],
                         "不是列表就当没选")
        saved = self.configure([cls, cls], title="  年级   总榜 ")["config"]
        self.assertEqual(saved, {"title": "年级 总榜", "classes": [cls]}, "去重、整理空格")
        audit = self.root.json("GET", "/api/admin/audit")[1]["audit"]
        self.assertTrue([a for a in audit if a["action"] == "leaderboard.config" and a["detail"]["classes"] == [cls]])

    def test_everyone_sees_the_combined_board_of_the_chosen_classes_only(self):
        c1, c2, c3 = self.fresh_class(self.ta, "总一"), self.fresh_class(self.tb, "总二"), self.fresh_class(self.ta, "不在")
        n1, a = self.pupil(self.ta, "甲班的", c1)
        _, b = self.pupil(self.tb, "乙老师班的", c2)
        _, out = self.pupil(self.ta, "没入选的班", c3)
        self.play(a, 40)
        self.play(b, 90)
        self.play(out, 9999)
        self.configure([c1, c2], title="十班总积分榜")
        student = self.login_as(n1, "Teach3r!pw")
        res = self.board(student)
        self.assertEqual(res["scope"], "overall")
        self.assertEqual(res["title"], "十班总积分榜")
        self.assertEqual(res["class_count"], 2)
        self.assertEqual([(e["name"], e["class_name"], e["points"]) for e in res["entries"]],
                         [("乙老师班的", c2, 90), ("甲班的", c1, 40)], "跨老师、跨班合在一起，旁边标班级；没入选的班不在")
        self.assertTrue(res["my_class_in_board"] and res["is_student"])
        self.assertEqual([(e["name"], e["points"]) for e in self.board(self.ta)["entries"]], [(e["name"], e["points"]) for e in res["entries"]], "老师默认也是总榜")
        self.assertEqual(self.board(self.root)["scope"], "overall")
        self.assertTrue(self.board(self.root)["can_configure"])
        self.assertFalse(res["can_configure"])

    def test_a_student_outside_the_chosen_classes_still_sees_the_board_but_has_no_rank(self):
        c1, other = self.fresh_class(self.ta, "入选"), self.fresh_class(self.ta, "外")
        _, a = self.pupil(self.ta, "入选生", c1)
        n, me = self.pupil(self.ta, "外班生", other)
        self.play(a, 5)
        self.play(me, 500)
        self.configure([c1])
        res = self.board(self.login_as(n, "Teach3r!pw"))
        self.assertEqual([e["name"] for e in res["entries"]], ["入选生"])
        self.assertIsNone(res["me"])
        self.assertFalse(res["my_class_in_board"])

    def test_a_teacher_can_still_pick_one_class_and_only_within_their_own_students(self):
        c1, c2 = self.fresh_class(self.ta, "师一"), self.fresh_class(self.tb, "师二")
        _, a = self.pupil(self.ta, "甲的", c1)
        _, b = self.pupil(self.tb, "乙的", c2)
        self.play(a, 3)
        self.play(b, 4)
        self.configure([c1, c2])
        one = self.board(self.ta, class_name=c1)
        self.assertEqual((one["scope"], [e["name"] for e in one["entries"]]), ("staff", ["甲的"]))
        self.assertEqual(self.board(self.ta, class_name=c2)["entries"], [], "别的老师的班，选了也是空的")
        student = self.login_as(self.pupil(self.ta, "学生丙", c1)[0], "Teach3r!pw")
        self.assertEqual(self.board(student, class_name=c2)["scope"], "overall", "学生传班级参数没用，仍是总榜")

    def test_clearing_the_setting_goes_back_to_one_class_per_board(self):
        cls = self.fresh_class(self.ta, "回")
        n, uid = self.pupil(self.ta, "回退", cls)
        self.play(uid, 1)
        self.configure([cls])
        self.configure([])
        self.assertEqual(self.board(self.login_as(n, "Teach3r!pw"))["scope"], "class")

    def test_a_broken_stored_value_is_treated_as_not_configured(self):
        self.db.execute("INSERT OR REPLACE INTO app_settings(key, value) VALUES ('leaderboard', '{not json')")
        self.assertEqual(leaderboard.get_config(self.db), {"title": "", "classes": []})


WEB = ROOT / "web"


def read(name):
    return (WEB / name).read_text(encoding="utf-8")


class TestLeaderboardPage(unittest.TestCase):
    def test_the_page_is_bilingual_and_has_the_shared_header_with_palettes(self):
        html = read("leaderboard.html")
        self.assertRegex(html, r'<script src="/shared/module-header\.js\?v=[0-9a-f]{8}"></script>', "共享页眉带语言切换和五个配色")
        self.assertIn("data-module-zh=", html)
        self.assertIn('id="portalHeaderControls"', html)
        self.assertIn('id="lbTitle"', html)
        self.assertEqual(html.count('data-period="'), 2, "总榜 / 本周")
        self.assertEqual(html.count('data-game="'), 4, "总分 / 中英配对 / 单词大比拼 / 排排坐")
        self.assertNotRegex(html, r'id="lbGames"[^>]*hidden', "学生也能切换看各个游戏的榜")
        js = (WEB / "js" / "page-leaderboard.js").read_text(encoding="utf-8")
        self.assertIn("'&game=' + state.game", js)
        self.assertIn("localStorage.setItem(GAME_KEY", js, "记住上次看的榜")
        self.assertIn("t('lb_what_' + (d.game || 'all'))", js, "说明跟着所选的榜")

    def test_medals_are_gold_silver_and_bronze_and_the_podium_is_silver_gold_bronze(self):
        js = read("js/page-leaderboard.js")
        for colour in ("#E9B94B", "#C9D2E0", "#D58F5B"):
            self.assertIn(colour, js)
        self.assertIn("slot(2, entries[1]) + slot(1, entries[0]) + slot(3, entries[2])", js, "左银、中金、右铜")
        css = read("css/leaderboard.css")
        for cls in ("lb-tier-1", "lb-tier-2", "lb-tier-3", "lb-pos-1", "lb-pos-2", "lb-pos-3"):
            self.assertIn("." + cls, css)
        self.assertIn("var tier = e ? Math.min(e.rank, 3) : rank;", js, "颜色跟名次走，并列第一两个都是金色")

    def test_only_the_top_ten_exist_server_side_and_names_are_escaped(self):
        self.assertEqual(leaderboard.TOP, 10)
        js = read("js/page-leaderboard.js")
        self.assertIn("esc(e.name)", js)
        self.assertNotIn("innerHTML = e.name", js)

    def test_the_class_picker_is_only_shown_to_staff_and_hidden_really_hides_it(self):
        js, css = read("js/page-leaderboard.js"), read("css/leaderboard.css")
        self.assertIn("if (d.is_student || d.scope === 'class') { box.hidden = true; return; }", js)
        self.assertIn(".lb-class[hidden]", css, "display:flex 会盖掉 hidden 属性，要单独写一条")

    def test_the_super_admin_gets_a_settings_link_and_a_tab_to_choose_the_classes(self):
        js, html = read("js/page-leaderboard.js"), read("leaderboard.html")
        self.assertIn("$('lbSettings').hidden = !d.can_configure;", js)
        self.assertIn('href="/word-puzzle/tenants.html#leaderboard"', html)
        tenants, code = read("tenants.html"), read("js/page-tenants.js")
        self.assertIn('id="tabLeaderboard"', tenants)
        self.assertIn("'/api/admin/leaderboard-config'", code)
        self.assertIn("leaderboard.config", code, "操作记录里要有这个动作的译文")

    def test_the_stage_is_dark_and_serif_and_the_title_has_a_plain_colour_fallback(self):
        css = read("css/leaderboard.css")
        self.assertIn("--serif:", css)
        self.assertRegex(css, r"\.lb-title \{[^}]*color: #f3d98b")       # 不支持渐变文字的浏览器看到的是纯金色，不是透明
        self.assertIn("@supports", css)

    def test_the_link_is_in_the_navigation_for_everyone_who_is_signed_in(self):
        code = read("js/auth-ui.js")
        self.assertIn("function addLeaderboardLink()", code)
        self.assertLess(code.index("addLeaderboardLink();\n    if (isStaffRole"), code.index("addNavLinks(user.role"),
                        "排在账号管理等老师入口前面")

    def test_no_css_that_older_in_app_browsers_cannot_parse(self):
        import re
        css = re.sub(r"/\*.*?\*/", "", read("css/leaderboard.css"), flags=re.S)       # 注释里提到这些词不算
        for risky in ("aspect-ratio", "inset:", "color-mix", ":has(", "@container"):
            self.assertNotIn(risky, css)
        self.assertNotRegex(css, r"display:\s*(-webkit-)?(inline-)?flex;[^}]*(?<![\w-])gap:", "flex 的 gap 在旧一点的微信浏览器里不认")


if __name__ == "__main__":
    unittest.main()
