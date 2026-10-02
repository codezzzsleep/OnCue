# 最新官方群通知与本地源码核对（2026-10-02 晚）

本记录对应用户在 2026-10-02 转述的最新官方通知。**群通知、仓库文档、代码实现、本机实测分别标注，不互相冒充。**
本轮同步参考源码、阅读原文、更新规程；没有修改应用业务代码、重签、推送、发 issue、发送 Matrix 消息或重建/换装宿主。

## 1. 本次按什么规则工作

| 项目 | 最新通知与执行口径 |
| --- | --- |
| 初赛形态 | 只做 OctoScript 应用；Rinx 小程序同样基于 OctoScript。原生/Rust/ROM 扩展放初赛后。 |
| 宿主 | 作品必须在 OctoSense 生态中运行；不能先交独立应用，声称以后再接入。OnCue 继续在 Rinx 内运行。 |
| 发布 | AppCard 经 App Hub 发布；不能用旧文档“无需等上架”来省略发布流程。 |
| 迭代 | 基本功能 → 结合 octos 的运行时 Agent → 整体可用后再调 UI。必要的文字可读/按钮可达修补仍属基本可用性。 |
| 初赛延期 | 通知原话为延期两天。按旧截止 10/4 23:59 推算为 **2026-10-06 23:59，北京时间**。 |
| 明日更新 | 按本次通知日期指 **2026-10-03**；具体发布时间、提交、能力与平台尚未给出。先同步、读差异和报告，不自动重建。 |

**时间纠正**：旧赛事仓库仍写初评 10/5–10/6 18:00、晋级 10/6 20:00，早于新截止。不能既承认延期，又把这些旧节点当作重新确认的新安排；也不能擅自全部顺延两天。此前项目记录中的“后续节点不变”“必须10/5前冻结”为过度确定的表述，现撤回。10/5 前准备稳定候选仅为内部留余量目标。

## 2. Git 同步结果与边界

六个参考仓库已经存在，无须覆盖重克隆。同步前均为干净 main；实际检查发现，除了赛事仓库，其余五个原为浅克隆。此次获取所有公开分支和 tags，并执行 `--unshallow` 补全历史；只做 `merge --ff-only origin/main`，未重置或清理工作树。

| 本地参考仓库 | 更新前 | 更新后（完整 HEAD） | 结果 |
| --- | --- | --- | --- |
| hackathon-agenticapp26 | a2a3e2e | `a2a3e2efbd6d009180fbb647fc87683fc1f79dc1` | main不变，非浅克隆 |
| Octoscript | 5991dfa | `5991dfae9344589e732b2605b530f788e8bbcd11` | main不变，历史已补全 |
| OctoScript-App-Design-Flow | caa5d36 | `caa5d3648be9289f11056c386a645038af14e5a5` | main不变，历史已补全 |
| OctoSense | c19da8d | `b221f7b4c877dd823d04e4ee510cc74880de5535` | fast-forward，12提交，34文件，+1653/-279 |
| OctoSense-App-Hub | 41bc959 | `41bc959fc13c44e27fa462df40eb8e300d48ab40` | main不变，历史已补全 |
| Rinx | c515e5f | `c515e5fc9b6dc22e67f7d551b09fdd793ec685a1` | main不变，历史已补全 |

同步方式：Git 直接访问官方仓库；清除 HTTP(S)/ALL_PROXY 环境变量并覆盖 Git HTTP proxy，SSH 明确关闭 ProxyCommand/ProxyJump。没有使用网页提取/URL 总结服务。

失败也保留：Design Flow 的 HTTPS fetch 先发生 HTTP/2 断流（exit128），改 HTTP/1.1 后连接超时（exit128）；随后使用已验证主机密钥的直连 SSH 成功（exit0）。宿主/App Hub/Rinx 也通过直连 SSH 同步成功。终检六仓 `--is-shallow-repository` 均为 `false`，工作树均干净。

**范围**：“六仓非浅克隆”不等于全部源码已读完，也不表示递归拉齐整个生态所有传递依赖。现有 Makepad、Octoscript-Makepad 构建依赖已在宿主构建目录内，含原有修改，未触碰；八项目教学索引中的 octoscode/OctoLoop/hagency 不是要求本项目全部接入的运行依赖。本轮阅读范围列于第7节。

