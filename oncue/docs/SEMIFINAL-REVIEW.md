# OnCue 复赛比较与实现说明

研究日期：2026-10-08。比较基线为0.4.8；功能审阅分支为 `feat/semifinal-rehearsal-workspace`，版本0.5.0。当前实现与验证范围分别见[产品说明](../BRIEF.md)和[验证记录](../VERIFICATION.md)。

## 1. 比较范围与评审时间

读取[报名 issue #13](https://github.com/gosimfoundation/hackathon-agenticapp26/issues/13)的49条评论，去重43支队伍、44个仓库；除OnCue外43仓库均下载并固定提交SHA，LiYu前后端同队。TIANYI仅标题，无法分析代码；DocGenie当前自述退出，保留为学习样本。

比较的是各仓库当前默认分支，不是初赛排名或冻结版本复审。D为文档、S为已读源码、R为仓库保存的运行记录；没有执行竞品代码或调用其真实服务。代码疑点如无特别说明均为静态推断，媒体未下载不作为项目缺陷。

复赛工作按 **10月13日23:59提交、10月14日评审** 安排。目标是可复现的完整用户任务，而非页面、Agent或代码数量。

## 2. 保留长处，弥补持续使用的不足

保留私人排练、不发送、程序取回原文、90秒总期限、一次修复、旧回调失效和保存回读。0.4.8已有真实Rinx/模型历史记录，但不能代替新版验证。

本次主要补齐：明确表达目标、直接比较三句、同一草稿继续修订、前后及A/B对照、按房间持久化、旧稿迁移与删除。引用与数字规则继续有限，不能升级成语义正确性保证。

## 3. 最值得学的八组具体设计

下表不是总排名。每项优势只覆盖列出的机制；不推导整体更可靠。

| 项目与已读实现 | 值得学什么 | 当前边界／不应照搬 |
|---|---|---|
| **CFAW News**：[引用校验](https://github.com/zhiguang127/cfaw-news-agent/blob/76121d75e6df/src/agent/results/insights.splash#L32-L47)、[改期确认](https://github.com/zhiguang127/cfaw-news-agent/blob/76121d75e6df/src/app/reschedule.splash#L31-L58)、[操作日志](https://github.com/zhiguang127/cfaw-news-agent/blob/76121d75e6df/src/data/storage/schedule_actions.splash#L27-L63) | 同一目标的证据快照、决定历史、新证据后重审；确认对象和版本；应用、核验、撤回分开。 | 应用内日程不是系统日历；逐字引用不证明语义支持。已读实时前后基准记录 failed、completed 为空，不能宣称基准提升已证实。 |
| **DailyFlow**：[只读查询路由](https://github.com/KumaYuriPool/DailyFlow/blob/423554ba8269/src/35_query_router.splash#L1-L44) | 模型只选择最多两项受控查询，代码从完整源记录算结果；来源带 record_id/revision，后续更正仍是同一对象。 | 当前是单 App 的内部模块，非跨 App 平台；部分明确意图会自动写记录，不适合直接替代 OnCue 的私人编辑确认。 |
| **BuWei**：[事实 ID 生成](https://github.com/WeiR-h/buwei/blob/baeb57d74b3f/native/src/community_model.rs#L146-L199)、[精确确认记录](https://github.com/WeiR-h/buwei/blob/baeb57d74b3f/native/crates/action-receipts/src/lib.rs#L294-L428) | 模型选择事实、代码渲染；确认绑定账号、动作、内容摘要、revision 和期限；不确定执行只查询，不盲目重发。 | Windows 原生宿主与真实多用户执行比 OnCue 大得多。本次只读代码，不宣称完整线上流程复现。OnCue 只借鉴本地草稿身份/版本，不复制发送框架。 |
| **Loom**：[完整计划回读核验](https://github.com/dyingforge/loom/blob/50be66fa145e/server/runtime/reconcile.py#L17-L58) | 候选与正式状态分离；完整保存结果必须等于获准变更，失败保留原计划；自然语言调整持续作用于同一任务。 | 自有日历加 Python 服务；后台任务内存化、缺取消和请求去重。无需为了增加闭环给 OnCue 加后端。 |
| **Writing Studio**：[提案审阅与应用](https://github.com/hhyyzz-enda/bluemsun-2026AgentticApp/blob/eb9bdd2f010f/apps/writing-studio-hub/bundle/main.splash#L640-L822) | 原文、可编辑提案、差异摘要、单独确认、作用对象。适合借鉴为三路线速览和 A/B 对照。 | 引用保护只认脚注标记；原生与脚本部分保存/回填/撤销链路有缺口。不能把审阅界面存在等价为全流程可靠；保留 OnCue 的事实/假设区分，不复制发布。 |
| **Invoice-Reconciliation**：[逐条事实绑定](https://github.com/BUNotesAI/Invoice-Reconciliation/blob/17d8198fc228/bot/src/validate.rs#L241-L325) | 数字按每一项允许的 fact_refs 比较，而非从整批材料随便借一个数；候选事实经人确认后才升级。 | 财务领域有明确金额/日期类型，不能原样套自由聊天。其[限制](https://github.com/BUNotesAI/Invoice-Reconciliation/blob/17d8198fc228/docs/limitations.md#L5-L32)说明真实模型尚未在 Rinx 完整走全流程。 |
| **TraceShop／牵线**：[TraceShop](https://github.com/prettygirlisnotme/TraceShop/blob/f07434ff12dd/bundle/main.splash#L264-L440)、[牵线](https://github.com/kkkkikun/qianxian-guardian/blob/db07c982ddc6/app/qianxian/bundle/main.splash#L1107-L1307) | TraceShop 借鉴候选→提案→采纳→确认→读回；牵线借鉴多条记录、筛选、定向取消/撤销。两者能力分别比较，不合并成共同功能。 | TraceShop 研究后改输入再选旧候选的绑定存在缺口；牵线取消不是删除，部分“读回一致”只有 write。OnCue 应学不变量，不照抄实现。 |
| **情境 DJ／City Matchmaker**：[人工优先](https://github.com/peterdlick-stack/agentic-app/blob/9919c0fca967/bundle/main.splash#L933-L1011)、[浏览与偏好分开](https://github.com/SuperLeilei2026/city-matchmaker/blob/fcc9fe2eaca6/core/discovery.mjs#L58-L97) | 允许人纠正系统理解；只问能区分当前选项的一问；浏览或保存不自动等于长期偏好。 | DJ 去听只打开搜索页，不能写成已播放；城市项目模型路径尚无真实闭环证据。OnCue 不应猜用户性格或群友心理。 |

其他样本的启发：晨报卡有真实有界工具循环和提示词版本留痕，但关键词“同意”会误收“不同意”；Pantry Steward 区分“生成、接受、实际消耗”；邮件承诺观察器为每次会话单独授权云分析；导航样本记录了模型总结与路线事实冲突，说明工具调用成功仍可能任务失败。共同教训是：**清楚定义对象、状态和证据，比多写几个 Agent 角色更重要。**

## 4. 已落实到0.5.0的设计

| 借鉴 | OnCue实现 | 保留的边界 |
|---|---|---|
| Writing Studio的候选审阅 | 三建议速览；原稿/当前及A/B对照；修订先暂存再应用 | 不自动改稿、不代发；不是逐字彩色diff |
| CFAW/DailyFlow的持续对象 | 房间主稿/A/B，保存目标、台词、引用编号、局部快照标记和文本版本 | 不落盘整批原文；快照标记不是内容哈希或跨会话变更检测 |
| BuWei/Invoice的依据分层 | 代码取原文，逐路线声明依据，数字/单位只在相应依据和用户提议中比较 | 字面检查非语义证明，不推断他人同意 |
| Loom/TraceShop的候选与正式状态 | 修订绑定原稿实际文本、目标、来源和版本；一次应用，保存独立 | 没有后台执行、外部事务或新后端 |
| 情境DJ/城市匹配的人控制理解 | 澄清/拒绝/推动下一步目标、明确补充条件 | 选句或保存不成为长期人格/偏好推断 |

### 模型协议

生成G2保留完整七节，允许拒绝陈述句，每路线明确来源。修订R1为依据、建议、改动说明三节。修改输入、来源、原稿、要求或停止后，旧结果失效。候选通过有限规则后仍需人核对；手工编辑不继承检查状态。

### 存储与删除

使用固定文件中的规范数组结构，不把房间ID拼接为路径。最多10个房间记录（含样例）、每稿8000字节、文件512 KiB。校验字段、完整规范JSON、写入返回和逐字回读。损坏或不确定状态停写，保留编辑；不自动恢复空记录或伪称原子事务，只支持一个写入窗口。

旧版主稿/A/B手动复制，旧文件与新房间记录分别确认删除。删除前使在途工作失效，失败保留编辑并继续视为未安全保存，不因旧缓存相同而允许无提示丢弃。

### 数据授权

房间读取与模型许可分开。模型许可在当前房间/勾选范围的打开实例内持续有效，每次点击发送当时输入；改变范围或撤回后须重新允许。请求省略发送者标签，正文仍可能识别人。宿主可能保留历史或提供工具；不把session.open、停止或本地删除称为清空模型历史。

## 5. 验证与后续审阅重点

生产函数在真实VM执行，模型/房间返回值受控注入；工具单测、VM、原生界面操作、真实模型质量分开报告。详细版本、哈希和实际结果集中在[验证记录](../VERIFICATION.md)，不拼接不同版本成功片段。

审阅重点是用户能否更快选择、修改并继续使用草稿。后续价值比较采用三个场景：时间/预算冲突、礼貌拒绝、催办澄清；与同模型直接问答成对比较，记录首次可用时间、修改量、错误承诺和实际选择。没有完成用户试用，不宣称证明产品价值。

本次不扩发送、日历、交易、跨账号记忆或持续监听，不为展示增加多Agent或迁移宿主。上游运行时问题可独立整理最小复现，不作为OnCue已解决的宿主能力宣传。
