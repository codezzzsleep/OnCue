# OnCue · 群聊试映室

**先试着说，再决定要不要发。**

> **当前 main：0.4.7。** 助手不再撰写事实摘要，只选原消息编号，应用取回原文逐字展示并拒绝改写；真实 Rinx 主机两个外窗尺寸下的阅读、播放、草稿恢复，以及 138 项真实 OctoScript 受控测试均已通过。实现边界与未覆盖项见[验证摘要](oncue/VERIFICATION.md)。

把一句还没发出去的话放进私人排练场，看三个不同的下一幕：
**顺着这句 / 换个问法 / 换个玩法**。回看原消息，逐句播放匿名的假设接话，
把喜欢的建议放进草稿，再对照两种写法。

<p align="center">
  <img src="evidence/screenshots/hero.png" width="100%"
       alt="OnCue 在 990×613 与 412×892 两个视口下的界面">
</p>

<p align="center">
  <sub>同一应用在 <b>990×613</b>（宽屏）与 <b>412×892</b>（窄屏）两个视口下的排版</sub>
</p>

参赛作品是 [`oncue/bundle/`](oncue/bundle/)：一个在 OctoSense / Rinx 宿主内运行的
**OctoScript 小程序**。

## 一分钟怎么玩

1. 打开虚构的「国庆搭子局」，试一句「明早 9 点出发，住一晚」——原消息里有人中午才能走、希望当天回来。
2. 改成「中午出发、当天回来，先核实预算」，重新试映，比较三个不同的接法。
3. 选「换个玩法」，把讨论变成半日旅行盲盒：每人给一个想做的事，再找条件的交集。
4. 播放、暂停或逐句查看假设对白，把喜欢的建议放进草稿；改两种写法，分别存 A、存 B，再取回对照。

<p align="center">
  <img src="evidence/screenshots/app-row.png" width="62%"
       alt="左侧：打开样例并试映下一幕；右侧：逐句播放假设对白">
</p>

<p align="center">
  <sub>左：打开虚构样例、回看原消息 · 右：逐句播放「顺着这句」的假设对白</sub>
</p>

原消息是事实线索，下一幕是假设，未被同意的行程和费用仍需自己核实。

## 在 Rinx 里运行

装这个应用有两条途径。

**途径一：App Hub（正式途径）**

在 Rinx 里打开 **Discover → Mini apps**，进入 App Hub 应用库（Recent / My apps / Browse），找到 OnCue 后 **Add** 安装已审核版本，再点 **Open**。打开时 Rinx 会列出这个应用申请的六项服务和唯一允许的房间，确认后才为本次运行授权。这条路目前走不通：上架审核还在进行（[App Hub #57](https://github.com/OctoSense-org/OctoSense-App-Hub/issues/57)），装不到属正常。

**途径二：本地导入（自测 / 评审复现途径）**

适合现在就想跑一遍的人。Rinx 的开发者导入有两个前提，先说明再给步骤：

- **不收带签名的包。** 仓库里的正式包带发布签名，而开发者导入按官方设计（ADR 0006/0008）故意拒绝签名包——防止本地文件夹冒充"已过商店审核"的应用。所以要先生成一份去掉签名的副本，内容与原包一致。
- **房间必须是你自己的。** 应用只读导入时选定的那个房间的消息。我们的测试房间你不在其中，填了也读不到。

步骤：

1. 生成去签名副本（一条命令）：
   `python3 oncue/tools/prepare_dev_bundle.py /tmp/my-oncue`
2. Rinx 里打开 **Discover → Mini apps → Import an app**。
3. 包路径填 `/tmp/my-oncue/bundle`，房间填**你自己的 Matrix 房间 ID**。
4. **Review** 核对服务清单与房间 → **Run**。

每次打开都要为当前账号和所选房间重新授权，关闭应用即撤销。

<p align="center">
  <img src="evidence/screenshots/rinx-flow.png" width="100%"
       alt="左侧：Import an app 表单；右侧：应用在 Rinx 宿主内运行">
</p>

<p align="center">
  <sub>左：Developer 入口填入包路径与测试房间 · 右：Review 通过后在宿主内运行</sub>
</p>

当前版本已在 Rinx 外窗 **412×892** 与 **990×613** 下逐页读取真实三路线与摘录；实际应用嵌入区分别为 **376×727** 与 **954×448**。逐项验证记录见 [VERIFICATION.md](oncue/VERIFICATION.md)。

## 数据与边界

- **不发送任何消息**。排练与草稿都只在本地，保存由使用者主动触发。
- **不携带凭据**。Matrix 登录留在宿主、模型凭据留在内核；应用只申请
  `matrix.room_info`、`matrix.read_messages`、`octos.session.open`、`octos.turn.start`、
  `octos.turn.interrupt` 与本地 `storage`，且 `hosts` 为空（不访问任何网络主机）。
- 房间名为空时显示「已授权群聊」，**不回落到完整房间 ID**。
- 来源核对不能保证所有假设或建议符合事实；取材与存储范围见[数据说明](oncue/PRIVACY.md)。

## 文档

- [产品说明](oncue/PRODUCT.md) — 目标、流程与状态反馈
- [数据说明](oncue/PRIVACY.md) — 数据来源、权限与隐私
- [原生工作流](oncue/docs/NATIVE-WORKFLOW.md) — 在宿主里装载与运行
- [宿主环境与复现](oncue/docs/DEPENDENCIES.md) — 宿主版本、支持平台、依赖
- [验证摘要](oncue/VERIFICATION.md) — 当前版本的实测结果与未覆盖项
- **当前版截图**：[包内两张](<oncue/bundle/screenshots/>)——真实 Rinx 主机、真实授权房间与真实助手回合的同版截图，已逐张打开查看。
- [当前版演示](<evidence/submission/DEMO-0.4.7.md>) — 2 分 58 秒真实连续录屏、时间轴与解说词
- [App Hub 材料](evidence/apphub/) — `hub check` 输出与 `hub scan` 七问回答
- [Apache License 2.0](oncue/LICENSE)
