#!/usr/bin/env bash
# 启动 OnCue 的宿主运行链（无密钥）：
#   Xvfb :99 (带 X 认证) → llvmpipe → OctoSense(含 Rinx/card 模块) → x0vncserver → websockify/noVNC
#
# 用法: deploy/start.sh [--no-vnc] [--launch <test-action>]
#
# 进程判定的四个坑（全部实测踩过，已修）：
#   1) `pgrep -f "<关键字>.*<端口>"` 会命中**调用者自己的命令行** → 改用端口探测/精确进程名。
#   2) `pgrep -x <名字>` 只说明"有同名进程"：同机可能有**另一个 display 的同类进程**，
#      直接 adopt 会误接管别人的进程（AI1 评审 #256）→ 只接受 DISPLAY/exe/端口都匹配的，
#      不匹配就报错退出，既不接管也不杀。
#   3) `setsid cmd &` 的 `$!` 常是 **setsid/nohup 包装进程**的 PID，不是真守护进程
#      （实测 xvfb.run 记成 /usr/bin/setsid、x0vnc.run 记成 /usr/bin/nohup）
#      → 启动后按身份特征轮询到真进程再记录（env.sh 的 launch_and_record）。
#   4) 身份记录含 starttime，避免旧 PID 被复用后误杀（见 stop.sh）。
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

port_up() { ss -ltn 2>/dev/null | grep -q "$1"; }

# find_first <exe_name> <matcher>：打印第一个满足 matcher 的 pid
find_first() {
  local name="$1" matcher="$2" pid
  for pid in $(pgrep -x "$name" 2>/dev/null || true); do
    if "$matcher" "$pid"; then echo "$pid"; return 0; fi
  done
  return 1
}
m_xvfb()  { proc_cmdline "$1" | grep -q -- "Xvfb $ONCUE_DISPLAY "; }
# m_host：**防假绿**的身份校验。只比 exe+DISPLAY 是不够的——
# 迁移到 /srv 时，若旧 /tmp（或旧 /root）起来的同一个二进制还在跑，
# ensure 会把它当成"已经在跑"而复用，于是"重启通过"其实从未迁移。
# 所以这里同时核对 cwd 与三个作用域变量（都只是路径，不含秘密）。
m_host() {
  [ "$(proc_exe "$1")" = "$(readlink -f "$OCTOSENSE_BIN")" ] || return 1
  proc_has_display "$1" || return 1
  [ "$(proc_cwd "$1")" = "$ONCUE_HOST_CWD" ] || return 1
  proc_environ_has "$1" "HOME=$ONCUE_HOST_HOME" || return 1
  proc_environ_has "$1" "RINX_DATA_DIR=$ONCUE_RINX_DATA_DIR" || return 1
  proc_environ_has "$1" "OCTOS_APP_CORE_DIR=$OCTOS_APP_CORE_DIR" || return 1
  return 0
}
m_x0vnc() { proc_cmdline "$1" | grep -q -- "-display $ONCUE_DISPLAY" && proc_cmdline "$1" | grep -q -- "-rfbport $ONCUE_VNC_PORT"; }
m_novnc() { proc_cmdline "$1" | grep -q -- "$ONCUE_NOVNC_PORT"; }

# ensure <name> <exe_name> <matcher> <start-fn> [want_display] [extra]
ensure() {
  local name="$1" exe_name="$2" matcher="$3" start_fn="$4" want="${5:-}" extra="${6:-}" pid
  if verify "$name"; then
    echo "  · $name 已由本 runtime 启动 (pid $(run_pid "$name"))"
    return 0
  fi
  if pid="$(find_first "$exe_name" "$matcher")"; then
    echo "  · 复用并核验同一 runtime 的 $name (pid $pid)"
    record "$name" "$pid" "$(proc_exe "$pid")" "$want" "$extra"
    return 0
  fi
  if pgrep -x "$exe_name" >/dev/null 2>&1; then
    echo "  ! 存在同名但特征不符的 $exe_name（可能是另一个 display / 另一个实例）："
    pgrep -ax "$exe_name" | sed 's/^/      /' || true
    echo "      → 不接管、不停它；本次 runtime 启动自己的实例。"
  fi
  # 只有真正的资源冲突才拒绝：端口被别的进程占着就没法启动
  local need_port=""
  [ "$name" = "x0vnc" ] && need_port="$ONCUE_VNC_PORT"
  [ "$name" = "websockify" ] && need_port="$ONCUE_NOVNC_PORT"
  if [ -n "$need_port" ] && ss -ltn 2>/dev/null | grep -q "127.0.0.1:$need_port"; then
    echo "  ✗ 端口 $need_port 已被占用，且持有者不是本 runtime 的进程；拒绝启动。" >&2
    exit 3
  fi
  "$start_fn"
}

