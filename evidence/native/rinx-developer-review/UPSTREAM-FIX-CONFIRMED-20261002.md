# 关键简化：我们的 room-lookup 补丁**已在上游 Rinx 中**

记录时间：2026-10-02（只读核对，未改任何宿主、未重建）

## 事实

我们此前一直在交付里标注 **"fixed Rinx 0879548 + local lookup patch"**，
补丁内容是把 mini app import 面板里含混的 `ids!(room)` 改成 `ids!(import_form.room)`（4 处）。

**核对上游 `hagency-org/Rinx` 后发现该修复早已合入：**

| 项 | 值 |
| --- | --- |
| 上游提交 | `bb2a4d4df7d0`（2026-10-01）**"fix: disambiguate mini app import room widget paths (#48)"** |
| 对应 PR | [#48](https://github.com/hagency-org/Rinx/pull/48) "fix: preserve attached room when reviewing imported mini apps" |
| 合并时间 | 2026-10-01T15:58:42Z |
| 上游最新 main | `c515e5fc9b6d`（2026-10-02，Merge PR #50） |

**上游 `main` 的 `src/miniapps/ui.rs` 实测：**
```
ids!(import_form.room) 出现 5 次    （第 221 / 329 / 352 / 735 / 904 行）
ids!(room)             只剩 1 次    （第 901 行附近，带注释解释为何这里是通用的）
```
第 901 行附近上游自己写了注释：
> `// The hidden Hub also has a `room` DropDown. Generic ids!(room)`

即上游用**与我们相同的思路**（消歧 mini app import 面板里的 room 控件路径）修掉了同一个 bug。

## 影响（对交付口径）

1. **交付不再需要自带补丁**：可改为"用**官方 Rinx `main`（≥ `bb2a4d4`，即 PR #48 之后）** 即可复现"。
   这比"附自定义补丁 + 说明如何打"干净得多，也正是主办方说的"可以更新 octosense 项目最新修改"。
2. **此前的限定语需要更新**：`fixed Rinx 0879548 + local lookup patch` → 应改为
   **官方 Rinx ≥ `bb2a4d4`（PR #48）**；历史证据里的旧限定语保留作溯源。
3. **本机现状未改**：`/opt/src/OctoSense/target/release/octosense` 仍是我们基于
   `/tmp/rinx-0879548-fixed` 构建的产物（sha256 `3800efbc…`）；官方产物备份在
   `/root/oncue-runtime/backup/octosense-official-20261002`。**是否改用上游重建，待指示。**

## 未做

- **未重新构建宿主**、未替换运行中的二进制、未改任何 Rinx 源码或数据；
- 本节全部为只读核对（HTTP GET 上游 raw/API）。
