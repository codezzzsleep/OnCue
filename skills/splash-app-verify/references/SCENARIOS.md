# Scenario files

One JSON file per behavior, kept in `<app>/tests/` beside `bundle/`. The runner
reads every `*.json` in the directory, in name order. Name them by contract
row: `01-first-screen.json`, `02-add-note.json`, `03-read-fails.json`. Files
whose names start with `_` are shared parts, not scenarios.

```json
{
  "name": "a message that arrived before sending is shown, and sending waits for a second confirmation",
  "use": "_room.json",
  "sizes": ["412x892", "954x448"],
  "host": {
    "matrix.read_messages": [
      {"data": {"messages": [{"sender": "ann", "sender_id": "@ann:example.org", "event_id": "$1", "body": "noon works", "ts": 1, "msgtype": "m.text"}]}},
      {"data": {"messages": []}, "delay": 1.5},
      {"error": "Mini-app authorization expired"}
    ],
    "matrix.send_message": {"data": {}}
  },
  "steps": [
    {"run": "_load.json"},
    {"scroll_to": {"id": "draft"}},
    {"type": {"into": {"id": "draft"}, "text": "see you at noon", "clear": true}},
    {"scroll_to": "Send"},
    {"click": "Send"},
    {"wait": {"text": ["Check the room and the text"]}, "timeout": 5},
    {"scroll_to": [{"contains": "see you at noon"}, {"text": "Confirm", "after": {"contains": "Room: Trip"}}]},
    {"expect": {"calls": [{"service": "matrix.send_message", "count": 0}]}}
  ]
}
```

## Top-level fields

| Field | Meaning | Default |
| --- | --- | --- |
| `name` | Shown in results and in `FEEDBACK.md` | the file name |
| `use` | A part (`"_room.json"`) or a list of them: their `host` replies, `storage` and shared fields fill in what this scenario does not set | none |
| `sizes` (or `size`) | Window sizes, `WxH` in layout points; the scenario runs once per size from a fresh launch | `412x892`, card-host's default |
| `viewport` | `[x, y, w, h]` that must hold what `in_view` lists | the whole window |
| `storage` | Files written into the app's jail before it starts: text, or JSON for an object | none |
| `host` | Replies for `host.request`, by service name; see below | every call answers `no service answers "<family>" on this device`, as card-host does |
| `fake_host` | `false` runs the bundle as it is, with card-host's real (empty) services | `true` |
| `startup_timeout` | Seconds to wait for the first widgets | 60 |
| `allow_runtime_errors` | `true` stops a runtime error in the log from failing the scenario | `false` |

Size the app the way its hosts do. A shell that gives the app part of its
window gives it a smaller rectangle than the window: measure that rectangle
from a screenshot of the shell and test that size.

## Shared parts

A part is a JSON file whose name starts with `_`. A scenario takes its fixtures
with `"use"`, and its steps with a `{"run": "_part.json"}` step, which the
runner replaces by the part's `steps`. Keep one part for the host replies of
the normal path (`_room.json`) and one for each sequence many scenarios repeat
(`_load.json`, `_confirm.json`). A scenario then states only what differs:
the one reply that fails, the steps after it, the checks.

## Host replies

A service maps to one reply, used for every call, or to a list, used in call
order with the last one repeating. `"*"` answers any service not listed.

| Reply | The app's callback gets |
| --- | --- |
| `{"data": …}` | `{is_ok: true, data: …, error: ""}` |
| `{"error": "text"}` | `{is_ok: false, data: nil, error: "text"}` |
| `{"never": true}` | No callback: test the app's own timeout or stop button |
| `"delay": seconds` | Wait before the callback (default 0.05); use it to test a second click while a request is out |

