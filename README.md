# OnCue · 群聊试映室

**先试着说，再决定要不要发。**

把一句还没发出去的话放进私人排练场，看看三个不同的下一幕：
**顺着这句 / 换个问法 / 换个玩法**。回看原消息，播放匿名的假设接话，
把喜欢的建议放进草稿，再对照两种写法。

队伍 **OnCue** · 成员 **YCOROY** · 赛道 **OctoSense 即时消息 · Rinx**。
开发与交付在 `main`，保留提交和运行证据历史。

## 比赛主作品：OctoScript 小程序

[oncue/bundle/](oncue/bundle/) 是供 OctoSense / Rinx 宿主加载的 OctoScript 应用包。
主要交付路径是 **原生小程序 → App Hub**；下面的 Python 网页版是辅助体验与验证工具。

截至 2026-10-01，main 中的 **0.4.2 是历史演练候选，尚未整体验收**：
两种窗口下按钮与存取操作有实际通过记录，但原消息和对白仍被裁切，正在补完整阅读路径。
本地 App Hub 已演练签名、检查和目录发布；**正式 App Hub Submit 尚未完成**。
[提交草稿](build/SUBMISSION.md) 会在最终版本冻结后替换版本、截图、tag、SHA与检查结果。

小程序包含明确标记的虚构样例、三路线、播放/暂停/逐句/重播和本地草稿 A/B。
真实模式请求 Rinx 授权的房间读取与共享 Octos 服务；
**同一 OnCue 实例的十二条读取和真实模型回合仍待实测**。
账号留在宿主，模型凭据留在内核，小程序不携带凭据、不申请群消息发送能力。

在已经登录的 Rinx 中，打开 **Mini apps → Import an app / App Hub → Developer**，
附加自己的测试房间，Review 后 Run。固定 Developer 入口拒绝未受信任的签名；
联调用仓库外、资源摘要相同、仅去掉签名字段的开发副本，保留签名候选原件。
具体步骤见 [原生工作流](oncue/docs/NATIVE-WORKFLOW.md)
和 [固定版本导入说明](evidence/RUNBOOK-step10-11.md)。
独立 card-host 的样例运行只能证明本地功能，不能代替 Rinx 服务验证。

## 一分钟怎么玩

1. 打开虚构的“国庆搭子局”，试一句“明早9点出发，住一晚”。原消息里有人中午才能走、希望当天回来。
2. 改成“中午出发、当天回来，先核实预算”，重新试映，比较三个不同的接法。
3. 选“换个玩法”，把讨论变成半日旅行盲盒：每人给一个想做的事，再找条件的交集。
4. 播放、暂停或逐句查看假设对白，把喜欢的建议放进草稿；改两种写法，分别存 A、存 B，再取回对照。

原消息是事实线索，下一幕是假设，未被同意的行程和费用仍需核实。
样例使用本地预设；真实模型模式必须取得宿主服务的实际结果。
播放与切换已有路线不重新请求模型。原生 A/B 保存的是**草稿文本**，不宣称保存了完整模型场景。

## 当前实测范围

| 范围 | 已有证据与限制 |
| --- | --- |
| 原生 0.4.1 草稿与 A/B | 实际保存、回读、重开恢复；当前 draft/A 为103字节、B为136字节。历史149字节的A已明确标注覆盖前时间 |
| 原生保存失败 | 独立 card-host 的有效64字节配额测试：失败提示可见、输入保留、文件未生成 |
| 原生播放 | 0.4.1暂停5秒及8秒计数稳定，逐句、重播、切路线有实测；不代表所有内部回调均已覆盖 |
| 0.4.2候选 | 412×892、990×613各16项操作/读回通过；AI1逐张看图发现全文裁切，整体阅读验收未通过 |
| 服务不可用 | 实际 card-host 显示 Matrix 不可用；可手动回样例继续。没有把它算作真实 Octos 失败分支测试 |
| Rinx与共享Octos | 登录及本人房间双向消息有AI2报告；OnCue读取十二条、真实七块剧本、停止/90秒超时/迟回调隔离仍待验证 |
| App Hub | 0.4.2资源摘要两边只读核对一致，实际Hub门禁/本地seq8演练有报告；不等官方收录或完整功能验收 |
| 辅助网页 | Chromium148.0.7778.0完整18项检查、浅色/深色/320px实际图；后端19项报告与真实MiniMax HTTP结果。不能代替原生共享Octos |

详见 [验证记录](oncue/VERIFICATION.md) 与 [0.4.2独立评审](evidence/native/042-ai1-review.md)。
可读性通过后，将用新版本、同版本截图和精确签名提交重新冻结；旧候选保留作溯源。

## 辅助网页体验

在仓库根目录运行，无需图形桌面或额外 Python 依赖：

```bash
python3 oncue/server/app.py
```

打开 `http://127.0.0.1:8787/`。默认是明确标记的本地规则演示。
若服务器已有仓库外的模型凭据文件：

```bash
MINIMAX_API_KEY_FILE=/absolute/path/minimax.key python3 oncue/server/app.py
```

模型模式需在页面选择并确认取材。网页支持保存和恢复完整排练场景，区别于原生的草稿A/B。
部署说明见 [服务器运行说明](oncue/README.md)。

![辅助网页的实际播放画面](evidence/playback/01-playback-light.png)

```bash
python3 -m unittest discover -s oncue/tests -v
# 需要已有 Playwright + Chromium，对运行中的辅助服务器执行：
python3 evidence/playback_check.py --url http://127.0.0.1:8787/
```

资源摘要的只读自检（需 `pip install blake3`）：

```bash
python3 oncue/tools/stamp_bundle.py oncue/bundle --check
```

该命令不修改文件；摘要匹配退出0，不匹配退出1。
它不验签、不替代 `hub check`，也不证明应用实际运行通过。

## 数据与源码

保存由使用者主动触发，未发送的排练不会自动发到群里。
来源核对不能保证所有假设或建议符合事实；取材与存储范围见 [数据说明](oncue/PRIVACY.md)。

- [产品说明](oncue/PRODUCT.md)
- [原生应用包](oncue/bundle/)
- [原生工作流](oncue/docs/NATIVE-WORKFLOW.md)
- [App Hub提交草稿与清单](build/SUBMISSION-CHECKLIST.md)
- [Apache License 2.0](oncue/LICENSE)
