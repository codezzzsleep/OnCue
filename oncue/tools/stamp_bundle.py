"""Check a bundle digest or refresh an unsigned development bundle."""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

from blake3 import blake3


def digest_bundle(root: Path) -> str:
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("A bundle may not contain symlinks")
        if path.is_file() and path.relative_to(root) != Path("manifest.json"):
            files.append(path.relative_to(root))
    hasher = blake3()
    for relative in sorted(files):
        data = (root / relative).read_bytes()
        hasher.update(str(relative).encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(struct.pack("<Q", len(data)))
        hasher.update(data)
    return hasher.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument(
        "--check", action="store_true",
        help="Check the recorded digest without modifying any file; not signature verification.",
    )
    args = parser.parse_args()
    root = args.bundle.resolve(strict=True)
    if not root.is_dir():
        parser.error("bundle must be a directory")
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if args.check:
        recorded = manifest.get("integrity", {}).get("bundle_blake3")
        actual = digest_bundle(root)
        matches = recorded == actual
        print(json.dumps({
            "id": manifest["id"],
            "version": manifest["version"],
            "recorded_digest": recorded,
            "calculated_digest": actual,
            "matches": matches,
            "signature_present": bool(manifest.get("integrity", {}).get("signature")),
            "note": "Resource digest only; not signature verification, hub admission or runtime acceptance.",
        }, ensure_ascii=False))
        raise SystemExit(0 if matches else 1)
    integrity = manifest.setdefault("integrity", {})
    if integrity.get("signature"):
        raise ValueError("Refusing to rewrite a signed manifest")
    integrity["bundle_blake3"] = digest_bundle(root)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "id": manifest["id"],
        "version": manifest["version"],
        "bundle_blake3": integrity["bundle_blake3"],
        "note": "Digest refreshed; this is not a hub admission result.",
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
