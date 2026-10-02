# 核心事实审查清单（供人工逐条核对）

> **用途**：这是本项目所有核心事实的**唯一权威清单**。此前我反复口头复述、前后不一致，
> 现在全部落成可逐条核对的形式：**原文 → 出处（文件:行号）→ 对我们的含义 → 现状 → 需你确认什么**。
>
> **依据**：2026-10-02 完整克隆并逐字读取的 6 个仓库
> `gosimfoundation/hackathon-agenticapp26`(a2a3e2e)、`OctoSense-org/OctoScript-App-Design-Flow`(caa5d36)、
> `OctoSense-org/OctoSense-App-Hub`(41bc959)、`OctoSense-org/OctoSense`(c19da8d)、
> `OctoSense-org/Octoscript`(5991dfa)、`hagency-org/Rinx`(c515e5f)。
> 原文**逐字引用**，出处为 `仓库相对路径:行号`，可自行打开核对。

---

## A. 赛事：时间

| # | 原文 | 出处 | 含义 | 需确认 |
|---|---|---|---|---|
| A1 | "9/23 23:59 前完成个人报名；10/4 23:59 初赛提交时提交队名、队长和成员登记信息并锁定名单。" | `hackathon-agenticapp26/docs/competition-schedule.md:42` | 报名 9/23 已截止；名单 10/4 锁定 | ⚠️ **报名是否已完成？** |
| A2 | "9/13（日）–10/4（日）23:59 ｜ 初赛海选：场景与可运行作品" | `…/competition-schedule.md:21` | 文档写的是 10/4 23:59 | — |
| **A2b** | **用户 2026-10-02 告知：初赛提交日往后延期两天** | **用户口头告知（非文档）** | **新截止 10/6 23:59**；后续节点是否顺延未知 | ⚠️ **需你确认或等官网更新** |
| A3 | "**9/24 18:00 前**：发布锁版本环境、支持设备、启动步骤、可用能力、示例数据和替代练习范围；9/25 收集异步自检结果。" | `…/competition-schedule.md:123` | 官方环境 9/24 已发布；练习数据范围须以它为准 | 我们**未核对**官方锁版本环境与我们的差异 |
| A4 | "10/5（一）–10/6（二）18:00 ｜ 初赛评审" | `…/competition-schedule.md:22` | 评审只用冻结版本 | — |
| A5 | "10/6 20:00 公布 50 人晋级" | `…/competition-schedule.md:23` | — | — |
| A6 | "10/9 23:59 复赛提交与版本冻结" | `…/competition-schedule.md:26` | — | — |
| A7 | "10/10（六）–10/11（日）18:00 ｜ 复赛材料评审" | `…/competition-schedule.md:27` | 结束时刻是 **10/11 18:00** | — |
| A8 | "10/12 13:00–17:00 线上决赛分组答辩；17:30 提供评分明细，18:30 前收齐纠错，19:30 锁分" | `…/competition-schedule.md:30`, `:92` | 答辩 8 分钟/项目（3+2+2+1） | — |
| A9 | "10/18（日）–10/31（六）｜ 赛后采纳与归档" | `…/competition-schedule.md:35` | 不改变线上结果 | — |

## B. 赛事：晋级与奖项

| # | 原文 | 出处 | 含义 |
|---|---|---|---|
| B1 | "晋级按人数统计，不是 50 支队伍；奖项以项目团队为单位，单人队伍同样适用。直播出勤不作为晋级条件。" | `…/competition-schedule.md:44` | 我队按人数算 |
| B2 | "奖池 ¥50,000：一等奖 1 名 ¥20,000、二等奖 2 名 ¥9,000、三等奖 3 名 ¥4,000" | `…/README.md:84` | 已公开金额 |
| B3 | "10/12 结合答辩与问答完成同一轮复赛评奖，不叠加初赛分" | `…/competition-schedule.md:84` | 初赛分不带入 |
| B4 | "现场不再评分"；"不能到场仍保留线上名次和奖励" | `…/competition-schedule.md:96,98` | — |

## C. 赛事：作品形态（**最关键**）

