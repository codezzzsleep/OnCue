# RUNBOOK — AI providers 的 UserProfile envelope 与保存流程

编写方式约定：【代码】= 只读 pinned 源码得出的结论（给出 file:line，未执行任何写操作）；
【实测】= 本次真读到/真看到的状态。本文**不含**任何密码、token、私钥或凭据取值——
涉及凭据只写**键名与类型**。未执行：鼠标/键盘/截图/VNC/桌面操作、`git commit/push`、
改宿主源码、写任何 profile 文件（本文是本次唯一落盘的新文件）。

固定源码根：`/root/oncue-runtime/OctoSense`（下称 `$OS`）、`/root/oncue-runtime/octos`（下称 `$OCT`）。

---

## 0. 结论速览

| 问题 | 结论 | 依据 |
|---|---|---|
| 内核 profile 文件必须是 | `<core_dir>/profiles/_main.json` 的**完整 UserProfile envelope** | `$OS/apps/ai-providers/config/src/profile.rs:1-28`、`profile.rs:54-57` |
| 裸 `{config}` 会怎样 | 缺 `id/name/created_at/updated_at`（serde 无默认值，必填）→ `UserProfile` 反序列化失败 → 当作 **no profile** | `$OCT/crates/octos-cli/src/profiles.rs:146-177`、`get` 失败路径 `profiles.rs:1766-1767` |
| `enabled=false` 会怎样 | 启动时 eager bootstrap **跳过**该 profile；甲方规则同样要求必须 `true`（写盘侧也会强制打开） | `$OCT/crates/octos-cli/src/commands/serve.rs:1224`；`$OS/apps/ai-providers/config/src/profile.rs:193` |
| 当前报错抛出点 | octos `session/open` 的 `ensure_known_profile` → `profile_unresolved_error`，经 peer broker 格式化成 `(profile_unresolved)`，由 shell `agents.rs:159` 打出 | `$OCT/crates/octos-cli/src/api/ui_protocol_transport.rs:10237-10246, 10268-10274, 22633`；`$OS/crates/app-peers/src/broker.rs:2280-2286`；`$OS/crates/shell/src/agents.rs:159` |
| 保存流程触发点 | AI providers 系统应用内宿主 sheet 的 **Save** → `llm.sheet.submit` → 合并写 `_main.json`（原子、0600）→ `octosense_kernel::restart()` | `$OS/apps/ai-providers/host-service/src/sheets.rs:582-592`、`src/lib.rs:285-293, 311-327`、`src/model.rs:284-321` |
| primary 合法值来源 | family_id 来自 `registry`（镜像 octos-llm）；model_id 来自 `model_catalog.json`；route 缺省即 official | `$OS/apps/ai-providers/config/src/registry.rs:50-94`、`config/data/model_catalog.json`、`src/catalog.rs:28, 61-65` |
| MiniMax 实测值来源 | Python 适配器 `engine.py` 默认值 + 实测留档 `minimax-live-result.json`；凭据文件仅路径 | `$ON/dev/OnCue/oncue/server/engine.py:234-261`、`$ON/dev/OnCue/evidence/minimax-live-result.json:69-72`、`$ON/state/minimax.key`（0600，**不读内容**） |

`$ON` = `/root/oncue-runtime`。

---

## 1. UserProfile envelope 完整字段表

### 1.1 octos 侧定义（唯一权威）

`UserProfile`：`$OCT/crates/octos-cli/src/profiles.rs:146-177`

| 字段 | 类型 | 必填 | 默认值 | 校验/语义 |
|---|---|---|---|---|
| `id` | String | **是**（无 `#[serde(default)]`） | 无 | slug 形状；不能用保留频道名（`profiles.rs` `validate_profile_id`）。内嵌内核必须是 `_main`：`$OCT/crates/octos-core/src/types.rs:494` `MAIN_PROFILE_ID = "_main"` |
| `name` | String | **是** | 无 | 展示名；AppCard 本地内核固定用 `_main`：`$OS/apps/appcard/app/app/src/lib.rs:6370-6380`（注释「session/open naming anything else … is rejected」） |
| `public_subdomain` | Option\<String\> | 否 | None | `profiles.rs:159-160`，本机单人场景不设 |
| `enabled` | bool | 否（`#[serde(default)]`） | **false** | `profiles.rs:161-163`。语义：profile 的 gateway 是否随 serve 自启；启动期 eager bootstrap 只收 `enabled==true`：`$OCT/crates/octos-cli/src/commands/serve.rs:1224` |
| `data_dir` | Option\<String\> | 否 | `~/.octos/profiles/{id}/data` | `profiles.rs:164-166` |
| `parent_id` | Option\<String\> | 否 | None | 子账号继承；本机不用 `profiles.rs:168-170` |
| `config` | ProfileConfig | **是** | 无 | `profiles.rs:171-172`；含 `llm`、`env_vars` 等 |
| `created_at` | DateTime\<Utc\> | **是** | 无 | chrono UTC 时间，序列化为 RFC3339（如 `2026-10-01T09:31:47Z`） |
| `updated_at` | DateTime\<Utc\> | **是** | 无 | 同上 |

`ProfileConfig`：`$OCT/crates/octos-cli/src/profiles.rs:180-376`。与本任务相关的两个键：

- `config.llm`：`Option<LlmProfileConfig>`（`profiles.rs:182-184`）。
- `config.env_vars`：`HashMap<String, String>`（`profiles.rs:268-272`）——**键是环境变量名，值是私密凭据本体或 keychain 标记**；octos 注释明确「Low-level environment overrides only (API keys, secrets, escape hatches)」。

其余字段（`mcp_servers`、`hooks`、`sandbox`、`memory`…）本机留空即可，合并写不会动它们。

### 1.2 写盘侧的 envelope 自愈（OctoSense llm-config）

`$OS/apps/ai-providers/config/src/profile.rs`：

