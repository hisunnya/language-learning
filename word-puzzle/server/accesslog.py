"""访问记录：谁、从哪个 IP、用什么设备和浏览器、看了哪些页面、停留多久。永久保留，不自动删除。

* **页面打开**由页面里的 tracker.js 上报（``POST /api/track``：view → 每 15 秒 ping → leave），一次页面打开一行
  ``page_views``；同一个浏览器标签页里先后打开的页面共用一个会话号 ``sid``，老师看到的「一次访问」就是一个 sid。
* **登录**（成功和失败）在登录接口里直接记 ``login_events``，失败的也记下试的是哪个学号。
* **IP**：只有请求来自本机的 nginx（对端是回环地址）时才相信转发头；nginx 把 Funnel 传来的原始
  ``X-Forwarded-For`` 原样放进 ``X-Wp-Edge-Xff``（别人伪造不了这个头：nginx 每次都会覆盖）。
  取转发链里**最后一个**有效地址——那是离我们最近、不是客户端自己写的一环。收到的转发头全部存进 ``forwarded``，
  方便以后核对来源；Funnel 到底传不传真实 IP，以线上实测为准。
* 停留时间 = 页面在**前台**的累计秒数（切到别的标签页 / 锁屏不算），页面每 15 秒报一次，离开时再报一次。
* 时间一律存 UTC 秒数，页面上由浏览器换成本地时间。
"""
from __future__ import annotations

import ipaddress
import json
import os
import re
import threading
import time
from collections import deque

from .db import Database

LOOPBACK = {"127.0.0.1", "::1"}

# ---------------------------------------------------------------- 浏览器 / 系统 / 设备

_BROWSERS = [      # 顺序重要：先认「带别的浏览器名的」，最后才是 Chrome / Safari
    ("Edge", r"(?:Edg|EdgA|EdgiOS|Edge)/([\d.]+)"),
    ("Opera", r"(?:OPR|OPiOS)/([\d.]+)"),
    ("Samsung Internet", r"SamsungBrowser/([\d.]+)"),
    ("UC Browser", r"(?:UCBrowser|UCWEB)/?([\d.]+)"),
    ("QQ Browser", r"(?:MQQBrowser|QQBrowser)/([\d.]+)"),
    ("Quark", r"Quark/([\d.]+)"),
    ("Huawei Browser", r"HuaweiBrowser/([\d.]+)"),
    ("Mi Browser", r"MiuiBrowser/([\d.]+)"),
    ("Baidu Browser", r"(?:baidubrowser|BIDUBrowser)[ /]([\d.]+)"),
    ("Sogou Browser", r"SogouMobileBrowser/([\d.]+)"),
    ("Firefox", r"(?:Firefox|FxiOS)/([\d.]+)"),
    ("Chrome", r"(?:Chrome|CriOS)/([\d.]+)"),
    ("Safari", r"Version/([\d.]+).*Safari/"),
]
_IN_APPS = [("WeChat", r"MicroMessenger/([\d.]+)"), ("WeCom", r"wxwork/([\d.]+)"), ("DingTalk", r"DingTalk/([\d.]+)"),
            ("QQ", r"\bQQ/([\d.]+)"), ("Alipay", r"AlipayClient/([\d.]+)"), ("Weibo", r"Weibo"), ("Feishu", r"Lark/([\d.]+)"),
            ("Douyin", r"(?:aweme|musical_ly)")]
_BOTS = re.compile(r"bot|spider|crawl|slurp|curl/|wget|python-requests|python-urllib|go-http-client|okhttp/|java/|libwww|scanner|headless|monitor",
                   re.I)


