# 验证记录

版本 **0.5.2，未签名**。验证日期：2026-10-10。

生产入口SHA-256：`5d6db93e931040d10eb926c96a3d47d27f1da8ecee8e2e30af9818cac52c9b8d`（`bundle/main.splash`）。

## 包检查

最新未签名包经 App Hub `main`（`18cd41d`）构建的 `hub` 检查：

```text
oncue-screening-room 0.5.2 — PASSED
  [warning] publisher-signature: unsigned: accountability rests on the hub alone
```

申请能力八项：`storage`、`matrix.room_info`、`matrix.read_messages`、`matrix.account_info`、`matrix.send_message`、`octos.session.open`、`octos.turn.start`、`octos.turn.interrupt`；不直连网络。

## 界面场景测试

用 [splash-app-verify](https://github.com/OctoSense-org/OctoSense-App-Flow/tree/main/skills/splash-app-verify) 在 card-host 里运行 `oncue/tests/ui/` 的界面契约与 38 个场景（5 个场景跑两个尺寸，共 **43 次运行，全部通过**，中位数约 1.5 秒一次，全量约 170 秒；card-host 内存 227–233 MB）。宿主回复全部注入，形状与错误原文取自 Rinx `fdcfed1` 源码；**不是真机运行**，不调用真实 Matrix 或模型服务。运行器像真宿主一样拒绝 manifest 未申请的服务。

| 项 | 结果 |
|---|---|
| 源码 SHA-256 | `5d6db93e…`（与本文一致） |
| 通过 | 43 / 43 |
| 尺寸 | 412×892 与 954×448 两种 |
| 覆盖 | 首屏、样例试映、载入房间、授权六态、生成/选句/修订、发送确认/读回/限流/超时、新消息复核、存储、重启恢复、双尺寸布局 |

基线与修复：在错误归因修复前，`09a`/`09b`/`10`/`11`/`18`/`20` 六个场景红（助手出错误报"没有读到群聊"、限流英文原文、授权过期按钮不刷新、确认作废状态条不刷新）；按契约修复后 43 次全绿。

重跑：

```sh
python3 <splash-app-verify>/scripts/uitest.py run bundle oncue/tests/ui --keep-going
```

## 12 套逻辑测试

真实 card-host 虚拟机，生产 154 个函数逐字节复制进测试包；宿主回包受控注入，UI、文件系统、时钟与计时器真实执行。同一源码 **12 套 368 项断言全部通过**，结果已归档 `evidence/logic-tests/` 可离线复核：

```sh
for s in parser pagination retry deadline playback storage grounding envelope send send2 send3 send4; do
  python3 oncue/tests/check_result.py --run-dir "evidence/logic-tests/$s" \
    --wait-seconds 0 --current-source bundle/main.splash || exit $?
done
```

| 套件 | 断言 | 内容 |
|---|---:|---|
| parser | 39 | 生成协议、标记、段落顺序、长度 |
| pagination | 15 | 文本守恒、组合字符、分页导航 |
| retry | 38 | 一次修复、实际拒绝原因及原请求保留、输入身份、许可、候选暂存与应用 |
| deadline | 6 | 真实 90 秒共享期限、迟到回包；观察窗口约 93 秒 |
| playback | 18 | 真实 1.4 秒计时、暂停/重播/切换 |
| storage | 56 | 规范格式、真实 I/O 失败、房间隔离、容量、草稿保护 |
| grounding | 96 | 来源、数字/单位（含中文数字、半天/半小时、复合单位）、承诺规则 |
| envelope | 25 | 异常回包、失败载入保留旧房间、切换确认、授权/账号/未登录/无服务错误 |
| send | 44 | 发送正文边界、窗口校验、匹配器、确认与单次发送、延迟/错误/重发 |
| send2 | 21 | 迟到回调、读回对抗、Unicode 前缀、选句/修订采用门 |
| send3 | 7 | 已核验本人消息采用门、发送记录元数据、显式保存 |
| send4 | 3 | 真实 30 秒发送超时、迟到成功不重写、无意外模型服务 |

**断言修订说明**：`envelope.auth_model_5`（试映路径的 `no service answers`）原断言把"当前宿主不提供群聊服务"当作正确文案——那正是错误归因 bug 的症状（助手服务出错却说群聊）。修复归因后，该断言期望改为"这个宿主现在没有可用的助手。可以先手写草稿；在 Rinx 设置里打开助手后再试。"；读群聊路径 `envelope.auth_room_5` 期望不变。

## 工具单元测试

**109 项通过**：生成器/检查器 12 项、原生验收工具 37 项、底层工具 60 项。不需要宿主和网络。

## 真实 Rinx 记录

| 证据 | 对应源码 | 内容 |
|---|---|---|
| `evidence/native-052/runs.json` | `56397f95…`（发送功能前） | 6 次真实模型试映：3 次首次通过、2 次修复后通过、1 次超时；拒绝原因原文在档 |
| `evidence/native-052/send-flow-results.json` | `21c8e8a6…`（措辞"返回修改"前） | 真实房间完整流程：生成→选句→修订→应用→保存→确认发送→读回确认→重开恢复；真实发送 1 条 |
| `evidence/native-052/auth-ui-results.json` | `21c8e8a6…` | 未选房间/未允许试映/未允许修订/撤回后四种授权状态实拍 |
| 本文所列各项 | `5d6db93e…`（最终） | 界面场景 43 次、逻辑 12 套、工具 109 项、hub check |

以上真实记录均早于最终源码（错误归因修复在前）；最终源码的行为差异仅限错误提示按服务归因、限流翻译、两处界面刷新，已由界面场景与逻辑测试覆盖。作者批准的话，可在最终源码上重发 1 条更新发送证据。

## 发现的宿主问题（复现材料）

**Palpo 房间密钥备份对无密钥房间返回 404，导致任何邀请失败。** Rinx `src/sliding_sync.rs:147` 开启"邀请时分享历史"，matrix-sdk `6892cb2` 的 `share_room_history`（`crates/matrix-sdk/src/room/shared_room_history.rs`）在邀请前先从**邀请人自己的备份**下载该房间密钥（`GET /room_keys/keys/{roomId}`），且不检查房间是否加密。Palpo（`crates/server/src/routing/client/room_key.rs:96`）对没有备份密钥的房间返回 `404 M_NOT_FOUND`，而 Matrix 规范要求返回 `200` 和 `{"sessions": {}}`。因此主账号（已开密钥备份）在新房间邀请任何人都会失败，不加密房间同样失败；第二账号未开备份时由其发起邀请则不会触发该查询。最小复现：开密钥备份的账号创建任意房间（可不加密），邀请任意用户 → 邀请接口报 `404 M_NOT_FOUND Backup key not found for this user's room`。是否向 Palpo 提 issue 由作者决定。

## 未验证

- 61 分钟授权过期实测（Rinx 授权一小时收回）：需真实等待，未执行。
- 跨账号"群里有新消息"实机演示：由界面场景 `13`/`15`/`21` 注入覆盖；真人第二账号演示待作者在场时进行。
- 最终源码上的真实发送（当前发送证据对应更早源码）。
- macOS、Windows、移动端；商店安装路径；并发写入与断电一致性。
- 语义正确性、数值归属、误拒率；字面规则不证明这些性质。
