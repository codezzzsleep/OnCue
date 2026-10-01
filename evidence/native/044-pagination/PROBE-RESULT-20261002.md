# OctoScript 最小 probe —— 实际运行结果（2026-10-02）

**这不是计划，是实际执行结果。**

- 命令：`card-host --bundle <probe bundle> --app-data <jail> --stamp --allow-unsigned --size 412x892`
- 运行者：`octosense-card-host`（由固定 App Hub `0f332112` 构建，`/opt/src/apphub/OctoSense-App-Hub/target/release/card-host`）
- 输出通道：**`fs.write`**——应用脚本里**没有** `log()`（已核对 makepad `platform/script/src`，
  `log` 只出现在 shader builtins），所以探针把结果写进 app storage 的 `probe-result.txt`
- 说明：`card-host` 是持续运行的 UI 应用，探针写完后由 `timeout` 终止（exit=124）；
  结果文件在终止前已写入。**exit=124 是超时终止，不是探针失败。**
- 准入日志：`card-host: ai2-probe 0.0.1 admitted — capabilities {"storage"}, hosts {}, storage 4194304 bytes, agent none`
- 隔离日志：`isolate jailed at <jail>/ai2-probe with 4194304 bytes, 1 capability(ies), 1 host(s), 8000000 instructions, 33554432 bytes of heap — all enforced`

## 原始结果文件内容

```
P1_len=8
P1_chars=3
P2_rebuilt=汉A🙂
P2_equal=true
P2_rawlen=8
P3_bad=2772165128578
P3_equal=false
```

## 对照 `probe-plan.md` 的预期

| 检查 | 预期 | 实测 | 结论 |
| --- | --- | --- | --- |
| `len()` | 8（UTF-8 字节） | **8** | ✓ |
| `to_chars().len()` | 3（字符） | **3** | ✓ |
| typed U32 重建 | `汉A🙂` | **汉A🙂** | ✓ |
| `rebuilt == src` | true | **true** | ✓ |
| `rebuilt.len()` | 8（仍是字节） | **8** | ✓ |
| 普通 `[]` 的 `to_string()` | 十进制数字文本 | **2772165128578** | ✓ 反证成立 |
| 普通 `[]` 等于原文 | false | **false** | ✓ |

**结论**：`probe-plan.md` 里由源码推导的判据**全部被真实 OctoScript 执行证实**：

1. **`string.len()` 是字节，不是字数** —— `"汉A🙂"` 的 `len()` = 8（3+1+4）。
   这直接证明 `cue_rehearse` 原来 `trial.len() > 240` 配"240 字"文案是真实缺陷（中文 121 字即 363 字节会被误拒）。
2. **`to_chars()` 是逐字符的 typed U32 数组** —— `to_chars().len()` = 3，且能逐字符重建原文。
3. **普通 `[]` 会把码点渲染成十进制文本** —— `P3_bad=2772165128578`（`27721`/`65`/`128578` 三个码点的拼接），
   与原文**不相等**。所以"页缓冲必须保留 typed U32 来源、不能用字面量 `[]`"是**必需**而非洁癖。

## 未覆盖 / 下一步

- 本 probe 只验证**字符 API 语义**，不验证 UI 渲染、不验证像素可读、不验证宿主内分页表现。
- 分页本身的真实验证仍需：412×892 与 990×613 **双视口逐页真图** + 值核对（见 `test-plan.md`，仍为**未运行**）。
- `card-host` 是独立 card 宿主，**不能替代** OctoSense/Rinx 宿主内的运行验证。
