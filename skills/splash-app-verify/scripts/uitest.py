#!/usr/bin/env python3
"""uitest: run a Splash script app's scenarios in card-host, the way a backend runs unit tests.

    uitest.py run <bundle> <scenario.json | directory> [--card-host PATH] [--out DIR] [--keep-going]
    uitest.py doctor [--card-host PATH]

A scenario is a JSON file: the host-service replies the app gets, files to put
in its storage jail before it starts, the window sizes to test, and steps that
act on the app and check what it shows. See references/SCENARIOS.md.

For each scenario and size the runner:

1. copies the bundle and prepends a fake `host` to the copy's `main.splash`
   (the source under test is otherwise byte-for-byte the original), so every
   `host.request` gets the scenario's reply instead of needing a real service;
2. starts card-host on the copy with a remote-control port, hidden, and on
   Linux under a private Xvfb display when there is none;
3. drives the steps through the remote routes (`/snap`, `/click`, `/t`, `/k`,
   `/m`), checks each expectation against the widget list, the calls the app
   made, the files in its jail and the runtime log;
4. on the first failure, writes the evidence and FEEDBACK.md: a repair request
   in the shape docs/MODEL-VALIDATION.md asks for, scoped to that one failure.

It never edits the bundle under test. Exit status: 0 all passed, 1 a scenario
failed, 2 the environment or a scenario file is broken.

Python 3.9+, standard library only.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
DEFAULT_SIZE = "412x892"
RUNTIME_ERROR_MARKERS = ("[E] splash", "on_render closure failed", "splash host callback error",
                         "isolate panic", "card-host: refused")
SHIM_BEGIN = "// ---- uitest fake host: test copy only ----"
SHIM_END = "// ---- end uitest fake host ----"


class ScenarioError(Exception):
    """The scenario file itself is wrong (not the app)."""


class StepFailed(Exception):
    def __init__(self, expected, actual, detail=None):
        super().__init__(expected)
        self.expected = expected
        self.actual = actual
        self.detail = detail or {}


# --------------------------------------------------------------- fake host
def splash_string(text):
    """A Splash double-quoted string literal for any text."""
    out = ['"']
    for ch in text:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def normalise_replies(host):
    """{service: reply | [reply, ...]} -> [{service, replies: [reply...]}] with full reply objects.

    A reply is {"data": …}, {"error": "…"} or {"never": true}, with an optional
    "delay" in seconds. A host answers every request once (SCRIPT-API: host
    services), so there is no form that calls back twice.
    """
    out = []
    for service, value in (host or {}).items():
        items = value if isinstance(value, list) else [value]
        if not items:
            raise ScenarioError(f"host replies for {service!r} are an empty list")
        replies = []
        for item in items:
            if not isinstance(item, dict) or not ({"data", "error", "never"} & set(item)):
                raise ScenarioError(f"host reply for {service!r} must be an object with \"data\", \"error\" "
                                    f"or \"never\", got {item!r}")
            if "stream" in item:
                raise ScenarioError(f"host reply for {service!r}: a host answers each request once; "
                                    "\"stream\" is not a reply form")
            if "error" in item:
                reply = {"is_ok": False, "data": None, "error": str(item["error"])}
            else:
                reply = {"is_ok": True, "data": item.get("data"), "error": ""}
            replies.append({"never": bool(item.get("never")), "delay": float(item.get("delay", 0.05)),
                            "reply": reply})
        out.append({"service": service, "replies": replies})
    return out


def shim_source(host):
    fixtures = json.dumps({"services": normalise_replies(host)}, ensure_ascii=False)
    return f"""{SHIM_BEGIN}
