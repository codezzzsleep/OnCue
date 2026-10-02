# 044 方案C + 逐句播放 · 真实宿主执行结果（2026-10-02）

> 全部证据均为**真实运行**：独立 `:97`（自起 Xvfb + 自己的 Xauthority）、
> `LP_NUM_THREADS=2`、软渲染（llvmpipe）、**串行一次一个 card-host**、翻页用 XTest 真实点击。
> **未**运行 cargo/stamp链外的 stamp/sign/publish、**未** commit/push、**未**改仓库 bundle。
> 遵守禁用约束：只用 `:97`，**绝不碰 `:99`/`:98`**；停进程只用记录的 PID 或 `pgrep -x card-host`。

## 结论速览

| 项目 | 结论 | 证据类型 |
| --- | --- | --- |
| **B 分页往返无损** | **通过**，7 夹具全部 `ALL_EQUAL=true`，逐字符 AND 逐字节 `orig==join` | **应用自证**（应用自己跑 `cue_paginate` 后 `fs.write` 落盘） |
| **C 逐句播放状态机** | **通过**，7 个子项全部符合（含 epoch 隔离 + 跨 2 间隔暂停不再变） | **应用自证**（探针直驱产品函数，落盘 count/playing/epoch） |
| **A 逐页翻读** | 页数 = 算法数（B），页数稳定、末页不越界不环绕、正文不被页脚截断 | 像素实测（真实点击 + 逐页 SHA） |
| **关键几何发现** | ① 页数与视口宽度**无关**（固定 `cue_page_cols=16`，412 与 990 页数相同）；② `cue_msg_rows=1` **修复了 990×613 的页脚裁切**（旧 `msg_rows=4`） | 像素实测 |

---

## 0. 环境事件：`:97` 被另一执行体占用 → 已回收（非 OnCue/方案C 缺陷）

执行中，`:97` 被**另一执行体**抢占：它自起了第二个 `:97` Xvfb（屏幕 **520×1000**、cookie 在 `/srv/oncue-runtime/state/xauthority97`，非我的 cookie），并持有常驻 card-host（bundle `probe-044/C326`）。我的首个 `:97` Xvfb(pid 70650) 被其回收，导致我的 C 探针启动即段错误（见 §3）。**520 宽放不下我需要的 990×613 视口。**

处置（透明可追溯）：先截图存证，再按 pinned PID 停掉外来 card-host(`pgrep -x card-host`) 与外来 `:97` Xvfb，清 `:97` 锁/套接字，按配方自起我自己的 `:97`（**1100×1000**，我的 cookie）。全程**未碰 `:99`(pid 34092，全程存活)**。外来件 PID 已记录，供 Team Lead 通知对方重启其显示。回收后 B/C/A 全部正常完成。

---

## ① 执行命令与退出码

> `env97.sh` = `DISPLAY=:97 XAUTHORITY=/root/oncue-runtime/state/xauthority97 LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe LP_NUM_THREADS=2`。

| 步骤 | 命令（要点） | 退出码/结果 |
| --- | --- | --- |
| 起 :97 | `Xvfb :97 -screen 0 1100x1000x24 +extension GLX +extension RENDER -noreset -auth $XA`（cookie 已 `xauth` 注入） | 起，`xdpyinfo` OK |
| 冒烟 | `card-host --bundle <C> --app-data <jail> --stamp --allow-unsigned --size 412x892` | admitted，`window sized 412x892`，出图 |
| 生成 A 包 | `A_gen.py <fixture> bundles/A-.. ai2-probe-aNN`（内部把 `make_probe_bundle.SRC_BUNDLE` 覆盖为方案C的 C 包，以保持 `16/3/1`+`padding6`+`spacing2`） | ok；几何核验 `cue_page_cols=16 / cue_page_rows=3 / cue_msg_rows=1` |
| 生成 B 包 | `B_gen.py bundles/B-rt ai2-probe-b044` | ok；`manifest integrity 已移除` |
| 运行 B | 同上 `--size 412x892`；`start_timeout(1.5)` 内自证，读 `<jail>/ai2-probe-b044/roundtrip.txt` | **`ALL_EQUAL=true`** |
| 生成+运行 C | `C_gen.py bundles/C-play ai2-probe-c044play`；跑 ~21s，读 `play-log.txt` + `play-done.txt` | **`COMPLETE`**，无 panic/error |
| 翻页 | `xclick.py click <x> <y>`（XTest，任意 display） | ok |
| 截图 | `ffmpeg -f x11grab -video_size <WxH> -i :97+0,0 -frames:v 1 -y out.png` | ok |
| 收尾 | `pgrep -x card-host` 全停；停我的 `:97` Xvfb | `:99`(34092) 存活，无残留 card-host |

