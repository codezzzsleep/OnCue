"""uitest regressions that need no card-host: fixtures, the fake host source, selectors, checks, feedback."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import uitest  # noqa: E402

WIDGETS = [
    {"i": "title", "ty": "Label", "r": [16, 16, 380, 30], "t": "Titled Notes"},
    {"i": "entry", "ty": "TextInput", "r": [16, 60, 300, 40], "t": "", "value": "Call the plumber"},
    {"i": "keep_button", "ty": "ButtonFlat", "r": [320, 60, 76, 40], "t": "Keep", "enabled": True},
    {"i": "title_button", "ty": "ButtonFlat", "r": [16, 900, 160, 40], "t": "Suggest a title", "enabled": False},
    {"i": "", "ty": "Label", "r": [16, 120, 380, 20], "t": "No notes yet."},
]


class FakeApp:
    def __init__(self, widgets, calls=(), files=None):
        self.widgets, self._calls, self.files = widgets, list(calls), files or {}

    def snap(self):
        return self.widgets

    def calls(self):
        return self._calls

    def find_file(self, name):
        return self.files.get(name)


class Fixtures(unittest.TestCase):
    def test_reply_forms(self):
        out = uitest.normalise_replies({
            "a.b": {"data": {"x": 1}},
            "c.d": [{"error": "nope", "delay": 1}, {"never": True}],
        })
        by = {e["service"]: e["replies"] for e in out}
        self.assertEqual(by["a.b"][0]["reply"], {"is_ok": True, "data": {"x": 1}, "error": ""})
        self.assertEqual(by["c.d"][0]["reply"]["is_ok"], False)
        self.assertEqual(by["c.d"][0]["delay"], 1.0)
        self.assertTrue(by["c.d"][1]["never"])

    def test_bad_reply_is_a_scenario_error(self):
        # A host answers each request once, so a streamed reply is not a fixture.
        for bad in ("yes", {"stream": [{"data": 1}]}, {"dta": 1}, []):
            with self.assertRaises(uitest.ScenarioError):
                uitest.normalise_replies({"a.b": bad})

    def test_shim_refuses_services_the_manifest_does_not_request(self):
        src = uitest.shim_source({})
        self.assertIn("fn uitest_granted(service)", src)
        self.assertIn('this app was not granted \\"" + family + "\\", which \\"" + service + "\\" needs', src)

    def test_shim_embeds_fixtures_as_one_string(self):
        src = uitest.shim_source({"x.y": {"data": {"say": 'he said "hi"\\n'}}})
        self.assertTrue(src.startswith(uitest.SHIM_BEGIN))
        self.assertIn("let host = {request: fn(service, args, callback){", src)
        literal = src.split("let uitest_fx = ", 1)[1].split(".parse_json()", 1)[0]
        # Undo the Splash escapes and the JSON must round-trip.
        text, i, body = [], 0, literal[1:-1]
        while i < len(body):
            if body[i] == "\\":
                text.append({"n": "\n", "r": "\r", "t": "\t"}.get(body[i + 1], body[i + 1]))
                i += 2
            else:
                text.append(body[i])
                i += 1
        text = "".join(text)
        self.assertEqual(json.loads(text)["services"][0]["service"], "x.y")

    def test_splash_string_escapes(self):
        self.assertEqual(uitest.splash_string('a"b\\c\nd'), '"a\\"b\\\\c\\nd"')

    def test_prepare_copy_leaves_the_original(self):
        with tempfile.TemporaryDirectory() as t:
            bundle = Path(t) / "bundle"
            bundle.mkdir()
            (bundle / "main.splash").write_text("let x = 1\n")
            (bundle / "manifest.json").write_text(json.dumps({"id": "a", "capabilities": ["model"],
                                                              "integrity": {"bundle_blake3": "", "signature": {"k": 1}}}))
            work = Path(t) / "work"
            work.mkdir()
            copy, lines = uitest.prepare_copy(bundle, work, {"host": {}})
            self.assertEqual((bundle / "main.splash").read_text(), "let x = 1\n")
            self.assertTrue((copy / "main.splash").read_text().endswith("let x = 1\n"))
            self.assertGreater(lines, 10)
            manifest = json.loads((copy / "manifest.json").read_text())
            self.assertIn("storage", manifest["capabilities"])
            self.assertNotIn("signature", manifest["integrity"])
            work2 = Path(t) / "w2"
            work2.mkdir()
            copy2, lines2 = uitest.prepare_copy(bundle, work2, {"fake_host": False})
            self.assertEqual(lines2, 0)
            self.assertEqual((copy2 / "main.splash").read_text(), "let x = 1\n")


class Checks(unittest.TestCase):
    view = [0, 0, 412, 892]

    def test_selectors(self):
        self.assertEqual(uitest.find(WIDGETS, "Keep")[1]["i"], "keep_button")
        self.assertEqual(uitest.find(WIDGETS, {"id": "entry"})[1]["ty"], "TextInput")
        self.assertEqual(uitest.find(WIDGETS, {"contains": "plumber"})[1]["i"], "entry")
        self.assertIsNone(uitest.find(WIDGETS, "Kee")[1])
        self.assertEqual(len(uitest.find(WIDGETS, {"type": "ButtonFlat"})[0]), 2)

    def test_after_picks_the_button_in_the_same_card(self):
        rows = [{"i": "", "ty": "Label", "r": [0, 0, 300, 20], "t": "Route A: noon"},
                {"i": "", "ty": "Button", "r": [0, 24, 80, 28], "t": "Use"},
                {"i": "", "ty": "Label", "r": [0, 60, 300, 20], "t": "Route B: evening"},
                {"i": "", "ty": "Button", "r": [0, 84, 80, 28], "t": "Use"}]
        _, w = uitest.find(rows, {"text": "Use", "after": {"contains": "Route B"}})
        self.assertEqual(w["r"][1], 84)
        self.assertIsNone(uitest.find(rows, {"text": "Use", "after": {"contains": "Route C"}})[1])

    def test_a_widget_cut_off_by_a_scroll_view_is_not_in_view(self):
        scroll = {"i": "app_scroll", "ty": "View", "r": [8, 50, 938, 390], "t": ""}
        cut = {"i": "cue_draft", "ty": "TextInput", "r": [67, 433, 869, 7], "t": "draft"}
        whole = {"i": "go", "ty": "Button", "r": [18, 342, 89, 28], "t": "Go"}
        widgets = [scroll, whole, cut]
        self.assertIs(uitest.clipped_by(widgets, cut), scroll)
        self.assertIsNone(uitest.clipped_by(widgets, whole))
        app = FakeApp(widgets)
        uitest.check_expectation(app, {"in_view": ["Go"]}, [0, 0, 954, 448])
        with self.assertRaises(uitest.StepFailed) as e:
            uitest.check_expectation(app, {"in_view": [{"id": "cue_draft"}]}, [0, 0, 954, 448])
        self.assertIn("cuts it off", e.exception.actual)

    def test_calls_excludes(self):
        app = FakeApp(WIDGETS, calls=[{"service": "model.complete", "args": {"text": "[[1, \"noon\"]]"}}])
        uitest.check_expectation(app, {"calls": [{"service": "model.complete", "excludes": "ann"}]}, self.view)
        with self.assertRaises(uitest.StepFailed):
            uitest.check_expectation(app, {"calls": [{"service": "model.complete", "excludes": "noon"}]}, self.view)

    def test_text_and_absent(self):
        app = FakeApp(WIDGETS)
        uitest.check_expectation(app, {"text": ["No notes yet.", "plumber"], "absent": ["Kept."]}, self.view)
        with self.assertRaises(uitest.StepFailed) as e:
            uitest.check_expectation(app, {"text": ["Kept."]}, self.view)
        self.assertIn("not on screen", e.exception.actual)

    def test_in_view_reports_the_overflow(self):
        app = FakeApp(WIDGETS)
        uitest.check_expectation(app, {"in_view": ["Keep"]}, self.view)
        with self.assertRaises(uitest.StepFailed) as e:
            uitest.check_expectation(app, {"in_view": ["Suggest a title"]}, self.view)
        self.assertIn("bottom by 48", e.exception.actual)

    def test_enabled_count_calls_files(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "notes.json"
            f.write_text('{"notes":["a"]}')
            app = FakeApp(WIDGETS, calls=[{"service": "model.complete", "args": {"input": {"note": "a"}}}],
                          files={"notes.json": f})
            uitest.check_expectation(app, {"enabled": ["Keep"], "disabled": ["Suggest a title"],
                                           "count": [{"of": {"type": "ButtonFlat"}, "n": 2}],
                                           "calls": [{"service": "model.complete", "count": 1, "contains": "note"}],
                                           "files": [{"name": "notes.json", "contains": ["notes"]},
                                                     {"name": "other.json", "missing": True}]}, self.view)
            for bad in ({"enabled": ["Suggest a title"]}, {"calls": [{"service": "mail.send"}]},
                        {"files": [{"name": "notes.json", "missing": True}]},
                        {"count": [{"of": {"type": "ButtonFlat"}, "n": 3}]}):
                with self.assertRaises(uitest.StepFailed):
                    uitest.check_expectation(app, bad, self.view)

    def test_feedback_has_the_template_parts(self):
        text = uitest.feedback({"scenario": "keep", "size": "412x892", "viewport": self.view,
                                "source_sha256": "abc", "file": "tests/02-keep.json",
                                "steps_run": [{"click": "Keep"}], "expected": 'text "Kept." is shown',
                                "actual": "not on screen", "detail": {"similar": []},
                                "evidence": {"snap": "snap.json", "log": "card-host.log"}}, "/app/bundle", "/bin/card-host")
        for part in ("Artifact:", "Runtime:", "Start state:", "Steps", "Expected:", "Actual:", "Evidence:", "Fix:", "Retest:"):
            self.assertIn(part, text)


class Scenarios(unittest.TestCase):
    def test_examples_are_valid(self):
        root = Path(__file__).resolve().parent.parent / "examples"
        files = sorted(root.glob("*/tests/*.json"))
        self.assertTrue(files)
        for f in files:
            for _, sc in uitest.load_scenarios(f):
                uitest.normalise_replies(sc.get("host"))
                for step in sc["steps"]:
                    self.assertTrue(set(step) & {"click", "type", "key", "scroll", "sleep", "expect", "wait"}, f)

    def test_broken_scenario_is_reported(self):
        for body in ('{"name": "no steps"}', '{"steps": [{"clik": "Keep"}]}', '{"steps": [{"run": "_missing.json"}]}'):
            with tempfile.TemporaryDirectory() as t:
                (Path(t) / "x.json").write_text(body)
                with self.assertRaises(uitest.ScenarioError):
                    uitest.load_scenarios(t)

    def test_parts_share_fixtures_and_steps(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d / "_room.json").write_text(json.dumps({
                "sizes": ["412x892", "954x448"],
                "host": {"a.read": {"data": {"rows": [1]}}, "a.info": {"data": {"id": "r"}}},
                "storage": {"s.json": "{}"},
                "steps": [{"click": "Load"}, {"wait": {"text": ["1 row"]}}]}))
            (d / "02-x.json").write_text(json.dumps({
                "use": "_room.json",
                "host": {"a.read": {"error": "expired"}},
                "steps": [{"run": "_room.json"}, {"expect": {"text": ["expired"]}, "note": "why"}]}))
            (d / "01-plain.json").write_text('{"steps": [{"sleep": 0}]}')
            scenarios = uitest.load_scenarios(d)
            self.assertEqual([f.name for f, _ in scenarios], ["01-plain.json", "02-x.json"])
            sc = scenarios[1][1]
            self.assertEqual(sc["sizes"], ["412x892", "954x448"])
            self.assertEqual(sc["host"]["a.read"], {"error": "expired"})   # the scenario wins
            self.assertEqual(sc["host"]["a.info"], {"data": {"id": "r"}})  # the part fills in
            self.assertEqual(sc["storage"], {"s.json": "{}"})
            self.assertEqual([list(s)[0] for s in sc["steps"]], ["click", "wait", "expect"])


class Scrolling(unittest.TestCase):
    class Scroller:
        """A column of widgets under a 400-point viewport; /m scroll moves them by dy * 0.5."""

        def __init__(self, target_y):
            self.offset, self.target_y, self.scrolls = 0.0, target_y, 0

        def snap(self):
            return [{"i": "top", "ty": "Label", "r": [0, 10 - self.offset, 100, 20], "t": "Top"},
                    {"i": "go", "ty": "ButtonFlat", "r": [0, self.target_y - self.offset, 80, 28], "t": "Send"}]

        def get(self, route, **params):
            assert route == "/m" and params["k"] == "scroll"
            self.scrolls += 1
            self.offset = max(0.0, self.offset + float(params["dy"]) * 0.5)

    def test_scrolls_until_in_view_whatever_the_scroll_unit(self):
        s = self.Scroller(target_y=1300)
        uitest.scroll_into_view(s, "Send", None, [0, 0, 400, 400], 10)
        y = s.target_y - s.offset
        self.assertTrue(0 <= y and y + 28 <= 400, y)
        self.assertLessEqual(s.scrolls, 4)

    def test_reports_when_scrolling_stops(self):
        s = self.Scroller(target_y=1300)
        s.get = lambda route, **p: None   # nothing moves
        with self.assertRaises(uitest.StepFailed) as e:
            uitest.scroll_into_view(s, "Send", None, [0, 0, 400, 400], 10)
        self.assertIn("no longer moves", e.exception.actual)


if __name__ == "__main__":
    unittest.main()
