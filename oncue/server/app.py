"""Small single-user preview service; Python 3.9+ standard library only."""
from __future__ import annotations

import argparse
import hmac
import http.cookies
import ipaddress
import json
import os
import secrets
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from engine import AppError, MiniMaxProvider, local_rehearsal, normalize_request, route_warnings, scenes

STATIC = Path(__file__).resolve().parent / "static"
ASSETS = {"/": ("index.html", "text/html; charset=utf-8"),
          "/app.js": ("app.js", "text/javascript; charset=utf-8"),
          "/style.css": ("style.css", "text/css; charset=utf-8")}


class OnCueServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, token="", provider=None, allowed_hosts=None, secure_cookie=False):
        super().__init__(address, Handler)
        self.token = token
        self.secure_cookie = secure_cookie
        self.provider = provider or MiniMaxProvider.from_environment()
        self.allowed_hosts = allowed_hosts or {"localhost", "127.0.0.1", "::1"}
        self.sessions = {}
        self.session_lock = threading.Lock()
        self.model_slots = threading.BoundedSemaphore(2)

    def create_session(self):
        value, now = secrets.token_urlsafe(32), time.monotonic()
        with self.session_lock:
            self.sessions = {k: v for k, v in self.sessions.items() if v > now}
            # Single-user preview; do not let unsuccessful browsers exhaust memory.
            if len(self.sessions) >= 128:
                self.sessions.pop(next(iter(self.sessions)))
            self.sessions[value] = now + 12 * 3600
        return value


class Handler(BaseHTTPRequestHandler):
    server: OnCueServer
    server_version = "OnCue/0.2"

    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def log_message(self, fmt, *args):
        # Avoid logging URLs, query strings, user input, model responses or credentials.
        pass

    def reply(self, status, value, content_type="application/json; charset=utf-8", cookie=None):
        data = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(data)

    def error(self, error):
        self.reply(error.status, {"error": {"code": error.code, "message": str(error)}})

    def check_host(self):
        try:
            host = urllib.parse.urlsplit("//" + self.headers.get("Host", "")).hostname
            if host not in self.server.allowed_hosts:
                raise AppError("访问地址不在配置范围内。", 403, "host_not_allowed")
        except ValueError:
            raise AppError("访问地址格式错误。", 400, "invalid_host") from None

    def authenticated(self):
        if not self.server.token:
            return True
        cookies = http.cookies.SimpleCookie()
        try:
            cookies.load(self.headers.get("Cookie", ""))
        except http.cookies.CookieError:
            return False
        value = cookies.get("oncue_session")
        with self.server.session_lock:
            return bool(value and self.server.sessions.get(value.value, 0) > time.monotonic())

    def require_auth(self):
        if not self.authenticated():
            raise AppError("请输入访问口令，打开你的试映室。", 401, "login_required")

    def read_json(self):
        if self.headers.get_content_type() != "application/json":
            raise AppError("请求需使用JSON格式。", 415, "invalid_content_type")
        origin = self.headers.get("Origin")
        if origin:
            parsed = urllib.parse.urlsplit(origin)
            if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() != self.headers.get("Host", "").lower():
                raise AppError("请从试映室页面发起操作。", 403, "invalid_origin")
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            raise AppError("请从试映室页面发起操作。", 403, "invalid_origin")
        if self.headers.get("Transfer-Encoding"):
            raise AppError("不支持此请求传输格式。", 400)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 65_536:
                raise AppError("消息过长，请精简到20条以内。", 413, "payload_too_large")
            if length <= 0:
                raise ValueError()
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeError):
            raise AppError("请求内容不是有效JSON。") from None

    def do_GET(self):
        try:
            self.check_host()
            path = urllib.parse.urlsplit(self.path).path
            if path in ASSETS:
                name, media_type = ASSETS[path]
                self.reply(200, (STATIC / name).read_bytes(), media_type)
            elif path == "/healthz":
                self.reply(200, {"ok": True, "version": "0.2.0"})
            elif path == "/api/status":
                auth = self.authenticated()
                self.reply(200, {"authenticated": auth, "requires_login": bool(self.server.token),
                                 "model_ready": self.server.provider.configured if auth else False,
                                 "model": self.server.provider.model if auth else ""})
            elif path == "/api/scenes":
                self.require_auth()
                self.reply(200, {"scenes": scenes()})
            else:
                raise AppError("这个页面不存在。", 404, "not_found")
        except AppError as error:
            self.error(error)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        try:
            self.check_host()
            path = urllib.parse.urlsplit(self.path).path
            if path == "/api/login":
                data = self.read_json()
                token = data.get("token", "") if isinstance(data, dict) else ""
                if not isinstance(token, str) or len(token) > 256 or not hmac.compare_digest(token.encode(), self.server.token.encode()):
                    raise AppError("访问口令不正确，请重新输入。", 401, "invalid_token")
                session = self.server.create_session()
                cookie = "oncue_session=" + session + "; HttpOnly; SameSite=Strict; Path=/; Max-Age=43200"
                if self.server.secure_cookie:
                    cookie += "; Secure"
                self.reply(200, {"ok": True}, cookie=cookie)
                return
            self.require_auth()
            if path == "/api/logout":
                self.read_json()
                cookies = http.cookies.SimpleCookie(self.headers.get("Cookie", ""))
                value = cookies.get("oncue_session")
                if value:
                    with self.server.session_lock:
                        self.server.sessions.pop(value.value, None)
                self.reply(200, {"ok": True}, cookie="oncue_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0")
            elif path == "/api/rehearse":
                request = normalize_request(self.read_json())
                if request["mode"] == "demo":
                    result = local_rehearsal(request)
                else:
                    if not self.server.model_slots.acquire(blocking=False):
                        raise AppError("还有试映正在进行，请等它结束后重试。", 429, "busy")
                    try:
                        result = self.server.provider.rehearse(request)
                    finally:
                        self.server.model_slots.release()
                result["trial_warnings"] = route_warnings({"draft": request["trial"], "replies": []}, request["messages"])
                for route in result["routes"]:
                    if "warnings" not in route:
                        route["warnings"] = route_warnings(route, request["messages"])
                self.reply(200, {"result": result})
            else:
                raise AppError("这个操作不存在。", 404, "not_found")
        except AppError as error:
            self.error(error)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            self.error(AppError("试映服务暂时没有完成，请重试。", 500, "internal_error"))


def main():
    parser = argparse.ArgumentParser(description="OnCue 群聊试映室，无需图形桌面。")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    token = os.environ.get("ONCUE_ACCESS_TOKEN", "")
    try:
        loopback = args.host == "localhost" or ipaddress.ip_address(args.host).is_loopback
    except ValueError:
        loopback = False
    if not loopback and len(token) < 24:
        parser.error("远程监听需要至少24字符的ONCUE_ACCESS_TOKEN。")
    hosts = {h.strip() for h in os.environ.get("ONCUE_ALLOWED_HOSTS", "localhost,127.0.0.1,::1").split(",") if h.strip()}
    try:
        server = OnCueServer((args.host, args.port), token=token, allowed_hosts=hosts,
                             secure_cookie=os.environ.get("ONCUE_SECURE_COOKIE") == "1")
    except ValueError as exc:
        parser.error(str(exc))
    print(f"OnCue 已启动：http://{args.host}:{server.server_port}", flush=True)
    print("模型已配置。" if server.provider.configured else "本地演示可用。模型试映可在配置MINIMAX_API_KEY后开启。", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