- `heal_envelope`（`profile.rs:186-199`）：`id` 缺省填 `"_main"`；`name` 缺省填 `"Main"`；`enabled` **无条件置 true**（`profile.rs:193`）；`created_at` 缺省填当前时间，`updated_at` 始终刷新为 `chrono::Utc::now().to_rfc3339()`（`profile.rs:194-198`）。
- 因此**只要经过宿主 sheet 保存，文件一定是完整 envelope**；只有手写文件才会缺字段。
- env var 名校验：`$OS/apps/ai-providers/config/src/lib.rs:210-216`（`[A-Z_][A-Z0-9_]*`，≤128 字节；首字符不能是数字）。

### 1.3 原子写与权限

`$OS/apps/ai-providers/config/src/profile.rs:312-342`（`write_atomic`）：

- 临时文件 `. _main.json.<pid>.<nanos>.tmp`（`profile.rs:323`），`create_new`（`profile.rs:326`）；
- Unix 下 `opts.mode(0o600)`（`profile.rs:330`）；`write_all` + `sync_all`（`profile.rs:333-334`）；`rename` 覆盖目标（`profile.rs:336`）；失败删临时文件（`profile.rs:338-339`）。
- 测试断言 0600 且无残留临时文件：`profile.rs:415-422`。
- octos 自己的 `ProfileStore::save` 同样原子 + 0600：`$OCT/crates/octos-cli/src/profiles.rs:1810-1830`。

---

## 2. `config.llm.primary` 的结构与合法值来源

### 2.1 octos 结构

- `LlmProfileConfig`：`$OCT/crates/octos-cli/src/profiles.rs:819-826` —— `primary: Option<LlmModelSelectionConfig>`，`fallbacks: Vec<LlmModelSelectionConfig>`。
- `LlmModelSelectionConfig`：`profiles.rs:829-880` 一带：
  - `family_id: Option<String>`（`profiles.rs:831-832`）——**必填才有意义**，缺它该 selection 判空（见 2.3）；
  - `model_id: Option<String>`（`profiles.rs:834-835`）；
  - `route: Option<LlmRouteConfig>`（`profiles.rs:837-838`）；
  - 可选附加：`model_hints`、`cost_per_m`、`strong`、`temperature`（有限值 0.0–2.0）、`top_p`（0.0–1.0）、`reasoning_effort`、`context_window`（`profiles.rs:839` 之后各字段）。
- `LlmRouteConfig`：`profiles.rs:886-900`：
  - `route_id: Option<String>`（如 `official`/`autodl`；**缺失即官方路由**，见 `catalog.rs` 说明）
  - `label`、`base_url`、`api_key_env`、`api_type`（`"openai" | "anthropic" | "responses"`）。

### 2.2 合法值从哪里查

- **family_id**：`$OS/apps/ai-providers/config/src/registry.rs:50-94`（`ALL` 表，镜像 `$OCT/crates/octos-llm/src/registry/*.rs`，漂移测试 `tests/registry_drift.rs` 对照 `$OCT_SRC` 重读）。解析大小写不敏感、支持别名：`registry.rs:102-106`。
- **model_id**：`$OS/apps/ai-providers/config/data/model_catalog.json`（`updated_at: SEED` 的 vendored 副本，来源 `config/data/README.md:1-12`）。每个 family 的模型带 `context_window`、价格、`default: true` 标记。
- **key_env（默认 api_key_env）**：`registry.rs:114-130` `key_env_for(family)`；只有非默认值才写进 `route.api_key_env`：`profile.rs:264-269`。
- **route 语义**：官方路由 = 不写 `route_id`（octos 读缺失为 official）：`$OS/apps/ai-providers/config/src/catalog.rs:28, 61-65`、`profile.rs:246-255, 293-295`；目录内非官方路由才写 `route_id/label/base_url/api_key_env`：`profile.rs:249-255`。
- **api_type**：`$OS/apps/ai-providers/config/src/lib.rs:33-40`（`openai` / `anthropic` / `responses`，精确小写，`lib.rs:52-60`）。

### 2.3 MiniMax 的合法取值（注册表 + 目录）

| 项 | family `minimax`（国际） | family `minimax-cn`（国内 Token-plan） |
|---|---|---|
| family_id | `minimax`（`registry.rs:77-78`） | `minimax-cn`，别名 `minimaxi`（`registry.rs:75-76`） |
| key env（默认 api_key_env） | `MINIMAX_API_KEY` | `MINIMAX_CN_API_KEY`（接受别名 `MINIMAX_API_KEY`） |
| 默认 base_url | `https://api.minimax.io/v1`（`registry.rs:78`；octos 原生 `$OCT/crates/octos-llm/src/registry/minimax.rs:15`） | `https://api.minimaxi.com/v1`（`registry.rs:76`；`minimax_cn.rs`） |
| 默认 model | `MiniMax-M3`（`registry.rs:78`，目录 `default: true`） | `MiniMax-M3`（目录 `default: true`） |
| 目录内可选 model_id | `MiniMax-M2`、`MiniMax-M2.1`、`MiniMax-M2.1-highspeed`、`MiniMax-M2.5`、`MiniMax-M2.5-highspeed`、`MiniMax-M2.7`、`MiniMax-M3`（均见 `config/data/model_catalog.json`，`M2.5` 还带 `wisemodel` 端点） | `MiniMax-M3`（带 `minimax-cn` 端点 `https://api.minimaxi.com/v1`、`MINIMAX_CN_API_KEY`） |

### 2.4 primary 判空/归一化（「no profile」的模型层）

`$OCT/crates/octos-cli/src/profiles.rs:1156-1175`（`normalize_llm_contract`）+ `1234-1249`（`LlmModelSelectionConfig::is_empty`）：
没有 `family_id` 且 `model_id`/`route`/hints/cost/strong/context_window 全空的 selection 被丢弃；`has_llm_selection`：`profiles.rs:1148-1154`。OctoSense 侧读侧同样跳过无 `family_id` 的 selection：`profile.rs:77, 279-283`。

