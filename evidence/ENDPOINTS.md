# OnCue 端点与路径清单（本机自建 App Hub，2026-10-01）

本清单只记录**路径与用途**：不摘抄任何密钥、口令、token 或账号内容。
所有端口均为**仅回环（127.0.0.1 / ::1 / :99）**绑定，不对外监听。

## 1. 运维脚本目录 `/root/oncue-runtime/deploy/`

| 脚本 | 一句话用途 | 关键命令（节选自脚本） |
| --- | --- | --- |
| `start.sh` | headless 一键启动/复用：Xvfb :99 → OctoSense（内嵌 Rinx 宿主）→ x11vnc :5901 → websockify/noVNC :6080。 | `Xvfb :99 -screen 0 1440x900x24 -nolisten tcp`；`dbus-run-session -- ./target/release/octosense --module rinx --test-action launch-rinx`；`x11vnc -display :99 -localhost -rfbport 5901 -rfbauth "$ONCUE_STATE_ROOT/vnc.pass" -forever -shared -noxdamage -wait 5 -defer 5`；`websockify --web="$ONCUE_INSTALL_ROOT/tools/noVNC" 127.0.0.1:6080 127.0.0.1:5901`；健康探测 `curl -s http://127.0.0.1:$MAKEPAD_REMOTE/help`，优雅退出 `curl -s http://127.0.0.1:$MAKEPAD_REMOTE/quit`（`start.sh:42,49,53,60,64,75,89`） |
| `publish-local-hub.sh` | 用真实 `hub` 二进制把 `oncue/bundle` 签名、校验并发布进本地镜像 `state/hub-mirror/`，最后用锚点公钥验证目录。 | `hub sign-manifest "$BUNDLE" --key "$KEYS/working.key" --key-id oncue.local`；`hub check "$BUNDLE" --publisher-key "oncue.local=$(cat "$KEYS/working.pub")"`；`hub check "$BUNDLE" … --catalog "$CATALOG"`（发布期闸门）；`hub publish "$BUNDLE" --catalog "$CATALOG" --key … --anchor-cert … --publisher oncue.local --repo https://github.com/codezzzsleep/OnCue --commit "$(git rev-parse HEAD)" --reviewer /root/oncue-runtime/deploy/oncue-reviewer.sh --out "$MIRROR"`；`hub verify "$CATALOG" --anchor "$ANCHOR"`（`publish-local-hub.sh:10-47`） |
| `oncue-env.sh` | 纯路径与固定修订号的运行时环境（自述「无密钥」），被其余脚本 `source`；定义 `OCTOSENSE_HOME/APP_DATA`、`OCTOSENSE_HUB`、`OCTOSENSE_HUB_ANCHOR`、`DISPLAY=:99`、`MAKEPAD_REMOTE=18141`。 | `source oncue-env.sh`；固定修订：OctoSense `6c4746f0…`、octos `fe08d8e6…`、makepad `1f3b1ded…`、octoscript `dbd48cfb…`、Rinx `0879548b…`（`oncue-env.sh:11-17`） |
| `oncue-reviewer.sh` | 充当 hub 的审核回调：从 stdin 读评审包 JSON，落盘问答记录并输出 hub 解析的裁决对象（`route = pass`）。 | 读 stdin → 写 `/tmp/oncue-reviewer-packet.json` 与 `evidence/hub-review-answers.md` → stdout 输出 `{"route":"pass","reasons":[…7 条…]}`（`oncue-reviewer.sh:5-7,40-52`） |

同目录另有 `stop.sh`（停止入口）、`README.md` / `REPORT.md`（部署说明），本文不展开。

## 2. hub 二进制与 App Hub 源码 rev

- hub 二进制：`/tmp/hubbuild/app-hub/target/release/hub`
  - ELF 64-bit LSB pie executable, ARM aarch64, not stripped；sha256 `6d7fc89eb46043a1d4b2afea005f5dc6671a3a42e858f8bdf7c48ba8001232ef`（2026-10-01 10:48）。
- 对应的 App Hub 源码 rev：`0f332112f0b5a379c5bb33790df74b21597190cf`
  - 来源：`publish-local-hub.sh:4-5` 注释「built from the pinned OctoSense-App-Hub rev 0f332112, the same dep OctoSense itself is locked to」。
  - 仓库锁定：`OctoSense/Cargo.toml:69,96,100-101,254-257` 与 `OctoSense/Cargo.lock:7364,7380,7408,7429` 均为同一 rev（`https://github.com/OctoSense-org/OctoSense-App-Hub`）。
  - 本机 checkout：`/root/.cargo/git/checkouts/OctoSense-App-Hub-0f87f6c76fe4766d/0f33211/`（与运行日志中的栈帧路径一致，见 `LOGS-EXCERPT.md` 第 B 组）。
- 发布/校验链（脚本内的调用顺序，即「闸门 + 签名者」）：`sign-manifest` → `check` → `check --catalog` → `publish` → `verify --anchor`。