def parse_user_agent(ua: str) -> dict:
    """从 User-Agent 里尽量多地认出：浏览器、版本、系统、系统版本、设备类型、型号、内置浏览器（微信等）。
    现代浏览器会把 UA 精简掉一部分（比如 Windows 11 也写成 10.0，安卓型号写成 K），这里只能认出 UA 里有的。"""
    ua = (ua or "").strip()
    out = {"browser": "", "browser_version": "", "os": "", "os_version": "", "device_type": "", "device_model": "", "in_app": ""}
    if not ua:
        return out
    for name, rx in _IN_APPS:
        m = re.search(rx, ua)
        if m:
            out["in_app"] = name + ((" " + m.group(1)) if m.lastindex else "")
            break
    for name, rx in _BROWSERS:
        m = re.search(rx, ua)
        if m:
            out["browser"], out["browser_version"] = name, m.group(1)
            break
    # 系统
    if m := re.search(r"Windows NT ([\d.]+)", ua):
        names = {"10.0": "10 / 11", "6.3": "8.1", "6.2": "8", "6.1": "7", "6.0": "Vista", "5.1": "XP"}
        out["os"], out["os_version"] = "Windows", names.get(m.group(1), m.group(1))
    elif m := re.search(r"(?:iPhone|CPU) OS ([\d_]+)", ua):
        out["os"], out["os_version"] = ("iPadOS" if "iPad" in ua else "iOS"), m.group(1).replace("_", ".")
    elif "iPad" in ua:
        out["os"] = "iPadOS"
    elif "HarmonyOS" in ua:
        m = re.search(r"HarmonyOS[ /]?([\d.]*)", ua)
        out["os"], out["os_version"] = "HarmonyOS", (m.group(1) if m else "")
    elif m := re.search(r"Android[ /]?([\d.]*)", ua):
        out["os"], out["os_version"] = "Android", m.group(1)
    elif m := re.search(r"Mac OS X ([\d_.]+)", ua):
        out["os"], out["os_version"] = "macOS", m.group(1).replace("_", ".")
    elif "CrOS" in ua:
        out["os"] = "ChromeOS"
    elif "Linux" in ua or "X11" in ua:
        out["os"] = "Linux"
    # 设备类型
    if _BOTS.search(ua):
        out["device_type"] = "bot"
    elif "iPad" in ua or "Tablet" in ua or ("Android" in ua and "Mobile" not in ua):
        out["device_type"] = "tablet"
    elif "iPhone" in ua or "Mobile" in ua or "Android" in ua or "HarmonyOS" in ua:
        out["device_type"] = "mobile"
    else:
        out["device_type"] = "desktop"
    # 型号
    if "iPhone" in ua:
        out["device_model"] = "iPhone"
    elif "iPad" in ua:
        out["device_model"] = "iPad"
    elif m := re.search(r"Android [\d.]+; ([^;)]+?)(?: Build/|\)|;)", ua):
        model = m.group(1).strip()
        if model.lower() not in ("k", "wv", "mobile"):
            out["device_model"] = model
    return out


# ---------------------------------------------------------------- 客户端地址

def _valid_ip(text: str) -> str:
    text = (text or "").strip().strip("[]")
    if text.count(":") == 1 and "." in text:          # 带端口的 IPv4：1.2.3.4:5678
        text = text.split(":", 1)[0]
    try:
        return str(ipaddress.ip_address(text))
    except ValueError:
        return ""


def _chain(value: str) -> list[str]:
    return [ip for ip in (_valid_ip(x) for x in (value or "").split(",")) if ip]


FORWARD_HEADERS = (            # 收到什么存什么（只存有的）
    ("X-Wp-Edge-Xff", "edge_xff"), ("X-Wp-Edge-Real-Ip", "edge_real_ip"), ("X-Wp-Edge-Forwarded", "edge_forwarded"),
    ("X-Wp-Edge-Tailscale", "edge_tailscale"), ("X-Forwarded-For", "xff"), ("X-Real-Ip", "real_ip"),
    ("Forwarded", "forwarded"), ("Via", "via"), ("Cf-Connecting-Ip", "cf"), ("True-Client-Ip", "true_client"),
)