let uitest_real_host = host
let uitest_fx = {splash_string(fixtures)}.parse_json()
let uitest_calls = []
fn uitest_later(callback, reply, delay){{ start_timeout(delay, || callback(reply)) }}
fn uitest_answer(service, nth){{
    let fallback = nil
    for entry in uitest_fx.services {{
        if entry.service == service {{
            let k = nth
            if k >= entry.replies.len() {{ k = entry.replies.len() - 1 }}
            return entry.replies[k]
        }}
        if entry.service == "*" {{ fallback = entry.replies[0] }}
    }}
    if fallback != nil {{ return fallback }}
    let family = service.split(".")[0]
    {{never: false, delay: 0.05, reply: {{is_ok: false, data: nil, error: "no service answers \\"" + family + "\\" on this device"}}}}
}}
fn uitest_granted(service){{
    let family = service.split(".")[0]
    for c in uitest_real_host.capabilities() {{ if c == family || c == service {{ return true }} }}
    false
}}
let host = {{request: fn(service, args, callback){{
    let nth = 0
    for c in uitest_calls {{ if c.service == service {{ nth += 1 }} }}
    uitest_calls.push({{service: service, args: args, at: time_now()}})
    fs.write("uitest-calls.json", uitest_calls.to_json())
    // As on a real host, a fixture cannot answer a service the manifest does not request.
    if !uitest_granted(service) {{
        let family = service.split(".")[0]
        uitest_later(callback, {{is_ok: false, data: nil, error: "this app was not granted \\"" + family + "\\", which \\"" + service + "\\" needs"}}, 0.0)
        return uitest_calls.len()
    }}
    let answer = uitest_answer(service, nth)
    if !answer.never {{ uitest_later(callback, answer.reply, answer.delay) }}
    uitest_calls.len()
}}, has: fn(name){{ uitest_real_host.has(name) }}, capabilities: fn(){{ uitest_real_host.capabilities() }}}}
{SHIM_END}
"""


def prepare_copy(bundle, workdir, scenario):
    """Copy the bundle; prepend the fake host; make sure the copy may write its call log."""
    copy = workdir / "bundle"
    shutil.copytree(bundle, copy)
    main = copy / "main.splash"
    if not main.is_file():
        raise ScenarioError(f"{bundle} has no main.splash; uitest runs script apps")
    shim_lines = 0
    if scenario.get("fake_host", True):
        shim = shim_source(scenario.get("host"))
        shim_lines = shim.count("\n")
        main.write_text(shim + main.read_text(encoding="utf-8"), encoding="utf-8")
        manifest_path = copy / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        caps = manifest.setdefault("capabilities", [])
        if "storage" not in caps:  # the copy logs its calls to its own jail
            caps.append("storage")
        integrity = manifest.setdefault("integrity", {})
        integrity.pop("signature", None)
        integrity.pop("github", None)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return copy, shim_lines


# --------------------------------------------------------------- card-host
def find_card_host(explicit):
    candidates = [explicit, os.environ.get("OCTO_CARD_HOST")]
    for root in (os.environ.get("OCTOSENSE_APP_HUB"), os.environ.get("CARGO_TARGET_DIR")):
        if root:
            candidates += [str(Path(root) / "target/release/card-host"), str(Path(root) / "release/card-host")]
    candidates += [shutil.which("card-host")]
    for c in candidates:
        if c and Path(c).is_file() and os.access(c, os.X_OK):
            return str(Path(c).resolve())
    return None


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Display:
    """Use $DISPLAY or a native window system; on headless Linux start one private Xvfb."""

    def __init__(self):
        self.proc = None
        self.env = {}

    def __enter__(self):
        if sys.platform.startswith("linux") and not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
            xvfb = shutil.which("Xvfb")
            if not xvfb:
                raise RuntimeError("no display and no Xvfb: install xvfb (see scripts/setup.sh)")
            for n in range(90, 140):
                if not Path(f"/tmp/.X11-unix/X{n}").exists() and not Path(f"/tmp/.X{n}-lock").exists():
                    break
            self.proc = subprocess.Popen([xvfb, f":{n}", "-screen", "0", "1600x1200x24", "-nolisten", "tcp"],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for _ in range(50):
                if Path(f"/tmp/.X11-unix/X{n}").exists():
                    break
                time.sleep(0.1)
            self.env = {"DISPLAY": f":{n}", "LIBGL_ALWAYS_SOFTWARE": "1"}
        self.env["MAKEPAD_HIDE_WINDOWS"] = "1"
        return self

    def __exit__(self, *exc):
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(5)
            except subprocess.TimeoutExpired:
                self.proc.kill()


class App:
    def __init__(self, card_host, bundle, data_dir, size, log_path, env):
        self.port = free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        self.log_path = log_path
        self.data_dir = data_dir
        self.log_file = open(log_path, "w", encoding="utf-8", errors="replace")
        full_env = dict(os.environ, **env, MAKEPAD_REMOTE=str(self.port))
        self.proc = subprocess.Popen(
            [card_host, "--bundle", str(bundle), "--app-data", str(data_dir), "--allow-unsigned", "--stamp",
             "--size", size],
            stdout=self.log_file, stderr=subprocess.STDOUT, env=full_env, cwd=str(bundle.parent),
            start_new_session=True)
        self.log_seen = 0
        self.line_offset = 0

    def get(self, route, timeout=10.0, **params):
        query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        url = f"{self.base}{route}" + (f"?{query}" if query else "")
        with urllib.request.urlopen(url, timeout=timeout) as r:
            body = r.read()
        if route in ("/g", "/grab") and params.get("raw"):
            return body
        try:
            return json.loads(body.decode("utf-8"))
        except ValueError:
            return body.decode("utf-8", "replace")

    def log_text(self):
        try:
            return Path(self.log_path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""

    def wait_ready(self, timeout):
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(f"card-host exited ({self.proc.returncode}); see {self.log_path}")
            log = self.log_text()
            if "card-host: refused" in log:
                raise StepFailed("the bundle is admitted", "card-host refused it",
                                 {"log": [l for l in log.splitlines() if "refused" in l][-3:]})
            try:
                snap = self.get("/snap", timeout=3)
                if isinstance(snap, dict) and snap.get("s"):
                    time.sleep(0.3)  # let start_timeout(0.05, …) loaders run
                    return
                last = snap
            except (OSError, ValueError) as e:
                last = str(e)
            time.sleep(0.25)
        raise RuntimeError(f"card-host did not answer /snap with widgets in {timeout}s (last: {last!r}); see {self.log_path}")

    def snap(self):
        data = self.get("/snap")
        widgets = data.get("s", []) if isinstance(data, dict) else []
        # The `Splash` host widget reports the whole script source as its text;
        # it is not something the app shows.
        return [w for w in widgets if w.get("ty") != "Splash"]

    def new_runtime_errors(self):
        lines = self.log_text().splitlines()
        fresh = lines[self.log_seen:]
        self.log_seen = len(lines)
        errors = [l for l in fresh if any(m in l for m in RUNTIME_ERROR_MARKERS)]
        # Error positions count the test shim's lines; report them against main.splash.
        def shift(m):
            return f"splash:{m.group(1)}:{max(1, int(m.group(2)) - self.line_offset)}:{m.group(3)}"
        return [re.sub(r"splash:(\d+):(\d+):(\d+)", shift, l) for l in errors]

    def find_file(self, name):
        for p in Path(self.data_dir).rglob(name):
            if p.is_file() and ".host" not in p.parts:
                return p
        return None

    def calls(self):
        p = self.find_file("uitest-calls.json")
        if not p:
            return []
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            return []

    def peak_rss_mb(self):
        """card-host's peak resident memory (Linux), for the resource record."""
        try:
            for line in Path(f"/proc/{self.proc.pid}/status").read_text().splitlines():
                if line.startswith("VmHWM:"):
                    return round(int(line.split()[1]) / 1024, 1)
        except OSError:
            pass
        return None

    def close(self):
        if self.proc.poll() is None:
            try:
                self.get("/quit", timeout=3)
            except Exception:
                pass
            try:
                self.proc.wait(5)
            except subprocess.TimeoutExpired:
                os.killpg(self.proc.pid, signal.SIGTERM)
                try:
                    self.proc.wait(5)
                except subprocess.TimeoutExpired:
                    os.killpg(self.proc.pid, signal.SIGKILL)
        self.log_file.close()


