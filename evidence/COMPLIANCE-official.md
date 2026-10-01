# OnCue · 官方文档符合性核对（OctoScript App Design Flow + OctoSense App Hub）

- 编写方式：**只抓取官方文档 + 只读本仓库/镜像/日志**。未执行任何鼠标/键盘/截图/VNC/桌面操作，未 `git commit` / `push`，未改动 `oncue/bundle/` 下任何既有文件（本文件为唯一新增文件）。
- 文档分支：官方文档均按任务要求从 **`master`** 分支抓取（App Hub README 的 `master` 直接 200，未回退 `main`）。
- 核对基准时间：2026-10-01（本机镜像 catalog **sequence 7**，bundle **0.4.1**）。
- 关于 HEAD：核对期间另一名操作者在同一仓库提交，HEAD 由 `ace6231` 前进到 `7d0ca91`（`git log --oneline -3`）；`oncue/bundle` 在此期间**逐字节未变**（`git diff --stat ace6231..HEAD -- oncue/bundle` 为空，且与镜像 0.4.1 工件 `diff -r` 仍 IDENTICAL）。因此"签名后的精确字节在 `9cb14a5`"这一事实不受影响，反而更能说明：**HEAD 会继续前进，`source.commit` 必须在发布瞬间取签名工件所在的那个提交**。
- 文档自述的状态日期：`docs/AI-SERVICES.zh-CN.md` 声明描述 **2026-09-27** 的状态（App Hub `main` = `e8601b8`/`a72989f`，OctoSense `main` = `89787ba`）；`docs/PUBLISHING.md` 声明在 App Hub `79a2c4f` 与 `main`(`6c075d0`) 上于 2026-09-26 验证。我们本机实际运行的 App Hub 源码 rev 为 `0f33211`（见 `evidence/ENDPOINTS.md` §2），与文档所述版本存在漂移，结论以"文档条文"为准，版本差异见差距清单 O6。
- 本文件不含任何密码/token/私钥；涉及密钥只写路径与键名。

---

## 1. 官方要求 → 我们现状 → 判定

