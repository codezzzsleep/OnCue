# OnCue 运行日志摘录（脱密，2026-10-01）

来源与时间窗：

- `/root/oncue-runtime/state/logs/octosense-rinx.log` —— 当前 OctoSense 实例（`--module rinx`）的宿主日志；实例启动时间 `Thu Oct 1 16:51:26 2026 CST`（launcher pid 441500），文件仍在增长。
- `/root/oncue-runtime/state/logs/cardhost.log`、`cardhost2.log` —— 卡片宿主（bundle 运行器）日志。
- `/root/oncue-runtime/state/octos-core/logs/serve.2026-10-01.log` —— 共享 octos 内核日志（tracing 时间戳为 UTC，+8h 即本机 CST）。
- `/root/oncue-runtime/state/logs/i4-ports.txt` —— 监听快照。

脱密规则：不出现任何密码、token、私钥；保留房间 ID 与事件 ID；**不摘抄聊天消息正文**；
操作者 Matrix ID 在本文件中记为 `@<redacted>:matrix.org`。
源日志中确实存在必须排除的内容（例如某行含 Matrix 备份密钥、以及会话/凭据字段），
本次摘录一律跳过，未复制任何密文；详见文末「脱密说明」。

---

## A. 小程序模块加载 / 模块实例（4 条）

`octosense-rinx.log:15`
```
[I] crates/shell/src/lib.rs:5283:9 - wm: modules linked: ["rinx", "terminal", "apphub", "card"]
```
→ 证明：宿主把 `apphub`（App Hub 目录模块）与 `card`（小程序卡片宿主）一起链入窗口管理器，本地自建 Hub 的入口模块存在。

`octosense-rinx.log:57`
```
[I] crates/shell/src/module_host.rs:508:9 - wm: module instance rinx.1 for client 1 in isolate SplashVmId(1) (scope i1g1)
```
→ 证明：Rinx 宿主作为 client 1 在独立 isolate 中起了模块实例（OnCue 的原生宿主环境）。

`octosense-rinx.log:187` 与 `octosense-rinx.log:188`
```
[I] crates/shell/src/module_host.rs:508:9 - wm: module instance card.1 for client 2 in isolate SplashVmId(3) (scope i2g2)
[I] crates/shell/src/lib.rs:2490:9 - wm: launched hub:oncue-screening-room as client 2 (in-process, card)
```
→ 证明：OnCue 是**从 Hub（apphub）入口启动**的 `hub:oncue-screening-room`，作为 client 2 的 `card` 模块实例运行在**另一个** isolate（`SplashVmId(3)`，scope `i2g2`）里，与 Rinx 宿主隔离。

## B. 卡片宿主：加载、能力授予与沙箱（4 条）

`octosense-rinx.log:189`
```
[I] /root/.cargo/git/checkouts/OctoSense-App-Hub-0f87f6c76fe4766d/0f33211/crates/appstore/src/cardapp.rs:94:9 - card: oncue-screening-room running under 6 capability(ies), 1 host(s), 65536 bytes of storage, 8000000 instructions, 33554432 bytes of heap
```
→ 证明：运行时确实由 **App Hub rev `0f33211`** 的 `crates/appstore/src/cardapp.rs` 承载（与 `ENDPOINTS.md` §2 的 rev 一致），并按 manifest 的 6 项能力、65536 B 存储、8000000 指令、33554432 B 堆运行。

`cardhost.log:9`
```
[I] src/host.rs:248:9 - card-host: oncue-screening-room 0.1.0 admitted — capabilities {"matrix.read_messages", "matrix.room_info", "octos.session.open", "octos.turn.interrupt", "octos.turn.start", "storage"}, hosts {}, storage 65536 bytes, agent none
```
→ 证明：bundle 被卡片宿主**接受（admitted）**，授予的正是 6 项声明能力（含 `octos.session.open` / `octos.turn.start` / `octos.turn.interrupt`），网络 hosts 为空、无 agent。

`cardhost.log:10`
```
[I] src/host.rs:280:9 - card-host: isolate jailed at /root/oncue-runtime/state/cardhost/oncue-screening-room with 65536 bytes, 6 capability(ies), 1 host(s), 8000000 instructions, 33554432 bytes of heap, prompts false — all enforced
```
→ 证明：隔离与配额是**强制执行**（`all enforced`），且禁用 prompts；日志同时给出运行态 jail 目录。