def trusted_proxies() -> set[str]:
    """我们自己信任的前置代理地址（环境变量 WP_TRUSTED_PROXIES，逗号分隔）：例如 PVE 宿主机 上的 nginx 把请求转给容器时，
    转发链最后一环是 PVE 宿主机，要跳过它才是真正的访客。"""
    return {ip for ip in (_valid_ip(x) for x in os.environ.get("WP_TRUSTED_PROXIES", "").split(",")) if ip}


def client_address(headers, peer: str) -> tuple[str, dict]:
    """返回 (ip, 收到的转发头)。peer 是 TCP 对端；只有对端是本机（我们自己的 nginx）才相信转发头。"""
    forwarded = {key: headers.get(h).strip()[:300] for h, key in FORWARD_HEADERS if headers.get(h)}
    forwarded["peer"] = peer
    ip = _valid_ip(peer) or peer
    if peer in LOOPBACK:
        for key in ("edge_xff", "xff", "edge_real_ip", "real_ip"):
            chain = _chain(forwarded.get(key, ""))
            if chain:
                trusted = trusted_proxies()
                while len(chain) > 1 and chain[-1] in trusted:
                    chain.pop()              # 跳过我们自己的前置代理
                ip = chain[-1]               # 离我们最近的一环：不是客户端自己写的
                break
    return ip, forwarded


# ---------------------------------------------------------------- 写入

class Throttle:
    """同一个对象一段时间内最多接收多少条上报，防止被人刷爆数据库。"""

    def __init__(self, limit: int, seconds: int, clock=time.time):
        self.limit, self.seconds, self.clock = limit, seconds, clock
        self.hits: dict[str, deque] = {}
        self.lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = self.clock()
        with self.lock:
            q = self.hits.setdefault(key, deque())
            while q and q[0] <= now - self.seconds:
                q.popleft()
            if len(q) >= self.limit:
                return False
            q.append(now)
            if len(self.hits) > 5000:               # 偶尔清掉空的，免得 dict 越来越大
                for k in [k for k, v in self.hits.items() if not v]:
                    del self.hits[k]
            return True


_ID = re.compile(r"[A-Za-z0-9_-]{8,48}")
CLIENT_KEYS = ("screen", "viewport", "dpr", "tz", "tz_offset", "lang", "langs", "platform", "cores", "memory", "touch",
               "connection", "downlink", "rtt", "save_data", "color_scheme", "online", "standalone", "cookies", "dnt",
               "ua_brands", "ua_mobile", "ua_platform", "ua_platform_version", "ua_model", "ua_arch", "ua_bitness",
               "ua_full_version")


def _text(value, limit: int) -> str:
    return re.sub(r"[\x00-\x1f\x7f]+", " ", str(value if value is not None else "")).strip()[:limit]


def clean_client_info(raw) -> dict:
    if not isinstance(raw, dict):
        return {}
    out = {}
    for key in CLIENT_KEYS:
        if key in raw and raw[key] is not None:
            value = raw[key]
            out[key] = value if isinstance(value, (int, float, bool)) and not isinstance(value, complex) else _text(value, 160)
    return out


def request_info(headers, peer: str) -> dict:
    ip, forwarded = client_address(headers, peer)
    ua = _text(headers.get("User-Agent") or "", 400)
    return dict(parse_user_agent(ua), ip=ip, forwarded=json.dumps(forwarded, ensure_ascii=False), user_agent=ua,
                accept_language=_text(headers.get("Accept-Language") or "", 120))


def _who(user: dict | None) -> dict:
    if not user:
        return {"user_id": None, "role": "", "student_no": "", "name": "", "class_name": ""}
    return {"user_id": user["id"], "role": user["role"] if user["role"] in ("admin", "teacher") else "student",
            "student_no": user["student_no"], "name": user["name"], "class_name": user["class_name"] or ""}


