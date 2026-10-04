# 宿主环境与复现（OnCue 0.4.7）

## 钉定组合

| 组件 | 仓库 | 提交 |
| --- | --- | --- |
| OctoSense | `OctoSense-org/OctoSense` | `6c4746f0854b74446f854fdcd32eeb87b5192a81` |
| Rinx（mini-app 宿主） | `hagency-org/Rinx` | `c515e5fc9b6dc22e67f7d551b09fdd793ec685a1` |
| octos（内核） | `octos-org/octos` | `fe08d8e6b3b32e672b0f956a2b692c3c8205b167` |
| App Hub / card-host | `OctoSense-org/OctoSense-App-Hub` | `0f332112f0b5a379c5bb33790df74b21597190cf` |

Rinx 用官方提交、无本地补丁；其中包含房间控件消歧修复 `bb2a4d4`，更早的提交在导入 Review 后会清空房间字段。

## 平台

- 已验证：Linux aarch64（Huawei Cloud EulerOS 2.0，X11 + llvmpipe）。`listing.json` 声明 `linux`。
- 未验证：macOS、Windows、Android、iOS。

## 运行依赖

- 图形会话（X11）与 Matrix 账号（Rinx 登录）。
- `card-host` 可预览样例和跑受控 VM 测试，但不提供 `matrix.*` / `octos.*` 宿主服务；真实房间与助手回合必须在 Rinx 小程序宿主里验。
- 正式安装走 App Hub 商店；开发复现走 Developer 导入（见[原生工作流](NATIVE-WORKFLOW.md)）。

## 新宿主组合（评估记录，非日常基线）

另一套已构建并实测的组合：OctoSense `a3098486` + Rinx `c515e5f`（cargo 依赖覆盖，非源码补丁）+ octos `056173e8`。真实读房、助手回合、三路线与草稿通过；新内核对多实例要求独立 `OCTOS_APP_CORE_DIR`。窄窗（412 宽）合成输入下 `CalloutTooltip` 会遮蔽点击，人工操作无此现象。日常验证仍用上面的钉定组合。

## 测试

8 套 146 项受控断言的历史运行与[恢复原件](<../../evidence/checkpoint-0.4.7-recovered/README.md>)；CI 只跑离线基础设施测试，不跑 VM 断言。