| # | 原文 | 出处 | 对我们的含义 | 现状 |
|---|---|---|---|---|
| **C1** | "统一最小交付应能展示：**事件或意图输入 → Agent 理解并形成操作计划 → 用户查看或授权 → 执行 → 核验结果 → 状态变化或失败处理**。**仅生成界面、摘要或静态卡片，不足以证明完成了任务自动化。**" | `…/docs/octosense-scenario-update-plan.md:56` | ⚠️ **本应用产出"摘要+假设对白"且不发送 → 可能被判为"仅生成摘要"** | ❌ **不满足** |
| **C2** | "10/9 23:59 前由晋级的 50 人提交…**区分参考卡、练习数据与真实在线结果，说明事件或意图输入、Agent 理解与计划、授权、执行、结果核验和后续状态处理；只生成界面或摘要不足以证明完成任务。**" | `…/competition-schedule.md:80` | 同上，复赛口径重复强调 | ❌ 同上 |
| **C3** | "实际演示应覆盖**启动、真实输入、必要授权、Agent 执行、结果核验和失败处理**。**聊天或账号相关作品还需演示接收者独立授权**，避免把发送者身份或权限带给接收者。" | `…/docs/app-hub-submission.md:51` | 验收六项 + 接收者授权 | ⚠️ 部分（缺结果核验、接收者授权） |
| **C4** | "即时消息**必须与 Rinx 绑定**"；"以 Rinx 为起点，做能分享、能使用的小程序" | `…/docs/octosense-scenario-update-plan.md:58,62` | 我们赛道 ✓ | ✅ |
| **C5** | "现有的原生应用分享：卡片携带内置应用 ID、版本及源码摘要；接收者打开同一内置应用"；"**发布结果**：预览后选聊天、确认账号和内容，由宿主通过 Matrix SDK 发送" | `…/docs/rinx-miniapps.md:13,15` | 官方期望含**分享**与**发布到聊天** | ❌ 我们都没有 |
| **C6** | "**独立授权**：每次打开须授权；授权关联账号、登录会话和应用实例，**最长一小时**，关闭或退出后撤销"；"**不能继承发送者的权限**" | `…/docs/rinx-miniapps.md:14` | 接收者授权的准确机制 | ❌ 未演示 |
| **C7** | "候选作品：Hub 卡片包 / 网页小程序 / 原生宿主扩展 / ROM 扩展"；"不能只交任意 `.card` 文件并假设现有宿主会安装" | `…/docs/rinx-miniapps.md:26`、`app-hub-submission.md` 形态表 | 我们属 **Hub 卡片包** | ✅ |
| **C8** | "**参赛无需等待上架。**"；"截至 2026-09-21，Rinx 的通用目录与包安装尚未接通，**自动提交入口仍在建设。现阶段各轮评审以公开源码仓库和可运行作品为准**" | `…/docs/rinx-miniapps.md:31`、`app-hub-submission.md:9` | **比赛提交 ≠ App Hub 提交**；无正式门户 | ⚠️ **提交入口需向赛务确认** |
| **C9** | "Agent 辅助开发、通过包预检、成功上架或累计 PR 数量，**均不能单独替代作品效果证据。**" | `…/docs/app-hub-submission.md:53` | 只能靠运行效果举证 | — |
| **C10** | "最佳 Agentic 评价任务自动化、**可靠性、结果核验、人机协作和复现证据**" | `…/docs/curriculum.md:96` | 五个评分维度 | — |
| **C11** | "最佳 Agentic…应用层作品可以获得最佳 Agentic 奖，**不要求修改 ROM，也不要求提交与自身任务无关的 PR 或 issue**" | `…/docs/octosense-scenario-update-plan.md:89` | 我们不必做贡献 | ✅ |

## D. 赛事：提交材料

