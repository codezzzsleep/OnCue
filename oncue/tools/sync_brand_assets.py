#!/usr/bin/env python3
"""Export the single source icon to web and, optionally, the native bundle."""
import argparse
import shutil
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--bundle", action="store_true", help="Also update bundle/assets/icon.svg; restamp the bundle afterwards.")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
source = root / "branding/icon.svg"
targets = [root / "server/static/icon.svg"]
if args.bundle:
    targets.append(root / "bundle/assets/icon.svg")
for target in targets:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    print(target.relative_to(root))
if args.bundle:
    print("Bundle artwork changed. Run hub stamp or tools/stamp_bundle.py before reviewing it again.")
