# 新 digest 冒烟（`2673402b…`）—— 不使用旧 `f1ef1dc1` 证据

按 AI1 #349：合入两项修复后，必须用**同一个新 digest** 重跑冒烟，不得拿旧包证据冒充。

## 已跑（card-host，真实渲染）

| 项 | 412×892 | 990×613 |
| --- | --- | --- |
| 启动接纳 | admitted ✓ | admitted ✓ |
| 草稿 A/B 写入 | take_a=18 | take_a=18 |
| **草稿 A/B 重开**（同一 app-data 第二次启动） | 读回 take_a=18、`ab_mode=2`、`take_read=0` ✓ | 同左 ✓ |
| 摘要（新修复） | `mode=1 sum_len=63 ws_pages=3` ✓ | 同左 ✓ |
| 截图 | `newsig-smoke-412x892.png` | `newsig-smoke-990x613.png` |

## 尚未跑（需要 Rinx 宿主环境，进行中）

- 真实 room 12 条（`matrix.read_messages`）
- 真实七块 Agent 回合（`octos.turn.start`）
- 停止 / 90 秒 / 迟回调隔离

这三项必须在 Rinx 宿主里跑（应用需要 matrix/octos 能力），**我会用同一新 digest 重跑并单独出证据**，
不会引用旧的 `f1ef1dc1` 结果。
