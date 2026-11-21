"""奖状：在周榜（总分或某一种玩法）上累计 10 / 15 / 30 天是榜首。周榜每周一重新排、天数累计不要求连续、并列都算、只发一次、谁能看到。"""
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

MON = datetime.date(2026, 10, 5)            # 一个周一：周榜从这天重新开始排
assert MON.weekday() == 0


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

    def daily(self, user, start, count, points, game="match"):
        for i in range(count):
            self.score(user, start + datetime.timedelta(days=i), points, game)

    def settle_to(self, day):
        return awards.catch_up(self.db, now=after(day))

    def mine(self, user):
        return [(a["game"], a["days"], a["start_day"], a["end_day"]) for a in awards.of_user(self.db, user["id"])]


def d(offset: int) -> datetime.date:
    return MON + datetime.timedelta(days=offset)


class TestWeeklyCumulative(AwardsCase):
    def test_ten_days_on_top_earn_bronze_once_and_nine_do_not(self):
        self.daily(self.a, MON, 10, 100)
        self.daily(self.b, MON, 10, 10)
        self.assertEqual(self.settle_to(d(8)), 0, "第 9 天结束：还差一天")
        self.assertEqual(self.mine(self.a), [])
        self.assertEqual(self.settle_to(d(9)), 2, "第 10 天：总分榜和中英配对榜各一张")
        self.assertEqual(sorted(self.mine(self.a)), [("all", 10, "2026-10-05", "2026-10-14"), ("match", 10, "2026-10-05", "2026-10-14")])
        self.assertEqual(self.mine(self.b), [])
        self.assertEqual(self.settle_to(d(9)), 0, "同一天不会再结算一次")
        a = awards.of_user(self.db, self.a["id"])[0]
        self.assertEqual((a["tier"], a["name"], a["class_name"], a["teacher"]), ("bronze", "安安", "一班", "孙老师"))
        self.assertRegex(a["serial"], r"^LX-2026-\d{6}$")

    def test_the_leader_is_decided_per_week_and_days_add_up_across_weeks(self):
        self.score(self.a, d(0), 100)             # 第 1 周：周一周二 a 领先
        self.score(self.b, d(2), 300)             # 周三 b 超过 a，领先到周日
        self.score(self.a, d(7), 100)             # 第 2 周周一重新排：b 的周积分归零，a 领先一整周
        self.score(self.a, d(14), 100)            # 第 3 周周一：a 的第 10 个榜首日
        self.settle_to(d(13))
        self.assertEqual(self.mine(self.a), [], "到第 2 周末 a 一共 2 + 7 = 9 天")
        leaders = lambda day: [r["user_id"] for r in self.db.query("SELECT user_id FROM board_leaders WHERE day=? AND game='all'", (day.isoformat(),))]
        self.assertEqual(leaders(d(7)), [self.a["id"]], "b 的累计积分更高，但周榜每周一重新开始")
        self.assertEqual(leaders(d(3)), [self.b["id"]])
        self.settle_to(d(14))
        self.assertIn(("match", 10, "2026-10-05", "2026-10-19"), self.mine(self.a), "跨周、中间被超过也接着累计")
        self.assertEqual(self.mine(self.b), [], "b 只有 5 天")

    def test_silver_at_fifteen_and_gold_at_thirty(self):
        self.daily(self.a, MON, 30, 10, "spell")
        self.settle_to(d(29))
        self.assertEqual(sorted((days, a["tier"]) for g, days, _s, _e in self.mine(self.a) if g == "spell"
                                for a in [next(x for x in awards.of_user(self.db, self.a["id"]) if x["game"] == g and x["days"] == days)]),
                         [(10, "bronze"), (15, "silver"), (30, "gold")])

    def test_each_game_has_its_own_weekly_board(self):
        self.daily(self.a, MON, 10, 500, "match")
        self.daily(self.b, MON, 10, 30, "spell")
        self.settle_to(d(9))
        self.assertIn(("all", 10, "2026-10-05", "2026-10-14"), self.mine(self.a))
        self.assertEqual(self.mine(self.b), [("spell", 10, "2026-10-05", "2026-10-14")], "总分不是第一，但单词大比拼是")

    def test_ties_count_for_everyone_tied(self):
        self.daily(self.a, MON, 10, 40)
        self.daily(self.b, MON, 10, 40)
        self.settle_to(d(9))
        self.assertEqual(len(self.mine(self.a)), 2)
        self.assertEqual(len(self.mine(self.b)), 2)

    def test_classes_are_separate_boards_and_zero_points_never_lead(self):
        self.daily(self.a, MON, 10, 100)
        self.daily(self.c, MON, 10, 1)
        self.settle_to(d(9))
        self.assertTrue(self.mine(self.c), "二班只有丙丙一个人有分，他是二班的第一")
        self.assertEqual(self.mine(self.b), [], "0 分不上榜")

    def test_with_an_overall_board_only_that_board_counts(self):
        leaderboard.set_config(self.db, "全校榜", ["一班", "二班"], self.teacher["id"])
        self.daily(self.a, MON, 10, 100)
        self.daily(self.c, MON, 10, 1)
        self.settle_to(d(9))
        self.assertEqual(self.mine(self.c), [])
        a = awards.of_user(self.db, self.a["id"])[0]
        self.assertEqual((a["board"], a["board_label"]), ("overall", "全校榜"))

    def test_a_rules_change_recomputes_the_leaders_but_keeps_issued_certificates(self):
        self.daily(self.a, MON, 10, 100)
        self.settle_to(d(9))
        before = len(awards.of_user(self.db, self.a["id"]))
        self.db.execute("UPDATE app_settings SET value='old-rules' WHERE key='awards_rules'")
        self.db.execute("INSERT INTO board_leaders(day, board, game, user_id, points) VALUES ('2025-01-01','x','all',999,1)")
        self.db._awards_ready = False             # 规则只会随新代码改变，新代码意味着服务重启：模拟重启
        awards.ensure(self.db)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM board_leaders")["n"], 0, "旧规则的榜首记录作废")
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM award_days")["n"], 0)
        self.assertEqual(self.settle_to(d(9)), 0, "重新补算不会重复发奖状")
        self.assertEqual(len(awards.of_user(self.db, self.a["id"])), before)
        self.db._awards_ready = False
        awards.ensure(self.db)
        self.assertGreater(self.db.one("SELECT COUNT(*) AS n FROM board_leaders")["n"], 0, "规则没变就不会再清")

    def test_the_board_is_the_one_the_student_sees_on_the_leaderboard(self):
        """和积分榜同一条规则：同班级名 + 共同的老师。另一位老师的「一班」是另一张榜。"""
        svc = AuthService(self.db)
        other, _ = svc.create_user("T2", "李老师", password="Teach3r!pw", role="teacher", must_change=False)
        far, _ = svc.create_user("S9", "远远", password="Ready2026x", must_change=False, class_name="一班", teacher_id=other["id"])
        self.daily(self.a, MON, 10, 100)
        self.daily(far, MON, 10, 5)
        self.settle_to(d(9))
        self.assertTrue(self.mine(far), "远远和安安都叫「一班」，但没有共同的老师，互相看不到，各是各的第一")
        self.assertEqual(awards.of_user(self.db, far["id"])[0]["board"], "c|一班")

    def test_a_deleted_classmate_does_not_block_the_leader(self):
        self.daily(self.a, MON, 10, 500)
        self.daily(self.b, MON, 10, 100)
        self.db.execute("UPDATE users SET deleted_at=1 WHERE id=?", (self.a["id"],))
        self.settle_to(d(9))
        self.assertEqual(len(self.mine(self.b)), 2, "积分榜上看不到被删除的安安，贝贝就是第一")
        self.assertEqual(self.mine(self.a), [])

    def test_one_certificate_per_game_and_tier_even_when_the_board_changes(self):
        self.daily(self.a, MON, 10, 100)
        self.settle_to(d(9))
        self.assertEqual(len(self.mine(self.a)), 2)
        self.db.execute("UPDATE users SET class_name='三班' WHERE id=?", (self.a["id"],))
        self.daily(self.a, d(10), 10, 100)
        self.settle_to(d(19))
        self.assertEqual(sorted((g, n) for g, n, _s, _e in self.mine(self.a)), [("all", 10), ("match", 10)],
                         "换到三班又当了 10 天第一，但铜奖已经有了，不重复发")

    def test_catch_up_does_not_wait_for_a_backfill_already_running(self):
        self.daily(self.a, MON, 10, 100)
        self.assertTrue(awards._lock.acquire(blocking=False))
        try:
            self.assertEqual(self.settle_to(d(9)), 0, "别的请求正在补算：直接返回，不排队")
        finally:
            awards._lock.release()
        self.assertEqual(self.settle_to(d(9)), 2)

    def test_a_failed_day_leaves_nothing_behind(self):
        self.daily(self.a, MON, 1, 100)
        groups = [{"key": "x", "label": "x", "members": {self.a["id"]}, "candidates": {self.a["id"]}},
                  {"key": "broken"}]                # 第二组缺字段：结算到一半出错
        with self.assertRaises(KeyError):
            awards.settle_day(self.db, MON, groups)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM board_leaders")["n"], 0, "整天回滚")
        self.assertIsNone(self.db.one("SELECT 1 FROM award_days WHERE day=?", (MON.isoformat(),)))

    def test_thresholds_and_tiers(self):
        self.assertEqual(awards.THRESHOLDS, (10, 15, 30))
        self.assertEqual([awards.tier_of(n) for n in (10, 14, 15, 29, 30)], ["bronze", "bronze", "silver", "silver", "gold"])