---

## 3. `config.env_vars` 的语义与注入链

### 3.1 是什么

`$OCT/crates/octos-cli/src/profiles.rs:268-272`：`env_vars: HashMap<String,String>`——**键 = 环境变量名，值 = 凭据本体或 keychain 标记**。keychain 标记：`"keychain:"`（账号=变量名）或 `"keychain:<ACCOUNT>"`（octos 用 `<ENV>::<profile id>` 惯例）：
`$OS/apps/ai-providers/host-service/README.md:203-218`、`$OS/apps/ai-providers/config/src/profile.rs:16-21, 37-42`、`vault.rs:45-51`。

### 3.2 哪些键是 host 侧私有凭据字段（只列键名与类型）

- 全部形如 `<FAMILY>_API_KEY` 的 provider 密钥环境变量（键名清单以 `registry.rs:50-94` 的 `key_env`/`key_env_aliases` 为准）。本任务相关：`MINIMAX_API_KEY`（`minimax` 族）、`MINIMAX_CN_API_KEY`（`minimax-cn` 族）。
- 类型均为 **string secret**（API key / token），放 `config.env_vars.<NAME>`（值为 secret）或 `keychain:` 标记（真值在 vault）。
- 同族第二个路由会拿到独立槽位 `<FAMILY>_<n>_API_KEY`（n=2,3,…）：`host-service/README.md:186-196`。
- 特例：`VERTEX_SA_JSON` 是 service-account JSON（同走 keychain）：`registry.rs:59-60`。

**落点（Linux，必须区分两层）**：`host-service/src/vault.rs:66-80` 的写入侧 vault 是
`<core_dir>/secrets/<ENV>`；但固定 octos CLI 的运行时解析器
`$OCT/crates/octos-cli/src/auth/keychain.rs:235-292` 读取的是
`$HOME/.octos/secrets/<ACCOUNT>`。灾后恢复实测把密钥只放前者会报
`MINIMAX_API_KEY not set or empty`。本项目的无界面恢复脚本因此写后者；profile 仍只写
`keychain:` 标记。两处同名目录不是同一个 keychain。

### 3.3 如何注入共享 kernel / 子进程

- ProfileRuntime bootstrap 第 6 步：`$OCT/crates/octos-cli/src/runtime/profile.rs:1103-1105` —— `crate::auth::keychain::resolve_env_vars(&profile.config.env_vars)` 得到 credentials，注释明确「Used by MCP, plugin spawns, and the shell tool when a profile-scoped env var is referenced」。
- 第 8 步：同文件 `1112-1127` 一带构建 `plugin_env_template`（`OCTOS_DATA_DIR` / `OCTOS_HOME` / `OCTOS_PROFILE_ID` 等 + profile 的搜索/一方 skill 环境变量），供插件/子进程 spawn 时注入。
- LLM provider 自身只从自己路由声明的 `api_key_env` 读键：`$OCT/crates/octos-cli/src/runtime/profile.rs:174`（「resolves ONLY from its declared api_key_env (profile env_vars / …)」）。
- 因此：**改 env_vars 后必须重启共享 kernel**（内核只在启动时读 profile）——即 `octosense_kernel::restart()`：`host-service/src/lib.rs:285-293`。

---

## 4. 解析与失败码：`profile_unresolved` 在哪抛出

### 4.1 抛出链（自底向上）

1. `profile_unresolved_error`：`$OCT/crates/octos-cli/src/api/ui_protocol_transport.rs:10237-10246`
   —— 消息 `profile '{profile_id}' is not configured for this AppUI session`，data `{"kind":"profile_unresolved","profile_id":…,"recoverable":true,"recovery":"create or select a local profile before opening the session"}`。
2. `profile_is_known`：`ui_protocol_transport.rs:10258-10266` —— store 里有该 id **或** 能解析出 session profile runtime **或**（无 store 且 id==`_main`）才算已知。
3. `ensure_known_profile`：`ui_protocol_transport.rs:10268-10274` —— 未知即抛。
4. 调用点：
   - `session/open`：`open_session_result`，`ui_protocol_transport.rs:22606`（函数）、`22633`（调用）；
   - WS `turn/start`：`handle_turn_start_with_accept`，`25356`（函数）、`25488`（调用）；
   - review start：`24792`/`24844`；voice admission：`25022`/`25029`；`raw_session_status_result`：`11961`。
5. AppUI 客户端侧包装：`$OS/crates/app-peers/src/broker.rs:2280-2286`（`rpc_error_text`：`data.kind` 存在时格式化成 `"{message} ({kind})"`）——即日志里 `… (profile_unresolved)` 后缀的来源。
6. shell 日志行：`$OS/crates/shell/src/agents.rs:159` —— `agents: {id}'s agent could not be prepared: {e}`；`{e}` 来自 `$OS/crates/ai-host/src/contained.rs:144-148`（`prepare` → peer `service.prepare()`）。peer 打开 session 时撞到第 4 步，故「agent 准备失败」与「profile 未配置」是同一件事。

### 4.2 各情形对照（以 `<core_dir>/profiles/_main.json` 为对象，本机 core_dir = `/root/oncue-runtime/state/octos-core`）

