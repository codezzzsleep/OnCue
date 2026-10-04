# OnCue · 群聊试映室

**先试着说，再决定要不要发。**

OnCue 是一个运行在 Rinx 里的 OctoScript 小程序。在群里发言之前，先把想说的话写在这里：它读取你授权的那个群的最近消息，请助手给出三种不同的说法（顺着说、换个问法、换个玩法），你挑一种改好，存成草稿。**应用自身不发送任何消息。**

演示录屏：[2 分 TODO 秒](evidence/demo/oncue-demo.mp4)

<p align="center">
  <img src="evidence/screenshots/hero.png" width="100%"
       alt="OnCue 在宽窗口和窄窗口下的界面">
</p>
<p align="center">
  <sub>宽窗口和窄窗口下的界面</sub>
</p>

提交的应用包在 [`oncue/bundle/`](oncue/bundle/)。

## 一分钟怎么玩

1. 打开内置样例「国庆搭子局」，试一句「明早 9 点出发，住一晚」。群里有人说过中午才能走，也有人想当天回来。
2. 改成「中午出发、当天回来，先核实预算」，重新试映，比较三个不同的接法。
3. 选「换个玩法」，把讨论变成半日旅行盲盒：每人给一个想做的事，再找条件的交集。
4. 播放、暂停或逐句查看假设对白，把喜欢的建议放进草稿；改两种写法，分别存 A、存 B，再取回对照。

<p align="center">
  <img src="evidence/screenshots/app-row.png" width="62%"
       alt="左侧：打开样例并试映下一幕；右侧：逐句播放假设对白">
</p>
<p align="center">
  <sub>左：打开内置样例、回看群聊消息 · 右：逐句播放「顺着这句」的假设对白</sub>
</p>

三种说法是助手的假设，不是群友的真实回复。

## 在 Rinx 里运行

**从 App Hub 安装**

在 Rinx 的 **Discover → Mini apps** 进入 App Hub 应用库，找到 OnCue 后 **Add** 安装、**Open** 打开；打开时宿主会列出应用申请的六项服务和所选房间，确认后为本次运行授权。上架申请：`TODO(作者)：最终版本对应的 issue 链接`。

**本地导入**

Rinx 的本地导入不接受已签名的包，先生成一份未签名副本：

```sh
# OCTO_HUB 指向本地构建的 hub，可执行文件的构建方法见 OctoScript-App-Design-Flow 的 QUICKSTART
export OCTO_HUB=/path/to/OctoSense-App-Hub/target/release/hub
DEV_ROOT="$(mktemp -d)"
python3 oncue/tools/prepare_dev_bundle.py "${DEV_ROOT}/bundle" --hub "$OCTO_HUB"
```

1. Rinx 里打开 **Discover → Mini apps → Import an app**。
2. 包路径填上一步打印出的目录，房间填你自己的 Matrix 房间 ID。
3. **Review** 核对名称、版本、六项服务与 Allowed room → **Run**。

每次打开都要重新授权，关闭后授权失效。完整步骤见[运行说明](oncue/docs/RUNNING.md)。

## 数据与权限

- **申请的六项能力**：`storage`（草稿 A/B）、`matrix.room_info` 与 `matrix.read_messages`（载入授权房间消息）、`octos.session.open` / `octos.turn.start` / `octos.turn.interrupt`（助手试映与停止）。
- **发给助手的内容**：点「试映下一幕」时，已载入的全部消息（编号、发送者、正文）和你的台词会交给宿主配置的助手。应用自己不联网，但宿主的助手可能是远程服务。详见[数据说明](oncue/PRIVACY.md)。
- **草稿**按账号保存在应用自己的存储目录里。
- **防编造**：「相关原文」由应用按编号从群聊里原样取出，不经过助手改写。助手的回答里如果出现群聊和你的台词里都没有的数字、不存在的消息编号，或者「已同意」「已订票」这类说法，整份回答会被丢弃并重试一次。

## 验证

- **包检查**：`hub check oncue/bundle --publisher-key oncue.dev=50578fd7e0d8ac51a1e9e590835427ce8e71f46dba491860c75ae4e7c8c78042` 通过。
- **逻辑测试**：8 套共 146 项断言。测试把 `main.splash` 的函数原样放进 card-host 的脚本虚拟机运行，宿主服务的返回值由测试脚本模拟。覆盖回答格式解析、重试、90 秒超时、播放计时、存储和来源检查。结果文件和复核命令见[测试说明](oncue/tests/README.md)。CI 只跑测试工具自身的 91 项单元测试，不包含这 146 项。
- **实机**：在 Rinx（OctoSense `6c4746f` + Rinx `c515e5f`，Linux aarch64）里，用比赛服务器 `matrix.rinx.chat` 上的房间和 MiniMax-M2.7 走通了读取群聊、试映、播放、保存草稿和关闭重开。宽窗口（990×613）和窄窗口（412×892）各测一遍。逐项结果见[验证记录](oncue/VERIFICATION.md)。

## 尚未验证

- 助手的回答是否符合事实。应用只检查编号、数字和几个固定用语。
- macOS、Windows 和移动端。目前只在 Linux aarch64 上运行过。
- 用户拒绝授权、授权到期时应用的表现。

## 文档

- [产品说明](oncue/BRIEF.md)
- [数据说明](oncue/PRIVACY.md)
- [运行说明](oncue/docs/RUNNING.md)
- [验证记录](oncue/VERIFICATION.md)
- [测试说明](oncue/tests/README.md)
- [演示录屏说明](evidence/demo/README.md)
- [更新记录](CHANGELOG.md)
- [App Hub 审核七问](build/REVIEW-ANSWERS.md)
- [Apache License 2.0](LICENSE)
