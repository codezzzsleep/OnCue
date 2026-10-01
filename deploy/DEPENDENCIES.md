# 宿主运行链的依赖清单与构建（2026-10-02 新容器实测）

本文记录**本次容器上实际装过、实际构建成功**的步骤，不是"照文档抄一遍"。
环境：Huawei Cloud EulerOS 2.0 (aarch64)，**cgroup v1**，16 vCPU（`cfs_quota_us 1450000 /
period 100000 = 有效 14.5 核`），**内存上限 25 GiB（26843545600 B）**、无 swap 余量。

## 1. 固定源码（不可漂移）

| 组件 | 仓库 | 钉定提交 |
| --- | --- | --- |
| OctoSense | `https://github.com/OctoSense-org/OctoSense.git` | `6c4746f0854b74446f854fdcd32eeb87b5192a81` |
| Rinx | `hagency-org/Rinx.git`，由 `Cargo.lock` 钉定 `tag=v1.0.0` → | `0879548ba826c786eb6ad3f60dfba7bd342bd750` |
| octos | `octos-org/octos.git` | `fe08d8e6b3b32e672b0f956a2b692c3c8205b167` |
| App Hub | `OctoSense-org/OctoSense-App-Hub` | `0f332112f0b5a379c5bb33790df74b21597190cf` |
| makepad | `OctoSense-org/makepad.git` | `1f3b1dedfbb81424eb8dbfe9e2c634fa73dc54`※ |
| Octoscript | `OctoSense-org/Octoscript.git` | `dbd48cfb799551c11e30970c393777d29644a605` |
| Octoscript-Makepad | `OctoSense-org/Octoscript-Makepad.git` | `cb66de073469063abeb2a5ab2a2bbf3cdb365745` |

※ makepad/Octoscript 的实际提交以 `Cargo.lock` 为准；仓库根**没有 `rust-toolchain.toml`**，
所以 Rust 版本**不是**由文件锁定的，只记录实际安装版本。

## 2. 系统包（dnf；HCE 源）

```bash
dnf -y install \
  gcc-c++ make cmake pkg-config openssl-devel ninja-build patch which tar xz unzip bzip2 \
  procps-ng net-tools lsof \
  xorg-x11-server-Xvfb xorg-x11-utils mesa-dri-drivers mesa-libGL mesa-libEGL mesa-libGBM \
  libxkbcommon libxkbcommon-devel libX11-devel libXcursor-devel libXrandr-devel libXi-devel \
  libXinerama-devel libXtst-devel libxcb-devel \
  fontconfig-devel freetype-devel alsa-lib-devel tigervnc-server ffmpeg openssl \
  xorg-x11-xauth
dnf -y install libdrm-devel    # ← 见下面"必须记住的那一条"
pip3 install --index-url https://mirrors.huaweicloud.com/repository/pypi/simple websockify
```

**必须记住的那一条**：链接阶段需要 `-ldrm`，而 HCE 源里只有运行库 `libdrm.so.2`，
**没有 `libdrm.so`**。不装 `libdrm-devel` 会得到：

```
error: linking with `cc` failed: exit status: 1
  = note: /usr/bin/ld: cannot find -ldrm
```

链接行实际要求（10 个）：`-lXcursor -lX11 -lasound -lpulse -lssl -lcrypto -ldrm -lxkbcommon
-lwayland-egl -lwayland-client`。除 `-ldrm` 外其余在 HCE 源里都有。

**替代说明（与 RECOVERY.md 的偏差，已核实）**：
- HCE 源**没有 x11vnc** → 用 `tigervnc-server` 提供的 **`x0vncserver`**（官方文档：
  它共享**已存在**的 X display，不另造 Xvnc），符合 `Xvfb → 真实宿主画面` 链路。
- HCE 源**没有 websockify / noVNC** → websockify 走 pip；noVNC 从
  `https://github.com/novnc/noVNC` clone（走本机 `127.0.0.1:17888` 代理）。