| 磁盘状态 | 解析行为 | 结果 |
|---|---|---|
| **文件不存在（当前实测状态）** | `store.get("_main")` → None；`state.profiles` 无 `_main`（启动期 `serve.rs:1222-1233` 没可 bootstrap 的 profile）；store 存在故无 `_main` 豁免 | `ensure_known_profile` 抛 **profile_unresolved**（`ui_protocol_transport.rs:10237-10246, 22633`） |
| **裸 `{config}`（无 envelope）** | `id/name/created_at/updated_at` serde 必填 → `serde_json::from_str::<UserProfile>` 失败（`profiles.rs:1766-1767`）；`list()` 直接 skip 并 warn「skipping invalid profile」（`profiles.rs:1744-1746`）；`profile_is_known` 里 `.ok()` 把错误吞成 None | 等同 **no profile** → 同样 profile_unresolved |
| **envelope 完整但 `enabled:false`** | `store.get` → Some → **能过** `ensure_known_profile`；但启动期 eager bootstrap 被跳过（`serve.rs:1224`）；按需 lazy bootstrap 注释明确 enabled 不拦 AppUI 会话（`ui_protocol_transport.rs:24112-24118`） | 行为依赖启动路径、且违反甲方规则；**必须 `true`**（宿主保存侧也会强制置 true：`profile.rs:193`） |
| **`enabled:true` 但无 llm selection** | 能过 `ensure_known_profile`；`has_llm_selection()` 为假 | 另一个 typed 错误 `profile_unconfigured`（`ui_protocol_transport.rs:23210-23235`）或 lazy bootstrap 返回 None → runtime 不可用 |
| **envelope 完整 + `config.llm.primary` 有 family_id/model_id** | store 有、runtime 可 bootstrap（`ensure_session_profile_runtime`，`ui_protocol_transport.rs:24061-24163`） | session/open、turn/start 正常 |

【实测】当前磁盘：`/root/oncue-runtime/state/octos-core/profiles/` **为空**（无 `_main.json`）；
`/root/oncue-runtime/state/logs/octosense-rinx.log:39` 已有
`agents: oncue-screening-room's agent could not be prepared: profile '_main' is not configured for this AppUI session (profile_unresolved)`；
`/root/oncue-runtime/state/octos-core/logs/serve.2026-10-01.log` 末行有
`WARN steer inbox sweep: AppState has NO profiles registered; …`（抛出点 octos 侧 `ui_protocol_transport.rs:27057` 一带）。
两者互为印证：共享内核侧同样没有任何 profile 注册。

---

## 5. host-owned sheet 的保存流程

### 5.1 触发点与写盘链（自上而下）

| 步骤 | 位置 |
|---|---|
| 宿主 sheet 的 Save 按钮 | `$OS/apps/ai-providers/host-service/src/sheets.rs:582-592`（`save()`：`host.request("llm.sheet.submit", form(false), …)`） |
| 前置：Test connection 必须通过才允许保存；网络失败时 sheet 提供「Save without testing」 | `host-service/README.md:13-22`、`sheets.rs:815`（`Bypass{text: "Save without testing"…}`） |
| 「submit 只能来自宿主 sheet」 | `host-service/src/lib.rs:23-29`（`dispatch` 拒绝其他人携带 key/PIN/code） |
| 加锁的读-改-写 | `host-service/src/lib.rs:311-327`（`Shared::change`：无变化不写盘也不重启内核，`lib.rs:320-323`） |
| 写 profile | `host-service/src/model.rs:284-321`（`ProfileStore::save`：key 先入 vault 失败才入 profile（`model.rs:286-299`）→ `profile::save_merge`（`model.rs:303`）→ 删除无人再读的 env（`model.rs:304-316`）→ 回读刷新（`model.rs:317-319`）） |
| 重启共享内核 + 通知 shell | `host-service/src/lib.rs:285-293`（`changed()`：`octosense_kernel::restart()`，无内核时为 no-op，再调 `on_changed`） |

**写哪条路径**：`<core_dir>/profiles/_main.json`（`profile.rs:54-57`）。core_dir 解析优先级：
`octosense_kernel::core_dir()`（宿主注册时显式传入）→ `$OCTOS_APP_CORE_DIR` → `$HOME/octos-home/.octos`
（`profile.rs:44-52`、`$OS/crates/kernel/src/dirs.rs:21-39`、`host-service/src/lib.rs:270-283`、注册处 `$OS/crates/ai-host/src/lib.rs:365-387`）。

**原子写**：是（临时文件 + `rename`，见 1.3）。**文件权限**：0600（`profile.rs:330`；`profile.rs:415-420` 测试断言）。

**之后如何重启共享 kernel**：每次变更（保存、重排、删除、导入）都调用 `octosense_kernel::restart()`
（`host-service/src/lib.rs:287-289`；README.md:76-79）。重启是分代的（generation），
日志在 shell 日志里（`$OS/crates/kernel/src/kernel.rs`）：

| 日志特征 | 位置 |
|---|---|
| `octos-core: starting kernel {generation}: {…}` | `kernel.rs:308` |
| `octos-core: kernel {generation} did not start: {e}`（失败特征） | `kernel.rs:315` |
| `octos-core: stopping kernel {generation}: {reason}` | `kernel.rs:385` |
| `octos-core: embedded core stopped: {…}`（OHOS 内嵌路径） | `kernel.rs:143` |

**如何确认重启成功**（三层，都要看）：

1. shell 日志出现**新的、generation 递增**的 `starting kernel`，且**没有**紧随的 `did not start`（`kernel.rs:308/315`）。
2. octos 内核自己的日志（`/root/oncue-runtime/state/octos-core/logs/serve.<date>.log`）出现新一轮启动：`initializing profile store and process manager`（`$OCT/crates/octos-cli/src/commands/serve.rs:1158`），随后
   `ProfileRuntime bootstrapped for /api/chat`，字段 `profile_id=_main provider=minimax model=<MINIMAX_MODEL>`（`serve.rs:1259-1265`）。
3. **旧阻塞行不复现**：新日志里不再出现 `AppState has NO profiles registered`（`ui_protocol_transport.rs:27057` 一带），shell 日志里 `oncue-screening-room` 的 agent 从 `could not be prepared` 变为 `is prepared`（`$OS/crates/shell/src/agents.rs:158`）。

### 5.2 README 原样引用（命令/代码照抄，**不要执行**）

