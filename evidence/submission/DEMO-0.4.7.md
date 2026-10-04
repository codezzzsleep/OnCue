# 初赛演示 — OnCue 0.4.7

- **提交视频**：[oncue-demo-0.4.7-subtitled.mp4](<../demo/oncue-demo-0.4.7-subtitled.mp4>) — **90 秒**，992×614，H.264，中文字幕解说，符合 2–3 分钟要求。
- **原始未字幕版**：[oncue-demo-047-v2-raw.mp4](<../demo/oncue-demo-047-v2-raw.mp4>)（同一次录制，字节不同的仅字幕轨）。
- **字幕时间轴**：[oncue-demo-047-v2.srt](<../demo/oncue-demo-047-v2.srt>)，由驱动日志逐事件生成：[oncue-demo-047-v2-narration.json](<../demo/oncue-demo-047-v2-narration.json>)。
- 2026-10-04 录制于钉定宿主（OctoSense `6c4746f` + Rinx `c515e5f`，Linux aarch64），赛事服务器 `matrix.rinx.chat`，模型 MiniMax-M2.7。全部操作是真实原生输入，模型等待未加速。

## 视频内容

| 时间 | 内容 |
| --- | --- |
| 0:00–0:15 | Developer 导入：填包路径与房间 → Review 显示六项服务与 Allowed room → Run 授权 |
| 0:15–0:22 | 载入群聊：真实房间 12 条消息按编号载入，逐条翻看 |
| 0:22–0:52 | 试映下一幕：输入台词，真实助手回合（等待约 30 秒未剪） |
| 0:52–1:00 | 原文摘录：助手只选编号，应用取回原文逐字展示 |
| 1:00–1:14 | 三路线：A 顺着这句逐句播放/暂停，切 B 换问法 |
| 1:14–1:30 | 草稿：建议放入草稿修改，存 A、存 B（写入回读确认），清空后取回 A |

## 历史版本

[oncue-demo-047.mp4](<../demo/oncue-demo-047.mp4>)（184.7 秒，无字幕）为 10 月 3 日录制的上一版，保留溯源；正式提交以上方 90 秒字幕版为准。更早的 0.4.4 录屏（179 秒）在[同目录](<../demo/oncue-demo-2min59.mp4>)。

## 录制方式

驱动脚本 `/tmp/record_demo2.py`（基于 `oncue/tools/` 的 bridge）：`ffmpeg -f x11grab` 抓 Rinx 窗口（990×613 外窗），每个动作是真实输入事件；字幕由事件时间戳生成后烧录。失败与接收者授权不在本视频范围，证据见[验证摘要](../../oncue/VERIFICATION.md)。
