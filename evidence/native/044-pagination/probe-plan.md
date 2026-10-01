# probe-plan.md — 最小 probe 计划（宿主就绪后执行）

> ## **未运行**
> 本计划**尚未执行**。本次修复期间宿主 / cardhost / Rinx 均不可用，
> 且任务硬约束禁止启动宿主、禁止 `cargo`、禁止 stamp/sign/publish。
> 因此下面所有"期望值"都是**依据已核实 API 推导出的预期**，不是实测结果。
> 任何一条与预期不符，都必须先回来改 `main.splash`，再继续后面的用例。

---

## 0. 前置条件

1. 宿主可用（cardhost / Rinx 之类的 OctoScript 宿主已就绪），且能加载
   `/root/hackthon/OnCue/oncue/bundle/main.splash` 这个包。
2. 有一个能执行 OctoScript 的最小 probe 入口：
   一个只含 probe 代码的 `probe.splash`（**不要**直接改 `main.splash` 做实验），
   或宿主提供的 REPL / 日志查看方式。
3. 日志可见：probe 结果通过 `log(...)` 或 `ui.<label>.set_text(...)` 打印出来，
   否则无法读数。

## 1. Probe 1 — 语义基础：`len()` 是字节、`to_chars().len()` 是字符

探针代码（最小，仅验证行为，不改产品逻辑）：

```javascript
let s = "汉A🙂"
log("len      = " + s.len())                 // 期望 8
log("chars    = " + s.to_chars().len())      // 期望 3
log("bytes    = " + s.to_bytes().len())      // 期望 8（与 len 相同，交叉验证）
```

| 表达式 | 期望值 | 依据 |
| --- | --- | --- |
| `"汉A🙂".len()` | **8** | string.rs:89-100 → Rust `str.len()`（UTF-8 字节） |
| `"汉A🙂".to_chars().len()` | **3** | string_heap.rs:580-618 → `str.chars()` 逐个转 u32 |
| `"汉A🙂".to_bytes().len()` | 8 | 与 `len()` 同为字节口径（交叉验证） |

**判据**：三个数分别是 8 / 3 / 8。若 `to_chars().len()` 不是 3（例如返回 8），
说明该 revision 的 `to_chars` 语义与已核对依据不一致，必须停下回报，
不得带着错误假设继续。

## 2. Probe 2 — typed U32 页缓冲的往返一致性（核心）

与 `cue_paginate` 使用**完全相同的构造方式**造页缓冲，验证
"拼接后逐字符等于原文"：

```javascript
let src = "汉A🙂"                       // 3 个码点 / 8 字节
let chars = src.to_chars()              // typed U32
let page = "".to_chars()                // typed U32 页缓冲
for i in chars.len() {
    page.push(chars[i])                 // 只 push 码点
}
let rebuilt = page.to_string()          // U32 → char::from_u32
log("rebuilt = " + rebuilt)
log("equal   = " + (rebuilt == src))    // 期望 true
log("raw     = " + page.to_string().len())     // 期望 8（len() 是**字节**，不是字符！）
```

| 检查 | 期望 | 依据 |
| --- | --- | --- |
| `rebuilt == src` | **true** | array.rs:459-482 的 `Self::U32` 分支 |
| `page.to_string().len()` | **8** | `len()` 是 UTF-8 字节（string.rs:89-100）；`"汉A🙂"` = 3+1+4 = 8。**不是 3** |
| `rebuilt` 打印出来 | `汉A🙂`（不是 `27721` 之类的十进制文本） | 若变成十进制文本，说明页缓冲掉进了 `ScriptValue` 存储 |

> 口径提醒：**字符数要用 `to_chars().len()`，`len()` 一律是字节。**
> 本页第一版表格把这一行写成"期望 3"，是笔误（AI1 2026-10-02 评审 #253 指出），已改为 8；
> 若实测读到 3，说明测的是 `to_chars().len()`，探针取错了表达式。

