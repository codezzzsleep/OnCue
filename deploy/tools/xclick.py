#!/usr/bin/env python3
"""XTest 指针注入（libX11 + libXtst）—— 用于**任意 display**。

为什么需要它：`rfb_input.py` 是 RFB/VNC 客户端，只能驱动 **x0vncserver 服务的那个 display**
（本机是 `:99`）。`card-host` 在 `:97`/`:98` 这类**没有 VNC** 的 display 上渲染时，
必须直接用 XTest 把指针事件送进那个 X server。

用法:
  xclick.py click X Y            # 移动 + 按下 + 抬起（左键）
  xclick.py move X Y
  xclick.py press X Y [button]   # button: 1=左 2=中 3=右
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
    x11, xtst = load()
    dpy = x11.XOpenDisplay(None)
    if not dpy:
        print("XOpenDisplay 失败（DISPLAY/XAUTHORITY 对吗？）", file=sys.stderr)
        return 1

    def motion(x, y):
        xtst.XTestFakeMotionEvent(dpy, -1, x, y, 0)   # -1 = 当前 screen
        x11.XFlush(dpy)
        time.sleep(0.08)

    if what == "move":
        motion(int(sys.argv[2]), int(sys.argv[3]))
        print(f"moved ({sys.argv[2]},{sys.argv[3]})")
    elif what == "click":
        x, y = int(sys.argv[2]), int(sys.argv[3])
        motion(x, y)
        xtst.XTestFakeButtonEvent(dpy, 1, 1, 0)
        x11.XFlush(dpy)
        time.sleep(0.06)
        xtst.XTestFakeButtonEvent(dpy, 1, 0, 0)
        x11.XFlush(dpy)
        print(f"clicked ({x},{y}) via XTest")
    elif what == "press":
        x, y = int(sys.argv[2]), int(sys.argv[3])
        btn = int(sys.argv[4]) if len(sys.argv) > 4 else 1
        motion(x, y)
        xtst.XTestFakeButtonEvent(dpy, btn, 1, 0)
        x11.XFlush(dpy)
        time.sleep(0.06)
        xtst.XTestFakeButtonEvent(dpy, btn, 0, 0)
        x11.XFlush(dpy)
        print(f"pressed ({x},{y}) button={btn} via XTest")
    else:
        print(f"未知动作 {what}", file=sys.stderr)
        return 2
    x11.XSync(dpy, 0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
