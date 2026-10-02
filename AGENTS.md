# AGENTS.md — OnCue 参赛项目规程（防遗忘 · 完整版）

> **作用**：把赛事要求、官方流程、环境事实、当前进度**固化在仓库里**，避免上下文变长或换 agent 接手时反复返工。
> **每次开工先读本文件；每次状态变化后更新第 8/9 节。**
> 依据：**完整克隆并逐字通读**的 6 个仓库
> `gosimfoundation/hackathon-agenticapp26`、`OctoSense-org/OctoScript-App-Design-Flow`
> （含 `README.zh-CN.md`、`AGENTS.md`、`flows/script-app/FLOW.md`、`docs/PUBLISHING.md`、
> `docs/CAPABILITIES.md`、`docs/ICONS.md`）、`OctoSense-org/OctoSense-App-Hub`
> （含 `docs/FIRST-APP.md`、`docs/PUBLISHING.md`）、`OctoSense`、`Octoscript`、`Rinx`。

> **✅ 2026-10-02 已确认的决策**
> 1. **初赛提交截止延至 10/6 23:59**；**后续节点不变** → 评审仍为 10/5–10/6 18:00，
>    **实际评审窗口被压缩**（提交与评审几乎重叠），因此**必须在 10/5 前完成冻结版本**。
> 2. **2026-10-03 OctoSense 更新** → 按用户决定：**只拉取并报告变更，先不重建宿主**。
> 3. **优先级（用户选定，四项全做）**：① 接收者独立授权演示 ②「执行 → 核验结果」定位改造
>    ③ 跨房间拒绝/实例撤销/迟回复 + Back/关闭-重开 ④ 2–3 分钟演示 + 第二张关键截图。

---

## 1. 项目概况

| 项 | 值 |
| --- | --- |
| 作品 | **OnCue · 群聊试映室** |
| 形态 | **OctoScript 脚本应用（script app）**，跑在 **Rinx** 小程序宿主内，经 **App Hub** 发布 |
| 赛道 | OctoSense 12 场景之 **即时消息**（官方明确：即时消息场景**绑定 Rinx**） |
| 包路径 | `oncue/bundle/` —— **只有 `bundle/` 会被提交** |
| 应用 id | `oncue-screening-room`（`[a-z0-9.-]{1,64}`，不以保留名结尾 ✓） |
| 版本 / digest | `0.4.4` / `9b221cd7ed27bb6fb38c7d91bdd04d13de6387b4055565d74bf7c1bce9f13b97` |
| 队伍 / 成员 | **OnCue / YCOROY**（用户 2026-10-02 确认；队长与人数待补） |
| 许可 | Apache-2.0（`oncue/LICENSE`） |

**功能一句话**：把还没发出去的一句话放进私人排练场，读**授权房间**消息作线索，
请设备助手生成**三条假设下一幕**，逐句播放查看，改动后存草稿 A/B，**应用自身不发送任何消息**。

### 1.1 仓库结构（官方约定）
```
OnCue/                       应用自己的仓库
  AGENTS.md  .gitignore      规则与忽略；不提交
  oncue/BRIEF.md             需求简报；不提交
  build/review.json          hub scan 审核包；不提交
  build/REVIEW-ANSWERS.md    七问回答；不提交
  .local-state/              card-host 的 jail 与日志；不提交
  oncue/bundle/              ★ THE SUBMISSION（唯一提交物）
    manifest.json  listing.json  main.splash
    assets/icon.svg  screenshots/01-native-rinx.png
```

---

## 2. 赛事硬性要求

### 2.1 时间（北京时间 UTC+8）
| 节点 | 时间 |
| --- | --- |
| **报名截止** | **9/23 23:59**（个人分别报名；队长不能代填） |
| **官方发布锁版本环境** | **9/24 18:00 前**（锁版本环境、支持设备、启动步骤、可用能力、示例数据、**即时消息练习数据接受范围**、替代练习范围）；9/25 收异步自检 |
| 开营 / 四场机制课 | 9/22 19:30–21:00 / 9/26–27 |
| 制作周 | 9/28–10/4（不增必修课；10/3–4 仅可选支持） |
| **初赛提交截止 / 版本冻结** | ~~10/4 23:59~~ → **10/6 23:59**（用户 2026-10-02 确认，延期两天）<br>⚠️ **后续节点不变** → 评审 10/5–10/6 18:00 **与提交重叠**，**须在 10/5 前冻结** |
| 初赛评审（只用冻结版本） | 10/5–10/6 18:00 |
| 公布 50 人晋级 | 10/6 20:00 |
| 复赛提交 | 10/9 23:59 |
| 复赛材料评审 | 10/10–**10/11 18:00** |
| 连线检查（非评分人员） | 10/11 10:00–12:00 |
| 线上决赛答辩 + 评奖 | 10/12 13:00–17:00，20:00 公布 |
| 复赛工作坊 | 10/7（三） |
| 收齐最终讲述材料 | 10/12 12:00 前 |
| 受邀团队确认到场代表 | 10/13 18:00 前 |
| 现场展示包冻结 | 10/15 18:00 |
| GOSIM 现场展示与颁奖 | 10/17（总排名前三名；**现场不再评分**，到场不影响线上名次） |
| 赛后采纳与归档 | 10/18–10/31 |

⚠️ **待确认**：报名是否已在 9/23 前完成（成员信息在 10/4 提交时锁定）。

### 2.2 形态与定位（官方原文要点）
- 张老师：**"初赛代码只要求 octoscript 的应用"**、**"appcard 必须通过 App Hub 发布"**、
  **"独立开发的应用不在 octosense 里就和比赛没关系了"**。
- 竞赛以 OctoSense 为核心：选手从**官方 12 个场景**选题（邮件、即时消息、日历、天气、新闻、音乐、
  视频、财经、导航、购物物流、写作创作、系统设备），**用 Agent 自动化完成真实任务**。
