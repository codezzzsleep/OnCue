# SUBMISSION-CHECKLIST — PUBLISHING §3.8 逐项对照（S3）

> **当前纠正，优先于下方起草时快照**：`6681bd2`已恢复精确签名包，资源摘要错误不再是当前阻断；公开main读取、push和只读摘要检查已有证据。0.4.2仍因全文裁切未被接受，全文查看修复正在执行，不是等待HUMAN决定是否修。push、tag、SHA及文档/检查整理属于用户已授权的开发交付工作，AI继续完成；外部Submit保持草稿，发布者身份/密钥最终确认另行处理。旧profile报错是历史观察，不能代替当前回合诊断。正式材料须替换为最终版本的同一工件、截图与检查结果；不得直接使用本快照的0.4.2标题与待办状态。

- 起草时间：2026-10-01T22:06–22:15+08:00；依据官方 `docs/PUBLISHING.md`（OctoScript App Design Flow）§3.8，其权威为 App Hub `docs/PUBLISHING.md` "Submitting"（截至 `79a2c4f`）
- 状态图例：**已有** = 本仓库/本机已有可核验证据；**待 HUMAN** = 只能由人做（密钥/账号/法律声明/打 tag/开 issue）；**待补** = 需要新的执行或改写（不含 HUMAN 专属动作）
- 配套草稿：`build/SUBMISSION.md`（issue 正文）
- 本文件不含密码/token/私钥

---

## A. §3.8 官方条目逐项

| # | §3.8 要求 | 本仓库证据 / 现状 | 状态 |
|---|---|---|---|
| A1 | ①把最终（已签名）`bundle/` 提交到公开仓库 | 签名工件已提交：`79a018e3625a54ef81b8dfeedcfa17d82f7d472f`，`git status -- oncue/bundle` 干净，HEAD 的 `oncue/bundle` 与该提交的签名字节**在 `241a7f5` 之前**一致；但本工作区**从未 `git push`**，公开性未核实（本容器外网超时） | **待 HUMAN**（push + 确认公开 URL；且见 B1，HEAD 字节需先重签） |
| A2 | ①给该提交打 tag（例如 `v0.4.2`） | `git tag -l` = **0 个** | **待 HUMAN** |
| A3 | ②在 OctoSense-org/OctoSense-App-Hub 开 issue，标题 `Submit <app id> <version>` | 0 个 issue；草稿正文见 `build/SUBMISSION.md` §0 | **待 HUMAN** |
| A4 | ②issue 内容：仓库 URL | `https://github.com/codezzzsleep/OnCue`（HTTPS 形式，与本地 mirror catalog 0.4.2 条目 `--repo` 一致）；本机 remote 实为 `git@github-dev:codezzzsleep/OnCue.git`，公开可达性未核实 | **待 HUMAN**（确认公开可达；文案已有） |
| A5 | ②issue 内容：tag 与完整 commit SHA | tag 无；签名后 SHA = `79a018e…`（草稿 §2 已写明"待 HUMAN 填"，未假装已有 tag） | **待 HUMAN** |
| A6 | ②issue 内容：bundle 在仓库中的路径 | `oncue/bundle`（5 个文件：`manifest.json`/`listing.json`/`main.splash`/`assets/icon.svg`/`screenshots/01-native-rinx.png`） | **已有** |
| A7 | ②issue 内容：应用 id 与版本 | `oncue-screening-room` / `0.4.2`（`manifest.json`；最新冻结版本，结论 `evidence/native/042-freeze.md`） | **已有** |
| A8 | ②issue 内容：发布者 id 与公钥（`hub pubkey`），或首次提交写 "unsigned" | id = `oncue.local`；取法 `$OCTO_HUB pubkey /root/oncue-runtime/state/hub-keys/working.key`（草稿 §3）；指纹 `98ecd01e0256723b` / sha256(working.pub)=`4f798d48…41b4ec`；**完整 64 位公钥串未贴**（按约束只给取法与指纹），需人粘贴；unsigned 选项已在草稿写明 | **待 HUMAN**（粘贴公钥，或明确选 unsigned / 换属主密钥） |
| A9 | ②issue 内容：该提交上**完整 `hub check` 输出**（签名时带 `--publisher-key`） | 完整输出在 `evidence/native/042-freeze-transcript.txt` 步骤 3（不带 catalog）与步骤 5（带 catalog）；S3 于 2026-10-01T22:06:12+08:00 在 `79a018e` 字节上重跑复现同样 `PASSED`（`build/SUBMISSION.md` §4.3） | **已有**（但需对应最终 tag 的提交重取，见 B1） |
| A10 | ②issue 内容：`hub scan` 七问答案 | 审阅包 `evidence/native/042-hub-scan.packet.json`（0.4.2 签名字节，`route: pass`，7 条 reasons）；七问答案 `evidence/hub-review-answers.md`（Q1–Q7 全文）；复发记录见 transcript 步骤 6 | **待补**（Q1 里"draft save/restore … still pending"已过期，需刷新——`042-freeze.md` §7.5；刷新后七问即"已有"） |
| A11 | "Useful to add"：实际测过的平台与交互、未测的部分 | 平台与交互实测/未测清单已成文：`build/SUBMISSION.md` §6；底层证据 `042-layout-fix.md`、`042-clicktest-412.log`、`042-clicktest-990.log`、`042-layout-geometry.json`、`041-playback-and-values.md`、`storage-quota-040.md`、`042-unavailable-cardhost.png`、`042-cardhost-unavailable.log`、`042-ai1-review.md`、`RUNBOOK-step10-11.md`、`RUNBOOK-provider-profile.md`、`COMPLIANCE-official.md` | **已有** |
| A12 | "An agent may draft its text … never claims a submission was made" | 草稿 `build/SUBMISSION.md` §0/§7 明确"本文件只是草稿，Agent 不代发、不声称已提交/已审核/已批准"；本仓库 0 tag / 0 issue | **已有** |

