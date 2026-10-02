# AGENTS.md — OnCue 参赛项目规程（防遗忘）

> **这份文件的作用**：把赛事硬性要求、官方流程、环境事实、当前进度**固化在仓库里**，
> 避免上下文变长或被新会话接手时反复返工。
> **每次开工前先读本文件；每次状态变化后更新本文件的第 6/7/8 节。**
> 官方 script-app 流程也要求 app 目录有 `AGENTS.md`（属"不提交"文件，不在 `bundle/` 内）。

---

## 1. 项目概况

| 项 | 值 |
| --- | --- |
| 作品 | **OnCue · 群聊试映室** |
| 形态 | **OctoScript 小程序 / Hub 卡片包**，跑在 **Rinx** 小程序宿主内，经 **App Hub** 发布 |
| 包路径 | `oncue/bundle/`（`main.splash` + `manifest.json` + `listing.json` + `assets/` + `screenshots/`） |
| 应用 id | `oncue-screening-room`（不以保留名结尾 ✓） |
| 版本 / digest | `0.4.4` / `9b221cd7ed27bb6fb38c7d91bdd04d13de6387b4055565d74bf7c1bce9f13b97` |
| 赛道 | OctoSense 即时消息 · **Rinx**（官方明确：即时消息场景绑定 Rinx） |
| 队伍 / 成员 | OnCue / YCOROY |
| 许可 | Apache-2.0（`oncue/LICENSE`） |

**一句话功能**：把还没发出去的一句话放进私人排练场，读授权房间消息作线索，
请设备助手生成三条假设下一幕，逐句播放查看，改动后存草稿 A/B，**应用自身不发送任何消息**。

---

## 2. 赛事硬性要求（不可违背）

### 2.1 时间（北京时间）
| 节点 | 时间 |
| --- | --- |
| **初赛提交截止 / 版本冻结** | **10/4 23:59** |
| 初赛评审（只用冻结版本） | 10/5–10/6 18:00 |
| 公布 50 人晋级 | 10/6 20:00 |
| 复赛提交 | 10/9 23:59 |
| 线上决赛答辩 / 评奖 | 10/12 |

### 2.2 形态与定位
- 张老师：**"初赛代码只要求 octoscript 的应用"**、**"appcard 必须通过 App Hub 发布"**、
  **"独立开发的应用不在 octosense 里就和比赛没关系了"**。
- 官方：**"统一最小交付应能展示：事件或意图输入 → Agent 理解并形成操作计划 → 用户查看或授权
  → 执行 → 核验结果 → 状态变化或失败处理。仅生成界面、摘要或静态卡片，不足以证明完成了任务自动化。"**
  → ⚠️ **本应用当前产出"摘要 + 假设对白"且不发送，存在被判为"仅生成界面/摘要"的风险（见第 7 节）**。
- 迭代顺序（官方）：**先完成基本功能 → 接 octos agent 上 agentic 功能 → 最后再调 UI**。
- 初赛**不要做太复杂**，能传达基本功能即可；应用层作品**不要求**改 ROM，也**不要求**提交无关 PR/issue。

### 2.3 提交材料（6 项）
1. 公开源码仓库 + 固定提交号/版本 + **Apache-2.0**
2. 应用目标、适用场景、图标、运行截图、作者与支持方式
3. 宿主版本、支持平台、依赖与启动说明
4. 数据来源、权限、隐私、授权/拒绝/失败行为
5. **Agent 任务演示**：输入、Agent 步骤、如何核验、哪些需人工确认
6. 运行截图/日志/复现步骤；**演示材料不能代替可运行作品**

### 2.4 聊天/账号类作品的额外硬要求
> **必须演示「接收者独立授权」**：发送者分享卡片 → 接收者用自己的账号独立授权 →
> 拿到自己的授权与草稿，**不继承发送者身份或权限**。（Rinx 基线核心机制之一）

---

## 3. 官方发布流程（必须逐步照做）

