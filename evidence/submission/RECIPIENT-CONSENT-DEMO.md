# 接收者独立授权演示（两个真实账号，2026-10-02）

> 对应官方硬要求（`app-hub-submission.md:51`）：
> "…聊天或账号相关作品还需演示**接收者独立授权**，避免把发送者身份或权限带给接收者。"
> 以及 Rinx 基线的机制定义（`rinx-miniapps.md:14`）：
> "**每次打开须授权**；授权关联账号、登录会话和应用实例，最长一小时，关闭或退出后撤销"
> "展示拒绝、重新打开及不同账号的行为；**不能继承发送者的权限**"

## 环境

| 项 | 值 |
| --- | --- |
| 服务器 | **`matrix.rinx.chat`**（赛事指定） |
| 账号 A（发送者） | `@codezzzsleep:matrix.rinx.chat` |
| 账号 B（接收者） | `@oriontraxmandl397:matrix.rinx.chat` |
| 宿主 | 两个独立 OctoSense/Rinx 实例（`:99` 与 `:98`），**官方 Rinx `c515e5fc9b6d` 零补丁** |
| 数据根 | A：`/srv/oncue-rinx-data-rinxchat`；B：`/srv/oncue-rinx-data-recipient` |
| 包 | `oncue-screening-room` 0.4.4，**未签名开发副本**（Rinx Developer 导入故意拒绝发布者签名，ADR 0006/0008） |

> **为什么用两个实例**：上游 Rinx **只持有一个会话**
> （`src/home/account_menu.rs:13`："upstream Rinx… holds exactly one session"），
> 没有应用内多账号切换。第二账号因此用独立数据根的第二实例，这也正好证明
> **授权与数据是按账号隔离的**。

## 证据链（逐项可核）

### 1. 授权不继承：A 有房间，B 为 None

| 账号 | Review 面板的 `Allowed room` |
| --- | --- |
| A | `!2TfOHq2ZGCYO5WJmDC:matrix.rinx.chat` |
| **B** | **`None`** |

截图：`evidence/screenshots/recipient-2-own-consent.png`
→ B 打开同一应用时**必须自己授权**，**没有继承 A 的房间授权**。

### 2. 数据按账号隔离：目录名即账号

```
A: /srv/oncue-rinx-data-rinxchat/miniapps/40636f64657a7a7a736c6565703a6d61747269782e72696e782e63686174/oncue-screening-room/
     └── take-a.txt = A-PRIVATE-DRAFT-001      （19 字节）
B: /srv/oncue-rinx-data-recipient/miniapps/406f72696f6e747261786d616e646c3339373a6d61747269782e72696e782e63686174/oncue-screening-room/
     └── （空，0 个文件）
```
目录名的十六进制解码后正是各自的 Matrix ID：
`@codezzzsleep:matrix.rinx.chat` / `@oriontraxmandl397:matrix.rinx.chat`

### 3. 应用内证实：B 取不到 A 的草稿

A 侧先在自己实例里写入 `A-PRIVATE-DRAFT-001` 并点「存 A」（落盘见上）。
B 侧运行同一应用后点「取 A」，状态行显示：

> **"版本 A 还没有内容。"**

截图：`evidence/screenshots/recipient-4-draft-isolated.png`
→ **B 看不到 A 的草稿**，尽管 A 账号下该文件确实存在。

### 4. 两个账号各自登录同一赛事服务器

```
A: /srv/oncue-rinx-data-rinxchat/latest_user_id.txt      → @codezzzsleep:matrix.rinx.chat
B: /srv/oncue-rinx-data-recipient/latest_user_id.txt     → @oriontraxmandl397:matrix.rinx.chat
```
B 的登录走**浏览器 SSO**，授权页明确显示
"Palpo Homeserver wants to access your account as **@oriontraxmandl397:matrix.rinx.chat**"。

## 诚实说明（未做/受限项）

1. **本演示不是"分享卡片"路径。** 官方 Rinx 基线的完整演示是"分享应用卡片 → 接收者打开同一内置应用"，
   那条路径属于**内置文章编辑器**的原生分享；我们的应用是通过 **Developer 文件夹导入**装的。
   本演示证明的是**同一应用的授权与数据按账号隔离、接收者不继承发送者权限**，
   与官方要求的实质一致，但**分享卡片这一形式未演示**。
2. **B 实例的助手内核启动失败**（面板显示 `Assistant (OctoSense): failed: the octos kernel stopped`），
   因为两个实例共用了同一个 `OCTOS_APP_CORE_DIR`。**这是我测试环境的配置问题，不是产品缺陷**；
   本演示不依赖 B 的 Agent 回合。
3. **"最长一小时自动过期"** 与 **"关闭后撤销"** 未单独计时验证。
4. **"拒绝（deny）"分支**未演示（只演示了允许）。
5. 平台为 **Linux aarch64 + Xvfb + llvmpipe**，官方声明**只验证过 Apple silicon macOS**；
   Linux 属未验证平台。