---

## B. S3 新发现的阻断项（草稿期间实测，需主进程/HUMAN 处理）

| # | 事项 | 证据 | 状态 |
|---|---|---|---|
| B1 | **HEAD 的 bundle 字节现在过不了 `hub check`**：`241a7f5` 在签名之后改了 `listing.json` 的 `release_notes`（"不会自动降级"的如实表述），未重走 stamp/sign。`hub check oncue/bundle` → `REFUSED [refused] digest: the bundle hashes to c78d9808…, the manifest claims 082844db…` | 2026-10-01T22:06:12+08:00 实测（`build/SUBMISSION.md` §4.3）；commit `241a7f5`；规则见 PUBLISHING §3.7 "Restamp rule" | **待补**（决定采用 HEAD 文案则 stamp→sign→check→重新提交，tag/SHA 全部换成新提交；否则还原 listing 再提交） |
| B2 | **当前候选未被 AI1 接受为最终交付**：两视口实图仍有裁切（原消息/虚构回应/建议台词不可完整阅读，本构建 `ScrollYView` 不滚动），双视口 16/16 只覆盖可点击性与状态回读 | `evidence/native/042-ai1-review.md`、`2df4a47`、`f70d993`、`042-layout-fix.md` §6 | **待 HUMAN**（决定是否先做全文视图/分页修订 → 新版本 + 新截图 + 重走冻结链） |
| B3 | 真实宿主回合无证据：`matrix.*` 房间读取与 `octos.*` 模型回合均未在提供服务的宿主上成功，硬阻塞 `profile_unresolved`（内核无 profiles，需宿主 AI providers GUI 走 `llm.sheet.submit`） | `evidence/RUNBOOK-step10-11.md` §0.4、`RUNBOOK-provider-profile.md`、`COMPLIANCE-official.md` M2/M3 | **待补**（且**无法用现有证据满足**：仓库内不存在任何一次成功的原生宿主回合证据） |
| B4 | `listing.json` 的 `privacy_policy_url` / `support` 指向 `https://github.com/codezzzsleep/OnCue/...`：公开存在性与文本归属需发布者确认（§3.2 HUMAN）；本容器外网不可达，未核实 | `oncue/bundle/listing.json`、`COMPLIANCE-official.md` 表 13 | **待 HUMAN** |
| B5 | 参赛作品是否等于 App Hub 正式提交，需向主办方确认 | `COMPLIANCE-official.md` M8（README §黑客松） | **待 HUMAN** |
| B6 | 发布者密钥是本机工作钥 `oncue.local`（本地一次性锚点，无外部 CA），非 §3.6"由应用所有者创建并保管"的 publisher key；换 key 会牵动 anchor/重签/重发布，且上目录后每次更新必须沿用同一 key（`continuity`） | `evidence/hub-review-answers.md` Q7、`COMPLIANCE-official.md` §0/M8、`042-freeze.md` §7.3 | **待 HUMAN** |
| B7 | mirror 里已含 0.4.2（sequence 8）。这只是 PUBLISHING §4 本地演练产物；若 HUMAN 要走正式链，需确认 mirror 是否维持/回滚（备份 `/tmp/oncue-042-backup/hub-mirror-pre042`，易失） | `042-freeze.md` §6/§7.6 | **待 HUMAN** |
| B8 | `build/` 目录（本文件与 `SUBMISSION.md` 所在）在 `.gitignore` 中没有条目；§6 checklist 要求"no build/ committed"，主进程统一提交时请注意别把它带进提交 | `git ls-files | grep ^build/` = 0；`.gitignore` 现状 | **待补**（一行 `.gitignore` 或提交时排除） |

---

