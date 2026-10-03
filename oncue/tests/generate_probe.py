#!/usr/bin/env python3
"""Generate, never execute, a full-page OctoScript production-code probe.

Python only packages source and literal fixtures. It does not implement OnCue's
parser, pagination, retry/deadline, playback, storage, or grounding logic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE = HERE.parent / "bundle" / "main.splash"
SUITES = ("parser", "pagination", "retry", "deadline", "playback", "storage", "grounding", "envelope")
REQUIRED_FUNCTIONS = {
    "cue_split_blocks", "cue_validate_blocks", "cue_paginate",
    "cue_rehearse", "cue_start_turn", "cue_accept_reply", "cue_deadline",
    "cue_invalidate", "cue_stop_wait", "cue_edit_trial", "cue_prompt",
    "cue_select_preview", "cue_ws_text", "cue_choose_route",
    "cue_source_excerpt", "cue_numeric_tokens", "cue_numbers_grounded",
    "cue_references_valid", "cue_validate_protocol", "cue_protocol_markers",
    "cue_toggle_playback", "cue_pause_playback", "cue_play_pulse",
    "cue_advance_playback", "cue_next_line", "cue_restart_playback",
    "cue_keep_draft", "cue_restore_draft", "cue_save_text", "cue_keep_take",
    "cue_refresh_takes", "cue_read_take", "cue_restore_take",
}
STORAGE_FIXTURES = {"draft.txt": "draft", "take-a.txt": "take_a", "take-b.txt": "take_b"}
INITIALIZER = re.compile(
    r"(?m)^start_timeout\(0\.05,\s*fn\(\)\{\s*"
    r"cue_show_demo\(\)\s+cue_refresh_takes\(\)\s*\}\)\s*$"
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def lexical_mask(source: str) -> str:
    """Keep positions/braces, hiding strings/comments (not a Splash parser)."""
    out = list(source)
    pos = 0
    state = "code"
    depth = 0
    while pos < len(source):
        char = source[pos]
        pair = source[pos:pos + 2]
        if state == "string":
            if char == "\\":
                out[pos] = " "
                pos += 1
                if pos < len(source):
                    out[pos] = " " if source[pos] != "\n" else "\n"
            else:
                if char == '"':
                    state = "code"
                out[pos] = " " if char != "\n" else "\n"
        elif state == "line":
            if char == "\n":
                state = "code"
            else:
                out[pos] = " "
        elif state == "block":
            out[pos] = " " if char != "\n" else "\n"
            if pair == "/*":
                depth += 1
                out[pos + 1] = " "
                pos += 1
            elif pair == "*/":
                depth -= 1
                out[pos + 1] = " "
                pos += 1
                if depth == 0:
                    state = "code"
        elif char == '"':
            state = "string"
            out[pos] = " "
        elif pair in ("//", "/*"):
            state = "line" if pair == "//" else "block"
            depth = 1
            out[pos:pos + 2] = [" ", " "]
            pos += 1
        pos += 1
    if state in ("string", "block"):
        raise ValueError("Unclosed string/comment: refusing an incomplete source snapshot")
    return "".join(out)


def extract_functions(source: str) -> dict[str, dict]:
    """Extract exact named production-function bytes, including their braces."""
    mask = lexical_mask(source)
    functions = {}
    for match in re.finditer(r"(?m)^fn\s+(cue_\w+)\s*\(", mask):
        name = match.group(1)
        if name in functions:
            raise ValueError(f"Duplicate production function {name}")
        opening = mask.find("{", match.end())
        if opening < 0:
            raise ValueError(f"Missing function body: {name}")
        depth = 1
        end = opening + 1
        while depth and end < len(mask):
            if mask[end] == "{":
                depth += 1
            elif mask[end] == "}":
                depth -= 1
            end += 1
        if depth:
            raise ValueError(f"Unclosed production function: {name}")
        exact = source[match.start():end]
        functions[name] = {
            "source": exact,
            "start_line": source.count("\n", 0, match.start()) + 1,
            "end_line": source.count("\n", 0, end) + 1,
            "sha256": digest(exact.encode("utf-8")),
        }
    missing = REQUIRED_FUNCTIONS - functions.keys()
    if missing:
        raise ValueError(f"Production API changed; adapt probe explicitly: {sorted(missing)}")
    return functions


def splash_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def build_probe(source: str, fixture_bytes: bytes, harness: str, suite: str) -> tuple[str, dict]:
    fixtures = json.loads(fixture_bytes)
    if fixtures.get("schema") != 1:
        raise ValueError("Unsupported fixtures schema")
    if suite not in SUITES:
        raise ValueError(f"Unknown probe suite: {suite}")
    functions = extract_functions(source)
    harness_mask = lexical_mask(harness)
    if re.search(r"\b(?:let|fn)\s+(?:fs|start_timeout|time_now|ui)\b", harness_mask):
        raise ValueError("Harness must not shadow real filesystem, timer, clock, or UI APIs")
    called = set(re.findall(r"\b(cue_\w+)\s*\(", harness_mask))
    if called - functions.keys():
        raise ValueError(f"Production API changed; missing harness calls: {sorted(called - functions.keys())}")
    starts = list(INITIALIZER.finditer(source))
    if len(starts) != 1:
        raise ValueError("Expected exactly one known demo initializer; review startup changes before adapting")
    if "probe_" in lexical_mask(source):
        raise ValueError("Production source contains probe_ names; refusing an already instrumented source")
    startup = starts[0]
    expected_ids = fixtures["assertion_ids"][suite]
    metadata = {
        "schema": 1,
        "suite": suite,
        "source_sha256": digest(source.encode("utf-8")),
        "fixtures_sha256": digest(fixture_bytes),
        "harness_sha256": digest(harness.encode("utf-8")),
        "expected_assertion_ids": expected_ids,
        "controlled_injection": True,
        "natural_model_test": False,
        "production_functions_unchanged": True,
        "real_deadline_seconds": 90,
        "real_playback_interval_seconds": 1.4,
        "filesystem": "real card-host jail; fs is not shadowed",
        "semantic_fact_verification": False,
        "storage_file_sha256": {
            name: digest(fixtures["storage"][key].encode("utf-8"))
            for name, key in STORAGE_FIXTURES.items()
        } if suite == "storage" else {},
    }
    header = (
        "// TEST-ONLY controlled host. No native host service is forwarded.\n"
        "let probe_meta = " + splash_string(json.dumps(metadata, ensure_ascii=False)) + ".parse_json()\n"
        "let probe_fixtures = " + splash_string(fixture_bytes.decode("utf-8")) + ".parse_json()\n"
    )
    instrumented = (
        source[:startup.start()]
        + "// Production demo/storage initialization disabled ONLY in this generated probe.\n"
        + "start_timeout(0.20, fn(){ probe_boot() })\n"
        + source[startup.end():]
    )
    # Object closures resolve lexical variables at creation: install the fake
    # host AFTER production state declarations, before any production function.
    # Function bodies remain byte-identical; no production state is shadowed.
    insertion = instrumented.index("\nfn cue_") + 1
    generated = (instrumented[:insertion] + header + harness
                 + "\n// ---- EXACT PRODUCTION FUNCTIONS/PAGE ----\n"
                 + instrumented[insertion:])
    extracted_again = extract_functions(generated)
    if set(functions) != set(extracted_again):
        raise ValueError("Generated production function inventory differs")
    for name, item in functions.items():
        if item["source"] != extracted_again[name]["source"]:
            raise ValueError(f"Probe changed production function: {name}")
    inventory = {
        **metadata,
        "generated_sha256_before_stamp": digest(generated.encode("utf-8")),
        "initializer_original": startup.group(),
        "initializer_source_line": source.count("\n", 0, startup.start()) + 1,
        "functions": {name: {key: value for key, value in item.items() if key != "source"}
                      for name, item in functions.items()},
    }
    return generated, inventory


def generate(source_path: Path, workdir: Path, suite: str) -> Path:
    source_path = source_path.resolve(strict=True)
    workdir = workdir.resolve()
    repository = HERE.parent.parent.resolve()
    # Output is intentionally a disposable directory, never the production tree.
    if workdir == Path("/") or workdir == repository or repository in workdir.parents:
        raise ValueError("--workdir must be a temporary directory OUTSIDE the OnCue repository")
    if workdir == source_path.parent or source_path.parent in workdir.parents:
        raise ValueError("Refusing to generate inside the source bundle")
    if not workdir.is_dir():
        raise ValueError("Create --workdir first (e.g. mktemp -d); generator never deletes/replaces a run")
    output = workdir / suite
    if output.exists():
        raise ValueError(f"Run directory already exists; use a fresh workdir: {output}")
    original = source_path.read_bytes()
    source = original.decode("utf-8")
    fixture_bytes = (HERE / "fixtures.json").read_bytes()
    harness = (HERE / "probe_harness.splash").read_text(encoding="utf-8")
    generated, inventory = build_probe(source, fixture_bytes, harness, suite)
    manifest = json.loads((source_path.parent / "manifest.json").read_text(encoding="utf-8"))
    app_id = "oncue-probe-" + suite
    manifest["id"] = app_id
    manifest["name"] = "OnCue controlled " + suite + " probe"
    manifest["agent"] = None
    manifest["capabilities"] = ["storage"]
    manifest["network"] = {"hosts": []}
    manifest["integrity"] = {"bundle_blake3": "0" * 64}
    listing_path = source_path.parent / "listing.json"
    listing_bytes = listing_path.read_bytes()
    listing = json.loads(listing_bytes)
    assets = []
    for relative in [listing.get("icon", ""), *listing.get("screenshots", [])]:
        if not isinstance(relative, str) or not relative:
            raise ValueError("Expected literal icon/screenshot asset paths")
        asset = source_path.parent / relative
        if asset.is_symlink() or not asset.is_file() or source_path.parent not in asset.resolve().parents:
            raise ValueError(f"Unsafe/missing source asset: {relative}")
        assets.append((relative, asset.read_bytes()))
    # Detect concurrent source editing before publishing the snapshot.
    if source_path.read_bytes() != original:
        raise ValueError("Production source changed during generation; rerun after the edit finishes")
    bundle = output / "bundle"
    bundle.mkdir(parents=True)
    (bundle / "main.splash").write_bytes(generated.encode("utf-8"))
    (bundle / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (bundle / "listing.json").write_bytes(listing_bytes)
    for relative, data in assets:
        target = bundle / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    inventory["source_path"] = str(source_path)
    inventory["app_id"] = app_id
    inventory["result_relative_to_run"] = f"app-data/{app_id}/probe-result.json"
    inventory["asset_note"] = "Existing production artwork/screenshots copied only for bundle admission, not probe evidence"
    (output / "provenance.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "production-main.splash").write_bytes(original)
    exact = extract_functions(source)
    (output / "production-functions.splash").write_text(
        "\n\n".join(item["source"] for item in exact.values()) + "\n", encoding="utf-8")
    print(f"Generated {suite}: {bundle}")
    print(f"Production SHA256: {inventory['source_sha256']}")
    print(f"Exact production functions: {len(exact)}; no runtime started")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--workdir", type=Path, required=True, help="Existing temporary directory outside OnCue")
    parser.add_argument("--suite", choices=SUITES, required=True)
    args = parser.parse_args()
    try:
        generate(args.source, args.workdir, args.suite)
    except (OSError, ValueError, KeyError) as error:
        print(f"Generation refused: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
