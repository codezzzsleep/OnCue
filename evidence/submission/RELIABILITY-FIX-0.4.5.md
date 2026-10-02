# 可靠性修复 0.4.4 → 0.4.5：七块解析被首尾分隔符误判

> 官方评分维度含「**可靠运行**」（`octosense-scenario-update-plan.md:85`）。
> 本修复针对一个**在真机上必然复现**的解析缺陷。

## 现象

在赛事服务器 `matrix.rinx.chat` 上运行 `0.4.4`，点「试映下一幕」连续两次得到：

> **`Agent 尚未形成七块完整剧本，请再试一次。`**

而内核日志显示 Agent **每次都成功返回**：
```
turn: LLM response received iteration=1 stop_reason=EndTurn tool_calls=0 response_content_len=2111
turn: LLM response received iteration=1 stop_reason=EndTurn tool_calls=0 response_content_len=2244
turn: LLM response received iteration=1 stop_reason=EndTurn tool_calls=0 response_content_len=2493
```
→ **不是模型的问题，是应用解析的问题。**

## 根因（有逐字节证据）

从内核 ledger 取出该次回复，开头与结尾分别是：
```
开头 repr: '@@@\n现场摘要：提议明早9点出发+杭州住一晚，与原消息"希望当天回来"存在冲突；…'
结尾 repr: '…预算500/人封顶，开车还缺一个人，谁方便？\n@@@'
```
即模型把七块**整体多包了一层 `@@@`**。

`0.4.4` 的 `cue_split_blocks` 对**每一个** `@@@` 行都 `push` 当前块（哪怕是空块），于是：

| 块 | 内容 |
| --- | --- |
| 1 | **（空）** ← 开头的 `@@@` 造成 |
| 2 | 现场摘要 |
| 3–8 | 路线 A/B/C 的正文与台词 |
| 9 | **（空）** ← 结尾的 `@@@` 造成 |

→ `blocks.len() == 9 != 7` → 报错，**尽管内容完全正确**。

## 修复（两级，因为模型输出格式不止一种写法）

实测发现模型有两种写法：
1. `@@@` **独占一行**，且常在首尾各多写一个；
2. `@@@` **直接贴在上一块末尾**（`"…住一晚？@@@\n【路线A…"`，全篇 0 个独占行，但 `@@@` 恰好 6 个）。

只处理第 1 种仍会失败，所以 `cue_split_blocks` 改成**两级容错**：
先按"独占一行"严格切；得不到七块就退回按**任意位置的 `@@@`** 松切。
两条路径都丢弃空块，且都要求**恰好七个非空块**。

### 第一级：过滤空块
```diff
         if line.trim() == "@@@" {
-            blocks.push(block.trim())
+            if block.trim() != "" { blocks.push(block.trim()) }
             block = ""
         } else {
             if block != "" { block += "\n" }
             block += line
         }
     }
-    blocks.push(block.trim())
+    if block.trim() != "" { blocks.push(block.trim()) }
     blocks
```
### 第二级：退回松切
```splash
fn cue_split_blocks(text){
    let strict = cue_split_strict(text)
    if strict.len() == 7 { return strict }
    cue_split_loose(text)
}
```
`cue_split_loose` 用 `text.split("@@@")` 取所有非空片段。

**仍然严格校验恰好七个非空块**（中间缺块 → 少于 7 → 照样报错），
既不把首尾的包装分隔符当成一块，也不因为 `@@@` 没换行就让用户重试。

## 验证

| 项 | 结果 |
| --- | --- |
| 历史 5 条**完整**模型回复回放 | 全部 **7 块通过**（含首尾包装型 834/927 字、内联分隔型 517 字、标准型 651/787 字） |
| Python 逐字复算 vs 真机 | 一致 |
| `hub check --publisher-key`（0.4.5） | **PASSED** |
| `tools/octo check`（未签名副本） | **PASSED**（仅未签名警告） |
| 真机复测（Rinx，`matrix.rinx.chat`） | 点「试映下一幕」→ **`现场摘要已就绪，点"摘要"可逐页读完；以下是 Agent 的假设排练，原消息仍在上方。`** |

## 版本与凭据
- 版本：`0.4.4` → **`0.4.5`**（gate 的 `version`/`continuity` 要求每次发布新版本）
- digest：`2b01ae050c6110a4921303ec18ca07949e1ffd6083db0fd77431a577f182111a`
  → **`055c5fd806055f74fc13fa9f1acefabfa3079079153137adc971ae80079684a1`**
- 已重新 `stamp` + `sign-manifest`（发布者 `oncue.dev`，密钥始终在仓库外）

## 追加：自动重试（同一版本内）

即使兼容了两种分隔符写法，模型仍会偶发地给出**真正不合协议**的回复（实测有一次点「试映下一幕」
得到 `Agent 尚未形成七块完整剧本，请再试一次。`）。让用户为偶发的模型抖动反复手点不合理。

改为：解析不通过时**自动重试一次**，仍不通过才提示用户。
- `cue_start_turn(prompt_text, request_revision, attempt)` 负责发回合
- `cue_accept_reply(reply, request_revision, attempt)` 负责解析；不通过且 `attempt < 1` 时自动重发
- 重试期间保持 busy 状态，用户可随时点「停止等待」中断
- 两次都不通过 → 保留原来的提示文案，不静默吞掉失败
