#!/usr/bin/env python3
"""通过 RFB(VncAuth) 向 x0vncserver 注入真实指针/键盘事件。

x0vncserver 把 RFB 事件经 XTest 送进 X server —— 走的是**真实事件路径**，
不是伪造的内部调用。用于驱动宿主 UI（启动应用、点按钮、填表单）。

用法:
  rfb_input.py click <x> <y>            # 左键单击
  rfb_input.py move <x> <y>             # 只移动
  rfb_input.py drag <x1> <y1> <x2> <y2>
  rfb_input.py type <text>              # 逐字符键入（ASCII 与 UTF-8 之外仅支持 keysym 直通）
  rfb_input.py key <keysym> [keysym…]   # 直接送 X keysym（16 进制或 10 进制）
  rfb_input.py keyname Return|Tab|BackSpace|Escape|Up|Down|Left|Right

密码从私有文件读，不在命令行暴露。
"""
import argparse
import os
import socket
import struct
import sys
import time
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

DES = algorithms.TripleDES
DEFAULT_RUNTIME = os.environ.get("ONCUE_RUNTIME_ROOT", "/srv/oncue-runtime")
DEFAULT_VNC_PW = str(Path(DEFAULT_RUNTIME) / "state" / "vnc" / "vnc.password.txt")

# RFB key codes: printable ASCII 的 keysym 就等于字符码
KEYNAMES = {
    "Return": 0xFF0D, "Enter": 0xFF0D, "Tab": 0xFF09, "BackSpace": 0xFF08,
    "Escape": 0xFF1B, "Delete": 0xFFFF, "Home": 0xFF50, "End": 0xFF57,
    "Left": 0xFF51, "Up": 0xFF52, "Right": 0xFF53, "Down": 0xFF54,
    "Space": 0x0020,
}


def vnc_des_key(password: bytes) -> bytes:
    pw = (password + b"\0" * 8)[:8]
    out = bytearray()
    for ch in pw:
        b = 0
        for i in range(8):
            b = (b << 1) | ((ch >> i) & 1)
        out.append(b)
    return bytes(out)


def recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise EOFError("连接关闭")
        buf += chunk
    return buf


def connect(host, port, password_file, timeout=20.0):
    password = Path(password_file).read_text().strip().encode()
    sock = socket.create_connection((host, port), timeout=timeout)
    sock.settimeout(timeout)
    recv_exact(sock, 12)
    sock.sendall(b"RFB 003.008\n")
    (nsec,) = struct.unpack(">B", recv_exact(sock, 1))
    secs = list(recv_exact(sock, nsec))
    if 2 not in secs:
        raise RuntimeError(f"服务端未提供 VncAuth（{secs}）")
    sock.sendall(struct.pack(">B", 2))
    challenge = recv_exact(sock, 16)
    enc = Cipher(DES(vnc_des_key(password)), modes.ECB()).encryptor()
    sock.sendall(enc.update(challenge) + enc.finalize())
    (result,) = struct.unpack(">I", recv_exact(sock, 4))
    if result != 0:
        raise RuntimeError(f"VNC 认证失败（{result}）")
    sock.sendall(struct.pack(">B", 1))  # shared
    recv_exact(sock, 4 + 16)            # ServerInit: w/h + pixel format
    (namelen,) = struct.unpack(">I", recv_exact(sock, 4))
    recv_exact(sock, namelen)
    return sock


def pointer(sock, x, y, mask):
    sock.sendall(struct.pack(">BBHH", 5, mask, x, y))


def click(sock, x, y, hold=0.06):
    pointer(sock, x, y, 0)
    time.sleep(0.05)
    pointer(sock, x, y, 1)   # button 1 down
    time.sleep(hold)
    pointer(sock, x, y, 0)   # up
    time.sleep(0.12)


def send_key(sock, keysym, down):
    sock.sendall(struct.pack(">BBHI", 4, 1 if down else 0, 0, keysym))


def press(sock, keysym, hold=0.03):
    send_key(sock, keysym, True)
    time.sleep(hold)
    send_key(sock, keysym, False)
    time.sleep(0.04)


# ---- 键盘映射（x0vncserver 的经典坑，AI1 #271 指出）--------------------------
# 只发 `KeyEvent(keysym=ord(ch))` 对**需要 Shift 的字符**是错的：RFB 服务端把 keysym
# 翻成 keycode 时不会自动补 Shift，于是 'A' 变成 'a'、'_' 变成 '-' —— 密码就会被静默打错。
# 正确做法：把字符翻成 (基础 keysym, 是否需要 Shift)，需要时显式按住 Shift_L。
SHIFT_KEYSYM = 0xFFE1
_US_SHIFT = {
    "~": "`", "!": "1", "@": "2", "#": "3", "$": "4", "%": "5", "^": "6",
    "&": "7", "*": "8", "(": "9", ")": "0", "_": "-", "+": "=",
    "{": "[", "}": "]", "|": "\\", ":": ";", '"': "'", "<": ",", ">": ".", "?": "/",
}


def char_plan(ch):
    """返回 (keysym, need_shift)。ASCII 之外的字符按原码点直发（多数布局可映射）。"""
    if "A" <= ch <= "Z":
        return ord(ch.lower()), True
    if ch in _US_SHIFT:
        return ord(_US_SHIFT[ch]), True
    return ord(ch), False


def press_shifted(sock, keysym, need_shift, hold=0.03):
    if need_shift:
        send_key(sock, SHIFT_KEYSYM, True)
        time.sleep(0.005)
    send_key(sock, keysym, True)
    time.sleep(hold)
    send_key(sock, keysym, False)
    if need_shift:
        time.sleep(0.005)
        send_key(sock, SHIFT_KEYSYM, False)
    time.sleep(0.04)


def type_text(sock, text):
    for ch in text:
        keysym, need_shift = char_plan(ch)
        press_shifted(sock, keysym, need_shift)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5901)
    ap.add_argument("--password-file", default=DEFAULT_VNC_PW)
    ap.add_argument("action", choices=["click", "move", "drag", "type", "key", "keyname"])
    ap.add_argument("args", nargs="*")
    a = ap.parse_args()

    sock = connect(a.host, a.port, a.password_file)
    try:
        if a.action == "click":
            x, y = int(a.args[0]), int(a.args[1])
            click(sock, x, y)
            print(f"clicked ({x},{y})")
        elif a.action == "move":
            pointer(sock, int(a.args[0]), int(a.args[1]), 0)
            print("moved")
        elif a.action == "drag":
            x1, y1, x2, y2 = map(int, a.args[:4])
            pointer(sock, x1, y1, 0); time.sleep(0.05)
            pointer(sock, x1, y1, 1); time.sleep(0.1)
            steps = 12
            for i in range(1, steps + 1):
                pointer(sock, x1 + (x2 - x1) * i // steps, y1 + (y2 - y1) * i // steps, 1)
                time.sleep(0.03)
            pointer(sock, x2, y2, 0)
            print(f"dragged ({x1},{y1})->({x2},{y2})")
        elif a.action == "type":
            type_text(sock, " ".join(a.args))
            print("typed")
        elif a.action == "keyname":
            for name in a.args:
                if name not in KEYNAMES:
                    raise SystemExit(f"未知键名 {name}（可用：{', '.join(KEYNAMES)}）")
                press(sock, KEYNAMES[name])
            print("sent", " ".join(a.args))
        elif a.action == "key":
            for raw in a.args:
                press(sock, int(raw, 0))
            print("sent", " ".join(a.args))
        time.sleep(0.2)
    finally:
        sock.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
