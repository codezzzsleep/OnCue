#!/usr/bin/env python3
"""为 044 分页验证生成**探针包**：把长文本夹具内联进 main.splash 的 cue_sources。

为什么要内联：卡片应用**读不到宿主文件系统**，所以夹具只能进源码。
为什么不 prepend：main.splash 第 1 行就是 `let cue_sources = []`，
在它前面赋值会与 `let` 冲突（且可能触发 TDZ），所以直接**替换第 1 行**。

用法: make_probe_bundle.py <fixture.txt> <out_dir> [app_id]
"""
import json
import re
import shutil
import sys
from pathlib import Path

SRC_BUNDLE = Path("/root/hackthon/OnCue/oncue/bundle")


def esc(s: str) -> str:
    """转成 Splash 字符串字面量内容：反斜杠、双引号、换行。"""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\r\n", "\n").replace("\n", "\\n")


def main():
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    fixture = Path(sys.argv[1])
    out = Path(sys.argv[2])
    app_id = sys.argv[3] if len(sys.argv) > 3 else "ai2-probe-" + fixture.stem

    text = fixture.read_text(encoding="utf-8")
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(SRC_BUNDLE, out)

    splash = out / "main.splash"
    src = splash.read_text(encoding="utf-8")

    # 关键：启动时会调用 cue_show_demo()，它**覆盖** cue_sources。
    # 所以只替换第 1 行没用——必须替换 cue_show_demo() 里那个 12 条消息的数组。
    marker = "fn cue_show_demo(){"
    i = src.index(marker)
    j = src.index("cue_sources = [", i)
    # 数组到其后第一个处于行首缩进的 "]" 结束（demo 数组里只有 {} 没有 []）
    k = src.index("\n    ]", j) + len("\n    ]")
    replaced = f'cue_sources = [\n        {{sender: "夹具", body: "{esc(text)}"}}\n    ]'
    src = src[:j] + replaced + src[k:]

    # 同时把第 1 行的空数组也填上（保险起见，避免首帧闪烁为空）
    first_nl = src.index("\n")
    line1 = src[:first_nl]
    if line1.strip().startswith("let cue_sources"):
        src = f'let cue_sources = [{{sender: "夹具", body: "{esc(text)}"}}]' + src[first_nl:]

    splash.write_text(src, encoding="utf-8")

    # manifest：唯一 id / 0.0.1 / 只要 storage / 去签名
    mf = out / "manifest.json"
    m = json.loads(mf.read_text(encoding="utf-8"))
    m["id"] = app_id
    m["version"] = "0.0.1"
    m["name"] = f"分页探针 {fixture.stem}"
    m["capabilities"] = ["storage"]
    integ = m.setdefault("integrity", {})
    integ.pop("signature", None)
    integ.pop("publisher", None)
    mf.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 证据：字符/字节/行数（不回显正文）
    print(f"夹具      : {fixture.name}")
    print(f"  chars={len(text)}  utf8_bytes={len(text.encode())}  lines={text.count(chr(10))+1}")
    print(f"探针包    : {out}")
    print(f"  app_id={app_id}  main.splash={splash.stat().st_size} B")
    print(f"  第1行已内联夹具（转义后 {len(esc(text))} 字符）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