- **主要开发基线是 `hagency-org/Rinx`**；选手在既有聊天/联系人/发现/小程序入口上做场景小程序。
- ⚠️ **"统一最小交付应能展示：事件或意图输入 → Agent 理解并形成操作计划 → 用户查看或授权 →
  执行 → 核验结果 → 状态变化或失败处理。仅生成界面、摘要或静态卡片，不足以证明完成了任务自动化。"**
- ⚠️ Rinx 基线给的演示要求：**"展示 Agent 在作品运行时如何读取获授权的状态、提出操作、执行并核验结果。
  Agent 帮忙写过代码或成功分享一张卡片，本身不能证明作品具有任务自动化能力。"**
- ⚠️ 即时消息的期望模式（官方举例）：*"a task event becomes an actionable card, the user reviews or
  authorizes an operation, and **the result returns to the source conversation**."*
- 迭代顺序：**先完成基本功能 → 接 octos agent 上 agentic 功能 → 最后再调 UI**。
- 初赛**不要太复杂**，能传达基本功能即可。应用层作品**不要求**改 ROM，也**不要求**提交无关 PR/issue。

### 2.3 提交材料（6 项）
1. 公开源码仓库 + 固定提交号/版本 + **Apache-2.0**
2. 应用目标、适用场景、图标、运行截图、作者与支持方式
3. 宿主版本、支持平台、依赖与启动说明
4. 数据来源、权限、隐私、授权/拒绝/失败行为
5. **Agent 任务演示**：输入、Agent 步骤、如何核验、哪些需人工确认
6. 运行截图/日志/复现步骤；**演示材料不能代替可运行作品**

### 2.4 聊天/账号类作品的额外硬要求
> **必须演示「接收者独立授权」**：Rinx 机制为——**每次打开须授权**；授权关联**账号、登录会话与应用实例**，
> **最长一小时**，关闭或退出后撤销；**不能继承发送者的权限**。要展示**拒绝、重新打开、不同账号**的行为。

Rinx 基线给选手的起步流程（官方原文）：
1. 走完「发现 → 文章编辑器」的授权、编辑、草稿、预览与确认发送；
2. **分享应用卡片，让另一位测试用户打开并独立授权**，检查对方得到**自己的草稿和账号**，**结果发送到选定聊天**；
3. 选一个真实任务，用 octoscode 与 OctoLoop 组织 Agent 制作和审查；
4. 网页项目交付可运行页面与 URL 卡片；**新增原生应用需在自己的宿主分支扩展并构建**，
   提交完整源码、宿主提交号与启动方式；
5. 展示 Agent 运行时**读取授权状态 → 提出操作 → 执行 → 核验结果**。

### 2.5 奖项（名额与奖金已公开，两个新奖项的映射待定稿）
奖池 ¥50,000：一等奖 1 名 ¥20,000、二等奖 2 名各 ¥9,000、三等奖 3 名各 ¥4,000。
**最佳 Agentic 奖评分维度（定性）**：**任务完成 / 可靠运行 / 结果核验 / 人机协作 / 复现证据**
（`octosense-scenario-update-plan.md:85`、`curriculum.md:96`；不设未确认的权重）。
**最佳技术突破奖**
（在工作应用基础上看生态反哺与 ROM/系统突破）。**应用层作品可获最佳 Agentic，不要求改 ROM，
也不要求提交无关贡献**；技术突破奖**不以先拿 Agentic 奖为前提**。


### 2.6 初赛提交材料（`curriculum.md:92` 原文要点）
> 10/4 23:59 初赛截止并锁定已报名成员。提交**需求、可运行最小原型及启动说明、源码或包、
> 2–3 分钟演示、两张关键截图、数据来源与限制、**已报名成员名单**（队名/队长/成员登记，10/4 提交时锁定）**。
> **至少能展示一次操作、可核对的结果，以及一个失败或空状态；静态概念图本身不满足原型要求。**

⚠️ 所以我们**还缺**：2–3 分钟演示（视频或逐步演示材料）、第二张关键截图。

### 2.7 复赛提交材料（`competition-schedule.md:80`、`curriculum.md:94`）
> 10/9 23:59 前由晋级的 50 人提交：**可运行应用、安装步骤、冻结版本、能力说明、
> 正常与失败场景验证、队外用户试用记录、完整演示及已知限制**。

`curriculum.md:64`：**"让队外用户完成一次任务，记录不能完成或需要人工接管的地方。"**
→ 复赛需要**队外用户试用记录**（不能只靠自己或队友）。

### 2.8 决赛答辩与计分（`competition-schedule.md:84/88/90/92`）
- 两个并行组各最多 25 个项目，**每项目 8 分钟：3 分钟应用演示 + 2 分钟 Agent 自动化与自选技术贡献 +
  2 分钟问答 + 1 分钟切换**。
- **17:30 向队伍提供评分明细；18:30 前收齐事实或计分错误说明；19:30 锁分。**
- **10/12 结合答辩与问答完成同一轮复赛评奖，不叠加初赛分。**
- 阻塞性修复须按统一规则**登记原因、前后版本和证据**。

### 2.9 运行验收清单（`app-hub-submission.md`「运行验收与评奖」原文）
> 实际演示应覆盖**启动、真实输入、必要授权、Agent 执行、结果核验和失败处理**。
> 聊天或账号相关作品**还需演示接收者独立授权**，避免把发送者身份或权限带给接收者。
> **Agent 辅助开发、通过包预检、成功上架或累计 PR 数量，均不能单独替代作品效果证据。**

→ 验收六项：**启动 / 真实输入 / 必要授权 / Agent 执行 / 结果核验 / 失败处理**，外加接收者独立授权。

### 2.10 按作品形态交付（`app-hub-submission.md`）
| 作品形态 | 交付方式 |
| --- | --- |
| **Hub 卡片包（本作品形态）** | 按 Hub 规范准备 manifest、listing、入口与本地素材，**附预检结果及实际运行证据** |
| 网页小程序 | 源码、可运行页面、URL 卡片与部署/启动说明，说明自己的账号与数据接入 |
| 原生宿主扩展 | 含扩展的可构建宿主版本、源码提交号、支持平台与运行说明 |
| OctoSense ROM 扩展 | 在可运行应用基础上附系统改动、构建/安装与复现说明、效果前后对照 |

