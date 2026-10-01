# RUNBOOK — OnCue 第 10 / 11 步（宿主源码机制 + 逐步操作 + 日志验证）

> 历史诊断记录：正文的日志、目录、profile_unresolved、65,536字节配额与源码行号是早期联调时的快照，不代表当前运行状态。后续宿主profile已经配置并迁移目录，正式包存储配额已改为4MiB；真实共享Octos回合仍未验证，必须以fresh回合错误或结果判断，不能沿用“目录为空”的旧硬阻塞结论。当前验收见 [验证记录](../oncue/VERIFICATION.md)，实际实例、房间授权与服务scope须重新核对。


面向任务：在 Rinx「发现 → Mini apps → 导入应用」里导入 OnCue bundle 并授予测试房间，读取该房间最近文本消息（第 10 步）；处理宿主弹出的 agent 同意面板（第 11 步）。

**路径前缀约定**（下文所有 `file:line` 均相对这些根）：

| 前缀 | 实际路径 |
| --- | --- |
| `rinx:` | `/root/.cargo/git/checkouts/rinx-cf0dcd4e7b4d3fa8/0879548/` |
| `octo:` | `/root/oncue-runtime/OctoSense/` |
| `hub:` | `/root/.cargo/git/checkouts/OctoSense-App-Hub-0f87f6c76fe4766d/0f33211/` |
| `bundle:` | `/root/oncue-runtime/dev/OnCue/oncue/bundle/` |
| `octos:` | `/root/oncue-runtime/octos/` |

日志：`/root/oncue-runtime/state/logs/octosense-rinx.log`（**注意：该文件会被宿主重启截断**，本次第 6 节里标「已实测」的字符串中有 4 条是在 17:40 前后的 7591 行版本里验证的，17:45 宿主重启后文件被清空重写为 538 行；仍在当前日志里的见下表）。

---

## 0. 关键事实速查

1. **没有任何鼠标/键盘之外的「程序化同意」入口**。OctoSense 的首次同意面板只吃指针事件：`octo:crates/shell/src/approvals/mod.rs:336-352` 的 `pointer()` 在第 337 行用 `matches!(event, Event::MouseDown(_) | Event::MouseUp(_) | Event::MouseMove(_) | Event::TouchUpdate(_) | Event::Scroll(_))` 过滤，**`Event::KeyDown` / `TextInput` 一律直接 `return false`**；`octo:crates/shell/src/approvals/view.rs:564-565` 的 `Widget::handle_event` 是空实现（注释原文："The shell routes presses (`approvals::pointer`); nothing here."）。所以回车点不动是设计如此，不是坐标问题。
2. **该面板属于 OctoSense shell 自己的 overlay 层**，不是 Rinx 的窗口、也不是 Rinx 的 Ask 面板。挂载点 `octo:crates/shell/src/lib.rs:219-232`（`shell_overlay := View{ ... shell_approvals := ShellApprovals{} shell_approvals_settings := ShellApprovalsSettings{} }`），由 `octo:crates/shell/src/approvals/view.rs:460-500` 的 `draw_consent()` 画，带 0.45 黑scrim（`view.rs:351-353`）且 `self.modal = true`（`view.rs:231-236`），在 `octo:crates/shell/src/lib.rs:5784-5789` 被**第一个**消费（"An approval sheet, the first-use sheet and the Approvals page are modal, over everything"），因此它盖在 Rinx 窗口和 Ask 面板之上并吞掉所有指针事件。
3. **该房间的 agent 同意已经被授予过**：`/root/oncue-runtime/state/octosense/approvals/consent.json` 现有

   ```json
   {"oncue-screening-room": {"allowed": true, "at": 1790846259}}
   ```

   `1790846259` = 2026-10-01 17:17:39 CST。也就是说 **第 11 步的面板在下次启动时不会再出现**（`consent.rs:152-167` 的 `ask()` 只在这条记录缺失时入队）。要重放面板必须先删掉这条记录之一（见第 5 节备选路径）。
4. **即使 Allow 成功，Octos 回合目前仍会失败**：`/root/oncue-runtime/state/octos-core/profiles/` 目录为空，`_main.json` 不存在，内核返回 `profile_unresolved`（`octos:api/OCTOS_UI_PROTOCOL_V1_SPEC_2026-04-24.md:2696-2708`：「A request that names a profile which is not present in server profile storage must fail with ... `data.kind = "profile_unresolved"`」）。这一条在当前日志里**已实测**（见第 6 节 G7）。这是第 11 步成功判据上的硬阻塞，与点不点得动 Allow 无关。

---

## 1. 「Room ID to allow」：定义 / 校验 / 保存 / 最终授予形态

### 1.1 Rinx 侧输入字段

| 环节 | 位置 |
| --- | --- |
| 字段定义 | `rinx:src/miniapps/ui.rs:55` — `room := TextInput {width: Fill empty_text: "Room ID to allow (optional)"}`，位于 `import_form`（`ui.rs:51-75`）内，与 `bundle_path`（`ui.rs:52-54`）并排 |
| 「Import an app」按钮 | `rinx:src/miniapps/ui.rs:49`（`import_app := Button{... text: "Import an app"}`）；点击 → `show_import()` `ui.rs:198-210` |
| 入口（导航） | 底部导航 Mini apps 标签 `rinx:src/home/navigation_tab_bar.rs:290-293`；或「发现」页 Mini apps 行 `rinx:src/home/mobile.rs:168`；面板打开 `ui.rs:854-858`（`MiniAppsAction::Open`） |
| 校验（Review 时） | `rinx:src/miniapps/ui.rs:328-331` — `if !room.trim().is_empty() { ruma::RoomId::parse(room.trim()).map_err(\|_\| "Invalid Matrix room ID")?; }`。**只有非空才校验**；留空是合法的 |
| 保存 | `rinx:src/miniapps/ui.rs:340` — `self.reviewed_room = room.trim().to_string();` |
| Review 提示文案 | `rinx:src/miniapps/ui.rs:337-339` — `"... \nServices: {capabilities}\nAllowed room: {room 或 "None"}\nRun grants these services for this session. Octos turns may use the connected core's tools."` |
| Run 时复检 | `rinx:src/miniapps/ui.rs:352-354` — `if room.trim() != self.reviewed_room { return Err("Room access changed. Review the bundle again") }`；再解析一次 `ui.rs:355-364` |
| 授予动作 | `rinx:src/miniapps/ui.rs:367-376` — `super::AUTHORITY.issue(InstanceId{app, account, room, generation}, manifest.capabilities, room.into_iter().collect(), Instant::now() + Duration::from_secs(3600))` |

即：**最终形态 = 一张 `Lease`**。`Lease` 的定义在 `rinx:crates/miniapp-core/src/lib.rs:26-35`（`services: BTreeSet<String>`、`rooms: BTreeSet<String>`、`expires`、`alive`、`epoch`），`InstanceId` 在 `lib.rs:16-22`（`app` / `account` / `room: Option<String>` / `generation`），签发函数 `SessionAuthority::issue` 在 `lib.rs:41-59`。**capability 名就是 manifest 的 `capabilities` 数组原样**（bundle:manifest.json：`storage`、`matrix.room_info`、`matrix.read_messages`、`octos.session.open`、`octos.turn.start`、`octos.turn.interrupt`，共 6 个），房间白名单 = `rooms` 这个 `BTreeSet`，只有「Room ID to allow」里那一个房间（`ui.rs:373` 的 `room.into_iter().collect()`）。

