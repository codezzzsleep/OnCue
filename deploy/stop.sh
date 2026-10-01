#!/usr/bin/env bash
# 停止 OnCue 运行链：**只按 start.sh 记录的 PID**，不用宽泛 `pkill -f`
# （旧容器曾因过宽清理误杀无关 card-host 进程）。
#
# 用法: deploy/stop.sh [--keep-x]
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=env.sh
source "$HERE/env.sh"

KEEP_X=0
[ "${1:-}" = "--keep-x" ] && KEEP_X=1

stop_one() {
  local name="$1" file="$ONCUE_STATE_DIR/$1.pid"
  [ -f "$file" ] || { echo "  · $name 无 PID 记录，跳过"; return 0; }
  local pid
  pid="$(cat "$file" 2>/dev/null || true)"
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    kill -TERM "$pid" 2>/dev/null || true
    for _ in $(seq 1 20); do kill -0 "$pid" 2>/dev/null || break; sleep 0.5; done
    if kill -0 "$pid" 2>/dev/null; then
      echo "  ! $name (pid $pid) 未在 10s 内退出，发送 KILL"
      kill -KILL "$pid" 2>/dev/null || true
    else
      echo "  ✓ $name (pid $pid) 已停止"
    fi
  else
    echo "  · $name (pid ${pid:-?}) 已不在运行"
  fi
  rm -f "$file"
}

echo "停止顺序（依赖反序）：noVNC → VNC → 宿主 → Xvfb"
stop_one websockify
stop_one x0vnc
stop_one octosense
[ "$KEEP_X" = 1 ] || stop_one xvfb
echo "完成。"