原文还强调：**"现有 Rinx 内置编辑器不是任意 Hub 包的安装入口，不能仅提交 `.card` 文件并假设宿主会加载。"**

---

### 2.11 其他赛事规则（`competition-schedule.md:44/96/98`）
- **晋级按人数统计，不是 50 支队伍**；奖项以**项目团队**为单位，单人队伍同样适用。
- **直播出勤不作为晋级条件。**
- **现场不再评分**；不能到场仍保留线上名次与奖励。
- 差旅支持另行说明，**不承诺未经确认的报销**。

## 3. 官方发布流程

### 3.1 script-app 十四步（`flows/script-app/FLOW.md`）
| # | 步骤 | 通过条件 | Human |
| --- | --- | --- | --- |
| 1 | 写 `$A/BRIEF.md`（画面/动作/数据/状态/主机/能力+理由） | 每画面每动作一行，每能力有理由 | 需求不明时确认 |
| 2 | `tools/octo new $A --id <id> --name "<Name>"`（复制 `bundle/`、`AGENTS.md`、`.gitignore`） | 打印 `created …` | 否 |
| 3 | 依 brief 填 `manifest.json` 的 capabilities 与 `network.hosts`，不多不少 | 每能力对应 brief 一行 | 否 |
| 4 | 写 `main.splash`，**只用能引用的 API**；用 `start_timeout(0.05, …)` 启动（`ui` 在主体后才注入） | 无不可引用的 API | 否 |
| 5 | `tools/octo run $B --port $P --hidden --detach` | `admitted` + `ready: first frame drawn` | 否 |
| 6 | `tools/octo shot $P /tmp/first.png` 并打开看 | 首屏可见、非空白非错误帧 | 否 |
| 7 | **用远程桥驱动每个动作**（`/click`、`/t`、`/k`），各动作后用截图或 `/snap` 或 jail 文件观察 | 每个动作效果被观察并记录 | 否 |
| 8 | 测**空 / 错误 / 重启持久化**（`/quit` 后重跑第 5 步） | 各状态合理；该持久化的数据存活重启 | 否 |
| 9 | 修到 5–8 全过 | 一轮全过 | 否 |
| 10 | 定稿 `listing.json`（**所有**字段），换 `assets/icon.svg` | 解析通过且只说真话 | 发布者信息=**人** |
| 11 | 驱动到最佳真实状态 → `tools/octo shot $P $B/screenshots/01-main.png`（**1–8 张**，列进 listing）；逐张打开看；`/quit` | 每张都是看过真实截图 | 否 |
| 12 | `tools/octo check $B` | `<id> <version> — PASSED`，只剩未签名警告 | 否 |
| 13 | `hub scan $B --packet $A/build/review.json`，七问写入 `$A/build/REVIEW-ANSWERS.md` | packet 写在 bundle 外、七问如实回答 | 否 |
| 14 | 按 §7 格式汇报，**停** | 汇报交付 | 交接给人 |

### 3.2 Definition of Done（交接给人之前必须全满足）
1. `tools/octo check <bundle>` 输出 `— PASSED`，只剩未签名警告
2. `bundle/screenshots/` 有真实截图，列在 `listing.json`，**每张都打开看过**
3. brief 里每个交互在 `card-host` 中**用远程桥原生驱动**并观察到效果
4. **空、错误、重启**状态都跑过
5. `hub scan` packet 写在 bundle 外，七问已回答
6. PUBLISHING 清单执行到**第一个 HUMAN** 行为止

### 3.3 每个应用必须遵守的规则
- **应用中不得有秘密**：无密码/PIN/验证码输入框（`is_password:true`、`TextInputContentType.Password`、
  `NewPassword`、`OneTimeCode` 会被 gate 拒绝且运行时失效）、无登录表单、无 API key/token。账号走宿主面板。
- **声明每一个 host**：`.splash` 里的 `https://<host>` 必须在 `network.hosts`（裸域名、小写、无 scheme/端口/通配）；
  `http://`、`file://`、`../` 一律拒绝；包内素材用 `{{assets}}`，**绝不自己写 loopback 源、`file://` 或 `../`**。
- **AI 功能都是可选的**：`card-host`（含 `tools/octo run`）**不提供**任何宿主服务，
  `octos.*` / `model` / `mail` 等调用会得到 `no service answers "…" on this device`。
  **永远不要把模型 key 放进应用**；`llm` 仅供系统应用。
- **只申请需要的能力**；每个能力都要对应画面上真实做的事。
- **截图必须是真实状态的真实截图**；绝不画、生成、裁切或从别的应用复制；绝不放错误帧或空白首帧。
- **每次编辑后重新 stamp**；**签名后任何编辑都要重新 stamp + 重新签名**。
- **保持 bundle 干净**：只放 `manifest.json`、`listing.json`、入口、图标、截图
  （卡应用为 `page.card`+`kit/`；声明自有 agent 时另加 `tools.json`/`AGENT.md`/`skills/`）。
- **无头运行**：`tools/octo run … --hidden`（设置 `MAKEPAD_HIDE_WINDOWS=1`，窗口不显示不抢焦点，
  截图由应用自身渲染，屏幕空也能截全）；多实例各用 `--port` 与 `--app-data`。
- **清理启动的进程**：用 `curl -s 127.0.0.1:<port>/quit`，不要 `pkill` 别人的窗口。
- **绝不伪造**批准、审核结果或提交记录。

