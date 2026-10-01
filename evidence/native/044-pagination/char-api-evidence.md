# char-api-evidence.md — 字符 API 依据与"逐字符相等"论证

- 目标源文件：`/root/hackthon/OnCue/oncue/bundle/main.splash`（唯一被修改的仓库文件）
- 依据来源：固定 revision 的 makepad 源码（只读）
  `/opt/src/OctoSense/.sources/makepad/`，revision
  `1f3b1dedfbb81424eb8dbf69e5e2c634fa73dc54`
- 本文所有行号与片段均为在当前 checkout 上重新读取核对的结果。

---

## 1. 五条已核实依据（原文引用）

### 依据 1 — `string.to_chars()` 注册 → `string_to_chars_array`

`platform/script/src/string.rs:77-87`

```rust
        native.add_type_method(
            heap,
            ScriptValueType::REDUX_STRING,
            id!(to_chars),
            &[],
            |vm, args| {
                let sself = script_value!(vm, args.self);
                vm.bx.heap.string_to_chars_array(sself).into()
            },
        );
```

结论：脚本里 `"任意字符串".to_chars()` 得到的是一个**数组**（`ScriptArray`），
元素由宿主逐个字符产生（见依据 3）。

### 依据 2 — `string.len()` 是 Rust `str.len()`，即 UTF-8 字节数

`platform/script/src/string.rs:89-100`

```rust
        native.add_type_method(
            heap,
            ScriptValueType::REDUX_STRING,
            id!(len),
            &[],
            |vm, args| {
                let sself = script_value!(vm, args.self);
                if let Some(len) = vm.bx.heap.string_with(sself, |_heap, s| s.len()) {
                    return (len as f64).into();
                }
```

结论：`"汉A🙂".len()` = 3 + 1 + 4 = **8**（字节），不是 3（字符）。
这正是 `cue_rehearse` 原来 `trial.len() > 240` 与文案"240 字"不一致的根因
（中文台词 121 字就有 363 字节，会被误判超限）。修复见第 3 节。

### 依据 3 — `string_to_chars_array`：`str.chars()` 逐字符转 `u32`，存为 `ScriptArrayStorage::U32`

`platform/script/src/string_heap.rs:580-618`（节选）

```rust
    pub fn string_to_chars_array(&mut self, v: ScriptValue) -> ScriptArray {
        let arr = self.new_array();
        ...
        if v.as_inline_string(|str| {
            let array = &mut self.arrays[arr];
            if let ScriptArrayStorage::U32(v) = &mut array.storage {
                v.clear();
                for c in str.chars() {
                    v.push(c as u32)
                }
            } else {
                array.storage = ScriptArrayStorage::U32(str.chars().map(|c| c as u32).collect());
            }
        })
        ...
        return arr;
    }
```

结论：`to_chars()` 的存储类型固定为 **U32 有类型数组**，元素是 Unicode 码点
（`c as u32`），**不是字节**。这是"页缓冲必须从 `"".to_chars()` 起"的原因。

### 依据 4 — `array.to_string()` 对 `U32` 存储逐元素 `char::from_u32` 还原字符

`platform/script/src/array.rs:459-482`（节选，`ScriptArrayStorage::to_string`）

```rust
    pub fn to_string(&self, heap: &ScriptHeap, s: &mut String) {
        match self {
            Self::U8(bytes) => {
                let v = String::from_utf8_lossy(bytes);
                s.push_str(v.as_ref());
            }
            Self::ScriptValue(vec) => {
                for v in vec {
                    heap.cast_to_string(*v, s);      // ← 数字会被格式化成十进制文本
                }
            }
            ...
            Self::U32(v) => {
                for v in v {
                    if let Some(c) = std::char::from_u32(*v) {
                        s.push(c)                   // ← 正确路径：码点还原成字符
                    }
                }
            }
```

结论（硬规则的来源）：

- 页缓冲若是 **U32** 存储 → `to_string()` 走 `char::from_u32`，**逐字符还原**。
- 页缓冲若是普通 `[]`（`ScriptValue` 存储）→ `to_string()` 走 `cast_to_string`，
  数字会变成十进制文本（例如 `[104, 105]` → `"104105"` 之类），**绝不可用**。

### 依据 5 — 数组 `to_string` 的方法注册（脚本侧调用形态）

`platform/script/src/array.rs:536-556`（节选）

```rust
        native.add_type_method(
            heap,
            ScriptValueType::REDUX_ARRAY,
            id!(to_string),
            &[],
            |vm, args| {
                if let Some(arr) = script_value!(vm, args.self).as_array() {
                    let max_len = vm
                        .bx
                        .heap
                        .array_storage(arr)
                        .to_string_len_upper_bound(&vm.bx.heap);
                    return vm
                        .bx
                        .heap
                        .new_string_with_preflight(max_len, "converting an array to a string", |heap, s| {
                            heap.array_storage(arr).to_string(heap, s);
                        })
                        .into();
                }
```

