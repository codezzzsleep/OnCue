# 0.4.3 冻结记录（阅读优先修复后）

- 时间：2026-10-01 23:0x–23:1x（UTC+08:00，容器 `date` 实测）
- 版本：**0.4.3**；digest **`ec7773d51f2078e618d1711bb9b2840629e272858b040abf0af19c1c492e9619`**
- 签名：`hub sign-manifest --key-id oncue.local`（工作钥，仅本机 dev 镜像的信任根；**不是**所有者正式发布者密钥）
- 签名工件提交：**`f0bf128452d806a7fab44b0748eab54a1fd99ddc`**

## 执行顺序（AI1 #176/#182/#197 要求的顺序，逐步实测）

| 步骤 | 命令要点 | 结果 |
| --- | --- | --- |
| 1 内容定稿 | 阅读优先版式 + listing 更正（"不会自动降级"）+ 阅读修复说明 | 工作树 `oncue/bundle` 变更 |
| 2 `hub stamp` | 重算 digest | 旧 `082844db…` → 新 **`ec7773d5…`** |
| 3 `hub sign-manifest` | `--key-id oncue.local` | `signed oncue-screening-room 0.4.3 with oncue.local` |
| 4 `hub check`（不带 catalog） | 本地门禁 | **PASSED** |
| 5 提交签名工件 | `git commit` | **`f0bf128`** |
| 6 **push** | `git push origin main` | 远端 main 前进到 `f0bf128` |
| 7 **核对远端精确字节** | `git fetch` + 从 **origin/main** 导出副本 | HEAD == `origin/main`；`stamp_bundle.py --check` → **matches true / signature_present true**；官方 `hub check` 对远端副本 **PASSED**；与本地 `diff -r` **IDENTICAL** |
| 8 `hub scan` | `--reviewer deploy/oncue-reviewer.sh --packet evidence/native/043-hub-scan.packet.json` | 七问齐全，route 判据见 packet |
| 9 `hub publish` | `--commit f0bf128…` | **published 0.4.3（catalog sequence 9）**，scan: Pass |
| 10 `hub verify` | `--anchor anchor.pub` | **`catalog sequence 9 verified, 9 entries`** |

→ **满足"签名提交先 push、核对远端后再用该精确 commit publish"**（0.4.2 那次是"先 publish 后 push"，仅作历史，已在 `042-freeze.md` 与本文件注明，不回滚掩盖）。

## 阅读修复的验收依据（本版本的内容变更）

- 原消息逐条翻读 + 位置/总数；对白按 **2 行/页**分页 + 页码/总页数，可翻到建议草稿；A/B 与建议同一阅读面板切换。
- 双视口 **412×892 / 990×613** 逐条（12/12 字段级一致）与逐页翻到底；**12 张真实 X 捕获**（`043-read-*.png`）；**裁切自检全部 ok**（内容卡底部留白为正、无半行、状态行不压内容）；字体未改。
- 3 行/页曾在 990 上把末行挤成半行（`h=13`），改为 2 行/页后消除——这是本版本的**明确取舍**。
- 样例文本为**虚构 fixture**；真实房间读取与真实模型回合**未在本版本验证**（另见 `043-rinx-real-room.md`）。
- 已知增强项（不计失败）：排练前阅读面板为空白（该 host 构建里"孤立单个动态 `CueText`"不渲染）。

## 状态

- 0.4.3 仅发布到**本机演练镜像**（sequence 9）；**正式 App Hub Submit 仍未发生**（issue 由人开）。
- `/srv/oncue-apps/oncue-screening-room/bundle` 保持 **0.4.1**（`hub check` PASSED）；0.4.3 的安装是单独一步。
- 发布者密钥归属、git tag、正式 Submit 仍为**待 HUMAN** 项。

## 验收状态（必须与上面的"执行体自检"区分开）

- 上面"阅读修复"一节的结论来自**执行体自检**（12 张真图 + 裁切自检 + 逐条/逐页读数）。
- **AI1 于 2026-10-01 15:29（#200）明确表示：043 报告已收到，正在独立查看 12 张图与分页源码，"尚未认可任意长文本完整阅读"。**
  因此 **0.4.3 的"全文可读"目前是"执行体自检通过、AI1 独立复核中"，不是已获验收**。
- 同理：本次 `hub publish` 只是**本机演练镜像**（sequence 9），**不是**正式 App Hub 提交；
  0.4.2/0.4.3 都不应被表述为"已通过评审的最终交付"。
- 若 AI1 复核发现长文本仍有截断，需按同一流程改版式并**升版本号**重走 stamp→sign→check→commit→push→核对→scan→publish→verify。
