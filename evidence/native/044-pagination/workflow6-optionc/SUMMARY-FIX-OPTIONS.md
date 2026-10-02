# 样例舞台「摘要」死循环：三种候选修法（**均未应用**）

根因：`cue_invalidate()` 清 `cue_summary`（`main.splash:168`）→ `cue_rehearse()` 开头调它 →
demo 路径 `cue_demo_routes()` 不重设 → `cue_show_summary()` 提示"先点试映下一幕"（正是清空它的操作）。

| 方案 | 改动 | 影响面 | 我的评估 |
| --- | --- | --- | --- |
| **a** | 在 `cue_demo_routes()` 里补一句 `cue_summary = "…样例摘要…"` | 仅 demo 路径；与真实 Agent 路径（`blocks[0]`）对称 | **推荐**：最小、语义清楚、不动清空逻辑 |
| b | 把清 `cue_summary` 从 `cue_invalidate()` 挪到"真实读取新房间时" | 动的是公共函数，影响所有路径 | 风险较大：`cue_invalidate` 被多处调用，容易漏 |
| c | 只改提示文案（不再指向"试映下一幕"） | 最小，但**摘要仍不可达** | 只治提示不治功能，不推荐单独用 |

**a 与 c 可同时做**（a 修功能，c 修提示），我倾向 "a + c"。
三种都会改 bundle 内容与 digest，**等 AI1 指示后再应用**。