# --------------------------------------------------------------- selectors and checks
def describe(sel):
    return json.dumps(sel, ensure_ascii=False) if not isinstance(sel, str) else f'"{sel}"'


def matches(w, sel):
    if isinstance(sel, str):
        sel = {"text": sel}
    text = (w.get("t") or "") + ("\n" + str(w["value"]) if w.get("value") not in (None, "") else "")
    if "id" in sel and w.get("i") != sel["id"]:
        return False
    if "type" in sel and w.get("ty") != sel["type"]:
        return False
    if "text" in sel and (w.get("t") or "").strip() != sel["text"]:
        return False
    if "contains" in sel and sel["contains"] not in text:
        return False
    return True


def find(widgets, sel):
    """All widgets matching sel, and the one it picks.

    `after` keeps only widgets listed after the first match of another
    selector: the button in the same card as a text, in a list without ids.
    `nth` counts what is on screen now, so it shifts when the view scrolls.
    """
    pool = widgets
    if isinstance(sel, dict) and "after" in sel:
        _, anchor = find(widgets, sel["after"])
        pool = widgets[widgets.index(anchor) + 1:] if anchor is not None else []
    found = [w for w in pool if matches(w, sel)]
    nth = sel.get("nth", 0) if isinstance(sel, dict) else 0
    return found, (found[nth] if len(found) > nth else None)


