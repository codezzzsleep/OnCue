# 0.4.0 草稿写入失败：存储配额根因（脱密）

日期：2026-10-01。本文件只记录路径、数字与源码位置，不含任何凭据内容。

## 1. 现象

同一 Shell 模块（App Hub card 路径），用控件树坐标点击：

| 操作 | 结果 |
| --- | --- |
| 点路线 | 状态变为「已选"换个问法"；点击播放或下一句展开假设对白。」 |
| 点「用这句」 | 草稿值被填入整句台词，状态「台词已放进草稿，可以继续修改；尚未发送。」 |
| 草稿框输入 | 内容确实被修改（…当天ZZ返回…） |
| 点「保留这句」/「存A」/「存B」 | **状态完全不变**；`find` 在 jail 内找不到任何新文件 |
| 点「取A」/「取B」 | 状态分别为「版本 A 还没有内容。」「版本 B 还没有内容。」（只读回调正常） |

所以：六个按钮的 on_click **都被调用了**（取A/取B 的反馈即证据），失败发生在写入阶段。

## 2. 最早异常（宿主日志，脱密）

`state/logs/octosense-rinx.log`，紧跟 OnCue 启动之后连续 6 次：

```
wm: launched hub:oncue-screening-room as client 2 (in-process, card)
card: oncue-screening-room running under 6 capability(ies), 1 host(s), 65536 bytes of storage
[E] splash:<tid>:298:27 - app storage is full (.sources/makepad/widgets/src/splash_storage.rs:306)
[E] splash:<tid>:298:27 - app storage is full (.sources/makepad/widgets/src/splash_storage.rs:306)
[E] splash:<tid>:270:27 - app storage is full (.sources/makepad/widgets/src/splash_storage.rs:306)
[E] splash:<tid>:298:27 - app storage is full (.sources/makepad/widgets/src/splash_storage.rs:306)
[E] splash:<tid>:298:27 - app storage is full (.sources/makepad/widgets/src/splash_storage.rs:306)
[E] splash:<tid>:298:27 - app storage is full (.sources/makepad/widgets/src/splash_storage.rs:306)
```

## 3. 实际占用与配额

| 项 | 值 | 依据 |
| --- | --- | --- |
| jail 根 | `$OCTOSENSE_APP_DATA/<app_id>` = `/srv/oncue-apps/oncue-screening-room` | `crates/shell/src/app_storage/mod.rs:193-198, 210` |
| jail 实际占用 | **181,275 B** | `du -sb` |
| 其中 bundle | **138,649 B** | `du -sb …/bundle` |
| manifest 声明配额 | **65,536 B** | `card: … 65536 bytes of storage`；bundle `manifest.json` |
| 默认上限（未声明时） | 16 MiB | `splash_storage.rs:40 MAX_TOTAL_BYTES` |
| 单文件上限 | 1 MiB | `splash_storage.rs:38 MAX_FILE_BYTES` |
| 条目上限 | 256 | `splash_storage.rs:42 MAX_ENTRIES` |

**结论**：jail 把安装包自己（bundle 138,649 B）算进配额，首帧即超 65,536 B，任何 storage 写入必然失败。

## 4. 写入判定与错误可捕获性（AI1 关注点）

- 判定位置：`.sources/makepad/widgets/src/splash_storage.rs:300-306`，`cap = quota_for_vm(vm)`、`(total, entries) = jail_usage(&root)`，超限即 `script_err_io!(vm.trap(), "app storage is full")`——**是 VM trap，不是返回值**。
- 配额来源：`splash.rs:228` 与 `splash.rs:816-822` 的 `set_storage_quota()` → `set_quota_for_heap(heap_key, total_bytes)` → `JAIL_QUOTAS`（`splash_storage.rs:54-80`），默认 `MAX_TOTAL_BYTES`。
- **没有**给脚本用的 usage/quota 查询接口（配额与根都放在 host 侧，注释明确"script can neither read nor raise its own quota"，`splash_storage.rs:54-56`）；native 侧有 `under_quota()`（`:114-119`）。
- 脚本语言**支持 try/catch**（`.sources/octoscript/fuzz/corpus/execution/try_catch.octoscript`、`recoverable_failure.octoscript`）。
- 但当前 bundle 用的是返回值约定：`main.splash:267-276`（草稿）与 `:293-300`（版本）都是 `let result = fs.write(...)`，`if result == nil { …成功… } else { cue_set_status("草稿暂时没有保存成功，请查看运行日志。") }`——**没有 try/catch**。因此配额耗尽时 trap 直接中断 handler，**那条"请查看运行日志"分支到不了**，界面状态保持不变（与第 1 节观察一致）。
- 对最终验收的含义：把配额调大后写入即可通过；若要在容量不足时仍给出可读反馈，bundle 侧需要把 `fs.write` 包进 try/catch（或改用返回错误值的调用形式），这是**下一版可选改进**，与本次 4 MiB 配额修复相互独立。

## 5. 复现步骤（供复核）

1. 安装 0.4.0（jail 内含 138,649 B bundle，manifest 声明 65536）。
2. 打开模块 → 点一条路线 → 点「用这句」→ 在草稿框输入任意字符。
3. 点「存A」：状态不变；`find /srv/oncue-apps/oncue-screening-room -name "take-a.txt"` 为空；日志出现 `app storage is full`。
4. 对照：点「取A」→「版本 A 还没有内容。」（只读路径不触发 trap）。