### 1.2 授权判定发生在哪个函数（重点回答）

三层，按调用顺序：

1. **`Lease::authorize`** — `rinx:crates/miniapp-core/src/lib.rs:83-105`。函数体 90-104 行：先 `self.check(account)`（租约存活/未过期/账号一致），再 `if !self.services.contains(service) { Err("Mini app was not granted {service}") }`，再 `if let Some(room) = room { if !self.rooms.contains(room) { Err("Mini app was not granted access to this room") } }`。
   **这就是 `matrix.room_info` 与 `matrix.read_messages` 的第一道也是主判定点。** 由宿主分发函数 `rinx:src/host/matrix/mod.rs:545-570` 的 `execute()` 调用，调用点在 `mod.rs:556`：
   `let target = args.get("room_id").or_else(|| args.get("space_id")).and_then(\|v\| v.as_str()); lease.authorize(&account, &service, target)?;`
   OnCue 这两个请求都不带 `room_id`（`bundle:main.splash:82` 是 `host.request("matrix.room_info", {}, ...)`、`main.splash:92` 是 `host.request("matrix.read_messages", {limit: 12}, ...)`），所以 `target == None`，**只查 service 名单，不查房间**。
2. **附加房间复查** — `rinx:src/host/matrix/mod.rs:557-570`：`let room = lease.identity().room...`（即 UI 里那个 Room ID），然后 `mod.rs:565-569` `if room.as_ref().is_some_and(\|id\| !lease.permits_room(id.as_str())) { return Err("Attached room was not granted") }`。`permits_room` 在 `rinx:crates/miniapp-core/src/lib.rs:107-109`。**只有填了 Room ID 才会有房间维度；留空则 `room == None`，直接走到下一步报错。**
3. **服务级的读取闸门** — `rinx:src/host/matrix/policy.rs:77-87` 的 `ensure_room_access(room, RoomAccess::Read)`：
   `if !ctx.lease.permits_room(room) || (matches!(access, RoomAccess::Write) && !writing(&ctx.service)) { return Err(ROOM_ACCESS_DENIED) }`（`ROOM_ACCESS_DENIED = "Mini app was not granted access to this room"`，`policy.rs:8`）。
   - `matrix.room_info` 的调用点：`rinx:src/host/matrix/room.rs:464-467`（`pub(crate) async fn info(...)` 内第 467 行）。
   - `matrix.read_messages` 的调用点：`rinx:src/host/matrix/room.rs:524-532`（`pub(crate) async fn read_messages(...)` 内第 532 行）。

另外两个与「有没有房间」直接相关的分支：
- `rinx:crates/miniapp-core/src/matrix.rs:134-146` 的 `room_free(service)` **不包含** `matrix.room_info` / `matrix.read_messages`（它们在 `matrix.rs:367` 和 `matrix.rs:370` 只出现在 `cost()` 计价表里）；
- `rinx:crates/miniapp-core/src/matrix.rs:180-183`：`if !room_free(service) && !has_room { return Err("this mini-app is not attached to a room") }`；以及 `rinx:src/host/matrix/mod.rs:531-533` 的 `(_, None) => return Err("this mini-app is not attached to a room")`。
  → **结论：Room ID 留空时，`matrix.read_messages` 一定失败，错误串就是 `this mini-app is not attached to a room`。**

### 1.3 bundle 侧如何消费授权

`bundle:main.splash:71-106` 的 `cue_import_room()`：先 `matrix.room_info`（`main.splash:82`），用返回的 `room.data.room_name`（回落 `room.data.room_id`，`main.splash:88-89`）当场景标题，再 `matrix.read_messages {limit: 12}`（`main.splash:92`），把 `result.data.messages` 逐条渲染成 `#N sender：body`（`main.splash:103-121`）。状态栏文案：`读取本次附加群聊的最近 12 条文本消息…`（`main.splash:81`）→ 成功 `原消息已载入；下面输入一句想接的话。`（`main.splash:104`）；空 `这个群聊暂时没有可读取的文本消息。`（`main.splash:102`）；失败 `消息读取失败：` + error（`main.splash:96`）/ `没有读到群聊：` + error（`main.splash:86`）。90 秒看门狗在 `main.splash:45-50`。

---

## 2. 读取上限与过滤（`matrix.read_messages` 实测实现）

宿主真正干活的函数：`rinx:src/host/matrix/room.rs:524-608`。

| 项目 | 值 / 行为 | 位置 |
| --- | --- | --- |
| **默认 limit** | `10` | `rinx:crates/miniapp-core/src/matrix.rs:210` |
| **limit 上限（硬钳制）** | `args["limit"].as_u64().unwrap_or(10).clamp(1, 30)` → **最大 30** | `rinx:crates/miniapp-core/src/matrix.rs:209-211` |
| OnCue 实际请求 | `limit: 12`（在 1..=30 内，不会被钳） | `bundle:main.splash:92` |
| 请求参数字节上限 | `MAX_REQUEST_BYTES = 256 * 1024` | `rinx:crates/miniapp-core/src/lib.rs:14` |
| 响应字节上限 | `MAX_REPLY_BYTES = 2 * 1024 * 1024` | `rinx:crates/miniapp-core/src/lib.rs:15` |
| 单条 body 截断 | `SERVICE_BODY_CLIP: usize = 500`（字符，按 char boundary 切，`clip_chars` 在 `rinx:src/host/matrix/mod.rs:538-543`） | `rinx:src/host/matrix/room.rs:31`、`room.rs:40-42` |
| 走缓存的分支 | `client.event_cache().room(&room_id)` → `events.iter().rev()`（新→旧），拼满 `limit` 即 break | `room.rs:547-563` |
| 缓存不够时的网络分页 | `out.clear(); for _ in 0..4 { ... }`：**最多再翻 4 页**，每页 `options.limit = 50u32.into()` | `room.rs:565-601` |
| 排序 | `out.reverse()` — **返回给小程序的是旧→新**（"Backward pagination is newest-first; apps read oldest-first."） | `room.rs:603` |
| 每行字段 | `{sender, sender_id, event_id, body, ts, msgtype}` + `{room_id, unread}` | `room.rs:38-51`、`room.rs:91-100` |
| 顶层还带 | `unread_count`（`room.num_unread_messages()`），OnCue 忽略 | `room.rs:604-607` |
| 房间状态要求 | `room.state() != RoomState::Joined` → `Err("room not joined")` | `room.rs:535-537` |

**是否过滤非文本事件 —— 部分过滤，且不是"只留文本"：**
- `room.rs:550-555` 和 `room.rs:583-588` 两处都是同一个模式：
  `let Ok(AnySyncTimelineEvent::MessageLike(AnySyncMessageLikeEvent::RoomMessage(SyncMessageLikeEvent::Original(msg)))) = event.raw().deserialize() else { continue };`
  → **只保留 `m.room.message` 的 Original 事件**；state 事件、reaction、redaction、sticker、encrypted 解不开的、以及 `*::Replacement`（编辑事件）全部被 `continue` 丢掉。
