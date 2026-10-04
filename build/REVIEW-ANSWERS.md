# `hub scan` 七问回答 — oncue-screening-room 0.4.7

依据当前入口源码、manifest、listing 与 scan packet 核对。HEAD `deadf2b2` 与 `v0.4.7`（`f363d4b`）的包一致。

## 1. Does the app do what its name, subtitle and description claim?

**是。** 名称「OnCue · 群聊试映室」与副标题「先试着说，再决定要不要发。」在页面直接显示。三路线由 `cue_rehearse → cue_start_turn → cue_accept_reply` 生成解析；按钮「A 顺着说 / B 换问法 / C 换玩法」切换预览。草稿「保留这句 / 取回草稿 / 存 A / 存 B / 取 A / 取 B」写入后回读比较。「摘要」是原文摘录——助手只选编号，`cue_source_excerpt` 按编号取回原文，prompt 请求 2–4 个、实际接受 1–4 个。源码与 manifest 无任何 Matrix 发送调用。

## 2. Do the listing's platforms and category fit?

**是。** `platforms: ["linux"]`：本项目在 Linux aarch64 实测；macOS/Windows/移动端未验证，不声明。`category: "productivity"`、`age_rating: "all"` 符合用途。

## 3. Do the granted capabilities match what the app visibly does?

**六项能力均有画面用途，无空置授权。**

| 能力 | 用途 |
| --- | --- |
| `storage` | 草稿写后回读；A/B 两版 |
| `matrix.room_info` | 载入群聊后标题显示房间名 |
| `matrix.read_messages` | 请求 limit 12 的最近消息并编号展示 |
| `octos.session.open` | 试映前打开本应用的助手会话 |
| `octos.turn.start` | 提交 prompt 生成编号选择与三路线 |
| `octos.turn.interrupt` | 停止与 90 秒期限时中断回合 |

直接网络主机：无（`network.hosts` 为空，未申请 `net`）。真实试映会把全部载入消息的 sender/body 与台词发给宿主配置的助手，应用本身不联网。

## 4. Is any part of the interface deceptive?

**未见。** 无登录/密码/PIN/验证码输入框，无支付或订阅界面，不冒用其他品牌。Review/Run 是宿主界面。需注意「已逐字核对」指原文取回核对，不是语义真实性保证——界面已标注假设内容需自行判断。

## 5. Does any text read as an instruction to an assistant?

**有，属于正常助手任务。** `cue_prompt` 包含角色与任务指令（七节格式、编号选原文、假设边界、不调用工具不发送），通过 `octos.turn.start` 的 `text` 字段发送。载入消息按数据传入并标注为待分析，但不是强隔离；`agent: null` 表示未声明自有 agent profile，运行时助手调用仍发生。

## 6. Is any wording abusive or aimed at a private individual?

**未见。** 样例与参与者均为虚构，prompt 要求匿名虚构回应、不模仿真人。授权房间消息可能含个人信息，由使用者决定是否载入与试映；应用不发送。

## 7. Route: pass, human-review, or reject?

**Route: human-review。**

1. 依赖 Rinx 宿主服务（`matrix.*` 仅 Rinx 提供；`octos.*` 由宿主或托管内核提供），card-host 两者皆无，须在 Rinx 复核。
2. 聊天类作品：已记录无绑定房间拒绝与另一账号 `Allowed room: None`；完整接收者授权（deny、租约到期）建议人工复核。
3. 数据范围：全部载入消息 sender/body + trial 进入宿主配置模型；草稿按账号+应用存储、不按房间；无持久草稿删除入口。
4. 证据：146 项受控断言（真实 VM，源码哈希一致，[原始核验链路](<../evidence/checkpoint-0.4.7-recovered/README.md>)）；真实宿主读房、真实回合、播放与草稿记录在[验证摘要](<../oncue/VERIFICATION.md>)。包检查本地 PASSED（`oncue.dev` 签名）。
5. listing release_notes 的「138 项」是上一签名版旧文案，当前为 146 项；随下一发布更新。
