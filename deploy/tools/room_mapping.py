#!/usr/bin/env python3
"""房间映射可复现脚本（**无凭据**）：API 事件元数据 × OnCue 有序正文指纹。

AI1 #327 / #332 的要求：
  1. 提交信息不能替代版本化源码 → 本脚本把规则全部固定下来
  2. `zip()` 会**静默截短**：若 app 侧只有 11 条而全部一致，旧版会报 11/11 并 exit 0（假绿）。
     所以现在**先做计数门禁**，任何一项不满足就直接失败：
       · body 文件编号必须是 1..N 连续、且 N == bodies-index 的 count
       · 每个文件的实际字节数必须等于 index 里声明的 bytes
       · len(app_side) 必须等于 --take
       · len(api_side) 必须等于 --take（API 返回不足也算失败）
  3. index 里的 app 侧 sender 要与 API 侧 sender**逐项比较**（否则"两侧一致"根本没被验证）
  4. 只读 600 会话文件；不打印 token / 正文 / 完整 room id（只出 SHA256 前 16 位）

用法:
  room_mapping.py --app-dir <探针落盘目录> [--session <600 会话文件>] [--room-file <room id 文件>]
                   [--limit 30] [--take 12]
"""
import argparse
import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

PROXY = "http://127.0.0.1:17888"