def nearest(widgets, sel, limit=5):
    """What the screen has that looks like the selector: for the feedback, not for passing."""
    key = sel if isinstance(sel, str) else (sel.get("text") or sel.get("contains") or sel.get("id") or "")
    key = str(key)
    scored = []
    for w in widgets:
        hay = f"{w.get('i','')} {w.get('t','')}"
        common = sum(1 for ch in set(key) if ch in hay)
        if common:
            scored.append((common, w))
    scored.sort(key=lambda x: -x[0])
    return [{"id": w.get("i"), "type": w.get("ty"), "text": w.get("t"), "rect": w.get("r")} for _, w in scored[:limit]]


def all_text(widgets):
    parts = []
    for w in widgets:
        if w.get("t"):
            parts.append(w["t"])
        if w.get("value") not in (None, ""):
            parts.append(str(w["value"]))
    return "\n".join(parts)


def inside(rect, view):
    x, y, w, h = rect
    vx, vy, vw, vh = view
    return x >= vx - 0.5 and y >= vy - 0.5 and x + w <= vx + vw + 0.5 and y + h <= vy + vh + 0.5


def clipped_by(widgets, w):
    """The container that cuts w off, if any.

    /snap reports the visible part of a widget inside a scroll view, so a
    half-hidden button looks like a short one. Its cut edge then lies exactly
    on the scroll view's edge, which a laid-out child (with padding) does not.
    """
    x, y, ww, hh = w["r"]
    for c in widgets:
        if c is w or c.get("ty") in ("Window", "KeyboardView"):
            continue
        cx, cy, cw, ch = c["r"]
        if ch < 2 * hh + 20 or not inside(w["r"], c["r"]):
            continue
        if abs(y - cy) < 0.5 or abs((y + hh) - (cy + ch)) < 0.5:
            return c
    return None


def fully_visible(widgets, w, view):
    return inside(w["r"], view) and clipped_by(widgets, w) is None


def check_expectation(app, exp, view):
    """Raise StepFailed unless every clause of exp holds now."""
    widgets = app.snap()
    text = all_text(widgets)
    for t in exp.get("text", []):
        if t not in text:
            raise StepFailed(f'text "{t}" is shown', "not on screen",
                             {"similar": nearest(widgets, {"contains": t})})
    for t in exp.get("absent", []):
        if t in text:
            hits = [{"id": w.get("i"), "text": w.get("t"), "rect": w.get("r")} for w in widgets if t in (w.get("t") or "")]
            raise StepFailed(f'text "{t}" is not shown', "it is on screen", {"widgets": hits[:5]})
    for sel in exp.get("in_view", []):
        found, w = find(widgets, sel)
        if not w:
            raise StepFailed(f"{describe(sel)} is fully inside the viewport {view}", "no such widget",
                             {"similar": nearest(widgets, sel)})
        if not inside(w["r"], view):
            x, y, ww, hh = w["r"]
            over = {"right": round(x + ww - (view[0] + view[2]), 1), "bottom": round(y + hh - (view[1] + view[3]), 1)}
            raise StepFailed(f"{describe(sel)} is fully inside the viewport {view}",
                             f"its rect is {w['r']}: past the right edge by {over['right']} and the bottom by {over['bottom']} points",
                             {"widget": {"id": w.get("i"), "type": w.get("ty"), "text": w.get("t"), "rect": w.get("r")}})
        cut = clipped_by(widgets, w)
        if cut is not None:
            raise StepFailed(f"{describe(sel)} is fully inside the viewport {view}",
                             f"only {w['r']} of it shows: the scroll view {cut.get('i') or cut.get('ty')} {cut['r']} cuts it off",
                             {"widget": {"id": w.get("i"), "type": w.get("ty"), "text": w.get("t"), "rect": w.get("r")}})
    for sel in exp.get("enabled", []):
        _, w = find(widgets, sel)
        if not w or not w.get("enabled", True):
            raise StepFailed(f"{describe(sel)} is enabled", "missing" if not w else "disabled", {})
    for sel in exp.get("disabled", []):
        _, w = find(widgets, sel)
        if not w or w.get("enabled", True):
            raise StepFailed(f"{describe(sel)} is disabled", "missing" if not w else "enabled", {})
    for item in exp.get("count", []):
        found, _ = find(widgets, item["of"])
        if len(found) != item["n"]:
            raise StepFailed(f"{item['n']} widgets match {describe(item['of'])}", f"{len(found)} match", {})
    for item in exp.get("calls", []):
        calls = [c for c in app.calls() if c.get("service") == item["service"]]
        if "contains" in item:
            calls = [c for c in calls if item["contains"] in json.dumps(c.get("args"), ensure_ascii=False)]
        want = item.get("count")
        if (want is None and not calls and "excludes" not in item) or (want is not None and len(calls) != want):
            raise StepFailed(f"{'≥1' if want is None else want} call(s) to {item['service']}"
                             + (f" with args containing \"{item['contains']}\"" if "contains" in item else ""),
                             f"{len(calls)} such call(s)", {"calls": app.calls()[-5:]})
        if "excludes" in item:
            leaked = [c for c in calls if item["excludes"] in json.dumps(c.get("args"), ensure_ascii=False)]
            if leaked:
                raise StepFailed(f"no call to {item['service']} sends \"{item['excludes']}\"",
                                 f"{len(leaked)} call(s) do", {"calls": leaked[-2:]})
    for item in exp.get("files", []):
        p = app.find_file(item["name"])
        if item.get("missing"):
            if p:
                raise StepFailed(f"no file {item['name']} in the jail", f"{p} exists", {})
            continue
        if not p:
            raise StepFailed(f"file {item['name']} in the jail", "missing", {})
        body = p.read_text(encoding="utf-8", errors="replace")
        for c in item.get("contains", []):
            if c not in body:
                raise StepFailed(f"{item['name']} contains \"{c}\"", "it does not", {"head": body[:400]})


