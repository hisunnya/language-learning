"""word-puzzle 后端。

只用 Python 标准库（``http.server`` + ``sqlite3``），服务器上不需要装任何依赖。

启动::

    python3 -m server.app --host 127.0.0.1 --port 8000

部署时 nginx 直接托管 ``web/`` 静态文件，把 ``/api/`` 反代到这里即可。
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import sys
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

if __package__ in (None, ""):  # 允许 `python3 server/app.py` 直接跑
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "server"

from server import bank as bank_mod           # noqa: E402
from server import hierarchy, materials, offline  # noqa: E402
from server.db import Database                 # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
OUTBOX = ROOT / "var" / "offline"

mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/json", ".json")


# ---------------------------------------------------------------- 工具

class HttpError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


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


def json_bytes(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False).encode("utf-8")


# ---------------------------------------------------------------- Handler

class Handler(BaseHTTPRequestHandler):
    server_version = "WordPuzzle/2.0"
    protocol_version = "HTTP/1.1"
    db: Database = None            # type: ignore[assignment]

    # ---------------- 基础响应 ----------------

    def log_message(self, fmt, *args):  # noqa: A003
        if os.environ.get("WP_QUIET"):
            return
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, status: int, body: bytes, ctype: str,
              extra: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def send_json(self, obj, status: int = 200) -> None:
        self._send(status, json_bytes(obj), "application/json; charset=utf-8")

    def send_error_json(self, status: int, message: str) -> None:
        self.send_json({"ok": False, "error": message}, status=status)

    def read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return b""
        if length > 50 * 1024 * 1024:
            raise HttpError(413, "请求体过大（上限 50MB）")
        return self.rfile.read(length)

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

    def _dispatch(self, method: str) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        query = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        try:
            if path.startswith("/api/"):
                self.handle_api(method, path, query)
            else:
                self.handle_static(path)
        except HttpError as exc:
            self.send_error_json(exc.status, exc.message)
        except Exception as exc:  # pragma: no cover - 兜底
            traceback.print_exc()
            self.send_error_json(500, f"服务器内部错误：{exc}")

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

        # ---- 层级元数据 ----
        if path == "/api/meta" and method == "GET":
            self.send_json({"ok": True, **hierarchy.describe()})
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
        if path == "/api/materials":
            if method == "GET":
                self.send_json({"ok": True, "materials": db.list_materials()})
                return
            if method == "POST":
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
                self.send_json({"ok": True, "banks": db.list_banks()})
                return
            if method == "POST":
                payload = self.read_json()
                try:
                    created = bank_mod.create_bank(db, payload)
                except bank_mod.BankError as exc:
                    raise HttpError(400, str(exc)) from exc
                self.send_json({"ok": True, "bank": created}, status=201)
                return

        m = re.fullmatch(r"/api/banks/(\d+)", path)
        if m and method == "GET":
            bid = int(m.group(1))
            try:
                self.send_json({"ok": True, **bank_mod.bank_payload(db, bid)})
            except bank_mod.BankError as exc:
                raise HttpError(404, str(exc)) from exc
            return

        m = re.fullmatch(r"/api/banks/(\d+)", path)
        if m and method == "DELETE":
            ok = db.delete_bank(int(m.group(1)))
            if not ok:
                raise HttpError(404, "题库不存在")
            self.send_json({"ok": True})
            return

        # ---- 生成离线测试页 ----
        m = re.fullmatch(r"/api/banks/(\d+)/offline", path)
        if m and method == "POST":
            self._make_offline(int(m.group(1)))
            return

        if path == "/api/offline" and method == "GET":
            self._list_offline()
            return

        m = re.fullmatch(r"/api/offline/([^/]+)", path)
        if m and method == "GET":
            self._download_offline(m.group(1), query.get("inline") == "1")
            return

        # ---- 成绩 ----
        if path == "/api/scores":
            if method == "GET":
                limit = min(int(query.get("limit", 100) or 100), 500)
                bank_id = query.get("bank_id")
                scores = db.list_scores(limit=limit,
                                        bank_id=int(bank_id) if bank_id else None)
                self.send_json({"ok": True, "scores": scores,
                                "stats": db.score_stats()})
                return
            if method == "POST":
                rec = self.read_json()
                try:
                    sid = db.insert_score(rec)
                except Exception as exc:
                    raise HttpError(400, f"成绩保存失败：{exc}") from exc
                self.send_json({"ok": True, "id": sid}, status=201)
                return

        if path == "/api/stats" and method == "GET":
            self.send_json({"ok": True, **db.score_stats()})
            return

        raise HttpError(404, f"未知接口 {path}")

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
        words = db.bank_words(bid)
        groups: dict[str, list[dict]] = {}
        order: list[str] = []
        for w in words:
            if w["unit"] not in groups:
                groups[w["unit"]] = []
                order.append(w["unit"])
            groups[w["unit"]].append(w)
        payload = [{"unit": u, "words": groups[u]} for u in order]
        try:
            filename, html = offline.build_offline_html(bank, payload)
        except ValueError as exc:
            raise HttpError(400, str(exc)) from exc
        OUTBOX.mkdir(parents=True, exist_ok=True)
        (OUTBOX / filename).write_text(html, encoding="utf-8")
        self.send_json({"ok": True, "filename": filename,
                        "url": "/api/offline/" + urllib_quote(filename),
                        "size": len(html.encode("utf-8")),
                        "levels": len(payload),
                        "words": len(words)})

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
        self._send(200, data, "text/html; charset=utf-8", {
            "Content-Disposition":
                f"{disp}; filename*=UTF-8''{quoted}",
        })


def urllib_quote(text: str) -> str:
    from urllib.parse import quote
    return quote(text, safe="")


# ---------------------------------------------------------------- 入口

def build_server(host: str = "127.0.0.1", port: int = 8000,
                 db_path: str | None = None) -> ThreadingHTTPServer:
    db = Database(db_path)
    Handler.db = db
    try:
        default_id = bank_mod.seed_default_bank(db)
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
