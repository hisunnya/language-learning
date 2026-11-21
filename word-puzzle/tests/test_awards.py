"""奖状：连续 5 / 15 / 30 天在积分榜（总分或某一种玩法）榜首。结算规则、并列、断了重来、只发一次、谁能看到。"""
from __future__ import annotations

import datetime
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, ROOT.as_posix())

from server import awards, leaderboard, tenancy           # noqa: E402
from server.auth import AuthService                       # noqa: E402
from server.db import Database                            # noqa: E402
from tests.test_auth import Client, HttpCase              # noqa: E402

DAY0 = datetime.date(2026, 10, 1)


def ts(day: datetime.date, hour: int = 12) -> str:
    return "%s %02d:00:00" % (day.isoformat(), hour)


def after(day: datetime.date) -> float:
    """「现在」= 这一天的第二天中午：这一天已经结束、可以结算。"""
    nxt = day + datetime.timedelta(days=1)
    return time.mktime((nxt.year, nxt.month, nxt.day, 12, 0, 0, 0, 0, -1))


class AwardsCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(str(Path(self.tmp.name) / "a.db"))
        svc = AuthService(self.db)
        self.teacher, _ = svc.create_user("T1", "孙老师", password="Teach3r!pw", role="admin", must_change=False)
        self.a, _ = svc.create_user("S1", "安安", password="Ready2026x", must_change=False, class_name="一班")
        self.b, _ = svc.create_user("S2", "贝贝", password="Ready2026x", must_change=False, class_name="一班")
        self.c, _ = svc.create_user("S3", "丙丙", password="Ready2026x", must_change=False, class_name="二班")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def score(self, user, day, points, game="match"):
        sid = self.db.insert_score({"score": points, "game_type": game}, user_id=user["id"])
        self.db.execute("UPDATE scores SET created_at=? WHERE id=?", (ts(day), sid))

    def mine(self, user):
        return [(a["game"], a["days"], a["start_day"], a["end_day"]) for a in awards.of_user(self.db, user["id"])]