`cardhost.log:8`
```
[I] src/host.rs:85:9 - card-host: stamped /root/oncue-runtime/dev/OnCue/oncue/bundle/manifest.json with digest 95f5df275ae1869c3c058f97bb0ed0fb0239bf186e9520ef88e1b5e1f5a93ebe
```
→ 证明：该次运行绑定的 bundle 是仓库工作树 `oncue/bundle`，并记录了 stamp 摘要（可用于比对版本与摘要，而非只凭 UI 提示）。

## C. matrix 房间读取（同步层：房间列表与分页，4 条）

`octosense-rinx.log:106`
```
[I] .../rinx-cf0dcd4e7b4d3fa8/0879548/src/sliding_sync.rs:4827:5 - Initial room list loading state is Loaded { maximum_number_of_rooms: Some(5) }
```
→ 证明：Rinx 的滑动同步已完成初始房间列表加载（上限 5），即设备能列出已加入房间——这是「附加房间」可被选中的前提。

`octosense-rinx.log:111`
```
[I] .../sliding_sync.rs:4369:5 - Adding new joined room !j6BaOOAvAASFVqB8jDJOd9O7F8OgOrFjGcFKMVa0WrI, name: Some(Named("oncue-test-room"))
```
→ 证明：本人私有测试房间 `!j6BaOOAvAASFVqB8jDJOd9O7F8OgOrFjGcFKMVa0WrI`（`oncue-test-room`）确实以「已加入」状态进入客户端状态机。

`octosense-rinx.log:117` 与 `octosense-rinx.log:118`
```
[I] .../sliding_sync.rs:940:21 - Starting backwards pagination request for MainRoom(!j6BaOOAvAASFVqB8jDJOd9O7F8OgOrFjGcFKMVa0WrI)...
[I] .../sliding_sync.rs:954:29 - Completed backwards pagination request for MainRoom(!j6BaOOAvAASFVqB8jDJOd9O7F8OgOrFjGcFKMVa0WrI), hit start of timeline? no
```
→ 证明：对该房间**实际发起了历史分页并成功完成**（回到时间线起点为 no，说明确实取到了事件），即「读消息」的传输路径可用；但这是宿主同步层，不等于小程序读消息成功（见「尚未出现」第 1 项）。

## D. octos 内核与服务注册（4 条）

`octosense-rinx.log:10` / `:12` / `:13`
```
[I] crates/ai-host/src/lib.rs:302:13 - octos: kernel service ready (starts on first use), core dir Some("/root/oncue-runtime/state/octos-core")
[I] crates/ai-host/src/lib.rs:393:5 - model: service registered (one-shot calls; granted apps only)
[I] crates/ai-host/src/lib.rs:356:9 - octos: contained apps' service registered (Consent)
```
→ 证明：宿主为受管小程序注册了 octos 内核服务、模型服务（**仅授予了能力的 app 可用**）与 Consent（同意）服务，并指向共享核心目录 `state/octos-core`。

`octosense-rinx.log:95`
```
[I] crates/ai-host/src/lib.rs:292:71 - octos-core: starting kernel 1: /root/oncue-runtime/octos/target/release/octos serve --stdio --data-dir /root/oncue-runtime/state/octos-core
```
→ 证明：共享 octos 核心按「首次使用时启动」真正拉起（`octos serve --stdio`），OnCue 的 `octos.*` 能力指向的就是这个内核。

## E. 阻塞/失败行：为什么现在还没有 octos 回合（3 条）

`octosense-rinx.log:3041`
```
[I] crates/shell/src/lib.rs:3574:17 - ask: oncue-screening-room's agent
```
→ 证明：宿主确实就 OnCue 的 agent 使用发起了询问（同意流程入口被触达）。

`octosense-rinx.log:4414`
```
[I] crates/shell/src/agents.rs:159:23 - agents: oncue-screening-room's agent could not be prepared: profile '_main' is not configured for this AppUI session (profile_unresolved)
```
→ 证明：本次运行中 OnCue 的 agent **未能准备**（`profile '_main'` 未配置，`profile_unresolved`），因此不会产生真实模型回合——这正是 octos session/turn 日志缺失的直接原因，不能记为通过。

