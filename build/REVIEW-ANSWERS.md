# `hub scan` 七问回答 — oncue-screening-room TODO(作者)：最终版本号

依据当前入口源码、manifest、listing 与 scan packet 核对。对应标签 `TODO(作者)：最终标签`。

## 1. Does the app do what its name, subtitle and description claim?

**是。** 名称「OnCue · 群聊试映室」与副标题「先试着说，再决定要不要发。」在页面直接显示。三路线由 `cue_rehearse → cue_start_turn → cue_accept_reply` 生成解析；按钮「A 顺着说 / B 换问法 / C 换玩法」切换预览。草稿「保留这句 / 取回草稿 / 存 A / 存 B / 取 A / 取 B」写入后读回来比对。「相关原文」由 `cue_source_excerpt` 按助手选的编号取出。应用没有申请也没有调用任何 Matrix 发送服务。

## 2. Do the listing's platforms and category fit?

**是。** 只在 Linux aarch64 上运行过，所以只声明 `linux`。`category: "productivity"`、`age_rating: "all"` 符合用途。

## 3. Do the granted capabilities match what the app visibly does?

**是。六项能力都有对应的界面功能。**

| 能力 | 用途 |
| --- | --- |
| `storage` | 草稿写后读回来比对；A/B 两版 |
| `matrix.room_info` | 载入群聊后标题显示房间名 |
| `matrix.read_messages` | 请求最近的消息并编号展示，最多 12 条 |
| `octos.session.open` | 试映前打开本应用的助手会话 |
| `octos.turn.start` | 提交 prompt 生成编号选择和三路线 |
| `octos.turn.interrupt` | 停止与 90 秒期限时中断回合 |

直接网络主机：无（`network.hosts` 为空，未申请 `net`）。试映时会把全部载入消息的 sender/body 与台词发给宿主配置的助手，应用本身不联网。

## 4. Is any part of the interface deceptive?

**未见。** 无登录/密码/PIN/验证码输入框，无支付或订阅界面，不冒用其他品牌。Review/Run 是宿主界面。界面底部标注了三种说法是助手的假设。

## 5. Does any text read as an instruction to an assistant?

**有，属于正常助手任务。** `cue_prompt` 包含角色与任务指令（七段格式、编号选原文、假设边界、不调用工具不发送），通过 `octos.turn.start` 的 `text` 字段发送。群聊消息在请求里标注为待分析的数据，但这只是文字上的区分，不能完全防止消息内容影响助手。应用没有声明自己的 agent（`agent: null`），用的是宿主的助手。

## 6. Is any wording abusive or aimed at a private individual?

**未见。** 样例与参与者均为虚构，prompt 要求匿名虚构回应、不模仿真人。授权房间消息可能含个人信息，由使用者决定是否载入与试映；应用不发送。

## 7. Route: pass, human-review, or reject?

**Route: human-review。**

1. 依赖 Rinx 宿主服务（`matrix.*` 仅 Rinx 提供；`octos.*` 由宿主或托管内核提供），card-host 两者皆无，须在 Rinx 复核。
2. 已测试：没有选择房间时读取被拒绝；另一个账号打开时没有继承房间授权。未测试：用户点拒绝、授权到期。
3. 数据范围：全部载入消息 sender/body 和你的台词进入宿主配置模型；草稿按账号+应用存储、不按房间；没有删除草稿的入口。
4. 证据：149 项逻辑测试的结果在 [evidence/logic-tests](<../evidence/logic-tests/README.md>)，实机检查记录在[验证记录](<../oncue/VERIFICATION.md>)。包检查通过。
