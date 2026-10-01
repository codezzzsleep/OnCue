#!/usr/bin/env bash
# 健康检查：每一步给**可判定的证据**，而不是"启动了就算通"。
# 用法: deploy/health.sh
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=env.sh
source "$HERE/env.sh"

fail=0
ok()   { echo "  ✓ $1"; }
bad()  { echo "  ✗ $1"; fail=1; }

echo "== 1. X 与认证 =="
if xdpyinfo >/dev/null 2>&1; then
  ok "带 XAUTHORITY 可打开 $ONCUE_DISPLAY"
  # 注意：不要写 `xdpyinfo | grep -q`。在 `set -o pipefail` 下，grep 命中即退出会让
  # xdpyinfo 收到 SIGPIPE、以 141 结束，于是整条管道被判为失败——GLX 会被误报缺失。
  # 先取全文再用 case 匹配，不经过管道。
  xinfo="$(xdpyinfo 2>&1 || true)"
  case "$xinfo" in
    *GLX*)    ok "GLX 扩展存在" ;;
    *)        bad "GLX 缺失（软件渲染可能失败）" ;;
  esac
  # 反向验证：不提供认证必须被拒
  if DISPLAY="$ONCUE_DISPLAY" XAUTHORITY=/nonexistent xdpyinfo >/dev/null 2>&1; then
    bad "不带认证也能打开显示：X 认证未生效"
  else
    ok "不带认证被拒（X 认证确实生效）"
  fi
else
  bad "无法打开 $ONCUE_DISPLAY"
fi

echo "== 2. 宿主进程 =="
if pgrep -f "$OCTOSENSE_BIN" >/dev/null 2>&1; then
  ok "宿主在运行 (pid $(pgrep -f "$OCTOSENSE_BIN" | head -1))"
  if grep -q 'modules linked' "$ONCUE_LOG_DIR/octosense.log" 2>/dev/null; then
    ok "日志含 modules linked: $(grep -m1 'modules linked' "$ONCUE_LOG_DIR/octosense.log" | sed 's/.*modules linked: //')"
  else
    bad "日志没有 modules linked 行"
  fi
  if grep -q 'wm: launched' "$ONCUE_LOG_DIR/octosense.log" 2>/dev/null; then
    ok "有窗口启动记录: $(grep -m1 'wm: launched' "$ONCUE_LOG_DIR/octosense.log" | sed 's/.*- //')"
  else
    echo "  · 尚无 wm: launched 记录（可能还没启动应用）"
  fi
else
  bad "宿主未运行"
fi

echo "== 3. VNC / noVNC =="
if ss -ltn 2>/dev/null | grep -q "127.0.0.1:$ONCUE_VNC_PORT"; then
  ok "x0vncserver 监听 127.0.0.1:$ONCUE_VNC_PORT"
else
  bad "VNC 端口未监听"
fi
if ss -ltn 2>/dev/null | grep -q "127.0.0.1:$ONCUE_NOVNC_PORT"; then
  code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 8 "http://127.0.0.1:$ONCUE_NOVNC_PORT/vnc.html" || echo 000)
  [ "$code" = "200" ] && ok "noVNC /vnc.html → 200" || bad "noVNC /vnc.html → $code"
else
  bad "noVNC 端口未监听"
fi

echo "== 4. 资源（cgroup v1）=="
u=$(cat /sys/fs/cgroup/memory/memory.usage_in_bytes 2>/dev/null || echo 0)
l=$(cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null || echo 0)
f=$(cat /sys/fs/cgroup/memory/memory.failcnt 2>/dev/null || echo '?')
awk -v u="$u" -v l="$l" -v f="$f" 'BEGIN{printf "  usage=%.2f GiB / limit=%.2f GiB (%.1f%%), failcnt=%s\n", u/2^30, l/2^30, (l?u*100/l:0), f}'

echo
[ "$fail" = 0 ] && echo "健康检查：全部通过" || echo "健康检查：有失败项（见上）"
exit "$fail"
