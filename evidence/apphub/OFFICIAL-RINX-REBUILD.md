# 用官方 Rinx 重建宿主（弃用本地补丁）— 2026-10-02

## 背景

此前宿主 `octosense` 是拿**本地改过的 Rinx 副本**构建的（`/tmp/rinx-0879548-fixed`），
补丁内容是把 mini app import 面板里含混的 `ids!(room)` 改成 `ids!(import_form.room)`。
原因是官方 v1.0.0（`0879548`）在 Review 之后会**清空已填的房间号**。

核对上游后确认：该修复**早已由上游 PR #48 合入**（`bb2a4d4df7d0`，2026-10-01）。

## 本次做法

1. `git clone` 官方 `hagency-org/Rinx`，检出 **`main` = `c515e5fc9b6dc22e67f7d551b09fdd793ec685a1`**
   —— **纯官方源码，零本地改动**（`git status --porcelain` 为空）
2. 用 path override 指向该克隆（不改 OctoSense 的 `Cargo.toml` 钉定）：
   ```toml
   [patch."https://github.com/hagency-org/Rinx.git"]
   rinx = { path = "/tmp/rinx-official" }
   ```
3. `CARGO_BUILD_JOBS=2 cargo build --release -p octosense --config /tmp/rinx-official-config.toml`
   → **8 分 33 秒，exit 0**

| | sha256 |
| --- | --- |
| 旧（含本地补丁） | `3800efbc761da7b112b9251e0f632542419eeb29c0ecd6a94b3f07a3fbe94930` |
| **新（官方 Rinx）** | **`87ed4dccd14bac51222f40c38d4db086911790786b688a68a503002ada64ba25`** |

## 验证

### 1. 隔离实例冒烟（`:98`，不碰生产）
- 新二进制启动正常；日志源码路径为 `/tmp/rinx-official/src/app.rs`（证明用的是官方源码）
- `wm: launched rinx as client 1 (in-process, rinx)`；Matrix SDK 循环启动

### 2. **关键项：Review 后房间是否保留**（这正是当年打补丁的 bug）
在官方构建上走 `Discover → Mini apps → Import an app`，填包路径 + 44 字符测试房间，
点 **Review bundle**，面板显示：
```
OnCue · 群聊试映室 0.4.4 · Local unsigned bundle
Services: storage, matrix.room_info, matrix.read_messages, octos.session.open, octos.turn.start, octos.turn.interrupt
Allowed room: !j6BaOOAvAASFVqB8jDJod9O7F8OgOrFjGcFKMVa0WrI
Run grants these services for this session. Octos turns may use the connected core's tools.
```
**Allowed room 与填入的房间号逐字一致，未被清空** ⇒ 官方修复生效，**本地补丁可彻底弃用**。
截图：`evidence/screenshots/`（`official-*` 系列在生产前采于 :98）。

### 3. 生产换装
按原参数（同 cwd / env / display）重启 `:99` 宿主：
- 新 pid `150001`，`/proc/<pid>/exe` sha256 = `87ed4dcc…`（与构建产物一致）
- `launched rinx as client 1`，`:99` 可访问

## 口径变化

| | 之前 | 现在 |
| --- | --- | --- |
| 宿主版本 | fixed Rinx `0879548` **+ 本地补丁** | **官方 Rinx `c515e5fc9b6d`，零改动** |
| 复现要求 | 需要打我们的补丁 | 用官方 Rinx ≥ `bb2a4d4` 即可 |
