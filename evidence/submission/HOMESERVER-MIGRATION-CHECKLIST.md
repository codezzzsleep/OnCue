# Matrix Homeserver 差异与迁移/复测清单（只形成清单；不索要、不传播凭据）

## 事实（非秘密，只读核对）

| 项 | 我们当前 | 赛事今日新增指南（`docs/rinx-guide.md`, commit a2a3e2e） |
| --- | --- | --- |
| Homeserver | `matrix.org`（客户端直连 `https://matrix-client.matrix.org/`） | **`https://matrix.rinx.chat`** |
| 认证站 | 无（直接密码登录） | **`https://auth.matrix.rinx.chat`**（统一认证/SSO） |
| MXID | `@codezzzsleep:matrix.org` | `@{user}:matrix.rinx.chat` |
| 登录方式 | 密码 + 直接 API | 认证站 SSO；两者**不能混填** |

## 结论（按 AI1 #360 定调）

1. **先完成当前包在现有已授权账户上的同版回归**，证据里**标注 homeserver=`matrix.org`**；
   **不得**把这批证据写成"赛事专用服务通过"。
2. 赛事专用账号需要**用户本人注册/授权**；**AI 不擅自创建或迁移**，也不索要/传播凭据。
3. 本清单只列"若要做迁移/复测，需要哪些步骤与证据"，不执行迁移。

## 迁移/复测清单（若用户决定切换）

| # | 步骤 | 谁做 | 产出 |
| --- | --- | --- | --- |
| 1 | 在 `https://auth.matrix.rinx.chat` 注册/登录，确认完整 MXID `@{user}:matrix.rinx.chat` | **用户本人** | 账号可用性确认（不含密码） |
| 2 | 在 Rinx 客户端按指南登录（Homeserver 填 `https://matrix.rinx.chat`，不要填认证站） | 用户本人 | 登录成功截图（脱敏） |
| 3 | 在赛事服务上建/加入测试房间，取得 room id | 用户本人 | room id（可用于 `Room ID to allow`） |
| 4 | 用 Developer `Import an app` 以该 room id 重新授权 Run | AI（用户在场） | Review 面板截图（Allowed room 一致） |
| 5 | 重跑 room 最新 N 条（脱敏指纹） | AI | 证据中**标注 homeserver=matrix.rinx.chat** |
| 6 | 重跑共享 Octos 七块回合 | AI | 七块结构 + 全文 SHA256 |
| 7 | 重跑 停止 / 90 秒 / 迟回调隔离 | AI | 状态量与 epoch |
| 8 | 在材料中同步更新"Homeserver / 支持平台 / 复现环境" | AI | README + 复现说明 |

## 明确不做

- 不创建赛事账号、不迁移现有账号、不索取或转存任何凭据；
- 不把现有 `matrix.org` 上的证据冒充为 `matrix.rinx.chat` 的结果。
