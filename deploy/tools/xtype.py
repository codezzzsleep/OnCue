#!/usr/bin/env python3
"""可靠的 X 键盘注入：直接用 libX11 + libXtst，按**服务器自己的键映射**算 keycode 与 Shift 层。

为什么不用 RFB 键事件：x0vncserver 把 RFB keysym 翻成 keycode 时**不补修饰键**，
实测输入 `A_z9!@#-_` 得到 `az9-rg`（大写与符号全错）。而密码里一旦有这类字符，
就会被静默打错 → 服务端回 403。

算法（与 xdotool 同思路）：
  keysym = XStringToKeysym(字符)
  keycode = XKeysymToKeycode(display, keysym)
  用 XkbKeycodeToKeysym(kc, group=0, level) 找到 keysym 落在哪一层
  level 1 → 按下 Shift_L；然后 XTestFakeKeyEvent 按下/抬起
因此不依赖 US 布局假设，也不依赖 RFB 的映射实现。

用法: xtype.py <text>      # 用法同 rfb_input.py type，但只做键盘
"""
import ctypes
import ctypes.util
import sys
import time

XK_SHIFT_L = 0xFFE1


def load():
    x11_name = ctypes.util.find_library("X11") or "libX11.so.6"
    xtst_name = ctypes.util.find_library("Xtst") or "libXtst.so.6"
    x11 = ctypes.CDLL(x11_name)
    xtst = ctypes.CDLL(xtst_name)

    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XStringToKeysym.restype = ctypes.c_ulong
    x11.XStringToKeysym.argtypes = [ctypes.c_char_p]
    x11.XKeysymToKeycode.restype = ctypes.c_ubyte
    x11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    x11.XkbKeycodeToKeysym.restype = ctypes.c_ulong
    x11.XkbKeycodeToKeysym.argtypes = [ctypes.c_void_p, ctypes.c_ubyte, ctypes.c_int, ctypes.c_int]
    x11.XFlush.argtypes = [ctypes.c_void_p]
    xtst.XTestFakeKeyEvent.restype = ctypes.c_int
    xtst.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
    return x11, xtst


def plan(x11, dpy, ch):
    """返回 (keycode, level) 或 None。

    注意：`XStringToKeysym` 要的是**键名**（"underscore"、"exclam"），不是字符本身，
    所以 `XStringToKeysym("_")` 返回 0。X11 的约定是 `0x20..0x7e` 的可打印 ASCII
    **其 keysym 值就等于字符码**，因此这里直接取 `ord(ch)`。
    """
    code = ord(ch)
    keysym = code if 0x20 <= code <= 0x7E else x11.XStringToKeysym(ch.encode("utf-8"))
    if keysym == 0:
        return None
    kc = x11.XKeysymToKeycode(dpy, keysym)
    if kc == 0:
        return None
    for level in range(4):
        if x11.XkbKeycodeToKeysym(dpy, kc, 0, level) == keysym:
            return kc, level
    return kc, 0


def tap(xtst, dpy, keycode, delay=8):
    xtst.XTestFakeKeyEvent(dpy, keycode, 1, delay)
    xtst.XTestFakeKeyEvent(dpy, keycode, 0, delay)


def main():
    if len(sys.argv) < 2:
        print("usage: xtype.py <text>", file=sys.stderr)
        return 2
    text = sys.argv[1]
    x11, xtst = load()
    dpy = x11.XOpenDisplay(None)
    if not dpy:
        print("XOpenDisplay 失败（DISPLAY/XAUTHORITY 对吗？）", file=sys.stderr)
        return 1
    shift_kc = x11.XKeysymToKeycode(dpy, XK_SHIFT_L)

    sent = 0
    skipped = []
    for ch in text:
        p = plan(x11, dpy, ch)
        if p is None:
            skipped.append(ch)
            continue
        kc, level = p
        need_shift = level == 1
        if need_shift:
            xtst.XTestFakeKeyEvent(dpy, shift_kc, 1, 6)
        tap(xtst, dpy, kc)
        if need_shift:
            xtst.XTestFakeKeyEvent(dpy, shift_kc, 0, 6)
        x11.XFlush(dpy)
        time.sleep(0.03)
        sent += 1
    x11.XFlush(dpy)
    print(f"typed {sent} 字符；无法映射 {len(skipped)} 个")
    if skipped:
        # 只报字符类别，避免把内容写进日志
        print(f"  无法映射的字符: {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