def wait_for(app, exp, view, timeout):
    deadline = time.time() + timeout
    while True:
        try:
            check_expectation(app, exp, view)
            return
        except StepFailed:
            if time.time() >= deadline:
                raise
            time.sleep(0.2)


def center(rect):
    x, y, w, h = rect
    return round(x + w / 2, 1), round(y + h / 2, 1)


def scroll_into_view(app, sel, on, view, attempts):
    """Scroll, as a person would, until the widget lies wholly inside the viewport.

    Works at every size without per-size distances. Fails when the widget is
    taller than the viewport or scrolling stops moving anything.
    """
    vx, vy, vw, vh = view
    ratio = 1.0          # measured content movement per unit of scroll
    before = None        # (target y, dy) of the previous attempt
    last_sig = None
    direction = 1        # while the widget is not listed: search down, then up
    for _ in range(attempts):
        widgets = app.snap()
        _, w = find(widgets, sel)
        if w and fully_visible(widgets, w, view):
            return
        if w and w["r"][3] > vh + 0.5:
            raise StepFailed(f"{describe(sel)} fits inside the viewport {view}",
                             f"it is {w['r'][3]} points tall", {"rect": w["r"]})
        sig = json.dumps([x.get("r") for x in widgets])
        if sig == last_sig:
            if not w and direction == 1:
                direction = -1  # reached the end without seeing it: look above
            else:
                raise StepFailed(f"{describe(sel)} can be scrolled into the viewport {view}",
                                 "scrolling no longer moves anything" + ("" if w else "; the widget never appeared"),
                                 {"similar": nearest(widgets, sel)} if not w else {"rect": w["r"]})
        last_sig = sig
        if w:
            y, h = w["r"][1], w["r"][3]
            if before is not None and before[1]:
                moved = before[0] - y
                if moved and (moved / before[1]) > 0:
                    ratio = moved / before[1]
            cut = clipped_by(widgets, w)
            if cut is not None:
                # Only its visible part is listed: move a third of a screen toward the cut edge.
                at_bottom = abs((y + h) - (cut["r"][1] + cut["r"][3])) < 0.5
                dy = (1 if at_bottom else -1) * vh * 0.33 / ratio
                before = None
            else:
                need = (y + h) - (vy + vh) + 12 if y + h > vy + vh else y - vy - 12
                dy = need / ratio
                before = (y, dy)
        else:
            dy = direction * vh * 0.6
            before = None
        if on:
            _, host_w = find(widgets, on)
            if not host_w:
                raise StepFailed(f"a widget {describe(on)} to scroll", "no such widget", {})
            px, py = center(host_w["r"])
        else:
            px, py = vx + vw / 2, vy + vh / 2
        app.get("/m", k="scroll", x=round(px, 1), y=round(py, 1), dy=round(dy, 1), wait=1)
    raise StepFailed(f"{describe(sel)} can be scrolled into the viewport {view}",
                     f"still outside after {attempts} scrolls", {})


