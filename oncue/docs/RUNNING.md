# 运行说明

## 需要什么

- Rinx，随 OctoSense 一起构建。测试用的版本见下表。
- 比赛服务器 `matrix.rinx.chat` 的账号，和一个有消息的房间。登录走浏览器单点登录。
- 宿主里已经配置好助手。
- 本地构建的 `hub`，用来生成未签名副本。构建方法见 OctoScript-App-Design-Flow 的 QUICKSTART。

card-host 可以打开应用并看内置样例，但它不提供 Matrix 和助手服务，读取群聊和试映只能在 Rinx 里进行。

## 宿主基线

以下版本用于既有0.4.8运行记录；当前版本的实际验证范围以[验证记录](../VERIFICATION.md)为准。

| 组件 | 仓库 | 提交 |
| --- | --- | --- |
| OctoSense | `OctoSense-org/OctoSense` | `6c4746f0854b74446f854fdcd32eeb87b5192a81` |
| Rinx | `hagency-org/Rinx` | `c515e5fc9b6dc22e67f7d551b09fdd793ec685a1` |
| octos | `octos-org/octos` | `fe08d8e6b3b32e672b0f956a2b692c3c8205b167` |
| App Hub / card-host | `OctoSense-org/OctoSense-App-Hub` | `0f332112f0b5a379c5bb33790df74b21597190cf` |

平台是 Linux aarch64（X11，软件渲染）。macOS、Windows、Android、iOS 没有测过。

0.4.8主流程也有 OctoSense `a3098486` + octos `056173e8` 的历史运行记录。

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

1. 打开后进入本地样例。点「载入群聊」读取授权房间，最多12条消息；需要宿主提供稳定房间ID。
2. 展开下方参考消息，核对并勾选本次范围。写台词，选澄清、拒绝或推动下一步，可补充边界。
3. 在数据范围卡允许当前范围内的试映与修订。点击「试映下一幕」，直接比较三句；每次请求总限90秒，含至多一次修复。
4. 点击「选用这句」或当前路线的「用这句」放入草稿。可直接编辑，也可填写修订要求、准备候选，核对后点击「应用修订」。
5. 「保留这句 / 存 A / 存 B」保存到当前房间，状态确认逐字回读后才完成。可切换原句/当前对照及A/B对照。
6. 重新打开后先载入同一房间再取回草稿。旧来源不自动当作当前消息，应重新核对。
7. 展开「本地草稿管理 / 删除 / 旧版迁移」可重新读取存储、删除本房间记录、手动复制旧版主稿/A/B或删除旧版文件。删除30秒确认，编辑变化后须重新确认。

未保存编辑切换房间会要求先保存或明确放弃。文件损坏、未知版本或其他窗口改写时停写；先关闭其他写入窗口并重新读取，无法恢复时只有明确清空全部新格式记录，不会自动覆盖空数据。

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