### 3.1 script-app 十四步（`OctoScript-App-Design-Flow/flows/script-app/FLOW.md`）
| # | 步骤 | 通过条件 | Human |
| --- | --- | --- | --- |
| 1 | 写 `$A/BRIEF.md`（画面/动作/数据/状态/主机/能力+理由） | 每画面每动作一行，每能力有理由 | 需求不明时确认 |
| 2 | `tools/octo new $A --id <id> --name "<Name>"` | 打印 `created …` | 否 |
| 3 | 依 brief 填 `manifest.json` 的 capabilities 与 `network.hosts`，不多不少 | 每能力对应 brief 一行 | 否 |
| 4 | 写 `main.splash`，**只用能引用的 API** | 无不可引用的 API | 否 |
| 5 | `tools/octo run $B --port $P --hidden --detach` | `admitted` + `ready: first frame drawn` | 否 |
| 6 | `tools/octo shot $P /tmp/first.png` 并打开看 | 首屏可见、非空白非错误帧 | 否 |
| 7 | **用远程桥驱动每个动作**：`/click?x=&y=`、`/t?t=`、`/k?k=down&c=`，各动作后用截图或 `/snap` 或 jail 文件观察 | 每个动作效果被观察并记录 | 否 |
| 8 | 测**空 / 错误 / 重启持久化**（`/quit` 后重跑第 5 步） | 各状态合理；该持久化的数据能存活重启 | 否 |
| 9 | 修到 5–8 全过 | 一轮全过 | 否 |
| 10 | 定稿 `listing.json`（subtitle/description/category/keywords/platforms/release_notes），换 `assets/icon.svg` | 解析通过且只说真话 | 发布者信息=**人** |
| 11 | 驱动到最佳真实状态 → `tools/octo shot $P $B/screenshots/01-main.png`（最多 8 张，列进 listing）；逐张打开看；`/quit` | 每张都是看过真实截图 | 否 |
| 12 | `tools/octo check $B` | `<id> <version> — PASSED`，只剩未签名警告 | 否 |
| 13 | `hub scan $B --packet $A/build/review.json`，七问写入 `$A/build/REVIEW-ANSWERS.md` | packet 已写、七问如实回答 | 否 |
| 14 | 按 §5 格式汇报，**停** | 汇报交付 | 交接给人 |

### 3.2 Definition of Done（交接给人之前必须全满足）
1. `tools/octo check <bundle>` 输出 `— PASSED`，只剩未签名警告
2. `bundle/screenshots/` 有真实截图，列在 `listing.json`，**每张都打开看过**
3. brief 里每个交互在 `card-host` 中**用远程桥原生驱动**（click/type/tap）并观察到效果
4. **空、错误、重启**状态都跑过
5. `hub scan` packet 写在 bundle 外，七问已回答
6. PUBLISHING 清单执行到**第一个 HUMAN** 行为止

### 3.3 每个应用必须遵守的规则（官方 AGENTS.md）
- **应用里不得有秘密**：无密码/PIN/验证码输入框、无登录表单、无 API key/token。账号走宿主 sheet。
- **声明的每个 host 都要在 `network.hosts`**（裸域名、小写、无 scheme/端口/通配），**永不用 `http://`**。
- **AI 功能都是可选的**：`card-host`（含 `tools/octo run`）**不提供** `octos.*` / `model`，
  调用会得到 `no service answers "…" on this device`。**永远不要把模型 key 放进应用**。
- **只申请需要的能力**；每个能力都要对应画面上真实做的事。
- **截图必须是真实状态的真实截图**，绝不画、生成、裁切或从别的应用复制。
- **每次编辑后重新 stamp**；签名后任何编辑都要重新 stamp + 重新签名。
- **保持 bundle 干净**：只放 `manifest.json`、`listing.json`、入口、图标、截图
  （声明自有 agent 时另加 `tools.json`/`AGENT.md`/`skills/`）。
  笔记、密钥、日志、审核包、`.local-state/` 一律不放。
- **无头运行**：`tools/octo run … --hidden`；多个实例各用 `--port` 与 `--app-data`。
- **清理启动的进程**：用 `curl -s 127.0.0.1:<port>/quit`，不要 `pkill` 别人的窗口。
- 语法提醒：`#x` 表示含 `e` 的十六进制颜色；`for i in n`，无 `range()`；
  `name := Widget{}` 用 `ui.name` 寻址；`on_render` 中 `if` 与 `for` 分开（无 `else for`）。

### 3.4 发布清单（`tools/octo package-help`）
```
1. tools/octo doctor
2. manifest.json：id / name / version（每次发布都要新）/ 只留用到的 capabilities / 每个 host
3. listing.json：占位全部替换；publisher、support、privacy_policy_url 必须 https；platforms 只写测过的
4. tools/octo run $B --port 8141 --detach          → admitted
5. 逐项原生测试：/snap、/click?x=&y=、/t?t=、/k?k=down&c=ReturnKey
6. tools/octo shot 8141 $B/screenshots/01-main.png → 打开看；curl /quit
7. tools/octo check $B                              → PASSED
8. hub scan $B --packet build/review.json           → 回答七问
9. 【人】密钥在仓库外：hub keygen / sign-manifest / check --publisher-key；签名后任何编辑都要重签
10.【人】打 tag + 在 OctoSense-App-Hub 开 issue "Submit <id> <version>"
    绝不改它的 catalog.json/index/artifacts；未真正提交前绝不声称已提交或已批准
```

---

## 4. 硬指标（已核对）