def record_login(db: Database, student_no: str, user: dict | None, success: bool, code: str, info: dict,
                 now: float | None = None) -> None:
    who = _who(user)
    db.execute(
        "INSERT INTO login_events(ts, student_no, user_id, name, class_name, success, code, ip, forwarded, user_agent, "
        "browser, browser_version, os, os_version, device_type, device_model, in_app, accept_language) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (int(now or time.time()), _text(student_no, 60), who["user_id"], who["name"], who["class_name"], 1 if success else 0,
         _text(code, 40), info["ip"], info["forwarded"], info["user_agent"], info["browser"], info["browser_version"],
         info["os"], info["os_version"], info["device_type"], info["device_model"], info["in_app"], info["accept_language"]))


def _bank_of(db: Database, search: str) -> tuple[int | None, str]:
    """页面地址里的 ?bank=编号 → (题库编号, 题库当时的标题)。标题在这里查好存下来，题库以后改名 / 删除，记录还是当时的样子。"""
    m = re.search(r"(?:^|[?&])bank=(\d{1,9})(?:&|$)", search or "")
    if not m:
        return None, ""
    bank = db.get_bank(int(m.group(1)))
    return int(m.group(1)), _text(bank["title"], 120) if bank else ""


# 页面文件名 → 给老师看的名字（筛选下拉框、页面浏览列表用；没列出的页面原样显示文件名）
PAGE_NAMES = {
    "index.html": ("首页", "Home"), "play.html": ("游戏", "Game"), "practice.html": ("读音练习", "Pronunciation practice"),
    "leaderboard.html": ("积分榜", "Leaderboard"), "stats.html": ("成绩记录", "Scores"), "bank.html": ("题库工作台", "Word banks"),
    "admin.html": ("账号管理", "Accounts"), "visits.html": ("访问记录", "Visits"), "tenants.html": ("老师与分配", "Teachers"),
    "login.html": ("登录", "Sign in"), "change-password.html": ("修改密码", "Change password"),
}


def page_file(path: str) -> str:
    """/word-puzzle/practice.html → practice.html；/word-puzzle/ → index.html"""
    path = path or ""
    return "index.html" if path.endswith("/") or not path else path.rsplit("/", 1)[-1] or "index.html"


def track(db: Database, user: dict | None, info: dict, payload: dict, now: float | None = None) -> bool:
    """处理一条上报。返回是否有效（无效的悄悄丢掉，不给页面报错）。"""
    now = int(now or time.time())
    event = payload.get("event")
    vid, sid = str(payload.get("vid") or ""), str(payload.get("sid") or "")
    if event not in ("view", "ping", "leave", "env") or not _ID.fullmatch(vid):
        return False
    try:
        active = max(0, int(float(payload.get("active") or 0)))
    except (TypeError, ValueError):
        active = 0
    who = _who(user)
    if event == "view":
        if not _ID.fullmatch(sid):
            return False
        path = _text(payload.get("path"), 200)
        search = _text(payload.get("search"), 300)
        bank_id, bank_title = _bank_of(db, search)
        db.execute(
            "INSERT OR IGNORE INTO page_views(vid, sid, user_id, role, student_no, name, class_name, ip, forwarded, user_agent, "
            "browser, browser_version, os, os_version, device_type, device_model, in_app, accept_language, path, title, "
            "referrer, client_info, started_at, last_seen_at, query, bank_id, bank_title) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (vid, sid, who["user_id"], who["role"], who["student_no"], who["name"], who["class_name"], info["ip"],
             info["forwarded"], info["user_agent"], info["browser"], info["browser_version"], info["os"], info["os_version"],
             info["device_type"], info["device_model"], info["in_app"], info["accept_language"],
             path if path.startswith("/") else "", _text(payload.get("title"), 120), _text(payload.get("referrer"), 300),
             json.dumps(clean_client_info(payload.get("client")), ensure_ascii=False), now, now, search, bank_id, bank_title))
        return True
    row = db.one("SELECT id, user_id, started_at, active_seconds, client_info FROM page_views WHERE vid=?", (vid,))
    if not row:
        return False
    if row["user_id"] is not None and row["user_id"] != who["user_id"]:
        return False                        # 别人的页面号：不让改
    if event == "env":                      # 浏览器后来才给出的详细型号等
        merged = json.loads(row["client_info"] or "{}")
        merged.update(clean_client_info(payload.get("client")))
        model = _text((payload.get("client") or {}).get("ua_model"), 80) if isinstance(payload.get("client"), dict) else ""
        db.execute("UPDATE page_views SET client_info=?, device_model=CASE WHEN ?<>'' THEN ? ELSE device_model END WHERE id=?",
                   (json.dumps(merged, ensure_ascii=False), model, model, row["id"]))
        return True
    cap = max(0, now - row["started_at"]) + 60           # 前台时间不可能比页面打开了多久还长
    db.execute("UPDATE page_views SET last_seen_at=?, active_seconds=MAX(active_seconds, ?), pings=pings+1, ended=? WHERE id=?",
               (now, min(active, cap), 1 if event == "leave" else 0, row["id"]))
    return True


