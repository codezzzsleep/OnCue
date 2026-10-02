# 发现：样例舞台下「摘要」在试映后不可达（提示自相矛盾）

**限定**：fixed Rinx 0879548 + local lookup patch；本缺陷在产品代码里，与宿主补丁无关。
发现方式：把 `cue_summary.to_chars().len()` 用只读探针逐步落盘（不改产品逻辑）。

## 实测（探针逐步落盘）

```
sum-a  init                summary_len=63  mode=0  demo=true
sum-b  after_show_demo     summary_len=63
sum-c  after_show_summary  summary_len=63  mode=1     <- 摘要阅读路径本身正常
sum-d  after_rehearse      summary_len=0   mode=0     <- 试映下一幕把它清空
```

## 根因（源码）

1. `cue_invalidate()` 里有 `cue_summary = ""`（`main.splash:168`）；
2. `cue_rehearse()` **开头就调用** `cue_invalidate()`；
3. 样例舞台路径走 `cue_demo_routes()`，**它不重新设置 `cue_summary`**
   （只有真实 Agent 路径在解析七块时用 `cue_summary = blocks[0]`，见 `main.splash:359`）。

## 后果

- 在样例舞台上点过 `试映下一幕` 之后，`摘要` **永远进不去**；
- 而 `cue_show_summary()` 给的提示是 **"还没有现场摘要：先点'试映下一幕'。"** ——
  **这正是让摘要保持为空的操作**，构成**自相矛盾的死循环提示**（用户按提示做只会更空）。

## 范围（不夸大）

- **只影响样例舞台（demo）路径**；真实 Agent 回合只要七块解析成功，`blocks[0]` 会写回 `cue_summary`，
  摘要可用。
- 不是宿主/Rinx 的问题，也不需要任何补丁环境。

## 建议修法（未擅自实施，等指示）

- 方案 a：样例路径的 `cue_demo_routes()` 里补一句 `cue_summary = ...`（与真实路径对齐）；
- 方案 b：把 `cue_invalidate()` 清 summary 的行为改成"仅在真实读取新房间时清"；
- 方案 c（最小）：把提示文案改成不再指向"试映下一幕"。
**这会改动 bundle 内容与摘要**，所以我没有自行合入 —— 需要你定方案后再 stamp。

## 候选修法（**均未应用**，等指示）

| 方案 | 改动 | 影响面 | 评估 |
| --- | --- | --- | --- |
| **a** | `cue_demo_routes()` 里补 `cue_summary = …` | 仅 demo 路径；与真实 Agent 路径对称 | **推荐** |
| b | 把清 `cue_summary` 从 `cue_invalidate()` 挪到"真实读取新房间时" | 动公共函数，多处调用 | 风险较大 |
| c | 只改提示文案 | 最小，但摘要仍不可达 | 只治提示，不单独用 |

倾向 **a + c**。三种都改 bundle 与 digest，等指示后再应用并只 stamp 一次。
