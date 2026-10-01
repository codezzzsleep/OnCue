# 042-freeze — OnCue · 群聊试映室 0.4.2 冻结演练结论（S2）

- 执行时间：2026-10-01T21:49–22:00+08:00（`date -Iseconds`）；主机 aarch64 / Linux
- 原始输出：`evidence/native/042-freeze-transcript.txt`（232 行，含每一步命令与 stdout 原文）
- 前置（S1，已核验存在且通过）：`/tmp/oncue-042-dev` 存在；`042-clicktest-412.log` / `042-clicktest-990.log` 各 **16/16 PASS**，两个视口全部控件可点击触达
- 工具：`OCTO_HUB=/tmp/hubbuild/app-hub/target/release/hub`、`OCTO_CARD_HOST=/tmp/hubbuild/card-host/target/release/card-host`；开工前 `octo doctor` 全部 ok
- 显示：**私有 Xvfb `:96`**（PID 472370，1440x900x24，`ls /tmp/.X11-unix/` 先见 X96 再启动宿主）；桥端口 **18171 / 18172** 仅回环；未占用 OctoSense 桌面（:99 / 18141 的 shell 未动）

---

## 1. 落地改动（只动 `oncue/bundle`，共 4 个文件）

| 文件 | 改动 |
|---|---|
| `main.splash` | S1 的窄视口修复原样落入（路线移到左栏两行、草稿六按钮两行、播放两行、提示去方位词），**外加**失败文案补空格：`label + "没有保存完成…"` → `label + " 没有保存完成…"`（一处同时修好「草稿」与「版本 A/B」两种标签） |
| `manifest.json` | `version` 0.4.1 → **0.4.2**；`integrity.signature` **移除**（改版本必然使旧签名失效；新签名由 `hub sign-manifest` 重签） |
| `listing.json` | 只改 `release_notes`：如实写 0.4.2 的布局修复与**宿主服务现状**（card-host 无任何宿主服务、应用转样例模式并显示不可用；托管内核的 Shell 在 `Policy::contained_apps` 放行〔默认按用户首次同意，`OCTOSENSE_CONTAINED_APPS` 为开发者覆盖〕且用户首次允许该应用 Agent 后可用；Rinx 迷你应用宿主在用户审核导入后提供同样四个 `octos.*`）。**未写**"必然不可用" |
| `screenshots/01-native-rinx.png` | 用 **0.4.2 候选自己的真实截图**替换（见 §5），非 0.4.1 旧图改名 |

`git diff --stat -- oncue/bundle`：4 files changed, 19 insertions(+), 17 deletions(-)（截图 Bin 101180 → 123622 bytes）。

## 2. 演练顺序（严格按任务 7 步 + 发布时门禁预检）

| # | 命令 | 结果 |
|---|---|---|
| 1 | `hub stamp oncue/bundle` | 新 digest **`082844db52ca4d191bbc3ec5ac30629098eca46c5c16a660f8322670af6b1daa`** |
| 2 | `hub sign-manifest oncue/bundle --key state/hub-keys/working.key --key-id oncue.local` | `signed oncue-screening-room 0.4.2 with oncue.local`（签名值 `a44ddcbf…d4e505`，key_id `oncue.local`） |
| 3 | `hub check oncue/bundle --publisher-key oncue.local=<working.pub>` | `oncue-screening-room 0.4.2 — PASSED` |
| 4 | `git add oncue/bundle && git commit`（**未 push**） | commit **`79a018e3625a54ef81b8dfeedcfa17d82f7d472f`**（OnCue \<oncue@local\>，"Freeze the 0.4.2 candidate bundle with the narrow-viewport reachability fix"） |
| 4b | `hub check … --catalog state/hub-mirror/catalog.json`（PUBLISHING §6 第二种 check / 发布时门禁预检） | `PASSED`（0.4.2 是新版本，不会被拒） |
| 5 | `hub scan oncue/bundle --publisher-key … --reviewer deploy/oncue-reviewer.sh --packet evidence/native/042-hub-scan.packet.json` | `route: pass`，七问理由见 transcript；packet 27557 B |
| 6 | `hub publish oncue/bundle --catalog … --key working.key --anchor-cert … --publisher oncue.local --publisher-key … --repo https://github.com/codezzzsleep/OnCue --commit 79a018e… --reviewer … --out state/hub-mirror` | `published oncue-screening-room 0.4.2 (catalog sequence 8)`；scan: Pass |
| 7 | `hub verify state/hub-mirror/catalog.json --anchor <anchor.pub>` | `catalog sequence 8 verified, 8 entries` |

