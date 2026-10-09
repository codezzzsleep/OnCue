#!/usr/bin/env python3
"""Pure packaging/checker self-tests. These DO NOT test OnCue runtime behavior.

No file writes, card-host, display, model, or production-algorithm mirror.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import re
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
        cls.harness = generate_probe.load_harness()

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
                self.assertIn("start_timeout(1.4", after["cue_play_pulse"]["source"])
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

    def test_all_new_assertion_ids_have_one_oracle(self):
        # IDs are reviewed fixture literals, not generated from the harness at run time.
        self.assertEqual(set(self.fixtures["assertion_ids"]), set(generate_probe.SUITES))
        literal = re.findall(r'probe_assert\("((?:parser|pagination|retry|deadline|playback|storage|grounding|envelope|send)\.[^"\n]+)"', self.harness)
        literal = [name for name in literal if name not in ("storage.legacy_explicit_copy_", "envelope.auth_room_", "envelope.auth_model_")]
        self.assertEqual(len(literal), len(set(literal)))
        dynamic = {
            "parser": {"parser." + case["id"] for case in self.fixtures["parser"] + self.fixtures["refinement"]},
            "pagination": {"pagination." + case["id"] for case in self.fixtures["pagination"]},
            "grounding": {"grounding." + case["id"] for group in ("excerpts", "tokens", "numbers", "references")
                          for case in self.fixtures["grounding"][group]},
            "envelope": {"envelope.auth_" + mode + "_" + str(i) for mode in ("room", "model") for i in range(6)},
            "storage": {"storage." + case["id"] for case in self.fixtures["storage"]["invalid_cases"]}
                       | {"storage.legacy_explicit_copy_" + name for name in ("draft", "a", "b")},
        }
        # "send"/"send2"/"send3" share the send.* ID namespace but run as three
        # suites to keep each real card-host process inside the 32 MiB heap quota;
        # partition them by the reviewed fixture lists, not by ID prefix.
        send_suites = ("send", "send2", "send3", "send4")
        send_union = set().union(*(set(self.fixtures["assertion_ids"][s]) for s in send_suites))
        for s in send_suites:
            others = set().union(*(set(self.fixtures["assertion_ids"][o]) for o in send_suites if o != s))
            self.assertEqual(set(self.fixtures["assertion_ids"][s]) & others, set())
        for suite in generate_probe.SUITES:
            if suite in send_suites:
                defined = set(self.fixtures["assertion_ids"][suite])
                for name in defined:
                    self.assertIn(name, literal, f"{name} missing a probe_assert oracle")
            else:
                defined = {name for name in literal if name.startswith(suite + ".")}
                defined |= dynamic.get(suite, set())
                self.assertEqual(defined, set(self.fixtures["assertion_ids"][suite]), suite)
            self.assertIn(f'if probe_meta.suite == "{suite}" {{ probe_{suite}() return }}', self.harness)
        self.assertEqual({n for n in literal if n.startswith("send.")}, send_union)

    def test_production_api_drift_and_shadowing_refused(self):
        for name in ("cue_source_excerpt", "cue_keep_take", "cue_play_pulse"):
            with self.subTest(function=name), self.assertRaises(ValueError):
                generate_probe.build_probe(self.source.replace("fn " + name + "(", "fn renamed_" + name + "("),
                                           self.fixture_bytes, self.harness, "storage")
        for name in ("fs", "start_timeout", "time_now", "ui"):
            with self.subTest(shadow=name), self.assertRaises(ValueError):
                generate_probe.build_probe(self.source, self.fixture_bytes,
                                           self.harness + "\nlet " + name + " = {}\n", "storage")
        with self.assertRaises(ValueError):
            generate_probe.build_probe(self.source, self.fixture_bytes, self.harness, "unknown")

    def test_storage_literal_byte_checker(self):
        _, provenance = generate_probe.build_probe(self.source, self.fixture_bytes, self.harness, "storage")
        # Synthetic bytes exist ONLY in memory; this is not a successful jail run.
        slots = copy.deepcopy(provenance["storage_expectation"]["slots"])
        for index, slot in enumerate(slots):
            slot[1] = index + 10
        value = [1, 3, [["probe-room", *slots]]]
        encode = lambda data: json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        files = {generate_probe.STORAGE_FILE: encode(value)}
        self.assertEqual(check_result.validate_storage_bytes(files, provenance), [])
        for data in (files[generate_probe.STORAGE_FILE] + b"x", files[generate_probe.STORAGE_FILE][:-1],
                     b" " + files[generate_probe.STORAGE_FILE], b"{}", b"null", b"[1,3,[]]"):
            self.assertTrue(check_result.validate_storage_bytes({generate_probe.STORAGE_FILE: data}, provenance))
        for index in range(3):
            for field in (0, 2, 3, 4, 5, 6, 7, 8):
                changed = copy.deepcopy(value)
                changed[2][0][index + 1][field] = "wrong"
                self.assertTrue(check_result.validate_storage_bytes({generate_probe.STORAGE_FILE: encode(changed)}, provenance))
        for name in generate_probe.LEGACY_FILES:
            self.assertTrue(check_result.validate_storage_bytes({**files, name: b"legacy"}, provenance))
        self.assertTrue(check_result.validate_storage_bytes({}, provenance))
        self.assertTrue(check_result.validate_storage_bytes(files, {}))

    def test_storage_final_revision_and_identity_checked(self):
        _, provenance = generate_probe.build_probe(self.source, self.fixture_bytes, self.harness, "storage")
        slots = copy.deepcopy(provenance["storage_expectation"]["slots"])
        for index, slot in enumerate(slots):
            slot[1] = index + 1
        valid = [1, 3, [["probe-room", *slots]]]
        mutations = []
        for revision in (True, -1, 2, "3", 3.5):
            changed = copy.deepcopy(valid)
            changed[1] = revision
            mutations.append(changed)
        changed = copy.deepcopy(valid)
        changed[2][0][0] = "wrong-room"
        mutations.append(changed)
        changed = copy.deepcopy(valid)
        changed[2].append(changed[2][0])
        mutations.append(changed)
        changed = copy.deepcopy(valid)
        changed[2][0][3][1] = 1
        mutations.append(changed)
        for changed in mutations:
            data = json.dumps(changed, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self.assertTrue(check_result.validate_storage_bytes({generate_probe.STORAGE_FILE: data}, provenance))

    def test_envelope_failure_is_not_xfail(self):
        _, provenance = generate_probe.build_probe(self.source, self.fixture_bytes, self.harness, "envelope")
        sample = {"schema": 1, "complete": True, "meta": copy.deepcopy(provenance),
                  "passed": True, "unexpected_host_requests": 0,
                  "started_at": 1000, "observed_at": 1001,
                  "assertions": [{"id": name, "passed": True, "detail": {"synthetic_checker_unit_input": True}}
                                 for name in provenance["expected_assertion_ids"]]}
        self.assertEqual(check_result.validate_result(sample, provenance), [])
        for entry in sample["assertions"]:
            if entry["id"] == "envelope.nil_data_handled_without_runtime_error":
                entry["passed"] = False
                entry["detail"] = {"threw": True, "synthetic_checker_unit_input": True}
        errors = check_result.validate_result(sample, provenance)
        self.assertTrue(any("FAIL envelope.nil_data_handled_without_runtime_error" in error for error in errors))

    def test_new_metadata_and_playback_window_checked(self):
        _, provenance = generate_probe.build_probe(self.source, self.fixture_bytes, self.harness, "playback")
        sample = {"schema": 1, "complete": True, "meta": copy.deepcopy(provenance),
                  "passed": True, "unexpected_host_requests": 0,
                  "started_at": 1000, "observed_at": 1007,
                  "assertions": [{"id": name, "passed": True, "detail": {"synthetic_checker_unit_input": True}}
                                 for name in provenance["expected_assertion_ids"]]}
        self.assertEqual(check_result.validate_result(sample, provenance), [])
        for key in ("real_playback_interval_seconds", "filesystem", "semantic_fact_verification", "storage_expectation"):
            changed = copy.deepcopy(sample)
            changed["meta"][key] = "incorrect"
            self.assertTrue(check_result.validate_result(changed, provenance))
        sample["observed_at"] = 1001
        self.assertTrue(check_result.validate_result(sample, provenance))

    def test_core_eight_suites_preserved_with_send_quadruplet(self):
        self.assertEqual(generate_probe.CORE_SUITES,
                         ("parser", "pagination", "retry", "deadline", "playback", "storage", "grounding", "envelope"))
        self.assertEqual(generate_probe.SUITES, (*generate_probe.CORE_SUITES, "send", "send2", "send3", "send4"))
        self.assertEqual(sum(len(self.fixtures["assertion_ids"][suite])
                             for suite in generate_probe.CORE_SUITES), 293)
        self.assertEqual(len(self.fixtures["assertion_ids"]["send"]), 44)
        self.assertEqual(len(self.fixtures["assertion_ids"]["send2"]), 21)
        self.assertEqual(len(self.fixtures["assertion_ids"]["send3"]), 7)
        self.assertEqual(len(self.fixtures["assertion_ids"]["send4"]), 3)

    def test_send_timeout_and_injection_metadata_checked(self):
        # The real 30s transport-timeout oracle lives in suite "send3"; "send"
        # and "send2" are the preparation/confirmation/freshness halves with no
        # long timer window.
        _, provenance = generate_probe.build_probe(self.source, self.fixture_bytes, self.harness, "send4")
        sample = {"schema": 1, "complete": True, "meta": copy.deepcopy(provenance),
                  "passed": True, "unexpected_host_requests": 0,
                  "started_at": 1000, "observed_at": 1031,
                  "assertions": [{"id": name, "passed": True, "detail": {"synthetic_checker_unit_input": True}}
                                 for name in provenance["expected_assertion_ids"]]}
        self.assertEqual(check_result.validate_result(sample, provenance), [])
        for key in ("real_send_timeout_seconds", "send_transport", "send_identity"):
            changed = copy.deepcopy(sample)
            changed["meta"][key] = "incorrect"
            self.assertTrue(check_result.validate_result(changed, provenance))
        sample["observed_at"] = 1029
        self.assertTrue(check_result.validate_result(sample, provenance))

    def test_send_host_allowlist_fail_hard_no_forwarding(self):
        self.assertIn('service != "matrix.account_info"', self.harness)
        self.assertIn('service != "matrix.send_message"', self.harness)
        self.assertIn("nil.probe_unexpected_service()", self.harness)
        self.assertIn("probe_checkpoint(false)", self.harness)

    def test_no_native_host_forwarding(self):
        self.assertNotIn("mod.host", self.harness)
        self.assertNotIn("native_host", self.harness)
        self.assertNotIn("start_timeout =", self.harness)
        self.assertNotIn("fn cue_", self.harness)


if __name__ == "__main__":
    unittest.main(verbosity=2)