| 项 | 规则 | 本包 |
| --- | --- | --- |
| 包内总量 | ≤ 8 MiB | **0.12 MiB** ✓ |
| 图标 | ≤ 1 MiB，方形，自包含（无脚本/外链；SVG 命名空间 URI 不算外链） | 554 B，`viewBox 0 0 256 256` ✓ |
| `storage.max_bytes` | 上限 16 MiB | 4 MiB ✓ |
| `compute.instruction_budget` | 上限 20,000,000 | 8,000,000 ✓ |
| `compute.memory_bytes` | 上限 64 MiB | 32 MiB ✓ |
| 保留 id 名 | 不得是或以 `agents apphub appcard card dev octos os reference rinx sheets shell system terminal toolbox workflow` 结尾 | `oncue-screening-room` ✓ |

### 4.1 能力（`docs/CAPABILITIES.md`）
- **`matrix.*`（45 个）只由 Rinx 小程序宿主提供。**
- **`octos.session.open/history/turn.start/turn.interrupt`** 由托管内核的 OctoSense shell 提供，
  **Rinx 小程序宿主也提供**；`card-host` 一律不提供。
- **不要申请**（无服务或商店应用零收益）：`prompt`、`llm`、`news`、`glance`、`research`、`crawl`、
  `clipboard`、`ledger.read`。
- 未申请即未授权；前缀（`octos.`、`matrix.`）或自造名都会被拒。

---

## 5. 环境事实（实测，可直接复用）

| 项 | 值 |
| --- | --- |
| 宿主二进制 | `/opt/src/OctoSense/target/release/octosense`，sha256 `87ed4dccd14bac51222f40c38d4db086911790786b688a68a503002ada64ba25` |
| 构建基线 | **官方 Rinx `c515e5fc9b6dc22e67f7d551b09fdd793ec685a1`（零本地补丁）** |
| 宿主启动 | `DISPLAY=:99`、`XAUTHORITY=/srv/oncue-runtime/state/xauthority`、cwd `/srv/oncue-host-cwd`、`HOME=/srv/oncue-home`、`RINX_DATA_DIR=/srv/oncue-rinx-data-rinxchat`、`OCTOS_APP_CORE_BIN=/srv/oncue-runtime/octos/octos`、`--module rinx --test-action launch-rinx` |
| 赛事服务器 | Homeserver `https://matrix.rinx.chat`（**直连即可，不需代理**）；认证 `https://auth.matrix.rinx.chat` |
| 赛事账号 | **`@codezzzsleep:matrix.rinx.chat`**（device `kI8muzdQV8`）；凭据在 `/srv/oncue-runtime/secrets/rinx-chat.env`（600） |
| 测试房间 | `!2TfOHq2ZGCYO5WJmDC:matrix.rinx.chat`（"OnCue 试映室测试房"，12 条消息） |
| 登录方式 | 该服务器**关闭本地注册与密码登录**，只能 SSO → 必须浏览器；本机已装 firefox |
| 官方工具链 | `OctoScript-App-Design-Flow/tools/octo`；先 `. /root/hackthon/refs/octo-env.sh` 设置 `OCTO_HUB`/`OCTO_CARD_HOST` |
| 参考仓库（完整克隆） | `/root/hackthon/refs/{hackathon-agenticapp26,OctoScript-App-Design-Flow,OctoSense-App-Hub,OctoSense,Octoscript,Rinx}` |
| 密钥 | 发布者私钥 `/srv/oncue-runtime/dev/keys/working.key`（id `oncue.dev`，公钥 `50578fd7e0d8ac51a1e9e590835427ce8e71f46dba491860c75ae4e7c8c78042`）——**永不入仓库** |

---

## 6. 当前状态（**每次状态变化后更新本节**）

### 6.1 已完成
- [x] 仓库梳理：40 个文件 / 1.4M，Markdown 断链 0
- [x] 包规范：`tools/octo check`（未签名）→ **PASSED**，仅未签名警告
- [x] `oncue/BRIEF.md`（流程第 1 步）
- [x] `build/review.json`（`hub scan` 审核包）+ `build/REVIEW-ANSWERS.md`（七问，route: human-review）
- [x] 产品/隐私/验证/依赖文档齐全
- [x] 宿主改用**官方 Rinx 重建**（弃用本地补丁），`:99` 已换装运行
- [x] **赛事服务器端到端实测通过**：登录 → 导入 → Review（房间保留）→ Run →
      `matrix.room_info`/`read_messages` 读到真实房间 → `octos.turn.start` 完成
      （内核日志 `LLM response received … response_content_len=1839`）
- [x] tag `v0.4.4` 已打并推送