def do_step(app, step, view):
    if "click" in step:
        sel = step["click"]
        widgets = app.snap()
        _, w = find(widgets, sel)
        if not w:
            raise StepFailed(f"a widget {describe(sel)} to click", "no such widget on screen",
                             {"similar": nearest(widgets, sel)})
        if not inside(w["r"], view):
            raise StepFailed(f"{describe(sel)} is inside the viewport so a person can click it",
                             f"its rect is {w['r']}, viewport {view}", {})
        x, y = center(w["r"])
        app.get("/click", x=x, y=y, wait=1)
    elif "type" in step:
        spec = step["type"]
        if "into" in spec:
            do_step(app, {"click": spec["into"]}, view)
            if spec.get("clear"):
                # The click leaves the caret wherever it landed: delete on both sides of it.
                _, w = find(app.snap(), spec["into"])
                n = len(str((w or {}).get("value") or (w or {}).get("t") or "")) + 2
                for key in ("Delete", "Backspace"):
                    for _ in range(n):
                        app.get("/k", k="down", c=key)
        app.get("/t", t=spec["text"], wait=1)
    elif "key" in step:
        app.get("/k", k="down", c=step["key"], wait=1)
        app.get("/k", k="up", c=step["key"], wait=1)
    elif "scroll" in step:
        spec = step["scroll"]
        _, w = find(app.snap(), spec["on"])
        if not w:
            raise StepFailed(f"a widget {describe(spec['on'])} to scroll", "no such widget", {})
        x, y = center(w["r"])
        app.get("/m", k="scroll", x=x, y=y, dy=spec.get("dy", 300), wait=1)
    elif "scroll_to" in step:
        targets = step["scroll_to"] if isinstance(step["scroll_to"], list) else [step["scroll_to"]]
        for sel in targets:
            scroll_into_view(app, sel, step.get("on"), view, int(step.get("max", 25)))
    elif "sleep" in step:
        time.sleep(float(step["sleep"]))
    elif "expect" in step:
        wait_for(app, step["expect"], view, float(step.get("timeout", 2.0)))
    elif "wait" in step:
        wait_for(app, step["wait"], view, float(step.get("timeout", 10.0)))
    else:
        raise ScenarioError(f"unknown step {step!r}")
    errors = app.new_runtime_errors()
    if errors and not step.get("allow_runtime_errors"):
        raise StepFailed("no runtime error in the log", errors[-1], {"log": errors[-5:]})


# --------------------------------------------------------------- run and report
def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def feedback(result, bundle, card_host):
    s = result
    steps = "\n".join(f"  {i + 1}. {json.dumps(st, ensure_ascii=False)}" for i, st in enumerate(s["steps_run"]))
    detail = json.dumps(s["detail"], ensure_ascii=False, indent=2) if s["detail"] else "(none)"
    return f"""# Repair request: {s['scenario']} @ {s['size']}

Artifact: {bundle}/main.splash, sha256 {s['source_sha256']}.
Runtime: card-host {card_host}, window {s['size']}, viewport {s['viewport']}; host services are the scenario's fixtures.
Start state: a fresh launch of scenario "{s['scenario']}" ({s['file']}); storage seeded as the scenario says.

Steps (the last one failed):
{steps}

Expected: {s['expected']}
Actual: {s['actual']}
Details:
```json
{detail}
```
Evidence: {s['evidence'].get('snap')}, {s['evidence'].get('log')}{', ' + s['evidence']['png'] if s['evidence'].get('png') else ''}

Fix: change only what makes this step pass. Keep widget ids, button texts and the behavior other scenarios check.
Retest: run every scenario again (`uitest.py run <bundle> <scenarios>`); report what still fails. Do not score yourself.
"""


def copy_jail(jail, dest, limit=4 * 1024 * 1024):
    """Copy the app's own files (not the host's, not the call log) if they are small enough."""
    files = [p for p in Path(jail).rglob("*") if p.is_file() and ".host" not in p.relative_to(jail).parts
             and p.name != "uitest-calls.json"] if Path(jail).is_dir() else []
    if not files or sum(p.stat().st_size for p in files) > limit:
        return False
    for p in files:
        target = dest / p.relative_to(jail)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, target)
    return True


