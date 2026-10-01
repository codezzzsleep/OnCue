#!/usr/bin/env python3
"""从私有凭据生成 octos 内核的 provider profile —— **不打印任何密文**。

权威格式：`apps/ai-providers/config/src/profile.rs:1-30`
  - 文件位置 `<core_dir>/profiles/_main.json`，权限 0600（原子替换）
  - 必须有完整 envelope：id/name/enabled/created_at/updated_at/config
    （**裸 `{config}` 会被 octos 当作"没有 profile"**，见 profile.rs 注释）
  - `config.env_vars.<NAME>` 放密文；`config.llm.primary.route.api_key_env` 指定变量名

用法:
  make_provider_profile.py [--creds PATH] [--core-dir DIR] [--dry-run]
"""
import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_CREDS = "/root/oncue-runtime/state/ai2-credentials.json"
DEFAULT_CORE = os.environ.get("OCTOS_APP_CORE_DIR", "/root/oncue-runtime/state/octos-core")


def mask(v):
    if len(v) <= 4:
        return f"len={len(v)} ***"
    return f"len={len(v)} {v[:2]}***{v[-2:]}"


def pick_family(base_url: str) -> tuple[str, str]:
    """返回 (family_id, api_key_env)。按 apps/ai-providers/config/src/registry.rs 的取值。"""
    host = base_url.lower()
    if "minimaxi.com" in host:
        return "minimax-cn", "MINIMAX_CN_API_KEY"
    if "minimax" in host:
        return "minimax", "MINIMAX_API_KEY"
    return "openai", "OPENAI_API_KEY"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--creds", default=DEFAULT_CREDS)
    ap.add_argument("--core-dir", default=DEFAULT_CORE)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    creds = json.loads(Path(a.creds).read_text(encoding="utf-8"))
    mm = creds.get("minimax")
    if not isinstance(mm, dict):
        raise SystemExit("凭据里没有 minimax 段")

    base_url = mm.get("base_url", "")
    api_type = mm.get("api_type", "openai")
    model_id = mm.get("model", "")
    api_key = mm.get("api_key", "")
    for k, v in (("base_url", base_url), ("model", model_id), ("api_key", api_key)):
        if not v:
            raise SystemExit(f"minimax.{k} 为空，拒绝生成半成品 profile")

    family_id, key_env = pick_family(base_url)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    profile = {
        "id": "_main",
        "name": "Main",
        "enabled": True,
        "created_at": now,
        "updated_at": now,
        "config": {
            "llm": {
                "primary": {
                    "family_id": family_id,
                    "model_id": model_id,
                    "route": {
                        "base_url": base_url,
                        "api_type": api_type,
                        "api_key_env": key_env,
                    },
                }
            },
            # 原生优先路径：密文**不写进 profile**，profile 只放 keychain 标记；
            # 真值放 <core_dir>/secrets/<ENV>，0600 / 目录 0700。
            # 依据：host-service/src/model.rs:284-300 的 save()（vault 成功→标记；失败才回退原文）
            #      与 vault.rs:79 SecretsDir::new(core_dir.join("secrets"))。
            "env_vars": {key_env: "keychain:"},
        },
    }
    secret_path = Path(a.core_dir) / "secrets" / key_env

    print("写入计划（脱敏）:")
    print(f"  profile  : {Path(a.core_dir) / 'profiles' / '_main.json'}")
    print(f"  secret   : {secret_path}  ← 密文放这里（0600，目录 0700）")
    print(f"  env_vars : {key_env} = 'keychain:'  ← profile 里只放标记，不放密文")
    print(f"  id/name  : {profile['id']} / {profile['name']}  enabled={profile['enabled']}")
    print(f"  family_id: {family_id}")
    print(f"  model_id : {model_id}")
    print(f"  base_url : {mask(base_url)}")
    print(f"  api_type : {api_type}")
    print(f"  api_key  : {mask(api_key)}（只在 secrets 文件里，不进 profile）")

    if a.dry_run:
        print("--dry-run：未写盘")
        return 0

    dest = Path(a.core_dir) / "profiles" / "_main.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(dest.parent, 0o700)

    # 1) 原生 secrets 文件：<core_dir>/secrets/<ENV>，0600 / 目录 0700
    secret_path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(secret_path.parent, 0o700)
    sfd = os.open(secret_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(sfd, "w", encoding="utf-8") as fh:
        fh.write(api_key + "\n")
    os.chmod(secret_path, 0o600)

    # 2) profile：原子替换 + 0600（与 profile.rs 的写盘约定一致）
    fd, tmp = tempfile.mkstemp(dir=str(dest.parent), prefix="._main.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(profile, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        os.chmod(tmp, 0o600)
        os.replace(tmp, dest)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

    st = os.stat(dest)
    sst = os.stat(secret_path)
    back = json.loads(dest.read_text(encoding="utf-8"))
    ok_envelope = all(k in back for k in ("id", "name", "created_at", "updated_at", "config"))
    ok_llm = bool(back["config"]["llm"]["primary"].get("family_id")
                  and back["config"]["llm"]["primary"].get("model_id"))
    # 关键自检：profile 里**不能**出现密文本身，只能是 keychain 标记
    env_vals = back["config"].get("env_vars", {})
    profile_has_marker = env_vals.get(key_env) == "keychain:"
    profile_leaks_secret = any(isinstance(v, str) and api_key in v for v in env_vals.values())
    print(f"已写入 profile : {dest}  权限={oct(st.st_mode & 0o777)}  字节={st.st_size}")
    print(f"已写入 secret  : {secret_path}  权限={oct(sst.st_mode & 0o777)}  字节={sst.st_size}")
    print(f"自检：envelope 完整={ok_envelope}  有 llm.primary={ok_llm}")
    print(f"自检：profile 里是 keychain 标记={profile_has_marker}  密文未泄漏进 profile={not profile_leaks_secret}")
    return 0 if (ok_envelope and ok_llm and profile_has_marker and not profile_leaks_secret) else 1


if __name__ == "__main__":
    sys.exit(main())