**四步门禁输出摘要**：check（不带 catalog）=PASSED；check（带 catalog）=PASSED；scan=pass；publish=已发布（sequence 8）；verify=验签通过（8 条）。0.4.2 条目的 `source.commit` = `79a018e…`，即签名工件所在提交。

## 3. 签名与 digest 状态

- bundle digest：`082844db52ca4d191bbc3ec5ac30629098eca46c5c16a660f8322670af6b1daa`（0.4.1 为 `8d00e986…`）
- 签名：`integrity.signature = {key_id: "oncue.local", value: "a44ddcbf…04ad4e505"}`，`hub check --publisher-key` PASSED
- 签名后 commit：`79a018e3625a54ef81b8dfeedcfa17d82f7d472f`（已记录，未 push；工作树 `oncue/bundle` 干净）
- mirror catalog：**sequence 7 → 8**，8 条；0.4.2 工件 `artifacts/oncue-screening-room-0.4.2.bundle` + `.pack.json`

## 4. 不可用态取证（合规 M7）

卡宿主跑本 0.4.2 候选包（无宿主服务），驱动到应用调用 `matrix.*` 的那一步（「载入群聊」→ `main.splash:82 matrix.room_info`）：

- **`cue_status.t` 原文**：`没有读到群聊：no service answers "matrix" on this device`
- `/snap?all=1` 读数（同刻）：`cue_scene_label='正在读取你选择并授权的群聊'`、`cue_status r=[12,542,966,25]`、`cue_draft` 空、`cue_trial` 保持样例台词；截图 `evidence/native/042-unavailable-cardhost.png`（990x613，sha256 `04d01e8a…`）
- 应用**以样例模式继续**：点「样例舞台」→「试映下一幕」→「A 顺着说」→「用这句」后 `cue_draft` 长 37、`cue_status='台词已放进草稿，可以继续修改；尚未发送。'`，全部本地功能不依赖宿主服务
- 房间未载入时点「试映下一幕」→ `先载入一个群聊，或打开样例舞台。`
- **「Agent 暂时不可用：」原文在 card-host 中不可达**（如实记录）：该文案在 `main.splash:168`（`octos.session.open` 失败分支），而 `cue_rehearse` 以 `cue_sources.len() == 0` 为前提（房间只能由 `matrix.read_messages` 填入，demo 舞台填入则走本地样例路线），card-host 无 matrix 服务故永远进不到模型分支。已尝试的替代路径（「载入群聊」后立刻点「停止等待」触发 `octos.turn.interrupt`）得到 `当前没有正在等待的请求。`——宿主在同一 pump 周期内已回复，无在途窗口。
- **card-host 日志**：`042-cardhost-unavailable.log`（19 行）中 `no service answers` 行数 **0**。源码实证：`appstore/src/services.rs:118` 只把该错误作为回复交给应用回调，不做日志；makepad `splash_host` 仅记录未授权能力的 `refused <cap>` 与回调错误。`no service answers "matrix" on this device` 的原文由应用状态行呈现并被 `/snap` 逐字捕获（见上）。

## 5. 截图来源与捕获方法

| 文件 | 尺寸 / sha256 | 来源与方法 |
|---|---|---|
| `oncue/bundle/screenshots/01-native-rinx.png` | 990x613 / `0a3898f0…56bb05` | **S1 的 `042-shot-990.png`**：0.4.2 候选在私有 Xvfb `:96` 的真实 X 捕获（`DISPLAY=:96 import -window 0x400002`；官方 `/g?raw=1` 本机 GL 下返回 `{"err":"grab timeout (is this backend rendering?)"}`，故不用）。画面为「试映下一幕后选中 A 顺着说、用这句填入草稿、播放中」。非 0.4.1 旧图（0.4.1 为 645x865 / `8-bit RGB`，101180 B，0.1.x 时代界面） |
| `evidence/native/042-unavailable-cardhost.png` | 990x613 / `04d01e8a…3bd1ab` | 本次取证运行（桥 18172）中、`cue_status` 正显示不可用文案时，`DISPLAY=:96 import -window 0x200002` 捕获；`/g?raw=1` 同样超时（404 + grab timeout JSON，已记录） |