- 编辑处理：`push_message()`（`room.rs:498-521`）把 `Relation::Replacement` 收进 `edits` 表，遇到被编辑的原消息时用新 body 覆盖，并同样走 500 字截断（`room.rs:514-518`）。所以**列表里看到的是编辑后的最终文本，且编辑本身不占一行**。
- **但不过滤媒体**：`message_json` 无条件输出 `"msgtype": msg.content.msgtype()`（`room.rs:49`）。所以 `m.image` / `m.file` / `m.emote` 也会作为一行返回，只是 `msgtype` 字段不同；OnCue 不判别 msgtype，会把它们当"文本消息"渲染进 `cue_sources`（`main.splash:97-101`）。**如果第 10 步要的是"最近 12 条文本"，实际语义是"最近 12 条 m.room.message"，含媒体。**
- OnCue 的 prompt 给消息编号是**旧→新**的 `#1..#N`（`main.splash:137-140` 的 `cue_prompt()`），所以 prompt 里写死的 `#2、#3` 指的是这 12 条里第 2、3 旧的那两条。

---

## 3. 第 11 步：agent 同意面板属于哪一层、Allow 触发什么、有没有非鼠标入口

### 3.1 面板就是它

标题、按钮、列出内容的唯一出处：

- `octo:crates/shell/src/approvals/view.rs:460-500` `fn draw_consent(&mut self, cx, screen, s: &AgentSummary, tok)`
  - 标题 `view.rs:471`：`let title = format!("Let {}'s agent start?", s.name);`
    → 观测到的「Let OnCue · 群聊试映室 agent start?」即 `s.name = "OnCue · 群聊试映室"`（该名字来自 App Hub 目录条目：`/root/oncue-runtime/state/apps/catalog.json` 里 `id=oncue-screening-room, name="OnCue · 群聊试映室"`，经 `octo:crates/shell/src/apps.rs:256-260` → `script_agent_app()` `apps.rs:275-282` 填进 `AgentApp.name`）。
  - 副标题 `view.rs:474`：`"The first time an app asks for its agent, you decide. You can change it in Settings."`
  - 三段列表头 `view.rs:480 / 484 / 488`：`"It may read"` / `"It may use"` / `"Where the model runs"`
  - **列出 `octos.session.open` / `octos.turn.start` / `octos.turn.interrupt` 的地方**：`view.rs:484-487` 遍历 `s.uses`。`uses` 由 `octo:crates/shell/src/approvals/consent.rs:38-64` 的 `AgentSummary::from_manifest()` 生成：`declared` = manifest `capabilities` 里 `octos.` 开头的（`consent.rs:51-56`）∩ `granted`（这里 `granted == app.octos`，即三个全中），再经 `describe_capability()`（`consent.rs:72-80`）把 `octos.*` 渲染成 `"Its agent ({c})"`。所以面板上显示的三行是：
    `• Its agent (octos.session.open)` / `• Its agent (octos.turn.start)` / `• Its agent (octos.turn.interrupt)`。
- 按钮：`view.rs:492-493` — `let allow = buttons.draw(cx, x, y, w, "Allow", true);` 和 `let deny = buttons.draw(cx, x + allow.size.x + 8.0, y, w, "Don't allow", false);`
- 命中区：`view.rs:494-495` — `self.hits.push((allow, Hit::Consent { app: s.app.clone(), allow: true }))` / `... allow: false`；枚举定义 `view.rs:60` `Consent { app: String, allow: bool }`。

### 3.2 属于哪个窗口 / 哪一层

**OctoSense shell 主窗口的 overlay 层，盖在一切之上，Rinx 只是它的一个 client。**

- 挂载：`octo:crates/shell/src/lib.rs:219-232`，`shell_overlay` 里的 `shell_approvals := ShellApprovals{}`（注释原文："The approval surface (approvals/): the shell's approval and first-use sheets, the time-box indicator, and Settings > Assistant > Approvals."）。
- 它**不是** Rinx 的 Ask 面板（`rinx:src/assistant/`、`rinx:src/agent_chat/`），也不是 Rinx 的 Mini apps 面板里那块 `approval` 视图。文件头注释写明："The shell-drawn approval surface (ADR 0004 §8, §4): drawn by the shell, over everything, in the shell's own chrome kit"（`view.rs:1-6`）。
- 模态性：`view.rs:229-236` `draw_all()` 里 `if let Some(summary) = &f.consent { self.modal = true; self.draw_consent(...) }`，并且**优先级高于审批单和问题卡**（`consent` 分支在 `sheet` / `question` 之前）。`view.rs:351-353` 先铺一层 `alpha 0.45` 的黑scrim。
- 事件路由顺序：`octo:crates/shell/src/lib.rs:5784-5789`，在 WM 自己的快捷键、drag、bar 模块之前就调用 `approvals::pointer(&self.ui, cx, event)`，一旦 taken 直接 `return`。`pointer()` 内部先问 settings page（`mod.rs:340-345`）再问 sheets（`mod.rs:346-351`）。

### 3.3 Allow 触发哪个 action / 函数

一条完整链路：

1. 指针按下/抬起必须**落在同一个矩形内**：`octo:crates/shell/src/approvals/view.rs:191-226` 的 `ShellApprovals::pointer()`。
   - `MouseDown` → `self.down = self.hit_at(p)`（`view.rs:206`），`hit_at` 在 `view.rs:185-187`：**先找非 `Hit::Card` 的命中**（按钮优先于卡片），再退回卡片。
   - `MouseUp` → `let hit = self.hit_at(p); let pressed = self.down.take(); if h == d { act(h.clone()) }`（`view.rs:210-217`）——**按下点和抬起点必须命中同一个 `Hit`，且类型与内容都相等**，否则什么都不做。
   - `return self.modal || hit.is_some()`（`view.rs:218`）—— 弹着时全部吞掉。
   → 这解释了为什么"远程桥只发 MouseUp"、"XTEST 落在错误的坐标/缩放空间"、"回车"都无效：**必须有一次配对的 MouseDown+MouseUp，坐标都在 `Allow` 那个 `rect` 内**。矩形不是写死的，是每次 draw 时按 `card_rect()`（`view.rs:345-349`，依赖当前屏幕尺寸）和 `Buttons::draw()`（`view.rs:88-99`，`width = measure(label) + 26.0`）现算的，所以窗口尺寸变化后坐标也会变。
2. `act()` 在 `octo:crates/shell/src/approvals/view.rs:518-547`；Allow 走 `view.rs:527-529`：
   `Hit::Consent { app, allow } => super::with(\|a\| a.consent.set(&ApprovalGesture::sheet_tap(), &app, allow, now))`
3. `ConsentStore::set()` 在 `octo:crates/shell/src/approvals/consent.rs:170-184`：
   - 允许 → `self.allowed.push(app)`（进入 `take_allowed()` 队列）；
   - `self.decided.insert(app, Record { allowed, at: now })`；
   - `self.asking.retain(\|a\| a != app)`（面板消失的条件）；
   - `self.save()`。