- HCE 源**没有 glx-utils / mesa-utils** → 暂无 `glxinfo`；软件渲染以真实像素与宿主日志为准，
  `xdpyinfo` 本身不证明 GL 渲染器。

## 3. Rust 工具链

系统源的 `rust/cargo` 只有 **1.57.0**（太老）。用 rustup + 华为云镜像：

```bash
export RUSTUP_DIST_SERVER=https://mirrors.huaweicloud.com/rustup
export RUSTUP_UPDATE_ROOT=https://mirrors.huaweicloud.com/rustup/rustup
curl -sSL -o rustup-init "$RUSTUP_DIST_SERVER/rustup/dist/aarch64-unknown-linux-gnu/rustup-init"
chmod +x rustup-init && ./rustup-init -y --profile default --default-toolchain stable --no-modify-path
```

实际装成：**rustc 1.98.1 / cargo 1.98.1 / rustup 1.29.1**。
（官方 `static.rust-lang.org` 在本机实测 15s 超时，只拿到 826991/943486 字节。）

crates 走 rsproxy 稀疏索引（`~/.cargo/config.toml`），`Cargo.lock` 的校验和仍保证完整性：

```toml
[source.crates-io]
replace-with = "rsproxy-sparse"
[source.rsproxy-sparse]
registry = "sparse+https://rsproxy.cn/index/"
[net]
git-fetch-with-cli = true
[http]
proxy = "http://127.0.0.1:17888"
```

## 4. 构建（串行、限并发）

```bash
cd /opt/src/OctoSense
python3 tools/setup.py                 # 准备 .sources/（makepad/octoscript/…）
python3 tools/setup.py --check --cargo # 图守卫：一个 makepad / 一个 App Hub / 一个 octos / 一个 Rinx
CARGO_BUILD_JOBS=2 cargo build --release --locked -p octosense
```

实测：`setup.py` exit 0；`--check --cargo` exit 0；构建 **665 个 crate 成功、0 编译错误**，
`Finished release profile [optimized] target(s) in 19.88s`（增量重链）。
产物 `target/release/octosense`，**195396864 B（186 MiB）**，
`sha256 6ee5eb1565bafbe53c38e972a916ce546d928c0d54ac238b100d542971e25fc3`。

**资源纪律**：`CARGO_BUILD_JOBS=2`、一次只跑一个构建；全程 cgroup
`memory.max_usage_in_bytes` 峰值 **12.42 GiB**（limit 25 GiB），`memory.failcnt=0`、`oom_kill=0`。

## 5. App Hub 本地演练（可选，用于把应用装进宿主）

`hub` 由 App Hub 仓库构建，需要 `../makepad`、`../octoscript`、`../octoscript-makepad`
三个**兄弟目录**（其 `Cargo.toml` 的 `[patch]` 按相对路径找）：

```bash
mkdir -p /opt/src/apphub && cd /opt/src/apphub
ln -s /opt/src/OctoSense/.sources/makepad makepad
ln -s /opt/src/OctoSense/.sources/octoscript octoscript
ln -s /opt/src/OctoSense/.sources/octoscript-makepad octoscript-makepad
cp -r <AppHub checkout> OctoSense-App-Hub && chmod -R u+w OctoSense-App-Hub
cd OctoSense-App-Hub && CARGO_BUILD_JOBS=2 cargo build --release -p octosense-app-hub --bin hub
```

演练信任根必须是**新建的**，不得冒充旧 `oncue.local`（RECOVERY.md §5）：

```bash
hub keygen keys/working.key && hub keygen keys/anchor.key
hub certify --anchor keys/anchor.key --working keys/working.key      # → anchor-cert
hub stamp <bundle>
hub sign-manifest <bundle> --key keys/working.key --key-id oncue.dev
hub check <bundle> --publisher-key oncue.dev=$(hub pubkey keys/working.key)
hub publish <bundle> --catalog mirror/catalog.json --key keys/working.key \
  --anchor-cert <cert> --publisher oncue.dev \
  --publisher-key oncue.dev=$(hub pubkey keys/working.key) --out mirror
hub verify mirror/catalog.json --anchor $(hub pubkey keys/anchor.key)
```

