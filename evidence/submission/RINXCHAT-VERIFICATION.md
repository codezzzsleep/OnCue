# 在赛事服务器 matrix.rinx.chat 上的端到端验证（2026-10-02）

## 为什么重做

此前所有宿主侧验证都跑在 **`matrix.org`** 上，而赛事指引
（`hackathon-agenticapp26/docs/rinx-guide.md`）指定的服务器是：

| 用途 | 地址 |
| --- | --- |
| 注册与登录 | `https://auth.matrix.rinx.chat` |
| Homeserver | `https://matrix.rinx.chat` |
| 账号格式 | `@{user}:matrix.rinx.chat` |

**这是本项目的重大偏差**：账号、房间与全部"真实房间读取 / Agent 回合"证据都在错的服务器上，按赛事口径均不作数。
本节记录在正确服务器上重做的完整结果。

## 环境事实（实测）

| 项 | 结果 |
| --- | --- |
| `matrix.rinx.chat` 直连 | HTTP 200（**不需要代理**） |
| 本地注册 | **关闭**（`Local registration is disabled while delegated authentication is enabled`） |
| 可用登录流程 | `m.login.sso` / `m.login.token` / `m.login.application_service`（**无 `m.login.password`**） |
| 因此必须 | 用浏览器完成 SSO；本机装了 firefox 完成注册/登录 |

## 账号与登录

- 账号：**`@codezzzsleep:matrix.rinx.chat`**（device `kI8muzdQV8`）
- 登录方式：**Rinx 自带的 SSO 流程**（`Continue with single sign-on`）——
  Rinx 起本地回调服务 `127.0.0.1:28783` 并调 `Uri::open()` 打开浏览器；
  浏览器在 `auth.matrix.rinx.chat` 完成登录并授权后回调 `?loginToken=…`，Rinx 据此建会话。
- 落盘证据：
  - `/srv/oncue-rinx-data-rinxchat/latest_user_id.txt` = `@codezzzsleep:matrix.rinx.chat`
  - `/srv/oncue-rinx-data-rinxchat/codezzzsleep_matrix.rinx.chat/persistent_state/session`

## 测试房间

`!2TfOHq2ZGCYO5WJmDC:matrix.rinx.chat`（"OnCue 试映室测试房"），
经 Client-Server API 发送 **12 条**消息并读回确认。

## 端到端结果（全部在 matrix.rinx.chat 上）

| 步骤 | 结果 | 证据 |
| --- | --- | --- |
| Rinx 登录赛事服务器 | ✅ | `latest_user_id.txt`；Rinx 房间列表显示"OnCue 试映室测试房" |
| Rinx 读该房间 | ✅ | 内核日志 `Completed backwards pagination request for MainRoom(!2TfOHq2ZGCYO5WJmDC:matrix.rinx.chat)` |
| Developer 路径导入应用 | ✅ | `Discover → Mini apps → Import an app`；面板显示 `Assistant (OctoSense) · primary: ready` |
| Review 保留房间 | ✅ | `Allowed room: !2TfOHq2ZGCYO5WJmDC:matrix.rinx.chat`（官方 Rinx，零补丁） |
| Run | ✅ | 面板 `Running · Back closes this app and revokes its services.` |
| **`matrix.room_info` + `matrix.read_messages`** | ✅ | 应用标题变为真实房名 **"OnCue 试映室测试房"**；状态行 `原消息已载入，可逐条翻看；长消息可用「上翻 / 下翻」逐页读完。` |
| **`octos.turn.start`（Agent 回合）** | ✅ | 状态行 `现场摘要已就绪，点「摘要」可逐页读完；以下是 Agent 的假设排练，原消息仍在上方。` |
| 内核确实调用了模型 | ✅ | 内核日志 `turn: calling LLM ... session=_main:api:octosense#peerctx-rinx-…oncue-s…` → `LLM response received stop_reason=EndTurn response_content_len=1839` |
| 内核为该应用建了记忆命名空间 | ✅ | `…/memory-namespaces/app/rinx/acct-bb9c0dca74620f31/ctx-855721e8-oncue-screening-room-g1/{recall,episodes}.redb` |

宿主模型：`octos: Model: MiniMax-M2.7`。

## 口径修正

- 本项目所有"真实房间 / Agent 回合"结论**以本节为准**，此前在 `matrix.org` 上的同类结论**作废**。
- 赛事账号：`@codezzzsleep:matrix.rinx.chat`。
- 遗留偏差：早期探针与部分截图产生于 `matrix.org`，仅作内部溯源，不作为赛事证据。