4. `save()` 在 `consent.rs:223-232`：写 `home/CONSENT_FILE`，`CONSENT_FILE = "approvals/consent.json"`（`consent.rs:18`），`home = OCTOSENSE_HOME`（`octo:crates/shell/src/octosense/paths.rs:62`；本机进程环境实测 `OCTOSENSE_HOME=/root/oncue-runtime/state/octosense`）→ 即 `/root/oncue-runtime/state/octosense/approvals/consent.json`，权限 0600、0700 目录（`mod.rs:404-434` 的 `write_private` / `create_private_dir`）。
5. 下一次 `approvals::tick()` → `octo:crates/shell/src/lib.rs:3510-3521` 的 `revoke_agents()` → `agents::pump(&revoked)`（`octo:crates/shell/src/agents.rs:193-200`）→ `agents::prepare(app)`（`agents.rs:143-180`）→ 起一个 `prepare-<id>` 线程跑 `ai_host::contained::prepare(&id)`，结果打在 `agents.rs:158-159` 两条日志之一。
6. 之后 `access()`（`agents.rs:74-81`）返回 `Allowed`，`app_chat::begin()`（`octo:crates/shell/src/app_chat/mod.rs:169-182`）才会 `connect()`。

### 3.4 谁把这个面板唤起来的（两条路，别搞混）

| 触发路径 | 函数链 | 面板上的 app id / name |
| --- | --- | --- |
| **A. 小程序自己调 `octos.*`（第 11 步的主路径）** | Card/Ap Hub 侧 `octos` 服务的 contained 闸门：`octo:crates/ai-host/src/lib.rs:132-142`（`ContainedGate::Consent` 注释："Each app once the person allowed its agent ... the first call asks"）→ `octo:crates/shell/src/approvals/mod.rs:142`（`set_consent(consent_for_contained)`）→ `mod.rs:263-270` `consent_for_contained()` → `mod.rs:250-261` `module_gate()` → `a.consent.granted(app, all)` 为假时 `AgentSummary::from_manifest(app, label, &manifest, &granted, ...)` + `a.consent.ask(...)` | app id `oncue-screening-room`，name = `app_label()`（`octo:crates/shell/src/approvals/sheet.rs:97-104`）= `Oncue-screening-room` |
| **B. 「Ask OnCue · 群聊试映室」/ Shift+F8（当前日志实际走的路）** | `octo:crates/shell/src/lib.rs:3570-3577` `ask_focused_app()`（"Ask <app>" for the focused window's app, the bar's button, Shift+F8, Setup › Assistant）→ `app_chat::open_app()` → `octo:crates/shell/src/app_chat/mod.rs:169-176` `begin()` → `octo:crates/shell/src/agents.rs:240-249` `agents::ask()` → `crate::approvals::consent_ask(summary)`（`mod.rs:230-234`） | app id `oncue-screening-room`，name = AgentApp.name = **`OnCue · 群聊试映室`** |

两条路共用同一个 `ConsentStore` 和同一个 `consent.json` 键 `oncue-screening-room`，所以**谁先问、问的是哪个名字，结果都落在同一条记录上**。标题带中文应用名 ⇒ 你看到的那次是路径 B（或等价的 `agents::ask`）。

Rinx 的 Mini apps 面板里那块审批视图是**另一块 UI**，别混：`rinx:src/miniapps/ui.rs:77-83`（`approval := View{ ... allow := Button{text: "Allow once"} deny := Button{text: "Deny"} }`）、`ui.rs:255-264` `show_approval()`、`ui.rs:664-679`（`event["kind"] == "approval_requested"` → `Approval { message: "Octos tool approval: {title}\n{body}" }`）、`ui.rs:768-793`（点击 → `provider.decide(lease, &approval.id, approve, tx)`）。它是普通 Makepad `Button` 部件，可以聚焦、可以用键盘，也能被小程序通过 `octos.turn.interrupt` 间接放弃（`bundle:main.splash:33-39`）。

### 3.5 除了鼠标点击，还有什么等价入口

**直接按 Allow：没有。**（证据见第 0 节第 1 条：`mod.rs:337` 的事件白名单 + `view.rs:564-565` 的空 `handle_event`。）

但**让面板不再出现 / 预先授予**有四条，按推荐顺序：

1. **改 consent 文件（最直接，纯文件操作）**
   `/root/oncue-runtime/state/octosense/approvals/consent.json`（键=app id，值=`{"allowed": bool, "at": <unix 秒>}`；读入逻辑 `octo:crates/shell/src/approvals/consent.rs:124-129` 的 `in_home()`，只在 `approvals::init`（`mod.rs:142-148`，由 `octo:crates/shell/src/lib.rs:5182` 在启动时调用）时读一次 ⇒ **必须改在宿主启动之前**）。
   要让第 11 步的面板重新出现验证一次，就把 `oncue-screening-room` 这条删掉再启动。
2. **开发者模式**：`octo:crates/shell/src/dev_mode.rs:537-539` `grants_all(app)` → `consent.rs:140-142` `granted()` 直接 `true` → `consent.rs:152-159` `ask()` 立即返回 `Allowed`，面板根本不入队；同时 `octo:crates/shell/src/approvals/dev_hooks.rs` 让闸门问都不问。UI 入口是 Setup → Developer options → Turn on（`octo:crates/shell/src/lib.rs:3369-3373` 的 `setup.developer.on`）。**副作用大**：它同时会自动批准所有审批（`dev_mode.rs:540-542` `auto_approve`），不适合当"只放行 OnCue"的手段。
3. **`OCTOSENSE_CONTAINED_APPS=1`（环境变量，只对 contained/Card 路径有效）**
   `octo:crates/ai-host/src/lib.rs:213-219` `contained_gate_from()`：`Some("1") => ContainedGate::Everyone`（"Every app, without asking"），`Some("0") => Off`，其它 = `Consent`。本机进程环境实测**未设置**该变量（只有 `OCTOSENSE_HOME=/root/oncue-runtime/state/octosense`），所以现在是 `Consent`。注意它**不影响路径 B**（`agents::ask`）。
4. **Settings → Assistant → Approvals 页面里的 Allow 按钮**
   `octo:crates/shell/src/approvals/settings_page.rs:320-324`（`State::Allowed => ("Turn off", Hit::AgentOff)`，否则 `("Allow", Hit::AgentAllow)`）→ `settings_page.rs:380` `Hit::AgentAllow(app) => a.consent.set(&ApprovalGesture::settings_tap(), &app, true, now)`；页面由 `octo:crates/shell/src/approvals/mod.rs:304-312` `open_settings()` 打开（入口 `octo:crates/shell/src/lib.rs:3364-3368` 的 `APPROVALS_ROW`，定义在 `octo:crates/shell/src/shell/menu.rs:789`）。**但这一页仍然是指针驱动的 Makepad 之外的自绘画布**（`settings_page.rs` 自己也有 `pointer()`），所以它只是"另一处可以点 Allow 的地方"，不是非鼠标入口。另外它列出的 app 来自 `consent.rs:207-220` 的 `agents()`，即 `register_agents()`（`mod.rs:313-320`）在 `open_settings()` 时用 `crate::apps::agent_apps()`（`apps.rs:201-215`）注册的——**没启动过的 app 也要等 Settings 打开时才会被登记**。

**不能用的：** `--test-action approval-consent`（`octo:crates/shell/src/approvals/mod.rs:357-395`）。它只是摆一个样例面板出来，`mod.rs:354-356` 的注释写得很清楚："Nothing here approves anything: the samples wait for the person."