| # | 官方要求（出处 + 原文短引用） | 我们现状（证据） | 判定 |
|---|---|---|---|
| 1 | **应用类型与语言**：脚本应用 = `main.splash` 入口；卡片应用 = `page.card`。"应用分为卡片应用（`page.card`）和脚本应用（`main.splash`）。"（App Hub README §发布应用）；"Only `bundle/` … `main.splash` the program"（PUBLISHING §1） | `oncue/bundle/manifest.json` 声明 `main.splash` 入口；`oncue/bundle/main.splash` 428 行 OctoScript/Splash；`bundle/` 仅 5 个文件（`manifest.json`/`listing.json`/`main.splash`/`assets/icon.svg`/`screenshots/01-native-rinx.png`），无符号链接，138 499 B < 8 MB 上限（`find oncue/bundle -type f`、`du -sb`） | **符合** |
| 2 | **能力声明与禁令**：能力列表封闭，未申请即不授予；"Ask for the least the app needs; the scan asks the reviewer to 'name any grant nothing on screen needs'."（CAPABILITIES §The list）；"**Declare every host.** Every `https://` host in `main.splash` is in `network.hosts` … Never `http://`."（AGENTS.md §Rules） | `capabilities` = 6 项（`storage`、`matrix.room_info`、`matrix.read_messages`、`octos.session.open`、`octos.turn.start`、`octos.turn.interrupt`），逐项用途见 `evidence/hub-review-answers.md` Q3；`network.hosts: []`，`main.splash` 中无任何 `http://`/`https://`（grep 实证）；`compute.instruction_budget` 8 000 000 / `memory_bytes` 33 554 432 / `storage.max_bytes` 4 194 304 均在 CAPABILITIES §Other manifest requests 的上限内 | **符合** |
| 3 | **不得持有凭据**："**No secrets in apps.** No password, PIN or one-time-code field, no login form, no API key or token in the bundle. Accounts go through a host service's sheet"（AGENTS.md §Rules）；gate `secrets` 检查拒 `is_password: true` / `TextInputContentType.Password` 等（PUBLISHING §2）；"`card-host` registers **no** services"（HOST-SERVICES §The services that exist） | `main.splash`/`listing.json`/`manifest.json` 中无 `is_password`/`Password`/`OneTimeCode`（grep 实证）；bundle 内无任何 key 文件；模型凭据在设备侧 AI providers（`evidence/RUNBOOK-provider-profile.md`：`config.env_vars` 键名与类型，不写取值）、Matrix 凭据在 Rinx 宿主（`oncue/PRIVACY.md` §Rinx 原生小程序）；仓库内仅 `collaboration/ai2-credential-public.pem`（`BEGIN PUBLIC KEY`，公钥）；`oncue/.env.example` 全为占位空值 | **符合** |
| 4 | **`octos.*` 与模型调用的官方立场**："**No AI feature the device cannot serve.** A contained app cannot ask OctoSense's assistant or a model yet: the `octos.*` capabilities pass the gate, but every call answers `no service answers "octos" on this device`, and `llm` is for system apps only."（AGENTS.md §Rules）；"**目前，商店应用在 OctoSense 设备上还不能向模型或助手提出任何请求。** … `card-host` 也不提供任何宿主服务。请把应用做成不依赖 AI 也完整可用。"（AI-SERVICES §简短回答）；"**No OctoSense shell and not `card-host`**: a call answers `no service answers "octos" on this device`. **Only Rinx's mini-app host serves them.**"（CAPABILITIES §Host services by exact name）；"`octos` \| **None in OctoSense.** … Rinx's mini-app host serves them to bundles imported into Rinx"（HOST-SERVICES） | 我们申请 3 个 `octos.*`，目标宿主正是 Rinx 迷你应用宿主（仓库 README"OctoSense/Rinx 原生版本"、`oncue/docs/NATIVE-WORKFLOW.md` 固定 Rinx `0879548b`）；gate 接受这些名称（`evidence/LOGS-EXCERPT.md` B 组：`card-host: … admitted — capabilities {… "octos.session.open", "octos.turn.interrupt", "octos.turn.start" …}`）；`main.splash:160-186` 对 `r.is_ok == false` 有分支并显示「Agent 暂时不可用：」+ `r.error`，样例路线（`cue_demo_routes`）使应用不依赖 AI 也完整可用 | **部分符合**（官方不禁止、且点名 Rinx 宿主是唯一响应方；但附加 4 项条件，见差距 M6/M7） |
| 5 | **`llm` 与 `os.*` id 仅限系统应用**："`llm` is for system apps only"（AGENTS.md）；"The service answers only `os.*` apps … a store app gains nothing from it: do not request it."（CAPABILITIES `llm` 行）；"`os.*` ids … are reserved for system apps"（CAPABILITIES §Reserved and absent names） | 未申请 `llm`；应用 id `oncue-screening-room` 不落在 `os.`；未使用 `agent`/`profile`；`manifest.agent = null`，无 `tools.json`/`AGENT.md`/`skills/`（同时规避了 AI-SERVICES §测试 所述"Rinx 迷你应用宿主会拒绝声明了 `agent` 的应用包"） | **符合** |
| 6 | **`card-host` 是否提供宿主服务**："`card-host` 不提供任何宿主服务，所以类似 Mail 的应用在其中会显示 `no service answers`"（README §应用中的 AI / §应用能做什么）；"A Mail-style app run in `card-host` gets that 'no service answers' error"（HOST-SERVICES） | 我们在 `card-host` 中只有 admitted 级证据（`evidence/LOGS-EXCERPT.md` B 组 `cardhost.log:9`，0.1.0），0.3.x 起的原生联调全部在 OctoSense Shell（`--module rinx`）与 Rinx Developer 宿主完成；`oncue/docs/NATIVE-WORKFLOW.md` §1 明确"Shell App Hub 里的首帧不能替代此实例的 Matrix/Octos 服务验证"。即：本应用 6 项能力中有 5 项（`matrix.*`×2、`octos.*`×3）**在 `card-host` 与库存 OctoSense Shell 中均无服务方**，我们按此设计了失败分支，但该分支本身**未留取证** | **部分符合** |
| 7 | **发布路径（gate → scan → 人工签名 → GitHub Submit issue）**：`hub stamp` → `hub check` → `hub scan --packet …`（7 问）→ **HUMAN** `hub keygen`/`sign-manifest` → **HUMAN** "Commit the final (signed) `bundle/` to the app's public repository and **tag the commit**" + "Open an issue … titled `Submit <app id> <version>`"（PUBLISHING §3.4–3.8）；"Signing is optional for a first submission and required for every update once a key is on record … an agent never creates, copies, uploads or prints a private key"（§3.6）；"**Never** open a pull request that edits `catalog.json`, `index/` or `artifacts/`"（§3.8）；App Hub README："目前还没有发布用的 Action，也没有独立的索引仓库：由维护者对你所打 tag 的那个提交的确切字节运行 `hub publish`，并提交签名后的目录。" | 已做：本地镜像 + 一次性锚点走通 `hub stamp`/`sign-manifest`(`oncue.local`)/`check`/`scan`/`publish`/`verify`，catalog **sequence 7**（0.1.0…0.4.1 共 7 条，publisher `oncue.local`，见 `evidence/RUNBOOK-publish-next.md`、`evidence/ENDPOINTS.md`）；`hub scan` 7 问答案落在 `evidence/hub-review-answers.md`（包外）。未做：① 未在任何仓库开 `Submit oncue-screening-room 0.4.1` issue；② `git tag` 为 0 个；③ 发布密钥是本机工作钥（`oncue.local`）而非 PUBLISHING §3.6 要求的"由应用所有者创建并保管"的 publisher key；④ 0.4.1 条目的 `source.commit = c1485bad…`，而签名后的精确字节在 `9cb14a5`、HEAD 已前进到 `7d0ca91`（`evidence/RUNBOOK-publish-next.md` §6 实测 15 已自证此问题）；⑤ catalog 记的 `--repo https://github.com/codezzzsleep/OnCue` 与 `git remote -v` 实际值 `git@github-dev:codezzzsleep/OnCue.git` 不一致 | **部分符合**（PUBLISHING §4"本地演练商店路径"完整达成；正式提交链的 5 个环节缺失或不准，且其中 4 个是 **HUMAN** 环节，Agent 不得代做） |
| 8 | **已验证平台**："已验证的平台是 Apple silicon 上的 macOS；Windows 和 Linux 未验证。"（README §黑客松）；"Every command was run on macOS (Apple silicon) unless marked **unverified**"（QUICKSTART 开头, PUBLISHING §3） | 我们全部原生验证在 **Linux aarch64** 上完成（`oncue/docs/NATIVE-WORKFLOW.md` 自述"实测平台为 Linux aarch64"）；`listing.json` 的 `platforms: ["linux"]` 只声明实测平台，未声明 macos/其他（符合 PUBLISHING §3.2"only platforms you actually ran it on"） | **部分符合**（平台声明如实；但需在提交与演示中明确"官方只在 Apple silicon macOS 验证，本作为 Linux aarch64 自建环境实测"） |
| 9 | **无头测试与远程桥**："**Run headless.** Start apps with `tools/octo run … --hidden` … so you never take over the person's screen."（AGENTS.md §Rules）；QUICKSTART §4a 给出 `--port`/`--app-data`/`/snap`/`/click`/`/g`/`/quit` 用法；"**Clean up what you launch.** End every `card-host` you start with `curl -s 127.0.0.1:<port>/quit`" | 我们以 Xvfb `:99` + OctoSense `--module rinx` + `MAKEPAD_REMOTE=18141`（仅回环）驱动，`/snap`、`/click`、`/t` 已在 `evidence/native/041-snap.py`、`041-restore-after-reopen.md` 中实际使用；`evidence/LOGS-EXCERPT.md` F 组证明三端口均绑回环；`deploy/start.sh` 以 `/help` 健康探测与 `/quit` 优雅退出。**没有** `tools/octo run … --hidden`（`MAKEPAD_HIDE_WINDOWS=1`）的运行留档；也没有 makepad `makepad_test` 脚本化回归 | **部分符合** |
| 10 | **截图要求**："**No dummy screenshots.** Screenshots are captures of the real app in a real state (`tools/octo shot`), opened and looked at. Never draw, generate, crop from another app, or copy one to make the gate pass."（AGENTS.md §Rules）；"`tools/octo shot` is `GET /g?raw=1` saved to a file … Never ship an error frame, an empty first frame, or a mock-up."（PUBLISHING §3.3）；"Not checked by the gate, but checked by the reviewer … that the screenshots are real captures of this app"（PUBLISHING §2 末） | `oncue/bundle/screenshots/01-native-rinx.png` 为 **645×865 的桌面窗口裁剪图**：右侧被桌面/窗口圆角截断、无 `card-host` 32 pt 标题栏、无 `/g?raw=1` 特征；内容是 0.1.x 时代 UI（单栏、样例消息 #1–#4、空"我的草稿"、仅"保留这句/取回草稿"两按钮，无三条路线/播放/A-B 工作区），与当前 0.4.1 界面（`evidence/native/041-snap-baseline.json`，1911 个控件）不同代；该文件由 `fa9a675`（0.1.1）引入，`oncue/VERIFICATION.md` 冻结清单第 3 条自认"现有素材为 0.3.1，须补 0.4.x 同版本" | **不符合** |
| 11 | **清单类检查（PUBLISHING §6 checklist / AGENTS.md Definition of done）**：§6 逐条列出 doctor/manifest/listing/icon/run/interactions/screenshots/quit/check/check --catalog/scan/git status/HUMAN sign/HUMAN tag+issue/report；Definition of done 要求 "`tools/octo check <bundle>` prints `— PASSED` with only the unsigned warning"、"hub scan packet written outside the bundle and its seven questions answered" | 已具备：bundle 目录卫生（无 key/`.local-state`/`build/`）、`git status -- oncue/bundle` 干净且 **HEAD 的 bundle 与镜像 0.4.1 工件逐字节相同**（`diff -r` + `git archive` 实证）、7 问答案在包外。缺失：① 0.4.1 的 `hub check`/`hub verify` stdout 未存档（`evidence/LOGS-EXCERPT.md`"尚未出现"第 4 项自认），仓库内 packet 仅 `hub-review.json`(0.1.0) 与 `hub-scan-0.4.0.json`(0.4.0)，0.4.1 的 packet 只在易失的 `/tmp/oncue-reviewer-packet.json` 且其 sha256 与答案文件记录的 packet digest 不一致；② 0.4.1 的 `check --catalog` 未对最终字节留档；③ §6 最后两项 HUMAN 未做 | **部分符合** |
| 12 | **`matrix.*` 也是 Rinx-only**："`matrix.*` (45 names …) \| … \| **Only Rinx's mini-app host**"（CAPABILITIES §Host services by exact name） | 申请 2 个 `matrix.*`；房间读取（`main.splash:82/92` 的 `matrix.room_info`/`matrix.read_messages`）在官方 `card-host`/Shell 中同样无服务方；实测层面 `oncue/VERIFICATION.md` 与 `evidence/LOGS-EXCERPT.md`"尚未出现"第 1 项均记为**尚无同一实例的 12 条读取成功证据`（宿主同步层分页成功 ≠ 小程序读取成功） | **部分符合** |
| 13 | **隐私/商店文本真实性**："`publisher.privacy_policy_url`: an https URL that exists (**HUMAN**: the publisher owns this text)"（PUBLISHING §3.2）；"the privacy policy URL says something true"（§2 末） | `listing.json` 无占位文本：`category: productivity`、`age_rating: all`、6 个关键词、1 张截图、`icon: assets/icon.svg`、`privacy_policy_url` 指向仓库 `oncue/PRIVACY.md`；`oncue/PRIVACY.md` 已如实区分"服务器体验版"与"Rinx 原生小程序"两条数据路径，并写明原生模型试映使用共享 Octos 服务、Matrix 凭据由 Rinx 宿主管理。URL 的可访问性与文本归属需 **HUMAN** 确认（仓库 remote 为 `github-dev`，公开性未在本任务内核实） | **部分符合** |
| 14 | **隔离/包体/资产规则**：允许扩展名白名单、无脚本/压缩包/二进制/符号链接、≤ 8 MB；`.splash` 中禁 `http://`/`file://`/`../`，非声明主机拒（PUBLISHING §2 `contents`/`size`/`assets`） | bundle 5 个文件全部落入白名单扩展名；无符号链接；138 499 B；`main.splash` 无任何 URL（因此 `assets` 检查无对象）；`listing.json` 的 https 地址属 manifest/listing 豁免范围 | **符合** |