### 6.2 未完成（按优先级）
| # | 缺口 | 说明 |
| --- | --- | --- |
| 1 | **接收者独立授权演示** | **官方硬要求**，目前零证据；需第二个账号 |
| 2 | ⚠️ **"最小交付"定位风险** | 官方要求含"执行→核验"，本应用不发送；需**产品决策** |
| 3 | **开 Submit issue** | 唯一挡住正式提交的动作；本机无 GitHub token |
| 4 | DoD #3：交互用**远程桥**驱动 | 此前用 XTest；`/snap` 已验证可用 |
| 5 | DoD #4：**空/错误/重启**三态完整测试 | 证据不完整 |
| 6 | 宿主内**停止 / 90 秒 / 迟回调**在赛事服务器重测 | 旧结论在 matrix.org 上，已作废 |
| 7 | 包的交付签名状态 | 现为**已签名**；官方开发态期望未签名（已签名时 `octo check` REFUSED） |
| 8 | 截图未用 `tools/octo shot` | 该工具在本机不可用（见第 8 节），已用 ffmpeg 变通 |
| 9 | 无运行视频（可选） | — |

---

## 7. 待决策（需人定，不要自行决定）

1. **定位**：是否要把"用户确认后回写原会话 / 显示真实回执"纳入范围，以满足官方
   "执行 → 核验结果"的最小交付？还是强化"核验结果"环节（例如对假设内容做事实核对）？
2. **交付签名状态**：仓库里放**未签名**（官方开发态、`octo check` PASSED）还是**已签名**？
3. **是否用官方 Rinx 重建宿主** —— 已完成（可回退：旧二进制备份在 `/root/oncue-runtime/backup/`）。

---

## 8. 已知 Gap / 环境坑（带复现）

1. **`tools/octo shot` 在本机不可用**
   ```
   tools/octo run <bundle> --port 8143 --detach   → ready: first frame drawn
   tools/octo shot 8143 out.png                   → GET /g?raw=1 failed: HTTP Error 404
   curl 127.0.0.1:8143/s     → 正常，窗口 412x892 存在
   curl 127.0.0.1:8143/g?raw=1 → {"err":"grab timeout (is this backend rendering?)"}
   curl 127.0.0.1:8143/gseq?n=1&every_ms=50 → 同样的 grab timeout
   ```
   平台 Linux aarch64 + Xvfb + llvmpipe；带不带 `--hidden` 都一样。
   **变通**：`ffmpeg -f x11grab -video_size WxH -i :99+<x>,<y>` 抓窗口。
2. **matrix.org 与 matrix.rinx.chat**：赛事用 **`matrix.rinx.chat`**。此前在 matrix.org 上的
   一切"真实房间/Agent 回合"结论**作废**，只作内部溯源。
3. **xclick/xtype 的坐标偏移会变**（窗口位置每次不同）：先 `xwininfo` 取实际位置，再换算。
4. **firefox 收不到键盘**：X 输入焦点在 OctoSense 窗口；须 `XSetInputFocus` 到 firefox 主窗口。
5. **`pkill -f <关键词>` 会杀掉自己**（命令行含该关键词）——按进程名或端口杀。
6. **Splash 限制**：无 `0x` 十六进制字面量（用十进制）；无空块 + `else`；`ok` 是保留变量名。

---

## 9. 纪律（每次都必须遵守）

- **绝不**向任何 Matrix 房间发送消息（本应用不发送；验证也不发）。
- **绝不**打印或提交任何凭据、token、私钥；密钥只在仓库外且 600。
- 卡片包面向比赛：**不放**内部协作产物、运维脚本、验收台账、历史考古、探针脚本。
- **未真正提交前，绝不声称已提交或已批准。**
- 任何"真实宿主"结论必须标注**在哪个服务器、哪个版本**上取得。
- 单次授权不得扩大为跨会话自动发言权限。

---

## 10. 常用命令

```sh
# 官方工具链
. /root/hackthon/refs/octo-env.sh
cd /root/hackthon/refs/OctoScript-App-Design-Flow
python3 tools/octo doctor
python3 tools/octo run /root/hackthon/OnCue/oncue/bundle --port 8141 --hidden --detach
python3 tools/octo check /tmp/oncue-unsigned/bundle        # 未签名副本
curl -s 127.0.0.1:8141/snap | head -c 400
curl -s 127.0.0.1:8141/quit

# 重新 stamp + 签名（内容改动后）
$OCTO_HUB stamp oncue/bundle
$OCTO_HUB sign-manifest oncue/bundle --key /srv/oncue-runtime/dev/keys/working.key --key-id oncue.dev
$OCTO_HUB check oncue/bundle --publisher-key oncue.dev=50578fd7e0d8ac51a1e9e590835427ce8e71f46dba491860c75ae4e7c8c78042

# 审核包
$OCTO_HUB scan <未签名副本>/bundle --packet build/review.json
```