## 3. 镜像与工件 `/root/oncue-runtime/state/hub-mirror/`

- `catalog.json` — 目录（签名对象）：`schema` / `sequence: 5` / `published: 2026-10-01` / `key.public`（工作公钥）/ `key.anchor_certificate` / `entries[5]` / `signature`；5 个条目版本为 `0.1.0, 0.1.1, 0.2.0, 0.3.0, 0.3.1`，`publisher: oncue.local`，`status.state: offered`。
- `artifacts/` — 工件命名规则：
  - 目录形：`artifacts/<app-id>-<semver>.bundle/`，内含 `manifest.json`（id/version/capabilities/integrity.bundle_blake3）、`listing.json`、`main.splash`、`assets/`、`screenshots/`；
  - 旁挂形：`artifacts/<app-id>-<semver>.bundle.pack.json`，为 `{"schema":1,"files":{<相对路径>: <base64 内容>}}` 的文件清单；
  - 例：`artifacts/oncue-screening-room-0.3.1.bundle/` 与 `artifacts/oncue-screening-room-0.3.1.bundle.pack.json`。
- 设备侧副本（安装后落地的目录状态）：`/root/oncue-runtime/state/apps/catalog.json`（`sequence: 5`）与上一版备份 `/root/oncue-runtime/state/apps/catalog.json.bak-seq4`（`sequence: 4`）。

## 4. 密钥路径（只写路径与用途，不摘抄内容）

目录 `/root/oncue-runtime/state/hub-keys/`（目录权限 700，文件 640）：

| 路径 | 用途 |
| --- | --- |
| `anchor.pub` | 锚点**公钥**；设备唯一信任的目录签名者，经 `OCTOSENSE_HUB_ANCHOR` 注入。 |
| `working.pub` | 发布者**公钥**（`key_id = oncue.local`），随 `hub check/publish --publisher-key` 注册。 |
| `anchor-cert.hex` | 锚点**证书**（把 working key 绑定到锚点），随 `hub publish --anchor-cert` 写入目录 `key.anchor_certificate`。 |
| `working.key` | 发布者**私钥** —— **永不外传、永不入库**；仅 `sign-manifest` / `publish` 时由脚本读取。 |
| `anchor.key` | 锚点**私钥**（同目录一并存在）—— 同属**永不外传、永不入库**，任何证据文件都不得摘抄其内容。 |

## 5. 运行态

- OctoSense 的 hub 环境变量（读自 `oncue-env.sh:37-38`，本文件不记录其取值内容）：
  - `OCTOSENSE_HUB` = `$ONCUE_STATE_ROOT/hub-mirror`（即 `/root/oncue-runtime/state/hub-mirror`）——小程序从本地镜像取目录与工件。
  - `OCTOSENSE_HUB_ANCHOR` = `$(cat "$ONCUE_STATE_ROOT/hub-keys/anchor.pub")` ——只信任这一个目录签名者。
- 小程序数据根：`/root/oncue-runtime/state/apps/oncue-screening-room/`
  - `bundle/` — 已安装工件（当前 `manifest.json` 为 `0.3.1`，`main.splash` 22193 B，含 `listing.json`、`assets/`、`screenshots/`）；
  - `common/` — 应用公共数据；`accounts/` — 按账号隔离的数据；`cache/` — 缓存（三者当前均为空目录）。
- 日志目录：`/root/oncue-runtime/state/logs/`（如 `octosense-rinx.log`、`cardhost.log`、`cardhost2.log`、`start*.log`）；octos 内核另有 `/root/oncue-runtime/state/octos-core/logs/serve.2026-10-01.log`。

## 6. 入口端口（仅本机绑定）

| 端点 | 用途 | 依据 |
| --- | --- | --- |
| `127.0.0.1:18141` | Makaepad 远程桥（`MAKEPAD_REMOTE`），`/help` 健康探测、`/quit` 优雅退出 | `oncue-env.sh:41`、`start.sh:42,49` |
| `127.0.0.1:5901` | x11vnc，把 `:99` 镜像出来（口令文件 `state/vnc.pass`，内容不记录） | `start.sh:3,75` |
| `127.0.0.1:6080` | websockify + noVNC，浏览器入口 `http://127.0.0.1:6080/vnc.html` | `start.sh:3,89,96` |
| `:99`（X11 DISPLAY） | Xvfb 虚拟显示（1440x900x24，`-nolisten tcp`） | `oncue-env.sh:20`、`start.sh:19` |

实测监听快照（`/root/oncue-runtime/state/logs/i4-ports.txt`）：`127.0.0.1:18141`、`127.0.0.1:6080`、`127.0.0.1:5901`、`[::1]:5901` —— 均为回环地址，无 `0.0.0.0` 绑定。

---

本文件不含任何密码/token/私钥内容。

以下 sha256 覆盖本行以上的全部正文（不含哈希行自身）。
sha256: d7cd8226b4bbf126602c7e4e6d168417b6d00fc596ded22e38364dcdb8fdbaf6