### 3.4 gate 实际执行的检查（`hub check`，与 hub 同一份代码）
| 检查名 | 拒绝什么 |
| --- | --- |
| `identity` | `os.` 开头的 id（保留给系统应用） |
| `digest` | `integrity.bundle_blake3` 与字节不符 → 每次改动后 `hub stamp` |
| `publisher-signature` | 签名验证失败，或已签名却没给 `--publisher-key`；未签名在 `--allow-unsigned` 下只是警告 |
| `contents` | 扩展名不在 `.card .json .l0 .octoscript .splash .svg .png .jpg .jpeg .webp .ttf .otf .txt .md`；**任何符号链接直接中止检查** |
| `size` | 包 > 8,388,608 字节 |
| `assets` | `.splash` 中的 `http://`/`file://`/`../`；未声明的 `https://` 主机（除获 `images`/`web`）；其他文本文件里的 `http(s)://`/`file://`/`../` |
| `secrets` | 声明 `is_password:true` / `TextInputContentType.Password` / `NewPassword` / `OneTimeCode` |
| `listing` | 缺 `listing.json`；解析失败；**隐私政策非 https**；description 空或 >4000；subtitle >80；keywords >10；screenshots >8；资产非纯相对 `.png`/`.svg`；无图标或无截图；named 图标/截图在包内不存在 |
| `policy` | 未知能力；host 带 scheme/路径/端口/通配；有 host 却没 `net`；id 不合 `[a-z0-9.-]{1,64}` 或以 `.` 开头或含 `..`；空版本；宿主不提供的 agent 工具 |
| `version` | （配 `--catalog`）该 id+version 已在 catalog |
| `continuity` | （配 `--catalog`）id 已发布，而本次版本未签名或换了密钥 |

**gate 不检查**（由审核人/人负责）：截图是否真实、listing 文本是否占位、
图标小尺寸是否可读、隐私政策 URL 内容是否真实。
**gate 也不覆盖**：页面解析、图片有效性、**真实交互**。
**`hub scan` 只生成审核材料，不证明应用能运行，也不替代比赛评审。**
→ "预检通过"不能作为可运行性的证据。

**合法取值**：
- `category` ∈ `productivity utilities photo-video news weather travel finance health education entertainment games social shopping lifestyle developer`
- `platforms` ∈ `android ios macos windows linux openharmony web`（**只写真跑过的**）
- `age_rating` ∈ `all 12+ 16+ 18+`
- id 不得是或以宿主保留名结尾（`agents apphub appcard card dev octos os reference rinx sheets shell system terminal toolbox workflow`），也不得是或以原生应用 id / 主机名结尾（如 `com.example.rinx`）

### 3.5 远程控制桥（`tools/octo run` 打开，全部 GET，坐标为窗口点、y 向下）
| 路由 | 作用 |
| --- | --- |
| `/snap`（`?q=` 过滤） | 组件及其矩形与文本 |
| `/d` | 整棵组件树的文本形式 |
| `/click?x=&y=&wait=1` | 一次真实点击 |
| `/t?t=TEXT&wait=1` | 向获得焦点的输入框输入 |
| `/k?k=down&c=ReturnKey` | 一个按键事件 |
| `/log?n=50` | 最近日志行 |
| `/g?raw=1` | 窗口 PNG（`tools/octo shot` 存的就是它）；不带 `raw=1` 返回 `{"png": path,…}` |
| `/quit`（或 `/gq`） | 退出；**最后一定要调用** |

`on_render` 生成的控件自 makepad `d0a9def5` 起出现在 `/snap` 与 `/d`；应用稍后才添加的内容
（定时器/响应）在绘制后出现，**请轮询 `/snap?q=` 等待**。

### 3.6 发布清单（`tools/octo package-help`）
```
1. tools/octo doctor
2. manifest.json：id / name / version（每次发布都要新）/ 只留用到的 capabilities / 每个 host
3. listing.json：所有占位替换；publisher、support、privacy_policy_url 必须 https；platforms 只写测过的
4. tools/octo run $B --port 8141 --detach          → admitted
5. 逐项原生测试：/snap、/click?x=&y=、/t?t=、/k?k=down&c=ReturnKey
6. tools/octo shot 8141 $B/screenshots/01-main.png → 打开看；curl /quit
7. tools/octo check $B                              → PASSED
8. hub scan $B --packet build/review.json           → 回答七问
9. 【人】密钥在仓库外：hub keygen / sign-manifest / check --publisher-key；签名后任何编辑都要重签
10.【人】打 tag + 在 OctoSense-App-Hub 开 issue "Submit <id> <version>"
    绝不改它的 catalog.json/index/artifacts；未真正提交前绝不声称已提交或已批准
```
issue 需附：仓库 URL、tag、完整 commit SHA、包在仓库中的路径、发布者 id 与公钥（**或写 "unsigned"**）、
`hub check --publisher-key` 的完整输出、七问回答。**首次提交一定等人工处理**。

### 3.7 汇报格式（`AGENTS.md#reporting`）
- **Verified**：跑过的每条命令与结果（gate 输出**原样引用**）、截图路径
- **Not verified**：没跑过的（平台、`card-host` 不提供的宿主服务、手机），**写"未验证"，不写"应该可以"**
- **Waiting on a human**：已到达的人工检查点与下一步要人做什么
- **Gaps found**：与文档不符的运行时/工具行为，附最小复现

---

## 4. 硬指标（已核对）

| 项 | 规则 | 本包 |
| --- | --- | --- |
| 包内总量 | ≤ 8 MiB（8,388,608 B） | **122,734 B** ✓ |
| 包内扩展名 | 见 §3.4 `contents` | `.json .png .splash .svg` ✓ |
| 符号链接 | 一律禁止 | 无 ✓ |
| 图标 | ≤1 MiB、方形、自包含（SVG 命名空间 URI 不算外链） | 554 B，`viewBox 0 0 256 256` ✓ |
| `storage.max_bytes` | 上限 16 MiB | 4 MiB ✓ |
| `compute.instruction_budget` | 上限 20,000,000 | 8,000,000 ✓ |
| `compute.memory_bytes` | 上限 64 MiB | 32 MiB ✓ |
| listing | subtitle ≤80 / description ≤4000 / keywords ≤10 / screenshots ≤8 | 12 / 120 / 6 / 1 ✓ |