注册 shell 侧服务（`host-service/README.md:37-57`）：

```rust
// The kernel first (octosense-kernel): on a phone its core dir is
// <data dir>/octos-home/.octos, on a desktop $OCTOS_APP_CORE_DIR, else
// $HOME/octos-home/.octos.
octosense_kernel::configure(octosense_kernel::Options::default().app_data_dir(data_dir));

// Defaults: the kernel's core dir, the platform's vault, no scanner.
octosense_llm_service::register();

// What a shell normally passes:
octosense_llm_service::register_with(
    octosense_llm_service::Options::default()
        .core_dir(octosense_kernel::core_dir().unwrap()) // the same dir, said out loud
        .scanner(Arc::new(MyScanner::default()))  // phone only
        .image_picker(Arc::new(MyPicker::default())) // a QR from a picture
        .image_drops(true),                       // desktop: drops go to offer_image
);
```

测试命令（`host-service/README.md:222-226`）：

```sh
cargo test --workspace
```

macOS keychain 测试需显式要求（`README.md:233-234`）：

```
cargo test -p octosense-llm-service -- --ignored keychain
```

model 服务测试与 live 检查（`README.md:256-258`）：

```sh
cargo test --locked -p octosense-llm-service --test complete
DEEPSEEK_API_KEY=… cargo run --locked -p octosense-llm-service --example model_complete_live
```

## 6. 「官方已实测成功的 MiniMax 值」在本机的来源

### 6.1 非凭据取值该从哪里读

| 值 | 取值 | 来源 |
|---|---|---|
| base URL（默认） | `https://api.minimax.cn/v1` | `$ON/dev/OnCue/oncue/server/engine.py:234`（`__init__` 默认参数）、`engine.py:260`（`from_environment` 读 `MINIMAX_BASE_URL`，默认同值） |
| 合法 host 白名单 | `api.minimax.cn` / `api.minimaxi.com` / `api.minimax.io`（HTTPS、路径恰为 `/v1`、端口仅 443） | `engine.py:236-241` |
| model（默认） | `MiniMax-M2.7` | `engine.py:235`、`engine.py:261`（`MINIMAX_MODEL` 覆盖） |
| 实测留档 | `"mode": "minimax"`、`"model": "MiniMax-M2.7"`、`"total_tokens": 1136` | `$ON/dev/OnCue/evidence/minimax-live-result.json:69-72` |
| 运行方式（原样引用） | `MINIMAX_API_KEY_FILE=/absolute/path/minimax.key python3 oncue/server/app.py` | `$ON/dev/OnCue/README.md:22-26`；`$ON/dev/OnCue/oncue/README.md:36-42`（`chmod 600`、默认模型、可切 `api.minimaxi.com` / `api.minimax.io`） |
| 凭据文件**路径**（0600） | `/root/oncue-runtime/state/minimax.key`（本 runbook 不读取、不打印其内容） | 【实测】`ls -l`：`-rw------- 1 root root 126 … state/minimax.key` |

### 6.2 Python 侧与内核侧取值不一致的注意点（必读）

- Python 实测走的是 **`https://api.minimax.cn/v1`**（`engine.py:234`），而 octos 注册表中：
  - `minimax` 族默认 base 是 `https://api.minimax.io/v1`（`registry.rs:78`；`$OCT/crates/octos-llm/src/registry/minimax.rs:15`）；
  - `minimax-cn` 族默认 base 是 `https://api.minimaxi.com/v1`（`registry.rs:76`）。
  - `api.minimax.cn` **不是**任何一族的默认 base。要在内核侧复现实测值，保存时必须走
    wizard 的 **custom base URL** 分支（README.md:13-22；`lib.rs:48-52`），由
    `route.base_url` 显式落盘（`profile.rs:256-259`）；否则内核会打到 `.io` 端点（国内 key 会 401）。
- model：实测 `MiniMax-M2.7` 在目录中存在（`config/data/model_catalog.json`，family `minimax`），
  不是该族 `default: true` 项（默认是 `MiniMax-M3`）——保存时选具体 model id，别依赖默认。
- key env：`minimax` 族读 `MINIMAX_API_KEY`（`registry.rs:77-78`）。宿主 sheet 的 host vault
  与 octos CLI 运行时 keychain 路径不同；本项目直接启动 kernel 时，原始 key 必须位于
  `$HOME/.octos/secrets/MINIMAX_API_KEY`（0600），profile 里只留 `keychain:` 标记。
- Python 侧成功（`minimax-live-result.json`）**不是**原生回合证据，不能互相代替
  （原生验收清单第 11 项：`$ON/dev/OnCue/oncue/docs/NATIVE-WORKFLOW.md:29`）。

---

## 7. 目标状态（envelope 样例；凭据一律占位符）

`/root/oncue-runtime/state/octos-core/profiles/_main.json`（宿主保存后即为该形态；时间字段由宿主写盘时生成，此处为占位）：

```json
{
  "id": "_main",
  "name": "Main",
  "enabled": true,
  "created_at": "<RFC3339 UTC，宿主保存时生成>",
  "updated_at": "<RFC3339 UTC，宿主保存时生成>",
  "config": {
    "llm": {
      "primary": {
        "family_id": "minimax",
        "model_id": "MiniMax-M2.7",
        "route": {
          "base_url": "https://api.minimax.cn/v1",
          "api_type": "openai"
        }
      },
      "fallbacks": []
    },
    "env_vars": {
      "MINIMAX_API_KEY": "keychain:"
    }
  }
}
```

说明（均为上文 file:line）：

- `enabled: true` 会被宿主强制（`profile.rs:193`）；`route.api_key_env` 仅在非默认键名时出现，
  这里用默认 `MINIMAX_API_KEY` 故省略（`profile.rs:264-269`）；
- `"keychain:"` 表示真值由 octos CLI keychain 的 `$HOME/.octos/secrets/MINIMAX_API_KEY`
  解引用——**占位符，不是凭据**；不要误指向 `<core_dir>/secrets` 的 host vault；