结论：脚本里 `arr.to_string()` 可用，且结果与存储类型相关（依据 4）。

### 补充依据 A — `array.push()` 保持 U32 存储类型

`platform/script/src/array.rs:327-334`

```rust
    pub fn push(&mut self, value: ScriptValue) {
        match self {
            Self::ScriptValue(v) => v.push_back(value),
            Self::F32(v) => v.push(value.as_f64().unwrap_or(0.0) as f32),
            Self::U32(v) => v.push(value.as_f64().unwrap_or(0.0) as u32),   // ← U32 页缓冲可继续 push
            ...
```

结论：从 `"".to_chars()`（U32）起 `push(码点)`，存储类型不变，仍走依据 4 的
`char::from_u32` 还原路径。`push` 的脚本侧注册见 `array.rs:626-639`
（`id!(push)`，`array_push_vec`）。

### 补充依据 B — 数组 `len()` 是元素个数（不是字节数）

`platform/script/src/array.rs:679-690`（`id!(len)` → `vm.bx.heap.array_len(sself)`）；
数组索引用 `ScriptArrayStorage::index`（`array.rs:254+`，U32 分支返回元素本身）。
比较运算走 `Opcode::GEQ/LT/...` → `handle_f64_cmp_op`
（`opcodes.rs:92-95`），即按 f64 数值比较，因此 `c == 10`、`c >= 9472` 这类
码点比较可以正常工作。

### 补充依据 C — 视觉行模型（为什么"每页行数"是硬上界）

`draw/src/text/layouter.rs:375-400`（`layout_multiline`）

```rust
    fn layout_multiline(mut self) -> LaidoutText {
        ...
        for (line_index, len) in self
            .text
            .clone()
            .split('\n')
            .map(|line| line.len())
            .enumerate()
        {
            if line_index != 0 {
                self.finish_current_row(true, false);   // 每个 \n 强制结束一行
            }
            ...
            self.layout(len);                            // 段内按宽度折行
        }
        ...
            self.finish_current_row(false, false);
            self.finish_with(false)
```

结论：渲染器先把文本按 `\n` 切段，段内按宽度折行，**收尾的空段也算一行**。
本项目的分页器 `cue_paginate` 用同一条模型计数，因此"每页视觉行数 ≤ page_rows"
不是估计值，而是与排版模型一致的判定。

---

## 2. 分页 / 拼接函数为何满足"逐字符等于原始输入"

### 2.1 代码（`main.splash`）

```javascript
fn cue_is_wide(c){
    if c >= 9472 { return true }                 // 0x2500 起：符号 / dingbats / CJK / 假名 / 全角
    if c >= 126976 && c <= 129791 { return true } // 0x1F300-0x1FAFF emoji
    false
}
fn cue_paginate(text, page_rows){
    let chars = text.to_chars()          // 依据 3：typed U32 码点数组
    let total = chars.len()              // 依据 B：元素个数 = 码点数
    let pages = []
    if total == 0 { pages.push("") return pages }
    let page = "".to_chars()             // 依据 3：新页缓冲同样是 typed U32
    let cols = 0
    let rows = 1
    for i in total {
        let c = chars[i]                 // 依据 B：U32 数组索引返回码点
        if c == 10 {
            if rows >= page_rows { pages.push(page.to_string()) page = "".to_chars() rows = 1 cols = 0 }
            page.push(c)                 // 依据 A：push 码点，存储类型仍为 U32
            cols = 0
            if rows >= page_rows { pages.push(page.to_string()) page = "".to_chars() rows = 1 cols = 0 }
            else { rows += 1 }
        } else {
            let w = 1
            if cue_is_wide(c) { w = 2 }
            if cols + w > cue_page_cols {
                if rows >= page_rows { pages.push(page.to_string()) page = "".to_chars() rows = 1 cols = 0 }
                else { rows += 1 cols = 0 }
            }
            page.push(c)                 // 依据 A
            cols += w
        }
    }
    if page.len() > 0 { pages.push(page.to_string()) }   // 依据 4：U32 → char::from_u32
    pages
}
```

调用点只有两处（阅读区与原消息各一套页缓存）：

```javascript
cue_ws_pages  = cue_paginate(cue_ws_text(),  cue_page_rows)   // 对白/建议、摘要、A/B 共用入口
cue_msg_pages = cue_paginate(s.body,         cue_msg_rows)     // 原消息正文
```

### 2.2 不变量证明

设输入 `T = t₁ t₂ … tₙ`（`tᵢ` 为 Unicode 码点），`n = T.to_chars().len()`。

1. **每个码点恰好被 push 一次**：`for i in total` 遍历 `0 … n-1`，每次迭代取
   `c = chars[i]`，两条分支（`c == 10` / 否则）都只执行一次 `page.push(c)`，
   且循环体内没有 `continue`/提前退出。
