#!/usr/bin/env python3
"""Collect/check a real card-host jail result; never execute app logic in Python."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_result(result: dict, provenance: dict) -> list[str]:
    errors = []
    if result.get("schema") != 1 or result.get("complete") is not True:
        errors.append("Result is not a completed schema-1 probe")
    meta = result.get("meta", {})
    for key in ("suite", "source_sha256", "fixtures_sha256", "harness_sha256",
                "expected_assertion_ids", "controlled_injection", "natural_model_test",
                "production_functions_unchanged", "real_deadline_seconds",
                "real_playback_interval_seconds", "filesystem",
                "semantic_fact_verification", "storage_file_sha256"):
        if meta.get(key) != provenance.get(key):
            errors.append(f"Provenance mismatch: {key}")
    if meta.get("controlled_injection") is not True or meta.get("natural_model_test") is not False:
        errors.append("Result does not disclose controlled injection")
    assertions = result.get("assertions", [])
    if not isinstance(assertions, list):
        return errors + ["Assertions must be an array"]
    expected = provenance.get("expected_assertion_ids", [])
    actual = [item.get("id") for item in assertions if isinstance(item, dict)]
    if len(actual) != len(assertions):
        errors.append("Malformed assertion entry")
    if Counter(actual) != Counter(expected):
        errors.append(f"Assertion inventory differs; missing={list((Counter(expected) - Counter(actual)).elements())}, "
                      f"extra={list((Counter(actual) - Counter(expected)).elements())}")
    for item in assertions:
        if isinstance(item, dict) and item.get("passed") is not True:
            errors.append(f"FAIL {item.get('id')}: {json.dumps(item.get('detail'), ensure_ascii=False)}")
    if result.get("passed") is not True:
        errors.append("Probe reported passed != true")
    if result.get("unexpected_host_requests") != 0:
        errors.append("Unexpected service requested; no requests were forwarded to a native host")
    started = result.get("started_at")
    observed = result.get("observed_at")
    if not isinstance(started, (int, float)) or not isinstance(observed, (int, float)) or observed < started:
        errors.append("Invalid runtime timestamps")
    elif meta.get("suite") == "deadline" and observed - started < 92.5:
        errors.append("Deadline probe did not run for the full real-time observation window")
    elif meta.get("suite") == "playback" and observed - started < 6.5:
        errors.append("Playback probe did not run for the real-timer observation window")
    return errors


def validate_storage_bytes(files: dict[str, bytes], provenance: dict) -> list[str]:
    """Compare literal fixture hashes, not a Python copy of production storage logic."""
    expected = provenance.get("storage_file_sha256", {})
    if set(expected) != {"draft.txt", "take-a.txt", "take-b.txt"}:
        return ["Storage provenance must identify all three real jail files"]
    errors = []
    for name, expected_hash in expected.items():
        if name not in files:
            errors.append(f"Missing real jail file: {name}")
        elif sha256(files[name]) != expected_hash:
            errors.append(f"Real jail bytes differ from literal fixture: {name}")
    return errors


def collect(run_dir: Path, wait_seconds: float, current_source: Path | None) -> int:
    run_dir = run_dir.resolve(strict=True)
    provenance = json.loads((run_dir / "provenance.json").read_text(encoding="utf-8"))
    if sha256((run_dir / "bundle" / "main.splash").read_bytes()) != provenance["generated_sha256_before_stamp"]:
        raise ValueError("Generated probe source changed after generation; regenerate instead of editing it")
    if sha256((run_dir / "production-main.splash").read_bytes()) != provenance["source_sha256"]:
        raise ValueError("Production source snapshot/provenance mismatch")
    if current_source is not None and sha256(current_source.read_bytes()) != provenance["source_sha256"]:
        raise ValueError("Current production source differs from this run; regenerate to test current bytes")
    result_path = (run_dir / provenance["result_relative_to_run"]).resolve()
    if run_dir not in result_path.parents:
        raise ValueError("Result path escapes the run directory")
    begun = time.monotonic()
    last_error = "result file has not appeared"
    result = None
    while True:
        if result_path.is_file():
            try:
                candidate = json.loads(result_path.read_text(encoding="utf-8"))
                if isinstance(candidate, dict) and candidate.get("complete") is True:
                    result = candidate
                    break
                last_error = "probe is incomplete; check checkpoint and card-host log"
            except (OSError, json.JSONDecodeError) as error:
                # fs.write may be observed between truncation and completion.
                last_error = str(error)
        if time.monotonic() - begun >= wait_seconds:
            break
        time.sleep(0.2)
    elapsed = time.monotonic() - begun
    if result is None:
        print(f"INCOMPLETE: {last_error}; collector waited {elapsed:.3f}s", file=sys.stderr)
        print(f"Inspect {result_path} and {run_dir / 'app-data' / 'card-host.log'}", file=sys.stderr)
        return 2
    errors = validate_result(result, provenance)
    if provenance["suite"] == "storage":
        # Inspect actual host-created files independently of the Splash assertions.
        files = {}
        for name in ("draft.txt", "take-a.txt", "take-b.txt"):
            path = result_path.parent / name
            if path.is_symlink() or path.resolve().parent != result_path.parent:
                errors.append(f"Storage path is not a direct real jail file: {name}")
            elif path.is_file():
                files[name] = path.read_bytes()
        errors.extend(validate_storage_bytes(files, provenance))
        for name, data in files.items():
            print(f"Real jail bytes: {name} | {len(data)} bytes | SHA256 {sha256(data)}")
    print(f"Suite: {provenance['suite']} | controlled injection, NOT natural model evidence")
    print(f"Production SHA256: {provenance['source_sha256']}")
    print(f"Runtime interval: {result['observed_at'] - result['started_at']:.3f}s | collector monotonic wait: {elapsed:.3f}s")
    for assertion in result.get("assertions", []):
        print(f"{'PASS' if assertion.get('passed') is True else 'FAIL'} {assertion.get('id')}")
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print(f"PASS: {len(result['assertions'])} assertions; source/provenance/assertion inventory verified")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--wait-seconds", type=float, default=0,
                        help="Collector wait only, never changes the app's production 90-second deadline")
    parser.add_argument("--current-source", type=Path,
                        help="Also reject results generated from stale production bytes")
    args = parser.parse_args()
    if args.wait_seconds < 0:
        parser.error("--wait-seconds must be nonnegative")
    try:
        return collect(args.run_dir, args.wait_seconds, args.current_source)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Result check failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
