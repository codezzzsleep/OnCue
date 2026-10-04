# 验证摘要 — OnCue 0.4.7

## 版本与包

- 版本 0.4.7，`oncue.dev` 签名（2026-10-04 重签）；`hub check --publisher-key` 通过。
- manifest 的 `bundle_blake3` 是**全包目录摘要**：各文件的相对路径、长度与内容依次入哈希（不含 manifest.json），由 `hub stamp` 写入、每次 `hub check` 重算——不是单个 `main.splash` 的哈希；验证digest 用 `hub check` 或 `oncue/tools/stamp_bundle.py --check`。
- 生产入口 SHA256 `4b2fd02fb3e893dd15214a22f7ce173eed3d11c5cab1cbda4c72ef8038e472b5`，65 个生产函数。
- 钉定宿主：OctoSense `6c4746f` + Rinx `c515e5f` + octos `fe08d8e6`，宿主二进制 SHA256 `87ed4dccd14bac51222f40c38d4db086911790786b688a68a503002ada64ba25`。平台 Linux aarch64，X11 + 软件渲染；赛事服务器 `matrix.rinx.chat`，模型 MiniMax-M2.7。

## 受控测试：146 项

8 套断言在真实 card-host OctoScript VM 中执行，宿主回调受控注入；生产函数逐字节保留，生成器校验哈希。源码与夹具哈希同当前发布包一致，[原始 run 与逐条结果](<../evidence/checkpoint-0.4.7-recovered/README.md>)可复核。

| 套件 | 断言 | 覆盖 |
| --- | --- | --- |
| parser | 30 | 七节协议、包装与行末分隔、歧义混合拒绝、无分隔符标记切分 |
| pagination | 15 | 字符守恒、组合字符/emoji/CRLF、长文本跨页 |
| retry | 8 | 格式重试一次、停止/编辑/新请求隔离、服务错误不重试 |
| deadline | 6 | 完整 90 秒期限（含 session 与重试），实测超时 90.0476 秒 |
| playback | 18 | 1.4 秒定时器、暂停/续播/重播、切路线旧计时器隔离 |
| storage | 14 | 真实 jail 写读、空白不覆盖、三份文件字节哈希 |
| grounding | 51 | 原文摘录、数字/编号核查、承诺词门禁 |
| envelope | 4 | `data:nil` 畸形回调不抛错、不发布结果 |

## 真实宿主验收

钉定宿主上的原生输入驱动，逐页读取内容核对（非仅“按钮有响应”）。

| 项目 | 990×613 | 412×892 |
| --- | --- | --- |
| 授权房间读取（12 条） | 通过 | 通过 |
| 长消息分页 | 通过 | 通过 |
| 真实助手回合（七节协议） | 通过 | 通过 |
| 三路线逐页阅读 | 通过 | 通过 |
| 播放/暂停/切路线隔离 | 通过 | 通过 |
| 草稿 A/B 保存与独立回读 | 通过 | 通过 |
| 关闭重开自动恢复 | 通过 | 通过 |
| 无绑定房间拒绝 | 通过（另一账号 `Allowed room: None`） | — |

记录：`build/current/` 动作与截图；演示录屏见 [DEMO-0.4.7](<../evidence/submission/DEMO-0.4.7.md>)。

## 2026-10-04 复验

修复开发工具后，用本机钉定宿主对 0.4.7 开发副本重新执行四模式验收，全部通过：真实读房（12 条）、真实 MiniMax-M2.7 回合、三路线与摘要逐页读取、播放计时推进（A/B 两路线）、草稿 A/B 字节回读、Back 关闭重导入后草稿自动恢复。逐项动作、状态与截图在 `build/validation-2026-10-04/{routes,playback,draft,reopen}/`。

环境说明：宿主重启后复用钉定组合；octos 内核数据目录换用干净目录并恢复 `_main` profile（旧目录的宿主 token 状态与新实例不匹配，会导致 `peer_host_token_mismatch`）。

## 未验证

- 语义级事实核验（形式核查通过不代表内容真实）
- macOS / Windows / 移动端
- 接收者授权链路的完整展示（deny、租约到期）
- App Hub 上架后的商店安装路径