A host answers each request once ([SCRIPT-API](../../../docs/SCRIPT-API.md#host-services-hostrequest)),
so a reply is one callback. As on a real host, a service the manifest does not
request answers `this app was not granted "<family>", which "<service>" needs`,
whatever the fixture says.

Copy reply shapes and error texts from the host's source or documentation, and
name the source in the contract. A fixture the real host could never send
tests nothing. Write the failure texts the host really produces, such as
`Mini-app authorization expired` or `no service answers "matrix" on this device`.

The fake `host` keeps `has` and `capabilities` from the real one. Every call is
logged to `uitest-calls.json` in the copy's jail, which the `calls` check reads;
the runner adds `storage` to the copy's manifest for that file.

## Steps

| Step | Does |
| --- | --- |
| `{"click": SELECTOR}` | Clicks the centre of the matching widget's visible part. Fails when none is on screen or it lies outside the viewport |
| `{"type": {"into": SELECTOR, "text": "…", "clear": true}}` | Clicks the field, optionally deletes its current text, types |
| `{"key": "ReturnKey"}` | Presses and releases a key (`Escape`, `Tab`, `Backspace`, …) |
| `{"scroll_to": SELECTOR}` | Scrolls until the widget is wholly inside the viewport, at any size; a list scrolls to each in turn. Fails when it never appears or does not fit. `"on": SELECTOR` scrolls over that widget instead of the viewport's centre |
| `{"scroll": {"on": SELECTOR, "dy": 300}}` | Scrolls over a widget by a fixed amount; prefer `scroll_to` |
| `{"expect": CHECKS, "timeout": 2}` | The checks must hold within the timeout |
| `{"wait": CHECKS, "timeout": 10}` | The same, for slower changes |
| `{"sleep": 0.5}` | Waits; prefer `wait` |
| `{"run": "_part.json"}` | The part's steps, in place |

Any step may add `"allow_runtime_errors": true`, and a `"note"` that says why
the step is there.

A `SELECTOR` is a string, matched against a widget's whole text, or an object:

| Key | Matches |
| --- | --- |
| `id` | The widget's `name :=` id |
| `text` | Its whole text, trimmed |
| `contains` | Part of its text or of an input's value |
| `type` | Its widget type, such as `TextInput` |
| `after` | Only widgets listed after the first match of this selector: the button in the same card as a text, in a list whose rows have no ids |
| `nth` | Which match, from 0, among those on screen now |

## Checks

| Check | Holds when |
| --- | --- |
| `"text": ["…"]` | Each text appears in some widget on screen, in its text or input value |
| `"absent": ["…"]` | No widget on screen shows the text |
| `"in_view": [SELECTOR]` | The widget is wholly inside the viewport and no scroll view cuts it off |
| `"enabled"` / `"disabled": [SELECTOR]` | The widget exists and is (not) enabled |
| `"count": [{"of": SELECTOR, "n": 3}]` | Exactly n widgets on screen match |
| `"calls": [{"service": "…", "count": 1, "contains": "…", "excludes": "…"}]` | The app made that many calls to the service; `contains` filters by the JSON of the arguments; without `count`, at least one; `excludes` fails if any of those calls sends the text (a name that must not reach a model, say) |
| `"files": [{"name": "…", "contains": ["…"]}]` | The jail has the file and it contains each text; `"missing": true` requires its absence |

## What the runner sees

The runner reads `/snap`, which lists the widgets on screen, the way a person
sees the app:

- A widget inside a scroll view is listed only while it is scrolled into view,
  and a half-hidden one is reported by its visible part. `in_view` and
  `scroll_to` recognise a widget cut off at a scroll view's edge.
- `text`, `absent` and `count` judge what is on screen now. Scroll to the part
  of the app first: an `absent` over an area that is off screen passes without
  testing anything.
- `nth` counts what is on screen, so it shifts when the view scrolls; use
  `after` or an `id`.
- A `TextInput`'s text is its value, or its placeholder while it is empty.

A widget can be drawn yet not readable this way (text clipped inside its own
box, colour, overlap); that is for the visual review.

After every run the runner copies the app's jail to `<out>/<scenario>@<size>/jail/`:
evidence of what the app wrote, and the seed for a restart scenario's `storage`.
