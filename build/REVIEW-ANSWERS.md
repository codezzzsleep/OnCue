# `hub scan` 七问回答 — oncue-screening-room 0.4.7

对应 `build/review.json`（`hub scan` 生成，含 7 个问题）。逐问作答，答案只引用包内真实内容。

---

## 1. Does the app do what its name, subtitle and description claim? Cite the text in its source.

**是。** 应用名 `OnCue · 群聊试映室`，副标题「先试着说，再决定要不要发」，描述写「把一句还没发出去的话放进群聊试映室，私下展开…三条假设路线…再把建议放进自己的编辑框」。

源码内对应实现（`main.splash`）：
- 标题与副标题直接绘制：`"OnCue · 群聊试映室"` / `"先试着说，再决定要不要发。"`
- 三条路线：`A 顺着这句` / `B 换个问法` / `C 换个玩法`
- 试映入口：`fn` 处理 `ui.cue_rehearse_button`，调 `host.request("octos.turn.start", …)`
- 草稿：`ui.cue_keep_button` / `ui.cue_store_a_button` / `ui.cue_store_b_button` / `ui.cue_load_a_button` / `ui.cue_load_b_button`
- 不发送：源码中**没有任何** `matrix.send_message` 或发送类调用（见第 3 问的逐项核对）。

描述里的「不发送」也由状态行重复声明：`原消息是事实线索；对白、摘要与 A/B 为逐页阅读的私下排练，仍需你判断。尚未发送。`

---

## 2. Do the listing's platforms and category fit an app of this kind?

**是。**
- `platforms: ["linux"]` —— 我们**只在** Linux aarch64（Huawei Cloud EulerOS 2.0，X11 + llvmpipe）上实测过；未在 macOS / Windows / 移动端验证，故不声明。
- `category: "productivity"` —— 应用做的是「发消息前整理措辞与预案」，属生产力工具，不是游戏或媒体类。
- `age_rating: "all"` —— 内容为群聊文字排练，无成人、暴力或赌博内容。

---

## 3. Do the granted capabilities match what the app visibly does? Name every host it requests and why. Name any grant nothing on screen needs.

**相符，且无空置授权。**

**请求的主机：无。** `network.hosts` 为空数组，未申请 `net`；源码中不存在任何 `https://` 主机引用，也没有 `http://`。

| 授权（商店显示原话） | 画面上对应的地方 |
| --- | --- |
| Keep its own data on this device（`storage`） | 「存 A / 存 B / 取 A / 取 B」把两版草稿写入应用自己的 jail |
| See details of rooms you allow（`matrix.room_info`） | 载入群聊后标题变为真实房间名；房名为空时显示「已授权群聊」 |
| Read messages in rooms you allow（`matrix.read_messages`） | 「载入群聊」后逐条展示原消息，并可上一条/下一条、上翻/下翻 |
| Open its own conversation with the assistant（`octos.session.open`） | 「试映下一幕」为该应用打开自己的助手会话 |
| Ask the assistant to work for it…（`octos.turn.start`） | 「试映下一幕」请助手生成三条假设路线；「摘要」请助手总结 |
| Stop assistant work it started（`octos.turn.interrupt`） | 「停止等待」中断进行中的回合 |

**没有任何一项授权在画面上找不到用途**；反过来，画面也没有用到未申请的授权。

---

## 4. Is any part of the interface deceptive: imitating a system prompt, a payment sheet, a login, or another brand?

**没有。**
- 无登录界面、无密码/PIN/验证码输入框、无支付或订阅界面。
- 应用内**不出现**任何系统提示样式的弹窗；所有文案都在应用自身的绘制区域内。
- 不模仿其他品牌：界面只用自有名称「OnCue」，图标为自绘 SVG（`assets/icon.svg`）。
- 唯一近似「系统」的文案是状态行对助手状态的如实描述（如「正在逐句播放…」「先试点试映下一幕，生成三条假设路线。」），不索取凭据、不暗示系统授权。
- 应用不申请、也不显示任何 `prompt` 类能力。

---

## 5. Does any text in the source or its data (not agent_files) read as an instruction to an assistant rather than content for a person?

**没有。**
- `main.splash` 中发往助手的内容是**任务描述与用户输入**，以 `octos.turn.start` 的 `input` 字段传递；这是应用与助手之间的正常服务调用，不是伪装成内容给助手下的指令。
- 送进助手的原消息文本**按数据传递**，未做指令包装（例如不拼接「忽略以上指令」之类）。
- 样例阶段的预设文案明确标注为虚构：`虚构群聊与预设路线，仅供体验玩法。`、`样例预设已展开；这些对白不是对真实群友的预测。`
- 界面文案全部面向人阅读，不含提示词、越狱语句或对助手的元指令。

---

## 6. Is any wording abusive, or aimed at a private individual?

**没有。**
- 内置样例是虚构的「国庆搭子局」，参与者为虚构角色（如「小林」），不影射真实个人。
- 假设对白为**匿名接话**，不指名真实群友，也不对其人格作评价。
- 应用读取的是**用户自己授权**的房间；不展示、不推断他人隐私，且房名为空时不回落显示完整房间 ID。
- 状态行持续提示：假设内容不是对真实群友的预测，需用户自行判断。

---

## 7. Route: pass, human-review, or reject. Give reasons a publisher can act on.

**Route: human-review.**

理由（供发布者核对）：
1. **依赖两个宿主服务族**（`matrix.*` 仅由 Rinx 小程序宿主提供；`octos.*` 由托管内核的 shell 或 Rinx 提供）。`card-host` 两者皆不提供——在 `card-host` 中这两类调用会得到 `no service answers …`。因此**必须在 Rinx 中复核**，不能只看 `card-host` 的结果。
2. **应用会读取用户房间消息并送去模型**（用户授权后）。需要人工确认：授权范围最小、房名不回落完整 ID、不发送任何消息、不缓存超出配额的内容。本包 `storage` 上限 4 MiB（远低于 16 MiB 上限）。
3. **不做「接收者独立授权」演示**：本应用不分享、不发送，材料中须写清这一点，避免被误认为具备分享/代发能力。
4. 已在 **赛事服务器 `matrix.rinx.chat`**（账号 `@codezzzsleep:matrix.rinx.chat`、测试房 `!2TfOHq2ZGCYO5WJmDC:matrix.rinx.chat`）完成端到端实测：真实房间读取与助手回合均成功（内核日志 `LLM response received … response_content_len=1839`）。
5. 图标、截图、listing 与能力声明均由 `tools/octo check` 与 `hub check` 通过（未签名状态 `— PASSED`）。
6. 未验证项已如实列出（见 `evidence/submission/RINXCHAT-VERIFICATION.md` 与 `oncue/VERIFICATION.md`）。