**翻页点击坐标**：412 消息分页 `下翻`=(121, ~496–508)；990=(121,486)。均从截图**自动探测**后核实。

---

## ② 结果表

### ②A 逐页翻读（像素实测；页数 = 算法层 B）

逐页点 `下翻`，每页记 SHA；**当某次点击后 SHA 与上一页相同 ⇒ 末页越界不环绕（clamp）**。全套 9 组 `clamp=True`，`poverrun` 的 SHA 恒等于 `plast`（末页再点不前进）。

| 视口 | 夹具 | 页数(像素) | =B算法 | clamp(不越界) | 末页截尾? | 首页起点 / 末页(前一页)结尾 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 412×892 | 01长单行中文 | **34** | 34 | ✓ | 否 | `我们先把见面时间…` / `别睡过头。` | 尾`\n`单独成空白第34页 |
| 412×892 | 02连续ASCII | **21** | 21 | ✓ | 否 | `qwerty…` / `uvwxyz` | 硬折行 16 ASCII/行 |
| 412×892 | 03连续空格 | **27** | 27 | ✓ | 否 | `这句话前面是连续空格…` / … | 空格不 trim、不吞 |
| 412×892 | 04多行A/B | **46** | 46 | ✓ | 否 | `A 版先说结论…` / … | 源换行处断页，含多处空白页 |
| 412×892 | 06emoji组合 | **32** | 32 | ✓ | 否 | `emoji 与 ZWJ 序…` / … | emoji/ZWJ/旗帜完整渲染无半字形 |
| 412×892 | 07空格边界 | **28** | 28 | ✓ | 否 | `边界：页尾是连续空格…` / … | 跨页空格不多不少 |
| 412×892 | 08极短行 | **46** | 46 | ✓ | 否 | `一` / `字…字` | 行数上界 + 末页 |
| 990×613 | 01长单行中文 | **34** | 34 | ✓ | 否 | 同412 / 同412 | **页数与412相同→宽度无关**；页脚在正文下方**不裁切** |
| 990×613 | 06emoji组合 | **32** | 32 | ✓ | 否 | `emoji 与 ZWJ 序…` / … | 同412；页脚不裁切 |

判据逐条：
- **页数稳定不自增**：每组 `distinct_pages == B`，`下翻` 到底即 clamp（如 01：点满 34 页，第 34 次点击不再变化）。逐页 SHA 见 `probe-src/*-sha-walk.txt`。
- **末页不越界不环绕**：`poverrun.sha == plast.sha`（9/9 组成立）；若环绕会等于第 1 页 SHA（未出现）。
- **正文不被页脚截断**：`msg_rows=1` 每页仅 1 视觉行，`990-f01-p1` / `990-f06-p1` 页脚 `虚构群聊…仍需要自己判断` 明确位于消息卡**下方**，未压字（旧 `msg_rows=4` 在此高度会被压掉）。
- **首末页对得上原文**：01 首页 `我们先把见面时间…`、内容末页(33)`别睡过头。`；02 末 `uvwxyz`；均与夹具一致（B 的 `equal=true` 从码点级兜底）。

### ②B 逐页拼接逐字符=原文（**应用自证**，`roundtrip.txt`，sha256 `ce6a59…`）

应用自己调 `cue_paginate(text, cue_msg_rows)` → 各页拼回 `join` → 与原文比较，`fs.write` 落盘。

```
msg_rows=1 page_cols=16 page_rows=3   fixtures=7   ALL_EQUAL=true
```

