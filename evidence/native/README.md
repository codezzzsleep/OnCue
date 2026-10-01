# Native interaction records (fixed Rinx host, 2026-10-01)

All three images come from the SAME running shell instance: OctoSense on
Xvfb :99, the OnCue module installed through the App Hub UI and opened
from its Library entry. The window is 990x613 inside the 1400x900
OctoSense window, so the content is taller than the viewport and these
captures are scrolled views of that one instance.

- 03-rehearsal-three-routes.png — after pressing 试映下一幕: the status
  line "样例预设已展开；这些对白不是对真实群友的预测。" and routes A
  (顺着这句) and B (换个问法), each with two fictional replies, its
  依据 line, the 建议台词 and the 把这句放进草稿 action.
- 04-route-into-draft.png — route C (换个玩法) plus the result of
  pressing 把这句放进草稿 on route A: the 我的草稿 box now holds
  "先按 12 点后出发、当天回来讨论。杭州是否合适，等车费和行程核实后再定。"
  followed by 保留这句 / 取回草稿.
- 05-two-take-ui.png — the A/B section of the two-take patch: 两个版本,
  the description line, 保存为 A / 保存为 B and the empty state. The
  save buttons did not react to clicks in this instance; no take-a.txt /
  take-b.txt was written (see the report to the team).

## 0.3.0 module window (990x613), 2026-10-01 16:2x

Same shell restarted with the published 0.3.0 artifact in
state/apps/oncue-screening-room/bundle, the app opened as a module
window (990x613, not maximized). Steps follow oncue/docs/NATIVE-WORKFLOW.md.

- 06-030-module-layout.png — the two-column layout: left 样例舞台/载入群聊,
  现场原消息 (scrolls, #1/#2 visible), 我想接一句, the trial input and the
  试映下一幕 / 停止等待 row; right 三条路线/草稿与 A/B, A/B/C, 播放/下一句/重播;
  the fixed status at the bottom.
- 07/08 — B 换个问法 and C 换个玩法 with their 假设剧本 counters and 建议台词.
- 09 — after 播放: 假设剧本 · 1 / 3 行 and the button has become 暂停.
- 10 — after 暂停 plus five seconds (more than two intervals): still 1 / 3 行.
- 11 — A playing, switched to B, six seconds later B is still 0 / 2 行:
  the old A timer did not advance B.
- 12 — playing B, switched to the 草稿与 A/B workspace and back: still
  1 / 2 行, i.e. the workspace switch paused playback.
- 13 — typing one character into the left trial line clears the routes:
  status 台词已改变，可以重新试映。
- 14 — 存 A pressed with a non-empty draft: no file, no status change, the
  take list still shows the empty state. 保留这句 / 取回草稿 / 存 B / 取 A /
  取 B behave the same, while the draft input itself accepts typing, so the
  workspace is live but its buttons do not receive clicks.

## 0.3.1 (native-fill-last.patch), 2026-10-01 16:5x

Applied AI1's native-fill-last.patch on 9ccb859 (version 0.3.1, digest
574a1d9a matches the patch's claim), stamped, signed with the working key,
checked PASSED and published as catalog sequence 5.

- 15-031-rinx-review.png — Rinx Developer Review bundle for the working
  tree bundle: "OnCue · 群聊试映室 0.3.1 · Local unsigned bundle" with the
  six services. (The import path must be real; symlinks are refused.)
- 16/17 — the Rinx Developer host after Run, before and after pressing
  试映下一幕. The layout fix landed: the trial input and the
  试映下一幕/停止等待 row are now above the message area, so the buttons
  exist and the rehearsal starts in the shorter developer viewport too.
- 18 — the 990x613 module window: 现场原消息 shows #1 小林 and #2 阿柚
  (the sample messages appear again) with the buttons still reachable.
- 19 — the same window after 试映下一幕: 顺着这句, 假设剧本 · 0 / 3 行,
  the hint line and 建议台词 render in the right column.
- 20 — the 草稿与 A/B workspace in 0.3.1: 我的草稿 · 尚未发送, the draft
  box, 保留这句/取回草稿, 两个草稿版本, 存 A/存 B/取 A/取 B and the empty
  state. The save/restore round trip is still unverified: the draft box
  did not take the typed text in this session, so 存 A could not be
  exercised; recorded as pending, not as passing.
