<p align="center">
  <img src="docs/readme/banner.png" alt="OnCue · 群聊试映室：在群里开口之前，先在这里试一下" width="100%">
</p>

<p align="center">
  <img src="docs/readme/badges/version.svg" alt="版本 0.5.3">
  <img src="docs/readme/badges/host.svg" alt="宿主 官方 Rinx 1.3.0">
  <img src="docs/readme/badges/ui.svg" alt="界面场景 85/85 通过">
  <img src="docs/readme/badges/logic.svg" alt="逻辑测试 12 套 437 项">
  <img src="docs/readme/badges/license.svg" alt="License Apache-2.0">
</p>

<p align="center">
  <a href="evidence/demo/oncue-demo-053.mp4"><b>▶ 演示视频（4:24）</b></a> ·
  <a href="OnCue%20复赛说明.pdf">复赛说明 PDF</a> ·
  <a href="oncue/VERIFICATION.md">验证记录</a> ·
  <a href="oncue/docs/RUNNING.md">运行说明</a>
</p>

---

在群里说话，最怕说错、说过头。**OnCue 是运行在 Rinx 里的群聊试映室**：开口之前，先把这句话私下试映一遍。它读你授权的群聊，请助手写出三种说法，**由程序逐条核对事实**，最后**由你决定发不发**；发出去以后，再把群友的真实回复和试映时的预想对照，给出下一句。

<p align="center">
  <img src="docs/readme/loop.gif" alt="官方 Rinx 1.3.0 真机录屏：读群、试映、两条说法被拦、确认发送、看反响、确认前来新消息" width="800">
  <br><sub>官方 Rinx 1.3.0 真机录屏（等待部分已加速）：读群 → 试映 → 逐条核对 → 确认发送 → 看反响 → 新消息复核</sub>
</p>

## 为什么需要它

让 AI 直接替人在群里说话，会出三类问题。OnCue 对每一类都设了一道把关：

| 问题 | 会发生什么 | OnCue 的把关 |
| --- | --- | --- |
| **编造** | 写出群里没人说过的数字和承诺 | 每条说法只能引用你勾选的消息；数字、中文数字、承诺句式没有出处就拒绝，**只拦那一条并写明原因** |
| **越权** | 没确认就发；结果不确定时重发；群里有了新消息还照发旧稿 | 两步确认才发送；发送前再读一次群，有新消息先标出来；发出后读回核实，**从不自动重发** |
| **断环** | 发完就结束，下一句只能靠猜 | 看反响：对方原话照列，助手对照试映时的预想给出下一句；对照同样要过检查 |

> **一句话原则：助手写措辞，程序做核对，人来做决定。**

## 一次发言，四幕试映

```mermaid
flowchart LR
    A["<b>01 读群</b><br/>打开即读最近 30 条<br/>保留原编号"]:::stage --> B["<b>02 试映</b><br/>助手写三种说法<br/>附假设对白与推荐"]:::stage
    B --> C{"程序逐条核对<br/>出处 · 数字 · 承诺"}:::check
    C -- "通过" --> D["推荐句进草稿<br/>可改可不发"]:::stage
    C -- "不通过" --> X["只拦这一条<br/>写明原因"]:::reject
    D --> E{"你确认发送？"}:::human
    E -- "确认" --> F["<b>03 上映</b><br/>发前再读群<br/>发后读回核实"]:::stage
    F --> G["<b>04 反响</b><br/>原话照列<br/>对照预想 · 给下一句"]:::stage
    G -. "下一句放进确认区" .-> E

    classDef stage fill:#F4F1E8,stroke:#1F6B4A,stroke-width:2px,color:#1B2420
    classDef check fill:#FFF4DF,stroke:#E3A23B,stroke-width:2px,color:#1B2420
    classDef human fill:#1F6B4A,stroke:#14201A,color:#FFFFFF
    classDef reject fill:#FBE9E2,stroke:#A34C24,color:#A34C24
```

人只做三次决定：**允许发给助手**、**应用修订**、**确认发送**。其余的读群、核对、读回都由 Agent 自动完成。

## 真机实拍

