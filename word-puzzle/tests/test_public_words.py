"""词境公开版 /words/：不用登录、谁都能访问；只有内置题库里的初中、高中；成绩按设备记、只看得到自己的；
不能登录、不能管理、不能下载离线页；读音只给公开题库里的词。nginx 把 /words/api/… 转成后端的 /pub/api/…。"""
from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, ROOT.as_posix())

from tests.test_auth import Client, HttpCase        # noqa: E402

WEB = ROOT / "web"
CONF = (ROOT / "deploy" / "family" / "nginx" / "word-puzzle-family.conf").read_text(encoding="utf-8")
INSTALL = (ROOT / "deploy" / "family" / "install.sh").read_text(encoding="utf-8")


def words(*pairs):
    return [{"unit": "U1", "en": en, "cn": cn} for en, cn in pairs]


def bank(db, title, level1, owner=None, items=(("apple", "苹果"),)):
    return db.insert_bank({"title": title, "level1": level1, "level2": "x", "level3": "y", "level4": "z",
                           "source": "seed", "owner_id": owner}, words(*items))


def score(bank_id, device="d-abc123-xyz98765", points=10):
    return {"bank_id": bank_id, "bank_title": "t", "score": points, "matched": 1, "total_pairs": 1, "wrong": 0,
            "best_combo": 1, "duration": 5, "level_count": 1, "device": device, "detail": []}


