#!/usr/bin/env bash
# 停止 OnCue 运行链：**只停止本 runtime 记录在案、且身份复核通过的进程**。
#
# 为什么不直接 kill：
#   · 旧 PID 会被系统复用，`kill -0 <pid>` 通过并不代表那是我们的进程；
#   · 同机可能有另一个 display 的同名进程（另一个 card-host / 另一个 OctoSense）。
# 所以停止前用 env.sh 的 `verify` 复核 (pid, starttime, exe, display) 四项；
# 任何一项对不上就**拒绝停止**并报出来，交给人工判断。
#
# 用法: deploy/stop.sh [--keep-x]
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=env.sh
source "$HERE/env.sh"

KEEP_X=0
[ "${1:-}" = "--keep-x" ] && KEEP_X=1

stop_one() {
  local name="$1" pid
  if [ ! -f "$ONCUE_STATE_DIR/$name.run" ]; then
    echo "  · $name 无身份记录，跳过（本 runtime 没启动过它）"
    return 0
  fi
  pid="$(run_pid "$name")"
  if ! verify "$name"; then
    echo "  ✗ $name 身份复核不通过（pid $pid 的身份/display/exe 与记录不符，可能已被复用或已被换掉）"
    echo "    → **拒绝停止**，不动这个进程；如确认无碍请手工处理，然后删除 $ONCUE_STATE_DIR/$name.run"
    return 1   # 让调用方知道"这一环没停成"（宿主没停成时要保留 Xvfb）
  fi
  kill -TERM "$pid" 2>/dev/null || true
  for _ in $(seq 1 20); do kill -0 "$pid" 2>/dev/null || break; sleep 0.5; done
  if kill -0 "$pid" 2>/dev/null; then
    echo "  ! $name (pid $pid) 未在 10s 内退出，发送 KILL"
    kill -KILL "$pid" 2>/dev/null || true
  else
    echo "  ✓ $name (pid $pid) 已停止（身份复核通过后停止）"
  fi
  forget "$name"
}

echo "停止顺序（依赖反序）：noVNC → VNC → 宿主 → Xvfb"
stop_one websockify
stop_one x0vnc
HOST_REFUSED=0
stop_one octosense || HOST_REFUSED=1
if [ "$KEEP_X" = 1 ]; then
  :
elif [ "$HOST_REFUSED" = 1 ]; then
  # 关键：Xvfb 一停，连在它上面的 X 客户端会跟着退出——那样"拒绝停止宿主"就形同虚设。
  # 所以只要宿主这一环没停成，就**保留 Xvfb**，把判断权交回给人。
  echo "  · 宿主未被停止 → **保留 Xvfb**（停掉它会把宿主的 X 连接一起带走，等于变相误杀）"
  echo "    确认两件事后再收尾：处理该宿主进程，然后手工停掉 Xvfb（或再跑一次 stop.sh）。"
else
  stop_one xvfb
fi
echo "完成。"
