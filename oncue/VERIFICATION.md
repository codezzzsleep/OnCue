# 验证记录

版本 **0.5.3，未签名**。验证日期：2026-10-12。

生产入口SHA-256：`d8056ab810664c89f4b558a2ce070af698a96c2e233067177fe463c6da92f2ec`（`bundle/main.splash`）。

## 包检查

最终未签名包经官方钉定 App Hub（`38635915`）构建的 `hub` 检查：

```text
oncue-screening-room 0.5.3 — PASSED
  [warning] publisher-signature: unsigned: accountability rests on the hub alone
```

申请能力八项：`storage`、`matrix.room_info`、`matrix.read_messages`、`matrix.account_info`、`matrix.send_message`、`octos.session.open`、`octos.turn.start`、`octos.turn.interrupt`；不直连网络。随包字体为 SIL OFL 许可的 OnCue Sans（Noto Sans CJK SC 裁剪重命名），授权全文在 `bundle/fonts/LICENSE.txt`。

## 界面场景测试

用 [splash-app-verify](../skills/splash-app-verify/)（仓库内副本；上游提交见 App Flow [PR #192](https://github.com/OctoSense-org/OctoSense-App-Flow/pull/192)）在 card-host 里运行 `oncue/tests/ui/` 的界面契约与 73 个场景（三种尺寸：412×892、954×448、1000×800；共 **83 次运行，全部通过**，全量约 310 秒）。宿主回复全部注入，形状与错误原文取自 Rinx `fdcfed1` 源码；**不是真机运行**，不调用真实 Matrix 或模型服务。运行器像真宿主一样拒绝 manifest 未申请的服务。

| 项 | 结果 |
|---|---|
| 源码 SHA-256 | `d8056ab8…`（与本文一致） |
| 通过 | 83 / 83 |
| 运行 ID | `ui-fix-final`（`run-tracked-ui.py`，含 63/64） |
| 尺寸 | 412×892、954×448、1000×800 三种 |
| 覆盖 | 首屏、样例试映、打开即读群、授权六态、一键试映与推荐、自动放进草稿、生成/选句/修订、发送确认/读回/限流/超时、新消息复核、看反响四态、阶段条、存储、重启恢复、三尺寸布局、审查修复回归 |

0.5.3 界面升级与审查修复新增 7 个场景（`56`–`62`）：三尺寸分区层级；确认视图只留核对区、返回后确认卡消失且草稿保留；恢复 unknown 后改目标/台词不解除发送拦截；秒级保存记录不匹配请求前的毫秒级旧消息；501 码点正文恢复后按前缀 500 字核对并标注部分核验；推荐理由不合规时退回默认路线且不展示虚构事实；最终读回延迟时「返回编辑」取消确认且迟到回包不发送。

早前记录：0.5.3 打开即读群等 12 个场景（`30`–`41`）先红后绿验证见历次提交说明。

重跑：

```sh
python3 <splash-app-verify>/scripts/uitest.py run bundle oncue/tests/ui --keep-going
```

## 12 套逻辑测试

真实 card-host 虚拟机，生产 184 个函数逐字节复制进测试包；宿主回包受控注入，UI、文件系统、时钟与计时器真实执行。同一源码 **12 套 435 项断言全部通过**，结果已归档 `evidence/logic-tests/` 可离线复核：

```sh
for s in parser pagination retry deadline playback storage grounding envelope send send2 send3 send4; do
  python3 oncue/tests/check_result.py --run-dir "evidence/logic-tests/$s" \
    --wait-seconds 0 --current-source bundle/main.splash || exit $?
done
```

| 套件 | 断言 | 内容 |
|---|---:|---|
| parser | 46 | 生成协议、标记、段落顺序、长度、推荐节写法 |
| pagination | 15 | 文本守恒、组合字符、分页导航 |
| retry | 38 | 一次修复、实际拒绝原因及原请求保留、输入身份、许可、候选暂存与应用 |
| deadline | 6 | 真实 90 秒共享期限、迟到回包；观察窗口约 93 秒 |
| playback | 18 | 真实 1.4 秒计时、暂停/重播/切换 |
| storage | 56 | 规范格式、真实 I/O 失败、房间隔离、容量、草稿保护 |
| grounding | 156 | 来源、数字/单位（含中文数字、半天/半小时、复合单位）、承诺句式识别与逐字放行、反响对照解析 |
| envelope | 25 | 异常回包、失败载入保留旧房间、切换确认、授权/账号/未登录/无服务错误 |
| send | 44 | 发送正文边界、窗口校验、匹配器、确认与单次发送、延迟/错误/重发 |
| send2 | 21 | 迟到回调、读回对抗、Unicode 前缀、选句/修订采用门 |
| send3 | 7 | 已核验本人消息采用门、发送记录元数据、显式保存 |
| send4 | 3 | 真实 30 秒发送超时、迟到成功不重写、无意外模型服务 |

**断言修订说明**：`envelope.auth_model_5`（试映路径的 `no service answers`）原断言把"当前宿主不提供群聊服务"当作正确文案——那正是错误归因 bug 的症状（助手服务出错却说群聊）。修复归因后，该断言期望改为"这个宿主现在没有可用的助手。可以先手写草稿；在 Rinx 设置里打开助手后再试。"；读群聊路径 `envelope.auth_room_5` 期望不变。

0.5.3 探针适配：启动序列识别接受打开即读群的第三段调用；send2 三个用例先服务试映后的自动新消息核对再走原手工选句断言（断言清单不变）；探针包指令预算 6400 万（一个 VM 步内同步驱动多次回包所致；生产 manifest 预算 800 万不变，单步单操作的界面场景在同一预算下通过）。

## 工具单元测试

**114 项通过**：生成器/检查器、实机验收脚本、审核包一致性、底层工具。不需要宿主和网络。

## 真实 Rinx 记录

| 证据 | 对应源码 | 内容 |
|---|---|---|
| `evidence/native-052/runs.json` | `56397f95…`（发送功能前） | 6 次真实模型试映：3 次首次通过、2 次修复后通过、1 次超时；拒绝原因原文在档 |
| `evidence/native-052/send-flow-results.json` | `21c8e8a6…`（措辞"返回修改"前） | 真实房间完整流程：生成→选句→修订→应用→保存→确认发送→读回确认→重开恢复；真实发送 1 条 |
| `evidence/native-052/auth-ui-results.json` | `21c8e8a6…` | 未选房间/未允许试映/未允许修订/撤回后四种授权状态实拍 |
| `evidence/native-053/`（results.md + 四张实拍） | `a44206f0…`（0.5.3 界面升级前） | 真实房间完整闭环：打开即读群（未点按钮自动载入）→ 一键允许并试映 → 真实模型两轮被数字接地规则如实拒绝、第三轮通过并给出【推荐】→ 推荐句自动放进草稿 → 两步确认发送（真实发送 1 条，台账 `.private/send-budget-052.json`）→ 读回核实 → 看反响如实显示「发出以后还没有新回复」，阶段条四段全勾 |

0.5.3 的四项行为变化已由界面场景、逻辑测试与上述真实闭环共同覆盖；真实记录早于最终界面升级与审查修复源码，对应行为差异另由注入测试覆盖。

## 发现的宿主问题（复现材料）

**Palpo 房间密钥备份对无密钥房间返回 404，导致任何邀请失败。** Rinx `src/sliding_sync.rs:147` 开启"邀请时分享历史"，matrix-sdk `6892cb2` 的 `share_room_history`（`crates/matrix-sdk/src/room/shared_room_history.rs`）在邀请前先从**邀请人自己的备份**下载该房间密钥（`GET /room_keys/keys/{roomId}`），且不检查房间是否加密。Palpo（`crates/server/src/routing/client/room_key.rs:96`）对没有备份密钥的房间返回 `404 M_NOT_FOUND`，而 Matrix 规范要求返回 `200` 和 `{"sessions": {}}`。因此主账号（已开密钥备份）在新房间邀请任何人都会失败，不加密房间同样失败；第二账号未开备份时由其发起邀请则不会触发该查询。最小复现：开密钥备份的账号创建任意房间（可不加密），邀请任意用户 → 邀请接口报 `404 M_NOT_FOUND Backup key not found for this user's room`。是否向 Palpo 提 issue 由作者决定。

## 授权到期实测（61 分钟）

真实 Rinx、0.5.2 最终源码（`5d6db93e…`）实测：04:04:54+08 打开应用并载入房间，05:08+08（约 65 分钟）观察——Rinx 在租赁过期后由 `pump()` 检查（`src/miniapps/ui.rs:569-584`）停止了小程序会话，界面显示 "Session ended. Review and run again." 并回到导入表单；截图在 `evidence/native-052/session-ended.png`。即**真实宿主到期表现为会话被结束**，应用内的"授权已过期"中文文案（含撤销允许、保留草稿）由界面场景 `04a` 与 envelope 注入测试确定性覆盖。

## 回应评审：拒绝授权与授权到期（0.5.3 界面重拍）

0.5.3 源码（`bundle/main.splash` SHA-256 `89a23d4c2e6c850b4aa6d4fc1f134d58cb11c4f21d39207ab9ab98e7daa766f0`）在真实 Rinx（官方 `c515e5fc`，零本地补丁）上重拍四种授权状态；应用内行为另有界面场景与逻辑断言兜底。

| 情形 | 怎么触发 | 用户看到的原文 | 草稿和存储怎样 | 证据 | 源码 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| 未选房间 | 导入时不填房间直接 Run | 「这次打开没有选房间。请关闭应用，导入时填上房间再打开。」（宿主另提示 "this mini-app is not attached to a room"） | 不载入、不写任何房间记录；样例舞台可编辑，但不保存到房间 | `evidence/auth-053/no-room-053.png`（未补丁对照机同路径实测见 `evidence/rinx-patch/unpatched-no-room.png`） | `89a23d4c…` |
| 未允许 | 载入群聊后不点允许 | 「允许后，试映、修订和看反响时，会把你的台词、目标、勾选的消息，以及你发出后群里新回复的正文（不含名字）发给助手。改了勾选、撤回或关闭应用后，要重新允许。」；阶段条「允许并试映」下注明本次发送内容 | 草稿本地保存不受影响；对助手零调用（场景 05a 断言 session.open/turn.start 均为 0） | `evidence/auth-053/model-not-allowed-053.png`、`oncue/tests/ui/05a-rehearse-needs-consent.json` | `89a23d4c…` |
| 撤回 | 已允许后点「已允许 · 点这里撤回」 | 「已撤回，之后不会再发给助手。」；点「看反响」只按原话列出新回复，不给对照（场景 N13/42） | 草稿与已列出的回复原话保留；撤回后不再调用助手（场景断言 turn.start 计数不变） | `evidence/auth-053/model-revoked-053.png`、`oncue/tests/ui/42-reaction-revoked.json` | `89a23d4c…` |
| 到期（Session ended） | 应用保持打开约 65 分钟，宿主租约到期 | Rinx 结束小程序会话：导入表单显示 "Session ended. Review and run again."；应用内「授权已过期」文案由场景 04a/envelope 注入覆盖 | **未保存编辑会丢**（会话被宿主结束，内存状态随之消失）；已保存草稿在应用私有存储里，重新打开后可载入 | `evidence/auth-053/session-ended-053.png`、`evidence/auth-053/expiry-record-053.json`（13:37 打开、14:44 观察到，约 67 分钟） | `89a23d4c…` |

## 未验证

- 最终源码的真实 Rinx 闭环（打开即读群→试映→确认发送→读回→看反响）：旧界面的闭环记录在上方；界面升级与审查修复后尚未在真实宿主重跑。
- 官方 OctoSense 桌面壳内的业务闭环：官方 RC6 源码构建与无账号启动通过，严格日志门未过（PulseAudio 回退 ALSA、上游 deferred UI 日志）；界面与逻辑验收在官方钉定 card-host/hub 下完成。
- 跨账号"群里有新消息"实机演示：由界面场景 `13`/`15`/`21`/`35` 注入覆盖；真人第二账号演示待作者在场时进行。
- macOS、Windows、移动端；商店安装路径；并发写入与断电一致性。
- 语义正确性、数值归属、误拒率；字面规则不证明这些性质。
- 恢复发送记录按账号/正文/时间核对是观察性的：另一客户端同文消息或时钟偏差不能排除；承诺句式条件豁免的已知缝隙：条件词后紧跟第三人称事实且没有逗号时（如「要是没问题他已经同意了」），中文不分词，无法稳妥判断「他」是新主句开头还是条件的一部分，此类句子按条件句放行。规则不再放宽：再宽会把「如果大家已经同意了」这类假设句误拦。