`octos-core/logs/serve.2026-10-01.log`（末行，UTC 09:31:47 = CST 17:31:47）
```
2026-10-01T09:31:47.379000Z  WARN steer inbox sweep: AppState has NO profiles registered; steer wake cannot run for any session
```
→ 证明：共享内核侧同样报告**没有任何 profile 注册**、任何会话都无法被唤醒，与上一行互为印证。

## F. 宿主入口与端口（1 条 + 1 段快照）

`octosense-rinx.log:2`（`:3` 为同内容的 tracing 行）
```
[makepad-remote] listening on 127.0.0.1:18141 pid=441504 app=octosense grabs=/tmp/makepad-remote/octosense-441504
```
→ 证明：当前实例的远程桥只监听回环 `127.0.0.1:18141`，可作为「仅本机绑定」的运行态佐证。

`i4-ports.txt`（监听快照）
```
LISTEN 0 128 127.0.0.1:18141
LISTEN 0 100 127.0.0.1:6080
LISTEN 0  32 127.0.0.1:5901
LISTEN 0  32 [::1]:5901
```
→ 证明：远程桥、noVNC、VNC 三个入口都是回环地址，无 `0.0.0.0` 监听。

---

## 尚未出现（不编造，逐项标注预期时机）

1. **小程序模块内部的自身日志**（`cue_*` 事件、从附加房间载入最近 12 条消息的**读取成功行**）——**尚未出现，预期在完成第 10 步后出现**（`oncue/docs/NATIVE-WORKFLOW.md` 第 10 项：从本人测试房间载入最近 12 条文本消息，核对房间与脱密 API 事件）。目前隔离内只有 `card: oncue-screening-room running under 6 capability(ies)…`（B 组）与 splash 求值行，没有任何应用级事件行。
2. **octos session/turn（真实模型回合）日志行**——尚未出现，预期在完成第 11 步后出现（同文件第 11 项：在宿主配置已授权模型、用共享 Octos 核心完成原生真实模型回合）；E 组两条 `profile_unresolved` / `NO profiles registered` 是当前的阻塞证据。
3. **catalog 接受 / 版本门的明文日志行**——尚未出现。目前只有**间接证据**：`wm: launched hub:oncue-screening-room`（A 组）＋卡片宿主 admitted（B 组）＋设备侧目录 `state/apps/catalog.json`（`sequence: 5`，条目 0.1.0…0.3.1）与已安装 `state/apps/oncue-screening-room/bundle/manifest.json`（`0.3.1`）。要拿到「版本门」原文，需要一次更旧/更新 bundle 被拦下的安装演练。
4. **hub CLI 校验输出**（`sign-manifest` / `check` / `check --catalog` / `publish` / `verify` 的 stdout）——尚未出现为独立日志文件；目前只有 `deploy/publish-local-hub.sh:25-47` 的脚本定义（见 `ENDPOINTS.md` §2）。发布时若要留证，需要把该脚本输出重定向到 `state/logs/`。

## 旁证（非日志，仅列路径，避免与上面混淆）

- `state/evidence/matrix-room-read.json` —— 脱密房间读取记录：只保留房间 ID、事件 ID、时间戳、发送者与**正文长度**，不含聊天正文；可用于第 10 步的房间读取核对。
- `state/octosense/approvals/consent.json` —— 同意记录：`oncue-screening-room.allowed = true`（UTC 2026-10-01 09:17:39），说明能力同意已落盘。

## 脱密说明

- 本文件不含任何密码、token、私钥内容；未摘抄任何聊天消息正文；操作者 Matrix ID 已记作 `@<redacted>:matrix.org`。
- 源日志 `octosense-rinx.log` 中存在必须排除的敏感行（例如一行打印了 Matrix 备份密钥、另有会话/凭据字段）。这些行本次**一律跳过、未复制**；建议后续在日志级别或写入前做一次脱敏/轮转，并把该类日志保持在仓库之外。
- 这些日志都在 `state/` 下（仓库外），且 `deploy/.gitignore` 已排除 `state/`、`*.log`、`*.png`；仓库内不放日志原件。

---

以上摘录合计 **20 条日志行 + 1 段监听快照（4 行）**，分 6 组（A–F）；另列 2 条旁证路径。
以下 sha256 覆盖本行以上的全部正文（不含哈希行自身）。
sha256: d1874893e25fb7ed08abaac7c79fc1398c5d479aee06f710bea28d5e47b98ff1
