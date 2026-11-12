"""word-puzzle 后端。

只用 Python 标准库（``http.server`` + ``sqlite3``），服务器上不需要装任何依赖。

启动::

    python3 -m server.app --host 127.0.0.1 --port 8000

部署时 nginx 直接托管 ``web/`` 静态文件，把 ``/api/`` 反代到这里即可。
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
import mimetypes
import os
import re
import sys
import threading
import time
import traceback
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

if __package__ in (None, ""):  # 允许 `python3 server/app.py` 直接跑
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "server"

from server import bank as bank_mod           # noqa: E402
from server import auth as auth_mod            # noqa: E402
from server import hierarchy, ipa, materials, offline, pdf, roster, tts  # noqa: E402
from server.db import Database                 # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
OUTBOX = ROOT / "var" / "offline"

mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/json", ".json")


# ---------------------------------------------------------------- 工具

class HttpError(Exception):
    def __init__(self, status: int, message: str, code: str = ""):
        super().__init__(message)
        self.status = status
        self.message = message
        self.code = code


def parse_multipart(body: bytes, content_type: str) -> dict:
    """极简 multipart/form-data 解析：返回 {name: {filename, data}}。"""
    m = re.search(r'boundary="?([^";]+)"?', content_type or "")
    if not m:
        raise HttpError(400, "multipart 请求缺少 boundary")
    boundary = b"--" + m.group(1).encode("utf-8")
    fields: dict = {}
    for part in body.split(boundary)[1:]:
        if part[:2] == b"\r\n":
            part = part[2:]
        if part[-2:] == b"\r\n":
            part = part[:-2]
        if part in (b"", b"--"):
            continue
        head, sep, data = part.partition(b"\r\n\r\n")
        if not sep:
            continue
        headers = head.decode("utf-8", "replace")
        name = re.search(r'name="([^"]*)"', headers)
        filename = re.search(r'filename="([^"]*)"', headers)
        if not name:
            continue
        fields[name.group(1)] = {
            "filename": filename.group(1) if filename else "",
            "data": data,
        }
    return fields


# PDF/OCR 解析和离线页生成很吃 CPU 和内存：同时最多处理这么多个，其余直接 503。
HEAVY_JOBS = threading.BoundedSemaphore(int(os.environ.get("WP_HEAVY_JOBS", "2")))


def int_param(value, name: str, default: int | None = None,
              low: int | None = None, high: int | None = None) -> int | None:
    """解析整数参数；非法输入返回 400，而不是让异常变成 500。"""
    if value in (None, ""):
        return default
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise HttpError(400, f"参数 {name} 需要是整数") from None
    if low is not None and number < low:
        raise HttpError(400, f"参数 {name} 不能小于 {low}")
    if high is not None:
        number = min(number, high)
    return number


def json_bytes(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False).encode("utf-8")


# ---------------------------------------------------------------- Handler

class Handler(BaseHTTPRequestHandler):
    server_version = "WordPuzzle/2.0"
    protocol_version = "HTTP/1.1"
    db: Database = None            # type: ignore[assignment]
    auth: "auth_mod.AuthService | None" = None     # None = 局域网版，不需要登录
    user: dict | None = None
    _body_read = False

    # ---------------- 基础响应 ----------------

    def log_message(self, fmt, *args):  # noqa: A003
        if os.environ.get("WP_QUIET"):
            return
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, status: int, body: bytes, ctype: str,
              extra: dict | None = None) -> None:
        self._close_if_body_unread()
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "same-origin")
        if self.auth is not None and self.auth.cookie_secure:
            self.send_header("Strict-Transport-Security", "max-age=31536000")
        if self.auth is not None and ctype.startswith(("application/json", "text/csv")):
            self.send_header("Cache-Control", "no-store")     # 带个人信息的响应不要被缓存
        if self.close_connection:
            self.send_header("Connection", "close")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def send_json(self, obj, status: int = 200) -> None:
        self._send(status, json_bytes(obj), "application/json; charset=utf-8")

    def send_error_json(self, status: int, message: str, code: str = "") -> None:
        body = {"ok": False, "error": message}
        if code:
            body["code"] = code
        self.send_json(body, status=status)

    def read_body(self) -> bytes:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            raise HttpError(400, "Content-Length 不合法") from None
        if length <= 0:
            self._body_read = True
            return b""
        if length > 50 * 1024 * 1024:
            raise HttpError(413, "请求体过大（上限 50MB）")
        data = self.rfile.read(length)
        self._body_read = True
        return data

    def read_json(self) -> dict:
        raw = self.read_body()
        if not raw:
            return {}
        try:
            doc = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise HttpError(400, f"请求体不是合法 JSON：{exc}") from exc
        if not isinstance(doc, dict):
            raise HttpError(400, "请求体需要是 JSON 对象")
        return doc

    # ---------------- 路由 ----------------

    def do_GET(self):      # noqa: N802
        self._dispatch("GET")

    def do_HEAD(self):     # noqa: N802
        self._dispatch("GET")

    def do_POST(self):     # noqa: N802
        self._dispatch("POST")

    def do_DELETE(self):   # noqa: N802
        self._dispatch("DELETE")

    @contextlib.contextmanager
    def _heavy(self):
        """限制同时进行的重活（PDF/OCR、离线页生成），超出就让客户端稍后再试。"""
        if not HEAVY_JOBS.acquire(blocking=False):
            raise HttpError(503, "服务器正忙，请稍后再试")
        try:
            yield
        finally:
            HEAVY_JOBS.release()

    def _has_unread_body(self) -> bool:
        if self._body_read:
            return False
        if self.headers.get("Transfer-Encoding"):
            return True
        return (self.headers.get("Content-Length") or "0").strip() not in ("", "0")

    def _same_origin(self) -> bool:
        """跨站伪造防护：浏览器发来的写请求，Origin 必须和 Host 同源。

        curl、脚本等没有 Origin 头的请求照常放行。
        """
        origin = self.headers.get("Origin")
        if not origin:
            return True
        host = (self.headers.get("X-Forwarded-Host")
                or self.headers.get("Host", "")).split(",", 1)[0].strip()
        return urlparse(origin).netloc == host

    def _dispatch(self, method: str) -> None:
        self._body_read = False
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        query = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        try:
            if method != "GET" and not self._same_origin():
                raise HttpError(403, "跨站请求被拒绝")
            self.user = self._load_user()
            if path.startswith("/api/"):
                self.handle_api(method, path, query)
            else:
                self.handle_static(path)
        except HttpError as exc:
            self._close_if_body_unread()
            self.send_error_json(exc.status, exc.message, exc.code)
        except Exception as exc:  # pragma: no cover - 兜底
            traceback.print_exc()
            self._close_if_body_unread()
            self.send_error_json(500, f"服务器内部错误：{exc}")

    def _close_if_body_unread(self) -> None:
        """出错时没读完请求体，就必须关连接：残留字节会被当成下一个请求，
        而 nginx 会复用到后端的长连接，污染别人的请求。"""
        if self._has_unread_body():
            self.close_connection = True

    # ---------------- 登录态 ----------------

    def _session_token(self) -> str | None:
        raw = self.headers.get("Cookie")
        if not raw:
            return None
        try:
            jar = SimpleCookie(raw)
        except Exception:
            return None
        morsel = jar.get(auth_mod.SESSION_COOKIE)
        return morsel.value if morsel else None

    def _load_user(self) -> dict | None:
        if self.auth is None:
            return None
        return self.auth.user_for_token(self._session_token())

    def _is_admin(self) -> bool:
        """局域网版没有账号体系，等同管理员（行为和以前一样）。"""
        return self.auth is None or bool(self.user and self.user["role"] == "admin")

    def _need_admin(self) -> None:
        if not self._is_admin():
            raise HttpError(403, "需要管理员权限", "forbidden")

    def _uid(self) -> int | None:
        return self.user["id"] if (self.auth is not None and self.user) else None

    def _bank_visible(self, bank: dict | None) -> bool:
        if not bank:
            return False
        if self._is_admin() or bank.get("owner_id") is None:
            return True
        return bank["owner_id"] == self._uid()

    def _gate(self, path: str) -> None:
        """家庭版：除了健康检查和登录相关接口，一律要先登录；还没改初始密码就只能去改密码。"""
        if self.auth is None or path == "/api/health" or path.startswith("/api/auth/"):
            return
        if not self.user:
            raise HttpError(401, "请先登录", "login_required")
        if self.user["must_change"]:
            raise HttpError(403, "请先修改初始密码", "password_change_required")

    # ---------------- 静态文件 ----------------

    def handle_static(self, path: str) -> None:
        if path in ("/", ""):
            path = "/index.html"
        rel = path.lstrip("/")
        target = (WEB / rel).resolve()
        try:
            target.relative_to(WEB.resolve())
        except ValueError:
            self.send_error_json(403, "非法路径")
            return
        if not target.exists() or not target.is_file():
            self.send_error_json(404, f"找不到 {path}")
            return
        data = target.read_bytes()
        ctype, _ = mimetypes.guess_type(str(target))
        if ctype and ctype.startswith("text/"):
            ctype += "; charset=utf-8"
        elif ctype == "application/javascript":
            ctype += "; charset=utf-8"
        # 开发期不缓存，避免改了脚本浏览器还在用旧版；
        # 生产环境由 nginx 直接托管 web/，缓存策略交给 nginx。
        self._send(200, data, ctype or "application/octet-stream",
                   {"Cache-Control": "no-cache, must-revalidate"})

    # ---------------- API ----------------

    def handle_api(self, method: str, path: str, query: dict) -> None:
        db = self.db

        # ---- 健康检查 ----
        if path == "/api/health":
            self.send_json({"ok": True, "time": time.strftime("%Y-%m-%d %H:%M:%S")})
            return

        # ---- 登录相关（不需要已登录） ----
        if path.startswith("/api/auth/"):
            self.handle_auth(method, path)
            return

        self._gate(path)

        # ---- 管理员接口 ----
        if path.startswith("/api/admin/"):
            self._need_admin()
            if self.auth is None:
                raise HttpError(404, "局域网版没有账号管理")
            self.handle_admin(method, path, query)
            return

        # ---- 层级元数据 ----
        if path == "/api/meta" and method == "GET":
            self.send_json({"ok": True, **hierarchy.describe(),
                            **tts.describe(), **pdf.describe(),
                            "ipa_available": ipa.available()})
            return

        # ---- 某年级的学期选项 ----
        if path == "/api/terms" and method == "GET":
            l1 = query.get("level1", "")
            l2 = query.get("level2", "")
            self.send_json({"ok": True,
                            "options": hierarchy.level3_options(l1, l2)})
            return

        # ---- 某学期的单元列表 ----
        if path == "/api/units" and method == "GET":
            l1 = query.get("level1", "")
            l2 = query.get("level2", "")
            l3 = query.get("level3", hierarchy.DEFAULT_TERM)
            units = hierarchy.CURRICULUM_OBJ.units_for(l1, l2, l3)
            self.send_json({"ok": True, "units": units,
                            "modes": hierarchy.level4_options(l1, l2, l3)})
            return

        # ---- 资料 ----
        if path.startswith("/api/materials"):
            self._need_admin()
        if path == "/api/materials":
            if method == "GET":
                self.send_json({"ok": True, "materials": db.list_materials()})
                return
            if method == "POST":
                with self._heavy():
                    self._upload_material()
                return

        m = re.fullmatch(r"/api/materials/(\d+)", path)
        if m and method == "DELETE":
            ok = db.delete_material(int(m.group(1)))
            if not ok:
                raise HttpError(404, "资料不存在")
            self.send_json({"ok": True})
            return

        # ---- 题库 ----
        if path == "/api/banks":
            if method == "GET":
                visible = None if self._is_admin() else self._uid()
                self.send_json({"ok": True, "banks": db.list_banks(visible)})
                return
            if method == "POST":
                payload = self.read_json()
                if not self._is_admin() and payload.get("source", "seed") != "seed":
                    raise HttpError(403, "只有管理员可以用上传的资料出题库", "forbidden")
                try:
                    created = bank_mod.create_bank(db, payload, owner_id=self._uid())
                except bank_mod.BankError as exc:
                    raise HttpError(400, str(exc)) from exc
                self.send_json({"ok": True, "bank": created}, status=201)
                return

        m = re.fullmatch(r"/api/banks/(\d+)", path)
        if m and method == "GET":
            bid = int(m.group(1))
            if not self._bank_visible(db.get_bank(bid)):
                raise HttpError(404, "题库不存在")
            try:
                self.send_json({"ok": True, **bank_mod.bank_payload(db, bid)})
            except bank_mod.BankError as exc:
                raise HttpError(404, str(exc)) from exc
            return

        m = re.fullmatch(r"/api/banks/(\d+)", path)
        if m and method == "DELETE":
            bank = db.get_bank(int(m.group(1)))
            if not self._bank_visible(bank):
                raise HttpError(404, "题库不存在")
            if not self._is_admin() and bank.get("owner_id") != self._uid():
                raise HttpError(403, "系统题库不能删除", "forbidden")
            ok = db.delete_bank(int(m.group(1)))
            if not ok:
                raise HttpError(404, "题库不存在")
            self.send_json({"ok": True})
            return

        # ---- 生成离线测试页（很吃资源，家庭版只给管理员） ----
        if path.startswith("/api/offline") or path.endswith("/offline"):
            self._need_admin()
        m = re.fullmatch(r"/api/banks/(\d+)/offline", path)
        if m and method == "POST":
            self.read_json()
            with self._heavy():
                self._make_offline(int(m.group(1)))
            return

        if path == "/api/offline" and method == "GET":
            self._list_offline()
            return

        m = re.fullmatch(r"/api/offline/([^/]+)", path)
        if m and method == "GET":
            self._download_offline(m.group(1), query.get("inline") == "1")
            return

        # ---- 发音音频（神经语音 MP3 / 本地 eSpeak WAV） ----
        if path.startswith("/api/audio/") and method == "GET":
            word = unquote(path[len("/api/audio/"):])
            if not tts.is_valid_word(word):
                raise HttpError(400, "单词不合法")
            data = tts.synth(word)
            if not data:
                raise HttpError(404, "服务器没有可用的语音合成器")
            self._send(200, data, tts.content_type(data),
                       {"Cache-Control": "public, max-age=604800"})
            return

        # ---- 成绩 ----
        if path == "/api/scores":
            if method == "GET":
                limit = int_param(query.get("limit"), "limit", 100, 1, 500)
                bank_id = int_param(query.get("bank_id"), "bank_id")
                # 家庭版：学生只能看自己的成绩，管理员看全部
                only = None if self._is_admin() else self._uid()
                scores = db.list_scores(limit=limit, bank_id=bank_id, user_id=only)
                self.send_json({"ok": True, "scores": scores,
                                "stats": db.score_stats(only)})
                return
            if method == "POST":
                rec = self.read_json()
                uid = self._uid()
                if uid is not None:
                    # 身份以登录态为准，不信客户端自己报的设备号和昵称
                    rec["device"] = "u%d" % uid
                    rec["nickname"] = self.user["name"]
                try:
                    sid = db.insert_score(rec, user_id=uid)
                except Exception as exc:
                    raise HttpError(400, f"成绩保存失败：{exc}") from exc
                self.send_json({"ok": True, "id": sid}, status=201)
                return

        if path == "/api/stats" and method == "GET":
            only = None if self._is_admin() else self._uid()
            self.send_json({"ok": True, **db.score_stats(only)})
            return

        raise HttpError(404, f"未知接口 {path}")

    # ---------------- 登录 / 账号 ----------------

    def handle_auth(self, method: str, path: str) -> None:
        if path == "/api/auth/me" and method == "GET":
            self.send_json({"ok": True, "auth_enabled": self.auth is not None,
                            "user": auth_mod.AuthService.public(self.user)})
            return
        if self.auth is None:
            raise HttpError(404, "局域网版没有登录功能")
        try:
            if path == "/api/auth/login" and method == "POST":
                body = self.read_json()
                user, token = self.auth.login(body.get("student_no", ""), body.get("password", ""))
                self.send_json_with_cookie({"ok": True, "user": self.auth.public(user)},
                                           self.auth.cookie_header(token))
                return
            if path == "/api/auth/logout" and method == "POST":
                self.read_body()
                self.auth.logout(self._session_token())
                self.send_json_with_cookie({"ok": True}, self.auth.clear_cookie_header())
                return
            if path == "/api/auth/change-password" and method == "POST":
                body = self.read_json()
                if not self.user:
                    raise HttpError(401, "请先登录", "login_required")
                token = self.auth.change_password(self.user, body.get("old_password", ""),
                                                  body.get("new_password", ""), self._session_token())
                fresh = self.auth.get_by_id(self.user["id"])
                self.send_json_with_cookie({"ok": True, "user": self.auth.public(fresh)},
                                           self.auth.cookie_header(token))
                return
        except auth_mod.AuthError as exc:
            raise HttpError(exc.status, exc.message, exc.code) from exc
        raise HttpError(404, f"未知接口 {path}")

    def send_json_with_cookie(self, obj, cookie: str, status: int = 200) -> None:
        self._send(status, json_bytes(obj), "application/json; charset=utf-8", {"Set-Cookie": cookie})

    def handle_admin(self, method: str, path: str, query: dict) -> None:
        auth = self.auth
        try:
            if path == "/api/admin/users" and method == "GET":
                users = auth.list_users(class_name=query.get("class_name", ""),
                                        college=query.get("college", ""),
                                        department=query.get("department", ""),
                                        q=query.get("q", "").strip())
                self.send_json({"ok": True, "users": users})
                return

            if path == "/api/admin/import" and method == "POST":
                body = self.read_body()
                ctype = self.headers.get("Content-Type", "")
                if "multipart/form-data" not in ctype:
                    raise HttpError(400, "请用 multipart/form-data 上传名单文件")
                fields = parse_multipart(body, ctype)
                upload = fields.get("file")
                if not upload or not upload["data"]:
                    raise HttpError(400, "没有收到名单文件")
                try:
                    table = roster.parse_roster(upload["filename"], upload["data"])
                except roster.RosterError as exc:
                    raise HttpError(400, str(exc)) from exc
                reset = fields.get("reset_existing", {}).get("data", b"").decode("utf-8", "ignore").strip() in ("1", "true", "on")
                report = auth.import_roster(table["rows"], reset_existing=reset)
                report["ignored_columns"] = table["ignored_columns"]
                self.send_json({"ok": True, **report})
                return

            m = re.fullmatch(r"/api/admin/users/(\d+)/(reset-password|disabled|unlock)", path)
            if m and method == "POST":
                uid, action = int(m.group(1)), m.group(2)
                payload = self.read_json()
                target = auth.get_by_id(uid)
                if not target:
                    raise HttpError(404, "没有这个用户")
                if action == "reset-password":
                    plain = auth.reset_password(uid)
                    self.send_json({"ok": True, "student_no": target["student_no"], "password": plain})
                elif action == "disabled":
                    if uid == self.user["id"]:
                        raise HttpError(400, "不能停用自己的账号")
                    auth.set_disabled(uid, bool(payload.get("disabled", True)))
                    self.send_json({"ok": True})
                else:
                    auth.unlock(uid)
                    self.send_json({"ok": True})
                return

            if path == "/api/admin/export/scores.csv" and method == "GET":
                data = self._scores_csv(query)
                self._send(200, data, "text/csv; charset=utf-8", {
                    "Content-Disposition": 'attachment; filename="lexica-scores.csv"'})
                return
        except auth_mod.AuthError as exc:
            raise HttpError(exc.status, exc.message, exc.code) from exc
        raise HttpError(404, f"未知接口 {path}")

    def _scores_csv(self, query: dict) -> bytes:
        where, args = [], []
        for column, key in (("u.class_name", "class_name"), ("u.college", "college"),
                            ("u.department", "department")):
            if query.get(key):
                where.append(column + "=?")
                args.append(query[key])
        sql = ("SELECT u.student_no, u.name, u.class_name, u.college, u.department, s.bank_title, "
               "s.score, s.matched, s.total_pairs, s.wrong, s.best_combo, s.duration, "
               "s.level_count, s.created_at FROM scores s JOIN users u ON u.id=s.user_id")
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY u.class_name, u.student_no, s.id"
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(["学号", "姓名", "班级", "学院", "院系", "题库", "得分", "配对数", "总对数",
                         "错误次数", "最高连击", "用时(秒)", "关数", "时间"])
        for row in self.db.query(sql, args):
            # 以 = + - @ 开头的单元格在 Excel 里会被当成公式，前面补一个单引号
            writer.writerow([("'" + str(v)) if isinstance(v, str) and v[:1] in "=+-@" else v
                             for v in tuple(row)])
        return ("\ufeff" + out.getvalue()).encode("utf-8")      # BOM：Excel 直接打开不乱码

    # ---------------- 具体处理 ----------------

    def _upload_material(self) -> None:
        ctype = self.headers.get("Content-Type", "")
        body = self.read_body()
        if "multipart/form-data" not in ctype:
            raise HttpError(400, "请用 multipart/form-data 上传文件")
        fields = parse_multipart(body, ctype)
        f = fields.get("file")
        if not f or not f["data"]:
            raise HttpError(400, "没有收到文件")
        filename = f["filename"] or "upload.txt"
        try:
            fmt, words = materials.parse_material(filename, f["data"])
        except materials.ParseError as exc:
            raise HttpError(400, str(exc)) from exc

        note = ""
        if "note" in fields:
            note = fields["note"]["data"].decode("utf-8", "replace").strip()
        name = note or Path(filename).stem
        mid = self.db.insert_material(name, filename, fmt, len(f["data"]),
                                      note, words)
        info = materials.summary(words)
        self.send_json({"ok": True, "material": self.db.get_material(mid),
                        "summary": info}, status=201)

    def _make_offline(self, bid: int) -> None:
        db = self.db
        bank = db.get_bank(bid)
        if not bank:
            raise HttpError(404, "题库不存在")
        try:
            # 和在线玩法用同一套分组（含「词多的单元拆成多关」）
            payload = bank_mod.bank_payload(db, bid)["groups"]
        except bank_mod.BankError as exc:
            raise HttpError(404, str(exc)) from exc
        words = db.bank_words(bid)
        try:
            audio = tts.synth_many([word["en"] for word in words])
            filename, html = offline.build_offline_html(
                bank, payload, audio=audio,
                back_href=self._offline_home_href())
        except tts.SynthesisError as exc:
            raise HttpError(503, str(exc)) from exc
        except ValueError as exc:
            raise HttpError(400, str(exc)) from exc
        OUTBOX.mkdir(parents=True, exist_ok=True)
        (OUTBOX / filename).write_text(html, encoding="utf-8")
        self.send_json({"ok": True, "filename": filename,
                        "url": "/api/offline/" + urllib_quote(filename),
                        "size": len(html.encode("utf-8")),
                        "levels": len(payload),
                        "words": len(words)})

    def _offline_home_href(self) -> str:
        configured = os.environ.get("WP_PUBLIC_HOME_URL", "").strip()
        if configured:
            parsed = urlparse(configured)
            if parsed.scheme in ("http", "https") and parsed.netloc and not parsed.username:
                return configured.rstrip("/") + "/"

        host = (self.headers.get("X-Forwarded-Host")
                or self.headers.get("Host", "")).split(",", 1)[0].strip()
        scheme = (self.headers.get("X-Forwarded-Proto", "http")
                  .split(",", 1)[0].strip().lower())
        if scheme not in ("http", "https") or not re.fullmatch(
                r"[A-Za-z0-9.-]+(?::\d{1,5})?", host):
            return ""
        return f"{scheme}://{host}/"

    def _list_offline(self) -> None:
        OUTBOX.mkdir(parents=True, exist_ok=True)
        files = []
        for p in sorted(OUTBOX.glob("*.html"), key=lambda x: x.stat().st_mtime,
                        reverse=True):
            st = p.stat()
            files.append({
                "name": p.name,
                "url": "/api/offline/" + urllib_quote(p.name),
                "size": st.st_size,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S",
                                           time.localtime(st.st_mtime)),
            })
        self.send_json({"ok": True, "files": files})

    def _download_offline(self, filename: str, inline: bool = False) -> None:
        name = Path(filename).name
        if not name.endswith(".html"):
            raise HttpError(400, "只能下载 .html 文件")
        target = (OUTBOX / name).resolve()
        try:
            target.relative_to(OUTBOX.resolve())
        except ValueError:
            raise HttpError(403, "非法路径")
        if not target.exists():
            raise HttpError(404, "文件不存在，请重新生成")
        data = target.read_bytes()
        quoted = urllib_quote(name)
        disp = "inline" if inline else "attachment"
        stamp = re.search(r"\d{8}-\d{6}", name)
        fallback = "lexica-offline-" + (stamp.group(0) if stamp else "page") + ".html"
        self._send(200, data, "text/html; charset=utf-8", {
            "Content-Disposition":
            f'{disp}; filename="{fallback}"; filename*=UTF-8\'\'{quoted}',
        })


def urllib_quote(text: str) -> str:
    from urllib.parse import quote
    return quote(text, safe="")


# ---------------------------------------------------------------- 入口

def build_server(host: str = "127.0.0.1", port: int = 8000,
                 db_path: str | None = None, auth: "bool | dict | None" = None) -> ThreadingHTTPServer:
    """auth: None = 看环境变量 WP_AUTH；True / dict = 启用登录（dict 是 AuthService 的参数）；False = 关闭。"""
    db = Database(db_path)
    Handler.db = db
    if auth is None:
        enabled = os.environ.get("WP_AUTH", "").strip().lower() in ("1", "true", "yes", "on")
        auth = ({"cookie_secure": os.environ.get("WP_COOKIE_SECURE", "").strip().lower() in ("1", "true", "yes", "on"),
                 "session_days": float(os.environ.get("WP_SESSION_DAYS", "14"))} if enabled else False)
    Handler.auth = auth_mod.AuthService(db, **(auth if isinstance(auth, dict) else {})) if auth else None
    try:
        default_id = bank_mod.seed_default_bank(db)
        bank_mod.seed_curriculum_banks(db)
    except Exception:
        traceback.print_exc()
        default_id = None
    httpd = ThreadingHTTPServer((host, port), Handler)
    httpd.daemon_threads = True
    httpd.default_bank_id = default_id  # type: ignore[attr-defined]
    return httpd


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="word-puzzle 后端")
    ap.add_argument("--host", default=os.environ.get("WP_HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("WP_PORT", "8000")))
    ap.add_argument("--db", default=os.environ.get("WP_DB", ""))
    args = ap.parse_args(argv)

    httpd = build_server(args.host, args.port, args.db or None)
    meta = hierarchy.CURRICULUM_OBJ.meta
    print("=" * 62)
    print("  word-puzzle 服务已启动")
    print(f"  地址：http://{args.host}:{args.port}/")
    print(f"  数据库：{Handler.db.path}")
    print("  登录：" + ("已启用（家庭版 / 班级版）" if Handler.auth else "未启用（局域网版）"))
    print(f"  内置词库：{meta.get('word_total', 0)} 词条 / "
          f"{meta.get('unit_total', 0)} 单元")
    print("  Ctrl-C 退出")
    print("=" * 62)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        httpd.server_close()
        Handler.db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