---

## 2. 差距清单

### A. 必须在 10/4 初赛提交前完成

| # | 具体动作 | 依据 |
|---|---|---|
| M1 | **换同版本真实截图并用 `/g?raw=1` 捕获**：在 Rinx Developer 宿主（无签名副本）把 0.4.1 开到目标状态 → `curl -s "127.0.0.1:18141/g?raw=1" -o /tmp/041-shot.png`（即 `tools/octo shot` 的取值方式），逐张看过 → 覆盖 `oncue/bundle/screenshots/01-native-rinx.png` → **重走** `hub stamp` → `hub sign-manifest` → `hub check` → 提交 → `publish` → `verify`（换图必改 digest，见 `evidence/RUNBOOK-publish-next.md` §5） | AGENTS.md "No dummy screenshots … Never … crop from another app"；PUBLISHING §3.3；`oncue/VERIFICATION.md` 冻结清单 3 |
| M2 | **真实模型回合（第 11 步）必须落证**：当前硬阻塞是 `profile '_main' is not configured for this AppUI session (profile_unresolved)` 与内核 `AppState has NO profiles registered`（`evidence/LOGS-EXCERPT.md` E 组）。动作：在宿主 **AI providers 系统应用的 GUI** 走 `llm.sheet.submit` 的 Test/Save（`evidence/RUNBOOK-provider-profile.md` §0 已定位：手写 `_main.json` 不是官方保存路径），再在同一 Rinx Developer 实例触发一次试映，保留 `/snap` 读回、脱密宿主日志与共享 octos 核心的成功行。在拿到该证据前，"应用内真实模型回合"只能报为**未在设备上验证** | `oncue/docs/NATIVE-WORKFLOW.md` §11；AI-SERVICES §测试/§错误表；AGENTS.md §Reporting "Not verified … never as 'should work'" |
| M3 | **房间 12 条读取（第 10 步）落证**：`matrix.room_info`/`matrix.read_messages` 不传 `room_id`，依赖 Rinx 导入时填的 "Room ID to allow"（`evidence/RUNBOOK-step10-11.md` §1.1–1.2：留空必然 `this mini-app is not attached to a room`）。动作：填房间 ID → Review → Run → 点"载入群聊" → `/snap` 读取 `cue_scene_label`/`cue_sources_list`，并留存脱密 API 事件（`state/evidence/matrix-room-read.json` 已有雏形） | 同上；CAPABILITIES `matrix.*` 行 |
| M4 | **存档 0.4.1 的 gate 与 scan 证据**（都在包外）：`/tmp/hubbuild/app-hub/target/release/hub check oncue/bundle --publisher-key "oncue.local=$(cat /root/oncue-runtime/state/hub-keys/working.pub)" \| tee evidence/hub-check-0.4.1.txt`；`hub check … --catalog /root/oncue-runtime/state/hub-mirror/catalog.json \| tee evidence/hub-check-0.4.1-catalog.txt`；`hub scan oncue/bundle --packet evidence/hub-scan-0.4.1.json`；`hub verify … --anchor … \| tee evidence/hub-verify-seq7.txt` | PUBLISHING §6 checklist（`hub check` 输出要随 issue 提交）；AGENTS.md Definition of done 5 |
| M5 | **修正 0.4.1 的溯源**：catalog 0.4.1 条目 `source.commit = c1485bad…`（签名前），而签名后字节在 `9cb14a5`、HEAD 已前进到 `7d0ca91`，且 `git tag` 为空。动作：按 `oncue/VERIFICATION.md` 冻结清单 2 的顺序发 **0.4.2**（内容/version 定稿 → `stamp` → `sign-manifest` → `check` → 提交签名后工件并 push → `git rev-parse HEAD` → `hub publish --commit <该提交>` → `verify`），并为该提交打 tag `v0.4.2` | PUBLISHING §3.8（issue 必须带 repo/tag/完整 SHA，维护者按 tag 的确切字节复跑）；`evidence/RUNBOOK-publish-next.md` §6 实测 15 |
| M6 | **在商店说明与报告里写明 `octos.*`/`matrix.*` 在库存设备上不起作用**：改 `oncue/bundle/listing.json` 的 `description` 或 `release_notes`（一句话即可，例如"原生模型试映与房间读取依赖 Rinx 迷你应用宿主；在库存 OctoSense Shell 与 card-host 中该两项不可用"），改后必重走 M1 的 stamp→sign→提交→发布链 | AI-SERVICES §最小调用示例结尾："**现在应该发布这个功能吗？** 只有在应用不依赖它也完整可用时才可以。… 如果保留这个调用，请在商店说明和你的报告中写明：在目前的设备上它不起作用。" |
| M7 | **补"不可用"状态的取证**：在 `card-host`/库存 Shell 跑一次（无签名副本），点试映 → 预期 `Agent 暂时不可用：no service answers "octos" on this device`，用 `/g?raw=1` 截图并 `/snap` 读回，与 M1 的截图一同入 `evidence/` | AI-SERVICES §测试："预期得到 `no service answers` 状态；把它截图作为应用的'不可用'状态。" |
| M8 | **HUMAN（只能由人做，Agent 不得代做）**：① 由应用所有者创建并保管 publisher key（`hub keygen "$KEYS/publisher.key"`，置于所有仓库之外），后续更新必须沿用同一 key（`continuity`）；② 用公开仓库 URL + tag + 完整 SHA + publisher 公钥 + `hub check` 输出 + 7 问答案，在 **OctoSense-App-Hub** 开 `Submit oncue-screening-room <version>` issue；③ 确认 `privacy_policy_url` 所指页面公开存在且文本归发布者所有；④ 向主办方确认参赛作品是否需要/是否等于 App Hub 正式提交 | PUBLISHING §3.6/§3.8/§5（Human checkpoints 表）；README §黑客松："参赛作品不等于自动提交到 App Hub；请向主办方确认他们需要什么。"；AGENTS.md §How to work 4（"Never fabricate an approval, a review result, a submission"） |