**容易踩的两个点**：
1. `hub publish` 内部会再跑一次门禁，**必须**同时给 `--publisher-key id=hex`，
   否则得到 `[refused] publisher-signature: publisher key "<id>" is not registered with this hub`。
2. 宿主的启动门禁**不联网**：它读 `<app 数据根>/catalog.json` 这个**本地缓存**
   （`app-hub-app/src/catalog.rs:151`）。只发布到镜像、不把目录放进缓存位置，启动时会得到
   `"<app> is not in this catalog"`，而且**不写日志、不打 client 行**。
   所以还要：`cp mirror/catalog.json ~/.octosense/apps/catalog.json`。

## 6. 启动与健康检查

```bash
deploy/start.sh                  # Xvfb → 宿主 → x0vncserver → noVNC
deploy/health.sh                 # 每步给可判定证据（含"不带认证必须被拒"的反证）
deploy/stop.sh                   # 只停止身份复核通过的进程，不用宽泛 pkill
```

### 6.1 进程身份纪律（AI1 评审 #256 要求）

`deploy/` 不用"同名进程"或"PID 还在"来判断归属，因为：

- 同机可能有**另一个 display / 另一个 card-host** 的同名进程 → 直接 adopt 会误接管；
- 旧 PID 会被系统**复用** → `kill -0` 通过并不代表那是我们的进程。

因此每个组件在 `$ONCUE_STATE_DIR/<name>.run` 记 **pid + starttime + exe + display + 启动时刻**，
`start.sh` 只接管特征完全一致的进程，`stop.sh` 停止前逐项复核，不符就**拒绝停止**并报出。
另外：**宿主没停成时 stop.sh 会保留 Xvfb**——因为停掉 Xvfb 会把它上面的 X 客户端一起带走，
那等于变相误杀。

`health.sh` 的三重判据（避免假绿）：① 身份复核通过；② 日志 mtime ≥ 本次启动时刻；
③ **本次启动动作预期的 `wm: launched` 必须出现**，否则不算全绿。

### 6.2 从干净 shell 按本文跑通（hub 变量必须显式给出）

`OCTOSENSE_HUB` / `OCTOSENSE_HUB_ANCHOR` 的默认值是**空的**，但本地演练镜像必须两个都给，
否则启动门禁读不到目录缓存。完整序列：

```bash
# 0) 干净 shell，只 source 无密钥配置
cd <this repo>
source deploy/env.sh

# 1) 指向本地演练镜像与它的**锚点公钥**（公钥，不是私钥）
export OCTOSENSE_HUB="$ONCUE_RUNTIME_ROOT/dev/mirror"
export OCTOSENSE_HUB_ANCHOR="$(/opt/src/apphub/OctoSense-App-Hub/target/release/hub \
  pubkey "$ONCUE_RUNTIME_ROOT/dev/keys/anchor.key")"

# 2) 把已签名目录放进宿主读取的**缓存位置**（否则报 "<app> is not in this catalog"）
cp "$OCTOSENSE_HUB/catalog.json" "$HOME/.octosense/apps/catalog.json"

# 3) 安装包到 app 数据根（布局固定为 <数据根>/<manifest-id>/bundle/）
mkdir -p "$HOME/.octosense/apps/oncue-screening-room"
cp -r "$OCTOSENSE_HUB/artifacts/oncue-screening-room-0.4.3.bundle" \
      "$HOME/.octosense/apps/oncue-screening-room/bundle"

# 4) 起链路并核对（health 不通过就不要往下走）
deploy/start.sh
deploy/health.sh
```

`start.sh` 在这两个变量为空时会打印提示但不退出——因为系统应用不需要 hub；
只有**本地演练镜像里的应用**才必须设置它们。

私有（**不进仓库**、600 权限、仓库外）：VNC 密码文件 `$ONCUE_STATE_DIR/vnc/vnc-passwd`、
Xauthority cookie、hub 演练私钥、账号/模型凭据。