## 3. OctoSense 今天实际拉到了什么

[本次更新比较](<https://github.com/OctoSense-org/OctoSense/compare/c19da8d6e99f10ace310c762abddb1a5523a1a6e...b221f7b4c877dd823d04e4ee510cc74880de5535>)：

- #272：系统助手对话支持选择、复制文本及逐条复制回复。
- #273：通知 toast、glance 卡片和面板关闭行为修复。
- #274：Photos、Maps、YouTube、Camera 增加 Agent 与通知工具，News 增加通知；共享通知卡迁到 Shell。`agents.ask` 等待本人同意并等 peer 就绪，不再立即返回 pending。
- #283：助手面板获得键盘焦点时仍把功能键交给 Shell。
- #284：应用确认面板阻挡的 Shell 退出请求可以到期，避免稍后关闭应用意外退出整个 Shell。

这些是 **10/2 已有 main 提交**，不是“10/3预告更新已完成”。相关代码/说明：
[系统应用 Agent](<https://github.com/OctoSense-org/OctoSense/blob/b221f7b4c877dd823d04e4ee510cc74880de5535/apps/README.zh-CN.md#L314-L363>)、
[agents.ask](<https://github.com/OctoSense-org/OctoSense/blob/b221f7b4c877dd823d04e4ee510cc74880de5535/crates/shell/src/agents.rs#L374-L464>)、
[退出等待](<https://github.com/OctoSense-org/OctoSense/blob/b221f7b4c877dd823d04e4ee510cc74880de5535/crates/shell/src/process_close.rs#L64-L77>)。

检查本次区间的根 Cargo、native-apps、native-runtime、runtime-patches 锁定文件，**无差异**。不能从这些系统应用改动推断 OnCue 的宿主 API 已改变或已实测兼容。

当前参考 OctoSense 的[原生依赖](<https://github.com/OctoSense-org/OctoSense/blob/b221f7b4c877dd823d04e4ee510cc74880de5535/native-apps.json>)锁 Rinx `4b89097d`、App Hub `58c3c8ae`，
[运行时锁](<https://github.com/OctoSense-org/OctoSense/blob/b221f7b4c877dd823d04e4ee510cc74880de5535/native-runtime.lock.json>)选 Octoscript-Makepad `8f103d0c`。
**参考仓库 main、宿主依赖 pin、实际构建源码、实际二进制是四个不同事实。**

本轮检查现有宿主二进制的 SHA-256 仍为：

```text
87ed4dccd14bac51222f40c38d4db086911790786b688a68a503002ada64ba25
```

没有运行构建、安装、重启或换装。更新参考源码不会自动改动 OnCue 独立仓库，也不会自动升级正在运行的二进制；未来若改宿主，应使用独立分支/工作树与固定提交，不强制覆盖本地改动。

## 4. 制作到发布：原文核对后的顺序

主入口已完整阅读：[Design Flow 中文 README](<https://github.com/OctoSense-org/OctoScript-App-Design-Flow/blob/caa5d3648be9289f11056c386a645038af14e5a5/README.zh-CN.md>)。
其明确要求继续读 AGENTS、流程索引、所选 FLOW、QUICKSTART、SCRIPT-API，以及两仓的 PUBLISHING；不是读完首页就停止。

1. 写清需求、数据、每个动作、保存内容、空态和失败态；逐项对应权限。
2. 制作脚本应用包：入口为 `main.splash`，不能把 Rust/Python/外置浏览器控制器当包内应用逻辑。
3. 用未签名开发副本在 card-host 驱动每个交互、空/错误/重启状态；截图须真实且逐张看过。
4. 依赖 Matrix/octos 的功能在 **Rinx** 内另做真实宿主验证；card-host 的 `no service answers` 只证明不可用分支。
5. 定稿说明、图标、截图、权限、版本；stamp/check → scan，七问如实回答，审核包在 bundle 外。
6. 人工确认发布者身份、隐私和平台声明。最终字节由发布者签名，再用公钥检查。
7. 固定公开 commit/tag，提交 `Submit <app id> <version>`，包含包路径、公钥、完整检查输出与七问。
8. 维护者取相同字节重检并发布签名目录。**开 issue ≠ 审核通过 ≠ 上架。** 不改官方 catalog/index/artifacts。

依据：[脚本应用14步](<https://github.com/OctoSense-org/OctoScript-App-Design-Flow/blob/caa5d3648be9289f11056c386a645038af14e5a5/flows/script-app/FLOW.md#L37-L70>)、
[App Hub 正式提交契约](<https://github.com/OctoSense-org/OctoSense-App-Hub/blob/41bc959fc13c44e27fa462df40eb8e300d48ab40/docs/PUBLISHING.md#L651-L743>)。

**签名纠正**：开发未签名副本与签名发布包是不同阶段，不必让用户二选一。
`tools/octo check` 遇已签名包不stamp，仍能转交 `--publisher-key` 检查；真正拒绝本地签名导入的是 card-host/Rinx Developer 的验证边界。
代码：[octo cmd_check](<https://github.com/OctoSense-org/OctoScript-App-Design-Flow/blob/caa5d3648be9289f11056c386a645038af14e5a5/tools/octo#L446-L475>)、
[Rinx 包加载](<https://github.com/hagency-org/Rinx/blob/c515e5fc9b6dc22e67f7d551b09fdd793ec685a1/src/miniapps/package.rs#L89-L104>)。

Rinx 同一实现还拒绝非空 `agent` profile，要求精确 `octos.*` 服务；因此 OnCue 的 `agent: null` **不等于没有运行时助手**，不能为“接 Agent”盲加不受支持的 manifest 字段。

## 5. 初赛、任务核验和权限：纠正三类误读

### 5.1 不能把复赛要求倒灌成初赛强制增功能

[初赛专门条款](<https://github.com/gosimfoundation/hackathon-agenticapp26/blob/a2a3e2efbd6d009180fbb647fc87683fc1f79dc1/docs/competition-schedule.md#L72-L84>)区分：

- 初赛：需求成立、作品能跑；一次操作及可核对结果、失败或空态，加固定版本、启动说明、2–3分钟演示、两截图、来源限制和成员名单。
- 复赛：完整任务自动化及后续状态、正常失败验证、队外试用、完整演示与已知限制。

通用 Agentic 仍重视计划、授权、执行与核验，但“回写原会话”在场景稿中是消息方向及例题，不能推出所有初赛应用必须发送。
[练习包](<https://github.com/gosimfoundation/hackathon-agenticapp26/blob/a2a3e2efbd6d009180fbb647fc87683fc1f79dc1/docs/courses/2026-09-26/workbook.md#L111-L116>)甚至明确：未接通发送时只交付草稿能力。

OnCue 已有[保存并回读逐字比对](<../../oncue/bundle/main.splash#L691-L710>)，所以“完全没有执行与核验”不准确。
初赛应证明 **授权房间取材 → octos假设排练 → 人查看/修改 → 保存草稿 → 回读核对**。
这不等于全部竞赛要求已通过，更不等于已实现聊天发布；不增加未经授权的发送操作。

消息作品仍需来源会话/原消息可追溯、草稿与已发送区分、账号隔离、拒绝/过期反馈；[运行验收条款](<https://github.com/gosimfoundation/hackathon-agenticapp26/blob/a2a3e2efbd6d009180fbb647fc87683fc1f79dc1/docs/app-hub-submission.md#L49-L53>)仍要求接收者独立授权。

### 5.2 45秒、60秒、90秒不能混为一种超时

| 数值 | 对应实现 | 核对结论 |
| --- | --- | --- |
| 90秒 | [OnCue计时器](<../../oncue/bundle/main.splash#L300-L305>) | 应用自己的等待预算，有源码依据；不是官方默认。 |
| 45秒 | [Rinx助手read_room/发送sheet](<https://github.com/hagency-org/Rinx/blob/c515e5fc9b6dc22e67f7d551b09fdd793ec685a1/src/assistant/mod.rs#L339-L426>) | 未答拒绝；不是普通miniapp读取必经的授权面板。 |
| 185秒 | [Rinx miniapp pending](<https://github.com/hagency-org/Rinx/blob/c515e5fc9b6dc22e67f7d551b09fdd793ec685a1/src/miniapps/ui.rs#L637-L645>) | 宿主兜底总等待，与应用层独立。 |
| 3600秒 | [Rinx实例lease](<https://github.com/hagency-org/Rinx/blob/c515e5fc9b6dc22e67f7d551b09fdd793ec685a1/src/miniapps/ui.rs#L367-L377>) | 授权有效期，不是服务耗时。 |
| 默认60秒 | [App Hub HostService契约](<https://github.com/OctoSense-org/OctoSense-App-Hub/blob/41bc959fc13c44e27fa462df40eb8e300d48ab40/docs/PUBLISHING.md#L602-L614>) | 可由服务覆盖，不能替代Rinx独立实现；Matrix SDK HTTP请求另有默认超时。 |

OnCue 经 Rinx Review/Run 获账号与房间lease，再由[miniapp dispatch](<https://github.com/hagency-org/Rinx/blob/c515e5fc9b6dc22e67f7d551b09fdd793ec685a1/src/miniapps/ui.rs#L481-L505>)调用 Matrix，不经过助手read_room sheet。
本节是源码核对，不是重新计时实测。无绑定房间错误也不能等同于跨已授权房间拒绝、租约撤销、迟回调已经全部验证。

### 5.3 最新功能不能从旧指南或字段存在推定

- `model`、`glance` 在普通 Shell 的支持不自动表示 Rinx miniapp 也提供。
- `tools.json`/`AGENT.md`/skills/triggers 被 gate 接纳，不等于每个宿主会执行；OnCue 不应为初赛依赖规划中功能。
- 旧课程里的独立原生天气应用、网页路径和旧 L0 限制不能覆盖最新“初赛OctoScript”的通知。
- 官方工具链的验证平台声明与我们 Linux aarch64 的实测是不同口径，不虚报 macOS/手机验证。

## 6. OnCue 当前状态与实际检查

版本状态保持三层：

| 位置 | 状态 |
| --- | --- |
| 本地/远端main | `bd7b94c3df21df74a9aa0e61d4fa5f58dbe04207`，包0.4.5 |
| 唯一tag及App Hub #57 | `v0.4.4`，指向 `fa02affd9be31d107e8b47c18ecff843b86d9203`，旧解析缺陷包 |
| 未提交工作区 | 0.4.6，三个包文件改动，约+192/-172；布局/解析/回调隔离尚未在本轮端到端验证 |

本次会话的当前包只读命令与输出：

```sh
. /root/hackthon/refs/octo-env.sh
"$OCTO_HUB" check /root/hackthon/OnCue/oncue/bundle --publisher-key oncue.dev=50578fd7e0d8ac51a1e9e590835427ce8e71f46dba491860c75ae4e7c8c78042
```

```text
oncue-screening-room 0.4.6 — REFUSED
  [refused] publisher-signature: the signature from key "oncue.dev" does not match the manifest
  grants: capabilities {"matrix.read_messages", "matrix.room_info", "octos.session.open", "octos.turn.interrupt", "octos.turn.start", "storage"}, hosts {}, storage 4194304 bytes, agent none
hub: the bundle was refused
```

退出码1；版本/摘要已改，签名旧值未同步。未重签。不能把历史PASSED当当前结果。
本次还运行官方 `tools/octo doctor` 和 `package-help`（均exit0）：Python、Hub、card-host、cargo、模板均 `[ok]`，诊断尾行为：

```text
ready: tools/octo new <dir> && tools/octo run <dir>/bundle
```

工具可发现不代表新宿主或0.4.6功能验收通过。另一本地 Python 摘要脚本因缺少 `blake3` 退出1；未为本轮阅读任务安装依赖。

[参赛主题#5](<https://github.com/gosimfoundation/hackathon-agenticapp26/issues/5#issuecomment-5852553339>)和[初赛仓库#13](<https://github.com/gosimfoundation/hackathon-agenticapp26/issues/13#issuecomment-5925966622>)均已只读核实。
#13 **已填MiniMax团队ID**，不再要求用户重复提供；尚未钉住冻结tag/commit。
[App Hub #57](<https://github.com/OctoSense-org/OctoSense-App-Hub/issues/57>)为OPEN、无评论；同步下来的[官方目录](<https://github.com/OctoSense-org/OctoSense-App-Hub/blob/41bc959fc13c44e27fa462df40eb8e300d48ab40/catalog.json>)为空，无OnCue发布条目。

已有[演示视频](<../demo/oncue-demo-2min59.mp4>)实际179.334秒、1440×1000、H.264、1623908字节。
[演示说明](<../submission/DEMO-2MIN.md#L95-L121>)诚实列出未包含失败态/接收者授权、无旁白字幕；不要称全部演示覆盖完成。

### 下一步工作顺序（本轮未执行）

1. 验证当前0.4.6基本交互、可读性、解析边界、草稿存取和失败态，不新增复杂功能。
2. 在现有Rinx宿主证明真实octos回合、用户查看、保存与回读，补当前版权限/停止/迟回调证据。
3. 对齐需求、隐私、依赖、验证摘要、七问与视频/截图，固定候选字节。
4. 到人工检查点后确认签名、公开commit/tag、App Hub修复版申请及#13冻结版补充。
5. 明日上游有新提交时先读差异、核对pin，再决定是否值得升级；不因预告暂停 OnCue 脚本包本身的开发。

## 7. 实际阅读清单与未覆盖范围

以下是本轮主线程与两个只读子审计的合并范围；子审计没有写文件。**“完整”指列出的文件从头到尾读取，不指仓库所有代码。**

### 主线程完整阅读

```text
OctoScript-App-Design-Flow @ caa5d364:
  README.zh-CN.md (453行), AGENTS.md (125)
  flows/README.zh-CN.md (75), flows/script-app/FLOW.md (70)
  docs/QUICKSTART.md (384), docs/SCRIPT-API.md (358)
  docs/CAPABILITIES.md (98), docs/HOST-SERVICES.md (184)
  docs/PUBLISHING.md (401), docs/NATIVE-WORKSPACE.md (40)
  docs/GLOSSARY.md (40), docs/AI-SERVICES.zh-CN.md (1144)
OctoSense-App-Hub @ 41bc959f:
  README.zh-CN.md (70), docs/FIRST-APP.md (228)
  docs/PUBLISHING.md (769), docs/DEVELOPMENT.zh-CN.md (94)
  docs/ICONS.md (95), catalog.json (11)
OctoSense @ b221f7b4:
  AGENTS.md (51), apps/AGENTS.md (107), apps/README.zh-CN.md (496)
  native-apps.json (116), native-runtime.lock.json (5)
```

主线程针对性读实现：App Hub gate的主检查函数（1–278），octo的cmd_check与发布清单（425–514）；Rinx包加载89–104及上下文、Review/Run、dispatch、pending185秒分支，助手read_room/answer/expire分支；OnCue计时器、助手请求/解析、草稿写入回读及当前diff。另读OctoSense新增提交日志和相关diff，并确认锁定文件没有变化。

### 赛事子审计完整阅读（a2a3e2ef）

```text
AGENTS.md; README.md
 docs/index.md; docs/SUMMARY.md
 docs/rinx-guide.md; docs/rinx-miniapps.md; docs/app-hub-submission.md
 docs/competition-schedule.md; docs/curriculum.md; docs/octosense-scenario-update-plan.md
 docs/courses/2026-09-26/README.md; lesson-01.md; lesson-02.md; workbook.md
 docs/courses/2026-09-26/demo-runbook.md; integration-and-sources.md
 docs/demo/2026-09-26/README.md; projects.md; process.md
 docs/demo/2026-09-26/octosense-octos.md; octoscript-pipeline.md; octo-weather-guardian.md
 src/components/AwardEvaluation.vue; AppHubSubmission.vue; ApplicationScenarios.vue; EventSchedule.vue
```

部分：赛事App.vue工具输出有超长行截断，不列全文已读。主线程另外完整读赛程、App Hub提交指南及Rinx注册指南，并复核草稿能力与消息场景条款。

### 运行机制子审计

完整阅读三仓英文根README，Rinx关键ADR0005/0006/0007/0008及小程序示例、部署/应用指南；中文README与OctoSense AI指南同时核对日期和状态。Octoscript中文README第273行太长被工具截断，**不声称全文逐字读完**。针对性代码核对Rinx包加载/目录/租约/授权/Matrix与Octos dispatch、助手读房sheet与超时，以及OctoSense ai-host、app-peers、系统应用注册和pin；终检读取OctoSense更新相关diff。

未覆盖：各仓全部实现与测试、所有历史文档、Rinx lab、所有传递依赖源码。英文AI-SERVICES未再次完整逐字复读（完整读了中文1144行版本）。没有跑Rust测试、编译、新宿主、0.4.6端到端、手机或完整签名目录安装。本记录不宣称官方批准或比赛通过。