def run_one(card_host, bundle, scenario_path, scenario, size, out_dir, display):
    view_cfg = scenario.get("viewport")
    w, h = (float(v) for v in size.lower().split("x"))
    view = view_cfg if view_cfg else [0, 0, w, h]
    tag = f"{scenario_path.stem}@{size}"
    work = Path(tempfile.mkdtemp(prefix="uitest-"))
    run_dir = out_dir / tag
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)
    result = {"scenario": scenario.get("name", scenario_path.stem), "file": str(scenario_path), "size": size,
              "viewport": view, "source_sha256": sha256(bundle / "main.splash"), "passed": False,
              "steps_run": [], "evidence": {}}
    app = None
    jail = work / "data"
    started = time.time()
    try:
        copy, shim_lines = prepare_copy(bundle, work, scenario)
        data = work / "data"
        manifest = json.loads((copy / "manifest.json").read_text(encoding="utf-8"))
        jail = data / manifest.get("id", "app")
        for name, body in (scenario.get("storage") or {}).items():
            target = jail / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body if isinstance(body, str) else json.dumps(body, ensure_ascii=False), encoding="utf-8")
        app = App(card_host, copy, data, size, run_dir / "card-host.log", display.env)
        app.line_offset = shim_lines
        app.wait_ready(float(scenario.get("startup_timeout", 60)))
        errors = app.new_runtime_errors()
        if errors and not scenario.get("allow_runtime_errors"):
            raise StepFailed("the app starts without a runtime error", errors[-1], {"log": errors[-5:]})
        for step in scenario.get("steps", []):
            result["steps_run"].append(step)
            do_step(app, step, view)
        result["passed"] = True
    except StepFailed as f:
        result.update(expected=f.expected, actual=f.actual, detail=f.detail)
    except ScenarioError:
        raise
    except Exception as e:  # environment trouble: report, do not blame the app
        result.update(expected="the runner reaches the step", actual=f"{type(e).__name__}: {e}", detail={},
                      environment_error=True)
    finally:
        result["seconds"] = round(time.time() - started, 2)
        if app:
            if not result["passed"]:
                try:
                    (run_dir / "snap.json").write_text(json.dumps(app.get("/snap"), ensure_ascii=False, indent=1))
                    result["evidence"]["snap"] = str(run_dir / "snap.json")
                    png = app.get("/g", raw=1, timeout=20)
                    if isinstance(png, (bytes, bytearray)) and png[:4] == b"\x89PNG":
                        (run_dir / "screen.png").write_bytes(png)
                        result["evidence"]["png"] = str(run_dir / "screen.png")
                except Exception:
                    pass
            calls = app.calls()
            (run_dir / "calls.json").write_text(json.dumps(calls, ensure_ascii=False, indent=1))
            result["peak_rss_mb"] = app.peak_rss_mb()
            app.close()
            result["evidence"]["log"] = str(run_dir / "card-host.log")
            # What the app left in its jail: evidence, and a seed for a restart scenario.
            kept = copy_jail(jail, run_dir / "jail")
            if kept:
                result["evidence"]["jail"] = str(run_dir / "jail")
        shutil.rmtree(work, ignore_errors=True)
    if not result["passed"]:
        (run_dir / "FEEDBACK.md").write_text(feedback(result, bundle, card_host), encoding="utf-8")
        result["feedback"] = str(run_dir / "FEEDBACK.md")
    (run_dir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    return result


STEP_KEYS = {"click", "type", "key", "scroll", "scroll_to", "sleep", "expect", "wait"}
SHARED_KEYS = ("sizes", "size", "viewport", "startup_timeout", "fake_host", "allow_runtime_errors")


def read_json(f):
    try:
        return json.loads(Path(f).read_text(encoding="utf-8"))
    except OSError as e:
        raise ScenarioError(f"{f}: cannot read ({e})")
    except ValueError as e:
        raise ScenarioError(f"{f}: not JSON ({e})")


def expand_steps(steps, base, f, depth=0):
    """Inline {"run": "_part.json"} steps: shared step sequences such as "load the room"."""
    if depth > 5:
        raise ScenarioError(f"{f}: \"run\" nests more than 5 deep")
    out = []
    for step in steps:
        if not isinstance(step, dict):
            raise ScenarioError(f"{f}: a step is an object, got {step!r}")
        if "run" in step:
            part = base / step["run"]
            data = read_json(part)
            if not isinstance(data, dict) or not isinstance(data.get("steps"), list):
                raise ScenarioError(f"{part}: a part used by \"run\" is an object with a \"steps\" list")
            out += expand_steps(data["steps"], part.parent, part, depth + 1)
            continue
        if not (STEP_KEYS & set(step)):
            raise ScenarioError(f"{f}: unknown step {step!r}; a step has one of {sorted(STEP_KEYS)} or \"run\"")
        out.append(step)
    return out


def resolve_scenario(f, data):
    """Apply "use" (shared host replies, storage and sizes from _parts) and expand "run" steps."""
    base = Path(f).parent
    uses = data.get("use", [])
    uses = [uses] if isinstance(uses, str) else uses
    host, storage, shared = {}, {}, {}
    for name in uses:
        part = read_json(base / name)
        if not isinstance(part, dict):
            raise ScenarioError(f"{base / name}: a part is an object")
        host.update(part.get("host") or {})
        storage.update(part.get("storage") or {})
        shared.update({k: part[k] for k in SHARED_KEYS if k in part})
    out = dict(shared)
    out.update({k: v for k, v in data.items() if k != "use"})
    out["host"] = dict(host, **(data.get("host") or {}))
    out["storage"] = dict(storage, **(data.get("storage") or {}))
    out["steps"] = expand_steps(data["steps"], base, f)
    return out


def load_scenarios(target):
    """Every *.json in name order; files whose names start with "_" are parts, not scenarios."""
    target = Path(target)
    files = sorted(p for p in target.glob("*.json") if not p.name.startswith("_")) if target.is_dir() else [target]
    out = []
    for f in files:
        data = read_json(f)
        if not isinstance(data, dict) or not isinstance(data.get("steps"), list):
            raise ScenarioError(f"{f}: a scenario is an object with a \"steps\" list")
        scenario = resolve_scenario(f, data)
        normalise_replies(scenario["host"])  # report a bad fixture before anything starts
        out.append((f, scenario))
    if not out:
        raise ScenarioError(f"no scenario files in {target}")
    return out


def cmd_run(args):
    bundle = Path(args.bundle).resolve()
    card_host = find_card_host(args.card_host)
    if not card_host:
        print("uitest: card-host not found; pass --card-host or set OCTO_CARD_HOST (scripts/setup.sh builds it)", file=sys.stderr)
        return 2
    try:
        scenarios = load_scenarios(args.scenarios)
    except ScenarioError as e:
        print(f"uitest: {e}", file=sys.stderr)
        return 2
    out_dir = Path(args.out or (bundle.parent / "build" / "uitest")).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    with Display() as display:
        for path, sc in scenarios:
            sizes = sc.get("sizes") or [sc.get("size") or DEFAULT_SIZE]
            for size in sizes:
                try:
                    r = run_one(card_host, bundle, path, sc, size, out_dir, display)
                except ScenarioError as e:
                    print(f"uitest: {path}: {e}", file=sys.stderr)
                    return 2
                results.append(r)
                mark = "PASS" if r["passed"] else ("ENV " if r.get("environment_error") else "FAIL")
                mem = f", {r['peak_rss_mb']} MB" if r.get("peak_rss_mb") else ""
                print(f"{mark} {r['scenario']} @ {r['size']} ({r['seconds']}s{mem})")
                if not r["passed"]:
                    print(f"     expected: {r['expected']}\n     actual:   {r['actual']}\n     feedback: {r['feedback']}")
                    if not args.keep_going:
                        break
            if results and not results[-1]["passed"] and not args.keep_going:
                break
    summary = {"bundle": str(bundle), "card_host": card_host, "passed": sum(r["passed"] for r in results),
               "failed": sum(not r["passed"] for r in results), "results": results}
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"{summary['passed']} passed, {summary['failed']} failed; details in {out_dir}")
    if any(r.get("environment_error") for r in results):
        return 2
    return 0 if summary["failed"] == 0 else 1