- 若选 `minimax-cn` 族 + `MiniMax-M3`，则 `family_id: "minimax-cn"`、`model_id: "MiniMax-M3"`，
  路由可省 `base_url`（用默认 `https://api.minimaxi.com/v1`），键名 `MINIMAX_CN_API_KEY`。
  **两者不要混搭**：国内 `.cn` 端点 + `minimax`（国际族）组合必须显式写 `base_url`，否则不生效。

---

## 8. 界面执行步骤（AI providers 系统应用；每步预期现象）

前置（只读核对，不做桌面操作时可先由操作者确认）：

- 宿主 shell 已在运行；`/root/oncue-runtime/state/octos-core/profiles/` 当前为空（第 4.2 节实测）。
- MiniMax key 已就位：`/root/oncue-runtime/state/minimax.key`（0600；本机实测值来源见第 6 节）。
  界面输入 key 时**由操作者粘贴**，runbook 不记录、不回显。

步骤：

1. 打开宿主里的 **AI providers** 系统应用（`os.ai-providers`）。
   预期：应用列出当前 providers（当前应为空列表）；界面只显示 key 状态（`set ••••1234` / `missing` / `not needed`），不显示 key 值（`host-service/src/lib.rs:9`）。
2. 选择 **Add provider**（或编辑既有条目）。
   预期：弹出**宿主 sheet**（五步向导：family → model → route → key → test+save；`README.md:13-22`、`sheets.rs:243`）。注意 key 只在这个 sheet 里输入，App 本身永远看不到 key（`README.md:3-7`）。
3. 第 1 步 family：选择 **MiniMax**（国际族，`minimax`）。
   预期：列表按字母序出现各 family（`lib.rs:10`）；MiniMax 一行显示其模型与 key 需求状态（`key_required=true`，`registry.rs:77-78`）。
4. 第 2 步 model：选择 **MiniMax-M2.7**（实测模型）。
   预期：下拉里出现 `MiniMax-M2 / M2.1 / M2.1-highspeed / M2.5 / M2.5-highspeed / M2.7 / M3`，
   带上下文/价格（`lib.rs:11`；目录条目见 `config/data/model_catalog.json`）。
5. 第 3 步 route：选择 **custom base URL**，填 `https://api.minimax.cn/v1`，协议 `openai`。
   预期：目录路由（official 等）之外有 custom 项；填错协议/URL 保存时按 `route.api_type` / `base_url` 落盘（`lib.rs:48-52`、`profile.rs:240-263`）。**此步是复现实测值的关键**（第 6.2 节）。
6. 第 4 步 key：输入 MiniMax API key（操作者粘贴；runbook 不记录）。
   预期：只显示脱密状态；保存动作此刻未发生。
7. 第 5 步 **Test connection**。
   预期：`llm.test` 打一次极小请求，返回 `{ok, ms}`（`lib.rs:18`、`sheets.rs:554-576` 一带的 `test()`）。
   若网络不通：sheet 提供 **Save without testing**（`README.md:16-18`、`sheets.rs:815`）——能用但不推荐，最好先修网络。
8. 点 **Save**。
   预期：`llm.sheet.submit` 落盘 → 合并写 `<core_dir>/profiles/_main.json`（原子 0600）→
   **共享 kernel 自动重启**（`sheets.rs:582-592` → `lib.rs:311-327` → `model.rs:303` → `lib.rs:287-289`）。
   shell 日志出现新一代 `octos-core: starting kernel N+1`（`kernel.rs:308`），无 `did not start`。
9. （幂等复核）回到 provider 列表。
   预期：MiniMax 显示为 **primary**（首位），key 状态为已设置（`lib.rs:9`）。
   若已有其他 provider，用 `llm.set_primary` / `llm.move`（`lib.rs:15-16`、`lib.rs:1146`）把 MiniMax 置 0 位。

---

## 9. 保存后核对清单（全部只读、脱密）

### 9.1 文件存在性与权限

```bash
ls -l /root/oncue-runtime/state/octos-core/profiles/
stat -c '%a %U:%G %s %n' /root/oncue-runtime/state/octos-core/profiles/_main.json
```

预期：目录里只有 `_main.json`（无 `*.tmp` 残留，`profile.rs:336-339`）；权限 **600**，属主为宿主进程用户。

### 9.2 字段/类型/启用状态（脱敏：只打印键与类型，不打印 env_vars 的值）

```bash
python3 - <<'PY'
import json,pathlib
p=pathlib.Path('/root/oncue-runtime/state/octos-core/profiles/_main.json')
v=json.loads(p.read_text())
print('envelope:', {k:type(v.get(k)).__name__ for k in ('id','name','enabled','created_at','updated_at')})
print('id/name/enabled =', v.get('id'), '/', v.get('name'), '/', v.get('enabled'))
cfg=v.get('config',{}); llm=cfg.get('llm',{})
pr=llm.get('primary') or {}
print('primary.family_id =', pr.get('family_id'), '| primary.model_id =', pr.get('model_id'))
print('primary.route =', {k:pr.get('route',{}).get(k) for k in ('base_url','api_type','route_id','api_key_env')})
ev=cfg.get('env_vars',{})
print('env_vars key types:', {k:type(x).__name__ for k,x in ev.items()})   # 只打印键名与类型，不打印值
print('env_vars markers  :', {k:(x=='keychain:' or str(x).startswith('keychain:')) for k,x in ev.items()})
PY
```

预期：`id == '_main'`、`name` 为非空字符串、`enabled is True`、`created_at`/`updated_at` 为字符串；
`primary.family_id` 为 `minimax`、`model_id` 为 `MiniMax-M2.7`、`route.base_url` 为 `https://api.minimax.cn/v1`；
`env_vars` 的键为 `MINIMAX_API_KEY`，值为 `keychain:` 标记（或原值——**不要在输出里回显**）。

