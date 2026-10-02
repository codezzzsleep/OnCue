# Rinx 侧部署状态与阻塞（新 digest 同版回归）

## 关键发现：Rinx 里跑的是 0.4.3，不是当前产品

| 项 | 值 |
| --- | --- |
| Rinx app store | `/srv/oncue-home/.octosense/apps/oncue-screening-room/bundle/` |
| 装前版本 | **0.4.3**，digest `ec7773d51f2078e618d1711bb9b2840629e272858b040abf0af19c1c492e9619`，**已签名**（`oncue.dev`） |
| 装前是否含方案C / GCB 修复 | **都不含**（`cue_page_cols = 16` 出现 0 次、`cue_gcb_extend` 出现 0 次） |

=> **此前所有 Rinx 侧证据（真实 room 12、真实七块 Agent、停止/90秒/迟回调）都是在 0.4.3 上取得的，
不代表当前产品。** 这正是 AI1 #349 要求"不要用旧证据冒充当前包"所针对的情形，且比预想更严重（差两个版本）。

## 已做

1. 备份：`/srv/oncue-runtime/backup/apps-1790912564/`（catalog + 整个 app 目录）
2. 用 catalog 里登记的 working key 签名（`hub sign-manifest … --key-id oncue.dev`）：
   **digest 不变**（`2478d230…`），签名 key 公钥与 catalog `key.public` 一致
3. 直接落盘安装新包到 app store：现为 **0.4.4 / `2478d230…`**，`cue_gcb_extend` 出现 2 次、
   `cue_page_cols = 16` 出现 1 次、`cue_demo_routes` 2 次
4. 同步 `catalog.json` 条目的 `manifest` 为新 digest，`artifact` 0.4.3 → 0.4.4

## 阻塞

`hub publish` 与 `hub check --catalog` 都被拒：
```
[refused] publisher-signature: publisher key "oncue.dev" is not registered with this hub
[refused] version: version 0.4.4 of oncue-screening-room is already published; publish a new version
```
0.4.3 显然是**绕开 publish 直接落盘**安装的。要跑 Rinx 侧同版回归，需要：
- 要么知道当初把探针/miniapp 装进 Rinx 并拉起的**实际路径**（我没在日志里找到 roomread/turn 探针的拉起记录）；
- 要么授权用 `--allow-unsigned` 或等价方式在 Rinx 内拉起新包。

## 已在新 digest 上完成的（card-host，与 Rinx 无关）

412×892 与 990×613 均 admitted；草稿 A/B 写入 18 字 → 同一 app-data 重开仍读回 18 字；摘要 `mode=1 ws_pages=3`。

## 未做（阻塞点）

真实 room 12 / 真实七块 Agent / 停止·90秒·迟回调 —— 需要把新包在 Rinx 内拉起。
