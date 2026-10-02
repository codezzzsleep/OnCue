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

## 修复

`oncue/bundle/main.splash` 的 `cue_split_blocks`：**推入前过滤空块**。
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
**仍然严格校验恰好七个非空块**（中间缺块 → 少于 7 → 照样报错），只是不再把首尾的包装分隔符当成一块。

## 验证

| 项 | 结果 |
| --- | --- |
| 用同一份 ledger 回复复算 | 修前 9 块（判失败）→ **修后 7 块（判通过）** |
| `hub check --publisher-key`（0.4.5） | **PASSED** |
| `tools/octo check`（未签名副本） | **PASSED**（仅未签名警告） |
| 真机复测（Rinx，`matrix.rinx.chat`） | 点「试映下一幕」→ **`现场摘要已就绪，点"摘要"可逐页读完；以下是 Agent 的假设排练，原消息仍在上方。`** |

## 版本与凭据
- 版本：`0.4.4` → **`0.4.5`**（gate 的 `version`/`continuity` 要求每次发布新版本）
- digest：`2b01ae050c6110a4921303ec18ca07949e1ffd6083db0fd77431a577f182111a`
  → **`055c5fd806055f74fc13fa9f1acefabfa3079079153137adc971ae80079684a1`**
- 已重新 `stamp` + `sign-manifest`（发布者 `oncue.dev`，密钥始终在仓库外）
