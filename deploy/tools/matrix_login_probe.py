#!/usr/bin/env python3
"""直接调用 Matrix 的 password 登录 API 做**凭据对照**（AI1 #271）。

目的：把"凭据本身是否有效"与"RFB 键盘注入是否把字符打错"分开。
**绝不打印**请求体、密码、access_token；只打印 HTTP 状态 / errcode / 是否成功 /
脱敏 user_id。成功时把 token 写入 600 文件（不进日志、不进聊天）。

用法: matrix_login_probe.py [--creds PATH] [--homeserver HOST] [--token-out PATH]
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_CREDS = "/root/oncue-runtime/state/ai2-credentials.json"
DEFAULT_HS = "matrix-client.matrix.org"          # 由 Rinx 的发现流程得到
DEFAULT_TOKEN_OUT = "/root/oncue-runtime/state/matrix-session.json"
PROXY = "http://127.0.0.1:17888"
TIMEOUT = 30


def mask(v, keep=2):
    if len(v) <= keep * 2:
        return f"len={len(v)} ***"
    return f"len={len(v)} {v[:keep]}***{v[-keep:]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--creds", default=DEFAULT_CREDS)
    ap.add_argument("--homeserver", default=DEFAULT_HS)
    ap.add_argument("--token-out", default=DEFAULT_TOKEN_OUT)
    ap.add_argument("--no-proxy", action="store_true")
    a = ap.parse_args()

    creds = json.loads(Path(a.creds).read_text(encoding="utf-8"))["matrix"]
    user_id = creds["user_id"]
    username = creds["username"]
    password = creds["password"]

    url = f"https://{a.homeserver}/_matrix/client/v3/login"
    body = json.dumps({
        "type": "m.login.password",
        "identifier": {"type": "m.id.user", "user": user_id},
        "password": password,
        "initial_device_display_name": "oncue-recovery-probe",
    }).encode()

    print(f"POST {url}")
    print(f"identifier(user_id) = @{mask(user_id.lstrip('@'))}")
    print(f"password            = {mask(password)}")
    print(f"proxy               = {'(直连)' if a.no_proxy else PROXY}")

    handlers = []
    if not a.no_proxy:
        handlers.append(urllib.request.ProxyHandler({"https": PROXY, "http": PROXY}))
    opener = urllib.request.build_opener(*handlers)
    req = urllib.request.Request(url, data=body,
                                headers={"Content-Type": "application/json"},
                                method="POST")

    status, payload = None, None
    try:
        with opener.open(req, timeout=TIMEOUT) as r:
            status = r.status
            payload = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        status = e.code
        raw = e.read().decode(errors="replace")
        try:
            payload = json.loads(raw)
        except ValueError:
            payload = {"_raw_len": len(raw)}

    print(f"HTTP 状态: {status}")

    if status == 200 and isinstance(payload, dict) and payload.get("access_token"):
        token = payload["access_token"]
        out = {
            "homeserver": f"https://{a.homeserver}",
            "user_id": payload.get("user_id", user_id),
            "device_id": payload.get("device_id", ""),
            "access_token": token,
        }
        p = Path(a.token_out)
        p.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(p.parent, 0o700)
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        os.chmod(p, 0o600)
        st = os.stat(p)
        # 只报脱敏结果
        print("结果: **登录成功（凭据有效）**")
        print(f"  user_id  = {mask(payload.get('user_id', ''))}")
        print(f"  device_id= {payload.get('device_id', '')}")
        print(f"  token 已写入 600 文件: {p}（权限 {oct(st.st_mode & 0o777)}，{st.st_size} B，不打印内容）")
        return 0

    # 失败：只输出 errcode 与脱敏信息
    errcode = payload.get("errcode") if isinstance(payload, dict) else None
    print(f"结果: **失败**")
    print(f"  errcode = {errcode}")
    if isinstance(payload, dict) and "error" in payload:
        # error 文案不含凭据，可安全展示
        print(f"  error   = {payload['error']}")
    print("  （请求体、密码、token 均未打印）")
    return 1


if __name__ == "__main__":
    sys.exit(main())