class PublicCase(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        admin, _ = cls.svc.create_user("T001", "孙老师", password="Teach3r!pw", role="admin", must_change=False)
        db = cls.app.Handler.db
        db.execute("UPDATE banks SET deleted_at=1")              # 只看这里建的几个，结果才确定
        cls.junior = bank(db, "七年级上", "初中", items=(("apple", "苹果"), ("Banana", "香蕉")))
        cls.senior = bank(db, "高一上", "高中", items=(("galaxy", "星系"),))
        cls.college = bank(db, "大一", "大学", items=(("thesis", "论文"),))
        cls.teachers = bank(db, "老师自己的初中", "初中", owner=admin["id"], items=(("secret", "秘密"),))
        # 内置的初中「单词大比拼」：公开版只放中英配对（新题型的录音、识别都要账号），所以看不到
        cls.spell = db.insert_item_bank({"title": "初中拼写", "level1": "初中", "level2": "七年级", "level3": "上册", "level4": "Unit 1",
                                         "source": "import", "game_type": "spell", "owner_id": None},
                                        [{"before": "", "answer": "apple", "after": "", "cn": "苹果", "text": "apple"}])

    def pub(self, method, path, body=None, c=None, headers=None):
        return (c or Client(self.port)).json(method, "/pub" + path, body, headers=headers)


class TestWhatTheVisitorSees(PublicCase):
    def test_only_built_in_junior_and_senior_banks(self):
        status, body = self.pub("GET", "/api/banks")
        self.assertEqual(status, 200, body)
        self.assertEqual(sorted(b["id"] for b in body["banks"]), sorted([self.junior, self.senior]))
        self.assertEqual(self.pub("GET", "/api/banks/%d" % self.junior)[0], 200)
        for hidden in (self.college, self.teachers, self.spell):
            self.assertEqual(self.pub("GET", "/api/banks/%d" % hidden)[0], 404, hidden)

    def test_me_says_public_and_ignores_a_signed_in_teacher(self):
        c = Client(self.port)
        self.assertEqual(c.json("POST", "/api/auth/login", {"student_no": "T001", "password": "Teach3r!pw"})[0], 200)
        me = self.pub("GET", "/api/auth/me", c=c)[1]
        self.assertEqual((me["public"], me["user"], me["guest_mode"]), (True, None, False))
        self.assertEqual(self.pub("GET", "/api/admin/users", c=c)[0], 404, "从公开入口进来，登录着也没有管理接口")
        self.assertEqual(c.json("GET", "/api/admin/users")[0], 200, "同一个人从 /word-puzzle/ 进来照常是老师")

    def test_everything_outside_the_whitelist_is_404(self):
        for method, path in (("GET", "/api/admin/users"), ("GET", "/api/admin/visits"), ("GET", "/api/leaderboard"),
                             ("POST", "/api/auth/login"), ("POST", "/api/auth/logout"), ("GET", "/api/materials"),
                             ("POST", "/api/banks"), ("POST", "/api/banks/%d/offline" % self.junior), ("GET", "/api/offline"),
                             ("GET", "/api/scores"), ("GET", "/api/stats"), ("POST", "/api/recent"), ("GET", "/api/records")):
            self.assertEqual(self.pub(method, path, {} if method == "POST" else None)[0], 404, (method, path))

    def test_the_login_entrance_is_unchanged(self):
        for path in ("/api/banks", "/api/scores/summary"):
            self.assertEqual(Client(self.port).json("GET", path)[0], 401, path)
        self.assertFalse(Client(self.port).json("GET", "/api/auth/me")[1]["public"])


class TestScoresByDevice(PublicCase):
    def test_a_score_is_kept_against_the_device_and_marked_public(self):
        status, body = self.pub("POST", "/api/scores", score(self.junior, "d-mine-00000001", 42))
        self.assertEqual(status, 201, body)
        row = self.app.Handler.db.one("SELECT user_id, mode, device, nickname FROM scores WHERE id=?", (body["id"],))
        self.assertEqual((row["user_id"], row["mode"], row["device"], row["nickname"]), (None, "public", "d-mine-00000001", ""))

    def test_each_device_sees_only_its_own(self):
        self.pub("POST", "/api/scores", score(self.senior, "d-alice-0000001", 7))
        self.pub("POST", "/api/scores", score(self.senior, "d-bob-000000001", 9))
        mine = self.pub("GET", "/api/scores/summary?device=d-alice-0000001")[1]["rows"]
        self.assertEqual([(r["device"], r["best"]) for r in mine], [("d-alice-0000001", 7)])
        self.assertEqual(self.pub("GET", "/api/scores/summary")[1]["rows"], [], "不给设备号就什么都没有")
        self.assertEqual(self.pub("GET", "/api/scores/summary?device=x' OR 1=1")[1]["rows"], [])
        plays = self.pub("GET", "/api/scores/plays?device=d-bob-000000001&bank_id=%d" % self.senior)[1]["plays"]
        self.assertEqual([p["score"] for p in plays], [9])

    def test_scores_only_on_public_banks_and_with_a_real_device_number(self):
        self.assertEqual(self.pub("POST", "/api/scores", score(self.college))[0], 404)
        self.assertEqual(self.pub("POST", "/api/scores", score(self.teachers))[0], 404)
        self.assertEqual(self.pub("POST", "/api/scores", score(None))[0], 400)
        self.assertEqual(self.pub("POST", "/api/scores", score(self.junior, "x"))[0], 400)

    def test_public_scores_never_reach_a_leaderboard_or_a_teacher(self):
        self.pub("POST", "/api/scores", score(self.junior, "d-board-0000001", 999))
        c = Client(self.port)
        c.json("POST", "/api/auth/login", {"student_no": "T001", "password": "Teach3r!pw"})
        board = c.json("GET", "/api/leaderboard")[1]
        self.assertNotIn(999, [r.get("points") for r in board.get("rows", [])])

    def test_too_many_scores_from_one_address_are_refused(self):
        from server import accesslog
        with mock.patch.object(self.app.Handler, "public_score_throttle", accesslog.Throttle(limit=2, seconds=60)):
            codes = [self.pub("POST", "/api/scores", score(self.junior, "d-spam-00000001"))[0] for _ in range(4)]
        self.assertEqual(codes, [201, 201, 429, 429])


class TestAudio(PublicCase):
    def test_only_words_of_public_banks_are_synthesised(self):
        with mock.patch("server.tts.synth", return_value=b"ID3fake") as synth:
            self.assertEqual(Client(self.port).request("GET", "/pub/api/audio/apple")[0], 200)
            self.assertEqual(Client(self.port).request("GET", "/pub/api/audio/banana")[0], 200, "大小写不同也认")
            for word in ("thesis", "secret", "hello world anything"):
                self.assertEqual(Client(self.port).request("GET", "/pub/api/audio/" + word)[0], 404, word)
        self.assertEqual([c.args[0] for c in synth.call_args_list], ["apple", "banana"])


class TestThePublicPages(unittest.TestCase):
    def test_build_copies_only_the_four_student_pages_with_the_new_prefix(self):
        sys.path.insert(0, (ROOT / "tools").as_posix())
        import build_public_web
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "web-public"
            build_public_web.build(WEB, out)
            self.assertEqual(sorted(p.name for p in out.glob("*.html")), ["index.html", "play.html", "practice.html", "stats.html"])
            for page in out.glob("*.html"):
                text = page.read_text(encoding="utf-8")
                self.assertNotIn("/word-puzzle/", text, page.name)
                self.assertIn('<meta name="wp-base" content="/words">', text, page.name)
                self.assertNotIn("sessionStorage", text, page.name + "：不按记下的角色跳转")
                self.assertIn("classList.add('role-student')", text, page.name)
            for js in (out / "js").glob("*.js"):
                self.assertNotIn("/word-puzzle/", js.read_text(encoding="utf-8"), js.name)
            self.assertTrue((out / "img" / "icon.svg").exists())
            self.assertFalse((out / "admin.html").exists())

    def test_the_pages_know_the_public_mode(self):
        ui = (WEB / "js" / "auth-ui.js").read_text(encoding="utf-8")
        self.assertIn("if (info.public) {", ui)
        self.assertIn("decoratePublic()", ui)
        stats = (WEB / "js" / "page-stats.js").read_text(encoding="utf-8")
        self.assertIn("deviceQuery()", stats)
        practice = (WEB / "practice.html").read_text(encoding="utf-8")
        self.assertRegex(practice, r'class="btn ghost admin-only" id="pracOffline"', "离线下载按钮只给老师")


class TestNginxAndInstaller(unittest.TestCase):
    def test_nginx_serves_words_and_sends_its_api_to_the_public_entrance(self):
        self.assertIn("location ^~ /words/ {", CONF)
        self.assertIn("alias @INSTALL_DIR@/web-public/;", CONF)
        block = re.search(r"location \^~ /words/api/ \{(.*?)\n    \}", CONF, re.S).group(1)
        self.assertIn("proxy_pass http://127.0.0.1:@PORT@/pub/api/;", block)
        self.assertIn("limit_req zone=wp_public_api", block)
        self.assertEqual(CONF.count("@PORT@/pub/"), 1, "只有这一处能到后端的 /pub/")

    def test_installer_builds_the_public_pages_and_checks_what_must_stay_closed(self):
        self.assertIn("tools/build_public_web.py", INSTALL)
        for path in ("/words/admin.html", "/words/login.html", "/words/api/admin/users", "/words/api/leaderboard"):
            self.assertIn(path, INSTALL)
        self.assertIn('("初中","高中")', INSTALL)


if __name__ == "__main__":
    unittest.main()
