#!/usr/bin/env python3
"""Read the makepad-remote /snap tree and print the cue_* widgets (no images)."""
import json, sys, urllib.request

def snap():
    with urllib.request.urlopen("http://127.0.0.1:18141/snap?all=1", timeout=15) as r:
        return json.load(r)["s"]

KEYS = ("cue_status", "cue_draft", "cue_trial", "cue_scene_label", "cue_preview_list")
BADGE = {"cue_status": "S", "cue_draft": "D", "cue_trial": "T", "cue_scene_label": "SC"}
for e in snap():
    i = e.get("i", "")
    r = e.get("r") or [0, 0, 0, 0]
    t = e.get("t", "") or ""
    v = e.get("val", "") or ""
    if i in KEYS:
        print(f"[{i}] r={r} t={t!r}")
        if v:
            print(f"    val(len={len(v)})={v!r}")
    elif e.get("ty") == "Button" and 380 <= r[1] <= 400 and 580 <= r[0] <= 850:
        print(f"  route [{r[0]},{r[1]}] cx={r[0]+r[2]//2} cy={r[1]+r[3]//2} {t!r}")
    elif e.get("ty") == "Button" and 338 <= r[1] <= 352 and 580 <= r[0] <= 920:
        print(f"  dbtn  [{r[0]},{r[1]}] cx={r[0]+r[2]//2} cy={r[1]+r[3]//2} {t!r}")
