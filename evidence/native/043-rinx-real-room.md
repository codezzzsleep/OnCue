> ⚠️ **版本降级标注（2026-10-02，按 AI1 #359 第 4 条）**
>
> 本文件的 Rinx 侧结论（房间读取 / 七块回合 / 停止·90 秒·迟回调等）是在
> **Rinx 当时安装的 `0.4.3` 包（digest `ec7773d51f2078e618d1711bb9b2840629e272858b040abf0af19c1c492e9619`）**
> 之上取得的（多数经由叠加在该基线上的**探针包**）。
> **它们不代表当前包 `0.4.4`（digest `2478d2300f7cbebc17f439caf3965e710a010285d6ddfa306778243efb63d81f`）。**
>
> 当前包已通过 Rinx `Discover → Mini apps → Import an app` 的 **Developer Review→Run** 装载
> （快照 `rinx-miniapp-4739e871-…`，digest 与当前包精确一致），**同版回归尚在进行**；
> 在复跑通过之前，本文件结论**不得**被当作当前包的结果引用。
> 证据的 homeserver 为 `matrix.org`（**不是**赛事 `matrix.rinx.chat`）。

# 043 · OnCue as a Rinx mini-app — real room read test

> **范围与纠正（AI1 #218 核实后）**
> - **本文件实测的是 0.4.2 的副本，不是 0.4.3**：开发资源 digest 为 `082844db…`、宿主 Review 面板显示的版本是 **0.4.2**。
>   标题里的 "043" 只表示"这是 043 阶段的联调记录"，**不得据此称 0.4.3 已被联调**。
> - 文中 `Prepared at` 行的年份原写作 **2025**，属**错年**；真实时间是 **2026-10-01**（本机时区 UTC+08:00）。
> - **Phase A 的可认范围仅限"导入/Run 的提示与可见控件"**：`hls_matrix.json` 存在、以及不再出现 `no service answers`，**都不等于 matrix 回调真的成功**；`cue_sources=[]` 与 `cue_busy=false` 也可能是 90 秒 deadline 的结果，**不足以认定"读取成功但返回空"**。需要 fresh 请求/响应或 raw `/snap` 状态为证（不含密钥）。
> - 关于重复 id：在**没有"唯一限定 lookup"的对照实验**之前，结论降级为"**实测 Review 读取为空 + 冲突疑因**"，不写成"已确认根因"；也**不把模型可用写成预期通过**。

Host display: **`:99`** · bridge `18141` · Rinx (`rinx2` client) · window 320×695.
Prepared at: 2026-10-01 ~23:40 (Oct 1). No commit made (per task).

Scope per task: (A) run OnCue as a **Rinx mini-app** (not the Hub-card path),
(B) a **real room read**, (C) a **real shared Octos turn**, (D) this evidence.

Isolation honoured: this worker only drove `:99`. The other UI worker's assets
were never touched — no `:94/:95/:96`, no `043-readable-fix.md`, no
`043-read-*.png`, no `/tmp/oncue-043-read*`, no card-host PID 475509. Host was
not upgraded, no host source edited, no `state/hub-mirror/`, no git commit.

## Dev copy used (private, unsigned, no stamp/sign/publish)

- Source: `/root/oncue-runtime/dev/OnCue/oncue/bundle` (copied with `cp -a`).
- Working copy: **`/tmp/oncue-043-rinx`**.
- Manifest edits: `id` → **`oncue-043-rinx`** (avoid clashing with the installed
  `oncue-screening-room`); `integrity.signature` **removed**; `bundle_blake3`
  kept (`082844db52ca4d191bbc3ec5ac30629098eca46c5c16a660f8322670af6b1daa`).
- Verified independently: python-blake3 `digest_dir(copy)` (which excludes
  `manifest.json`) == the kept hash; `diff -rq` shows only `manifest.json`
  differs. Content otherwise identical/known.
