# 宿主环境与复现（OnCue 0.4.4）

本文件给出评审复现所需的**宿主版本、支持平台与依赖**。

## 1. 宿主与组件（钉定提交）

| 组件 | 仓库 | 钉定提交 |
| --- | --- | --- |
| OctoSense | `OctoSense-org/OctoSense` | `6c4746f0854b74446f854fdcd32eeb87b5192a81` |
| Rinx（mini-app 宿主） | `hagency-org/Rinx` | **`c515e5fc9b6dc22e67f7d551b09fdd793ec685a1`**（官方 main，见下） |
| octos（内核） | `octos-org/octos` | `fe08d8e6b3b32e672b0f956a2b692c3c8205b167` |
| App Hub | `OctoSense-org/OctoSense-App-Hub` | `0f332112f0b5a379c5bb33790df74b21597190cf` |

> **关于 Rinx 版本**：本作品**使用官方 Rinx `main`（`c515e5fc9b6d`），未做任何源码改动**。
> 其中 room 控件消歧由上游 PR #48 `bb2a4d4df7d0`（2026-10-01 合并）提供 —— 该 PR 修掉了
> mini app import 面板里 `ids!(room)` 的歧义。**比它更早的 Rinx 会出现"Review 后房间被清空"的问题**，
> 因此本作品要求 **Rinx ≥ `bb2a4d4`**；本次交付在官方 `c515e5fc9b6d` 上构建并实测。
> 上游在 `0879548`(v1.0.0) 与 `c515e5fc` 之间还含 `5a9e2af2`（对齐 OctoSense 当前钉定的
> makepad / App Hub / octos）等提交。

## 2. 支持平台

- 已验证：**Linux（aarch64）**，Huawei Cloud EulerOS 2.0，X11 + 软件渲染（llvmpipe）。
- `listing.json` 的 `platforms` 据此声明为 `["linux"]`。
- 未在其他平台验证。

## 3. 运行依赖

- 图形会话（X11）与一个可用的 Matrix 账号（Rinx 登录用）。
- `card-host`（App Hub 自带）可用于**本地功能预览**；但它**不提供任何宿主服务**
  （`matrix.*` / `octos.*` 都不可用），因此**不能**用它验证房间读取或助手回合。
- 真实房间读取与助手回合需要 **Rinx 的 mini-app 宿主**（`matrix.*` 仅由它提供；
  `octos.*` 由它或托管内核的 OctoSense shell 提供）。

## 4. 如何装载与运行

见 [原生工作流](NATIVE-WORKFLOW.md)：在已登录的 Rinx 里
`Discover → Mini apps → Import an app`，填本包路径与你自己的测试房间，Review 后 Run。

## 5. 包摘要自检（可选）

```bash
python3 oncue/tools/stamp_bundle.py oncue/bundle --check
```
只读校验资源摘要是否与 manifest 声明一致；**不验签、不替代 `hub check`、不证明运行通过**。
