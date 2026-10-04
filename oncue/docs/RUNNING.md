# 运行说明

## 需要什么

- Rinx，随 OctoSense 一起构建。测试用的版本见下表。
- 比赛服务器 `matrix.rinx.chat` 的账号，和一个有消息的房间。登录走浏览器单点登录。
- 宿主里已经配置好助手。
- 本地构建的 `hub`，用来生成未签名副本。构建方法见 OctoScript-App-Design-Flow 的 QUICKSTART。

card-host 可以打开应用并看内置样例，但它不提供 Matrix 和助手服务，读取群聊和试映只能在 Rinx 里进行。

## 测试用的版本

| 组件 | 仓库 | 提交 |
| --- | --- | --- |
| OctoSense | `OctoSense-org/OctoSense` | `6c4746f0854b74446f854fdcd32eeb87b5192a81` |
| Rinx | `hagency-org/Rinx` | `c515e5fc9b6dc22e67f7d551b09fdd793ec685a1` |
| octos | `octos-org/octos` | `fe08d8e6b3b32e672b0f956a2b692c3c8205b167` |
| App Hub / card-host | `OctoSense-org/OctoSense-App-Hub` | `0f332112f0b5a379c5bb33790df74b21597190cf` |

平台是 Linux aarch64（X11，软件渲染）。macOS、Windows、Android、iOS 没有测过。

主流程也在 OctoSense `a3098486` + octos `056173e8` 上跑通过。

## 本地导入

1. 生成未签名副本。Rinx 的本地导入不接受已签名的包。

   ```sh
   export OCTO_HUB=/path/to/OctoSense-App-Hub/target/release/hub
   DEV_ROOT="$(mktemp -d)"
   python3 oncue/tools/prepare_dev_bundle.py "${DEV_ROOT}/bundle" --hub "$OCTO_HUB"
   ```

2. 在 Rinx 里打开 **Discover → Mini apps → Import an app**。包路径填上一步打印出的目录，房间填你的 Matrix 房间 ID。
3. 点 **Review bundle**。面板会列出应用名、版本、六项服务和 Allowed room。
4. 点 **Run**。每次打开都要重新授权，点 Back 关闭后授权失效。

## 使用

1. 打开后显示的是内置样例。点「载入群聊」读取你授权的房间，最多 12 条文本消息。
2. 写一句想说的话，点「试映下一幕」。助手通常在 30 秒左右返回，超过 90 秒应用会停止等待。
3. 点「A 顺着说」「B 换问法」「C 换玩法」查看三种说法，点「相关原文」查看助手选出的相关原文。
4. 点「用这句」把建议放进草稿框，修改后点「存 A」或「存 B」。

## 常见问题

- **点 Review 之后房间号被清空**：Rinx 早于 `bb2a4d4` 的版本有这个问题，升级 Rinx。
- **状态行显示“助手暂时不可用”**：宿主的助手没有启动或没有配置模型，在 OctoSense Settings → Accounts → AI providers 里检查。
- **同一台机器上开两个宿主实例时，第二个实例的助手启动失败**：每个实例要用不同的 `OCTOS_APP_CORE_DIR`。
- **状态行显示“这次打开没有选房间”**：导入时没有填房间。关闭应用，填上房间后重新导入。

## 几个时间限制

| 时间 | 是什么 |
| --- | --- |
| 90 秒 | 应用等待助手回答的上限，包含自动重试 |
| 185 秒 | Rinx 等待一次宿主服务调用的上限 |
| 1 小时 | 一次授权的有效期 |