| # | 原文 | 出处 |
|---|---|---|
| D1 | 初赛："10/4 23:59 前提交简短需求、可运行最小原型及启动说明、固定版本源码或包、**2–3 分钟演示**、**两张关键截图**、数据来源与限制、**已报名成员名单**。至少展示**一次操作及可核对的结果，以及一个失败或空状态**。静态概念稿本身不满足原型要求。" | `…/competition-schedule.md:74` |
| D2 | 复赛："可运行应用、安装步骤、冻结版本、能力说明、正常与失败场景验证、**队外用户试用记录**、完整演示及已知限制" | `…/competition-schedule.md:80` |
| D3 | 通用 6 项：公开源码仓库+固定提交号+Apache-2.0；目标/场景/图标/截图/作者/支持；宿主版本/平台/依赖/启动；数据来源/权限/隐私/授权拒绝失败；Agent 任务演示（输入/步骤/如何核验/哪些需人工确认）；截图日志视频+复现步骤 | `…/docs/app-hub-submission.md` |

## E. 发布流程（App Hub，官方契约）

| # | 原文 | 出处 |
|---|---|---|
| E1 | "**Only `bundle/`.** Everything else in the app repository (AGENTS.md, notes, tools, keys, logs, `.local-state/`, `build/review.json`) stays outside it." | `OctoScript-App-Design-Flow/docs/PUBLISHING.md:21` |
| E2 | "`hub check` (`crates/app-hub/src/gate.rs`) is **the same code the hub runs**." | `…/docs/PUBLISHING.md:39` |
| E3 | "**The route maintainers accept now:** 1. Push the signed bundle to your app's public repository and tag the commit. 2. Open an issue in OctoSense-App-Hub titled `Submit <app id> <version>`… 3. **Do not open a pull request that edits `catalog.json`, `index/` or `artifacts/`**" | `OctoSense-App-Hub/docs/PUBLISHING.md:721,725,734` |
| E4 | "**Definition of done**（交接给人之前）：1 `tools/octo check` → `— PASSED` 只剩未签名警告；2 真实截图且每张看过；3 每个交互在 `card-host` 用远程桥原生驱动并观察；4 **空、错误、重启**状态都跑过；5 `hub scan` packet 在 bundle 外且七问已回答；6 清单执行到第一个 HUMAN | `OctoScript-App-Design-Flow/AGENTS.md:93` |
| E5 | "**No dummy screenshots.** Screenshots are captures of the real app in a real state" | `…/AGENTS.md:68` |
| E6 | "**Restamp after every edit.**"；签名后任何编辑都要重新 stamp + 签名 | `…/AGENTS.md:71` |
| E7 | "**Keep the bundle clean.**" | `…/AGENTS.md:73` |
| E8 | "**Every AI feature is optional.**… `card-host` serves neither: every call there answers `no service answers "…" this device`" | `…/AGENTS.md:51` |
| E9 | gate 拒绝项：`identity`(os. 前缀) / `digest` / `publisher-signature` / `contents`(扩展名白名单、**符号链接中止**) / `size`(>8 388 608 B) / `assets`(http\://、file\://、../、未声明主机) / `secrets`(is_password 等) / `listing`(≥1 截图、https 隐私 URL、各字段限额) / `policy` / `version` / `continuity` | `…/docs/PUBLISHING.md:43-56` |
| E10 | "App Hub 核查版本：**97c2a1fd**"（我们本地构建是 `41bc959`，**版本不同**） | `hackathon-agenticapp26/docs/app-hub-submission.md`「核查依据」 |

## F. 运行机制（Rinx，我们的宿主）

| # | 原文 | 出处 | 含义 |
|---|---|---|---|
| F1 | "**Room reads are granted per account and persisted.** The first `read_room` of a room shows Rinx's read sheet with three answers: **allow once, always allow, or deny**. If the person does not answer **within 45 seconds**, that counts as a denial. 'Always' is stored for the signed-in Matrix account only… **Another account on the device never inherits it.**" | `Rinx/docs/adr/0007-…md:472-477` | **接收者独立授权的核心机制**；45 秒（不是我之前说的 90 秒） |
| F2 | "App-to-Octos transfer of room data **requires both** the relevant Matrix read grant **and** the Octos grant." | `Rinx/docs/adr/0005-…md:19` | 把房间消息交给 `octos.turn.start` 需**两类授权** |
| F3 | "…its developer importer **deliberately rejects publisher signatures**." | `Rinx/docs/adr/0006-…md:12` | **Rinx 的 Developer 导入也拒绝已签名包**（不只 card-host） |
| F4 | "**A parser test, mocked provider or static screenshot alone is not end-to-end completion.**" | `Rinx/docs/adr/0005-…md:42` | 静态截图不算端到端 |
| F5 | Rinx 1.1.0：`Discover → Mini apps` 的 **App Hub 入口**打开原生库（Recent/My apps/Browse），**Add/Update 安装**，**Open 授予新的运行时会话** | `Rinx/docs/adr/0006-…md` | 正规商店路径 |
| F6 | "upstream Rinx… **holds exactly one session**"（无应用内多账号切换） | `Rinx/src/home/account_menu.rs:13` | **演示接收者要用第二个宿主实例** |
| F7 | `matrix.*`（45 个名）"**Only Rinx's mini-app host**" 提供 | `…/docs/CAPABILITIES.md:61` | 我们必须在 Rinx 里验证 |
| F8 | `octos.*` 4 个："An OctoSense shell that hosts a kernel…serves them once the person allows the app's agent at first use… **Rinx's mini-app host serves them too.**" | `…/docs/CAPABILITIES.md:60` | ✓ |

## G. 环境事实（本机实测，非文档）

| # | 事实 | 来源 |
|---|---|---|
| G1 | 宿主 `octosense` 用**官方 Rinx c515e5fc9b6d 零补丁**重建，sha256 `87ed4dcc…` | 本次构建 |
| G2 | 赛事服务器 `matrix.rinx.chat` **直连可达**（不需代理）；认证 `auth.matrix.rinx.chat` | 本次实测 |
| G3 | Matrix **客户端 API** 的 `/register` 与 `m.login.password` 被关闭；**认证网站上可正常注册/登录**（已注册 2 个账号） | 本次实测 |
| G4 | 账号 A `@codezzzsleep:matrix.rinx.chat`；账号 B `@oriontraxmandl397:matrix.rinx.chat` | 你提供 |
| G5 | 测试房 `!2TfOHq2ZGCYO5WJmDC:matrix.rinx.chat`（12 条消息） | 本次创建 |
| G6 | 官方工具链 `tools/octo` 在本机可用；**`tools/octo shot` 不可用**（`grab timeout`，见 §7.1） | 本次实测 |
| G7 | 官方声明**只验证过 Apple silicon macOS**；**Linux 未验证**（我们跑 Linux aarch64） | `OctoScript-App-Design-Flow/README.zh-CN.md:51` |
| G8 | 宿主模型 `octos: Model: MiniMax-M2.7` | 宿主日志 |

## H. 我们项目的现状

**已完成**
1. 包 `oncue/bundle` 0.4.4，digest `9b221cd7…`；`tools/octo check`（未签名）→ **PASSED**
2. `BRIEF.md`、`build/review.json`、`build/REVIEW-ANSWERS.md`（七问，route: human-review）
3. 仓库 45 个文件、断链 0；listing 全部 gate 限额通过；图标与包体合规
4. 赛事服务器端到端：登录 → 导入 → Review（房间保留）→ Run → **真实房间读取** → **Agent 回合**
   （内核日志 `LLM response received … response_content_len=1839`）
5. 宿主换装官方 Rinx（弃用本地补丁）

**未完成（14 项）**
1. ❌ **C1/C2「执行 → 核验结果」** —— 本应用不发送，可能被判"仅生成摘要"（**产品决策**）
2. ❌ **C3/C6 接收者独立授权** —— 账号 B 已给，尚未演示
3. ❌ **F1 读房授权 sheet**（三选项 / 45 秒 / 跨账号不继承）未演示
4. ❌ **D1 2–3 分钟演示 + 第二张关键截图** —— 初赛硬性材料
5. ❌ **D2 队外用户试用记录** —— 复赛材料
6. ❌ **E3 开 Submit issue** —— 本机无 GitHub token
7. ❌ **C8 比赛提交入口** —— 需向赛务确认
8. ❌ **F3 已签名包被拒** —— 演示/回访需未签名副本（有变通做法）
9. ⚠️ **F1/F4 跨房间拒绝、实例撤销、迟回复** 未测
10. ⚠️ **Back / 键盘 / 关闭-重开** 未测
11. ⚠️ **E4-3 用远程桥驱动全部交互** —— 此前用 XTest
12. ⚠️ **E4-4 空/错误/重启三态** 证据不完整
13. ⚠️ **A3 官方锁版本环境** 未与我们环境核对
14. ⚠️ **A1 报名是否完成** 未确认

---

## I. 需要你人工确认的 6 件事

| # | 事项 | 我的建议 | 你的决定 |
|---|---|---|---|
| **1** | **C1/C2 定位**：是否给应用补"执行 → 核验结果"（如**用户确认后把选中草稿回写到原会话**并显示真实回执）？ | 官方两处明说"仅生成界面/摘要不足"；Rinx 基线还要求"结果回到原会话"。**建议补**，否则有被判不达标的风险 | ☐ 补执行/回写　☐ 保持现状 |
| **2** | **C6 接收者独立授权**：用账号 B 起第二个宿主实例演示？ | 我可以做：A 存私有草稿 → B 打开同一应用 → B **必须自己授权**（读房 sheet 三选项）→ B 草稿为空 → 两账号数据目录不同 | ☐ 现在做　☐ 稍后 |
| **3** | **C8 比赛提交入口**：初赛作品交到哪个仓库/表单？ | 官方称"入口仍在建设，以公开源码仓库和可运行作品为准"。**需你或赛务确认** | ☐ 我去问　☐ 你已知道：______ |
| **4** | **A1 报名**：9/23 截止的个人报名是否已完成？ | 未完成则无法参赛 | ☐ 已完成　☐ 未完成 |
| **5** | **D1 演示材料**：2–3 分钟演示 + 两张关键截图，要不要我准备？ | 初赛硬性材料 | ☐ 要　☐ 不要 |
| **6** | **交付签名状态**：仓库里放未签名（官方开发态、`octo check` PASSED）还是已签名？ | 官方 DoD 期望**未签名**；已签名时 `card-host`/`octo check` 都拒绝 | ☐ 未签名　☐ 已签名　☐ 两者都留 |

---

## J. 出处索引（我读过的全部文档）

**竞赛仓库 `hackathon-agenticapp26`**：`README.md`、`AGENTS.md`、`docs/index.md`、`docs/SUMMARY.md`、
`docs/app-hub-submission.md`、`docs/competition-schedule.md`、`docs/curriculum.md`、`docs/rinx-guide.md`、
`docs/rinx-miniapps.md`、`docs/octosense-scenario-update-plan.md`、`docs/courses/2026-09-26/README.md`、
`docs/demo/2026-09-26/projects.md`、`docs/promo-article.md`（部分）

**设计流程仓库 `OctoScript-App-Design-Flow`**：`README.zh-CN.md`、`AGENTS.md`、`CLAUDE.md`、
`flows/README.md`、`flows/script-app/FLOW.md`、`docs/PUBLISHING.md`、`docs/CAPABILITIES.md`、
`docs/ICONS.md`（在 App Hub）、`docs/QUICKSTART.md`（部分）、`docs/HOST-SERVICES.md`（部分）、
`docs/app-card-design-requirements.md`、`docs/NATIVE-WORKSPACE.md`（部分）

**App Hub `OctoSense-App-Hub`**：`README.zh-CN.md`、`docs/PUBLISHING.md`、`docs/FIRST-APP.md`、`docs/ICONS.md`

**Rinx**：`docs/adr/0002/0005/0006/0007/0008`、`src/home/account_menu.rs`（多账号结论）

**尚未通读**：`OctoScript-App-Design-Flow/docs/AI-SERVICES.md`(1325 行)、`docs/SCRIPT-API.md` 全文、
`docs/GLOSSARY.md`、`OctoSense/` 与 `Octoscript/` 的多数文档、`hackathon…/docs/courses/**` 与 `demo/**` 全文、
`Rinx/lab/**`、`Rinx/RELEASE_NOTES`。