## C. 生成 A4–A10 所需的上游门禁项（§3.1–3.7 现状，供 HUMAN 复核）

| # | 上游要求 | 现状与证据 | 状态 |
|---|---|---|---|
| C1 | §3.1 manifest：id 定稿、版本 NEW、capabilities 最小、每个 host 声明 | `id=oncue-screening-room`、`version=0.4.2`（新于目录内 0.4.1）、6 项能力逐项有可见用途（Q3）、`network.hosts: []` 且 `main.splash` 无任何 URL（grep 实证） | **已有** |
| C2 | §3.2 listing：无占位、category/platforms/age_rating 合法、privacy URL https 且真实 | `productivity` / `["linux"]` / `all`；无 `example.com` 占位；privacy URL 指向仓库 `oncue/PRIVACY.md`（公开性与归属见 B4） | **已有**（URL 公开性 **待 HUMAN**） |
| C3 | §3.3 真实截图、看过、在 listing 中登记；不得 dummy/crop/改名 | `screenshots/01-native-rinx.png` = 990x613 / sha256 `0a3898f0…56bb05`，**0.4.2 候选自己的真实 X 捕获**（`/g?raw=1` 本机 GL 超时故用 `import -window`），已逐张看过；替代图 `042-unavailable-cardhost.png` 为不可用态取证。**但**两图都被 AI1 判定有裁切（B2） | **待补**（若做 B2 修订，截图需重拍重登记） |
| C4 | §3.4 `hub stamp` + `hub check` | stamp digest `082844db…`；check PASSED（transcript 步骤 1/3/5 + S3 复核） | **已有**（对 `79a018e` 字节；HEAD 见 B1） |
| C5 | §3.5 `hub scan` → 7 问书面答案 | packet + 答案见 A10 | **待补**（Q1 刷新） |
| C6 | §3.6 发布者密钥（HUMAN） | 现用 `oncue.local` 工作钥；属主密钥未建 | **待 HUMAN** |
| C7 | §3.7 对最终字节签名（签名覆盖 stamp 后 digest；改后必须重走链） | 已签：`integrity.signature = {key_id:"oncue.local", value:"a44ddcbf…d4e505"}`，`hub check --publisher-key` PASSED；`241a7f5` 破坏了这一点（B1） | **已有**（对 `79a018e`）/ **待补**（对 HEAD） |
| C8 | §6 checklist：`octo doctor`、`git status` 只提交 bundle/与应用源码、无 key/`.local-state`/`build/` | `octo doctor` ok（S1/S2 开工前均有记录：`042-freeze-transcript.txt` 头 3 行）；`git status -- oncue/bundle` 干净、HEAD 无 key 文件（`collaboration/ai2-credential-public.pem` 在仓库根但不在 bundle，且只是公钥） | **已有**（`build/` 排除见 B8） |
| C9 | 工具链 rev 漂移需在提交说明中写明 | 本机 hub/card-host 来自 App Hub rev `0f33211`，而文档所述为 `79a2c4f`/`6c075d0`/`e8601b8`/`a72989f` | **待补**（写进 issue 或提交说明一行） |

---

## D. 结论：能否用现有证据满足？

- **可以满足（已有证据）**：应用 id/版本、bundle 路径、仓库 URL 文案、`hub check` 完整输出、`hub scan` 七问答案（改一句过期文案后）、实测/未测清单、草稿文本本身。
- **只能由人满足（待 HUMAN）**：push、打 tag、填 SHA、开 issue、粘贴或确认发布者公钥/选 unsigned、隐私政策 URL 与参赛口径确认、是否等 AI1 的全文视图修订、mirror 去留。
- **无法用现有证据满足（需要新的执行）**，共 3 条：
  1. **B3 真实宿主回合**：`matrix.*` 房间读取与 `octos.*` 模型回合——仓库内不存在任何一次成功的原生宿主回合证据，硬阻塞 `profile_unresolved` 需在宿主 GUI 配置 provider profile。这不是"整理证据"能解决的。
  2. **B2 全文可见性**：AI1 的阻断性复核要求显式全文查看路径（分页/单条 + 位置/总数）并在两个视口复验——需要改版式、重拍截图、重走 stamp→sign→check→提交→发布（新版本号）。
  3. **B1 最终提交的门禁输出**：issue 必须贴"**最终要 tag 的那个提交**"上的 `hub check`；在 `241a7f5` 未重签之前，这个输出对 HEAD 字节不存在（现在是 `REFUSED`）。修正后即可产出，属执行缺口而非原理障碍。

> 一句话：**材料本身可以起草完（本文件 + `build/SUBMISSION.md`），但"可提交状态"还差 3 件执行 + 一批 HUMAN 动作；其中真实宿主回合与全文可见性两项，砸多少整理功夫都变不出来，必须真跑。**