# ---------------------------------------------------------------- 查询（老师页面 / 导出用）

def _filters(role: str, class_name: str, q: str, since, until, table: str, people: tuple[str, tuple] | None = None,
             extra: dict | None = None):
    """people：按人过滤（server/tenancy.py 的 people_where，列名 user_id）——老师只看自己名下学生的记录。
    extra：page（页面文件名）、bank（题库编号，或标题里的字）、device（mobile / tablet / desktop / bot）、
    app（内置浏览器，例如 微信；写 any 表示「任何内置浏览器」，none 表示「普通浏览器」）、os、min_seconds（停留至少几秒）。"""
    extra = extra or {}
    where, args = [], []
    if people is not None:
        where.append(people[0]); args += list(people[1])
    ts = "ts" if table == "login_events" else "started_at"
    if role == "student":
        where.append("role='student'" if table == "page_views"
                     else "user_id IN (SELECT id FROM users WHERE role='student')")
    elif role == "admin":                      # 「老师」：超级管理员和老师
        where.append("role IN ('admin','teacher')" if table == "page_views"
                     else "user_id IN (SELECT id FROM users WHERE role IN ('admin','teacher'))")
    elif role == "anonymous":
        where.append("user_id IS NULL")
    if class_name:
        where.append("class_name=?"); args.append(class_name)
    if q:
        like = "%" + q.strip() + "%"
        if table == "page_views":
            where.append("(student_no LIKE ? OR name LIKE ? OR ip LIKE ? OR user_agent LIKE ? OR device_model LIKE ? OR title LIKE ? OR bank_title LIKE ?)")
            args += [like] * 7
        else:
            where.append("(student_no LIKE ? OR name LIKE ? OR ip LIKE ? OR user_agent LIKE ? OR device_model LIKE ?)")
            args += [like] * 5
    if extra.get("device") in ("mobile", "tablet", "desktop", "bot"):
        where.append("device_type=?"); args.append(extra["device"])
    if extra.get("os"):
        where.append("os=?"); args.append(str(extra["os"])[:40])
    app = str(extra.get("app") or "")
    if app == "any":
        where.append("in_app<>''")
    elif app == "none":
        where.append("in_app=''")
    elif app:                                     # 库里存的是「WeChat 8.0.44」这样带版本号的：按名字开头匹配
        where.append("(in_app=? OR in_app LIKE ?)"); args += [app[:40], app[:40] + " %"]
    if table == "page_views":
        page = str(extra.get("page") or "")[:60]
        if page:
            if page == "index.html":
                where.append("(path LIKE '%/index.html' OR path LIKE '%/')")
            else:
                where.append("path LIKE ?"); args.append("%/" + page)
        bank = str(extra.get("bank") or "").strip()[:60]
        if bank:
            if bank.isdigit():
                where.append("bank_id=?"); args.append(int(bank))
            else:
                where.append("bank_title LIKE ?"); args.append("%" + bank + "%")
        try:
            min_seconds = int(extra.get("min_seconds") or 0)
        except (TypeError, ValueError):
            min_seconds = 0
        if min_seconds > 0:
            where.append("active_seconds>=?"); args.append(min_seconds)
    if since:
        where.append(ts + ">=?"); args.append(int(since))
    if until:
        where.append(ts + "<?"); args.append(int(until))
    return (" WHERE " + " AND ".join(where)) if where else "", args