**为什么 XTEST / 远程桥 / 回车点不动（机制归纳）**：`approvals::pointer` 只认配对 MouseDown+MouseUp（`view.rs:206-217`），命中判定是 `contains(rect, abs_point)`（`view.rs:185-187`，`contains` 来自 `octo:crates/shell/src/shell/ui.rs`）。因此必要条件 = (a) 同一窗口坐标空间里的 `abs` 坐标（VNC 缩放/偏移会让它偏）；(b) 按下与抬起都落在 `Allow` 的 `rect` 内（该 rect 每次 draw 现算，见 3.3 第 1 条）；(c) 事件确实进了 shell 的 `handle_event` 且没被前面的分支提前 `return`（`lib.rs:5784-5789` 之前没有任何分支会为审批面板让路，反之亦然）。回车无效则纯粹是因为 337 行的白名单里没有键盘事件。

---

## 4. 第 10 / 11 步逐步操作 + 预期现象 + grep 什么

> 运行环境事实（本次已实测）：Matrix 已登录 `@codezzzsleep:matrix.org`；测试房间 `!j6BaOOAvAASFVqB8jDJOd9O7F8OgOrFjGcFKMVa0WrI` 已在 joined 列表里；Rinx 以 hosted 模式跑（`ai-host: rinx (i1g1) took its assistant service`）。

### 第 10 步

**10.1 打开导入表单**
- 操作：Rinx 底部导航「Mini apps」（`rinx:src/home/navigation_tab_bar.rs:290-293`）或「发现 → Mini apps」（`rinx:src/home/mobile.rs:168`）→ 面板里点「Import an app」（`rinx:src/miniapps/ui.rs:49`）。
- 预期：出现两个文本框 + Review/Run 两个按钮（`rinx:src/miniapps/ui.rs:51-75`）。第一个 `empty_text` 是 `OctoSense bundle folder`（`ui.rs:53`），第二个是 `Room ID to allow (optional)`（`ui.rs:55`）。
- grep：本步无宿主日志。可观察文件系统副作用：`/root/oncue-runtime/state/octosense/apps/rinx/data/miniapps/imports/`（`ui.rs:319`、`ui.rs:324` 传入的 snapshots；`app_data_dir` 见日志 `App::handle_startup(): app_data_dir: "/root/oncue-runtime/state/octosense/apps/rinx/data"`）。
  **注意（AI1 #94 纠正）**：该目录当前为空**不能**推出"导入路径从未成功过一次"——`Snapshot` 的 `Drop` 会自动 `remove_dir_all`（`rinx:crates/miniapp-core/src/package.rs:48-52`），Review 失败、返回或关闭之后目录都会被清掉。因此第 10 步的快照证据必须在 **Review/Run 仍然存活时**抓取，并在关闭前后各记一次（关闭前应能看到 `rinx-miniapp-<uuid>/`，关闭后消失）。

**10.1b 开发者签名的真实语义（AI1 #94 补充）**

- 本地 Developer 的 `Package::load_in` 使用 **`RefuseAllSignatures`**；manifest 里的 `require_signature:false` 只表示"**允许 unsigned**"，**并不保证任意 signed 包都能通过**。
- 因此必须对当前 **signed 0.4 包**做一次**实际 Review**并核对错误信息；若出现签名拒绝，则用**仓库之外的临时开发副本**，**只移除 `manifest.integrity.signature`**（保留 `bundle_blake3` 与全部内容）走官方 unsigned developer 路径，并记录该副本与签名包的**源码/资源摘要相同**（例如 `hub stamp` 结果一致、`diff -r` 仅 manifest 差异）。
- **正式 bundle 始终保持签名**；不为此更换宿主、不改公钥校验、不改正式包。

**10.1c 关于 prompt 里的编号**

- 样例 preset 的对白里写死 `#2`/`#3` 只是样例文本；**真实 `cue_prompt` 的编号是按当前所有来源动态生成的**，不能把样例里的编号当成模型链路的硬编码。

**10.2 填 bundle 绝对路径**
- 操作：在「OctoSense bundle folder」填 `/root/oncue-runtime/dev/OnCue/oncue/bundle`。
- 依据：`rinx:src/miniapps/ui.rs:324` `Package::load_in(&PathBuf::from(path.trim()), &snapshots)`；`Package::load_inner` 在 `rinx:src/miniapps/package.rs:69-101` 会把整个目录**拷贝**成快照 `snapshots/rinx-miniapp-<uuid>`（`package.rs:74-79`），读 `manifest.json` + `SCRIPT_ENTRY`（本 bundle 是 `main.splash`，`package.rs:114-116`），并 `admit_digest(..., RefuseAllSignatures)`（`package.rs:95-99`，`HostLimits{require_signature:false}`）。
  ⚠️ 注意 `package.rs:89-91`：`if manifest.agent.is_some() { Err("Bundle agent profiles are not supported here; declare explicit octos.* services instead") }`。本 bundle 的 `"agent": null` 正好落在 `None`，能过。
- 预期：无独立反馈（错误会以 notice 形式出现在面板上）。
- grep：无。

**10.3 填 Room ID**
- 操作：在「Room ID to allow (optional)」填 `!j6BaOOAvAASFVqB8jDJOd9O7F8OgOrFjGcFKMVa0WrI`。
- 依据+后果：`rinx:src/miniapps/ui.rs:329-331` 用 `ruma::RoomId::parse` 校验；空着不报错，但 room_info/read_messages 会以 `this mini-app is not attached to a room` 失败（`rinx:crates/miniapp-core/src/matrix.rs:180-183`、`rinx:src/host/matrix/mod.rs:531-533`）。
- grep：`Adding new joined room !j6BaOOAvAASFVqB8jDJOd9O7F8OgOrFjGcFKMVa0WrI`（**已实测**，来自 `rinx:src/sliding_sync.rs:4369`，说明该房间确实 joined，`room.rs:535-537` 的 `room not joined` 不会触发）。

**10.4 点「Review bundle」**
- 操作：点 `review`（`rinx:src/miniapps/ui.rs:72`）→ `review()` `ui.rs:315-326` → `review_package()` `ui.rs:328-343`。
- 预期现象（面板 notice，`ui.rs:337-339`）：
  ```
  OnCue · 群聊试映室 0.4.0 · Local unsigned bundle
  Services: storage, matrix.room_info, matrix.read_messages, octos.session.open, octos.turn.start, octos.turn.interrupt
  Allowed room: !j6BaOOAvAASFVqB8jDJOd9O7F8OgOrFjGcFKMVa0WrI
  Run grants these services for this session. Octos turns may use the connected core's tools.
  ```
  **`Allowed room:` 后面必须是完整房间 ID。** 若是 `None`，回 10.3。
- 失败态：`Invalid Matrix room ID`（`ui.rs:330`）。
- 副作用：`miniapps/imports/` 下多出一个 `rinx-miniapp-<uuid>/` 目录。
- grep：无宿主日志（Rinx 侧只有 `notice` 标签，不打 log）。

**10.5 点「Run」**
- 操作：点 `run`（`rinx:src/miniapps/ui.rs:73`）→ `run()` `ui.rs:345-441`。
- 预期现象：
  1. lease 签发：`ui.rs:367-376`，`Instant::now() + 3600s`（1 小时有效）。
  2. `ContextProvider::open(&lease)`（`ui.rs:401-407`）：本机 hosted 模式有 assistant，正常；失败也只记进 `self.octos_unavailable`，不让 Run 失败。
  3. splash 适配 + `set_host_tag("rinx-miniapp-<generation>")`（`ui.rs:420-421`）。
  4. notice 变 `Running · Back closes this app and revokes its services.`（`ui.rs:436-438`）。
  5. OnCue 界面出现；`bundle:main.splash:313` `start_timeout(0.05, fn(){ cue_show_demo() cue_refresh_takes() })` 0.05 秒后跑样例舞台，状态栏显示 `虚构群聊与预设路线，仅供体验玩法。`（`main.splash:69`）。