## 3. Probe 3 — 反证：普通 `[]` 缓冲会输出十进制文本（证明硬规则的必要性）

```javascript
let bad = []
let c = "汉A🙂".to_chars()          // typed U32：这一步没问题
for i in c.len() { bad.push(c[i]) } // 但 push 进普通字面量 []，落成 ScriptValue 存储
log("bad = " + bad.to_string())     // 期望：不是 "汉A🙂"，而是十进制数字文本
```

**判据**：`bad.to_string()` 与原文**不相等**（输出十进制数字）。
这一条的作用是证明"页缓冲必须保留 typed U32 来源"不是洁癖，而是必需的；
若这一条反而相等，说明该 revision 的 `cast_to_string` 行为与
`array.rs:463-467`（`Self::ScriptValue` → `heap.cast_to_string`）不符，需要回报。

> 第一版这里写了 `bad.push(""[0].to_chars().len())` 作为"例子"——那是错的：
> `""[0]` 对空串取下标会越界，而且同一个 `let bad` 声明了两次。
> 已删除错误示例，只保留上面这段干净的反证（AI1 2026-10-02 评审 #253 指出）。

## 4. Probe 4 — 分页器端到端（只读，不动产品代码路径）

把 `cue_paginate` 的逻辑原样复制进 probe（同一份源码，避免偏差），喂入
`fixtures/` 里的文本，逐页打印并累加，检查：

```javascript
let src = <读入 fixtures/01-long-single-line-zh.txt 的内容>
let pages = cue_paginate(src, 5)
let joined = ""
for i in pages.len() { joined += pages[i] }
log("pages = " + pages.len())
log("joined == src : " + (joined == src))     // 期望 true
log("joined.len() == src.len() : " + (joined.len() == src.len()))
```

| fixtures | 页数预算 | 必须成立 |
| --- | --- | --- |
| `01-long-single-line-zh.txt` | 5 | `joined == src` |
| `02-continuous-ascii.txt` | 5 | `joined == src` |
| `03-continuous-spaces.txt` | 5 | `joined == src` |
| `04-multiline-ab.txt` 与 `"\n" + draft` 的拼接 | 5 | `joined == src` |
| `05-long-dialogue.txt` | 5 | `joined == src` |
| `06-emoji-combining.txt` | 5 | `joined == src` |
| `07-space-boundary.txt` | 4 | `joined == src` |
| `08-minimal.txt` | 4 | `joined == src` |

其中 `joined == src` 在 OctoScript 里就是字符串的 `==` 比较；若宿主不提供
字符串相等比较，退化为 `joined.len() == src.len() && joined.to_chars().len() == src.to_chars().len()`，
并逐码点比较：

```javascript
let a = joined.to_chars()
let b = src.to_chars()
let same = a.len() == b.len()
for i in a.len() { if a[i] != b[i] { same = false } }
log("codepoint-equal: " + same)      // 期望 true
```

## 5. Probe 5 — `240 字` 口径

```javascript
let zh120 = "字".repeat(120)      // 120 个汉字 = 360 字节
log("zh120.to_chars().len() = " + zh120.to_chars().len())   // 期望 120
log("zh120.len()             = " + zh120.len())             // 期望 360
```

判据：`cue_rehearse` 的守卫 `trial.to_chars().len() > 240` 对 120 个汉字
**不应**触发（修复前 `trial.len() = 360 > 240` 会误触发）。

## 6. 通过标准

1. Probe 1 三个数 = 8 / 3 / 8。
2. Probe 2 `rebuilt == src` 为 true 且 `rebuilt` 是人话（`汉A🙂`）。
3. Probe 3 的普通 `[]` 缓冲确实输出十进制文本（反证成立）。
4. Probe 4 全部 fixtures `joined == src`（或码点级相等）为 true。
5. Probe 5：120 个汉字不被 240 限制误伤。

任一条不通过：停下来回报主控，不要继续 `test-plan.md` 的人工核对。