### B. 可选改进

| # | 具体动作 | 依据 |
|---|---|---|
| O1 | 用 `tools/octo run oncue/bundle --port 8142 --hidden --detach` + `/snap`/`/click`/`/g?raw=1` + `curl -s 127.0.0.1:8142/quit` 做一轮无头回归，替代"Xvfb + VNC + 桌面点击"的做法，并可按 QUICKSTART §4a 引入 makepad `makepad_test` 做脚本化 UI 测试 | AGENTS.md "Run headless … never take over the person's screen"；QUICKSTART §4a |
| O2 | 把 `collaboration/ai2-credential-public.pem` 移出仓库或确认无需保留（公钥无害，但 PUBLISHING §1 要求非 bundle 内容不进入提交面；目前它在仓库根、不在 `bundle/`，仅属卫生问题） | PUBLISHING §1；AGENTS.md "Keep the bundle clean" |
| O3 | 刷新过期快照：`evidence/ENDPOINTS.md` 仍写 `sequence: 5` / 已安装 `0.3.1`，实际为 sequence 7 / 已安装 0.4.0 / bundle 0.4.1；在文首加一行"当前值（发布前须重核）" | AGENTS.md §Reporting（报告要能让人不重跑即可核对） |
| O4 | `deploy/oncue-reviewer.sh` 是静态通过型评审（答案写死），换版本（尤其能力/界面变化）时同步更新 7 问答案与 `reasons`，否则评审记录与事实不符 | `evidence/RUNBOOK-publish-next.md` §3.3 |
| O5 | 把 0.4.1 的 `hub scan` packet 从易失 `/tmp` 复制进 `evidence/`（M4 已含），并让 `hub-review-answers.md` 记录的 packet digest 能在仓库内解析（当前记录值 `4980959f…` 与 `/tmp/oncue-reviewer-packet.json` 的 sha256 `f6aa1123…` 不一致，说明该 packet 已被后续运行覆盖） | AGENTS.md Definition of done 5 |
| O6 | 记录工具链版本漂移：本机 hub 来自 App Hub rev `0f33211`，而文档所述为 `79a2c4f`/`6c075d0`/`e8601b8`/`a72989f`，Shell 锁定 `46d67e51`。在提交说明中写明实际 rev，避免审核方按文档版本复现 | AI-SERVICES §状态一览"需要知道的版本差异"；PUBLISHING 开头版本声明 |
| O7 | `hub scan` packet 的 `screenshots` 字段为空数组（`evidence/hub-scan-0.4.0.json`、`/tmp/oncue-reviewer-packet.json` 均为 `[]`，`hub` CLI 恒为空）。如需让审核方看到截图，随 issue 附上截图路径清单 | `evidence/RUNBOOK-publish-next.md` §3.1 |

