# 来源说明

本目录是界面测试技能 splash-app-verify 的第 3.3 版，用来运行 OnCue 的界面场景（`oncue/tests/ui/`）。

| 项 | 内容 |
| --- | --- |
| 作者 | OnCue 团队。为开发 OnCue 而写，本身是通用的，可以测试任何 Splash 脚本应用 |
| 去向 | 计划作为 PR 提交给 [OctoSense App Flow](https://github.com/OctoSense-org/OctoSense-App-Flow)，放在 `skills/splash-app-verify/`。PR 链接提交后补上；在那之前，App Flow 仓库里没有这个目录 |
| 版本 | 第 3.3 版（App Flow 补丁里的提交 `8d36c646`）。运行器协议版本仍是 `scripts/uitest.py` 中的 `RUNNER_VERSION = 3` |
| 对应补丁 | 基于 App Flow `main` 的 `dd25bdb6a3f9e3757b586447e4b5ca57d412deb5`（2026-10-10）。也能干净地应用到 2026-10-11 的 `main`（`15b1da01`）。本目录与补丁里的 `skills/splash-app-verify/` 逐字相同（本文件除外），可以用 `diff -r` 核对 |
| 验证环境 | card-host 用 App Hub `main` 的 `8d3853c9f9b6604fa1d095e7aff20911093e273a` 编译，Splash 运行时是 Octoscript-Makepad `6cf2d90aa33ff4ae603f49c7557f3ecf986207f0` |

文中的相对链接（如 `../../docs/SCRIPT-API.md`）是按 App Flow 仓库的目录结构写的，在本仓库里打不开。请到 App Flow 对应提交阅读：<https://github.com/OctoSense-org/OctoSense-App-Flow/tree/dd25bdb6a3f9e3757b586447e4b5ca57d412deb5/docs>。