2026-10-13 在[**官方 Rinx 1.3.0 发布包**](https://github.com/hagency-org/Rinx/releases/tag/v1.3.0)（零本地补丁）上跑通完整闭环，模型 MiniMax-M2.7-highspeed。下面是那次运行的实拍截图（[完整证据](evidence/native-130/)）。

<p align="center">
  <a href="evidence/demo/oncue-demo-053.mp4"><img src="docs/readme/video-thumb.png" alt="演示视频（4:24）：官方 Rinx 1.3.0 真机录屏，中文配音" width="720"></a>
  <br><sub>点击观看带配音的完整演示（4:24）</sub>
</p>

<table>
  <tr>
    <td width="33%"><img src="evidence/native-130/02-auto-read.png" alt="打开即读群"></td>
    <td width="33%"><img src="evidence/native-130/03-takes.png" alt="两条说法没通过核对，推荐改用 C"></td>
    <td width="33%"><img src="evidence/native-130/04-draft.png" alt="推荐句进草稿"></td>
  </tr>
  <tr>
    <td><b>① 读群</b>　打开就读，阶段条「读群」打勾</td>
    <td><b>② 核对</b>　A 写了「4个人」、B 写了「已经参与订」，都被拦下；推荐改用 C</td>
    <td><b>③ 草稿</b>　通过核对的推荐句进草稿框</td>
  </tr>
  <tr>
    <td><img src="evidence/native-130/05-confirm.png" alt="确认视图"></td>
    <td><img src="evidence/native-130/07-reaction.png" alt="看反响"></td>
    <td><img src="evidence/native-130/08-n16-flagged.png" alt="确认前来了新消息"></td>
  </tr>
  <tr>
    <td><b>④ 确认</b>　发到哪个群、完整正文，确认后才发；发后读回</td>
    <td><b>⑤ 反响</b>　第二账号的原话照列，对照预想给出下一句</td>
    <td><b>⑥ 新消息复核</b>　确认那一刻群里来了新消息，标出来再决定</td>
  </tr>
</table>

## 三道把关是怎么串起来的

```mermaid
sequenceDiagram
    autonumber
    actor 你
    participant O as OnCue（小程序）
    participant R as Rinx 宿主
    participant A as 宿主助手（octos）
    你->>O: 写台词、选目标，点「允许并试映」
    O->>R: 读最近 30 条消息
    O->>A: 台词 + 目标 + 勾选的消息（不含名字）
    A-->>O: 三种说法 + 推荐
    O->>O: 逐条核对出处、数字、承诺
    O-->>你: 通过的说法和被拦原因，推荐句进草稿
    你->>O: 发到群里 → 去核对 → 确认发送
    O->>R: 再读一次群（有新消息就标出，等你重看）
    O->>R: 原样发送
    O->>R: 读回核验
    O-->>你: 读回看到这条，才显示「已发到」
```

## 架构与权限

```mermaid
flowchart TB
    subgraph Rinx["Rinx 宿主（官方 1.3.0）"]
        direction TB
        O["<b>OnCue</b><br/>Splash 小程序 · 不直连网络 · 不持有密钥"]:::app
        H["小程序宿主<br/>逐项授权 · 1 小时或关闭即收回"]:::host
        O <--> H
    end
    H <--> M[("Matrix 服务器<br/>只限所选的群")]:::ext
    H <--> K["octos 内核<br/>（宿主配置的助手）"]:::ext
    K <--> L(["大模型"]):::ext

    classDef app fill:#F4F1E8,stroke:#1F6B4A,stroke-width:2px,color:#1B2420
    classDef host fill:#E8E3D4,stroke:#6B756F,color:#1B2420
    classDef ext fill:#FFFFFF,stroke:#B8B1A0,color:#46524C
```

| 申请的服务 | 用途 |
| --- | --- |
| `storage` | 草稿按房间存在本机 |
| `matrix.room_info` | 房间名称与稳定身份 |
| `matrix.read_messages` | 读取所选群的最近消息，核对变化与发送结果 |
| `matrix.account_info` | 当前账号身份，用来确认「是我刚发的」 |
| `matrix.send_message` | 你确认后，把草稿原样发到这个群 |
| `octos.session.open` · `octos.turn.start` · `octos.turn.interrupt` | 请助手试映、修订、对照，以及停止等待 |

应用本身不联网；Rinx 和宿主助手可能联网并保留历史，在 OnCue 里删除草稿不影响那边。详见[数据说明](oncue/PRIVACY.md)。

## 快速开始

需要 **Rinx v1.2.0 或更新版本**（推荐[官方 1.3.0 发布包](https://github.com/hagency-org/Rinx/releases/tag/v1.3.0)），以及一个已登录、有消息的 Matrix 群，并在 Rinx 里配置好助手。没有选房间时，应用打开后进入本地样例，可以先看一遍流程（样例不调用模型）。

**从 App Hub 安装**：Rinx 里打开 **Discover → Mini apps**，进入 App Hub，找到 OnCue 后 **Add**、**Open**。打开时宿主列出八项服务和所选的群，确认后本次运行才获得授权。

**本地导入**：仓库里的 `bundle/` 是未签名的应用包，可以直接导入。

1. Rinx 里打开 **Discover → Mini apps → Import an app**。
2. 包路径填仓库的 `bundle/` 目录，房间填你的 Matrix 房间 ID。
3. 点 **Review bundle**，核对名称、版本、「Local unsigned bundle」标记、八项服务和 Allowed room，然后 **Run**。应用在独立的「Rinx · Mini apps」窗口里打开。

每次打开都要重新授权。完整步骤和常见问题见[运行说明](oncue/docs/RUNNING.md)。

## 验证

**每改一次代码，全部测试重跑。**

| 层次 | 结果 | 怎么测的 |
| --- | --- | --- |
| 界面场景 | **85/85** 次运行通过 | 75 个场景 × 412×892、954×448、1000×800 三种尺寸；宿主的每种回复和错误由场景注入 |
| 逻辑测试 | **12 套 437 项**断言通过 | 在真实 card-host 虚拟机里直接跑生产函数，结果[可离线复核](evidence/logic-tests/) |
| 工具单元测试 | **114 项**通过 | `oncue/tools` 的单元测试 |
| 打包检查 | `hub check` 通过 | 只有「未签名」提示 |
| 真机闭环 | 官方 Rinx 1.3.0 跑通 | 读群 → 试映 → 确认发送 → 读回 → 看反响 → 新消息复核，[证据](evidence/native-130/) |
| 授权状态 | 4 种实拍 | 未选房间、未允许、撤回、到期，[证据](evidence/auth-053/) |

为适配最新运行时，核对拆进计时器回调分步执行，避开 Rinx 1.3.0 单次回调 20 万条指令的上限；等待助手的期限为 150 秒。细节见[验证记录](oncue/VERIFICATION.md)和[测试说明](oncue/tests/README.md)。

## 对 OctoSense 的贡献

| 贡献 | 内容 | 链接 |
| --- | --- | --- |
| **splash-app-verify 测试技能** | 先写界面契约和场景，再写代码；假宿主按场景回复，每次修改全量重跑。帮 OnCue 在交付前抓到 5 个真问题，任何 Splash 应用都能用；Splash 空态语法文档随同一 PR 提交 | [App Flow PR #192](https://github.com/OctoSense-org/OctoSense-App-Flow/pull/192) · [仓库内副本](skills/splash-app-verify/) |
| **Rinx 房间绑定问题复现** | 导入表单读错房间号，应用以「没有房间」启动；整理了复现与修复材料；上游 1.2.0 已修复 | [复现材料](build/RINX-PR-room-binding.md) |
| **Palpo 密钥备份 404 复现** | 开了密钥备份的账号在新房间邀请任何人都失败；规范要求 200，Palpo 返回 404 | [验证记录](oncue/VERIFICATION.md) |

<details>
<summary><b>回应初赛评审的建议</b></summary>

<table>
  <tr><th>建议</th><th>做了什么</th></tr>
  <tr><td>补「拒绝授权、授权到期」的验证记录</td><td>在官方 Rinx 上实拍四种授权状态；授权到期实测约 1 小时</td></tr>
  <tr><td>防编造扩展到中文数字和承诺句式</td><td>覆盖中文数字、半天、复合单位；承诺句式逐句检查</td></tr>
  <tr><td>应用包移到仓库根目录</td><td>已移到 <code>bundle/</code></td></tr>
  <tr><td>改用 GitHub 发布流程</td><td>打 tag 触发 <code>publish-app.yml</code>，版本 0.5.3</td></tr>
  <tr><td>「【推荐】B」同行写法也算推荐</td><td>解析器同时接受独占行与同行写法，逻辑测试覆盖</td></tr>
  <tr><td>反响协议改名，避免与修订协议混淆</td><td>反响对照协议改名 F1，修订协议仍为 R1</td></tr>
  <tr><td>「允许并试映」旁说明这次发什么</td><td>按钮下方列出这次发给助手的内容（不含名字）</td></tr>
</table>

</details>

<details>
<summary><b>仓库结构</b></summary>

```text
bundle/                     应用包（main.splash、manifest、字体与图标）
oncue/
  BRIEF.md                  产品说明
  PRIVACY.md                数据说明
  VERIFICATION.md           验证记录
  docs/RUNNING.md           运行说明
  tests/                    界面场景与逻辑测试
  tools/                    打包、印章与证据工具
skills/splash-app-verify/   测试技能（已向 App Flow 提交 PR #192）
evidence/                   真机截图、测试结果与演示视频
build/                      审核问答与宿主问题复现材料
```

</details>

## 文档

[产品说明](oncue/BRIEF.md) · [数据说明](oncue/PRIVACY.md) · [运行说明](oncue/docs/RUNNING.md) · [验证记录](oncue/VERIFICATION.md) · [测试说明](oncue/tests/README.md) · [更新记录](CHANGELOG.md) · [审核问答](build/REVIEW-ANSWERS.md)

<p align="center"><sub>Apache License 2.0 · GOSIM 智能体应用黑客松 2026 复赛作品</sub></p>