---

## 3. 明确结论：主推的"应用内真实模型回合"是否与官方文档冲突

**结论：不属于被禁止的用法，但与官方文档现状存在两处实质冲突；按官方规则，该特性目前只能报为"未在设备上验证"，且必须附带"不可用"说明。**

1. **官方允许声明，且点名唯一响应方就是我们选的宿主。** `octos.session.open` / `octos.turn.start` / `octos.turn.interrupt` 是通过准入检查的精确服务名（CAPABILITIES §Host services by exact name；AI-SERVICES §助手相关权限），原始参数/返回形状就来自 Rinx 迷你应用宿主（AI-SERVICES §助手相关权限："参数和返回的形状取自目前唯一提供这些名称的宿主：Rinx 的迷你应用宿主"）。因此"在 Rinx 迷你应用宿主里做真实模型回合"是官方承认的路径，冲突不在"能不能做"。
2. **冲突一：主推话术与"未验证"事实冲突。** 我们至今没有一次成功回合证据——阻塞是 `profile '_main' is not configured for this AppUI session (profile_unresolved)` 与 `AppState has NO profiles registered`（`evidence/LOGS-EXCERPT.md` E 组）；`oncue/VERIFICATION.md` 亦记"尚无同一 Rinx 实例的真实七块剧本回合"。AGENTS.md 的报告规则要求 "Not verified: anything you did not run … stated as not verified, never as 'should work'"，而 AGENTS.md 的规则原文是 "**No AI feature the device cannot serve.** … report such a feature as not verified on a device"。所以把"应用内真实模型回合"当作已实现主推力推，与官方规则冲突。
3. **冲突二：在 App Hub/库存设备路径上它必然不可用，却不加说明。** 官方原文："**目前，商店应用在 OctoSense 设备上还不能向模型或助手提出任何请求。** 没有任何 OctoSense Shell 向隔离运行的应用提供助手请求，`card-host` 也不提供任何宿主服务。"（AI-SERVICES §简短回答）；"在 `card-host` 和 OctoSense Shell 中都一样（已在 `card-host` 中验证）"返回 `no service answers "octos" on this device`。我们不补这句说明就直接上架/提交，违反该文档对发布条件的规定。