### 4.1 能力规则（`docs/CAPABILITIES.md`）
- **`matrix.*`（45 个精确名）只由 Rinx 小程序宿主提供。**
- **`octos.session.open/history/turn.start/turn.interrupt`**：由托管内核的 OctoSense shell 提供，
  **Rinx 小程序宿主也提供**；`card-host` 一律 `no service answers "octos"`。
- **商店应用可用的宿主服务**：`storage`、`net`、`images`、`web`、`camera`、`microphone`、`library`、
  `location`、`mail`、**`model`**、**`glance`**、4 个 `octos.*`、45 个 `matrix.*`。
  - **`model`（`model.complete`）**：一次性、按 schema 校验的模型调用（`{task,input,schema,class}`，
    `class` 为 `fast`/`strong`），由宿主按用户配置选模型并**限每日预算**；**shell 内的商店应用可用**，
    `card-host` 不提供（`no service answers "model"`）。
  - **`glance`**：向 glance 屏发布卡片；**获 `glance` 的任意 contained app 在 OctoSense shell 中可用**，
    仅 `card-host` 不提供。（**此前的"不要申请"名单把 `glance` 写错了，已更正**。）
- **不要申请**（当前无服务或商店应用零收益）：`prompt`、`llm`、`news`、`research`、`crawl`、
  `clipboard`、`ledger.read`。
- 未申请即未授权；前缀（`octos.`、`matrix.`）或自造名都会被拒。
- 每个 `host.request("<family>.<method>")` 需要能力 `<family>`（或精确服务名）。


### 4.2 Rinx 小程序机制（Rinx ADR 0005/0006/0007/0008）

**机制定位（ADR 0005）**：OctoScript 小程序包在 **Rinx** 内打开，保留原生 UI 与状态，
通过**单一宿主服务边界**调用 `matrix.*`（对**接收者自己的** Matrix 账号）与 Octos 会话/工具。
- **凭据留在宿主**：Matrix 凭据在 Rinx，模型凭据在 Octos；应用永远拿不到。
- **三重独立校验**：认证已安装包的字节与发布者；认证用户（用 Rinx 既有 Matrix 会话）；
  授权**这个应用实例**执行**这个具体操作**。**发布者签名不能替代用户许可。**
- **`octos.*` 由宿主拥有 peer**（ADR 0007）：启动时给应用一个**受限的宿主服务句柄**，
  应用不选 provider、不持有凭据；**只认精确注册的服务名**，以 `octos.` 开头不等于有权限。
- 关闭实例 = 撤销其租约、取消未完成工作、**丢弃迟到的回复**；返回不会终止 Rinx。
- 应用包声明**永不携带**凭据、文档、媒体密钥或授权。

**发行路径（ADR 0006，Rinx 1.1.0）**：`Discover → Mini apps` 的 **App Hub 入口**会打开原生库
（Recent / My apps / Browse）；**Add/Update 安装已审核版本**，**Open 为当前 Matrix 账号与所选房间
授予新的运行时会话**。`Developer` 入口才是我们用的文件夹导入。

**ADR 0005 的官方验证清单（针对我们这类应用，逐条照做）**：
1. A2App Matrix 解析契约；**授权拒绝、跨房间拒绝、实例撤销、迟回复处理**
2. 同一包走共享渲染器与 Rinx 宿主；**演练一次改变状态的输入与一次宿主服务结果**
3. 演练**真实 Matrix 与 Octos 协议适配器**，把协议夹具与实机结果**分开记录**
4. 验证独立与 OctoSense 宿主两种构建；确认 **Back、键盘、关闭/重开**，以及宿主 Rinx 复用 Octos provider
5. **明确记录未验证的平台/服务组合。解析器测试、mock provider 或静态截图本身都不算端到端完成。**

⚠️ 我们的清单对照：第 1 项**跨房间拒绝 / 实例撤销 / 迟回复**未测；第 4 项 **Back / 键盘 / 关闭重开**未测。

### 4.3 Rinx 读房授权 sheet（接收者独立授权的关键机制）
`Rinx/docs/adr/0007` 原文要点：
- **房间读取按账号授权并持久化。** 首次读某个房间时 Rinx 弹出读房 sheet，三个选项：
  **allow once / always allow / deny**。
- **45 秒内不回答即视为拒绝。**
- **"always" 只存给当前登录的 Matrix 账号**（`<data>/assistant/room_grants.json`）；
  **同一设备上的其他账号永不继承。**
- `Settings → Privacy → Assistant access` 列出已授权房间并可撤销。
- 把房间数据交给 `octos.turn.start` **需要同时具备 Matrix 读授权与该 Octos 授权**（ADR 0005）。
- 宿主服务默认超时 **60 秒**（服务可另行声明）。

⚠️ **更正**：此前"停止 / **90 秒** / 迟回调"里的 90 秒**没有文档依据**，应改为
**读房 sheet 45 秒**、**宿主服务默认 60 秒**。

---

## 5. 环境事实（实测，可直接复用）

