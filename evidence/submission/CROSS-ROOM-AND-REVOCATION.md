# 授权拒绝 / 跨房间（房间绑定）拒绝 / 实例撤销 / 迟回复 — ADR 0005 第 1 项

> 官方要求（`Rinx/docs/adr/0005-octoscript-miniapps-matrix-octos.md:38` 第 1 条）：
> "Check the existing A2App Matrix parser contract, **grant denial, cross-room denial,
> instance revocation and late-reply handling.**"

## 先读源码：机制到底怎么实现的

`Rinx/crates/miniapp-core/src/lib.rs`：
```rust
pub fn authorize(&self, account: &str, service: &str, room: Option<&str>) -> Result<(), String> {
    self.check(account)?;                                    // 账号代际校验
    if !self.services.contains(service) {
        return Err(format!("Mini app was not granted {service}"));        // ← 授权拒绝
    }
    if let Some(room) = room {
        if !self.rooms.contains(room) {
            return Err("Mini app was not granted access to this room".into());  // ← 跨房间拒绝
        }
    }
    Ok(())
}
```
`Rinx/src/host/matrix/policy.rs`：`pub const ROOM_ACCESS_DENIED: &str = "Mini app was not granted access to this room";`

`Rinx/crates/miniapp-core/src/matrix.rs`：
```rust
if !room_free(service) && !has_room {
    return Err("this mini-app is not attached to a room".into());
}
```

**关键**：脚本**不能自带账号或房间**。`crates/miniapp-core/src/lib.rs` 的测试
`script_arguments_cannot_supply_host_identity` 明确要求脚本传入的 `account`/`room`/`generation`
不生效，身份与房间由宿主按租约注入。因此"跨房间"在应用侧的可观测形式是
**"实例未被授予任何房间，却调用房间绑定服务" → 被拒**。

## 实测结果（全部在 Rinx 内）

| # | 项 | 操作 | 结果 | 状态 |
| --- | --- | --- | --- | --- |
| 1 | **房间绑定（跨房间）拒绝** | 接收者实例 **B**（Review 时 `Allowed room: None`）运行同一应用 → 点「载入群聊」 | 状态行 **`没有读到群聊：this mini-app is not attached to a room`** | ✅ **已验证** |
| 2 | 对照：有房间授权时读取成功 | 实例 **A**（`Allowed room: !2TfOHq2ZGCYO5WJmDC:matrix.rinx.chat`）→ 点「载入群聊」 | 标题变为真实房名「OnCue 试映室测试房」，状态行「原消息已载入…」 | ✅ 已验证（`RINXCHAT-VERIFICATION.md`） |
| 3 | **授权拒绝（服务未授予）** | `card-host` 中调用 `matrix.*` | `没有读到群聊：no service answers "matrix" on this device` | ⚠️ 部分：证明了"宿主不提供"的拒绝；`"Mini app was not granted <service>"` 这一分支**未在真机上单独触发** |
| 4 | **实例撤销** | 点 Rinx 的 `Back` | 应用关闭、返回 Mini apps 库；面板原文 "Back closes this app and revokes its services" | ⚠️ **只观测到"关闭"**；日志未打印 revoke/lease 事件，**"租约确实被撤销"未做独立计量** |
| 5 | **迟回复处理** | — | **未验证** | ❌ 无外部可观测信号；需带埋点的探针 |

## 诚实边界

1. **第 1 项是本轮唯一新增的硬证据**：同一应用、两个实例，一个有房间授权一个没有，
   行为可复现地分成"读取成功"与"被拒"。
2. **第 3~5 项没有独立计量验证**。源码能证明机制存在（`authorize` 的租约校验、
   `"Mini app was not granted {service}"`、关闭时撤销租约），但**源码存在 ≠ 实机已验证**。
   按 ADR 0005 第 5 条"**解析器测试、mock provider 或静态截图本身都不算端到端完成**"，
   我不能把它们写成"已验证"。
3. 要做完整的 3~5 项，需要一个**带埋点的探针包**：在回合进行中关闭实例，观察
   (a) 关闭后到达的响应是否被丢弃、(b) 租约是否失效、(c) 是否出现 `Mini app was not granted …`。
   这属于**待做**。
4. 平台：Linux aarch64（官方只验证过 Apple silicon macOS）。
