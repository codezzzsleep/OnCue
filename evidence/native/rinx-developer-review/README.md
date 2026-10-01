# Rinx Developer Review 实测：`Allowed room: None`（2026-10-02）

## 现象（两张真实截图）

| 截图 | 输入 | Review 输出 |
| --- | --- | --- |
| [`01-valid-room-id-allowed-room-none.png`](01-valid-room-id-allowed-room-none.png) | **精确 room id**（44 字符，该房含 8 条 `[OnCue 测试房]` 消息） | `Allowed room: None` |
| [`02-invalid-room-id-still-none.png`](02-invalid-room-id-still-none.png) | **明显无效值** `this-is-not-a-room-id` | **仍是 `Allowed room: None`**，且**未**报 `Invalid Matrix room ID` |

Review 其余部分正确（两次都如此）：
```
OnCue · 群聊试映室 0.4.4 · Local unsigned bundle
Services: storage, matrix.room_info, matrix.read_messages, octos.session.open, octos.turn.start, octos.turn.interrupt
Allowed room: None
Run grants these services for this session. Octos turns may use the connected core's tools.
```

## 为什么这能证明"字段没被读取"

按固定源码，若字段值被读取，无效值**必须**报错：

- `rinx:src/miniapps/ui.rs:328-331`：`if !room.trim().is_empty() { ruma::RoomId::parse(room.trim()).map_err(|_| "Invalid Matrix room ID")?; }`
- `ui.rs:340`：`self.reviewed_room = room.trim().to_string();`
- `ui.rs:337-339`：Review 文案里 `Allowed room: {room 或 "None"}`

**有效值与无效值得到完全相同的 `None`，且无效值未触发必须触发的解析错误** →
`import_form.room` 这个 `TextInput` 的**取值没有被读到**（每次都当空值）。

这不是输入问题：截图里字段**可见地**含有那串文本；输入经 `xtype --stdin`（不进命令行/日志）。

## 复现路径（可独立重走）

1. Rinx（官方启动器打开，已登录并自动恢复会话）
2. `Discover` → `Mini apps` → `Import an app`
   （入口位置按固定源码定位：`rinx:src/home/mobile.rs:165-175` 的 `discover_mini_apps` 行、`:494` 的点击处理）
3. `OctoSense bundle folder` 填**仓库外 unsigned 开发副本**；
   `Room ID to allow (optional)` 填上面两种值之一
4. 点 `Review bundle`，读 `Allowed room:` 行

## 相关事实

- 开发副本：0.4.4、**unsigned**、`digest 724721aa8a34b5ae86d85672a94a1e59f96d29831a6bdc16e53a509b056bea58`
  （补丁后**重新 stamp**，非旧 `cf0f314e…`），`hub check --allow-unsigned` = PASSED
- 精确 room id 的取得：用已落盘的 Matrix 会话只读 API 列 joined_rooms 并比对消息内容，
  另一个同名 `oncue-test-room` 为 0 条文本，故可区分
- 「在 Rinx 打开房间看到 12 条」**只是前置**；核心验收是小程序**自己**读它的 12 条后再走
  `session.open` / `turn.start` 的七块 —— 在 room 绑定修好前无法进行