def sessions(db: Database, *, role: str = "", class_name: str = "", q: str = "", since=None, until=None,
             limit: int = 100, offset: int = 0, people: tuple[str, tuple] | None = None, extra: dict | None = None) -> dict:
    """一次访问 = 同一个浏览器标签页（sid）里同一个账号先后打开的页面。最近的在最前面。"""
    cond, args = _filters(role, class_name, q, since, until, "page_views", people, extra)
    group = "FROM page_views" + cond + " GROUP BY sid, COALESCE(user_id, 0)"
    total = db.one("SELECT COUNT(*) AS n FROM (SELECT 1 " + group + ")", args)["n"]
    keys = db.query("SELECT sid, COALESCE(user_id, 0) AS uid, MAX(started_at) AS last " + group +
                    " ORDER BY last DESC LIMIT ? OFFSET ?", (*args, max(1, min(limit, 500)), max(0, offset)))
    out = []
    for key in keys:
        rows = [dict(r) for r in db.query(
            "SELECT * FROM page_views WHERE sid=? AND COALESCE(user_id, 0)=? ORDER BY started_at, id", (key["sid"], key["uid"]))]
        first = rows[0]
        ips = list(dict.fromkeys(r["ip"] for r in rows if r["ip"]))
        out.append({
            "sid": key["sid"], "user_id": first["user_id"], "role": first["role"], "student_no": first["student_no"],
            "name": first["name"], "class_name": first["class_name"], "ip": ips[0] if ips else "", "ips": ips,
            "browser": first["browser"], "browser_version": first["browser_version"], "os": first["os"], "os_version": first["os_version"],
            "device_type": first["device_type"], "device_model": first["device_model"], "in_app": first["in_app"],
            "pages": len(rows), "first_at": first["started_at"], "last_at": max(r["last_seen_at"] for r in rows),
            "active_seconds": sum(r["active_seconds"] for r in rows),
            "first_path": first["path"],
            "pages_seen": list(dict.fromkeys(page_file(r["path"]) for r in rows)),
            "banks": list(dict.fromkeys(r["bank_title"] or ("#%s" % r["bank_id"]) for r in rows if r["bank_id"])),
        })
    return {"sessions": out, "total": total}


def pageviews(db: Database, *, role: str = "", class_name: str = "", q: str = "", since=None, until=None,
              limit: int = 100, offset: int = 0, people: tuple[str, tuple] | None = None, extra: dict | None = None) -> dict:
    """一次页面浏览一行（不按访问合并）：谁、什么时候、哪一页、用的哪个题库、停了多久。最近的在最前面。"""
    cond, args = _filters(role, class_name, q, since, until, "page_views", people, extra)
    total = db.one("SELECT COUNT(*) AS n FROM page_views" + cond, args)["n"]
    rows = db.query("SELECT id, sid, user_id, role, student_no, name, class_name, ip, browser, browser_version, os, os_version, "
                    "device_type, device_model, in_app, path, title, query, bank_id, bank_title, referrer, started_at, active_seconds "
                    "FROM page_views" + cond + " ORDER BY started_at DESC, id DESC LIMIT ? OFFSET ?",
                    (*args, max(1, min(limit, 500)), max(0, offset)))
    return {"pageviews": [dict(r, page=page_file(r["path"])) for r in rows], "total": total}