两张图均用 PNG 直方图核验非空白（主色 `#F5F7F3` 应用底色、白卡片、`#136C47` 按钮绿）。截图只存文件，未使用 `read_image`。

## 6. 演练后恢复与复核

| 项 | 结果 |
|---|---|
| `/srv/oncue-apps/oncue-screening-room/bundle` | 与 `git show 9cb14a5:oncue/bundle`（0.4.1 签后提交）**逐字节 IDENTICAL**，未需改写 |
| `hub check /srv/.../bundle --publisher-key …` | `oncue-screening-room 0.4.1 — PASSED` |
| mirror `artifacts/oncue-screening-room-0.4.1.bundle` | 与 git **IDENTICAL**；`.pack.json` 与演练前备份 IDENTICAL |
| mirror 0.1.0 / 0.1.1 / 0.2.0 / 0.3.0 / 0.3.1 / 0.4.0 工件 | 全部与演练前备份 IDENTICAL（publish 只新增，未改旧工件） |
| 演练对 mirror 的唯一写入 | 新增 `oncue-screening-room-0.4.2.bundle`(+`.pack.json`) 与 `catalog.json`（sequence 7→8）。演练前完整 mirror 备份在 `/tmp/oncue-042-backup/hub-mirror-pre042`，需要时可整目录回滚到 sequence 7 |
| `state/apps/oncue-screening-room/bundle` | 另一处 0.4.0 安装，未动（不属本次恢复范围，仅记录） |

## 7. 未做 / 待 HUMAN 项

1. **`git tag`**：当前 0 个 tag。PUBLISHING §3.6/3.7 要求对"签名后精确字节所在提交"打 tag（即 `79a018e…`）——HUMAN。
2. **正式 Submit issue**：未在 OctoSense-App-Hub 开 `Submit oncue-screening-room 0.4.2`——HUMAN。
3. **发布者密钥**：现用本机工作钥 `oncue.local`，而非 PUBLISHING §3.6 要求的"由应用所有者创建并保管"的 publisher key。若改用所有者自己的密钥：需 `hub keygen` + `hub certify`（anchor 换新）+ 重签 + 重跑 check/scan/publish；注意**重签会改 manifest 字节，签名后 commit 需重做**（bundle digest 不含 manifest.json，不变）。
4. **真实房间读取 / 模型回合**：尚未在真正提供 `matrix.*`/`octos.*` 的宿主上验证（Shell 需 `contained_apps` 放行 + 首次同意；或 Rinx 审核导入）——保持 pending，不阻断基础冻结。
5. **审阅答案文本刷新**：`deploy/oncue-reviewer.sh` 是静态文本，本次 scan 把它重写到 `evidence/hub-review-answers.md`，仅 packet digest 行变化（`4980959f…` → `1f991286…`）；其 Q1 仍写"draft save/restore round trip … were still pending"，而 S1 的 16/16 双视口实测已覆盖存/取 A/B 回读。建议主进程在正式提交前刷新这句。
6. **mirror 是否回滚到 sequence 7**：演练按任务指定 `--out state/hub-mirror`，故 mirror 现含 0.4.2；如主进程希望本地镜像维持"只发布 0.4.1"，可用 `/tmp/oncue-042-backup/hub-mirror-pre042` 回滚。

## 8. 事件与说明（需主进程知悉）

