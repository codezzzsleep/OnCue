#!/usr/bin/env bash
# 启动 OnCue 的宿主运行链（无密钥）：
#   Xvfb :99 (带 X 认证) → llvmpipe → OctoSense(含 Rinx/card 模块) → x0vncserver → websockify/noVNC
#
# 用法: deploy/start.sh [--no-vnc] [--launch <test-action>]
#
# 进程判定的两个坑（实测踩过，已修）：
#   1) 绝不用 `pgrep -f "<关键字>.*<端口>"`：它会把**调用者自己的命令行**也算进去
#      （包装脚本里同时出现关键字和端口），于是"看起来已在运行"而实际没启动。
#      这里改用：PID 文件 → 精确进程名 `pgrep -x` → 端口探测。
#   2) 不用宽泛 `pkill -f`；停止只在 stop.sh 里按记录的 PID 做。
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=env.sh
source "$HERE/env.sh"

mkdir -p "$ONCUE_STATE_DIR" "$ONCUE_LOG_DIR"
chmod 700 "$ONCUE_STATE_DIR"

WITH_VNC=1
LAUNCH="$ONCUE_LAUNCH_ACTION"
while [ $# -gt 0 ]; do
  case "$1" in
    --no-vnc) WITH_VNC=0; shift ;;
    --launch) LAUNCH="$2"; shift 2 ;;
    *) echo "未知参数: $1" >&2; exit 2 ;;
  esac
done

started() { echo "  ✓ $1 (pid $2)"; }
alive()   { local f="$ONCUE_STATE_DIR/$1.pid"; [ -f "$f" ] && kill -0 "$(cat "$f" 2>/dev/null)" 2>/dev/null; }
port_up() { ss -ltn 2>/dev/null | grep -q "$1"; }
adopt()   { echo "$2" > "$ONCUE_STATE_DIR/$1.pid"; }   # 纳入管理，让 stop.sh 也能停掉外部已启动的

# ---- 1) Xvfb（真实 X 认证：生成/复用 Xauthority cookie）-----------------------
if [ ! -f "$ONCUE_XAUTHORITY" ]; then
  umask 077
  touch "$ONCUE_XAUTHORITY"; chmod 600 "$ONCUE_XAUTHORITY"
  xauth -f "$ONCUE_XAUTHORITY" add "${ONCUE_DISPLAY#:}" MIT-MAGIC-COOKIE-1 "$(openssl rand -hex 16)"
fi
if alive xvfb; then
  echo "  · Xvfb 已由本脚本启动过 (pid $(cat "$ONCUE_STATE_DIR/xvfb.pid"))"
elif pgrep -x Xvfb >/dev/null 2>&1; then
  adopt xvfb "$(pgrep -x Xvfb | head -1)"
  echo "  · 复用已在运行的 Xvfb (pid $(cat "$ONCUE_STATE_DIR/xvfb.pid"))，已纳入 PID 管理"
else
  setsid nohup Xvfb "$ONCUE_DISPLAY" -screen 0 "$ONCUE_SCREEN" \
    +extension GLX +extension RENDER -noreset -auth "$ONCUE_XAUTHORITY" \
    > "$ONCUE_LOG_DIR/xvfb.log" 2>&1 &
  echo $! > "$ONCUE_STATE_DIR/xvfb.pid"
  sleep 3
  started "Xvfb $ONCUE_DISPLAY" "$(cat "$ONCUE_STATE_DIR/xvfb.pid")"
fi
xdpyinfo >/dev/null 2>&1 || { echo "X 认证失败：xdpyinfo 打不开 $ONCUE_DISPLAY" >&2; exit 1; }

# ---- 2) 宿主（含 Rinx 与 card 模块）------------------------------------------
[ -x "$OCTOSENSE_BIN" ] || { echo "宿主二进制不存在：$OCTOSENSE_BIN（见 deploy/DEPENDENCIES.md）" >&2; exit 1; }
if alive octosense; then
  echo "  · 宿主已由本脚本启动过 (pid $(cat "$ONCUE_STATE_DIR/octosense.pid"))"
elif pgrep -x octosense >/dev/null 2>&1; then
  adopt octosense "$(pgrep -x octosense | head -1)"
  echo "  · 复用已在运行的宿主 (pid $(cat "$ONCUE_STATE_DIR/octosense.pid"))"
else
  setsid nohup "$OCTOSENSE_BIN" --module rinx --test-action "$LAUNCH" \
    > "$ONCUE_LOG_DIR/octosense.log" 2>&1 &
  echo $! > "$ONCUE_STATE_DIR/octosense.pid"
  sleep 5
  started "octosense ($LAUNCH)" "$(cat "$ONCUE_STATE_DIR/octosense.pid")"
fi

# ---- 3) VNC + noVNC ----------------------------------------------------------
if [ "$WITH_VNC" = 1 ]; then
  [ -f "$ONCUE_VNC_PASSWD" ] || { echo "缺少 VNC 密码文件：$ONCUE_VNC_PASSWD（600，仓库外）" >&2; exit 1; }
  if pgrep -x x0vncserver >/dev/null 2>&1; then
    adopt x0vnc "$(pgrep -x x0vncserver | head -1)"
    echo "  · x0vncserver 已在运行 (pid $(cat "$ONCUE_STATE_DIR/x0vnc.pid"))"
  else
    setsid nohup x0vncserver -display "$ONCUE_DISPLAY" -rfbport "$ONCUE_VNC_PORT" \
      -interface 127.0.0.1 -PasswordFile "$ONCUE_VNC_PASSWD" \
      -SecurityTypes VncAuth -AlwaysShared -localhost \
      > "$ONCUE_LOG_DIR/x0vnc.log" 2>&1 &
    echo $! > "$ONCUE_STATE_DIR/x0vnc.pid"
    sleep 2
    started "x0vncserver 127.0.0.1:$ONCUE_VNC_PORT" "$(cat "$ONCUE_STATE_DIR/x0vnc.pid")"
  fi
  # 以**端口**判定，而不是 pgrep -f
  if port_up "127.0.0.1:$ONCUE_NOVNC_PORT"; then
    echo "  · noVNC 端口已在监听"
  else
    setsid nohup python3 -m websockify --web "$ONCUE_NOVNC_WEB" \
      "127.0.0.1:$ONCUE_NOVNC_PORT" "127.0.0.1:$ONCUE_VNC_PORT" \
      > "$ONCUE_LOG_DIR/websockify.log" 2>&1 &
    echo $! > "$ONCUE_STATE_DIR/websockify.pid"
    sleep 3
    started "noVNC http://127.0.0.1:$ONCUE_NOVNC_PORT/vnc.html" "$(cat "$ONCUE_STATE_DIR/websockify.pid")"
  fi
fi

echo "启动完成。健康检查: deploy/health.sh"