- 失败态与定位：
  - `Review a bundle first`（`ui.rs:347`）— 没 Review 就 Run。
  - `Package changed; review it again`（`rinx:src/miniapps/package.rs:161-172` 的 `unchanged()` 比对原始 bundle 的 `signing_bytes`）— Review 之后又改了 bundle。
  - `Log in to Matrix before running a mini app`（`ui.rs:349-351`）。
  - `Room access changed. Review the bundle again`（`ui.rs:352-354`）— Review 后动了 Room ID 输入框。
- grep（**已实测**，均来自本次日志）：
  - `\[SPLASH\] eval: .* bytes preserve=false view=true` — 证明 splash 真的在 Rinx 的 Mini apps 面板里跑起来了。**注意：这条在 17:45 宿主重启后的当前日志里没有**（app 没在跑），是 17:40 前后那一轮实测到的（`octo:.sources/makepad/widgets/src/splash.rs:412-417` 的 `log!`）。同一次还实测到 `wm: launched hub:oncue-screening-room as client 2 (in-process, card)`（`octo:crates/shell/src/lib.rs:2490`）和 `card: oncue-screening-room running under 6 capability(ies), 1 host(s), 65536 bytes of storage, 8000000 instructions, 33554432 bytes of heap`（`hub:crates/appstore/src/cardapp.rs:94-97`，6 = manifest 的 6 个 capability）——这两条是 **App Hub card 路径**的启动痕迹，不是 Rinx Mini apps 路径；如果你的证据要证明"第 10 步是从 Rinx 面板跑的"，请以 `\[SPLASH\] eval` + `miniapps/imports/` 快照目录为准。
  - `Mini app was not granted access to this room` / `this mini-app is not attached to a room` — 均**实测为 0 次命中**，即当前日志里没有房间授权失败。

**10.6 在小程序里点「载入群聊」**
- 操作：点 `CueButton{text: "载入群聊"}`（`bundle:main.splash:334`）→ `cue_import_room()` `main.splash:71-106`。
- 预期现象（按顺序）：
  1. 场景标签变 `正在读取你选择并授权的群聊`（`main.splash:78`）；状态栏 `读取本次附加群聊的最近 12 条文本消息…`（`main.splash:81`）。
  2. `matrix.room_info` 返回 → 场景标签变房间名 `oncue-test-room`（`main.splash:88-89`，来自 `room.rs:485` 的 `room_name`）。
  3. `matrix.read_messages` 返回 → 「现场原消息」区渲染 `#1 … #N`（`main.splash:97-101`），状态栏 `原消息已载入；下面输入一句想接的话。`（`main.splash:104`）；房间真没消息则是 `这个群聊暂时没有可读取的文本消息。`（`main.splash:102`）。
  4. **顺序是旧→新**（`room.rs:600-601` 的 `out.reverse()`），`#1` 是这 12 条里最旧的。
- 失败态与根因对照：
  | 状态栏文案 | 宿主错误串 | 根因 / 位置 |
  | --- | --- | --- |
  | `没有读到群聊：room not joined` | `room not joined` | `rinx:src/host/matrix/room.rs:470-472` |
  | `没有读到群聊：Mini app was not granted access to this room` | `ROOM_ACCESS_DENIED` | `rinx:src/host/matrix/policy.rs:77-86` ← 房间不在 lease.rooms |
  | `消息读取失败：Mini app was not granted matrix.read_messages` | — | `rinx:crates/miniapp-core/src/lib.rs:94-96` |
  | `消息读取失败：this mini-app is not attached to a room` | — | Room ID 留空，`matrix.rs:180-183` / `mod.rs:530-532` |
  | `消息读取失败：not logged in` | — | `room.rs:533`、`room.rs:541` |
  | `消息读取失败：couldn't read messages: …` | — | `room.rs:576-581`，4 页分页仍没拼满 |
  | `消息读取等待超过 90 秒，已结束等待。…` | — | `bundle:main.splash:45-50` 的看门狗 |
  | 另外：单个请求最多挂 185 秒被 `Service timed out` 掐掉 | — | `rinx:src/miniapps/ui.rs:644-651` |
- grep：Rinx 侧**不打印** matrix 服务成功/失败的日志（`dispatch()` 只在出错时 `self.notice(cx, &e)`，`ui.rs:698-700`）。所以第 10.6 步的验证只能靠小程序 UI 文案 + 文件系统。可用的间接证据是第 10.3 条的房间 joined 行，以及（若 Rinx 面板路径跑通）`\[SPLASH\] eval`。

### 第 11 步

**11.1 先确认面板这次会不会出现**
- 操作：`cat /root/oncue-runtime/state/octosense/approvals/consent.json`。
- 当前实测内容：`oncue-screening-room` = `{"allowed": true, "at": 1790846259}`（= 2026-10-01 17:17:39 CST），`rinx` = `{"allowed": true, ...}`。
- 判定（`octo:crates/shell/src/approvals/consent.rs:132-137` 的 `state()` / `consent.rs:152-167` 的 `ask()`）：
  - 记录存在且 `allowed: true` → **不会再弹**，`agents::access()` 直接 `Allowed`（`agents.rs:74-81`）。
  - 想重放面板：删掉 `oncue-screening-room` 这一条，重启宿主，再走 10.x + 点「试映下一幕」（或 Ask OnCue）。
- grep：**已实测** `agents: oncue-screening-room's agent could not be prepared: profile '_main' is not configured for this AppUI session (profile_unresolved)`（`octo:crates/shell/src/agents.rs:159`）。**这条在每个宿主启动时都会出现，而且它本身就是"consent 已允许、但模型侧没配好"的判据**——如果 consent 是 Denied/未决定，`prepare()` 会在 `agents.rs:144-146` 提前 return，这条日志根本不会出现。

**11.2 触发**
- 操作：在 Rinx 面板里跑起来的 OnCue 中，写一句台词，点「试映下一幕」（`bundle:main.splash:343-344`）→ `cue_rehearse()` `main.splash:147-193` → `host.request("octos.session.open", {}, ...)`（`main.splash:160`）。注意 `cue_rehearse` 在 `cue_sources.len() == 0` 时会以 `先载入一个群聊，或打开样例舞台。` 拦住（`main.splash:152`），所以必须先做 10.6。或者：焦点在 OnCue 窗口时按 Shift+F8 / 点 bar 上的 Ask（`octo:crates/shell/src/lib.rs:3570-3577`、`lib.rs:5916-5919`）。
- 预期现象：屏幕中央弹出一张卡，压暗整个桌面，标题 `Let OnCue · 群聊试映室's agent start?`（`octo:crates/shell/src/approvals/view.rs:471`），副标题 `The first time an app asks for its agent, you decide. You can change it in Settings.`（`view.rs:474`），随后 `It may read` / `It may use`（三行 `Its agent (octos.*)`）/ `Where the model runs`（`view.rs:480-489`），底部 `Allow` / `Don't allow`（`view.rs:492-493`）。
- grep：**已实测** `ask: oncue-screening-room's agent`（`octo:crates/shell/src/lib.rs:3574`）——这条只证明"Ask <app>"被调用了；**不能**证明同意面板弹了（面板弹出不打日志）。

