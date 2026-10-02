# 走 Rinx Developer「Mini apps → Import an app」正规路径跑当前 0.4.4（2026-10-02）

按 AI1 #359 第 1–3 步执行。**不使用**"直接改 app store / catalog"，那两步已回滚、只算诊断准备。

## 一、开发副本（仓库外）

| 项 | 值 |
| --- | --- |
| 路径 | `/root/oncue-work/dev-import/oncue-screening-room-0.4.4` |
| 版本 | `0.4.4` |
| digest | `2478d2300f7cbebc17f439caf3965e710a010285d6ddfa306778243efb63d81f` |
| 签名 | **已移除**（与仓库包同 digest） |
| 与仓库一致性 | 只移除 `integrity.signature`；版本/digest/resources 精确一致 |

顺带回答 AI1 的第 6 问：**第 2 次 stamp 后我没有自动沿用 #355 的 PASSED**。
我在 `2478d230…` 上**重新执行**过 `hub check --allow-unsigned`：
- 带我为"直接落盘安装"加的 `oncue.dev` 签名时 → **REFUSED**（publisher key 未注册）；
- **移除签名后 → PASSED**（`[warning] publisher-signature: unsigned`）。
由此可确认：#355 的 PASSED 只属于第一次 `2673402b`，**不能**自动沿用到 `2478d230`。

## 二、真实 UI 路径（Rinx 内，:99）

`Discover → Mini apps → Import an app`：
1. `OctoSense bundle folder` 填开发副本绝对路径；
2. `Room ID to allow (optional)` 填此前已验证的测试房间（44 字符）；
3. 点 **Review bundle** → 界面显示：

```
OnCue · 群聊试映室 0.4.4 · Local unsigned bundle
Services: storage, matrix.room_info, matrix.read_messages, octos.session.open, octos.turn.start, octos.turn.interrupt
Allowed room: !j6BaOOAvAASFVqB8jDJod9O7F8OgOrFjGcFKMVa0WrI
Run grants these services for this session. Octos turns may use the connected core's tools.
```
→ **"Local unsigned bundle"** 印证 AI1 所说：该入口本就是 Developer 未签名快照，不需要 `--allow-unsigned`；
→ **Allowed room 与测试房间精确一致**。

4. 点 **Run** → 应用在 Rinx 内真实运行，顶部显示
   `Running · Back closes this app and revokes its services.`

## 三、Run 后的快照核对（AI1 要求的第一件事）

```
/srv/oncue-rinx-data/miniapps/imports/rinx-miniapp-4739e871-3e0f-4fae-9728-57299b3adf72
  id: oncue-screening-room   version: 0.4.4
  digest: 2478d2300f7cbebc17f439caf3965e710a010285d6ddfa306778243efb63d81f   ← 与当前包精确一致
  signature: (无)                                                            ← 符合 Local unsigned
```
**快照在存活期存在，且 splash/资源 digest 等于当前 digest。** 截图见同目录。

## 四、第一个真实错误（如实记录）

Import 面板上一直显示一条 Assistant 报错（**在 Run 之前就存在**）：

```
Assistant (OctoSense): failed: cwd
  /tmp/oncue-home/.octosense/apps/rinx/accounts/ae83ac7e1d730e9a08555d26d654cc78
  is not usable: No such file or directory (os error 2)
· AI settings: OctoSense Settings → Accounts → AI providers
```

它指向**旧的 `/tmp/oncue-home`**（我们已迁到 `/srv/oncue-home`），即宿主的 Rinx 账号工作目录仍按旧 HOME 解析，
该目录已不存在。这条错误与当前包无关，但会影响"Octos 回合走宿主 AI"的能力，**建议先修它**再评判七块回合。

## 五、尚未完成（下一步）

- **真实房间 12/13 条**：点 `载入群聊` 后界面状态未变化，且 **Rinx 内嵌视图在 `现场原消息` 处被裁切**，
  看不到消息列表 —— 需要在 Rinx 里把窗口拉高或在 card-host 侧取消息区证据。
- **共享 Octos 七块 / 停止 / 90 秒 / 迟回调**：同上，受视图裁切与上面的 Assistant cwd 错误影响。
- **混用版本的结论降级**：按 AI1 #359 第 4 条执行（见 `evidence/` 各处标注）。