| 项 | 值 |
| --- | --- |
| 宿主二进制 | `/opt/src/OctoSense/target/release/octosense`，sha256 `87ed4dccd14bac51222f40c38d4db086911790786b688a68a503002ada64ba25` |
| 构建基线 | **官方 Rinx `c515e5fc9b6dc22e67f7d551b09fdd793ec685a1`（零本地补丁）** |
| 宿主启动 | `DISPLAY=:99`、`XAUTHORITY=/srv/oncue-runtime/state/xauthority`、cwd `/srv/oncue-host-cwd`、`HOME=/srv/oncue-home`、`RINX_DATA_DIR=/srv/oncue-rinx-data-rinxchat`、`OCTOS_APP_CORE_BIN=/srv/oncue-runtime/octos/octos`、`--module rinx --test-action launch-rinx`；宿主模型 `octos: Model: MiniMax-M2.7` |
| 赛事服务器 | Homeserver `https://matrix.rinx.chat`（**直连即可，不需代理**）；认证 `https://auth.matrix.rinx.chat` |
| 赛事账号 | **`@codezzzsleep:matrix.rinx.chat`**（device `kI8muzdQV8`）；凭据 `/srv/oncue-runtime/secrets/rinx-chat.env`（600） |
| 测试房间 | `!2TfOHq2ZGCYO5WJmDC:matrix.rinx.chat`（"OnCue 试映室测试房"，12 条消息） |
| 登录方式 | **官方指南（`rinx-guide.md`）称 `auth.matrix.rinx.chat` 提供注册与密码找回**；<br>本机实测：**Matrix 客户端 API 的 `POST /register` 与 `m.login.password` 被关闭**（delegated auth），<br>但**认证网站上可以正常注册与登录**（已成功注册两个账号）→ 流程为**浏览器 SSO**。本机已装 firefox。 |
| 官方工具链 | `OctoScript-App-Design-Flow/tools/octo`；先 `. /root/hackthon/refs/octo-env.sh`（设置 `OCTO_HUB`/`OCTO_CARD_HOST`） |
| 参考仓库（完整克隆） | `/root/hackthon/refs/{hackathon-agenticapp26,OctoScript-App-Design-Flow,OctoSense-App-Hub,OctoSense,Octoscript,Rinx}` |
| 密钥 | 发布者私钥 `/srv/oncue-runtime/dev/keys/working.key`（id `oncue.dev`，公钥 `50578fd7e0d8ac51a1e9e590835427ce8e71f46dba491860c75ae4e7c8c78042`）——**永不入仓库** |
| **官方验证平台** | **仅 Apple silicon macOS**；**Windows 与 Linux 未验证**（我们跑在 Linux aarch64，属未验证平台） |
| Rinx 参赛基线提交 | `05daf9bdb05fafc6d8f04dcb312a35f1d46a661e`（2026-09-21 内容审查基线；课堂包另行锁定） |

---

## 6. 参赛提交入口与上架的关系（**重要：与 App Hub 提交是两件事**）

官方原文（`app-hub-submission.md`「当前使用方式」）：
> 截至 2026-09-21，**Rinx 的通用目录与包安装尚未接通，自动提交入口仍在建设。**
> **现阶段各轮评审以公开源码仓库和可运行作品为准，无需等待 Hub 上架。**
> 后续入口和适用宿主版本开放后，由赛事方公布使用方式。

`rinx-miniapps.md`：**"参赛无需等待上架。"**
`README.zh-CN.md`：**"参赛作品不等于自动提交到 App Hub；请向主办方确认他们需要什么。"**
`competition-schedule.md`：赛务"需公布…**提交入口**…"（即入口本身仍待赛务公布）。

→ **结论**：
1. **比赛评审** = 公开源码仓库 + 可运行作品（+ §2.6 的六类材料）；**没有正式提交门户**，也**不需要**先上架。
2. **App Hub 的 `Submit` issue** 是发布流程，与比赛提交**是两件事**，不要混为一谈。
3. 仍需向赛务/主办方确认**提交入口**（公告里的"指定 github 仓库"）。

**App Hub 核查版本（赛事引用的基准）**：`97c2a1fd9aa49a6b87586f228e070e0c16b1067b`
（我们本地构建的 App Hub 是另一个提交，结论以就近实测为准并标注版本）。

---

## 7. 已知 Gap / 环境坑（带复现）

1. **`tools/octo shot` 在本机不可用**
   ```
   tools/octo run <bundle> --port 8143 --detach   → ready: first frame drawn
   tools/octo shot 8143 out.png                   → GET /g?raw=1 failed: HTTP Error 404
   curl 127.0.0.1:8143/s        → 正常，窗口 412x892 存在
   curl 127.0.0.1:8143/g?raw=1  → {"err":"grab timeout (is this backend rendering?)"}
   curl 127.0.0.1:8143/gseq?n=1&every_ms=50 → 同样 grab timeout
   ```
   平台 Linux aarch64 + Xvfb + llvmpipe；带不带 `--hidden` 都一样。
   **变通**：`ffmpeg -f x11grab -video_size WxH -i :99+<x>,<y>` 抓窗口。
2. **已签名包在开发态一律被拒**：
   - `card-host` 拒绝已签名 manifest（即使加 `--allow-unsigned`）——*"请在签名之前截图"*；
   - **Rinx 的 Developer 文件夹导入同样故意拒绝发布者签名**（ADR 0006：*"its developer importer
     deliberately rejects publisher signatures"*；ADR 0008：*"Local imports remain visibly unsigned
     and cannot impersonate built-ins."*）。
   → **演示接收者流程、回访已签名版本时，都必须另做一份未签名副本。**
3. **matrix.org ≠ matrix.rinx.chat**：赛事用后者。此前在 matrix.org 上的一切"真实房间/Agent 回合"
   结论**作废**，只作内部溯源。
4. **xclick/xtype 的坐标偏移每次不同**：先 `xwininfo` 取实际窗口位置再换算。
5. **firefox 收到不到键盘**：X 输入焦点在 OctoSense 窗口；须 `XSetInputFocus` 到 firefox 主窗口。
6. **`pkill -f <关键词>` 会杀掉自己**（命令行含该关键词）——按进程名或端口杀。
7. **Splash 语法限制**（`docs/SCRIPT-API.md#gotchas`）：
   - **十六进制颜色**以 `#` 开头；**含 `e` 且紧邻数字时必须写 `#x`**（`#x1e1e2e`、`#x2ecc71`），
     `#x` 一律安全 —— 否则分词器会把它读成指数。
   - **无 `range()`**：用 `for i in n`。
   - **背景**：`View{show_bg: true draw_bg.color: …}` 在 `card-host` 中不绘制背景；
     用 **`SolidView`** 或 `RoundedView` 做填充面板。
   - **`ButtonFlat` 不能有子控件**：里面的 `Label` 不会被绘制。
   - `local_time()` 在 card-host 中是 **UTC**。
   - **文字默认白色**。
   - **`TextInput` 必须有数值高度**。
   - 无空块 + `else`（`on_render` 中 `if` 与 `for` 必须分开）；`ok` 是保留变量名。
   - `ui` 在主体执行后才注入，须 `start_timeout(0.05, …)` 启动。
