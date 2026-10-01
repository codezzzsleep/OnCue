# 0.4.1 低配额失败反馈验证（官方 card-host + 隔离 app id，仓库外诊断）

日期：2026-10-01。目的：按 AI1 #142/#149 的要求，验证 0.4.1 的 `try/catch` 失败反馈**在容量不足时真的可达**，
且要求「失败反馈 + 编辑框内容保留 + 目标文件未创建」，**不触碰 `state/hub-mirror/`**、**不预写 consent**。
本文件不含任何凭据内容。

## 1. 方法（全部在仓库外 / 独立显示上）

| 项 | 值 |
| --- | --- |
| 官方工具 | `tools/octo doctor`（`/root/kaggle/OctoScript-App-Design-Flow/tools/octo`），以 `OCTO_HUB` / `OCTO_CARD_HOST` **复用已构建二进制**，未重编译 |
| card-host | `/tmp/hubbuild/card-host/target/release/card-host`（其 makepad pin 与宿主同为 `1f3b1dedfbb81424eb8dbf69e5e2c634fa73dc54`） |
| 探针包 | `/tmp/oncue-probe-lowquota`（由 `oncue/bundle` 复制，**仅改 manifest.json**：`id` → `oncue-lowquota-probe`、`name` → `OnCue 存储探针`、`storage.max_bytes` → `64`、移除 `integrity.signature`） |
| app-data | `/tmp/oncue-probe-data`（jail：`/tmp/oncue-probe-data/oncue-lowquota-probe`） |
| 显示 | 独立 **Xvfb :98**（不占用 OctoSense 所在的 `:99`），`--size 990x613`，桥 `MAKEPAD_REMOTE=18152` |
| 启动 | `DISPLAY=:98 card-host --bundle /tmp/oncue-probe-lowquota --app-data /tmp/oncue-probe-data --allow-unsigned --stamp --size 990x613` |

操作要点：**每次点击前重新取 `/snap`**，用该次快照的控件坐标点击（本实例宽布局：六按钮排 `y=205`、
路线排 `y=249`（最右 56 宽者为「用这句」）、播放排 `y=293`）。

## 2. 实际 admitted 的有效配额（关键前提）

```
card-host: stamped /tmp/oncue-probe-lowquota/manifest.json with digest 8d00e9861335dac70d5474f9a4c15477e8d7ef352ce7bafd947e0d9dd479d8d6
card-host: oncue-lowquota-probe 0.4.1 admitted — capabilities {"matrix.read_messages","matrix.room_info","octos.session.open","octos.turn.interrupt","octos.turn.start","storage"}, hosts {}, storage 64 bytes, agent none
card-host: isolate jailed at /tmp/oncue-probe-data/oncue-lowquota-probe with 64 bytes, 6 capability(ies), 1 host(s), 8000000 instructions, 33554432 bytes of heap, prompts false — all enforced
```

→ **隔离 app id + 小配额在本路径确实生效**（这正是卡片路径做不到的：那里策略来自已验证 catalog 条目，见
`evidence/native/041-lowquota-and-incident.md` §2）。

## 3. 失败路径实测（状态原文照抄）

| 步骤 | `cue_status` 原文 | `cue_draft` 长度 | jail 文件 |
| --- | --- | --- | --- |
| 初始 | 虚构群聊与预设路线，仅供体验玩法。 | 0 | `[]` |
| 试映下一幕 | 样例预设已展开；这些对白不是对真实群友的预测。 | 0 | `[]` |
| 选第一条路线 | 已选「顺着这句」；点击播放或下一句展开假设对白。 | 0 | `[]` |
| 用这句 | 台词已放进草稿，可以继续修改；尚未发送。 | **37** | `[]` |
| **存A** | **版本 A没有保存完成；编辑框内容仍在。请检查应用存储空间，再重试。** | **37** | **`[]`** |
| **保留这句** | **草稿没有保存完成；编辑框内容仍在。请检查应用存储空间，再重试。** | **37** | **`[]`** |

结论：**失败反馈可达**；**编辑框内容保留**（37 字符未被清空）；**目标文件未创建**（jail 全程为空）。

## 4. 附带观察（供后续版本与 QA 参考）

1. 状态文案缺一个空格：「版本 A**没有**保存完成」——由 `"版本 " + label` 与 `label + "没有保存完成…"` 拼接产生，建议下一版改为「版本 A 没有保存完成」。
2. **窄布局裁剪**：`--size 412x892` 时，草稿六按钮只显示前三个（保留这句/取回草稿/存A），**存B/取A/取B 被挤出可视区**；`990x613` 下六个齐全。若要在窄视口验收 A/B 存取，需要先调布局。
3. 本次 990×613 探针里播放可正常展开，窄布局那次还出现过完成态文案
   「这条假设路线已播完。可以改台词、换路线，或把建议放进草稿。」——**0.4.1 的完成状态是真实存在的**
   （0.3.1 那次复核的争议仅限旧帧，见 `evidence/native/AI2-recheck-031-playback-report.txt`）。
4. 操作坑（记录以免重犯）：`card-host` 在 **DISPLAY 不存在**时会直接 SIGSEGV（非报错退出）。我最初两次
   "崩溃"就是 Xvfb :98 未真正存活所致；用受管后台任务起 Xvfb 后一切正常。另外 `pkill -f <模式>` 若模式
   与自身命令行匹配会自杀，清理请按 PID。
5. 环境观察（未触碰）：机器上仍有三个早期会话遗留的 `card-host` 进程（`--bundle …/dev/OnCue/oncue/bundle
   --app-data …/state/cardhost`），属历史证据进程，本次未干预。

## 5. 复核命令（可复现）

```bash
# 1) 起独立显示
Xvfb :98 -screen 0 1400x900x24 -nolisten tcp &
# 2) 造探针（仅改 manifest 四处）
cp -a <repo>/oncue/bundle /tmp/oncue-probe-lowquota   # 改 id/name/storage/去签名
# 3) 跑（仓库外、unsigned、隔离 app id）
DISPLAY=:98 MAKEPAD_REMOTE=18152 card-host --bundle /tmp/oncue-probe-lowquota \
  --app-data /tmp/oncue-probe-data --allow-unsigned --stamp --size 990x613
# 4) 驱动：试映 → 选路线 → 用这句 → 存A；读 /snap 的 cue_status.t 与 cue_draft.val，并 `ls` jail
```
