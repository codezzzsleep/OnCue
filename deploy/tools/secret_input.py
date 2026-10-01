#!/usr/bin/env python3
"""从私有 state 读取凭据字段并注入到宿主 UI —— **凭据不出现在命令行，也不打印明文**。

用法:
  secret_input.py type <field> [--creds PATH]    # 私有字段经 stdin 送到 xtype
  secret_input.py masked <field> [--creds PATH]  # 只打印长度，不打印字段取值

支持点号路径，例如 `matrix.homeserver` / `matrix.password` / `minimax.api_key`。
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

DEFAULT_CREDS = "/root/oncue-runtime/state/ai2-credentials.json"
DEFAULT_VNC_PW = "/root/oncue-runtime/state/vnc/vnc.password.txt"


def get_field(path, dotted):
    node = json.loads(Path(path).read_text(encoding="utf-8"))
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            raise SystemExit(f"凭据文件里没有字段 {dotted!r}（在 {part!r} 处中断）")
        node = node[part]
    if not isinstance(node, str):
        raise SystemExit(f"字段 {dotted!r} 不是字符串")
    return node


def mask(value):
    return f"len={len(value)} ***"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["type", "masked"])
    ap.add_argument("field")
    ap.add_argument("--creds", default=DEFAULT_CREDS)
    ap.add_argument("--vnc-password-file", default=DEFAULT_VNC_PW)
    ap.add_argument("--port", type=int, default=5901)
    a = ap.parse_args()

    value = get_field(a.creds, a.field)

    if a.action == "masked":
        print(f"{a.field}: {mask(value)}")
        return 0

    # 用 xtype（libX11+libXtst，按服务器自身键映射算 Shift 层）而不是 RFB 键事件：
    # RFB 路径实测会把 `A_z9!@#-_` 打成 `az9-rg`，密码一旦含大写/符号就被静默打错。
    import subprocess
    xtype = str(Path(__file__).resolve().parent / "xtype.py")
    proc = subprocess.run([sys.executable, xtype, "--stdin"], input=value,
                          capture_output=True, text=True)
    sys.stdout.write(proc.stdout)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
    # 只报长度，绝不回显取值
    print(f"typed {a.field} ({mask(value)})")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
