# 参赛要求核对与当前进度（2026-10-02）

> 依据（当日拉取上游原文）：`OctoScript-App-Design-Flow/README.zh-CN.md` + `docs/PUBLISHING.md`（401 行）、
> `OctoSense-App-Hub/docs/PUBLISHING.md`（769 行，权威发布契约）、
> `hackathon-agenticapp26/docs/app-hub-submission.md`、`docs/competition-schedule.md`、`docs/rinx-miniapps.md`。

## 0. 最重要的一条：时间

| 节点 | 时间（北京时间） |
| --- | --- |
| **初赛提交截止 / 版本冻结** | **10/4（日）23:59** ← **今天 10/2，还有 2 天** |
| 初赛评审 | 10/5–10/6 18:00 |
| 公布 50 人晋级 | 10/6 20:00 |
| 复赛提交 | 10/9 23:59 |
| 线上决赛答辩 + 评奖 | 10/12 |

初赛提交内容（赛程原文）：**提交需求、可运行原型、源码、截图、演示与已报名成员名单**；
10/4 截止并**冻结初赛版本**，评审只使用冻结版本。

## 1. 作品形态（已定）

- 赛道：**OctoSense 即时消息 · Rinx**。
- 形态：**OctoScript 小程序 / Hub 卡片包**，在 OctoSense / Rinx 宿主内运行，经 **App Hub** 发布。
- 张老师明确：「初赛代码只要求 octoscript 的应用」「appcard 必须通过 App Hub 发布」。
- 官方 `rinx-miniapps.md` 确认：`matrix.*` 仅由 **Rinx mini-app 宿主**提供；`octos.*` 由 Rinx 或托管内核的 shell 提供。
  ⇒ 本作品的运行宿主必须是 **Rinx**，不是 `card-host`。

## 2. 官方发布流程（`docs/PUBLISHING.md` §3 + §6 checklist）逐项对照

| # | 官方要求 | 我们的现状 | 状态 |
| --- | --- | --- | --- |
| 1 | manifest：id 定稿、版本 NEW、能力最小、声明所有 host | `id=oncue-screening-room`、`version=0.4.4`、6 项能力各有可见用途、`network.hosts=[]` | **已有** |
| 2 | listing：无占位文本；category/platforms/age_rating 合法；隐私 URL 为 https 且真实 | `productivity` / `["linux"]` / `all` / `https://github.com/codezzzsleep/OnCue/blob/main/oncue/PRIVACY.md`（仓库公开可达） | **已有**（需 HUMAN 最终确认 URL 可用） |
| 3 | 图标在 listing 指定的路径、小尺寸可辨 | `assets/icon.svg`（listing 指向它，存在） | **已有** |
| 4 | 用真实宿主运行并逐项驱动交互（点击/输入）并观察效果 | 已实测：28/28 控件可达、逐句播放 7 项、双视口分页、字素边界 15 类 | **已有**（card-host 侧；宿主侧见第 6 节） |
| 5 | 真实截图，逐张看过，并列在 listing 里 | `screenshots/01-native-rinx.png`（当前 0.4.4 实拍）；README 另有双视口与装载流程截图 | **已有**（listing 只列 1 张，可加） |
| 6 | `hub check` → PASSED（未签名阶段只剩未签名警告） | 未签名阶段曾 PASSED；**现已签名**，改用 `hub check --publisher-key oncue.dev=50578fd7…` → **PASSED** | **已有** |
| 7 | `hub scan` 生成审核包，并**书面回答七问** | 七问已书面回答（`evidence/apphub/hub-scan-answers-0.4.4.md`）；审核包本身未留档 | **部分**（把 packet 也入库） |
| 8 | `hub check --allow-unsigned --catalog <App Hub catalog>` → 无版本/连续性拒绝 | 因发布者密钥尚未在 hub 登记，`--catalog` 检查被 `publisher-signature` 拒绝 | **待发布后**（属发布方流程，非作品缺陷） |
| 9 | 仓库里只应有 bundle 与源码；**不得有密钥、`.local-state`、`build/`** | 仓库 33 个文件，已清理；密钥在仓库外（`/srv/oncue-runtime/dev/keys/`） | **已有** |
| 10 | **HUMAN**：`hub sign-manifest` + `hub check --publisher-key` → PASSED | 已完成（key_id `oncue.dev`，公钥与 catalog 登记一致） | **已有** |
| 11 | **HUMAN**：打 tag + 在 `OctoSense-App-Hub/issues` 开 `Submit <id> <version>` | tag `v0.4.4` 已打并推送；**issue 未开**（本机无 GitHub token） | **未完成** |

## 3. 提交材料（`app-hub-submission.md` 的 6 项）逐项对照