def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch(opener, base, token, path, tries=4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(base + path, headers={"Authorization": "Bearer " + token})
            with opener.open(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as exc:  # 网络抖动：退避重试
            last = exc
            time.sleep(1.5 * (i + 1))
    raise last


def read_app_side(app_dir: Path):
    """返回 (entries, problems)。entries = [(idx, sender, chars, bytes, file_bytes, sha256)]。

    计数门禁：编号连续、count 匹配、文件字节 == index 声明字节、无残留。任一不满足记进 problems。
    """
    problems = []
    idxf = app_dir / "bodies-index.txt"
    if not idxf.is_file():
        return [], [f"缺少 {idxf}"]
    index_text = idxf.read_text(encoding="utf-8")
    m_count = re.search(r"^count=(\d+)$", index_text, re.M)
    if not m_count:
        problems.append("bodies-index.txt 里没有 count=")
        declared_count = None
    else:
        declared_count = int(m_count.group(1))

    rows = re.findall(r"^M(\d+) sender=(\S+) chars=(\d+) bytes=(\d+)$", index_text, re.M)
    entries = []
    for idx_s, sender, chars_s, bytes_s in rows:
        i = int(idx_s)
        f = app_dir / f"body-{i}.txt"
        if not f.is_file():
            problems.append(f"index 声明了 M{i}，但 body-{i}.txt 不存在")
            continue
        raw = f.read_bytes()
        if len(raw) != int(bytes_s):
            problems.append(f"M{i}: 文件 {len(raw)} B ≠ index 声明的 {bytes_s} B（fs.write 应逐字节落盘）")
        entries.append((i, sender, int(chars_s), int(bytes_s), len(raw), sha256_hex(raw)))

    got = sorted(e[0] for e in entries)
    if got and got != list(range(1, len(got) + 1)):
        problems.append(f"body 编号不连续: {got}")

    on_disk = sorted(int(p.stem.split("-")[1]) for p in app_dir.glob("body-*.txt")
                     if p.stem.split("-")[1].isdigit())
    if on_disk != got:
        problems.append(f"落盘 body 文件编号 {on_disk} 与 index 声明的 {got} 不一致（疑似残留）")

    if declared_count is not None and declared_count != len(entries):
        problems.append(f"count={declared_count} 与实际条目 {len(entries)} 不一致")
    return entries, problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app-dir", required=True, help="探针落盘目录（含 body-N.txt 与 bodies-index.txt）")
    ap.add_argument("--session", default="/srv/oncue-runtime/state/matrix-session.json")
    ap.add_argument("--room-file", default="/srv/oncue-runtime/state/test-room-id.txt")
    ap.add_argument("--limit", type=int, default=30, help="API 一次取多少条（越大越能确保不饱和）")
    ap.add_argument("--take", type=int, default=12, help="与 app 侧对照的最新 N 条（产品 limit=12）")
    a = ap.parse_args()

    app_dir = Path(a.app_dir)
    sess = json.loads(Path(a.session).read_text(encoding="utf-8"))
    app_entries, app_problems = read_app_side(app_dir)

    base = sess["homeserver"].rstrip("/")
    token = sess["access_token"]
    room_id = Path(a.room_file).read_text(encoding="utf-8").strip()
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({"https": PROXY, "http": PROXY}))
    chunk = fetch(opener, base, token,
                  f"/_matrix/client/v3/rooms/{urllib.parse.quote(room_id)}/messages"
                  f"?dir=b&limit={a.limit}")["chunk"]
    msgs = [m for m in chunk
            if m.get("type") == "m.room.message"
            and "[OnCue" in m.get("content", {}).get("body", "")]
    msgs.reverse()  # dir=b 新的在前 → 转时间正序
    api_side = msgs[-a.take:]

    print(f"# 房间映射（可复现，含计数门禁） 生成时间 {time.strftime('%Y-%m-%dT%H:%M:%S%z')}")
    print(f"# room_id(SHA256前16)  {sha256_hex(room_id.encode())[:16]}")
    print(f"# 筛选: type==m.room.message 且 body 含 '[OnCue'")
    print(f"# 排序: /messages?dir=b&limit={a.limit} 取回后 reverse 成时间正序")
    print(f"# 取样: 最新 {a.take} 条；API 侧筛后共 {len(msgs)} 条，app 侧 {len(app_entries)} 条")
    print()

    problems = list(app_problems)
    if len(app_entries) != a.take:
        problems.append(f"app 侧条目 {len(app_entries)} ≠ 期望 {a.take}（zip 会静默截短，故必须先卡这里）")
    if len(api_side) != a.take:
        problems.append(f"API 侧条目 {len(api_side)} ≠ 期望 {a.take}")

    print("| # | event_id(SHA256前16) | origin_server_ts | sender | API正文SHA256(前16) | OnCue正文SHA256(前16) | sender一致 | 正文一致 |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- |")
    body_ok = sender_ok = paired = 0
    for n, (m, app) in enumerate(zip(api_side, app_entries), start=1):
        _i, app_sender, _ac, _ab, _af, app_h = app
        # 两侧表示不同，必须归一化后才能比：
        #   API 侧 : "@codezzzsleep:matrix.org"
        #   app 侧 : "codezzzsleep"（host 归一化成 localpart，且**不带** @）
        api_sender = m["sender"].split(":")[0].lstrip("@")
        app_sender_n = app_sender.lstrip("@")
        api_h = sha256_hex(m["content"]["body"].encode("utf-8"))
        same_body = api_h == app_h
        same_sender = app_sender_n == api_sender
        body_ok += same_body
        sender_ok += same_sender
        paired += 1
        print(f"| {n} | {sha256_hex(m['event_id'].encode())[:16]} | {m['origin_server_ts']} | "
              f"{api_sender} | {api_h[:16]} | {app_h[:16]} | {'✓' if same_sender else '✗'} | {'✓' if same_body else '✗'} |")
    print()
    print(f"配对条数: {paired}/{a.take}")
    print(f"正文指纹一致: {body_ok}/{a.take}")
    print(f"sender 一致  : {sender_ok}/{a.take}")
    if len(msgs) > len(app_entries):
        print(f"未被 app 读到的是**最早**那条（chars={len(msgs[0]['content']['body'])}）")
    print("说明: event_id / origin_server_ts 仅来自 API 侧；app 响应只暴露 sender/body，"
          "故本表是**有序正文指纹对照**，不声称 app 看到了事件元数据。")

    if problems:
        print()
        print("门禁失败：")
        for p in problems:
            print(f"  ✗ {p}")
        return 1
    ok = (paired == a.take and body_ok == a.take and sender_ok == a.take)
    print()
    print(f"门禁：计数/编号/字节/app文件 全部通过；最终判据={ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
