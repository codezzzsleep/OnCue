#!/usr/bin/env python3
"""为 044 分页验证生成**探针包**：把长文本夹具内联进 main.splash 的 cue_sources。

为什么要内联：卡片应用**读不到宿主文件系统**，所以夹具只能进源码。
为什么不 prepend：main.splash 第 1 行就是 `let cue_sources = []`，
在它前面赋值会与 `let` 冲突（且可能触发 TDZ），所以直接**替换第 1 行**。

用法: python3 make_probe_bundle.py <fixture.txt> <out_dir> [app_id]

生成后必须使用官方 card-host 的 ``--stamp`` 重新计算开发探针摘要；
本工具会主动移除复制来的旧摘要，避免把不一致的产物误当成已校验包。
"""
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_BUNDLE = REPO_ROOT / "oncue" / "bundle"


def esc(s: str) -> str:
    """转成 Splash 字符串字面量内容：反斜杠、双引号、换行。"""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def validate_out(out: Path) -> Path:
    """拒绝会删除仓库、源码、当前目录或广泛父目录的输出路径。"""
    resolved = out.expanduser().resolve()
    protected = (Path("/"), Path.cwd().resolve(), REPO_ROOT, SRC_BUNDLE)
    if resolved in protected:
        raise ValueError(f"拒绝危险输出目录: {resolved}")
    if REPO_ROOT.is_relative_to(resolved):
        raise ValueError(f"输出目录不能包含仓库: {resolved}")
    if resolved.is_relative_to(SRC_BUNDLE):
        raise ValueError(f"输出目录不能位于源 bundle 内: {resolved}")
    if not resolved.name:
        raise ValueError(f"无效输出目录: {resolved}")
    return resolved


def main():
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    fixture = Path(sys.argv[1]).expanduser().resolve()
    try:
        out = validate_out(Path(sys.argv[2]))
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2
    app_id = sys.argv[3] if len(sys.argv) > 3 else "ai2-probe-" + fixture.stem

    if not fixture.is_file():
        print(f"夹具不存在或不是文件: {fixture}", file=sys.stderr)
        return 2
    text = fixture.read_text(encoding="utf-8").replace("\r\n", "\n")
    if "\r" in text or "\x00" in text:
        print("夹具含不受支持的孤立 CR 或 NUL", file=sys.stderr)
        return 2
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
    integ.pop("bundle_blake3", None)
    integ.pop("signature", None)
    integ.pop("publisher", None)
    mf.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 证据：字符/字节/行数（不回显正文）
    print(f"夹具      : {fixture.name}")
    print(f"  chars={len(text)}  utf8_bytes={len(text.encode())}  lines={text.count(chr(10))+1}")
    print(f"探针包    : {out}")
    print(f"  app_id={app_id}  main.splash={splash.stat().st_size} B")
    print(f"  第1行已内联夹具（转义后 {len(esc(text))} 字符）")
    print("  摘要已移除；运行前必须用 card-host --stamp 重新计算")
    return 0


if __name__ == "__main__":
    sys.exit(main())