# ---- 1) Xvfb（真实 X 认证）----------------------------------------------------
if [ ! -f "$ONCUE_XAUTHORITY" ]; then
  umask 077
  touch "$ONCUE_XAUTHORITY"; chmod 600 "$ONCUE_XAUTHORITY"
  xauth -f "$ONCUE_XAUTHORITY" add "${ONCUE_DISPLAY#:}" MIT-MAGIC-COOKIE-1 "$(openssl rand -hex 16)"
fi
xvfb_start() {
  launch_and_record xvfb Xvfb m_xvfb "$(readlink -f "$(command -v Xvfb)")" "" "-auth $ONCUE_XAUTHORITY" -- \
    Xvfb "$ONCUE_DISPLAY" -screen 0 "$ONCUE_SCREEN" \
    +extension GLX +extension RENDER -noreset -auth "$ONCUE_XAUTHORITY"
}
ensure xvfb Xvfb m_xvfb xvfb_start "" "-auth $ONCUE_XAUTHORITY"
xdpyinfo >/dev/null 2>&1 || { echo "X 认证失败：xdpyinfo 打不开 $ONCUE_DISPLAY" >&2; exit 1; }

# ---- 2) 宿主（含 Rinx 与 card 模块）------------------------------------------
[ -x "$OCTOSENSE_BIN" ] || { echo "宿主二进制不存在：$OCTOSENSE_BIN（见 deploy/DEPENDENCIES.md）" >&2; exit 1; }
if [ -z "$OCTOSENSE_HUB" ] || [ -z "$OCTOSENSE_HUB_ANCHOR" ]; then
  echo "  ! 提示：OCTOSENSE_HUB / OCTOSENSE_HUB_ANCHOR 有一个为空。" >&2
  echo "    若应用来自本地演练镜像，必须两个都设置（见 deploy/DEPENDENCIES.md §5）。" >&2
fi
host_start() {
  # 三个作用域变量**只在这一条命令上生效**（cd + env 只影响宿主进程）：
  #   · 不改本脚本所在 shell 的 HOME，也不 export，故不污染 cargo/git
  #   · `env` 直接 exec 宿主二进制，所以 /proc/<pid>/exe 仍等于 OCTOSENSE_BIN，
  #     m_host 的身份复核（exe + display）照旧成立
  mkdir -p "$ONCUE_HOST_HOME" "$ONCUE_RINX_DATA_DIR" "$ONCUE_HOST_CWD" 2>/dev/null || true
  chmod 700 "$ONCUE_HOST_HOME" "$ONCUE_RINX_DATA_DIR" "$ONCUE_HOST_CWD" 2>/dev/null || true
  launch_and_record octosense octosense m_host "$(readlink -f "$OCTOSENSE_BIN")" yes "" -- \
    bash -c 'cd "$1" && exec env HOME="$2" RINX_DATA_DIR="$3" "$4" --module rinx --test-action "$5"' _ \
      "$ONCUE_HOST_CWD" "$ONCUE_HOST_HOME" "$ONCUE_RINX_DATA_DIR" "$OCTOSENSE_BIN" "$LAUNCH"
}
ensure octosense octosense m_host host_start yes ""

# ---- 3) VNC + noVNC ----------------------------------------------------------
if [ "$WITH_VNC" = 1 ]; then
  [ -f "$ONCUE_VNC_PASSWD" ] || { echo "缺少 VNC 密码文件：$ONCUE_VNC_PASSWD（600，仓库外）" >&2; exit 1; }
  x0_start() {
    launch_and_record x0vnc x0vncserver m_x0vnc "$(readlink -f "$(command -v x0vncserver)")" "" "-rfbport $ONCUE_VNC_PORT" -- \
      x0vncserver -display "$ONCUE_DISPLAY" -rfbport "$ONCUE_VNC_PORT" \
      -interface 127.0.0.1 -PasswordFile "$ONCUE_VNC_PASSWD" \
      -SecurityTypes VncAuth -AlwaysShared -localhost
  }
  ensure x0vnc x0vncserver m_x0vnc x0_start "" "-rfbport $ONCUE_VNC_PORT"

  # noVNC 同样走 ensure：能识别就纳入身份管理（否则 stop 停不掉它，
  # health 也会被一个"不属于本 runtime"的监听端口给出假绿）。
  m_novnc() { proc_cmdline "$1" | grep -q -- "$ONCUE_NOVNC_PORT" && proc_cmdline "$1" | grep -q -- "$ONCUE_VNC_PORT"; }
  novnc_start() {
    launch_and_record websockify python3 m_novnc "$(readlink -f "$(command -v python3)")" "" "$ONCUE_NOVNC_PORT" -- \
      python3 -m websockify --web "$ONCUE_NOVNC_WEB" \
      "127.0.0.1:$ONCUE_NOVNC_PORT" "127.0.0.1:$ONCUE_VNC_PORT"
  }
  ensure websockify python3 m_novnc novnc_start "" "$ONCUE_NOVNC_PORT"
fi

echo "启动完成。健康检查: deploy/health.sh"
