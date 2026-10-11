# Titled Notes

A small script app in the [narrow shape](../../references/SHAPE.md): notes kept
on the device, and a "Suggest a title" button that asks the host's
`model.complete` once. Its scenarios cover the first screen at two sizes, the
main action, an empty input, a restart, a corrupt store, a title from the
model, the model refusing on budget, no model service at all, and a model that
never answers.

```sh
python3 skills/splash-app-verify/scripts/uitest.py run \
  skills/splash-app-verify/examples/titled-notes/bundle \
  skills/splash-app-verify/examples/titled-notes/tests --out /tmp/uitest-titled --keep-going
```

Recorded on 2026-10-09 (Linux x86_64, 2 cores, Xvfb with Mesa llvmpipe, card-host
built from App Hub `18cd41d`): all 10 runs pass. Each takes 0.8–1.3 s, except the
"never answers" scenario, which waits out the app's own 20-second timer. card-host's
peak resident memory was 242–245 MB in every run.

## The braced `else` in `on_render`

Change the list to `if notes.len() == 0 { Label{…} } else { for … }` and run the
same scenarios: `01-first-screen` fails at both sizes and `05-corrupt-store`
fails, each with `text "No notes yet." is shown` / `not on screen`. That is the
documented `else for` gotcha in its braced form; see
[SCRIPT-API](../../../../docs/SCRIPT-API.md#gotchas).
