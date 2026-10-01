#!/usr/bin/env bash
# 健康检查：每步给**可判定的证据**，而不是"启动了就算通"。
#
# 两个"假绿"陷阱（AI1 评审 #256 指出，已修）：
#   1) `pgrep -f <BIN>` 会命中**包装调用者自己的命令行**（关键字出现在包装脚本里）；
#   2) 只看日志里有没有 `wm: launched`，会把**上一次运行留下的日志**当成这次的成功。
# 现在：进程用 env.sh 的 `verify` 复核身份；日志要求 mtime 不早于本次启动时刻，
# 并且**本次启动动作预期的窗口记录必须出现**，否则不算全绿。
#
# 用法: deploy/health.sh
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=env.sh
source "$HERE/env.sh"

fail=0
ok()  { echo "  ✓ $1"; }
bad() { echo "  ✗ $1"; fail=1; }

echo "== 1. X 与认证 =="
if xdpyinfo >/dev/null 2>&1; then
  ok "带 XAUTHORITY 可打开 $ONCUE_DISPLAY"
  # 不要写 `xdpyinfo | grep -q`：`set -o pipefail` 下 grep 命中即退出会让 xdpyinfo
  # 收到 SIGPIPE 以 141 结束，整条管道被判失败 → GLX 会被误报缺失。先取全文再 case 匹配。
  xinfo="$(xdpyinfo 2>&1 || true)"
  case "$xinfo" in *GLX*) ok "GLX 扩展存在" ;; *) bad "GLX 缺失（软件渲染可能失败）" ;; esac
  if DISPLAY="$ONCUE_DISPLAY" XAUTHORITY=/nonexistent xdpyinfo >/dev/null 2>&1; then
    bad "不带认证也能打开显示：X 认证未生效"
  else
    ok "不带认证被拒（X 认证确实生效）"
  fi
else
  bad "无法打开 $ONCUE_DISPLAY"
fi
if verify xvfb; then ok "Xvfb 身份复核通过 (pid $(run_pid xvfb))"; else bad "Xvfb 身份复核不通过（本 runtime 记录与当前进程不符）"; fi

echo "== 2. 宿主进程与本次启动日志 =="
if verify octosense; then
  hpid="$(run_pid octosense)"
  ok "宿主身份复核通过 (pid $hpid)"
  LOG="$ONCUE_LOG_DIR/octosense.log"
  started_at="$(sed -n 5p "$ONCUE_STATE_DIR/octosense.run" 2>/dev/null)"
  if [ -f "$LOG" ]; then
    mtime="$(stat -c %Y "$LOG" 2>/dev/null || echo 0)"
    if [ -n "${started_at:-}" ] && [ "$mtime" -ge "$started_at" ]; then
      ok "日志 mtime($mtime) ≥ 本次启动时刻($started_at)：内容属于本次运行"
      if grep -q 'modules linked' "$LOG" 2>/dev/null; then
        ok "modules linked: $(grep -m1 'modules linked' "$LOG" | sed 's/.*modules linked: //')"
      else
        bad "本次日志没有 modules linked 行"
      fi
      # 启动动作预期的窗口记录：本次 launch 动作必须真的产出窗口，否则不算全绿
      if [ -n "${ONCUE_LAUNCH_ACTION:-}" ]; then
        if grep -q "wm: launched" "$LOG" 2>/dev/null; then
          ok "本次窗口记录: $(grep -m1 'wm: launched' "$LOG" | sed 's/.*- //')"
        else
          bad "本次启动动作 '$ONCUE_LAUNCH_ACTION' 没有产生 wm: launched —— 应用没起来，不能算全绿"
        fi
      fi
    else
      bad "日志比本次启动还旧（mtime=$mtime < started_at=${started_at:-?}）：可能读到了上一次运行的日志"
    fi
  else
    bad "找不到宿主日志 $LOG"
  fi
else
  bad "宿主身份复核不通过（pid 记录与当前进程不符，或进程已退出）"
fi

echo "== 3. VNC / noVNC =="
if verify x0vnc; then ok "x0vncserver 身份复核通过 (pid $(run_pid x0vnc))"; else bad "x0vncserver 身份复核不通过"; fi
if ss -ltn 2>/dev/null | grep -q "127.0.0.1:$ONCUE_VNC_PORT"; then ok "VNC 端口 $ONCUE_VNC_PORT 在监听"; else bad "VNC 端口未监听"; fi
if verify websockify || ss -ltn 2>/dev/null | grep -q "127.0.0.1:$ONCUE_NOVNC_PORT"; then
  code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 8 "http://127.0.0.1:$ONCUE_NOVNC_PORT/vnc.html" || echo 000)
  [ "$code" = "200" ] && ok "noVNC /vnc.html → 200" || bad "noVNC /vnc.html → $code"
else
  bad "noVNC 未运行"
fi

echo "== 4. 资源（cgroup v1）=="
u=$(cat /sys/fs/cgroup/memory/memory.usage_in_bytes 2>/dev/null || echo 0)
l=$(cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null || echo 0)
f=$(cat /sys/fs/cgroup/memory/memory.failcnt 2>/dev/null || echo '?')
awk -v u="$u" -v l="$l" -v f="$f" 'BEGIN{printf "  usage=%.2f GiB / limit=%.2f GiB (%.1f%%), failcnt=%s\n", u/2^30, l/2^30, (l?u*100/l:0), f}'

echo
[ "$fail" = 0 ] && echo "健康检查：全部通过" || echo "健康检查：有失败项（见上）"
exit "$fail"