### 9.3 octos CLI keychain（Linux secrets 目录）

```bash
ls -l "$HOME/.octos/secrets/" 2>/dev/null
```

预期：存在 `MINIMAX_API_KEY` 文件、权限 0600，父目录 0700。只列文件名，不读内容。
`<core_dir>/secrets` 是 OctoSense host vault，不能用它证明 octos CLI 已能解引用。

### 9.4 共享 kernel 重启的日志特征

```bash
grep -n "octos-core: starting kernel" /root/oncue-runtime/state/logs/octosense-rinx.log | tail -3
grep -n "octos-core: kernel .* did not start" /root/oncue-runtime/state/logs/octosense-rinx.log | tail -3
grep -n "initializing profile store\|ProfileRuntime bootstrapped" /root/oncue-runtime/state/octos-core/logs/serve.<date>.log | tail -5
```

预期：`starting kernel` 的 generation 比保存前**+1**；**没有**新的 `did not start`；
serve 日志出现 `ProfileRuntime bootstrapped for /api/chat` 且 `profile_id=_main provider=minimax model=MiniMax-M2.7`
（`serve.rs:1259-1265`）。

### 9.5 `profile_unresolved` 是否消失

```bash
grep -n "profile_unresolved\|could not be prepared" /root/oncue-runtime/state/logs/octosense-rinx.log | tail -10
grep -n "NO profiles registered" /root/oncue-runtime/state/octos-core/logs/serve.<date>.log | tail -3
grep -n "oncue-screening-room's agent" /root/oncue-runtime/state/logs/octosense-rinx.log | tail -5
```

预期变化：

- **旧的** `profile '_main' is not configured … (profile_unresolved)` 行（如 `octosense-rinx.log:39`）作为历史证据保留；
- 保存+重启**之后**出现 `agents: oncue-screening-room's agent is prepared (its peer is listed for the system agent)`
  （`$OS/crates/shell/src/agents.rs:158`）；
- 新一轮 `agent could not be prepared: … (profile_unresolved)` **不再出现**（时间戳晚于 9.4 的重启行）；
- serve 新日志里 `NO profiles registered`（octos 侧 `ui_protocol_transport.rs:27057` 一带）**不再出现**。

---

## 10. 之后：同一个 Rinx Developer 的 OnCue 实例的 session.open / turn.start 检查点

**同一实例的定义**：此前发起过 Ask（宿主日志 `ask: oncue-screening-room's agent`，
`$OS/crates/shell/src/lib.rs:3572-3575`）、consent 已落盘
（`$ON/state/octosense/approvals/consent.json`，`oncue-screening-room.allowed = true`，
见 `$ON/dev/OnCue/evidence/LOGS-EXCERPT.md` 旁证节）的那个 Rinx Developer 里的 OnCue 实例。
不要新开一个实例充数。

小程序侧调用点（用于对照日志）：`cue_rehearse` 发起 `octos.session.open` + `octos.turn.start`，
`cue_invalidate` / `cue_stop_wait` 发 `octos.turn.interrupt`
（`$ON/dev/OnCue/evidence/hub-review-answers.md:15-16`；实现 `$ON/dev/OnCue/oncue/bundle/main.splash:147-194`）。

要留的证据（每项都给「文件/日志路径 + 脱敏摘录」）：

1. **session.open 成功**：宿主 shell 日志 / 共享内核 serve 日志里该 app 的 session 建立记录
   （对应 AppUI `session/open` 成功路径 `ui_protocol_transport.rs:22606+`）。
2. **turn.start 真实模型回合**：octos 侧 turn/会话日志行（此前完全缺失，是本次要补的核心证据；
   缺失原因即第 4.2 节）。必须在 octos 日志里看到 provider=minimax、model=MiniMax-M2.7 的真实调用。
3. **七块输出**：小程序把回复按 `\n@@@\n` 切分，**必须恰为 7 块且每块非空**：
   第 1 块 20–60 字现场摘要，第 2/3 块路线 A 假设对白+依据 / 建议台词，第 4/5 块路线 B，第 6/7 块路线 C
   （`bundle/main.splash:143`）。切分校验与失败提示：`main.splash:171-186`
   （`!=7` →「Agent 尚未形成七块完整剧本，请再试一次。」；空块 →「这份剧本有一块是空的，请再试一次。」）。
   留存：回复**脱敏文本**（可含房间引用编号，不含聊天正文全文与任何凭据）+ 界面状态。
4. **脱敏字段**：任何留档只保留：房间 ID、事件 ID、时间戳、发送者显示名、正文**长度**、
   provider/model 名、token 计数（参照 `$ON/state/evidence/matrix-room-read.json` 的既有做法）。
   **不摘抄**：消息正文、API key、`env_vars` 值、`keychain:` 以外的凭据、PIN、bearer。
5. **原生截图路径**：完整原生窗口截图存入 `$ON/dev/OnCue/evidence/`，图上**不得含凭据**
   （宿主验收第 10 项：`$ON/dev/OnCue/oncue/docs/NATIVE-WORKFLOW.md:28-29` 一带的实房间载入与截图要求）。
   本 runbook 不读取、不内联任何图片。
6. **失败分支也要实测**（验收第 11/12 项，`NATIVE-WORKFLOW.md:29-31`）：provider 不可用、空块/格式不符时的
   真实反馈文案；等待期间停止、90 秒超时、连续请求旧回复不覆盖新结果。

---

## 11. 明确「不要做什么」

- **不配置未知 profile**：只配 `_main`；不手写 `default` 或任何其他 id 的文件
  （`MAIN_PROFILE_ID = "_main"`：`$OCT/crates/octos-core/src/types.rs:494`；
  AppCard 命名其他 id 会被拒：`$OS/apps/appcard/app/app/src/lib.rs:6370-6380`）。
