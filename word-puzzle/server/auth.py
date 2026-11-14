"""家庭版 / 班级版的账号体系（WP_AUTH=1 才启用；局域网版完全不受影响）。

设计取舍
--------
* 没有自助注册：账号由管理员导入名单创建（见 roster.py / admin.py），初始密码随机生成，
  学生首次登录**必须先改密码**才能做别的事。
* 用学号登录，少一个要记的东西。
* 只用标准库：密码用 ``hashlib.scrypt``，会话令牌用 ``secrets``，库里只存令牌的哈希。
* 服务可能放在 Tailscale Funnel / 反向代理后面，看不到可靠的客户端 IP，所以不能靠 IP 限流：
  用「单账号连续失败锁定」+「单学号 / 全站的登录速率上限」。
"""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import threading
import time
import unicodedata
from collections import deque
from typing import Callable

from .db import Database, TagError, normalize_tags, now_iso

SESSION_COOKIE = "wp_session"
SCRYPT_N, SCRYPT_R, SCRYPT_P = 2 ** 14, 8, 1
MIN_PASSWORD = 8
MAX_PASSWORD = 128
INITIAL_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"      # 去掉易混淆的 i l o 0 1
COMMON_PASSWORDS = {
    "12345678", "123456789", "1234567890", "password", "password1", "qwertyui", "qwerty123",
    "11111111", "00000000", "88888888", "iloveyou", "abc12345", "abcd1234", "admin123",
}
STUDENT_NO_RE = re.compile(r"[A-Za-z0-9_.-]{1,32}")
MESSAGE_BAD_LOGIN = "学号或密码不对（连续错 5 次会临时锁定 15 分钟）"


class AuthError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


# ---------------------------------------------------------------- 密码

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt,
                            n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=32)
    return "scrypt$%d$%d$%d$%s$%s" % (SCRYPT_N, SCRYPT_R, SCRYPT_P, salt.hex(), digest.hex())


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt_hex, digest_hex = stored.split("$")
        if scheme != "scrypt":
            return False
        expected = bytes.fromhex(digest_hex)
        got = hashlib.scrypt(password.encode("utf-8"), salt=bytes.fromhex(salt_hex),
                             n=int(n), r=int(r), p=int(p), dklen=len(expected))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(got, expected)


# 账号不存在时也算一遍 scrypt，避免用响应时间猜学号是否存在
_DUMMY_HASH = hash_password("dummy-password-for-timing")


def generate_initial_password() -> str:
    while True:
        pw = "".join(secrets.choice(INITIAL_ALPHABET) for _ in range(8))
        if any(c.isdigit() for c in pw) and any(c.isalpha() for c in pw):
            return pw


def password_problem(new: str, student_no: str = "", old: str = "") -> str:
    """返回不合格的原因；合格返回空串。"""
    if len(new) < MIN_PASSWORD:
        return "新密码至少 %d 位" % MIN_PASSWORD
    if len(new) > MAX_PASSWORD:
        return "新密码太长了（最多 %d 位）" % MAX_PASSWORD
    if new == old:
        return "新密码不能和旧密码一样"
    if student_no and student_no.lower() in new.lower():
        return "新密码不能包含学号"
    if len(set(new)) < 4:
        return "新密码太简单，请换一个"
    if new.lower() in COMMON_PASSWORDS:
        return "这个密码太常见了，请换一个"
    classes = sum([any(c.islower() for c in new), any(c.isupper() for c in new),
                   any(c.isdigit() for c in new), any(not c.isalnum() for c in new)])
    if classes < 2:
        return "新密码请至少混合使用两种字符（字母、数字、符号）"
    return ""


# ---------------------------------------------------------------- 限速

class RateLimiter:
    """滑动窗口：window 秒内最多 limit 次。"""

    def __init__(self, limit: int, window: float, clock: Callable[[], float] = time.time):
        self.limit, self.window, self.clock = limit, window, clock
        self._hits: dict[str, deque] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = self.clock()
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and now - hits[0] > self.window:
                hits.popleft()
            if len(hits) >= self.limit:
                return False
            hits.append(now)
            if len(self._hits) > 5000:         # 防止被乱填的学号撑爆内存
                for k in [k for k, v in self._hits.items() if not v or now - v[-1] > self.window]:
                    self._hits.pop(k, None)
            return True