def options(db: Database, people: tuple[str, tuple] | None = None) -> dict:
    """筛选下拉框的选项：只列这位老师看得到的记录里真有的页面、题库、系统、内置浏览器。"""
    cond, args = _filters("", "", "", None, None, "page_views", people)
    pages: dict[str, int] = {}
    for r in db.query("SELECT path, COUNT(*) AS n FROM page_views" + cond + " GROUP BY path", args):
        pages[page_file(r["path"])] = pages.get(page_file(r["path"]), 0) + r["n"]
    gate = (cond + " AND " if cond else " WHERE ")
    banks = [dict(r) for r in db.query(
        "SELECT bank_id AS id, MAX(bank_title) AS title, COUNT(*) AS n FROM page_views" + gate + "bank_id IS NOT NULL "
        "GROUP BY bank_id ORDER BY n DESC LIMIT 100", args)]
    oses = [r["os"] for r in db.query("SELECT os, COUNT(*) AS n FROM page_views" + gate + "os<>'' GROUP BY os ORDER BY n DESC", args)]
    apps: list[str] = []
    for r in db.query("SELECT in_app, COUNT(*) AS n FROM page_views" + gate + "in_app<>'' GROUP BY in_app ORDER BY n DESC", args):
        name = r["in_app"].split(" ")[0]                  # 去掉版本号，下拉框里只放名字
        if name not in apps:
            apps.append(name)
    return {"pages": [{"page": k, "zh": PAGE_NAMES.get(k, (k, k))[0], "en": PAGE_NAMES.get(k, (k, k))[1], "n": v}
                      for k, v in sorted(pages.items(), key=lambda kv: -kv[1])],
            "banks": banks, "os": oses, "apps": apps}


def session_pages(db: Database, sid: str, user_id: int | None, people: tuple[str, tuple] | None = None) -> list[dict]:
    cond, args = (" AND " + people[0], tuple(people[1])) if people is not None else ("", ())
    rows = db.query("SELECT * FROM page_views WHERE sid=? AND COALESCE(user_id, 0)=?" + cond + " ORDER BY started_at, id",
                    (sid, user_id or 0, *args))
    out = []
    for r in rows:
        d = dict(r)
        try:
            d["client_info"] = json.loads(d["client_info"] or "{}")
            d["forwarded"] = json.loads(d["forwarded"] or "{}")
        except ValueError:
            d["client_info"], d["forwarded"] = {}, {}
        out.append(d)
    return out


def logins(db: Database, *, role: str = "", class_name: str = "", q: str = "", only_failed: bool = False, since=None,
           until=None, limit: int = 100, offset: int = 0, people: tuple[str, tuple] | None = None,
           extra: dict | None = None) -> dict:
    cond, args = _filters(role, class_name, q, since, until, "login_events", people, extra)
    if only_failed:
        cond += (" AND " if cond else " WHERE ") + "success=0"
    total = db.one("SELECT COUNT(*) AS n FROM login_events" + cond, args)["n"]
    rows = db.query("SELECT * FROM login_events" + cond + " ORDER BY ts DESC, id DESC LIMIT ? OFFSET ?",
                    (*args, max(1, min(limit, 500)), max(0, offset)))
    return {"logins": [dict(r) for r in rows], "total": total}


def all_rows(db: Database, table: str, *, class_name: str = "", q: str = "", since=None, until=None,
             people: tuple[str, tuple] | None = None, role: str = "", extra: dict | None = None) -> tuple[list[str], list[tuple]]:
    """导出用：整张表的所有列（含转发头、客户端信息原文），按时间先后。筛选和页面上选的一致。"""
    cond, args = _filters(role, class_name, q, since, until, table, people, extra)
    order = "ts, id" if table == "login_events" else "started_at, id"
    cur = db.query("SELECT * FROM " + table + cond + " ORDER BY " + order, args)
    cols = list(cur[0].keys()) if cur else [r["name"] for r in db.query("PRAGMA table_info(%s)" % table)]
    return cols, [tuple(r) for r in cur]