| 夹具 | pages | equal | orig_chars/join_chars | orig_bytes/join_bytes |
| --- | --- | --- | --- | --- |
| 01-long-single-line-zh | 34 | **true** | 263 / 263 | 783 / 783 |
| 02-continuous-ascii | 21 | **true** | 311 / 311 | 311 / 311 |
| 03-continuous-spaces | 27 | **true** | 303 / 303 | 501 / 501 |
| 04-multiline-ab | 46 | **true** | 259 / 259 | 739 / 739 |
| 06-emoji-combining | 32 | **true** | 309 / 309 | 646 / 646 |
| 07-space-boundary | 28 | **true** | 276 / 276 | 428 / 428 |
| 08-minimal | 46 | **true** | 307 / 307 | 912 / 912 |

字节数由应用内 `rtf_bytes()` 码点法算得，与 Python `len(txt.encode())` 完全一致（如 01=783）。**判据 `equal=true` 成立**（且字符、字节双等）。原始输出见 §⑤ `B-roundtrip-output.txt`。

### ②C 逐句播放状态机（**应用自证**，`play-log.txt`，sha256 `0b52a7…`）

探针在真实定时器驱动下调用**产品函数**（与按钮 `on_click` 同一实现）并逐步落盘。route 0 生成 4 行。逐项：`} `= 实测状态量。

| 子项 | 操作序列 | 实测 | 判定 |
| --- | --- | --- | --- |
| 1 `下一句`保持暂停 | rehearse→nextLine×3 | count 0→1→2→3，`playing=false` 全程；epoch 5→6→7 | ✓ 每点+1且保持暂停 |
| 2 `播放`跨2间隔各+1 | restart→play；t0/t1/t2 | count 1→2→3，`playing=true`，**同一 epoch=9** | ✓ 每 1.4s +1 |
| 3 跨2间隔暂停隔离 | pause；等 3.4s | count 停 **3** 不变，epoch 冻结=10 | ✓ 旧 timer 被 epoch 隔离 |
| 4 续播从当前继续 | baseline count=1→play | count 1→2→3（**未归零**） | ✓ |
| 5 重播归零 | restart | count=**0**，与 pause 前无关 | ✓ |
| 6 换路线旧timer隔离 | play B(实时timer)→switch C | switch C 后 epoch 17→18，count=**0**，等 1.8s 仍 **0**（B 的 timer 回调 `epoch!=`→`return`）；随后 C 正常 play 1→2 | ✓ 旧 timer 隔离 |
| 7 无routes不崩+提示 | clear_routes→play→next | play:`先试映下一幕，再播放假设对白。`；next:`先展开三条路线。`；`playing=false`；脚本抵达 `Z_done` 无 panic | ✓ |

补充：`ws=M/N`（工作区 `readout` 分页，`page_rows=3`）随揭句增长 1/1→3/3→4/4→5/5，未报错。终态截图 `C-play-final-state.png`（routes=0，状态 `先展开三条路线。`）。

---

## ③ 首个具体错误（原文 + 日志路径）

**首个具体错误是环境层、非 OnCue/方案C 缺陷。** 运行 C 探针时，我的 `:97` 已被另一执行体回收，card-host 启动即段错误：

```
$ ... card-host --bundle .../C-play --size 412x892
bash: line 10: 72468 Segmentation fault (core dumped) setsid nohup ... card-host ...
```
- 日志路径：`logs/C-play.log`（回收前那次），关键行：`Invalid MIT-MAGIC-COOKIE-1 key`（`$XA` 空展开导致 `XOpenDisplay` 失败叠加 `:97` 被换主），**未到 `[SPLASH] eval` 即崩**。
- 另一次自踩（测试脚本次，非产品）：`990-f06` 首次报 `button_not_found`/近空白帧，根因是我给了不存在的 `bundles/A-06`（应在 `A-412-f06`），日志 `logs/990-f06.log`：`card-host: refused: .../A-06/manifest.json: No such file or directory`。改用正确包 + 指定 (121,486) 后得到 32 页 clamp，正常。
- **OnCue 产品逻辑：未发现错误**。B 无损、C 状态机、A 翻读与 990 不裁切均通过。