| # | 官方要求 | 我们的现状 | 状态 |
| --- | --- | --- | --- |
| 1 | 公开源码仓库、固定提交号/发布版本、**Apache-2.0** | 仓库公开；tag `v0.4.4` → 最终提交；`oncue/LICENSE` = Apache-2.0 | **已有** |
| 2 | 应用目标、适用场景、图标、运行截图、作者与支持方式 | `oncue/PRODUCT.md`、`assets/icon.svg`、README 截图、listing 的 publisher/support | **已有** |
| 3 | 宿主版本、支持平台、依赖与启动说明 | `oncue/docs/DEPENDENCIES.md`（官方 Rinx `c515e5fc9b6d`、linux/aarch64、装载步骤） | **已有** |
| 4 | 数据来源、权限、隐私、授权/拒绝/失败行为 | `oncue/PRIVACY.md` + 六项能力逐项用途 + 失败状态反馈 | **已有** |
| 5 | **Agent 任务演示**：输入、Agent 步骤、如何核验、哪些需人工确认 | 有真实七块回合的设计与 card-host 侧验证；**宿主内当前包的可视证据缺**（见下） | **部分** |
| 6 | 运行截图/日志/视频 + 复现步骤；演示材料不能代替可运行作品 | 截图与复现步骤齐；**无视频**（可选） | **部分** |

## 4. 官方明确要求的「接收者独立授权」——我们还没做

> 聊天或账号相关作品**还需演示「接收者独立授权」**，避免把发送者身份或权限带给接收者。

Rinx 基线同样把它列为核心机制（每次打开须授权、关联账号与会话、关闭即撤销、接收者用自己的账号与草稿）。
**我们在这一项上没有任何证据。** 需要两个账号：发送者分享卡片 → 接收者打开并独立授权 → 拿到自己的授权与草稿、不继承发送者权限。
注：OnCue **不分享、不发送**，材料中必须写清"未发送排练"与授权边界。

## 5. 仓库与产物现状

```
仓库 HEAD = a0814a0    tag v0.4.4 -> a0814a0    跟踪文件 33 个 / 1.4M
包 0.4.4  digest 2b01ae050c6110a4921303ec18ca07949e1ffd6083db0fd77431a577f182111a
已签名（oncue.dev）；hub check --publisher-key -> PASSED
宿主 :99 运行中，pid 150001，exe sha256 87ed4dcc…（官方 Rinx c515e5fc 构建，零本地补丁）
```

## 6. 尚未完成（按优先级）

1. **开 Submit issue**（唯一挡住"正式提交"的一步）——需要 GitHub token，或由人手动粘贴已备好的正文。
2. **宿主内当前包的可视证据**：room 12 条 / 七块回合 / 停止·90 秒 —— 受 Rinx 内嵌视图裁切所限未取得。
3. **接收者独立授权演示**（官方硬要求，我们完全没有）。
4. `hub scan` 的 packet 入库；`tools/octo` 获取（官方 checklist 用它，功能与我们用的 `hub check`/`card-host` 等价）。
5. listing 里的截图可从 1 张增加到多张。
6. （可选）运行视频。

## 7. 我们**已经比初赛要求做得多**的部分

初赛要求「不要太复杂，能传达基本功能即可」，而我们已经做到：
双视口逐页像素核对、字素边界保护（15 类边界 0 处切断）、逐句播放状态机 7 项、
28/28 控件可达、拼接逐字符逐字节无损、真实房间 12 条与七块回合的 card-host 侧验证、
以及用**官方 Rinx（零补丁）**复现的完整装载流程。

---

## 8. 深读后新增的发现（2026-10-02 第二次通读）

| 项 | 内容 | 影响 |
| --- | --- | --- |
| 提交入口 | `app-hub-submission.md`：**"截至 2026-09-21，Rinx 的通用目录与包安装尚未接通，自动提交入口仍在建设。现阶段各轮评审以公开源码仓库和可运行作品为准，无需等待 Hub 上架。"** | **比赛提交 ≠ App Hub 提交**；没有正式门户，评审看公开仓库 + 可运行作品 |
| 初赛材料 | `curriculum.md:92`：需求、可运行最小原型及启动说明、源码或包、**2–3 分钟演示**、**两张关键截图**、数据来源与限制；**至少展示一次操作、可核对的结果、一个失败或空状态** | 我们**缺**演示材料与第二张关键截图 |
| 运行验收 | `app-hub-submission.md`：**启动 / 真实输入 / 必要授权 / Agent 执行 / 结果核验 / 失败处理** + 聊天类**接收者独立授权** | "结果核验"是明确验收项；本应用当前不产生"结果" |
| 证据规则 | 同上：**"Agent 辅助开发、通过包预检、成功上架或累计 PR 数量，均不能单独替代作品效果证据。"** | 只能靠运行效果举证 |
| 交付形态 | 按作品形态交付表：我们属 **Hub 卡片包** —— 需附**预检结果及实际运行证据** | 预检结果我们有；运行证据需在 Rinx 中 |
| 平台 | `README.zh-CN.md`：**已验证平台仅 Apple silicon macOS；Windows 与 Linux 未验证** | 我们跑在 Linux aarch64，属**未验证平台**，须如实标注 |
| 签名与截图 | `README.zh-CN.md` / `FIRST-APP.md`：**`card-host` 拒绝已签名 manifest（即使 `--allow-unsigned`）；请在签名之前截图** | 回访已签名版本必须另做未签名副本 |
| gate 完整规则 | `docs/PUBLISHING.md §2` 的 11 项检查（identity/digest/publisher-signature/contents/size/assets/secrets/listing/policy/version/continuity）与字段限额 | 已逐条核对本包，**全部通过** |
| App Hub 基准 | 赛事引用核查版本 `97c2a1fd9aa49a6b87586f228e070e0c16b1067b` | 与本地构建版本不同，结论须标注版本 |