def cmd_doctor(args):
    ok = True
    card_host = find_card_host(args.card_host)
    print(f"[{'ok' if card_host else 'fail'}] card-host: {card_host or 'not found (scripts/setup.sh, or --card-host)'}")
    ok &= bool(card_host)
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        x = shutil.which("Xvfb")
        print(f"[{'ok' if x else 'fail'}] display: none; Xvfb {'found at ' + x if x else 'missing (apt install xvfb)'}")
        ok &= bool(x)
    else:
        print("[ok] display: available")
    print(f"[ok] python {sys.version.split()[0]}")
    return 0 if ok else 2


def main(argv=None):
    p = argparse.ArgumentParser(prog="uitest.py", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run scenarios against a bundle")
    r.add_argument("bundle")
    r.add_argument("scenarios", help="a scenario .json file or a directory of them")
    r.add_argument("--card-host")
    r.add_argument("--out", help="evidence directory (default <app>/build/uitest)")
    r.add_argument("--keep-going", action="store_true", help="run every scenario even after a failure")
    d = sub.add_parser("doctor", help="check that card-host and a display are available")
    d.add_argument("--card-host")
    args = p.parse_args(argv)
    return cmd_run(args) if args.cmd == "run" else cmd_doctor(args)


if __name__ == "__main__":
    sys.exit(main())