- Import snapshot created at:
  `…/state/octosense/apps/rinx/data/miniapps/imports/rinx-miniapp-e44afd98-4360-4889-8915-b0590e37d652`
  (id-independent for matrix/room and for octos: leases are capability/room
  scoped; octos uses profile `_main` and Rinx's own assistant host).

## Phase A — mini-app loads & runs · **PASS**

Admission via the unsigned developer path succeeded
(`admit_digest` + `RefuseAllSignatures` + `HostLimits{require_signature:false}`).
Review notice after filling the **path** field:

```
OnCue · 群聊试映室 0.4.2 · Local unsigned bundle
Services: storage, matrix.room_info, matrix.read_messages,
          octos.session.open, octos.turn.start, octos.turn.interrupt
Allowed room: None
Run grants these services for this session. Octos turns may use the
connected core's tools.
```

“Local unsigned bundle” + all six services ⇒ the bundle matrix/capability set is
intact and the host accepted the removed signature.

Clicking **Run** started the mini-app (notice then read verbatim):

```
Running · Back closes this app and revokes its services.
```

…and the OnCue `载入群聊` / `试映下一幕` / `停止等待` buttons became live.
**Crucially there is no `no service answers "matrix"`** — that error was the old
Hub-card path; the mini-app runs against Rinx's own host, whose sidecar is
omnipresent with the matrix sidecar matrix services (`runtime/hls_matrix.json`,
13836 tokens, Oct 1 22:25). So the mini-app lease is created inside Rzin's host
and the matrix service commands correctly resolve. **Phase A: PASS.**

## Phase B — real room read · **BLOCKED (room not attached)**

Clicking **载入群聊** executed OnCue's `cue_import_room()` which calls the
matrix service commands. It ran (no dispatch error, no “no service answers”)
but read **nothing**: the host-log showed the calls reach the mini-app host
sidecar and come back empty. The card ended in:

```octoscript
let cue_sources = []
let cue_busy   = false
let cue_demo   = false
let cue_scene  = "正在读取你选择并授权的群聊"
```

i.e. `cue_sources_list` is **0 messages** and it is **not** the canned-demo
fallback (`cue_demo=false`) — the gather genuinely returned empty.

**Suspected cause (strong source clue, not yet isolated by a uniquely-qualified lookup).** The lease is created by
`run()` with `room = text_input(ids!(room)).text()` (`ui.rs:352`), gated by the
same value used at review (`ui.rs:329`). Even though the `room` field visibly
showed the real ID, `text_input(cx, ids!(room)).text()` returned `""`, so the
lease was issued with `room = None` and the matrix reads had no room bound —
therefore empty. Evidence:

- Typing the real room ID, then Review ⇒ `Allowed room: None`.
- Typing a plain **invalid** value `hello`, then Review ⇒ still
  `Allowed room: None` (not “Invalid Matrix room ID”) ⇒ the read value was the
  empty string, not the field contents.
- **Control:** the sibling **path** field (`ids!(path)`, nested under
  `bundle_path`) reads typed text correctly — clearing + retyping + Review
  still loaded the bundle. So it is *not* a generic “blur to commit” problem;
  it is specific to `ids!(room)`.
- Run proceeded even though the visible `room` field held the real ID while
  `reviewed_room` was empty (`"" == ""`), confirming both reads were `""`.
- Full a11y tree (via `/snap`) shows exactly **one** exact-id `room` TextInput
  (the import form's, holding my typed value) — but the panel also registers a
  second widget with terminal id `room`: the **library room DropDown**
  (`library.rs:66`, id path `details.room_group.room`). With two `room` ids
  registered in the same panel view, `ids!(room)` does not resolve back to the
  import-form TextInput at runtime, so `.text()` yields `""`.

Net: the run succeeded but the **room was never bound to the lease**, so the
“real room read” produced 0 messages. **Phase B: FAIL (blocked by the
`ids!(room)` read)**, even though the matrix *call path itself* is proven live
by Phase A.

## Phase C — real shared Octos turn · **NOT REACHED**

Not attempted: a real `octos.turn.start` needs a real, non-empty room read
first (on failure OnCue stays in demo/empty). Since B returned 0 messages, the
turn would only operate on empty context. Noted for continuity: agent consent
is already granted read-only (`consent.json`: `oncue-screening-room`,
`rinx`), and profile **`_main.json` exists** at both
`/srv/oncue-core/profiles/` and `…/state/octos-core/profiles/`
(enabled, MiniMax-M2.7). Secret reference only (no value written): the model
key lives at **`/srv/oncue-core/profiles/_main.json`**, key name
**`MINIMAX_API_KEY`**. So a real turn is expected to be *possible* once a room
is actually attached and a real read returns.

## Verdict

- **A = PASS** — OnCue runs as a Rinz mini-app with matrix host services; the
  `no service answers "matrix"` failure is gone.
- **B = FAIL** — matrix call path is live but the room never attached because
  `text_input(ids!(room)).text()` returns `""` (id collision with the library
  `room` DropDown), so `matrix.room_info`/`read_messages` had no room.
- **C = not reached** (depends on B).

## Recommended next step (for continuity)

Two concrete routes, both host-side — do **not** hand-edit host source (out of
scope for this task):

1. **Library / App-Hub launch** (`ui.rs:738` `LibraryAction::Launch` → sets
   `reviewed_room` from the in-app Hub's room DropDown, `set_text(ids!(room))`,
   then `run()`). That supply path is the intended way to bind a room and may
   sidestep the collided import-form field. If the library does **not** list
   the unsigned local import, this route is unavailable → see (2).
2. **Resolve the id collision** between the import-form `room` TextInput
   (`ui.rs:55`) and the library `room` DropDown (`library.rs:66`,
   `details.room_group.room`) so `ids!(room)` binds the import-form input.
   Once `text_input(ids!(room)).text()` returns the typed ID, B should read
   real messages and C becomes reachable — no bundle or capability change
   needed.