- **不手写/伪造 profile 文件**：本次只调研并写本 runbook；profile 一律由宿主 AI providers 界面保存产生
  （保存链见第 5.1 节）。裸 `{config}` 等于 no profile（第 4.2 节）。
- **不生成假的模型回合**：不本地伪造 `reply.data.text`、不拿样例/演示路线冒充模型结果
  （样例与演示在界面有明确标记：`bundle/main.splash:109-133` 的 `cue_demo_routes`）。
- **不把服务注册/同步层成功当作原生回合成功**：provider 配置成功、kernel 重启成功、
  agent prepared 都只是前置条件；真实证据只能是 octos 侧的 session/turn 日志与七块输出
  （`NATIVE-WORKFLOW.md:29`；Python/浏览器 MiniMax 成功不能代替）。
- **不打印凭据**：任何报告/文件不出现 key、token、PIN、私钥值；只写键名与类型
  （第 3.2 节）。核对命令只用 `ls -l` / 类型检查，不 `cat` 凭据文件
  （`state/minimax.key`、`state/octos-core/secrets/*`、`state/hub-keys/*`）。
- **不动桌面**：不做鼠标/键盘/截图/VNC 操作（本任务约束；另有一个执行体正在用桌面实测）。
- **不改宿主源码、不 git commit/push、不写 profile 文件**（本任务约束）。

---

## 附：file:line 速查

| 事实 | 位置 |
|---|---|
| profile 文件路径 `<core_dir>/profiles/_main.json` | `$OS/apps/ai-providers/config/src/profile.rs:54-57` |
| envelope 自愈（id/_main、name/Main、enabled 强制 true、时间字段） | `profile.rs:186-199` |
| 原子写 + 0600 | `profile.rs:312-342`（mode `330`、rename `336`） |
| 裸 `{config}` 被当 no profile 的注释 | `profile.rs:23-28` |
| env 名校验 | `$OS/apps/ai-providers/config/src/lib.rs:210-216` |
| api_type 枚举 | `lib.rs:33-40` |
| family/key_env 注册表 | `$OS/apps/ai-providers/config/src/registry.rs:50-94, 114-130` |
| 模型目录（MiniMax 行） | `$OS/apps/ai-providers/config/data/model_catalog.json` |
| official 路由语义 | `$OS/apps/ai-providers/config/src/catalog.rs:28, 61-65` |
| UserProfile 结构（必填 id/name/config/created_at/updated_at） | `$OCT/crates/octos-cli/src/profiles.rs:146-177` |
| LlmProfileConfig / Selection / Route | `profiles.rs:819-826 / 829-880 / 886-900` |
| llm 归一化（无 family_id 判空） | `profiles.rs:1148-1175, 1234-1249` |
| ProfileStore list/get（非法 JSON skip） | `profiles.rs:1709-1756, 1758-1784` |
| serve 启动期 bootstrap 跳过 disabled | `$OCT/crates/octos-cli/src/commands/serve.rs:1220-1233`（skip `1224`） |
| `ProfileRuntime bootstrapped` 日志 | `serve.rs:1259-1265` |
| profile_unresolved_error / profile_is_known / ensure_known_profile | `$OCT/crates/octos-cli/src/api/ui_protocol_transport.rs:10237-10246 / 10258-10266 / 10268-10274` |
| session/open 调用点 | `ui_protocol_transport.rs:22606, 22633` |
| turn/start(WS) 调用点 | `ui_protocol_transport.rs:25356, 25488` |
| 懒加载 bootstrap 不因 enabled 拒绝 AppUI | `ui_protocol_transport.rs:24061-24163`（注释 `24112-24118`） |
| profile_unconfigured（有 profile 无 llm） | `ui_protocol_transport.rs:23210-23235` |
| env_vars → credentials/插件 env 注入 | `$OCT/crates/octos-cli/src/runtime/profile.rs:1103-1127` |
| octos keychain/Linux secrets 解析 | `$OCT/crates/octos-cli/src/auth/keychain.rs` |
| `(profile_unresolved)` 后缀格式化 | `$OS/crates/app-peers/src/broker.rs:2280-2286` |
| shell 日志行（agent could not be prepared） | `$OS/crates/shell/src/agents.rs:158-159` |
| contained prepare → peer | `$OS/crates/ai-host/src/contained.rs:144-148` |
| AppCard 本地内核 profile id `_main` | `$OS/apps/appcard/app/app/src/lib.rs:6313-6322, 6368-6380` |
| llm 服务注册（core_dir=内核） | `$OS/crates/ai-host/src/lib.rs:365-387` |
| sheet Save → submit | `$OS/apps/ai-providers/host-service/src/sheets.rs:582-592` |
| Shared::change 加锁写盘 | `host-service/src/lib.rs:311-327` |
| ProfileStore::save（vault 优先） | `host-service/src/model.rs:284-321` |
| changed() → kernel restart | `host-service/src/lib.rs:285-293` |
| kernel 重启日志特征 | `$OS/crates/kernel/src/kernel.rs:308, 315, 385` |
| vault：Linux secrets 目录 | `host-service/src/vault.rs:66-80`；`README.md:203-218` |
| MiniMax Python 适配器 | `$ON/dev/OnCue/oncue/server/engine.py:233-261` |
| MiniMax 实测留档 | `$ON/dev/OnCue/evidence/minimax-live-result.json:69-72` |
| 凭据文件路径（0600） | `$ON/state/minimax.key` |
| 七块输出契约 | `$ON/dev/OnCue/oncue/bundle/main.splash:143, 171-186` |
| OnCue 会话调用点 | `$ON/dev/OnCue/evidence/hub-review-answers.md:15-16` |
| 宿主验收第 10/11 项 | `$ON/dev/OnCue/oncue/docs/NATIVE-WORKFLOW.md:28-31` |

本文件不含任何密码/token/私钥内容。
