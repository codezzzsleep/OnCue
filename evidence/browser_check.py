#!/usr/bin/env python3
"""OnCue v0.2 真实浏览器核验：Chromium(headless) + Playwright，闭环核心流程并取证。"""
import json, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path("/root/oncue-runtime/dev/OnCue-v0.2/evidence")
OUT.mkdir(parents=True, exist_ok=True)
URL = "http://127.0.0.1:8787/"
report = {"console_errors": [], "page_errors": [], "steps": [], "screens": []}

def note(step, ok, detail=""):
    report["steps"].append({"step": step, "ok": bool(ok), "detail": detail})
    print(("PASS " if ok else "FAIL ") + step + (" | " + detail if detail else ""))

with sync_playwright() as p:
    browser = p.chromium.launch(args=["--no-sandbox"])
    ctx = browser.new_context(viewport={"width": 1440, "height": 900},
                              color_scheme="light", accept_downloads=True)
    page = ctx.new_page()
    page.on("console", lambda m: report["console_errors"].append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: report["page_errors"].append(str(e)))

    page.goto(URL, wait_until="load", timeout=20000)
    note("页面加载", "群聊试映室" in page.title(), page.title())
    note("登录面板隐藏(本地无口令)", page.locator("#login-panel").is_hidden())
    note("工作室显示", page.locator("#studio").is_visible())
    page.screenshot(path=str(OUT / "01-desktop-light.png"), full_page=True)

    # 填入台词并试映
    page.fill("#trial", "那就定周五晚的新干线？")
    page.click("#rehearse")
    page.wait_for_selector("#result-panel:not([hidden])", timeout=15000)
    note("试映出结果面板", True)
    routes = page.locator("#routes .route, #routes [data-route], #routes > *").count()
    note("三条路线渲染", routes >= 3, f"route nodes={routes}")
    page.screenshot(path=str(OUT / "02-routes-light.png"), full_page=True)

    # 切换路线 B / C
    page.locator("#routes > *").nth(1).click()
    time.sleep(0.4)
    sub_b = page.locator("#route-subtitle").inner_text()
    page.screenshot(path=str(OUT / "03-route-b.png"), full_page=True)
    page.locator("#routes > *").nth(2).click()
    time.sleep(0.4)
    sub_c = page.locator("#route-subtitle").inner_text()
    page.screenshot(path=str(OUT / "04-route-c.png"), full_page=True)
    note("路线切换(subtitle 变化)", sub_b != sub_c, f"B={sub_b} / C={sub_c}")

    # 放进草稿 -> 保留 -> 存档两次 -> 对照
    page.click("#use-draft"); time.sleep(0.3)
    draft_val = page.locator("#draft").input_value()
    note("草稿自动填充", len(draft_val) > 5, draft_val[:40])
    page.click("#keep-draft"); time.sleep(0.3)
    note("草稿保留", "已保留" in (page.locator("#draft-status").inner_text() or ""),
         page.locator("#draft-status").inner_text())
    page.click("#save-take"); time.sleep(0.3)
    page.fill("#trial", "换成：周五新干线+看山旅馆，人均 7500 够吗？")
    page.click("#rehearse")
    page.wait_for_selector("#result-panel:not([hidden])", timeout=15000)
    page.click("#save-take"); time.sleep(0.4)
    n_arch = page.locator("#archive-list > *").count()
    note("两个存档点", n_arch == 2, f"archive nodes={n_arch}")
    page.screenshot(path=str(OUT / "05-archives.png"), full_page=True)
    page.click("#compare"); time.sleep(0.5)
    cmp_visible = page.locator("#compare-panel").is_visible()
    note("对照面板显示", cmp_visible)
    page.screenshot(path=str(OUT / "06-compare.png"), full_page=True)

    # 导出草稿（真实下载）
    with page.expect_download(timeout=8000) as dl:
        page.click("#export-draft")
    d = dl.value
    path = OUT / "07-export.suggestion.txt"
    d.save_as(str(path))
    note("导出台词下载", path.exists() and path.stat().st_size > 10,
         f"{d.suggested_filename} {path.stat().st_size}B")

    # 刷新后草稿持久化（放末尾，避免打乱存档序列）
    page.reload(wait_until="load"); time.sleep(0.8)
    restored = page.locator("#draft").input_value() if page.locator("#draft").is_visible() else ""
    note("刷新后草稿持久化", restored.startswith("玩个半日旅行盲盒"),
         restored[:40] if restored else "(草稿面板未恢复)")
    arch_after_reload = page.locator("#archive-list > *").count()
    note("刷新后存档仍保留", arch_after_reload == 2, f"archives={arch_after_reload}")
    page.screenshot(path=str(OUT / "10-after-reload.png"), full_page=True)

    # 窄屏 320 / 736 + 深色主题
    for w, tag in ((320, "m320"), (736, "m736")):
        page.set_viewport_size({"width": w, "height": 900}); time.sleep(0.4)
        overflow = page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
        note(f"{tag}px 无横向溢出", not overflow)
        page.screenshot(path=str(OUT / f"08-{tag}.png"), full_page=True)
    page.set_viewport_size({"width": 1440, "height": 900})
    ctx.dark = None
    dark = browser.new_context(viewport={"width": 1440, "height": 900},
                               color_scheme="dark", accept_downloads=True)
    dp = dark.new_page(); dp.goto(URL, wait_until="load", timeout=20000)
    dp.fill("#trial", "深色主题下试一句：那我们先定周五晚的新干线？")
    dp.click("#rehearse")
    dp.wait_for_selector("#result-panel:not([hidden])", timeout=15000)
    dp.screenshot(path=str(OUT / "09-dark.png"), full_page=True)
    note("深色主题渲染", dp.locator("#result-panel").is_visible())
    dark.close()

    report["screens"] = sorted(x.name for x in OUT.glob("*.png"))
    browser.close()

report["verdict"] = "ALL PASS" if all(s["ok"] for s in report["steps"]) and not report["console_errors"] else "HAS FAILURES"
(OUT / "browser-verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
print("\nconsole_errors:", report["console_errors"][:5], "page_errors:", report["page_errors"][:3])
print("VERDICT:", report["verdict"])
sys.exit(0 if report["verdict"] == "ALL PASS" else 1)