**官方推荐的替代/兜底做法（AI-SERVICES.zh-CN.md 原文）：**

- "请把应用做成不依赖 AI 也完整可用。"（§简短回答）
- "把'不可用'当作正常状态：设备上没有内核（iOS、没有内核的桌面端）、没有配置提供方、未授权、未登录。用一句话说明，并让其他界面照常工作。永远不要向用户索要密钥或提供方。那属于宿主的 AI providers 应用。"（§最小调用示例与"不可用"状态）
- "**现在应该发布这个功能吗？** 只有在应用不依赖它也完整可用时才可以。审核者会问界面上用不到的授权（`hub scan`），每个 `octos.*` 都会出现在商店的权限列表中。如果保留这个调用，请在商店说明和你的报告中写明：在目前的设备上它不起作用。"（同节结尾）
- 需要"真模型"又能今天合规落地的形态，官方给的是普通 HTTPS API 路径："应用在 `net` 下声明的普通 HTTPS API 只是一次网络请求，即使背后运行着模型也是如此。常规规则照样适用：应用包中没有密钥或 token，主机已列出，隐私说明写明哪些数据会离开设备。"（§简短回答末）——我们在 `oncue/server/`（浏览器/服务器版 + `evidence/minimax-live-result.json`）正是这条合规路径，可在 10/4 作为"今日可用"的模型能力呈现，原生 `octos.*` 回合作为"在 Rinx 宿主中推进中"的阶段成果呈现。
- `model.complete`（一次性模型调用）官方标注为**即将推出**（OctoSense#95 草稿），同样"调用返回 `no service answers \"model\" on this device`"，不要作为依赖（§状态一览）。

---

## 4. 附件：抓取的文档（URL / HTTP 码 / 字节数 / 本地缓存）

Base：`https://raw.githubusercontent.com/OctoSense-org/OctoScript-App-Design-Flow/master/`