2. **顺序不变**：push 的顺序就是 `i` 的递增顺序。
3. **页与页的边界只落在两个码点之间**：`pages.push(page.to_string())` 只把
   *已经 push 过* 的码点结算掉，随后的 `page = "".to_chars()` 开始空缓冲；
   当前码点若已 push 则属于新页，若未 push 则随后被 push 进新页。
   因此没有任何码点被跳过、重复或跨页。
4. **U32 → 字符串是码点的逆映射**：依据 4 的 `Self::U32(v) => char::from_u32(*v)`。
   对合法 UTF-8 字符串（脚本字符串必然合法），`str.chars()` 产生的每个码点
   `char::from_u32` 必返回原字符，`s.push(c)` 写回的字节与原字节一致。
5. **合成**：把所有页按产生顺序拼接，得到的码点序列与 `T` 相同，
   即 `pages[0] + pages[1] + … == T`，且这是**字符级**相等（不是字节近似）。
6. **不 trim**：没有对页内容做任何 `trim()`、`strip()`、空白裁剪；
   空格、换行、Tab 原样保留（目标 7 的"保留原有换行与空格"）。
7. **不使用字节切片**：全程没有 `str` 切片 / 下标 / 截断操作，
   不存在切断 UTF-8 多字节序列的可能（目标 6）。

### 2.3 视觉行上界（目标 3 / 目标 5）

- 折行判定与排版模型（依据 C）同源：`\n` 强制结束一行；非换行符按
  `cols + w > cue_page_cols`（`cue_page_cols = 11` 显示列，CJK/emoji 记 2 列）
  软折行。宽度启发式**只可能偏保守**：偏多算 → 提前折行；偏少算 → 渲染器多折一行，
  两种情况都不改变字符内容。
- 每页占用的视觉行数上限就是 `page_rows`
  （阅读区 `cue_page_rows = 5`，原消息 `cue_msg_rows = 4`）。
- 因此阅读区内容高度有确定上界，配合 `RoundedView{height: Fill}` + 阅读区
  `View{height: Fit}` 的布局，以及按钮行/状态行都是 `height: Fit`
  （位于阅读区上方/最底部，不重叠），满足"状态行与操作按钮不得遮挡正文"。
- 例外：源文本自身以 `\n` 结尾时，**最后一页**可能多出一条空行
  （依据 C 的"收尾空段也算一行"），即最后一页最多 `page_rows + 1` 行；
  版面仍留有 ≥1 行的余量（见 `test-plan.md` 的高度预算）。

### 2.4 离线自查结果（不是宿主运行结果）

`fixtures/simulate_paginate.py` 用 Python 逐行复刻 `cue_paginate`，
对 8 个 fixtures + 3 个真实路径上的组合文本（`body + "\n" + draft`）验证：
**"所有页拼接后 == 原始输入"全部 PASS，每页视觉行数 ≤ 预算全部 PASS，
无空中间页**。另做了 12000 组随机文本 × 预算 {2,3,4,5,6} 的 fuzz，
同样全部通过（唯一"失败"是空输入返回单页空串，这是设计行为）。
**这只是算法层面的自查，不是 OctoScript 运行结果**；宿主就绪后必须按
`probe-plan.md` 复核。

---

## 3. 额外修复：`cue_rehearse` 的 240 限制与文案口径

### 问题

原代码：

```javascript
if trial.len() > 240 { cue_set_status("先把台词缩到 240 字以内。") return }
```

依据 2：`string.len()` 是 **UTF-8 字节数**。于是：

- 120 个汉字 = 360 字节 > 240 → 被拒，但用户明明只写了 120 字；
- 240 个 ASCII 字母 = 240 字节 → 通过，但用户写了 240"字"，口径也不对。

### 选择

**改为按字符数判断，文案保持"240 字"**：

```javascript
if trial.to_chars().len() > 240 { cue_set_status("先把台词缩到 240 字以内。") return }
```

### 依据与理由

1. 文案面向用户，语义是"字"；中文场景下 240 个汉字是合理的"一句想接的话"上限，
   240 **字节**只有 80 个汉字，会把正常长度的台词全部拒掉——这是真实缺陷。
2. 与同一文件里的模型约束口径一致：`cue_prompt` 里写的是
   "每条建议台词最多150字，全文最多1000字"（也是字数口径）。
3. `to_chars().len()` 依据 3 + 补充依据 B：元素个数就是 Unicode 码点数，
   中文/英文/emoji 都按"一个字符"计，与用户对"字"的直觉一致。
4. 代价（已记录在风险里）：码点数 ≠ 字素簇（grapheme）数，
   例如 `é` 写成 `e + U+0301` 时算 2 个码点，比用户感知的"1 个字"略严；
   但这是**偏严**方向，不会让超长文本通过，安全。
5. 备选方案（把文案改成"240 字节"）被否掉：会把"80 个汉字"当成上限，
   与"一句想接的话"的产品语义和模型侧 150 字/1000 字的约束都不搭。
