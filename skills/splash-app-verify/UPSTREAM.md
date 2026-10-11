# 来源说明

本目录是界面测试技能 splash-app-verify 的第 3 版，用来运行 OnCue 的界面场景（`oncue/tests/ui/`）。

| 项 | 内容 |
| --- | --- |
| 作者 | OnCue 团队。为开发 OnCue 而写，本身是通用的，可以测试任何 Splash 脚本应用 |
| 去向 | 仅作为 OnCue 仓库内的开发测试工具使用；当前没有向 OctoSense App Flow 提交 Skill 的授权 |
| 版本 | 第 3 版，`scripts/uitest.py` 中 `RUNNER_VERSION = 3` |
| 对应补丁 | 基于 App Flow `main` 的 `dd25bdb6a3f9e3757b586447e4b5ca57d412deb5`（2026-10-10）。本目录与补丁里的 `skills/splash-app-verify/` 逐字相同（本文件除外），可以用 `diff -r` 核对 |
| 验证环境 | card-host 用 App Hub `main` 的 `8d3853c9f9b6604fa1d095e7aff20911093e273a` 编译，Splash 运行时是 Octoscript-Makepad `6cf2d90aa33ff4ae603f49c7557f3ecf986207f0` |

文中的相对链接（如 `../../docs/SCRIPT-API.md`）是按 App Flow 仓库的目录结构写的，在本仓库里打不开。请到 App Flow 对应提交阅读：<https://github.com/OctoSense-org/OctoSense-App-Flow/tree/dd25bdb6a3f9e3757b586447e4b5ca57d412deb5/docs>。