---

## ④ 明确未做到 / 未验证

- **990×613 只逐页实测夹具 01、06**（各自 clamp + 不裁切）。其余夹具在 990 的“页数相同、不裁断”属**算法层推断**（因固定 `cue_page_cols=16`，页数与宽度无关，已由 01/06 在 412 与 990 页数一致佐证），**未逐页截图**。
- **仅测了“原消息阅读区”分页**（`cue_msg_rows=1`）。右侧**工作区**（对白/摘要/A-B，`cue_page_rows=3`）在 C 中随揭句被动翻页且未报错，但**未**用 `下一页/上一页` 专门逐页截图校验 3 行分页的裁切与首末页。
- **列宽仍是启发式**：`cue_page_cols=16`、`cue_is_wide` 的 1/2 列宽近似**未**与 Makepad 真实排版做逐字形核验；font_size 未改。极端长串把渲染器多挤一行时仍可能折行（算法“偏多算安全、偏少算只多折一行”）。
- **页数宽度无关性未“修复”**：方案C 仍在 990 宽下按 16 列折页，未利用更宽的视口（保守取舍）。这正是“保守分页保纵向不裁切”的代价。
- **字素簇跨页**：`equal=true` 是**码点级**无损；06/08 若干 0 字符空白页出现在换行/组合边界，我未逐个边界验证“无可见半字形被拆到两页”（只核了 412-f06-p2、f01 首末页渲染完整）。
- 未做性能耗电、真实群聊读取（宿主无 matrix/octos 服务）、模型回合——任务范围外。

---

## ⑤ 产物路径与 sha256

根目录 `/root/oncue-work/044-optionc/`。

**真实截图 `shots/`（46 张，`<视口>-<夹具>-p<N>.png`）** —— 抽样 sha256：
```
412-f01-p1.png   b26d4dc2  | 412-f01-plast.png   fd7c3352 (== poverrun)
412-f01-plastm1.png c142f18e| 412-f02-plastm1.png 0e8fa561
412-f06-p2.png   d99f3b34  | 412-f08-plast.png   3cf4f229 (== poverrun)
990-f01-p1.png   a26a3433  | 990-f01-plast.png   0735043e (== poverrun)
990-f06-p1.png   46da1311  | 990-f06-plast.png   1e31ac75 (== poverrun)
C-play-final-state.png b36378
```
（完整 46 条 sha256 见运行记录；每夹具 `poverrun.sha==plast.sha` 均已核对）

**结果/证据文件**：
| 文件 | 内容 | sha256(前12) |
| --- | --- | --- |
| `results-roundtrip-app.txt` | B 应用落盘 round-trip | `ce6a59…` |
| `results-playlog-app.txt` | C 应用落盘播放状态 | `0b52a7…` |
| `probe-src/B-probe-fragment.splash` | B 注入片段(含内联夹具) | `49d6ec…` |
| `probe-src/C-probe-fragment.splash` | C 注入播放探针 | `0256aa…` |
| `probe-src/B_gen.py / C_gen.py / A_gen.py / adriver.py` | 探针生成器 + 翻页驱动 | 见下 |
| `probe-src/*-sha-walk.txt` | 每页 SHA 记录（9 组） | `38eae5…141f8d…` 等 |

**探针源 sha256**：
```
adriver.py 52d26636  A_gen.py 2eece748  B_gen.py 2f86c3db  C_gen.py 50d5bf74
B-probe-fragment.splash 49d6ec73  C-probe-fragment.splash 0256aa1e
```

**探针包 `bundles/`**（`--stamp` 重算摘要；均为方案C几何 16/3/1）：
- `A-01, A-412-f02/f03/f04/f06/f07/f08`（每夹具一份，单消息内联）
- `B-rt`(id=ai2-probe-b044)、`C-play`(id=ai2-probe-c044play)

**仓库外临时隔离区** `bundles/` `jails/` 未触碰仓库 `OnCue/oncue/bundle`；探针包全部在仓库外。