1. **card-host 拒绝带签名的 manifest**：实测 `card-host --bundle oncue/bundle`（0.4.2 已签名）被拒——`card-host: refused: no signature verifier is installed, so the signature from key "oncue.local" cannot be checked`（`app-policy/src/verify.rs` 的 `RefuseAllSignatures`；`args.rs` 明示 "A signed manifest is still refused: card-host verifies no publisher keys"）。因此不可用态取证使用同一份 0.4.2 应用字节的副本，仅删 manifest 的 signature 块并以 `--allow-unsigned` 准入；`digest_dir` 不含 `manifest.json`，故 bundle digest `082844db…` 与其余 4 个文件逐字节不变（已 `cmp` 逐个核验）。
2. **git commit**：按任务 §2 的"严格"演练顺序（publish 需要 `--commit` 指向签名工件提交），本次只提交了 `oncue/bundle` 一个提交（`79a018e…`，未 push）；`evidence/native/042-*` 等文件**未提交**，留给主进程统一提交。
3. `evidence/hub-review-answers.md` 被 reviewer 脚本重写（见 §7.5），是本次演练的预期产物、非误改。
4. 清理：两个 card-host 实例均以 `curl -s 127.0.0.1:<port>/quit` 退出（`{"ok":1}`），Xvfb :96 已结束；`/tmp` 下的演练副本与数据目录保留在 `/tmp/oncue-042-backup`、`/tmp/oncue-042-frozen-bundle` 供复核（需要可删）。
5. 本文件与 transcript 不含任何密码/token/私钥；密钥只写路径与键名。

## 9. 证据文件索引

| 文件 | 内容 |
|---|---|
| `evidence/native/042-freeze-transcript.txt` | 全程原始输出（8 步演练 + 不可用态取证 + 恢复复核） |
| `evidence/native/042-freeze.md` | 本结论 |
| `evidence/native/042-hub-scan.packet.json` | 0.4.2 审阅包（七问） |
| `evidence/native/042-cardhost-unavailable.log` | 取证运行的 card-host 全量日志 |
| `evidence/native/042-unavailable-cardhost.png` | 不可用态截图（状态行可见 `no service answers "matrix"`） |
| `evidence/native/042-shot-990.png` / `042-shot-412.png` | S1 双视口截图（990 已作为商店截图随包发布） |
| `evidence/native/042-layout-fix.md`、`042-clicktest-412.log`、`042-clicktest-990.log`、`042-layout-geometry.json`、`042-main-splash.diff` | S1 布局修复与双视口 16/16 实测 |
| `evidence/hub-review-answers.md` | reviewer 记录（本次 scan 重写，packet digest `1f991286…`） |

---

## 10. 事后记录（本报告完成后、主进程并行提交期间观察到的事实）

- 主进程已把本次演练的提交与证据收进历史：`79a018e`（我的签名后 bundle 提交，**在 HEAD 祖先链上**）→ `066cf74`（布局修复与 0.4.2 演练记录）→ `f6a0f18`（041 复核件与 reviewer 答案）→ `2df4a47`（"Correct two claims AI1 checked against the real images"）。HEAD 的 `oncue/bundle` 与本报告冻结的字节**逐字节相同**（version 0.4.2 / digest `082844db…` / 签名 `a44ddcbf…`），故 catalog 中 0.4.2 条目的 `source.commit = 79a018e…` 仍然指向签名工件所在提交。
- **`2df4a47` 记录了一条影响本候选包的判断**：AI1 直接读取了两张视口截图，发现两个视口都仍有裁切，结论是"当前候选不构成整体通过，16/16 仅覆盖可点击性与状态回读"，选定方向是给消息/对白/草稿一个显式全文视图而非接受裁切。若按此方向再改版式，bundle 必须重新 `stamp` → 重签 → 重跑 check/scan/publish（digest 必变），mirror 里的 0.4.2 条目应按需 `hub withdraw`（条目保留并标注）或用 `/tmp/oncue-042-backup/hub-mirror-pre042` 回滚——**这些都不在本次任务范围内，留待主进程决定**。
- **审阅包 digest 三种取值的成因**（证据可追溯性备注）：reviewer 记录的 `1f991286…` = 管道收到的紧凑 JSON 去掉 `$(cat)` 吃掉的末尾换行后的 sha256；reviewer 自存的 `/tmp/oncue-reviewer-packet.json` 多一个换行 → `a921cad5…`；`--packet` 落盘的 `042-hub-scan.packet.json` 是 pretty 版 → `9fc69fbf…`。三者内容等价，与本仓库 0.4.1 时期记录的同源现象一致。