8. **手机（Android）无法侧载任意应用包**；`card-host` 的远程控制桥在 Android 上被编译移除。

---

## 8. 当前状态（**每次状态变化后更新本节**）

### 8.1 已完成
- [x] 仓库梳理：45 个文件，Markdown 断链 0
- [x] 包规范：`tools/octo check`（未签名）→ **PASSED**，仅未签名警告
- [x] `oncue/BRIEF.md`（流程第 1 步）
- [x] `build/review.json`（审核包）+ `build/REVIEW-ANSWERS.md`（七问，route: human-review）
- [x] 产品/隐私/验证/依赖文档齐全；listing 全部 gate 限额通过
- [x] 宿主改用**官方 Rinx 重建**（弃用本地补丁），`:99` 已换装运行
- [x] **赛事服务器端到端实测通过**：登录 → 导入 → Review（房间保留）→ Run →
      `matrix.room_info`/`read_messages` 读到真实房间 → `octos.turn.start` 完成
      （内核日志 `LLM response received … response_content_len=1839`）
- [x] tag `v0.4.4` 已打并推送

### 8.2 未完成（按优先级）
| # | 缺口 | 说明 |
| --- | --- | --- |
| 1 | **接收者独立授权演示** | **官方硬要求**，零证据；需第二个账号（分享 → 接收者独立授权 → 自己的草稿/账号，不继承权限） |
| 2 | ⚠️ **"执行 → 核验结果"缺失** | 官方两次强调"仅生成界面/摘要不足以证明任务自动化"，Rinx 基线还要求"**结果回到原会话**"。本应用不发送 → **产品决策** |
| 3 | **开 Submit issue** | 唯一挡住 App Hub 正式提交的动作；本机无 GitHub token |
| 4 | **比赛提交入口未确认** | 入口仍待赛务公布；现阶段"以公开源码仓库和可运行作品为准，无需等待上架" |
| 4b | **2–3 分钟演示 + 第二张关键截图** | `curriculum.md:92` 明确的初赛材料，我们还没有 |
| 4c | **"一次操作 + 可核对的结果 + 一个失败/空状态"** | 初赛原型的最低演示要求；失败/空状态已有部分证据 |
| 5 | DoD #3：交互用**远程桥**驱动 | 此前用 XTest；`/snap` 已验证可用 |
| 6 | DoD #4：**空/错误/重启**三态完整测试 | 证据不完整 |
| 7 | 宿主内**停止 / 超时（读房 sheet 45 s、服务默认 60 s）/ 迟回调**在赛事服务器重测 | 旧结论在 matrix.org 上，已作废；"90 秒"无依据已更正 |
| 7a | **读房授权 sheet 三选项与 45 秒拒绝、跨账号不继承**未演示 | 接收者独立授权的核心机制 |
| 7b | **跨房间拒绝 / 实例撤销 / 迟回复**未测（ADR 0005 第 1 项） | 需在 Rinx 上跑 |
| 7c | **Back / 键盘 / 关闭-重开**未测（ADR 0005 第 4 项） | 需在 Rinx 上跑 |
| 8 | 包的交付签名状态 | 现为**已签名**；官方开发态期望未签名（已签名时 `card-host`/`octo check` 拒绝） |
| 9 | 截图未用 `tools/octo shot` | 该工具在本机不可用（见 §7.1），已用 ffmpeg 变通 |
| 10 | **报名是否完成** | 9/23 截止，需确认 |
| 11 | 无运行视频（可选） | — |

---

## 9. 待决策（需人定，不要自行决定）

1. **定位**：是否补「执行 → 核验结果」（例如用户确认后把选中草稿**回写到原会话**并显示真实回执），
   以满足官方最小交付与 Rinx 基线的"结果回到原会话"？还是强化"核验结果"环节？
2. **交付签名状态**：仓库里放**未签名**（官方开发态、`octo check` PASSED）还是**已签名**？
3. **比赛提交入口**：向主办方确认初赛作品提交到哪个仓库/表单（与 App Hub issue 是两件事）。
4. **报名状态**：是否已完成个人报名（9/23 截止）。

---

## 10. 纪律（每次都必须遵守）

- **绝不**向任何 Matrix 房间发送消息（本应用不发送；验证也不发）。
- **绝不**打印或提交任何凭据、token、私钥；密钥只在仓库外且 600。
- **绝不**绕过 human checkpoint：不伪造批准、审核结果、提交记录。
- 卡片包面向比赛：**不放**内部协作产物、运维脚本、验收台账、历史考古、探针脚本。
- 任何"真实宿主"结论必须标注**在哪个服务器、哪个版本**上取得。
- 单次授权不得扩大为跨会话自动发言权限。

---

## 11. 常用命令

```sh
# 官方工具链
. /root/hackthon/refs/octo-env.sh
cd /root/hackthon/refs/OctoScript-App-Design-Flow
python3 tools/octo doctor
python3 tools/octo package-help
python3 tools/octo run /root/hackthon/OnCue/oncue/bundle --port 8141 --hidden --detach
curl -s "127.0.0.1:8141/snap?q=Button" | head -c 400
curl -s "127.0.0.1:8141/click?x=150&y=140&wait=1"
curl -s 127.0.0.1:8141/quit

# 未签名副本（回访已签名版本时必须）
rm -rf /tmp/oncue-unsigned && mkdir -p /tmp/oncue-unsigned
cp -a oncue/bundle /tmp/oncue-unsigned/bundle
python3 -c "import json,pathlib;p=pathlib.Path('/tmp/oncue-unsigned/bundle/manifest.json');d=json.loads(p.read_text());d['integrity'].pop('signature',None);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+chr(10))"
python3 tools/octo check /tmp/oncue-unsigned/bundle     # → PASSED

# 重新 stamp + 签名（内容改动后）
$OCTO_HUB stamp oncue/bundle
$OCTO_HUB sign-manifest oncue/bundle --key /srv/oncue-runtime/dev/keys/working.key --key-id oncue.dev
$OCTO_HUB check oncue/bundle --publisher-key oncue.dev=50578fd7e0d8ac51a1e9e590835427ce8e71f46dba491860c75ae4e7c8c78042

# 审核包
$OCTO_HUB scan <未签名副本>/bundle --packet build/review.json
```