**11.3 点 Allow**
- 操作：用鼠标在 `Allow` 矩形内完成一次按下+抬起。
- 预期现象：面板消失；`consent.json` 的 `at` 时间戳刷新（`octo:crates/shell/src/approvals/consent.rs:170-184`）。
- grep（**代码推断，未实测**——因为已经 allowed，本轮不会再产生）：
  - 成功且模型 profile 配好：`agents: oncue-screening-room's agent is prepared (its peer is listed for the system agent)`（`octo:crates/shell/src/agents.rs:158`）。
  - 成功但 profile 没配（**当前状态**）：`agents: oncue-screening-room's agent could not be prepared: profile '_main' is not configured ... (profile_unresolved)`（`agents.rs:159`）——见 11.1。
- 点 `Don't allow` 的话：`consent.rs:172-174` → `revoke(app)`，`octo:crates/shell/src/lib.rs:3519` 打 `approvals: oncue-screening-room's agent turned off; revoked 0 module service(s) and its contained peer`（**代码推断，未实测**）。

**11.4 Allow 之后的实际结果（当前必现）**
- 现象：`octos.session.open` 的 reply 会给小程序，但紧接着 `octos.turn.start` 会失败；小程序状态栏显示 `Agent 暂时不可用：…` 或 `这次试映没有完成：…`（`bundle:main.splash:164`、`main.splash:170`）。
- 根因（已验证）：`/root/oncue-runtime/state/octos-core/profiles/` 目录**为空**，`_main.json` 不存在。规范位置见 `octo:crates/ai-host/src/lib.rs:243`（"Where the kernel's profile lives (`<core_dir>/profiles/_main.json`)"）与 `octos:api/OCTOS_UI_PROTOCOL_V1_SPEC_2026-04-24.md:2705-2708`（profile 不存在 ⇒ `profile_unresolved`）。`core_dir` 见日志 `octos: kernel service ready ... core dir Some("/root/oncue-runtime/state/octos-core")`（`octo:crates/ai-host/src/lib.rs:302`）。
- 这条**同时是第 11 步的验收门槛**：不把它修掉，Allow 点了也看不到三条路线。

**11.5 如果第 11 步的目标只是让小程序把消息读出来**
那根本不需要第 11 步：`matrix.room_info` / `matrix.read_messages` 是小程序 manifest 声明的 capability，由 Run 时的 `Lease` 授予，与 agent 同意**完全无关**（`rinx:src/miniapps/ui.rs:367-376` + `rinx:crates/miniapp-core/src/lib.rs:83-105`）。只有点「试映下一幕」调 `octos.session.open` / `octos.turn.start`（`bundle:main.splash:160-167`）才会碰到 agent 同意闸门。

---

## 5. 单列一节：Allow 面板的可选操作路径与结论

**结论（先说死）**：`Let …'s agent start?` 这张首次同意面板**只有鼠标入口**。所有代码路径汇总如下：

| 想做的事 | 有没有路 | 具体是什么 |
| --- | --- | --- |
| 用键盘（回车/空格/Tab+回车）按 Allow | **没有** | `octo:crates/shell/src/approvals/mod.rs:337` 的 `matches!` 白名单里没有 `KeyDown`/`KeyUp`/`TextInput`；`octo:crates/shell/src/approvals/view.rs:564-565` 的 `handle_event` 是空函数，注释即 "The shell routes presses (`approvals::pointer`); nothing here." |
| 用 CLI flag 直接批准 | **没有** | `octo:crates/shell/src/approvals/mod.rs:354-356`：`--test-action approval-consent` / `approvals-settings` 只是"摆个样例在前面"，"Nothing here approves anything: the samples wait for the person." |
| 用环境变量跳过问询 | **有（部分路径）** | `OCTOSENSE_CONTAINED_APPS=1`（`octo:crates/ai-host/src/lib.rs:213-219` → `ContainedGate::Everyone`，"Every app, without asking"）。**只盖住 contained/Card 路径（3.4 节的路径 A）**，不盖住 `agents::ask`（路径 B）。本机当前未设置该变量 |
| 用设置项预先授予 | **有** | Setup → Assistant → Approvals 页面里该 app 行的 `Allow`（`octo:crates/shell/src/approvals/settings_page.rs:320-324`、`settings_page.rs:380`；页面打开 `octo:crates/shell/src/approvals/mod.rs:304-312`，菜单行 `octo:crates/shell/src/shell/menu.rs:789` + `octo:crates/shell/src/lib.rs:3364-3368`）。**但这一页同样是自绘画布 + 指针**，所以它是"另一处鼠标入口"，不是"非鼠标入口" |
| 开开发者模式全放行 | **有（副作用大）** | `octo:crates/shell/src/dev_mode.rs:537-539` `grants_all()` → `consent.rs:140-142`；入口 `octo:crates/shell/src/lib.rs:3369-3373` `setup.developer.on`。它同时让所有审批自动通过（`dev_mode.rs:540-542` `auto_approve`、`octo:crates/shell/src/approvals/dev_hooks.rs`），不适合只放行 OnCue |
| 直接写 consent 文件 | **技术上可行，但不得当作正常授权流程或授权验证** | 文件：`$OCTOSENSE_HOME/approvals/consent.json`（`octo:crates/shell/src/approvals/consent.rs:18`；本机 `OCTOSENSE_HOME=/root/oncue-runtime/state/octosense`，已从运行进程环境实测）。格式：`{"schema":1,"apps":{"<app id>":{"allowed":true,"at":<unix 秒>}}}`（`consent.rs:92-101` 的 `Record` / `ConsentFile`）。app id = `oncue-screening-room`。**约束：只在 `approvals::init`（`octo:crates/shell/src/approvals/mod.rs:142-148`，由 `octo:crates/shell/src/lib.rs:5182` 启动时调用）读一次，所以必须写在宿主启动前**；文件权限会被写成 0600/目录 0700（`mod.rs:404-434`）。删除某条记录 = 下次会重新弹面板。 **AI1 #94 明确要求**：不得把手写 `consent.json`、`Everyone`/`grants_all` 当作正常授权流程或授权验证；本机 `oncue-screening-room` 的同意已由**真实操作**授予（`allowed:true`，17:17:39），无需重放。第 11 步只保留普通的真实 Allow / Settings 操作路径。 |

**给第 11 步的实操建议**：既然面板确实是纯鼠标，且 `oncue-screening-room` 的同意**已经授予过**（`consent.json`，17:17:39），第 11 步真正待解决的不是"怎么点 Allow"，而是 11.4 的 `profile_unresolved`——`/root/oncue-runtime/state/octos-core/profiles/_main.json` 缺失。把 provider profile 配上（Settings → AI providers，或放好 `_main.json`）之后再跑「试映下一幕」，`octos.turn.start` 才能真的出三条路线。

---

## 6. 日志验证清单（已实测 vs 代码推断）

日志文件：`/root/oncue-runtime/state/logs/octosense-rinx.log`。**该文件在宿主重启时被清空重写**（本次：17:40 时 7591 行 / 3.3 MB → 17:45 时 538 行 / 0.12 MB）。截至完稿（18:02）该文件又长到 3340 行，其中 `[SPLASH] eval` 共 7 次：6 次 809 bytes、1 次 19828 bytes，**没有一次是 OnCue 的 22193 bytes**，即当前没有 OnCue 在宿主里跑。下表「状态」列的区分以文本落盘时刻为准。

