# 0.4.4 playback source correction (AI1 review)

Scope: source review only. This is not a native-host PASS and it does not
replace the required Rinx/Card-host interaction evidence.

The first 0.4.4 pagination candidate had changed playback into automatic page
navigation. The UI exposed `上一页 / 下一页 / 重播`, while the README and
listing still promised `播放 / 暂停 / 逐句 / 重播`. That was a product-level
semantic mismatch: a visual page may contain part of one long sentence or
several short lines.

The corrected source restores the earlier line-by-line state machine and keeps
pagination as an independent reading control:

- Selecting A/B/C splits the route body on newlines and starts at `0 / N`.
- `下一句` reveals one model-output line and remains paused.
- `播放` reveals one line per timer pulse; `暂停` invalidates the old timer via
  the existing epoch check.
- `重播` returns to `0 / N`; the next play starts from the first line.
- The visible prefix is repaginated after each reveal, and the reader moves to
  the last page so that a long revealed line remains readable.
- The suggested draft appears after all hypothetical lines have been revealed.
  It is still editable and is never sent automatically.

Before accepting this change, AI2 must run the same native 0.4.4 candidate and
record at least: one manual `下一句`, play → pause across two timer intervals,
resume to completion, replay from zero, route switch invalidating the old
timer, and a long revealed line spanning multiple visual pages. Both 412x892
and 990x613 layouts must keep every control reachable. The bundle digest must
be refreshed after applying this source change; the current recorded digest is
expected to be stale until that happens.