# ---------------------------------------------------------------- 服务

class AuthService:
    def __init__(self, db: Database, *, cookie_secure: bool = False, session_days: float = 14,
                 lock_after: int = 5, lock_minutes: float = 15,
                 clock: Callable[[], float] = time.time):
        self.db = db
        self.cookie_secure = cookie_secure
        self.session_seconds = session_days * 86400
        self.lock_after = lock_after
        self.lock_seconds = lock_minutes * 60
        self.clock = clock
        self.per_student = RateLimiter(10, 300, clock)    # 同一个学号 5 分钟最多试 10 次
        self.overall = RateLimiter(120, 60, clock)        # 全站每分钟最多 120 次登录尝试

    # ---- 用户 ----

    @staticmethod
    def normalize_student_no(value: str) -> str:
        return unicodedata.normalize("NFKC", str(value or "")).strip()

    @staticmethod
    def public(user: dict | None) -> dict | None:
        if not user:
            return None
        return {"id": user["id"], "student_no": user["student_no"], "name": user["name"],
                "class_name": user["class_name"], "college": user["college"],
                "department": user["department"], "role": user["role"],
                "must_change": bool(user["must_change"])}

    def get_by_student_no(self, student_no: str) -> dict | None:
        row = self.db.one("SELECT * FROM users WHERE student_no=?",
                          (self.normalize_student_no(student_no),))
        return dict(row) if row else None

    def get_by_id(self, uid: int) -> dict | None:
        row = self.db.one("SELECT * FROM users WHERE id=?", (uid,))
        return dict(row) if row else None

    def create_user(self, student_no: str, name: str, *, password: str | None = None,
                    class_name: str = "", college: str = "", department: str = "",
                    role: str = "student", must_change: bool = True) -> tuple[dict, str]:
        """返回 (用户, 明文初始密码)。明文只在这里出现一次，库里只有哈希。"""
        student_no = self.normalize_student_no(student_no)
        if not STUDENT_NO_RE.fullmatch(student_no):
            raise AuthError(400, "bad_student_no", "学号只能是字母、数字和 _ . -，最长 32 位")
        name = str(name or "").strip()
        if not name or len(name) > 40:
            raise AuthError(400, "bad_name", "姓名不能为空，最长 40 个字")
        for label, value in (("班级", class_name), ("学院", college), ("院系", department)):
            if len(str(value)) > 60:
                raise AuthError(400, "bad_field", "%s太长了（最多 60 个字）" % label)
        if self.get_by_student_no(student_no):
            raise AuthError(409, "exists", "学号 %s 已经存在" % student_no)
        plain = password or generate_initial_password()
        with self.db._tx() as conn:
            cur = conn.execute(
                "INSERT INTO users(student_no, name, class_name, college, department, role, "
                "pw_hash, must_change, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (student_no, name, str(class_name).strip(), str(college).strip(),
                 str(department).strip(), role, hash_password(plain), 1 if must_change else 0,
                 now_iso()))
        return self.get_by_id(cur.lastrowid), plain

    def list_users(self, *, class_name: str = "", college: str = "", department: str = "",
                   q: str = "") -> list[dict]:
        where, args = [], []
        for column, value in (("u.class_name", class_name), ("u.college", college),
                              ("u.department", department)):
            if value:
                where.append(column + "=?")
                args.append(value)
        if q:
            where.append("(u.student_no LIKE ? OR u.name LIKE ?)")
            args += ["%" + q + "%", "%" + q + "%"]
        sql = ("SELECT u.id, u.student_no, u.name, u.class_name, u.college, u.department, u.role, "
               "u.must_change, u.disabled, u.locked_until, u.last_login_at, "
               "COUNT(s.id) AS games, COALESCE(MAX(s.score),0) AS best, "
               "COALESCE(SUM(s.score),0) AS total "
               "FROM users u LEFT JOIN scores s ON s.user_id=u.id")
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " GROUP BY u.id ORDER BY u.class_name, u.student_no"
        now = self.clock()
        out = []
        tags = self.db.user_tags_map()
        for row in self.db.query(sql, args):
            d = dict(row)
            d["locked"] = d.pop("locked_until") > now
            d["tags"] = tags.get(d["id"], [])
            out.append(d)
        return out

    # ---- 会话 ----

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _new_session(self, uid: int) -> str:
        token = secrets.token_urlsafe(32)
        now = self.clock()
        with self.db._tx() as conn:
            conn.execute("DELETE FROM sessions WHERE expires_at < ?", (now,))
            conn.execute("INSERT INTO sessions(token_hash, user_id, created_at, expires_at, last_seen) "
                         "VALUES (?,?,?,?,?)",
                         (self._token_hash(token), uid, now, now + self.session_seconds, now))
        return token

    def user_for_token(self, token: str | None) -> dict | None:
        if not token:
            return None
        row = self.db.one("SELECT s.expires_at, u.* FROM sessions s JOIN users u ON u.id=s.user_id "
                          "WHERE s.token_hash=?", (self._token_hash(token),))
        if not row:
            return None
        user = dict(row)
        if user["expires_at"] < self.clock() or user["disabled"]:
            return None
        return user

    def logout(self, token: str | None) -> None:
        if token:
            self.db.execute("DELETE FROM sessions WHERE token_hash=?", (self._token_hash(token),))

    def drop_sessions(self, uid: int, keep_token: str | None = None) -> None:
        keep = self._token_hash(keep_token) if keep_token else ""
        self.db.execute("DELETE FROM sessions WHERE user_id=? AND token_hash<>?", (uid, keep))

    # ---- 登录 / 改密码 ----

    def login(self, student_no: str, password: str) -> tuple[dict, str]:
        sn = self.normalize_student_no(student_no)
        password = str(password or "")
        if not sn or not password or len(password) > MAX_PASSWORD or len(sn) > 64:
            raise AuthError(400, "missing", "请输入学号和密码")
        if not (self.overall.allow("*") and self.per_student.allow(sn.lower())):
            raise AuthError(429, "rate_limited", "尝试太频繁了，请稍后再试")
        user = self.get_by_student_no(sn)
        now = self.clock()
        if not user:
            verify_password(password, _DUMMY_HASH)
            raise AuthError(401, "invalid_credentials", MESSAGE_BAD_LOGIN)
        if user["disabled"] or user["locked_until"] > now:
            verify_password(password, _DUMMY_HASH)
            raise AuthError(401, "invalid_credentials", MESSAGE_BAD_LOGIN)
        if not verify_password(password, user["pw_hash"]):
            failed = user["failed_count"] + 1
            locked = 0.0
            if failed >= self.lock_after:
                failed, locked = 0, now + self.lock_seconds
            self.db.execute("UPDATE users SET failed_count=?, locked_until=? WHERE id=?",
                            (failed, locked, user["id"]))
            raise AuthError(401, "invalid_credentials", MESSAGE_BAD_LOGIN)
        self.db.execute("UPDATE users SET failed_count=0, locked_until=0, last_login_at=? WHERE id=?",
                        (now_iso(), user["id"]))
        return user, self._new_session(user["id"])

    def change_password(self, user: dict, old: str, new: str, keep_token: str | None) -> str:
        """改密码并返回新的会话令牌：其他设备上的登录全部作废。"""
        if not verify_password(str(old or ""), user["pw_hash"]):
            raise AuthError(400, "wrong_old_password", "旧密码不对")
        problem = password_problem(str(new or ""), user["student_no"], str(old or ""))
        if problem:
            raise AuthError(400, "weak_password", problem)
        self.db.execute("UPDATE users SET pw_hash=?, must_change=0 WHERE id=?",
                        (hash_password(new), user["id"]))
        self.drop_sessions(user["id"])
        return self._new_session(user["id"])

    # ---- 管理员操作 ----

    def reset_password(self, uid: int) -> str:
        user = self.get_by_id(uid)
        if not user:
            raise AuthError(404, "no_user", "没有这个用户")
        plain = generate_initial_password()
        self.db.execute("UPDATE users SET pw_hash=?, must_change=1, failed_count=0, locked_until=0 "
                        "WHERE id=?", (hash_password(plain), uid))
        self.drop_sessions(uid)
        return plain

    def set_disabled(self, uid: int, disabled: bool) -> None:
        if not self.get_by_id(uid):
            raise AuthError(404, "no_user", "没有这个用户")
        self.db.execute("UPDATE users SET disabled=? WHERE id=?", (1 if disabled else 0, uid))
        if disabled:
            self.drop_sessions(uid)

    def unlock(self, uid: int) -> None:
        self.db.execute("UPDATE users SET failed_count=0, locked_until=0 WHERE id=?", (uid,))

    def import_roster(self, rows: list[dict], *, reset_existing: bool = False) -> dict:
        """按名单建号。已存在的学号只更新姓名 / 班级 / 学院 / 院系（不动密码，除非 reset_existing）。
        返回 {created, updated, skipped, errors, credentials}。credentials 里有明文初始密码，
        只在这一次返回，之后谁也查不到。"""
        report = {"created": 0, "updated": 0, "skipped": 0, "errors": [], "credentials": []}
        seen: set[str] = set()
        for rec in rows:
            line = rec.get("_row", "?")
            sn = self.normalize_student_no(rec.get("student_no", ""))
            if not sn:
                report["skipped"] += 1
                report["errors"].append({"row": line, "student_no": "", "reason": "学号为空"})
                continue
            if sn.lower() in seen:
                report["skipped"] += 1
                report["errors"].append({"row": line, "student_no": sn, "reason": "学号在名单里重复，已跳过"})
                continue
            seen.add(sn.lower())
            fields = {k: rec.get(k, "") for k in ("name", "class_name", "college", "department")}
            existing = self.get_by_student_no(sn)
            try:
                # 「标签」列：有内容就整组替换；列不存在或这一格是空的，保持原样
                try:
                    new_tags = normalize_tags(rec["tags"]) if str(rec.get("tags") or "").strip() else None
                except TagError as exc:
                    raise AuthError(400, "bad_tags", exc.args[0]) from exc
                if existing is None:
                    custom = rec.get("password") or None
                    if custom and len(custom) < 6:
                        raise AuthError(400, "bad_password", "初始密码至少 6 位（或留空自动生成）")
                    user, plain = self.create_user(sn, fields["name"], password=custom, **{
                        k: fields[k] for k in ("class_name", "college", "department")})
                    report["created"] += 1
                    if new_tags is not None:
                        self.db.set_user_tags(user["id"], new_tags)
                    report["credentials"].append({"student_no": user["student_no"], "name": user["name"],
                                                  "class_name": user["class_name"], "password": plain})
                else:
                    if existing["role"] == "admin":
                        raise AuthError(400, "is_admin", "这是管理员账号，名单导入不会修改它")
                    if not str(fields["name"]).strip():
                        raise AuthError(400, "bad_name", "姓名不能为空")
                    self.db.execute("UPDATE users SET name=?, class_name=?, college=?, department=? WHERE id=?",
                                    (fields["name"].strip(), fields["class_name"].strip(),
                                     fields["college"].strip(), fields["department"].strip(), existing["id"]))
                    report["updated"] += 1
                    if new_tags is not None:
                        self.db.set_user_tags(existing["id"], new_tags)
                    if reset_existing:
                        plain = self.reset_password(existing["id"])
                        report["credentials"].append({"student_no": sn, "name": fields["name"],
                                                      "class_name": fields["class_name"], "password": plain})
            except AuthError as exc:
                report["skipped"] += 1
                report["errors"].append({"row": line, "student_no": sn, "reason": exc.message})
        return report

    # ---- Cookie ----

    def cookie_header(self, token: str) -> str:
        parts = ["%s=%s" % (SESSION_COOKIE, token), "Path=/", "HttpOnly", "SameSite=Lax",
                 "Max-Age=%d" % int(self.session_seconds)]
        if self.cookie_secure:
            parts.append("Secure")
        return "; ".join(parts)

    def clear_cookie_header(self) -> str:
        parts = ["%s=" % SESSION_COOKIE, "Path=/", "HttpOnly", "SameSite=Lax", "Max-Age=0"]
        if self.cookie_secure:
            parts.append("Secure")
        return "; ".join(parts)