class TestStreaks(AwardsCase):
    def test_five_days_on_top_earns_bronze_once(self):
        self.score(self.a, DAY0, 100)
        self.score(self.b, DAY0, 50)
        made = awards.catch_up(self.db, now=after(DAY0 + datetime.timedelta(days=4)))
        self.assertEqual(made, 2, "总分榜和中英配对榜各一张")
        self.assertEqual(sorted(self.mine(self.a)), [("all", 5, "2026-10-01", "2026-10-05"), ("match", 5, "2026-10-01", "2026-10-05")])
        self.assertEqual(self.mine(self.b), [])
        self.assertEqual(awards.catch_up(self.db, now=after(DAY0 + datetime.timedelta(days=4))), 0, "同一天不会再结算一次")
        a = awards.of_user(self.db, self.a["id"])[0]
        self.assertEqual((a["tier"], a["name"], a["class_name"], a["teacher"]), ("bronze", "安安", "一班", "孙老师"))
        self.assertRegex(a["serial"], r"^LX-2026-\d{6}$")

    def test_fifteen_and_thirty_days_earn_silver_and_gold(self):
        self.score(self.a, DAY0, 10, "spell")
        awards.catch_up(self.db, now=after(DAY0 + datetime.timedelta(days=29)))
        self.assertEqual(sorted(d for g, d, _s, _e in self.mine(self.a) if g == "spell"), [5, 15, 30])
        self.assertEqual({a["tier"] for a in awards.of_user(self.db, self.a["id"])}, {"bronze", "silver", "gold"})

    def test_each_game_has_its_own_board(self):
        self.score(self.a, DAY0, 500, "match")
        self.score(self.b, DAY0, 30, "spell")
        awards.catch_up(self.db, now=after(DAY0 + datetime.timedelta(days=4)))
        self.assertIn(("all", 5, "2026-10-01", "2026-10-05"), self.mine(self.a))
        self.assertEqual(self.mine(self.b), [("spell", 5, "2026-10-01", "2026-10-05")], "总分不是第一，但单词大比拼是")

    def test_ties_count_for_everyone_tied(self):
        self.score(self.a, DAY0, 40)
        self.score(self.b, DAY0, 40)
        awards.catch_up(self.db, now=after(DAY0 + datetime.timedelta(days=4)))
        self.assertEqual(len(self.mine(self.a)), 2)
        self.assertEqual(len(self.mine(self.b)), 2)

    def test_a_broken_streak_starts_again(self):
        self.score(self.a, DAY0, 100)
        self.score(self.b, DAY0 + datetime.timedelta(days=3), 200)        # 第 4 天贝贝超过安安
        self.score(self.a, DAY0 + datetime.timedelta(days=5), 300)        # 第 6 天安安又回到第一
        awards.catch_up(self.db, now=after(DAY0 + datetime.timedelta(days=8)))
        self.assertEqual(self.mine(self.a), [], "安安 10-01~03 第一（3 天），10-06 起又是第一，到 10-09 才 4 天")
        awards.catch_up(self.db, now=after(DAY0 + datetime.timedelta(days=9)))
        self.assertIn(("all", 5, "2026-10-06", "2026-10-10"), self.mine(self.a), "第二段满 5 天")
        self.assertEqual(self.mine(self.b), [], "贝贝只第一了 2 天")

    def test_classes_are_separate_boards_and_zero_points_never_lead(self):
        self.score(self.a, DAY0, 100)
        self.score(self.c, DAY0, 1)
        awards.catch_up(self.db, now=after(DAY0 + datetime.timedelta(days=4)))
        self.assertTrue(self.mine(self.c), "二班只有丙丙一个人有分，他是二班的第一")
        self.assertEqual(self.mine(self.b), [], "0 分不上榜")

    def test_with_an_overall_board_only_that_board_counts(self):
        leaderboard.set_config(self.db, "全校榜", ["一班", "二班"], self.teacher["id"])
        self.score(self.a, DAY0, 100)
        self.score(self.c, DAY0, 1)
        awards.catch_up(self.db, now=after(DAY0 + datetime.timedelta(days=4)))
        self.assertEqual(self.mine(self.c), [])
        a = awards.of_user(self.db, self.a["id"])[0]
        self.assertEqual((a["board"], a["board_label"]), ("overall", "全校榜"))


