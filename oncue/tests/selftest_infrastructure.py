#!/usr/bin/env python3
"""Pure packaging/checker self-tests. These DO NOT test OnCue runtime behavior.

No file writes, card-host, display, model, or production-algorithm mirror.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

# Keep this command entirely read-only, including imported Python modules.
sys.dont_write_bytecode = True
import generate_probe
import check_result

HERE = Path(__file__).resolve().parent


class InfrastructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = generate_probe.DEFAULT_SOURCE.read_bytes().decode("utf-8")
        cls.fixture_bytes = (HERE / "fixtures.json").read_bytes()
        cls.fixtures = json.loads(cls.fixture_bytes)
        cls.harness = (HERE / "probe_harness.splash").read_text(encoding="utf-8")

    def test_exact_production_functions_for_every_suite(self):
        before = generate_probe.extract_functions(self.source)
        for suite in generate_probe.SUITES:
            with self.subTest(suite=suite):
                generated, provenance = generate_probe.build_probe(
                    self.source, self.fixture_bytes, self.harness, suite)
                after = generate_probe.extract_functions(generated)
                self.assertEqual(set(before), set(after))
                for name in before:
                    self.assertEqual(before[name]["source"], after[name]["source"])
                self.assertIn("start_timeout(90.0", after["cue_deadline"]["source"])
                self.assertEqual(provenance["source_sha256"], generate_probe.digest(self.source.encode("utf-8")))
                self.assertFalse(provenance["natural_model_test"])
                self.assertEqual(generated.count("let host = {request:"), 1)
                self.assertEqual(generated.count("start_timeout(0.20, fn(){ probe_boot() })"), 1)
                self.assertEqual(len(generate_probe.INITIALIZER.findall(generated)), 0)

    def test_extractor_ignores_braces_in_strings_and_comments(self):
        altered = self.source.replace(
            "fn cue_split_blocks(text){",
            'fn cue_split_blocks(text){\n// } { comment\n/* { nested /* } */ } */\nlet ignored = "} \\\" {"',
            1)
        extracted = generate_probe.extract_functions(altered)
        self.assertIn('let ignored = "} \\\" {"', extracted["cue_split_blocks"]["source"])
        self.assertEqual(extracted["cue_split_blocks"]["source"][-1], "}")

    def test_missing_or_duplicate_initializer_refused(self):
        for source in (
            generate_probe.INITIALIZER.sub("", self.source),
            self.source + "\nstart_timeout(0.05, fn(){ cue_show_demo() cue_refresh_takes() })\n",
        ):
            with self.assertRaises(ValueError):
                generate_probe.build_probe(source, self.fixture_bytes, self.harness, "parser")

    def test_fixture_ids_are_unique_and_complete(self):
        for suite, ids in self.fixtures["assertion_ids"].items():
            self.assertEqual(len(ids), len(set(ids)), suite)
        for suite in ("parser", "pagination"):
            declared = set(self.fixtures["assertion_ids"][suite])
            for fixture in self.fixtures[suite]:
                self.assertIn(suite + "." + fixture["id"], declared)
        for fixture in self.fixtures["parser"]:
            if fixture["valid"]:
                self.assertEqual(len(fixture["blocks"]), 7)
                self.assertTrue(all(isinstance(block, str) and block.strip() for block in fixture["blocks"]))
        for fixture in self.fixtures["pagination"]:
            for cluster in fixture["clusters"]:
                self.assertEqual(fixture["text"].count(cluster), 1, "Cluster containment oracle requires unique fixtures")

    def test_checker_rejects_incomplete_stale_missing_failed_and_duplicate(self):
        _, provenance = generate_probe.build_probe(self.source, self.fixture_bytes, self.harness, "parser")
        # Synthetic checker unit input ONLY; never emitted as runtime evidence.
        sample = {"schema": 1, "complete": True, "meta": copy.deepcopy(provenance),
                  "passed": True, "unexpected_host_requests": 0,
                  "started_at": 1000, "observed_at": 1001,
                  "assertions": [{"id": name, "passed": True, "detail": {"synthetic_checker_unit_input": True}}
                                 for name in provenance["expected_assertion_ids"]]}
        self.assertEqual(check_result.validate_result(sample, provenance), [])
        changes = []
        changed = copy.deepcopy(sample)
        changed["complete"] = False
        changes.append(changed)
        changed = copy.deepcopy(sample)
        changed["meta"]["source_sha256"] = "stale"
        changes.append(changed)
        changed = copy.deepcopy(sample)
        changed["assertions"].pop()
        changes.append(changed)
        changed = copy.deepcopy(sample)
        changed["assertions"][0]["passed"] = False
        changes.append(changed)
        changed = copy.deepcopy(sample)
        changed["assertions"].append(changed["assertions"][0])
        changes.append(changed)
        for changed in changes:
            self.assertTrue(check_result.validate_result(changed, provenance))

    def test_no_native_host_forwarding(self):
        self.assertNotIn("mod.host", self.harness)
        self.assertNotIn("native_host", self.harness)
        self.assertNotIn("start_timeout =", self.harness)
        self.assertNotIn("fn cue_", self.harness)


if __name__ == "__main__":
    unittest.main(verbosity=2)
