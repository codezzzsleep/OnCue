# Back / 键盘 / 关闭-重开（ADR 0005 官方验证第 4 项）

> 官方要求（`Rinx/docs/adr/0005-octoscript-miniapps-matrix-octos.md:40` 第 4 条）：
> "Verify standalone and OctoSense-hosted builds and native runtime behavior on macOS and Android.
> **Confirm Back, keyboard handling, close/reopen**, and that hosted Rinx reuses the Octos provider."
> 另 ADR 0005："Closing an instance **revokes its leases, cancels pending work and drops late replies**；
> returning from the app does not terminate Rinx or the OctoSense shell."

## 环境
- 宿主：**OctoSense/Rinx 实例 2（`:98`）**，账号 **`@oriontraxmandl397:matrix.rinx.chat`**（接收者 B）
- 包：`oncue-screening-room` 0.4.4 未签名开发副本
- Rinx 基线：官方 `c515e5fc9b6d`，零补丁
- **不干扰生产实例**（`:99`）

## 逐项结果

| # | 项 | 操作 | 观察到 | 截图 |
| --- | --- | --- | --- | --- |
| 1 | **键盘** | 点草稿框 → 键入 `RINX-KEYBOARD-TEST-01` → 点「存 A」 | 应用接受输入；落盘 `<data>/miniapps/<hex(B)>/oncue-screening-room/take-a.txt` = **`RINX-KEYBOARD-TEST-01`** | `rinx-1-keyboard-input.png` |
| 2 | **Back** | 点 Rinx 的 `Back` | 应用**关闭**并返回 Mini apps 库（Built-in apps / App Hub / Import an app）；面板原本写明 "**Back closes this app and revokes its services**" | `rinx-2-back-closed.png` |
| 3 | **关闭-重开** | `Import an app` → 填同一包路径 → `Review bundle` → `Run` | 应用**重新运行**（`Running · Back closes this app and revokes its services.`） | `rinx-3-reopened.png` |
| 4 | **重开后数据仍在** | 点「取 A」 | **草稿框出现 `RINX-KEYBOARD-TEST-01`** —— 跨关闭/重开存活 | `rinx-4-draft-after-reopen.png` |
| 5 | **关闭不终止外壳** | Back 之后 | Rinx 与 OctoSense 外壳继续运行（返回库，不是退出） | 同上 |

## 诚实说明
1. **平台**：在 **Linux aarch64 + Xvfb + llvmpipe** 上验证；官方 ADR 要求的是 macOS 与 Android。
   官方声明**只验证过 Apple silicon macOS**，Linux 属**未验证平台**。Android 未测。
2. **"撤销租约 / 丢弃迟回复"未做独立计量验证**：日志未打印 revoke/lease 事件，
   本演示只能证明**应用关闭、返回库、外壳不退出、重开可用**。
   要做到 ADR 0005 第 1 条的"**实例撤销 + 迟回复处理**"，需要一个会在回合进行中被关闭的探针
   （见 `CROSS-ROOM-AND-REVOCATION.md`，待做）。
3. **点击坐标**：窗口在 `:98` 上并非固定位置，且按钮布局与 `card-host` 的 412 宽布局不同；
   本轮坐标为逐图实测（非猜测）。