class TestAwardsOverHttp(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.svc.create_user("T001", "孙老师", password="Teach3r!pw", role="admin", must_change=False)
        cls.s1, _ = cls.svc.create_user("S001", "安安", password="Ready2026x", must_change=False, class_name="一班")
        cls.s2, _ = cls.svc.create_user("S002", "贝贝", password="Ready2026x", must_change=False, class_name="一班")
        db = cls.app.Handler.db
        day = datetime.date.today() - datetime.timedelta(days=7)
        for user, points, game in ((cls.s1, 100, "match"), (cls.s2, 30, "spell")):
            sid = db.insert_score({"score": points, "game_type": game}, user_id=user["id"])
            db.execute("UPDATE scores SET created_at=? WHERE id=?", (ts(day), sid))

    def login(self, no, pw):
        c = Client(self.port)
        self.assertEqual(c.json("POST", "/api/auth/login", {"student_no": no, "password": pw})[0], 200)
        return c

    def test_a_student_sees_their_own_certificates_and_can_mark_them_seen(self):
        c = self.login("S001", "Ready2026x")
        status, body = c.json("GET", "/api/awards")
        self.assertEqual(status, 200, body)
        self.assertEqual({(a["game"], a["days"]) for a in body["awards"]}, {("all", 5), ("match", 5)})
        self.assertEqual(body["unseen"], 2)
        self.assertEqual(c.json("POST", "/api/awards/seen", {})[0], 200)
        self.assertEqual(c.json("GET", "/api/awards")[1]["unseen"], 0)

    def test_others_cannot_read_someone_elses_but_the_teacher_can(self):
        c = self.login("S002", "Ready2026x")
        self.assertEqual(c.json("GET", "/api/awards?user_id=%d" % self.s1["id"])[0], 404)
        teacher = self.login("T001", "Teach3r!pw")
        self.assertEqual(len(teacher.json("GET", "/api/awards?user_id=%d" % self.s1["id"])[1]["awards"]), 2)
        self.assertEqual(Client(self.port).json("GET", "/api/awards")[0], 401)

    def test_leaderboard_per_game_and_badges_next_to_names(self):
        c = self.login("S002", "Ready2026x")
        c.json("GET", "/api/awards")
        spell = c.json("GET", "/api/leaderboard?game=spell")[1]
        self.assertEqual([(e["name"], e["points"]) for e in spell["entries"]], [("贝贝", 30)])
        self.assertEqual(spell["game"], "spell")
        overall = c.json("GET", "/api/leaderboard")[1]
        first = overall["entries"][0]
        self.assertEqual(first["name"], "安安")
        self.assertIn({"game": "all", "days": 5, "tier": "bronze"}, first["badges"])
        self.assertNotIn("id", first, "不把账号编号发给页面")


class TestTeachersSeeAndDownloadTheirStudentsCertificates(TestAwardsOverHttp):
    def test_admin_award_list_is_for_staff_only_and_follows_the_class_filter(self):
        teacher = self.login("T001", "Teach3r!pw")
        status, body = teacher.json("GET", "/api/admin/awards")
        self.assertEqual(status, 200, body)
        self.assertEqual({(a["name"], a["game"]) for a in body["awards"]}, {("安安", "all"), ("安安", "match"), ("贝贝", "spell")})
        self.assertEqual(body["classes"], ["一班"])
        self.assertTrue(all(a["teacher"] == "孙老师" and a["serial"].startswith("LX-") for a in body["awards"]))
        self.assertEqual(teacher.json("GET", "/api/admin/awards?class_name=二班")[1]["awards"], [])
        student = self.login("S001", "Ready2026x")
        self.assertEqual(student.json("GET", "/api/admin/awards")[0], 403)


class TestPages(unittest.TestCase):
    WEB = ROOT / "web"

    def test_profile_page_and_certificate_drawing(self):
        me = (self.WEB / "me.html").read_text(encoding="utf-8")
        for needle in ("awards-ui.js", "page-me.js", 'id="meBadges"', 'id="meCerts"', "site-footer.js", 'id="portalHeaderControls"'):
            self.assertIn(needle, me)
        ui = (self.WEB / "js" / "awards-ui.js").read_text(encoding="utf-8")
        for needle in ("CERTIFICATE OF EXCELLENCE", "荣誉证书", "toBlob(", "'image/' + type", "gold:", "silver:", "bronze:", "aw-modal"):
            self.assertIn(needle, ui)
        self.assertIn("/me.html", (self.WEB / "js" / "auth-ui.js").read_text(encoding="utf-8"), "页眉里点自己的名字进「我的」")

    def test_scores_page_has_my_honours_and_the_teachers_list_with_samples(self):
        html = (self.WEB / "stats.html").read_text(encoding="utf-8")
        for needle in ('id="honorsCard"', 'id="staffAwardsCard"', 'id="awSampleBtn"', 'id="awClass"', "awards-ui.js", "page-honors.js"):
            self.assertIn(needle, html)
        js = (self.WEB / "js" / "page-honors.js").read_text(encoding="utf-8")
        self.assertIn("if (info.public || !info.user) return;", js, "公开版没有账号，不显示荣誉")
        self.assertIn("/api/admin/awards", js)
        self.assertIn("WPAwards.samples(", js)


if __name__ == "__main__":
    unittest.main()
