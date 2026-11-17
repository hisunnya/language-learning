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
from server import accesslog, hierarchy, leaderboard, modules, policy, tenancy, ipa, materials, offline, pdf, roster, scorebook, tts  # noqa: E402
from server.db import Database, TagError, normalize_category, normalize_tags  # noqa: E402

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
    auth: "auth_mod.AuthService | None" = None     # None = 家庭版，不需要登录
    user: dict | None = None
    _body_read = False
    track_throttle = accesslog.Throttle(limit=900, seconds=60)     # 每个来源地址每分钟最多收这么多条上报
    login_throttle = accesslog.Throttle(limit=300, seconds=60)

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
        if self.auth is not None and self._secure_cookie():
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
        """超级管理员。家庭版没有账号体系，等同超级管理员（行为和以前一样）。"""
        return self.auth is None or bool(self.user and self.user["role"] == "admin")

    def _is_staff(self) -> bool:
        """能用管理功能的人：超级管理员和老师（老师只管得了自己名下的，范围见 server/tenancy.py）。"""
        return self.auth is None or bool(self.user and self.user["role"] in policy.STAFF_ROLES)

    def _guest_entrance(self) -> bool:
        """内网入口（家庭版）：不登录也能用所有页面，管理功能才要登录。
        只有「开了 WP_LAN_GUEST」且「请求来自本机 nginx」且「nginx 的内网入口打了 X-Wp-Entry: lan」才算；
        公网入口的 nginx 每次都把这个头清空，外面的人自己带了也没用。"""
        return (self.auth is not None and os.environ.get("WP_LAN_GUEST") == "1"
                and self._peer() in accesslog.LOOPBACK and self.headers.get("X-Wp-Entry") == "lan")

    def _scope(self) -> "tenancy.Scope":
        """这个请求能看到、能管理哪些数据（超管 / 老师 / 学生 / 家庭版访客）。"""
        return tenancy.scope_for(self.auth is not None, self.user, self._guest_entrance())

    def _need(self, action: str, resource: dict | None = None) -> None:
        """按 server/policy.py 判断当前用户能不能做这件事；局域网版（没有账号体系）等同允许。"""
        if self.auth is None or policy.allow(self.user, action, resource):
            return
        if not self.user:
            raise HttpError(401, "请先用教师账号登录", "login_required")
        raise HttpError(403, "需要管理员权限", "forbidden")

    def _need_staff(self) -> None:
        """老师或超级管理员。"""
        self._need("admin")

    def _need_admin(self) -> None:
        """只有超级管理员（加老师、共享 / 分配、恢复删除、审计记录）。"""
        self._need("tenants.manage")

    def _uid(self) -> int | None:
        return self.user["id"] if (self.auth is not None and self.user) else None

    def _bank_visible(self, bank: dict | None) -> bool:
        """超管看得到全部；老师看得到自己的、共享给他的、内置的；学生看得到某位老师给他开放的；家庭版访客看得到内置的和超管的。"""
        return tenancy.bank_visible(self.db, self._scope(), bank)

    @staticmethod
    def _tags_meta(payload: dict) -> tuple[str | None, list[str] | None]:
        """从请求里取分类和标签；没传的那一项返回 None（保持不变）。不合法返回 400。"""
        try:
            category = normalize_category(payload["category"]) if "category" in payload else None
            tags = normalize_tags(payload["tags"]) if "tags" in payload else None
        except TagError as exc:
            raise HttpError(400, exc.args[0], "bad_tags") from exc
        return category, tags

    def _gate(self, path: str) -> None:
        """学生版：除了健康检查和登录相关接口，一律要先登录；还没改初始密码就只能去改密码。"""
        if self.auth is None or self._guest_entrance() or path == "/api/health" or path.startswith("/api/auth/"):
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

        # ---- 访问记录上报（没登录也收：登录页的访问也要记；家庭版不记） ----
        if path == "/api/track" and method == "POST":
            self.handle_track()
            return

        self._gate(path)

        # ---- 管理员接口（老师和超级管理员；超管专属的在里面另外检查） ----
        if path.startswith("/api/admin/"):
            self._need_staff()
            if self.auth is None:
                raise HttpError(404, "家庭版没有账号管理")
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
            self._need_staff()
        if path == "/api/materials":
            if method == "GET":
                where, args = tenancy.material_where(self._scope())
                self.send_json({"ok": True, "materials": db.list_materials(where, args)})
                return
            if method == "POST":
                with self._heavy():
                    self._upload_material()
                return

        m = re.fullmatch(r"/api/materials/(\d+)", path)
        if m and method == "DELETE":
            mid = int(m.group(1))
            if not tenancy.material_visible(db, self._scope(), mid):
                raise HttpError(404, "资料不存在")
            tenancy.soft_delete(db, "materials", mid, self._uid())       # 软删除：超管能恢复
            tenancy.audit(db, self._uid(), "material.delete", "material", mid)
            self.send_json({"ok": True})
            return

        # ---- 模块登记表 / 各学科通用的成绩记录 ----
        if path == "/api/modules" and method == "GET":
            self.send_json({"ok": True, "modules": modules.listing()})
            return
        if path == "/api/records":
            self.handle_records(method, query)
            return
        if path == "/api/recent":
            self.handle_recent(method, query)
            return

        # ---- 题库 ----
        if path == "/api/banks":
            if method == "GET":
                self.send_json({"ok": True, "banks": tenancy.list_banks(db, self._scope())})
                return
            if method == "POST":
                # 建题库属于题库管理：老师和超管（家庭版没有账号，等同超管）。题库归建的人所有。
                self._need_staff()
                payload = self.read_json()
                if payload.get("source") == "material":
                    try:
                        mid = int(payload.get("material_id") or 0)
                    except (TypeError, ValueError):
                        mid = 0
                    if mid and not tenancy.material_visible(db, self._scope(), mid):
                        raise HttpError(400, "资料不存在，可能已被删除")
                category, tags = self._tags_meta(payload)
                split = bool(payload.get("split_units"))
                if split and category is None:
                    category = normalize_category(payload.get("title"))     # 分类默认就是书名
                try:
                    if split:
                        made = bank_mod.create_bank_per_unit(db, payload, owner_id=self._uid())
                    else:
                        made = [bank_mod.create_bank(db, payload, owner_id=self._uid())]
                except bank_mod.BankError as exc:
                    raise HttpError(400, str(exc)) from exc
                if category is not None or tags is not None:
                    for item in made:
                        db.set_bank_meta(item["id"], category, tags, teacher_id=self._scope().tag_teacher)
                banks = [db.list_banks_by_id(item["id"], tag_teacher=self._scope().tag_teacher) for item in made]
                self.send_json({"ok": True, "bank": banks[0], "banks": banks}, status=201)
                return


        if path == "/api/banks/tags" and method == "POST":
            # 批量开放 / 收回：给一批题库加或去掉自己的标签（自己名下的学生有相同标签就能看到）
            self._need_staff()
            payload = self.read_json()
            ids = payload.get("bank_ids")
            if not isinstance(ids, list) or not ids or not all(isinstance(i, int) for i in ids):
                raise HttpError(400, "请选择要修改的题库")
            scope = self._scope()
            ids = [i for i in ids if tenancy.can_tag_bank(db, scope, db.get_bank(i))]
            try:
                add, remove = normalize_tags(payload.get("add")), normalize_tags(payload.get("remove"))
            except TagError as exc:
                raise HttpError(400, exc.args[0], "bad_tags") from exc
            if not add and not remove:
                raise HttpError(400, "请填写要加或要去掉的标签")
            self.send_json({"ok": True, "changed": db.change_bank_tags(ids, add, remove, teacher_id=scope.tag_teacher)})
            return

        m = re.fullmatch(r"/api/banks/(\d+)", path)
        if m and method == "GET":
            bid = int(m.group(1))
            if not self._bank_visible(db.get_bank(bid)):
                raise HttpError(404, "题库不存在")
            scope = self._scope()
            try:
                self.send_json({"ok": True, **bank_mod.bank_payload(db, bid, scope.tag_teacher if scope.staff else -1)})
            except bank_mod.BankError as exc:
                raise HttpError(404, str(exc)) from exc
            return

        m = re.fullmatch(r"/api/banks/(\d+)", path)
        if m and method == "DELETE":
            self._need_staff()
            bank = db.get_bank(int(m.group(1)))
            scope = self._scope()
            if not bank or bank.get("deleted_at") or not tenancy.bank_visible(db, scope, bank):
                raise HttpError(404, "题库不存在")
            try:
                done = tenancy.delete_bank_for(db, scope, bank)       # 自己的：软删除；共享过来的：从自己名下移走
            except PermissionError as exc:
                raise HttpError(403, str(exc), "forbidden") from exc
            tenancy.audit(db, self._uid(), "bank." + ("delete" if done == "deleted" else "unshare_self"), "bank", bank["id"],
                          title=bank["title"])
            self.send_json({"ok": True, "done": done})
            return

        # ---- 改题库的分类和标签（只有老师） ----
        m = re.fullmatch(r"/api/banks/(\d+)/meta", path)
        if m and method == "POST":
            self._need_staff()
            category, tags = self._tags_meta(self.read_json())
            bank, scope = db.get_bank(int(m.group(1))), self._scope()
            if not tenancy.can_tag_bank(db, scope, bank):
                raise HttpError(404, "题库不存在")
            if category is not None and not tenancy.can_edit_bank(db, scope, bank):
                raise HttpError(403, "只有题库的主人能改分类（内置题库和别人共享的题库不能改）", "forbidden")
            db.set_bank_meta(bank["id"], category, tags, teacher_id=scope.tag_teacher)
            self.send_json({"ok": True, "bank": db.list_banks_by_id(bank["id"], tag_teacher=scope.tag_teacher)})
            return

        # ---- 生成离线测试页（很吃资源，学生版只给管理员） ----
        if path.startswith("/api/offline") or path.endswith("/offline"):
            self._need_staff()
        m = re.fullmatch(r"/api/banks/(\d+)/offline", path)
        if m and method == "POST":
            kind = self.read_json().get("kind") or "game"          # game = 配对游戏，practice = 读音练习
            if kind not in ("game", "practice"):
                raise HttpError(400, "kind 只能是 game 或 practice", "bad_kind")
            with self._heavy():
                self._make_offline(int(m.group(1)), kind)
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

        # ---- 积分榜：学生只看自己班，老师看自己名下各班，超管看全部 ----
        if path == "/api/leaderboard" and method == "GET":
            scope = self._scope()
            if scope.kind in (tenancy.GUEST, tenancy.NOBODY):
                raise HttpError(403, "积分榜要登录后才能看", "login_required")
            self.send_json({"ok": True, **leaderboard.board(db, scope, self.user, query.get("class_name", "").strip()[:60],
                                                           query.get("period", "all"))})
            return

        # ---- 成绩 ----
        if path == "/api/scores":
            if method == "GET":
                limit = int_param(query.get("limit"), "limit", 100, 1, 500)
                bank_id = int_param(query.get("bank_id"), "bank_id")
                # 超管看全部；老师看自己名下学生的；学生只看自己的；家庭版访客只看没登录时按设备记的
                people = tenancy.people_where(self._scope(), "user_id")
                scores = db.list_scores(limit=limit, bank_id=bank_id, people=people)
                self.send_json({"ok": True, "scores": scores,
                                "stats": db.score_stats(people=people)})
                return
            if method == "POST":
                rec = self.read_json()
                uid = self._uid()
                if uid is not None and not self._is_admin() and rec.get("bank_id") not in (None, ""):
                    # 成绩只能记在自己能打开的题库上，防止猜题库编号探测
                    try:
                        bank_id = int(rec["bank_id"])
                    except (TypeError, ValueError):
                        raise HttpError(400, "bank_id 不合法") from None
                    if not self._bank_visible(db.get_bank(bank_id)):
                        raise HttpError(404, "题库不存在")
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

        # ---- 成绩汇总：每个学生 × 每套题一行；点开一行看每一次的明细 ----
        if path == "/api/scores/summary" and method == "GET":
            scope = self._scope()
            self.send_json({"ok": True, **scorebook.summarize(
                db, people=tenancy.people_where(scope, "s.user_id"),
                class_name=query.get("class_name", "") if scope.staff else "",
                bank_id=int_param(query.get("bank_id"), "bank_id"), q=query.get("q", ""))})
            return
        if path == "/api/scores/plays" and method == "GET":
            scope = self._scope()
            if scope.staff or scope.kind == tenancy.GUEST:
                uid = int_param(query.get("user_id"), "user_id")
                device = None if uid is not None else (query.get("device") if "device" in query else None)
            else:
                uid, device = self._uid(), None          # 学生只能看自己的，传什么参数都一样
            if uid is None and device is None:
                raise HttpError(400, "请指明是谁的成绩")
            bank_id = int_param(query.get("bank_id"), "bank_id")
            self.send_json({"ok": True, "plays": scorebook.plays_of(
                db, user_id=uid, device=device, bank_id=bank_id, people=tenancy.people_where(scope, "s.user_id"),
                bank_title=query.get("bank_title") if bank_id is None and "bank_title" in query else None)})
            return

        if path == "/api/stats" and method == "GET":
            self.send_json({"ok": True, **db.score_stats(people=tenancy.people_where(self._scope(), "user_id"))})
            return

        raise HttpError(404, f"未知接口 {path}")

    # ---------------- 登录 / 账号 ----------------

    def handle_auth(self, method: str, path: str) -> None:
        if path == "/api/auth/me" and method == "GET":
            self.send_json({"ok": True, "auth_enabled": self.auth is not None,
                            "guest_mode": self._guest_entrance(),
                            "user": auth_mod.AuthService.public(self.user)})
            return
        if self.auth is None:
            raise HttpError(404, "家庭版没有登录功能")
        try:
            if path == "/api/auth/login" and method == "POST":
                body = self.read_json()
                typed = body.get("student_no", "")
                try:
                    user, token = self.auth.login(typed, body.get("password", ""))
                except auth_mod.AuthError as exc:
                    self._record_login(typed, None, False, exc.code)
                    raise
                self._record_login(typed, user, True, "")
                self.send_json_with_cookie({"ok": True, "user": self.auth.public(user)},
                                           self.auth.cookie_header(token, self._secure_cookie()))
                return
            if path == "/api/auth/logout" and method == "POST":
                self.read_body()
                self.auth.logout(self._session_token())
                self.send_json_with_cookie({"ok": True}, self.auth.clear_cookie_header(self._secure_cookie()))
                return
            if path == "/api/auth/change-password" and method == "POST":
                body = self.read_json()
                if not self.user:
                    raise HttpError(401, "请先登录", "login_required")
                token = self.auth.change_password(self.user, body.get("old_password", ""),
                                                  body.get("new_password", ""), self._session_token())
                fresh = self.auth.get_by_id(self.user["id"])
                self.send_json_with_cookie({"ok": True, "user": self.auth.public(fresh)},
                                           self.auth.cookie_header(token, self._secure_cookie()))
                return
        except auth_mod.AuthError as exc:
            raise HttpError(exc.status, exc.message, exc.code) from exc
        raise HttpError(404, f"未知接口 {path}")

    def _secure_cookie(self) -> bool:
        """会话 Cookie 带 Secure 吗：配置要求带，除非我们自己的 nginx 明确说这条请求是明文 http
        （内网入口 http://内网地址:8082 没有证书；带着 Secure 浏览器会直接丢掉 Cookie，登不上）。公网入口恒为 https。"""
        if not (self.auth is not None and self.auth.cookie_secure):
            return False
        return not (self._peer() in accesslog.LOOPBACK and self.headers.get("X-Forwarded-Proto") == "http")

    def _peer(self) -> str:
        return self.client_address[0] if self.client_address else ""

    def _record_login(self, typed, user: dict | None, success: bool, code: str) -> None:
        """登录成功和失败都记；记录出错绝不能影响登录本身。"""
        try:
            info = accesslog.request_info(self.headers, self._peer())
            if user is None and typed:       # 失败的也尽量带上账号信息，老师才知道是谁在试
                user = self.auth.get_by_student_no(self.auth.normalize_student_no(typed)) \
                    if len(str(typed)) <= 64 else None
            accesslog.record_login(self.db, str(typed or ""), user, success, code, info)
        except Exception:      # pragma: no cover
            traceback.print_exc()

    def handle_track(self) -> None:
        """页面上报：打开、每 15 秒一次的在线心跳、离开。无效的悄悄丢掉；永远回 204。"""
        body = self.read_json()
        if self.auth is not None:
            info = accesslog.request_info(self.headers, self._peer())
            if self.track_throttle.allow(info["ip"]):
                try:
                    accesslog.track(self.db, self.user, info, body)
                except Exception:      # pragma: no cover
                    traceback.print_exc()
        self._send(204, b"", "text/plain")

    def send_json_with_cookie(self, obj, cookie: str, status: int = 200) -> None:
        self._send(status, json_bytes(obj), "application/json; charset=utf-8", {"Set-Cookie": cookie})

    def handle_super(self, method: str, path: str, query: dict) -> bool:
        """超级管理员专属：老师、共享 / 分配、已删除和恢复、审计记录。处理了返回 True。"""
        db, auth = self.db, self.auth
        if not (path.startswith("/api/admin/teachers") or path in ("/api/admin/assign", "/api/admin/deleted",
                                                                    "/api/admin/restore", "/api/admin/audit")):
            return False
        self._need_admin()
        me = self._uid()

        if path == "/api/admin/teachers" and method == "GET":
            rows = db.query(
                "SELECT u.id, u.student_no, u.name, u.role, u.disabled, u.must_change, u.last_login_at, u.created_at, u.teacher_group, "
                "(SELECT COUNT(*) FROM teacher_students ts JOIN users s ON s.id=ts.student_id "
                " WHERE ts.teacher_id=u.id AND s.deleted_at=0) AS students, "
                "(SELECT COUNT(*) FROM banks b WHERE b.owner_id=u.id AND b.deleted_at=0) AS own_banks, "
                "(SELECT COUNT(*) FROM teacher_banks tb JOIN banks b ON b.id=tb.bank_id "
                " WHERE tb.teacher_id=u.id AND b.deleted_at=0) AS shared_banks, "
                "(SELECT COUNT(*) FROM materials m WHERE m.owner_id=u.id AND m.deleted_at=0) AS materials "
                "FROM users u WHERE u.role IN ('admin','teacher') AND u.deleted_at=0 ORDER BY u.role, u.id")
            self.send_json({"ok": True, "teachers": [dict(r) for r in rows]})
            return True

        if path == "/api/admin/teachers" and method == "POST":
            body = self.read_json()
            password = str(body.get("password") or "") or None
            if password and len(password) < 8:
                raise HttpError(400, "初始密码至少 8 位（或留空自动生成）", "bad_password")
            try:
                user, plain = auth.create_user(body.get("student_no", ""), body.get("name", ""), password=password,
                                               role="teacher", must_change=True)
            except auth_mod.AuthError as exc:
                raise HttpError(exc.status, exc.message, exc.code) from exc
            tenancy.audit(db, me, "teacher.create", "user", user["id"], student_no=user["student_no"], name=user["name"])
            self.send_json({"ok": True, "teacher": auth.public(user), "password": plain}, status=201)
            return True

        m = re.fullmatch(r"/api/admin/teachers/(\d+)/group", path)
        if m and method == "POST":
            target = auth.get_by_id(int(m.group(1)))
            if not target or target["role"] not in policy.STAFF_ROLES or target.get("deleted_at"):
                raise HttpError(404, "没有这位老师")
            group = tenancy.set_teacher_group(db, target["id"], self.read_json().get("group", ""))
            tenancy.audit(db, me, "teacher.group", "user", target["id"], teacher=target["name"], group=group)
            self.send_json({"ok": True, "group": group})
            return True

        m = re.fullmatch(r"/api/admin/teachers/(\d+)/delete", path)
        if m and method == "POST":
            target = auth.get_by_id(int(m.group(1)))
            if not target or target["role"] != "teacher" or target.get("deleted_at"):
                raise HttpError(404, "没有这位老师")
            tenancy.soft_delete(db, "users", target["id"], me)
            tenancy.audit(db, me, "teacher.delete", "user", target["id"], student_no=target["student_no"])
            self.send_json({"ok": True})
            return True

        if path == "/api/admin/assign" and method == "POST":
            body = self.read_json()
            kind, mode = body.get("kind"), body.get("mode")
            ids, teacher_id = body.get("ids"), body.get("teacher_id")
            if kind not in ("bank", "student") or mode not in ("share", "move", "unshare"):
                raise HttpError(400, "kind 是 bank / student，mode 是 share / move / unshare", "bad_assign")
            if not isinstance(ids, list) or not ids or not all(isinstance(i, int) for i in ids):
                raise HttpError(400, "请选择要分配的题库或学生", "bad_assign")
            teacher = auth.get_by_id(int(teacher_id)) if isinstance(teacher_id, int) else None
            if not teacher or teacher["role"] not in policy.STAFF_ROLES or teacher.get("deleted_at"):
                raise HttpError(400, "请选择一位老师", "bad_teacher")
            changed = 0
            for row_id in ids:
                if kind == "bank":
                    bank = db.get_bank(row_id)
                    if not bank or bank.get("deleted_at"):
                        continue
                    if mode == "share":
                        changed += tenancy.link_bank(db, teacher["id"], row_id, me)
                    elif mode == "move":
                        tenancy.move_bank(db, row_id, teacher["id"])
                        changed += 1
                    else:
                        tenancy.unlink_bank(db, teacher["id"], row_id)
                        changed += 1
                else:
                    student = auth.get_by_id(row_id)
                    if not student or student["role"] != "student" or student.get("deleted_at"):
                        continue
                    if mode == "share":
                        changed += tenancy.link_student(db, teacher["id"], row_id, me)
                    elif mode == "move":
                        tenancy.move_student(db, row_id, teacher["id"], me)
                        changed += 1
                    else:
                        tenancy.unlink_student(db, teacher["id"], row_id)
                        changed += 1
                tenancy.audit(db, me, kind + "." + mode, kind if kind == "bank" else "user", row_id,
                              teacher_id=teacher["id"], teacher=teacher["name"])
            self.send_json({"ok": True, "changed": changed})
            return True

        if path == "/api/admin/deleted" and method == "GET":
            self.send_json({"ok": True, **tenancy.deleted_rows(db)})
            return True

        if path == "/api/admin/restore" and method == "POST":
            body = self.read_json()
            table = {"user": "users", "bank": "banks", "material": "materials"}.get(body.get("kind"))
            if not table or not isinstance(body.get("id"), int):
                raise HttpError(400, "kind 是 user / bank / material，id 是编号", "bad_restore")
            if not tenancy.restore(db, table, body["id"]):
                raise HttpError(404, "没有这条已删除的记录")
            tenancy.audit(db, me, body["kind"] + ".restore", body["kind"], body["id"])
            self.send_json({"ok": True})
            return True

        if path == "/api/admin/audit" and method == "GET":
            self.send_json({"ok": True, "audit": tenancy.audit_rows(db, int_param(query.get("limit"), "limit", 200, 1, 1000))})
            return True

        raise HttpError(404, f"未知接口 {path}")

    def _managed_user(self, uid: int) -> dict:
        """这个人管得了的账号；管不了的一律当成不存在（别让老师探测别人有哪些学生）。老师不能动老师 / 管理员。"""
        target = self.auth.get_by_id(uid)
        if not tenancy.can_manage_user(self.db, self._scope(), target):
            raise HttpError(404, "没有这个用户")
        return target

    def handle_admin(self, method: str, path: str, query: dict) -> None:
        auth = self.auth
        scope = self._scope()
        if self.handle_super(method, path, query):
            return
        try:
            if path == "/api/admin/users" and method == "GET":
                users = auth.list_users(class_name=query.get("class_name", ""),
                                        college=query.get("college", ""),
                                        department=query.get("department", ""),
                                        q=query.get("q", "").strip(), scope=scope,
                                        role=query.get("role", "") if scope.everything else "")
                self.send_json({"ok": True, "users": users, "super": scope.everything})
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
                report = auth.import_roster(table["rows"], reset_existing=reset,
                                            teacher_id=scope.tag_teacher or None, actor=self._uid())
                report["ignored_columns"] = table["ignored_columns"]
                self.send_json({"ok": True, **report})
                return

            if path == "/api/admin/tags" and method == "GET":
                self.send_json({"ok": True, "tags": self.db.all_tags(teacher_id=scope.tag_teacher)})
                return

            if path == "/api/admin/users/tags" and method == "POST":
                # 批量：给一批（自己名下的）学生加 / 去自己的标签
                payload = self.read_json()
                ids = payload.get("user_ids")
                if not isinstance(ids, list) or not ids or not all(isinstance(i, int) for i in ids):
                    raise HttpError(400, "请选择要修改的学生")
                try:
                    add, remove = normalize_tags(payload.get("add")), normalize_tags(payload.get("remove"))
                except TagError as exc:
                    raise HttpError(400, exc.args[0], "bad_tags") from exc
                if not add and not remove:
                    raise HttpError(400, "请填写要加或要去掉的标签")
                known = {u["id"] for u in auth.list_users(scope=scope) if u["role"] == "student"}
                ids = [i for i in ids if i in known]
                self.db.change_user_tags(ids, add, remove, teacher_id=scope.tag_teacher)
                self.send_json({"ok": True, "changed": len(ids)})
                return

            if path == "/api/admin/users/delete" and method == "POST":
                # 删学生 / 删一个班：软删除；也挂在别的老师名下的，只从自己名下移走
                ids = self.read_json().get("user_ids")
                if not isinstance(ids, list) or not ids or not all(isinstance(i, int) for i in ids):
                    raise HttpError(400, "请选择要删除的学生")
                done = {"deleted": 0, "unlinked": 0}
                for uid in ids:
                    target = auth.get_by_id(uid)
                    if not target or target.get("deleted_at") or target["role"] != "student" \
                            or not tenancy.can_manage_user(self.db, scope, target):
                        continue
                    result = tenancy.delete_student_for(self.db, scope, target)
                    done[result] += 1
                    tenancy.audit(self.db, self._uid(), "student." + ("delete" if result == "deleted" else "unlink_self"),
                                  "user", uid, student_no=target["student_no"])
                self.send_json({"ok": True, **done})
                return

            m = re.fullmatch(r"/api/admin/users/(\d+)/tags", path)
            if m and method == "POST":
                target = self._managed_user(int(m.group(1)))
                try:
                    tags = normalize_tags(self.read_json().get("tags"))
                except TagError as exc:
                    raise HttpError(400, exc.args[0], "bad_tags") from exc
                self.db.set_user_tags(target["id"], tags, teacher_id=scope.tag_teacher)
                self.send_json({"ok": True, "tags": tags})
                return

            if path == "/api/admin/share-requests" and method == "GET":
                self.send_json({"ok": True, **tenancy.share_requests(self.db, scope)})
                return

            m = re.fullmatch(r"/api/admin/share-requests/(\d+)/decide", path)
            if m and method == "POST":
                try:
                    status = tenancy.decide_share_request(self.db, scope, int(m.group(1)),
                                                          bool(self.read_json().get("approve")), self._uid())
                except LookupError as exc:
                    raise HttpError(404, str(exc), "no_request") from exc
                except PermissionError as exc:
                    raise HttpError(403, str(exc), "not_primary") from exc
                self.send_json({"ok": True, "status": status})
                return

            m = re.fullmatch(r"/api/admin/users/(\d+)/(reset-password|disabled|unlock)", path)
            if m and method == "POST":
                uid, action = int(m.group(1)), m.group(2)
                payload = self.read_json()
                target = self._managed_user(uid)
                if not tenancy.can_manage_account(self.db, scope, target):
                    raise HttpError(403, "这个学生由别的老师负责，只有他或超级管理员能重置密码、停用、解锁", "not_primary")
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

            if path == "/api/admin/export/score-summary.csv" and method == "GET":
                data = self._score_summary_csv(query)
                self._send(200, data, "text/csv; charset=utf-8", {
                    "Content-Disposition": 'attachment; filename="lexica-score-summary.csv"'})
                return

            if path == "/api/admin/visits" and method == "GET":
                self.send_json(dict(ok=True, **accesslog.sessions(
                    self.db, role=query.get("role", ""), class_name=query.get("class_name", ""), q=query.get("q", "").strip(),
                    people=tenancy.people_where(scope, "user_id"),
                    since=int_param(query.get("since"), "since"), until=int_param(query.get("until"), "until"),
                    limit=int_param(query.get("limit"), "limit", 100, 1, 500),
                    offset=int_param(query.get("offset"), "offset", 0, 0))))
                return

            if path == "/api/admin/visits/pages" and method == "GET":
                uid = int_param(query.get("user_id"), "user_id")
                self.send_json({"ok": True, "pages": accesslog.session_pages(self.db, query.get("sid", ""), uid,
                                                                             people=tenancy.people_where(scope, "user_id"))})
                return

            if path == "/api/admin/logins" and method == "GET":
                self.send_json(dict(ok=True, **accesslog.logins(
                    self.db, role=query.get("role", ""), class_name=query.get("class_name", ""), q=query.get("q", "").strip(),
                    people=tenancy.people_where(scope, "user_id"),
                    only_failed=query.get("failed") == "1",
                    since=int_param(query.get("since"), "since"), until=int_param(query.get("until"), "until"),
                    limit=int_param(query.get("limit"), "limit", 100, 1, 500),
                    offset=int_param(query.get("offset"), "offset", 0, 0))))
                return

            if path in ("/api/admin/export/page-views.csv", "/api/admin/export/logins.csv") and method == "GET":
                table = "page_views" if "page-views" in path else "login_events"
                self._send(200, self._access_csv(table, query), "text/csv; charset=utf-8", {
                    "Content-Disposition": 'attachment; filename="lexica-%s.csv"' % ("page-views" if table == "page_views" else "logins")})
                return

            if path == "/api/admin/export/scores.csv" and method == "GET":
                data = self._scores_csv(query)
                self._send(200, data, "text/csv; charset=utf-8", {
                    "Content-Disposition": 'attachment; filename="lexica-scores.csv"'})
                return
        except auth_mod.AuthError as exc:
            raise HttpError(exc.status, exc.message, exc.code) from exc
        raise HttpError(404, f"未知接口 {path}")

    def _score_summary_csv(self, query: dict) -> bytes:
        """一人一套题一行的汇总，老师拿去排名 / 存档。"""
        data = scorebook.summarize(self.db, class_name=query.get("class_name", ""),
                                   people=tenancy.people_where(self._scope(), "s.user_id"),
                                   bank_id=int_param(query.get("bank_id"), "bank_id"), q=query.get("q", ""))
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(["班级", "学号", "姓名", "题库", "次数", "完成次数", "最高分", "最低分", "平均分",
                         "平均用时(秒)", "最近一次"])
        for r in data["rows"]:
            cells = [r["class_name"], r["student_no"], r["name"], r["bank_title"], r["plays"], r["completed"],
                     r["best"], r["worst"], r["avg_score"], r["avg_duration"], r["last_at"]]
            # 以 = + - @ 开头的单元格在 Excel 里会被当成公式，前面补一个单引号
            writer.writerow([("'" + v) if isinstance(v, str) and v[:1] in "=+-@" else v for v in cells])
        return ("\ufeff" + out.getvalue()).encode("utf-8")

    def handle_recent(self, method: str, query: dict) -> None:
        """首页「最近玩过」，按账号存在服务器上，换设备也看得到。没登录的访客（家庭版内网入口）没有账号，
        接口告诉页面 device_only，页面就改用这台设备浏览器里的记录。"""
        db = self.db
        uid = self._uid()
        if method == "POST":
            body = self.read_json()
            try:
                bank_id = int(body.get("bank_id"))
            except (TypeError, ValueError):
                raise HttpError(400, "bank_id 不合法", "bad_bank") from None
            bank = db.get_bank(bank_id)
            if not self._bank_visible(bank):
                raise HttpError(404, "题库不存在")
            if uid is None:
                self.send_json({"ok": True, "stored": False, "device_only": True})
                return
            db.touch_recent(uid, bank_id, int(time.time()))
            self.send_json({"ok": True, "stored": True})
            return
        if method == "GET":
            if uid is None:
                self.send_json({"ok": True, "recent": [], "device_only": True})
                return
            limit = int_param(query.get("limit"), "limit", 4, 1, db.RECENT_KEEP)
            by_id = {b["id"]: b for b in db.list_banks()}
            out = []
            for row in db.recent_rows(uid):
                bank = by_id.get(row["bank_id"])
                if bank and self._bank_visible(bank) and len(out) < limit:      # 现在看不到的（被收回标签）不给
                    out.append({"bank": bank, "last_at": row["last_at"]})
            self.send_json({"ok": True, "recent": out})
            return
        raise HttpError(405, "不支持的方法")

    def handle_records(self, method: str, query: dict) -> None:
        """各学科通用的成绩 / 进度：POST 存一条，GET 取（学生只看自己的，老师按 policy 看全部）。"""
        db = self.db
        if method == "POST":
            body = self.read_json()
            subject = str(body.get("subject") or "")
            if subject not in modules.enabled_ids():
                raise HttpError(400, "未知的学科模块", "bad_subject")
            payload = body.get("payload", {})
            if not isinstance(payload, dict):
                raise HttpError(400, "payload 需要是 JSON 对象", "bad_payload")
            text = json.dumps(payload, ensure_ascii=False)
            if len(text.encode("utf-8")) > 20 * 1024:
                raise HttpError(413, "payload 太大（上限 20KB）", "payload_too_large")
            uid = self._uid()
            device = "" if uid is not None else re.sub(r"[^A-Za-z0-9_.:-]", "", str(body.get("device") or ""))[:64]
            kind = re.sub(r"[^A-Za-z0-9_.-]", "", str(body.get("kind") or ""))[:40]
            cur = db.execute("INSERT INTO subject_records(user_id, device, subject, kind, payload, created_at) VALUES (?,?,?,?,?,?)",
                             (uid, device, subject, kind, text, int(time.time())))
            self.send_json({"ok": True, "id": cur.lastrowid}, status=201)
            return
        if method == "GET":
            subject = query.get("subject", "")
            limit = int_param(query.get("limit"), "limit", 100, 1, 500)
            where, args = [], []
            if subject:
                where.append("subject=?")
                args.append(subject)
            if query.get("kind"):
                where.append("kind=?")
                args.append(query["kind"])
            if policy.allow(self.user, "records.read_all", {"subject": subject}) or self.auth is None:
                people, pargs = tenancy.people_where(self._scope(), "user_id")       # 老师只看自己名下学生的
                where.append(people)
                args += list(pargs)
                if query.get("user_id"):
                    where.append("user_id=?")
                    args.append(int_param(query["user_id"], "user_id"))
            elif self.user:
                where.append("user_id=?")
                args.append(self.user["id"])
            elif query.get("device"):
                where.append("user_id IS NULL AND device=?")
                args.append(query["device"])
            else:
                raise HttpError(400, "请指明 device", "need_device")
            sql = "SELECT id, user_id, device, subject, kind, payload, created_at FROM subject_records"
            if where:
                sql += " WHERE " + " AND ".join(where)
            rows = db.query(sql + " ORDER BY id DESC LIMIT ?", (*args, limit))
            records = []
            for r in rows:
                d = dict(r)
                try:
                    d["payload"] = json.loads(d["payload"])
                except ValueError:
                    d["payload"] = {}
                records.append(d)
            self.send_json({"ok": True, "records": records})
            return
        raise HttpError(405, "不支持的方法")

    def _access_csv(self, table: str, query: dict) -> bytes:
        """访问记录 / 登录记录的完整导出：所有列，时间换成 UTC+8 的可读时间。"""
        cols, rows = accesslog.all_rows(self.db, table, class_name=query.get("class_name", ""), q=query.get("q", "").strip(),
                                        people=tenancy.people_where(self._scope(), "user_id"),
                                        since=int_param(query.get("since"), "since"), until=int_param(query.get("until"), "until"))
        stamps = {"ts", "started_at", "last_seen_at"}
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(cols)
        for row in rows:
            cells = []
            for col, v in zip(cols, row):
                if col in stamps and isinstance(v, int):
                    v = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(v + 8 * 3600))
                if isinstance(v, str) and v[:1] in "=+-@":
                    v = "'" + v
                cells.append(v)
            writer.writerow(cells)
        return ("\ufeff" + out.getvalue()).encode("utf-8")

    def _scores_csv(self, query: dict) -> bytes:
        people, pargs = tenancy.people_where(self._scope(), "s.user_id")      # 老师只导出自己名下学生的
        where, args = [people], list(pargs)
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
                                      note, words, owner_id=self._uid())
        info = materials.summary(words)
        self.send_json({"ok": True, "material": self.db.get_material(mid),
                        "summary": info}, status=201)

    def _make_offline(self, bid: int, kind: str = "game") -> None:
        db = self.db
        bank = db.get_bank(bid)
        if not self._bank_visible(bank):              # 别人的、删掉的：当成不存在
            raise HttpError(404, "题库不存在")
        try:
            # 和在线玩法用同一套分组（含「词多的单元拆成多关」）
            payload = bank_mod.bank_payload(db, bid)["groups"]
        except bank_mod.BankError as exc:
            raise HttpError(404, str(exc)) from exc
        words = db.bank_words(bid)
        try:
            audio = tts.synth_many([word["en"] for word in words])
            if kind == "practice":
                filename, html = offline.build_practice_html(bank, payload, audio=audio)
            else:
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
    """auth: None = 看环境变量 WP_AUTH（1 = 带登录；内网入口是否允许不登录由 WP_LAN_GUEST 决定）；True / dict = 启用登录（dict 是 AuthService 的参数）；False = 关闭。"""
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
    print("  登录：" + ("已启用（学生版）" if Handler.auth else "未启用（家庭版）"))
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
