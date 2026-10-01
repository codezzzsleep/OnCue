#!/usr/bin/env python3
"""XTest 指针注入（libX11 + libXtst）—— 用于**任意 display**。

为什么需要它：`rfb_input.py` 是 RFB/VNC 客户端，只能驱动 **x0vncserver 服务的那个 display**
（本机是 `:99`）。`card-host` 在 `:97`/`:98` 这类**没有 VNC** 的 display 上渲染时，
必须直接用 XTest 把指针事件送进那个 X server。

用法（调用方须显式设置正确的 DISPLAY/XAUTHORITY）:
  python3 xclick.py click X Y            # 移动 + 按下 + 抬起（左键）
  python3 xclick.py move X Y
  python3 xclick.py press X Y [button]   # button: 1=左 2=中 3=右
"""
import ctypes
import ctypes.util
import sys
import time


def load():
    x11 = ctypes.CDLL(ctypes.util.find_library("X11") or "libX11.so.6")
    xtst = ctypes.CDLL(ctypes.util.find_library("Xtst") or "libXtst.so.6")
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XFlush.argtypes = [ctypes.c_void_p]
    x11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
    xtst.XTestFakeMotionEvent.restype = ctypes.c_int
    xtst.XTestFakeMotionEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]
    xtst.XTestFakeButtonEvent.restype = ctypes.c_int
    xtst.XTestFakeButtonEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
    return x11, xtst


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    what = sys.argv[1]
    expected = {"move": (4, 4), "click": (4, 4), "press": (4, 5)}
    if what not in expected or not expected[what][0] <= len(sys.argv) <= expected[what][1]:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        x, y = int(sys.argv[2]), int(sys.argv[3])
        btn = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    except ValueError:
        print("X、Y 和 button 必须是整数", file=sys.stderr)
        return 2
    if x < 0 or y < 0 or not 1 <= btn <= 5:
        print("X/Y 必须非负，button 必须在 1..5", file=sys.stderr)
        return 2
    x11, xtst = load()
    dpy = x11.XOpenDisplay(None)
    if not dpy:
        print("XOpenDisplay 失败（DISPLAY/XAUTHORITY 对吗？）", file=sys.stderr)
        return 1

    def motion(x, y):
        if not xtst.XTestFakeMotionEvent(dpy, -1, x, y, 0):   # -1 = 当前 screen
            raise RuntimeError("XTestFakeMotionEvent 失败")
        x11.XFlush(dpy)
        time.sleep(0.08)

    if what == "move":
        motion(x, y)
        print(f"moved ({x},{y})")
    elif what == "click":
        motion(x, y)
        if not xtst.XTestFakeButtonEvent(dpy, 1, 1, 0):
            raise RuntimeError("XTest 左键按下失败")
        x11.XFlush(dpy)
        time.sleep(0.06)
        if not xtst.XTestFakeButtonEvent(dpy, 1, 0, 0):
            raise RuntimeError("XTest 左键抬起失败")
        x11.XFlush(dpy)
        print(f"clicked ({x},{y}) via XTest")
    elif what == "press":
        motion(x, y)
        if not xtst.XTestFakeButtonEvent(dpy, btn, 1, 0):
            raise RuntimeError(f"XTest button {btn} 按下失败")
        x11.XFlush(dpy)
        time.sleep(0.06)
        if not xtst.XTestFakeButtonEvent(dpy, btn, 0, 0):
            raise RuntimeError(f"XTest button {btn} 抬起失败")
        x11.XFlush(dpy)
        print(f"pressed ({x},{y}) button={btn} via XTest")
    x11.XSync(dpy, 0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
