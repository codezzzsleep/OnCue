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
