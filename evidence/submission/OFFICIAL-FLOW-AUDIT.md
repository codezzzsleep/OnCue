# 官方流程逐条核对（读完仓库原文后重做）— 2026-10-02

> 依据：**完整克隆**并以 read 工具逐字读过的仓库
> `gosimfoundation/hackathon-agenticapp26`、`OctoSense-org/OctoScript-App-Design-Flow`
> （含 `AGENTS.md`、`flows/script-app/FLOW.md`、`docs/CAPABILITIES.md`、`docs/PUBLISHING.md`）、
> `OctoSense-org/OctoSense-App-Hub`（`docs/PUBLISHING.md`、`docs/ICONS.md`）。
> 此前的结论是 curl 抓单文件得出的，**不可靠**；本文件以本次通读为准。

## 一、此前遗漏、本次补上的关键要求

| 来源 | 要求 | 此前状态 |
| --- | --- | --- |
| `OctoScript-App-Design-Flow/AGENTS.md` | 有正式的 **Definition of Done（6 条）** 与 **Rules for every app** | **完全没读过** |
| `flows/script-app/FLOW.md` | 官方 **14 步流程**，第 1 步要写 `BRIEF.md` | 没写 |
| `flows/script-app/FLOW.md` | 用 **`tools/octo run/shot/check`** 与**远程桥**（`/click`、`/t`、`/snap`）驱动 | 用的是 XTest + ffmpeg |
| `FLOW.md` 第 13 步 | `hub scan --packet build/review.json` + 七问写入 `build/REVIEW-ANSWERS.md` | 只有零散答案，无 packet |
| `FLOW.md` 第 8 步 | 必须测**空、错误、重启持久化**三种状态 | 只部分做过 |
| `docs/CAPABILITIES.md` | `matrix.*` **仅** Rinx 小程序宿主提供；`octos.*` 由托管内核的 shell 或 Rinx 提供 | 已知 |
| `docs/CAPABILITIES.md` | 商店应用**不要**申请 `prompt`/`llm`/`news`/`glance`/`research`/`crawl`（无服务或零收益） | 未申请 ✓ |
| `docs/CAPABILITIES.md` | 上限：`storage` 16 MiB、`instruction_budget` 2000 万、`memory` 64 MiB | 我们 4 MiB / 800 万 / 32 MiB ✓ |
| `docs/ICONS.md` | 包内总量 ≤ 8 MiB；图标 ≤ 1 MiB 且方形 | 待核 |
| `hackathon.../docs/octosense-scenario-update-plan.md` | **"统一最小交付应能展示：事件或输入 → Agent 理解并形成计划 → 用户查看或授权 → 执行 → 核验结果 → 状态变化或失败处理。仅生成界面、摘要或静态卡片，不足以证明完成了任务自动化。"** | **没读过；对我们的定位有直接影响** |
| 同上 | 即时消息场景**绑定 Rinx**；消息题验收重点：来源可追溯、草稿与已发送状态清楚、发送对象可检查、权限拒绝与过期有反馈 | 未核对 |

## 二、官方 14 步流程逐条现状

| # | 官方步骤 | 现状 |
| --- | --- | --- |
| 1 | 写 `$A/BRIEF.md`（画面/动作/数据/状态/主机/能力+理由） | ✅ 已补 `oncue/BRIEF.md` |
| 2 | `tools/octo new` | ⏭ 包是手写的；`octo doctor` 已通过 |
| 3 | manifest 依 brief | ✅ |
| 4 | `main.splash` 只用可引用的 API | ✅（源码内注明 makepad 出处） |
| 5 | `tools/octo run $B --port $P --hidden --detach` | ✅ 已跑通：`admitted` + `ready: first frame drawn` |
| 6 | `tools/octo shot $P /tmp/first.png` | ❌ **本机不可用**（见第三节 gap） |
| 7 | 用 `/click`、`/t`、`/snap` 驱动每个动作 | ⚠️ `/snap` 可用；交互此前用 XTest 驱动 |
| 8 | 测空、错误、重启持久化 | ⚠️ 部分 |
| 9 | 修到 5–8 全过 | — |
| 10 | 定稿 `listing.json` | ✅ |
| 11 | 驱动到最佳真实状态后 `tools/octo shot` 到 `bundle/screenshots` | ⚠️ 截图用 ffmpeg 抓窗口（因 gap） |
| 12 | `tools/octo check $B` → `— PASSED` | ✅ **已达成**（未签名副本：`oncue-screening-room 0.4.4 — PASSED`，仅未签名警告） |
| 13 | `hub scan --packet build/review.json` + 七问 | ✅ 已补 `build/review.json` 与 `build/REVIEW-ANSWERS.md` |
| 14 | 按 AGENTS.md 格式汇报 | ✅ 见本文件第四节 |

## 三、Gaps found（工具行为与文档不符，含最小复现）

**`tools/octo shot` 在本机平台不可用。**

```
$ . refs/octo-env.sh
$ tools/octo run <bundle> --port 8143 --detach
  ... ready: first frame drawn
$ tools/octo shot 8143 out.png
  octo: GET http://127.0.0.1:8143/g?raw=1 failed: HTTP Error 404

$ curl -s 127.0.0.1:8143/s
  {"app":"card-host","pid":159365,"w":[{"i":0,"t":"Card host [remote]","sz":[412,892],...
$ curl -s 127.0.0.1:8143/g?raw=1
  {"err":"grab timeout (is this backend rendering?)"}
$ curl -s 127.0.0.1:8143/gseq?n=1&every_ms=50
  {"err":"gseq frame 0: grab timeout (is this backend rendering?)"}
```
- 平台：Linux aarch64，Xvfb `:99` 1440x1000，`LIBGL_ALWAYS_SOFTWARE=1` + llvmpipe。
- 窗口确实存在（`xwininfo` 可见 `Card host [remote]` 412x892），`/snap`、`/s/`、`/quit` 均正常，**只有抓帧路由超时**。
- `--hidden` 与不带 `--hidden` 结果相同。
- 变通：直接抓 X11 窗口（`ffmpeg -f x11grab`），README 与证据截图即由此产生。

## 四、按官方格式的汇报

**Verified**
- `tools/octo doctor` → `[ok]` python / App Hub checkout / hub / card-host / cargo / template；`ready: …`
- `tools/octo run … --port 8141 --hidden --detach` → `card-host: oncue-screening-room 0.4.4 admitted …` + `ready: first frame drawn`
- `tools/octo check <未签名副本>` → `oncue-screening-room 0.4.4 — PASSED`（仅 `[warning] publisher-signature: unsigned: accountability rests on the hub alone`）
- `hub scan --packet build/review.json` → `wrote the review packet …; the packet holds 7 questions for one`
- `hub check --publisher-key oncue.dev=50578fd7…`（已签名状态）→ `PASSED`
- 赛事服务器端到端：见 `evidence/submission/RINXCHAT-VERIFICATION.md`

**Not verified**
- `tools/octo shot`（本机抓帧超时，见第三节）
- 未在 macOS / Windows / 移动端验证
- `card-host` **不提供** `matrix.*` / `octos.*`；这两类只能在 Rinx 中验证
- 「接收者独立授权」未演示（本应用不分享、不发送）

**Waiting on a human**
- §9 publisher key 与 `hub sign-manifest`（已完成一次；任何后续编辑都需重新 stamp + 签名）
- §10 打 tag 与在 `OctoSense-App-Hub` 开 `Submit oncue-screening-room 0.4.4` issue

**Gaps found**
- 见第三节。
