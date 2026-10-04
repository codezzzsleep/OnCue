# 验证记录

本次验证日期：2026-10-04。包版本 `0.4.8`，内容对应提交 `4b67d9e`。

## 测试环境

| 项 | 值 |
| --- | --- |
| OctoSense | `6c4746f` |
| Rinx | `c515e5f`，官方提交，没有本地补丁 |
| octos 内核 | `fe08d8e6` |
| App Hub / card-host | `0f332112` |
| 平台 | Linux aarch64，X11，软件渲染 |
| Matrix 服务器 | `matrix.rinx.chat`（比赛服务器） |
| 模型 | MiniMax-M2.7，由宿主配置 |

## 包检查

发布包已签名，`hub check oncue/bundle --publisher-key oncue.dev=50578fd7e0d8ac51a1e9e590835427ce8e71f46dba491860c75ae4e7c8c78042` 通过。

只移除签名的开发副本通过 `hub check --allow-unsigned`，用于 card-host 和 Rinx 的本地导入。

## 逻辑测试

8 套共 149 项断言。测试把 `main.splash` 的 64 个函数原样放进测试包，在 card-host 的脚本虚拟机里运行。宿主服务的返回值由测试脚本模拟，不调用模型。

| 套件 | 断言数 | 测什么 |
| --- | --- | --- |
| parser | 30 | 七段格式的解析，各种分隔写法，缺段、重复、乱序时拒绝 |
| pagination | 15 | 长文本分页不丢字，不切断 emoji 和组合字符 |
| retry | 9 | 格式不对时重试一次；停止、改台词、发新请求后，旧回答不生效 |
| deadline | 6 | 90 秒超时，包含打开会话和重试的时间 |
| playback | 18 | 逐句播放的计时，暂停、继续、重播，切换路线 |
| storage | 14 | 草稿写入和读取，空白内容不覆盖 |
| grounding | 53 | 相关原文的取出，编号、数字、固定用语的检查 |
| envelope | 4 | 宿主返回的数据结构异常时不报错、不显示结果 |

结果文件和复核命令在 [evidence/logic-tests](../evidence/logic-tests/README.md)，重跑方法在[测试说明](tests/README.md)。

这些测试对应的 `main.splash` SHA-256：`71c9fe59b92a12755d1810ba70e2278e7b092235c13efcdd9ce63bcab3961031`。改了 `main.splash` 就要重跑并更新这一行。

## 实机检查

2026-10-04，用脚本在 Rinx 里模拟点击和输入。表头是实测 Rinx 框架尺寸；小程序可视区域分别为 954×448 和 376×727。

| 检查 | 990×613 | 412×892 |
| --- | --- | --- |
| 读取授权房间的 12 条消息 | 通过 | 通过 |
| 长消息在列表里自动换行 | 通过 | 通过 |
| 助手按七段格式返回三种说法 | 通过 | 通过 |
| 三种说法和相关原文都能读完 | 通过 | 通过 |
| 播放、暂停、切换路线 | 通过 | 未判定：三次尝试都因暂停后剩余行数不足以区分播放与计时而停在检查处；不记通过也不记失败 |
| 草稿 A、B 保存后读取一致 | 通过 | 通过 |
| 关闭后重新打开，草稿还在 | 通过 | 通过 |

四种验收模式均不传 `--size`；窄屏直接指定 412×892。几何检查为零容差。

默认窗口下小程序可视区域是 954×448，三种说法和草稿都在第一屏内。

连续 10 次真实试映：7 次首轮通过，2 次自动重试后通过，1 次失败（该次助手首轮与重试的回答都没通过应用检查）。耗时 15.6–41.3 秒。结果汇总见[本轮实测记录](../evidence/host-checks/design3-results.json)。

## 授权和失败状态

| 检查 | 结果 | 测试版本 | 截图 |
| --- | --- | --- | --- |
| 打开时没有选房间，点「载入群聊」 | 显示“这次打开没有选房间。请关闭应用，导入时填上房间再打开。” | 0.4.7（271e79d） | [截图](../evidence/screenshots/design3-no-room.png) |
| 用另一个账号打开同一个应用 | 授权面板显示 `Allowed room: None`，没有沿用第一个账号的房间授权 | 0.4.4 | [截图](../evidence/screenshots/recipient-2-own-consent.png) |
| 另一个账号点「取 A」 | 显示“版本 A 还没有内容”，读不到第一个账号的草稿 | 0.4.4 | [截图](../evidence/screenshots/recipient-4-draft-isolated.png) |
| 点 Back | 应用关闭，回到小程序列表，同一 Rinx 进程继续运行 | 0.4.7（271e79d） | [截图](../evidence/screenshots/design3-back-closed.png) |
| 关闭后重新导入 | 编辑框与保存的草稿逐字节一致；未重启宿主 | 0.4.7（271e79d） | [截图](../evidence/screenshots/design3-draft-after-reopen.png) |
| 在 card-host 里点「载入群聊」 | 显示“当前宿主不提供群聊服务，请在 Rinx 里打开。” | 0.4.7（271e79d） | [截图](../evidence/screenshots/design3-card-host-room-unavailable.png) |

## 未验证

- 助手的回答是否符合事实。应用只检查编号、数字和几个固定用语。
- macOS、Windows、移动端。
- 用户在授权面板点拒绝、授权满一小时到期、回答进行中关闭应用。
- 从 App Hub 商店安装。
- 当前内容的跨账号授权和草稿隔离：本轮没有可供核对的第二个已登录宿主，因此上表两项保留 0.4.4 的历史结果。
