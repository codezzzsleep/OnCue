# 无密钥环境变量（deploy/env.sh）
#
# 这个文件**不含任何密钥**：凭据、VNC 密码、hub 演练私钥都在仓库外的私有目录。
# 用 `source deploy/env.sh` 载入；所有路径都可以用同名环境变量覆盖。

# ---- 运行目录（仓库外，含私有 state；**持久非系统路径**）--------------------
# 为什么不是 /tmp：/tmp 只算过渡诊断，重启即失，不能作为可重启交付。
# 为什么不是 /root：octos 的 `session/open` 禁止 workspace 落在系统根
#   （禁用根清单 etc,sbin,bin,boot,dev,proc,sys,usr,var,root；见
#    octos-cli/src/api/ui_protocol_transport.rs:23267-23280）。
# /srv 两者都避开，且是持久盘。父目录 0700。
: "${ONCUE_RUNTIME_ROOT:=/srv/oncue-runtime}"
: "${ONCUE_STATE_DIR:=$ONCUE_RUNTIME_ROOT/state}"
: "${ONCUE_LOG_DIR:=$ONCUE_RUNTIME_ROOT/logs}"

# ---- 宿主进程的三个作用域变量（**只给 OctoSense 子进程**）--------------------
# 这三个**不能导出到构建/git shell**：export 会污染 cargo 的 HOME（拉错缓存）、
# 也会改掉 git 的全局配置位置。所以 env.sh 只声明它们，真正生效点是 start.sh 里
# 对宿主的一次 `cd <cwd> && env HOME=… RINX_DATA_DIR=… <bin>`。
#   ONCUE_HOST_HOME      ：宿主 HOME；octos CLI keychain 读 $HOME/.octos/secrets，
#                          OctoSense 的 app storage 读 ~/.octosense（cx.get_data_dir()）。
#   ONCUE_RINX_DATA_DIR  ：Rinx 数据根（rinx/src/lib.rs:131-143 支持该覆盖）；
#                          mini app 的 agent workspace 由它派生，必须在非系统根下。
#   ONCUE_HOST_CWD       ：宿主工作目录（同上，禁止落在系统根）。
: "${ONCUE_HOST_HOME:=/srv/oncue-home}"
: "${ONCUE_RINX_DATA_DIR:=/srv/oncue-rinx-data}"
: "${ONCUE_HOST_CWD:=/srv/oncue-host-cwd}"

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

# ---- octos 内核与 core dir（无密钥；AI1 评审 #258 + #267）---------------------
# 桌面宿主用 ai-host 的 KernelSource::Env 找内核：**只认 OCTOS_APP_CORE_BIN**，
# 不会接管"任意一个已在跑的 octos serve"。没有它，宿主日志只会是：
#   octos: no octos kernel: no kernel binary configured (OCTOS_APP_CORE_BIN)
#
# core dir 的解析顺序（crates/kernel/src/dirs.rs:18-45，first match wins）：
#   1) shell 显式传入的 Options::core_dir
#   2) **$OCTOS_APP_CORE_DIR**（非空）      ← 变量名就是它，没有别的
#   3) <app data dir>/octos-home/.octos
#   4) $HOME/octos-home/.octos
# **重要**：dirs.rs 的 shared_profile_source 只在 ①② 都没设时，才从
# $HOME/octos-home/.octos 继承旧 profile。所以一旦显式设置 $OCTOS_APP_CORE_DIR，
# **不会自动迁移**——必须自己把 provider profile 放到
#     <effective core dir>/profiles/_main.json
# 本文件只放**路径**，不放任何取值/密钥；profile 内容由用户私有配置（600/700）。
: "${OCTOS_APP_CORE_BIN:=$ONCUE_RUNTIME_ROOT/octos/octos}"
: "${OCTOS_APP_CORE_DIR:=$ONCUE_STATE_DIR/octos-core}"
export OCTOS_APP_CORE_BIN OCTOS_APP_CORE_DIR
mkdir -p "$OCTOS_APP_CORE_DIR/profiles" 2>/dev/null || true

# ---- 宿主出网代理（可选；AI1 #266 实测需要）----------------------------------
# 本机直连 matrix.org **超时**（curl 6.2s connection timed out），
# 但走本地 mixed 代理 200/0.83s，`.well-known/matrix/client` 也 200。
# Rinx 的客户端若读系统代理环境变量，就需要把这三个变量一起给宿主。
# NO_PROXY 必须带 127.0.0.1：宿主自己要连本地服务（如 App Hub 的 8765）。
: "${ONCUE_HOST_PROXY:=}"
if [ -n "$ONCUE_HOST_PROXY" ]; then
  export HTTPS_PROXY="$ONCUE_HOST_PROXY" HTTP_PROXY="$ONCUE_HOST_PROXY"
  : "${ONCUE_HOST_PROXY_SOCKS:=}"
  [ -n "$ONCUE_HOST_PROXY_SOCKS" ] && export ALL_PROXY="$ONCUE_HOST_PROXY_SOCKS"
  export NO_PROXY="${NO_PROXY:-localhost,127.0.0.1,::1}"
  export no_proxy="$NO_PROXY"
fi

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
proc_cwd() { readlink -f "/proc/$1/cwd" 2>/dev/null; }

# proc_environ_has <pid> <KEY=value>：environ 里**精确**含该赋值。
# 用途：宿主现在有 HOME / RINX_DATA_DIR / OCTOS_APP_CORE_DIR 三个作用域变量，
# 只比 exe+display 会把"旧路径起来的同一个二进制"误判成迁移后的宿主（假绿）。
# 这三个值都只是**路径**，不含秘密。
proc_environ_has() {
  [ -r "/proc/$1/environ" ] || return 1
  tr '\0' '\n' < "/proc/$1/environ" 2>/dev/null | grep -qxF "$2"
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

