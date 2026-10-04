# OnCue · 群聊试映室

**先试着说，再决定要不要发。**

OnCue 是一个运行在 Rinx 里的 OctoScript 小程序：把还没发出去的一句话放进私人排练场，读取授权房间的消息作为线索，请设备助手生成三个不同方向的假设下一幕——顺着这句、换个问法、换个玩法。逐句播放查看，把喜欢的建议存成草稿 A/B 对照修改。**应用自身不发送任何消息。**

<p align="center">
  <img src="evidence/screenshots/hero.png" width="100%"
       alt="OnCue 在 990×613 与 412×892 两个视口下的界面">
</p>
<p align="center">
  <sub>同一应用在 <b>990×613</b>（宽屏）与 <b>412×892</b>（窄屏）两个视口下的排版</sub>
</p>

参赛作品是 [`oncue/bundle/`](oncue/bundle/)（manifest、listing、入口、图标、两张真实截图）。

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

**途径一：App Hub（正式途径）**

在 Rinx 的 **Discover → Mini apps** 进入 App Hub 应用库，找到 OnCue 后 **Add** 安装、**Open** 打开；打开时宿主会列出应用申请的六项服务和所选房间，确认后为本次运行授权。上架审核中（[App Hub #57](https://github.com/OctoSense-org/OctoSense-App-Hub/issues/57)）。

**途径二：本地导入（开发/复现途径）**

Rinx 的 Developer 导入按设计拒绝带签名的包，所以先生成未签名副本：

```sh
. /root/hackthon/refs/octo-env.sh
DEV_ROOT="$(mktemp -d /tmp/oncue-dev.XXXXXX)"
python3 oncue/tools/prepare_dev_bundle.py "${DEV_ROOT}/bundle" --hub "$OCTO_HUB"
```

1. Rinx 里打开 **Discover → Mini apps → Import an app**。
2. 包路径填打印出的目录（destination 本身就是包目录，直接含 `manifest.json`，不要再加一层 `bundle`）；房间填你自己的 Matrix 房间 ID。
3. **Review** 核对名称、版本、六项服务与 Allowed room → **Run**。

每次打开都要为当前账号和所选房间重新授权，关闭即撤销。详见[原生工作流](oncue/docs/NATIVE-WORKFLOW.md)。

## 数据与权限

- **不发送任何消息**：没有发送能力，产物是本地草稿。
- **六项能力**对应六个真实功能：`storage`（草稿 A/B）、`matrix.room_info` 与 `matrix.read_messages`（载入授权房间消息）、`octos.session.open` / `octos.turn.start` / `octos.turn.interrupt`（助手试映与停止）。
- **试映的数据范围**：点击「试映下一幕」时，全部已载入消息的编号、发送者、正文和你的台词会交给宿主配置的助手；应用本身不直连网络（`network.hosts` 为空），但宿主助手可能是远程服务——见[数据说明](oncue/PRIVACY.md)。
- 草稿按账号 + 应用存储；原文摘录逐字取回，数字与编号引用有界核查——这些是形式核查，语义真实性仍需使用者判断。

## 验证

- **包检查**：`hub check --publisher-key` 通过（0.4.7，`oncue.dev` 签名）。
- **受控测试**：8 套共 146 项断言在真实 card-host OctoScript VM 中通过，覆盖协议解析、分页、重试、90 秒期限、播放计时、存储字节、来源核查与畸形回调；源码哈希与发布包一致，[原始证据](evidence/checkpoint-0.4.7-recovered/README.md)可逐套复核。146 项 VM 断言与 91 项工具离线单测互不重叠——CI 只跑后者。
- **真实宿主**：在钉定宿主（OctoSense `6c4746f` + Rinx `c515e5f`）上完成授权读房、真实助手回合、三路线逐页阅读、播放控制、草稿保存恢复与关闭重开，宽窗 990×613 与窄窗 412×892 两个尺寸；逐条记录见[验证摘要](oncue/VERIFICATION.md)。

## 尚未验证

语义级事实核验（形式核查通过不代表内容真实）、其他平台（macOS/Windows/移动端）、接收者授权链路的完整展示（deny、租约到期）。应用运行平台为 Linux aarch64。

## 文档

- [产品说明](oncue/PRODUCT.md) — 流程与状态反馈
- [数据说明](oncue/PRIVACY.md) — 数据来源、模型请求与本地存储
- [原生工作流](oncue/docs/NATIVE-WORKFLOW.md) — 装载、运行与记录步骤
- [宿主环境与复现](oncue/docs/DEPENDENCIES.md) — 钉定版本组合与平台
- [验证摘要](oncue/VERIFICATION.md) — 测试矩阵与证据索引
- [演示录屏](evidence/demo/oncue-demo-0.4.7-subtitled.mp4) — 90 秒实录配中文字幕，[时间轴与解说](evidence/submission/DEMO-0.4.7.md)
- [七问回答](build/REVIEW-ANSWERS.md) — `hub scan` 审核材料
- [Apache License 2.0](oncue/LICENSE)