| 文档 | URL | HTTP | 字节 | 本地缓存 |
|---|---|---|---|---|
| README.zh-CN.md | `…/OctoScript-App-Design-Flow/master/README.zh-CN.md` | 首次 `000`（curl 超时，0 字节）→ 重试 `200` | 34 106 | `/tmp/octodocs/README.zh-CN.md` |
| AGENTS.md | `…/master/AGENTS.md` | `200` | 7 571 | `/tmp/octodocs/AGENTS.md` |
| docs/PUBLISHING.md | `…/master/docs/PUBLISHING.md` | `200` | 21 525 | `/tmp/octodocs/docs_PUBLISHING.md` |
| docs/CAPABILITIES.md | `…/master/docs/CAPABILITIES.md` | 首次 `000`（超时）→ 重试 `200` | 11 083 | `/tmp/octodocs/docs_CAPABILITIES.md` |
| docs/AI-SERVICES.zh-CN.md | `…/master/docs/AI-SERVICES.zh-CN.md` | `200` | 58 097 | `/tmp/octodocs/docs_AI-SERVICES.zh-CN.md` |
| docs/QUICKSTART.md | `…/master/docs/QUICKSTART.md` | `200` | 20 514 | `/tmp/octodocs/docs_QUICKSTART.md` |
| docs/SCRIPT-API.md（Gotchas 小节已读，行 280–327） | `…/master/docs/SCRIPT-API.md` | `200` | 20 093 | `/tmp/octodocs/docs_SCRIPT-API.md` |
| App Hub README.zh-CN.md | `https://raw.githubusercontent.com/OctoSense-org/OctoSense-App-Hub/master/README.zh-CN.md` | `200`（未回退 `main`） | 6 839 | `/tmp/octodocs/apphub_readme_zh.md` |
| （附加，非任务清单）docs/HOST-SERVICES.md | `…/OctoScript-App-Design-Flow/master/docs/HOST-SERVICES.md` | 首次 `000`（超时）→ 重试 `200` | 9 334 | `/tmp/octodocs/docs_HOST-SERVICES.md` |

未取到的文档：**无**。`000` 均为瞬时网络超时，同一 `master` URL 重试即成功；无需回退 `main`，也未使用 GitHub HTML 页面重试。

本机侧只读取证（未改动）：`/root/oncue-runtime/state/hub-mirror/catalog.json`（sequence 7）、`.../artifacts/oncue-screening-room-0.4.1.bundle/`（与 HEAD 的 `oncue/bundle` 逐字节相同）、`/root/oncue-runtime/state/apps/oncue-screening-room/bundle/manifest.json`（已安装 0.4.0）、`/tmp/oncue-reviewer-packet.json`（0.4.1 scan packet，易失）、`git tag`（0 个）、`git remote -v`（`git@github-dev:codezzzsleep/OnCue.git`）。


---

## 7. 纠偏（AI1 #147 逐条核对当前 main 文档与固定源码后）

以下六条**更正并取代上文对应表述**。依据分三类：**(a)** 当前 main 文档
`OctoSense-org/OctoSense` `docs/ai-services.zh-CN.md`（280 行，2026-10-01 抓取，HTTP 200 / 36838 B，
本地 `/tmp/octosense-main-ai-services.md`）；**(b)** 固定宿主源码 `6c4746f`；**(c)** 本机运行时观察。

### C1 「商店/App Hub 必然无 octos 服务」不准确；「model 仍未合并」错误
- (a) `:30`：「隔离运行的脚本应用（系统应用或商店应用）向助手提问 | **在托管了内核的 Shell 中可用**（#106）：`octos` 宿主服务为每个应用分配自己的 peer（`card.<应用 id>`），前提是 `Policy::contained_apps` 为开（**默认关闭**；`OCTOSENSE_CONTAINED_APPS=1`），且用户在首次使用时允许了该应用的 Agent（#120）」。
- (a) `:31`：「供隔离应用使用的一次性模型调用（`model`，`model.complete`）| **目前可用**（#95）…（App-Hub#24，已在 Shell 锁定的 App Hub 中）」。
- (a) `:164`：「**Rinx 迷你应用**。Rinx 托管经过审核的 OctoScript 迷你应用，并向它们提供同样的四个 `octos.*` 服务…这不是 App Hub 的安装路径。」
- (a) `:177` 与 `:186-191`：`octos` 服务的三个前提（Shell 托管内核、`Policy::contained_apps`、用户首次同意）与三种失败返回：开关关闭 → `The assistant is turned off for apps on this device`；**尚未允许 → `Waiting for the person to allow this app's agent (OctoSense asks the first time)`**；不链接内核的构建 → `no service answers "octos" on this device`；**`card-host` 中调用任何服务 → `no service answers "<family>" on this device`**。
- (a) `:193`：2026-09-28 已在 macOS release 桌面、隐藏窗口下验证：声明 `octos.session.open`/`octos.turn.start` 的系统应用得到来自 peer `card.<应用 id>` 的回复，内核数据里出现其记忆命名空间。
- (a) `:195`：manifest 的 `agent` 字段会被 App Hub 接受，但 **Shell 中没有任何东西为它运行 Agent**，且 **Rinx 拒绝导入声明了 `agent` 的应用包**（我们 `agent = null`，符合）。
- (b) 固定 `6c4746f`：`crates/ai-host/src/contained.rs:370-374` 有 `impl HostService for ContainedOctos { fn family() -> "octos" }`；`crates/ai-host/src/lib.rs:174-180` 的 `Policy::shipped()` 读取 `OCTOSENSE_CONTAINED_APPS`（`1`=对所有应用开、`0`=关，未设置=按同意）并 `with_contained_gate(gate)`。
- (c) 本机运行时：宿主环境**未设置** `OCTOSENSE_CONTAINED_APPS`（`/proc/<pid>/environ` 实测，deploy 脚本亦未设置）；日志有
  `octos: contained apps' service registered (Consent)` 与
  `agents: oncue-screening-room's agent is prepared (its peer is listed for the system agent)`；
  `state/octosense/approvals/consent.json` 中 `oncue-screening-room` 与 `rinx` 均为 `allowed=true`。
