#!/usr/bin/env python3
"""Exercise scene playback in a real Chromium browser against a running OnCue server."""
import argparse
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--url", default="http://127.0.0.1:8787/")
parser.add_argument("--out", type=Path, default=Path("evidence/playback"))
parser.add_argument("--executable", type=Path, help="Use an already installed Chromium/Chrome executable.")
args = parser.parse_args()
args.out.mkdir(parents=True, exist_ok=True)
report = {"steps": [], "console_errors": [], "page_errors": [], "screens": []}


def check(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": detail})
    print(("PASS " if ok else "FAIL ") + name, detail)
    if not ok:
        raise AssertionError(name)


def watch(page):
    page.on("console", lambda m: report["console_errors"].append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: report["page_errors"].append(str(e)))


def visible_count(page):
    return page.locator("#replies .reply:not([hidden])").count()


def shot(page, name):
    page.screenshot(path=str(args.out / name), full_page=True, animations="disabled")
    report["screens"].append(name)


try:
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"],
                                    executable_path=str(args.executable) if args.executable else None)
        report["browser"] = {"name": "chromium", "version": browser.version}
        context = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="light")
        page = context.new_page()
        watch(page)
        calls = []
        page.on("request", lambda req: calls.append(req.url) if req.method == "POST" and
                req.url.endswith("/api/rehearse") else None)
        page.goto(args.url, wait_until="load")
        page.locator("#trial").fill("不如每人带一个线索，中午出发、当天回来？")
        with page.expect_response(lambda r: r.url.endswith("/api/rehearse")) as pending:
            page.locator("#rehearse").click()
        result = pending.value.json()["result"]
        page.locator("#result-panel").wait_for(state="visible")
        check("Origin shows the actual unsent trial", page.locator("#scene-line").inner_text() ==
              "不如每人带一个线索，中午出发、当天回来？")
        check("Hypothetical dialogue stays labelled", page.locator(".fiction-tag").inner_text() == "假设对白")
        count = len(result["routes"][0]["replies"])
        page.wait_for_selector("#replies .reply:not([hidden])")
        check("Autoplay reveals replies", visible_count(page) > 0)
        page.locator("#show-scene").click()
        check("Show all reveals the current route", visible_count(page) == count)
        check("Completed controls have clear states", page.locator("#play-scene").inner_text() == "重新播放" and
              page.locator("#next-cue").is_disabled() and page.locator("#show-scene").is_disabled())

        page.locator("#play-scene").click()
        page.locator("#play-scene").click()
        frozen = visible_count(page)
        page.wait_for_timeout(1250)
        check("Pause freezes playback", frozen < count and visible_count(page) == frozen)
        page.locator("#next-cue").click()
        check("Next cue reveals exactly one reply", visible_count(page) == frozen + 1)
        page.locator("#play-scene").focus()
        page.keyboard.press("Enter")
        expect(page.locator("#play-scene")).to_have_text("重新播放", timeout=10_000)
        check("Keyboard play resumes to completion", visible_count(page) == count)
        shot(page, "01-playback-light.png")

        for index in (2, 1, 0):
            page.locator("#routes .route").nth(index).click()
        page.locator("#show-scene").click()
        expected = result["routes"][0]["replies"]
        page.wait_for_timeout(1250)
        check("Rapid route changes cancel old cues", page.locator("#replies .reply p").all_text_contents() ==
              expected and visible_count(page) == len(expected))
        page.locator("#save-take").click()
        page.locator("#play-scene").click()
        page.locator("#trial").fill("这句已经改了，不应继续播放旧台词。")
        page.wait_for_timeout(1250)
        check("Editing the trial invalidates old playback", page.locator("#result-panel").is_hidden() and
              "播放中" not in page.locator("#playback-status").text_content())
        page.get_by_role("button", name="继续这一幕", exact=True).first.click()
        page.locator("#show-scene").click()
        check("Saved take restores the scene and dialogue", page.locator("#scene-line").inner_text() ==
              "不如每人带一个线索，中午出发、当天回来？" and visible_count(page) == count)
        check("Playback and restore add no model/API calls", len(calls) == 1, str(len(calls)))

        page.set_viewport_size({"width": 320, "height": 900})
        check("320px playback has no horizontal overflow", page.evaluate(
              "document.documentElement.scrollWidth <= document.documentElement.clientWidth"))
        shot(page, "02-playback-320.png")
        page.set_viewport_size({"width": 1440, "height": 900})
        page.emulate_media(color_scheme="dark")
        shot(page, "03-playback-dark.png")

        reduced = browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        rp = reduced.new_page()
        watch(rp)
        rp.goto(args.url, wait_until="load")
        rp.locator("#rehearse").click()
        rp.locator("#result-panel").wait_for(state="visible")
        reduced_total = rp.locator("#replies .reply").count()
        check("Reduced motion shows every reply immediately", reduced_total > 0 and
              visible_count(rp) == reduced_total and rp.locator("#play-scene").inner_text() == "重新播放")
        check("Reduced motion has no cue animation", rp.locator("#replies .scene-enter").count() == 0)
        rp.locator("#play-scene").click()
        check("Reduced motion replay stays immediate", visible_count(rp) == reduced_total)
        rp.locator("#routes .route").nth(1).click()
        check("Opening warnings are separate from corrected routes", rp.locator("#trial-warnings").is_visible() and
              rp.locator("#route-warnings").is_hidden())
        rp.locator("#trial").fill("中午12点后出发、当天回来，预算和路线先核实？")
        rp.locator("#rehearse").click()
        rp.locator("#result-panel").wait_for(state="visible")
        check("Rewriting the opening clears the old warning", rp.locator("#trial-warnings").is_hidden())
        reduced.close()
        context.close()
        browser.close()
except Exception as error:
    report["failure"] = str(error)

report["verdict"] = "ALL PASS" if report["steps"] and all(s["ok"] for s in report["steps"]) and not (
    report["console_errors"] or report["page_errors"] or report.get("failure")) else "HAS FAILURES"
(args.out / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(report["verdict"])
sys.exit(0 if report["verdict"] == "ALL PASS" else 1)