---

## 12. 附录：依据文档清单（完整性可审计）

本文件的内容全部来自以下**已逐字读完**的上游文档。若要核对"是否有遗漏"，
按本表逐项检查；新增上游文档时同步补进本表。

### 12.1 竞赛仓库 `gosimfoundation/hackathon-agenticapp26`
| 文件 | 贡献的章节 |
| --- | --- |
| `README.md` | §2.2 竞赛定位、12 场景、报名与名单锁定、§2.5 奖项 |
| `docs/competition-schedule.md` | §2.1 时间线、评审与晋级规则、赛务待公布项 |
| `docs/app-hub-submission.md` | §2.3 提交材料 6 项、§2.7 运行验收清单、§2.8 交付形态表、§6 提交入口现状 |
| `docs/curriculum.md` | §2.6 初赛材料（2–3 分钟演示、两张截图、一次操作/可核对结果/失败或空状态） |
| `docs/rinx-miniapps.md` | §2.4 独立授权机制、选手起步 5 步、基线提交 `05daf9bd` |
| `docs/rinx-guide.md` | §5 赛事 Matrix 注册与登录方式 |
| `docs/octosense-scenario-update-plan.md` | §2.2 最小交付原文、"仅生成界面/摘要不足" |
| `AGENTS.md` | 仓库性质（官网仓库，非作品仓库） |

### 12.2 设计流程仓库 `OctoSense-org/OctoScript-App-Design-Flow`
| 文件 | 贡献的章节 |
| --- | --- |
| `README.zh-CN.md` | §3.1 快速上手预期输出、§5 平台（仅 macOS 已验证）、§7.2 签名与截图关系、§6 参赛≠上架 |
| `AGENTS.md` | §3.2 Definition of Done、§3.3 每个应用的规则、§3.7 汇报格式、语法提醒 |
| `flows/README.md` | §3.6 共同交接（stamp/check/run/shot） |
| `flows/script-app/FLOW.md` | §3.1 十四步流程 |
| `docs/PUBLISHING.md` | §3.4 gate 11 项检查表、§3.2 listing 取值与限额、§3.5 远程桥路由 |
| `docs/CAPABILITIES.md` | §4.1 能力规则、上限、"不要申请"名单、保留 id 名 |
| `docs/QUICKSTART.md` | §5 工具链与运行方式（部分） |
| `docs/HOST-SERVICES.md` | §3.3 宿主服务与面板（部分） |
| `docs/NATIVE-WORKSPACE.md` | §5 原生运行时工作区（部分） |

### 12.3 App Hub 仓库 `OctoSense-org/OctoSense-App-Hub`
| 文件 | 贡献的章节 |
| --- | --- |
| `docs/PUBLISHING.md` | §3.6 发布清单原文、签名与提交契约、Do not 清单 |
| `docs/FIRST-APP.md` | §3.3 `{{assets}}` 规则、§7.2 card-host 拒绝已签名、§1.1 仓库结构 |
| `docs/ICONS.md` | §4 图标与包体规则 |
| `README.zh-CN.md` | §5 App Hub 定位 |

### 12.4 Rinx 仓库 `hagency-org/Rinx`
| 文件 | 贡献的章节 |
| --- | --- |
| `docs/adr/0002-octoscript-mini-app-authority.md` | §4.2 三重校验、凭据边界 |
| `docs/adr/0005-octoscript-miniapps-matrix-octos.md` | §4.2 机制定义 + **官方 5 项验证清单** |
| `docs/adr/0006-shared-app-hub-miniapps.md` | §4.2 Rinx 1.1.0 的 App Hub 库安装/打开路径 |
| `docs/adr/0007-host-owned-octos-app-peers.md` | §4.2 `octos.*` 由宿主拥有 peer、精确服务名 |
| `docs/adr/0008-rinx-system-app-catalog.md` | §4.2 内置目录与导入包的边界 |
| `docs/rinx-guide.md`（赛事仓库） | §5 Matrix 服务器与登录 |

### 12.5 已做的完整性审计（2026-10-02）
用独立审计员（subagent）以本文件为基准、对上述全部文档做逐条比对，**发现并修正了 16 处遗漏/不准确**：
复赛材料清单（含队外用户试用记录）、最佳 Agentic 评分维度、初赛材料漏"已报名成员名单"、
时间表漏 5 个节点、9/24 环境发布节点、决赛答辩与计分流程、出勤/现场/晋级口径、
Rinx 开发态导入同样拒绝发布者签名、`hub scan` 不证明可运行、**十六进制规则写错（应为 `#x`）**、
`glance` 被误列入"不要申请"、漏记 `model.complete`、Splash gotchas 缺 6 条、
**读房授权 sheet 机制（45 秒）与"90 秒"无依据**、房间数据转交 octos 需两类授权、
注册说法与官方指南矛盾。全部已并入正文。

### 12.6 尚未通读（若后续需要再读，读完请补进上表）
`OctoScript-App-Design-Flow/docs/SCRIPT-API.md`、`docs/AI-SERVICES.md`（1325 行）、
`docs/GLOSSARY.md`、`docs/app-card-design-requirements.md`（已读，属卡应用视觉需求，与本脚本应用关系小）、
`docs/matter-centered-ux-research.md`、`OctoSense/` 与 `Octoscript/` 各仓库的多数文档、
`hackathon-agenticapp26/docs/courses/**`、`docs/demo/**`、`docs/promo-article.md`、
`Rinx/lab/**`。

> **备注**：`docs/app-card-design-requirements.md`（208 行，卡应用与事务 Tile 的 UX 需求）
> 已读，其 SRC-01…07 / TIME-01…12 / AC-01…14 面向**卡应用（L0）**形态；
> 本作品是**脚本应用**，不逐条适用，但它的"来源可追溯""原文与模型复述分开标识"
> 与本应用的设计一致。
