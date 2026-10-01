# 无密钥环境变量（deploy/env.sh）
#
# 这个文件**不含任何密钥**：凭据、VNC 密码、hub 演练私钥都在仓库外的私有目录。
# 用 `source deploy/env.sh` 载入；所有路径都可以用同名环境变量覆盖。

# ---- 运行目录（仓库外，含私有 state）----------------------------------------
: "${ONCUE_RUNTIME_ROOT:=/root/oncue-runtime}"
: "${ONCUE_STATE_DIR:=$ONCUE_RUNTIME_ROOT/state}"
: "${ONCUE_LOG_DIR:=$ONCUE_RUNTIME_ROOT/logs}"

# ---- 宿主二进制 --------------------------------------------------------------
# 由固定源码 OctoSense 6c4746f0854b74446f854fdcd32eeb87b5192a81 构建：
#   CARGO_BUILD_JOBS=2 cargo build --release --locked -p octosense
: "${OCTOSENSE_SRC:=/opt/src/OctoSense}"
: "${OCTOSENSE_BIN:=$OCTOSENSE_SRC/target/release/octosense}"

# ---- X / 渲染 ----------------------------------------------------------------
: "${ONCUE_DISPLAY:=:99}"
: "${ONCUE_SCREEN:=1440x1000x24}"
# 容器内无 GPU：强制 Mesa 软件渲染（llvmpipe）
: "${LIBGL_ALWAYS_SOFTWARE:=1}"
: "${GALLIUM_DRIVER:=llvmpipe}"
: "${ONCUE_XAUTHORITY:=$ONCUE_STATE_DIR/xauthority}"
export LIBGL_ALWAYS_SOFTWARE GALLIUM_DRIVER
export DISPLAY="$ONCUE_DISPLAY"
export XAUTHORITY="$ONCUE_XAUTHORITY"

# ---- VNC / noVNC -------------------------------------------------------------
: "${ONCUE_VNC_PORT:=5901}"
: "${ONCUE_NOVNC_PORT:=6080}"
: "${ONCUE_NOVNC_WEB:=/opt/novnc}"
# 私有 VNC 密码文件（600，仓库外；内容绝不进仓库/日志）
: "${ONCUE_VNC_PASSWD:=$ONCUE_STATE_DIR/vnc/vnc-passwd}"

# ---- App Hub 本地演练镜像（可选）---------------------------------------------
# OCTOSENSE_HUB 为目录时表示本地镜像（<dir>/catalog.json + <dir>/artifacts/…）。
# OCTOSENSE_HUB_ANCHOR 是**公钥**，不是密钥。
: "${OCTOSENSE_HUB:=}"
: "${OCTOSENSE_HUB_ANCHOR:=}"
: "${ONCUE_LAUNCH_ACTION:=launch-hub:oncue-screening-room}"
export OCTOSENSE_HUB OCTOSENSE_HUB_ANCHOR

# ---- Rust 工具链 -------------------------------------------------------------
export PATH="$HOME/.cargo/bin:$PATH"

# ---- 进程身份校验（AI1 评审 #256）--------------------------------------------
# 只靠"同名进程"或"PID 还在"是不够的：
#   · 同一台机上可能有**另一个 display / 另一个 card-host** 的同名进程 → adopt 会误接管；
#   · 旧 PID 被系统复用 → stop 会误杀无关进程。
# 因此每个组件记录 (pid, starttime, exe, display)，停止前必须逐项复核。
# starttime 取 /proc/<pid>/stat 第 22 字段（内核 jiffies，进程一生不变）。

proc_starttime() { awk '{print $22}' "/proc/$1/stat" 2>/dev/null; }
proc_exe()       { readlink -f "/proc/$1/exe" 2>/dev/null; }
proc_cmdline()   { tr '\0' ' ' < "/proc/$1/cmdline" 2>/dev/null; }
proc_has_display() {
  [ -r "/proc/$1/environ" ] || return 1
  tr '\0' '\n' < "/proc/$1/environ" 2>/dev/null | grep -qx "DISPLAY=$ONCUE_DISPLAY"
}

# record <name> <pid> <exe> [display_required(yes|"")] [extra_match]
# 注意：必须用 ${4:-}/${5:-}，否则调用方在 `set -u` 下少传一个参数就会直接中断。
record() {
  local name="${1:-}" pid="${2:-}" exe="${3:-}" want="${4:-}" extra="${5:-}"
  [ -n "$name" ] && [ -n "$pid" ] || return 1
  printf '%s\n%s\n%s\n%s\n%s\n%s\n' \
    "$pid" "$(proc_starttime "$pid")" "$exe" "$want" "$(date +%s)" "$extra" \
    > "$ONCUE_STATE_DIR/$name.run"
}

# verify <name> → 0 表示记录里的进程**现在仍然是那一个**（pid+starttime+exe+display 全中）
verify() {
  # 注意：不能写成一条 `local name=... f="...${name}..."`——bash 在 `set -u` 下
  # 会在赋值**之前**展开所有词，于是报 `name: unbound variable`（实测复现）。
  local name="${1:-}"
  local pid st exe want extra
  local f="$ONCUE_STATE_DIR/${name}.run"
  [ -n "$name" ] || return 1
  [ -f "$f" ] || return 1
  { read -r pid; read -r st; read -r exe; read -r want; read -r _; read -r extra; } < "$f"
  [ -n "$pid" ] || return 1
  kill -0 "$pid" 2>/dev/null || return 1
  [ "$(proc_starttime "$pid")" = "$st" ] || return 1
  [ -z "$exe" ] || [ "$(proc_exe "$pid")" = "$exe" ] || return 1
  [ "$want" != "yes" ] || proc_has_display "$pid" || return 1
  [ -z "$extra" ] || proc_cmdline "$pid" | grep -q -- "$extra" || return 1
  return 0
}
run_pid()  { [ -n "${1:-}" ] && sed -n 1p "$ONCUE_STATE_DIR/$1.run" 2>/dev/null; }
forget()   { [ -n "${1:-}" ] && rm -f "$ONCUE_STATE_DIR/$1.run" "$ONCUE_STATE_DIR/$1.pid"; }

# launch_and_record <name> <exe_name> <matcher> <record_exe> <want_display|""> <extra|""> -- <cmd...>
# `setsid cmd &` 的 `$!` 常常是 **setsid/nohup 包装进程**的 PID，不是真守护进程
# （实测：xvfb.run 记成 /usr/bin/setsid、x0vnc.run 记成 /usr/bin/nohup）。
# 所以启动后按"身份特征"轮询到真正的进程，再记录它的 pid。
launch_and_record() {
  local name="${1}" exe_name="${2}" matcher="${3}" rec_exe="${4}" want="${5:-}" extra="${6:-}"
  shift 6
  setsid "$@" > "$ONCUE_LOG_DIR/$name.log" 2>&1 &
  local i pid
  for i in $(seq 1 40); do
    sleep 0.25
    if pid="$(find_first "$exe_name" "$matcher" 2>/dev/null)"; then
      record "$name" "$pid" "$rec_exe" "$want" "$extra"
      echo "  ✓ $name (pid $pid)"
      return 0
    fi
  done
  echo "  ✗ $name 启动后 10s 内未找到匹配进程（见 $ONCUE_LOG_DIR/$name.log）" >&2
  return 1
}

