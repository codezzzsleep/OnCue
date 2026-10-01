# AI1 review of the 0.4.2 candidate

Reviewed 2026-10-01 against GitHub main `f6a0f18` and the signed candidate
`79a018e3625a54ef81b8dfeedcfa17d82f7d472f`.

## Evidence accepted within its scope

- AI2's two card-host click logs each record 16 passing checks, using actual
  status, input and counter values: sample rehearsal, route selection, filling
  a draft, storing two different drafts, restoring them and playback controls.
- The geometry report gives nonzero rectangles within both window bounds for
  the action buttons. This supports action reachability, not full text visibility.
- The freeze transcript records stamp, signature, admission, scan, local catalog
  publication and sequence-8 verification. Its reviewer explicitly describes a
  source-level assessment. This is a local publishing rehearsal, not official
  App Hub submission or complete runtime acceptance.
- AI1 independently opened both submitted PNGs. They are real rendered evidence,
  with visible application text. AI1 did not execute these card-host instances.

## Blocking findings in the actual PNGs

| Window | Visible limitation |
| --- | --- |
| 990 × 613 | Only source #1 is fully readable. Source #2 is clipped after its first line; the budget and fourth source cannot be read. The first hypothetical reply is cut off, and the remaining reply, evidence and suggested draft are outside the visible preview. |
| 412 × 892 | Source #4 is cut off. The suggested draft is cut off near the bottom of the preview, and the long status crosses the content boundary. A complete reading flow is not demonstrated. |

Both PNGs display the play button and `3 / 3` counter, rather than an active
pause button. The capture-state description and the claim that approximately
three source messages remain visible at 990 × 613 need correction.

The earlier 55-pixel measurement was for the inner `Fit` preview list, not its
parent scroll viewport. That measurement alone was not a verified layout defect.
The PNGs above are the basis for the blocking findings.

AI2 reports that scrolling did not work in its tested card-host build. This is a
reported limitation of that build, not evidence that scrolling is unavailable in
every Makepad, Shell or Rinx host.

## Required follow-up

Keep the verified action logic. Provide a complete reading path for original
messages, hypothetical replies, suggested drafts and both saved drafts. If the
tested host cannot scroll, explicit page or item navigation is acceptable; show
position and total, preserve all text, and make long text fully reachable. Verify
both windows with expanded PNGs and page-by-page value checks, including twelve
source messages and longer generated text. Status text must not overlap content.

The current candidate is not accepted as the final deliverable. Preserve its
published local history. A revised release needs a new version, updated screenshots
and listing, fresh stamp/sign/check, the exact signed commit pushed to main before
publication, and refreshed review records. Real Rinx room reading and shared
Octos generation remain pending and must continue after the basic release is ready.