class TestAwardsOverHttp(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.svc.create_user("T001", "孙老师", password="Teach3r!pw", role="admin", must_change=False)
        cls.s1, _ = cls.svc.create_user("S001", "安安", password="Ready2026x", must_change=False, class_name="一班")
        cls.s2, _ = cls.svc.create_user("S002", "贝贝", password="Ready2026x", must_change=False, class_name="一班")
        db = cls.app.Handler.db
        for back in range(11, 0, -1):             # 最近 11 天每天都玩：第 10 天满 10 个榜首日
            day = datetime.date.today() - datetime.timedelta(days=back)
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
        self.assertEqual({(a["game"], a["days"]) for a in body["awards"]}, {("all", 10), ("match", 10)})
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
        self.assertEqual([(e["name"], e["points"]) for e in spell["entries"]], [("贝贝", 330)])
        self.assertEqual(spell["game"], "spell")
        overall = c.json("GET", "/api/leaderboard")[1]
        first = overall["entries"][0]
        self.assertEqual(first["name"], "安安")
        self.assertIn({"game": "all", "days": 10, "tier": "bronze"}, first["badges"])
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

    def test_texts_say_weekly_and_cumulative(self):
        ui = (self.WEB / "js" / "awards-ui.js").read_text(encoding="utf-8")
        self.assertIn("days in total", ui)
        self.assertIn("周榜上，累计 ", ui)
        self.assertNotIn("consecutive", ui)
        for page in ("me.html", "stats.html"):
            html = (self.WEB / page).read_text(encoding="utf-8")
            self.assertIn("累计 10 天、15 天、30 天", html, page)
            self.assertNotIn("连续 5", html, page)


if __name__ == "__main__":
    unittest.main()
