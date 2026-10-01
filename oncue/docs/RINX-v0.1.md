# OnCue · 群聊试映室 v0.1

队伍：OnCue。成员：YCOROY。赛道：OctoSense 即时消息 · Rinx。

把当前群聊存成一个“剧情现场”，私下试一句话，展开“顺着这句 / 换个问法 / 换个玩法”
三条路线，再把喜欢的台词放进自己的草稿。

## 已制作的部分

- bundle/main.splash：Rinx OctoScript 小程序初版。
- 虚构群聊与标明为预设的三条样例路线，可在没有模型服务时体验。
- 通过 matrix.room_info、matrix.read_messages 读取本次附加并授权的群聊。
- 通过 octos.session.open、octos.turn.start 请求宿主的 Agent。
- 原消息编号、假设对白、可编辑草稿、账号内的本地草稿存储。
- 输入或场景改变时撤销旧剧本，丢弃过期响应。
- 原生等待期间可停止；读取或模型回合超过 90 秒会结束等待。每次请求使用新修订号，旧计时器不会取消后续试映。

账号和模型都在 Rinx / OctoSense 宿主中配置。
本包没有申请消息发送能力。草稿保存后可由用户自行带回群聊。

## 当前验证范围

详见 VERIFICATION.md。浏览器概念样例与原生小程序代码是两个交付层次。
没有在原生 Rinx / Makepad 环境启动，也没有经过 hub check / hub scan；
因此本包不能称为已上架、已通过准入或原生运行已验证的作品。
真实消息、真实模型回合与原生布局需要下一步联调。
新增停止按钮、超时反馈及连续请求时的计时器隔离同样等待原生实测。

## 在 Rinx 中尝试开发包

先使用包含 OctoScript 小程序开发入口的 Rinx / OctoSense 版本。

1. 在 Rinx 登录自己的 Matrix 账号。
2. 桌面端打开 Mini apps；手机端打开 Discover → Mini apps。
3. 选择 Import an app，或 App Hub → Developer。
4. 输入解压后 bundle/ 的绝对路径，选择 Review bundle，查看申请的能力。
5. 样例舞台可以不附加群聊。测试真实消息时，在宿主中选择一个自己的测试群聊。
6. 选择 Run，先点击“试映下一幕”体验预设，再点“载入群聊”。
7. 真实试映需要宿主 Agent 已配置好模型。若服务不可用，小程序会显示错误。

导入的是 bundle/ 文件夹。修改后须重新计算摘要并再次 Review；
正在运行的包是宿主冻结的副本，修改原目录不会改变它。

## 修改后的重新封装

优先使用 Rinx 官方工具：

    cargo build --manifest-path /path/to/Rinx/tools/miniapp-package/Cargo.toml
    /path/to/Rinx/tools/miniapp-package/target/debug/rinx-miniapp-package /path/to/oncue/bundle

本项目也提供按官方算法实现的 Python 摘要工具：

    python -m pip install blake3
    python tools/stamp_bundle.py bundle

摘要一致只代表内容摘要正确，不能替代原生运行检查或 App Hub 准入、扫描与人工审核。

## 初赛前还要完成

- 在实际 Rinx 版本上跑通样例、真实消息读取、Agent 试映和草稿保存。
- 截取真实原生截图，录制“改一句台词，展开不同路线”的短演示。
- 根据实际表现调整 UI、失败反馈和模型输出协议。
- 准备公开源码仓库、真实发布者信息、支持方式与隐私说明。
- 补齐 listing.json、图标和真实截图，运行官方 hub check 与 hub scan。
- 按主办方提交要求与 App Hub 发布契约提交；本包尚未执行这些外部操作。

## 官方依据

- [Rinx 小程序示例](https://github.com/upstreamlabs/Rinx/tree/main/examples/miniapps)
- [Matrix 与 Octos 服务](https://github.com/upstreamlabs/Rinx/blob/main/docs/adr/0005-octoscript-miniapps-matrix-octos.md)
- [共享 App Hub 分发](https://github.com/upstreamlabs/Rinx/blob/main/docs/adr/0006-shared-app-hub-miniapps.md)
- [OctoScript API](https://github.com/OctoSense-org/OctoScript-App-Design-Flow/blob/main/docs/SCRIPT-API.md)
- [App Hub 发布契约](https://github.com/OctoSense-org/OctoSense-App-Hub/blob/main/docs/PUBLISHING.md)

## 许可证

初版代码采用 Apache License 2.0，见 LICENSE。
