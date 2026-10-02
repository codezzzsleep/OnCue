# OnCue · 群聊试映室

**先试着说，再决定要不要发。**

> **当前 main：0.4.6 开发检查点，尚非最终验收/上架版。** 已保存响应式布局、解析与重试修复及49项原生受控测试；模型事实边界、完整视觉/持久化回归和同版演示仍待完成。见[检查点说明](<evidence/submission/CHECKPOINT-0.4.6.md>)。下方展示图与旧视频均为历史版本，不作为本版验收证据。

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

队伍 **OnCue** · 成员 **YCOROY** · 赛道 **OctoSense 即时消息 · Rinx**。

参赛作品是 [`oncue/bundle/`](oncue/bundle/)：一个在 OctoSense / Rinx 宿主内运行的
**OctoScript 小程序**，按 App Hub 流程准备发布；当前尚未官方收录。

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

开发复现使用[未签名副本工具](<oncue/tools/prepare_dev_bundle.py>)生成独立副本，不直接导入仓库里的签名包。然后在已登录的 Rinx 中打开 **Discover → Mini apps → Import an app**，
填入副本路径与**你自己的测试房间**，Review 后 Run。完整命令见[检查点复现说明](<evidence/submission/CHECKPOINT-0.4.6.md>)；登录与模型配置均留在宿主。

<p align="center">
  <img src="evidence/screenshots/rinx-flow.png" width="100%"
       alt="左侧：Import an app 表单；右侧：应用在 Rinx 宿主内运行">
</p>

<p align="center">
  <sub>左：Developer 入口填入包路径与测试房间 · 右：Review 通过后在宿主内运行</sub>
</p>

当前检查点已在 Rinx 外窗 **412×892** 与 **990×613** 下逐页读取真实三路线与摘要；实际应用嵌入区分别为 **376×727** 与 **954×448**。完整视觉与全部交互验收尚未结束。

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
- [更多截图](evidence/screenshots/) — 双视口实机截图、Rinx 装载流程与字素边界细节
- [App Hub 材料](evidence/apphub/) — `hub check` 输出与 `hub scan` 七问回答
- [Apache License 2.0](oncue/LICENSE)
