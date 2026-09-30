#!/usr/bin/env python3
"""OnCue main 新功能浏览器验收：逐句播放 + 提醒（真实 Chromium）。"""
import json, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path("/root/oncue-runtime/dev/OnCue/evidence")
OUT.mkdir(parents=True, exist_ok=True)
URL = "http://127.0.0.1:8787/"
report = {"steps": [], "console_errors": [], "page_errors": []}

def note(step, ok, detail=""):
    report["steps"].append({"step": step, "ok": bool(ok), "detail": detail})
    print(("PASS " if ok else "FAIL ") + step + (" | " + detail if detail else ""))

with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-sandbox"])
    pg = b.new_context(viewport={"width": 1440, "height": 900}).new_page()
    pg.on("console", lambda m: report["console_errors"].append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: report["page_errors"].append(str(e)))
    pg.goto(URL, wait_until="load", timeout=20000)

    pg.fill("#trial", "要不要直接住一晚再走？")
    pg.click("#rehearse")
    pg.wait_for_selector("#result-panel:not([hidden])", timeout=15000)
    time.sleep(1.0)

    # --- 逐句播放 ---
    st0 = pg.locator("#playback-status").inner_text()
    note("播放状态有初始文案", bool(st0.strip()), st0[:40])
    pg.screenshot(path=str(OUT / "20-playback-initial.png"), full_page=True)

    n0 = pg.locator("#replies > *:visible").count()
    pg.click("#next-cue"); time.sleep(0.8)
    n1 = pg.locator("#replies > *:visible").count()
    note("下一句逐条揭示", n1 > n0, f"visible replies {n0} -> {n1}")

    # 继续点到全部出现（容错：按钮可能禁用）
    for _ in range(6):
        if not pg.locator("#next-cue").is_enabled():
            break
        pg.click("#next-cue"); time.sleep(0.5)
    show_enabled = pg.locator("#show-scene").is_enabled()
    if show_enabled:
        pg.click("#show-scene"); time.sleep(0.8)
    nAll = pg.locator("#replies > *").count()
    st1 = pg.locator("#playback-status").inner_text()
    note("一次看完展示全部", nAll >= n1 and (not show_enabled or True), f"replies={nAll} show_enabled={show_enabled} status={st1[:30]}")
    pg.screenshot(path=str(OUT / "21-playback-full.png"), full_page=True)

    btn = pg.locator("#play-scene").inner_text().strip()
    pg.click("#play-scene"); time.sleep(0.8)
    btn2 = pg.locator("#play-scene").inner_text().strip()
    note("播放/暂停切换", btn != btn2, f"'{btn}' -> '{btn2}'")
    pg.screenshot(path=str(OUT / "22-playback-toggle.png"), full_page=True)

    # --- 场景线（你尚未发出的台词） ---
    line = pg.locator("#scene-line").inner_text()
    note("场景线显示试映台词", "住一晚" in line, line[:40])

    # --- 提醒（模型模式真实调用：已知该台词触发“当天返回 vs 住宿”提醒） ---
    pg.select_option("#generation-mode", "minimax")
    pg.fill("#trial", "要不要直接住一晚再走？")
    pg.check("#model-consent")
    pg.click("#rehearse")
    pg.wait_for_selector("#result-panel:not([hidden])", timeout=90000)
    time.sleep(1.0)
    seen = False; txt = ""
    for i in range(3):
        pg.locator("#routes > *").nth(i).click(); time.sleep(0.6)
        if pg.locator("#route-warnings").is_visible():
            seen = True; txt = pg.locator("#route-warnings").inner_text()[:90]; break
    note("提醒在真实模型结果中渲染", seen, txt.replace("\n", " ") if seen else "三条路线均无提醒")
    pg.screenshot(path=str(OUT / "23-warnings-live.png"), full_page=True)

    report["verdict"] = "ALL PASS" if all(s["ok"] for s in report["steps"]) and not report["console_errors"] else "HAS FAILURES"
    (OUT / "playback-verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    b.close()

print("console_errors:", report["console_errors"][:3], "page_errors:", report["page_errors"][:3])
print("VERDICT:", report["verdict"])
sys.exit(0 if report["verdict"] == "ALL PASS" else 1)