- **更正后的表述**：`card-host` **没有**任何宿主服务；而**托管内核的 Shell**里，隔离脚本应用可在
  `Policy::contained_apps` 放行（默认=按用户首次同意；`OCTOSENSE_CONTAINED_APPS` 是开发者覆盖）且用户允许其 Agent 后使用四个 `octos.*`；**Rinx 迷你应用宿主**另向导入 Rinx 的包提供同样四个服务。**不应**再写"所有 App Hub/库存设备必然 no service answers"，也不应写"`model` 尚未合并"。**不要**用换版本的方式掩盖此前的错误表述。

### C2 git 远端不是合规差距
`git@github-dev:codezzzsleep/OnCue.git` 是同 owner/repo 的 **SSH 连接别名**，与 `https://github.com/codezzzsleep/OnCue` 指向同一仓库 → 上文表格第 7 行 ⑤ 不作为差距。

### C3 截图问题的准确性质；捕获方法不唯一
- 旧截图（`screenshots/01-native-rinx.png`，645×865）**需要更新是因为版本不符**（0.1.x 时代 UI，与 0.4.1 不同代），**不是**"crop from another app"——它是同一 OnCue 的真实像素截图裁剪。
- **不得把 `/g?raw=1` 写成唯一必需的取证方法**：本机 Linux GL 下 `/g` 超时已有记录；应保留已有的真实捕获手段（远程桥截图 + 控件树/像素证据），并把能取到的形式如实标注。

### C4 Linux 未验证 ≠ 我方不合规
官方"仅在 Apple silicon macOS 验证"是**官方未测试 Linux**；我们 `platforms: ["linux"]` 只声明**实际跑过的平台**，符合 PUBLISHING §3.2。只需在提交材料与演示中说明"官方验证平台为 macOS，本作为 Linux aarch64 自建环境实测"。

### C5 未成功的模型回合一律 pending
"计划做"不等于"虚报已实现"。本报告与其余证据中，模型回合始终标注为 **pending（未在设备上验证）**；不得写成"已虚报"。

### C6 密钥不在 bundle；开发期手写配置不等于"应用持有秘密"
模型服务密钥位于**宿主私有配置**（`state/octos-core` 的 profile，0600）而非 `bundle/`；开发期为解开 `profile_unresolved` 手写 envelope 属于**宿主侧开发诊断**，不能据此判定"应用持有秘密"。正式使用应走 **AI providers 宿主设置流程**（GUI 保存）并重新验证；**配置与回合都仍需验证**。

### 仍然成立的实质差距（保持）
1. **正式 Hub Submit 未做**（本地镜像只是 PUBLISHING §4 的"本地演练商店路径"）。
2. 需在冻结时补齐：**本版本截图、listing 说明、最终 `hub check` + `hub scan` 七问答案、发布者公钥、git tag、精确 commit**。
3. **基础功能先冻结**；Rinx 服务作为**明确列为增强项**的验收内容，**未成功的回合不得阻断基础初赛包**。
4. **不代替用户在 OctoSense-App-Hub 开 issue**。

## 8. 提交材料清单（按 PUBLISHING §3.8；Agent 只可起草）

| # | 材料 | 来源/命令 | 责任 |
| --- | --- | --- | --- |
| 1 | 仓库 URL | `git remote -v`（HTTPS 形式） | Agent 准备 |
| 2 | tag 与**完整 commit SHA** | 由人对**签名后工件所在提交**打 tag | **HUMAN** |
| 3 | bundle 在仓库中的路径 | `oncue/bundle` | Agent |
| 4 | 发布者 id 与公钥（或 "unsigned"） | `hub pubkey`；本机为 `oncue.local` | **HUMAN** 决定用哪把钥 |
| 5 | 该 commit 上**完整 `hub check` 输出**（签名时带 `--publisher-key`） | `evidence/native/041-hub-check-verify.txt` §1 已有 0.4.1 的 PASSED 样本 | Agent（冻结版本重跑） |
| 6 | **`hub scan` 七问答案** | `evidence/native/041-hub-scan.txt` + `evidence/native/041-hub-scan.packet.json`；答案另见 `evidence/hub-review-answers.md` | Agent |
| 7 | 实际测试过的平台与交互、以及**未测试**的部分 | `oncue/docs/NATIVE-WORKFLOW.md`、`oncue/VERIFICATION.md`、本报告 | Agent 起草，**如实** |
| 8 | issue 本身 | OctoSense-App-Hub，标题 `Submit oncue-screening-room <version>` | **HUMAN 本人账号** |