### 已实测（在本会话内真实 grep 命中）

| # | grep 串（可直接复制） | 命中次数 | 说明 / 出处 |
| --- | --- | --- | --- |
| G1 | `Adding new joined room !j6BaOOAvAASFVqB8jDJOd9O7F8OgOrFjGcFKMVa0WrI` | 1 | 测试房间已 joined；`rinx:src/sliding_sync.rs:4369`。**当前日志里仍在** |
| G2 | `oncue-test-room` | 2 | 两个同名房间（`!j6BaOO…` 与 `!dYWyHEBF…`），**填 Room ID 时别填错那一个**；`sliding_sync.rs:4369` |
| G3 | `wm: modules linked` | 1 | `["rinx","terminal","apphub","card"]`；`octo:crates/shell/src/lib.rs:5283`。当前仍在 |
| G4 | `wm: --test-action launch rinx` | 1 | 宿主启动方式；`octo:crates/shell/src/lib.rs:4734`。当前仍在 |
| G5 | `ai-host: rinx (i1g1) took its assistant service` | 1 | Rinx 是 hosted 模式，`octosense_app_peers` 已注入；`octo:crates/ai-host/src/lib.rs:615`。当前仍在 |
| G6 | `octos: contained apps' service registered (Consent)` | 1 | contained 闸门处于 Consent（不是 Everyone）；`octo:crates/ai-host/src/lib.rs:356`。当前仍在 |
| G7 | `agents: oncue-screening-room's agent could not be prepared` | 1 | **同时证明 consent 已 Allowed 且 profile 缺失**；`octo:crates/shell/src/agents.rs:159`。当前仍在（每次启动都会出现） |
| G8 | `octos-core: starting kernel 1:` | 1 | 内含 `--data-dir /root/oncue-runtime/state/octos-core`；`octo:crates/ai-host/src/lib.rs:292`。当前仍在 |
| G9 | `wm: launched rinx as client 1 (in-process, rinx)` | 1 | Rinx 作为 shell 的 in-process 模块起；`octo:crates/shell/src/lib.rs:2490`。当前仍在 |
| G10 | `\[SPLASH\] eval: .* bytes preserve=false view=true` | 1 | 证明 splash 小程序真的跑起来了；`octo:.sources/makepad/widgets/src/splash.rs:412-417`。**17:45 重启后已不在当前日志** |
| G11 | `wm: launched hub:oncue-screening-room as client 2 (in-process, card)` | 1 | App Hub card 路径启动痕迹；`octo:crates/shell/src/lib.rs:2490`。**17:45 重启后已不在** |
| G12 | `card: oncue-screening-room running under 6 capability(ies)` | 1 | 6 = manifest 的 6 个 capability；`hub:crates/appstore/src/cardapp.rs:94-97`。**17:45 重启后已不在** |
| G13 | `ask: oncue-screening-room's agent` | 1 | 「Ask <app>」被调用；`octo:crates/shell/src/lib.rs:3574`。**17:45 重启后已不在** |

### 反证（已实测为 0 命中 ⇒ 这些失败当前都没发生）

| # | grep 串 | 命中 | 含义 |
| --- | --- | --- | --- |
| G14 | `Mini app was not granted access to this room` | 0 | 没有房间授权失败（`rinx:src/host/matrix/policy.rs:8`） |
| G15 | `room not joined` | 0 | 房间都在（`rinx:src/host/matrix/room.rs:471`、`:536`） |
| G16 | `not logged in` | 0 | Matrix 已登录 |
| G17 | `this mini-app is not attached to a room` | 0 | 从未在"Room ID 留空"状态下跑过 read_messages |
| G18 | `Invalid Matrix room ID` | 0 | Room ID 从未填错（`rinx:src/miniapps/ui.rs:330`） |
| G19 | `Room access changed` | 0 | 从未出现 Review 后改 Room ID（`rinx:src/miniapps/ui.rs:353`） |
| G20 | `OctoSense bundle folder` | 0 | 该串只是 `empty_text` 占位符，不打日志 |
| G21 | `Room ID to allow` | 0 | 同上（`rinx:src/miniapps/ui.rs:55`） |

### 仅代码推断（本次未实测到）

| # | grep 串 | 出处 | 何时出现 |
| --- | --- | --- | --- |
| G22 | `agents: oncue-screening-room's agent is prepared (its peer is listed for the system agent)` | `octo:crates/shell/src/agents.rs:158` | Allow 之后**且** profile 已配好 |
| G23 | `approvals: oncue-screening-room's agent turned off; revoked` | `octo:crates/shell/src/lib.rs:3519` | 点了 `Don't allow`（或在 Settings 关掉） |
| G24 | `wm: --test-action approval` | `octo:crates/shell/src/lib.rs:4836-4840` | 用了 `--test-action approval-*`；注意它**不批准任何东西**（`octo:crates/shell/src/approvals/mod.rs:354-356`） |
| G25 | `Mini app is closed` / `Mini app already has 16 pending requests` / `Service timed out` | `rinx:src/miniapps/ui.rs:501`、`:499`、`:649` | Run 前撤回 / 并发超 16 / 单请求 185 秒超时 |

### 已知日志盲区（重要）

Rinx 侧对 mini-app 服务调用**只打错误、不打成功**：`rinx:src/miniapps/ui.rs:698-700` 只有 `if let Err(error) = result { self.notice(cx, &error); }`。因此：
- `matrix.read_messages` 成功读了几条、读了哪个房间，**日志里没有任何记录**；
- 第 10.6 步的正面证据只能来自小程序 UI 的状态栏文案（`bundle:main.splash:81/102/104`）和 `miniapps/imports/` 快照目录；
- OctoSense shell 侧对首次同意面板的弹出/消失**也不打日志**（`octo:crates/shell/src/approvals/view.rs:518-547` 的 `act()` 只在出错时 `log!`，`view.rs:524`）。唯一可观测的副作用是 `consent.json` 的写入与 `agents.rs:158/159` 那两行。

---

## 7. 附：本次结论对应的 bundle 对照（便于核对声明与调用一致）

`bundle:manifest.json` 的 `capabilities` = `["storage","matrix.room_info","matrix.read_messages","octos.session.open","octos.turn.start","octos.turn.interrupt"]`，与 `bundle:main.splash` 实际调用一一对应：`matrix.room_info`（`main.splash:82`）、`matrix.read_messages`（`main.splash:92`）、`octos.session.open`（`main.splash:160`）、`octos.turn.start`（`main.splash:167`）、`octos.turn.interrupt`（`main.splash:37`）。`storage` 由 `fs.write/fs.read/fs.exists` 使用（`main.splash:265-310`）。`"agent": null` 是为了过 `rinx:src/miniapps/package.rs:89-91` 的检查（`manifest.agent.is_some()` 会直接拒绝）。`compute`/`storage` 数值与日志 `card: … 65536 bytes of storage, 8000000 instructions, 33554432 bytes of heap` 一致。

---

sha256(正文，仅覆盖上面这一行「sha256(...)」之上的全部内容) = ff6efe6465c3391cb964043c80973dc7baf421d713f33bd20d50cda201b92df3
