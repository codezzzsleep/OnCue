#!/usr/bin/env python3
"""房间映射可复现脚本（**无凭据**）：API 事件元数据 × OnCue 有序正文指纹。

AI1 #327 的要求：提交信息不能替代版本化源码。本脚本把「怎么筛 / 怎么排序 /
怎么取最新 12 / event_id 怎么哈希 / 正文怎么哈希 / 怎么与 app 落盘顺序对照」全部固定下来，
并且**只以布尔与 SHA 输出**——不打印 token、不打印正文、不打印完整 room id。

用法:
  room_mapping.py --app-dir <探针落盘目录> [--session <600 会话文件>] [--room-file <room id 文件>]
                   [--limit 30] [--take 12]

输入约定:
  · <探针落盘目录> 里应有 roommap 探针写下的 body-1.txt … body-N.txt 与 bodies-index.txt
    （探针源码见 evidence/native/rinx-developer-review/probe-src/roommap-probe.splash）
  · 会话文件只被**读取**，token 绝不打印、绝不写入任何输出
  · room id 从 --room-file 读；输出里**只出现 room id 的 SHA256 前 16 位**

输出（stdout，确定性）:
  · 头部：条数、筛选规则、排序规则、取多少
  · 表格：序号 | event_id(SHA256前16) | origin_server_ts | sender(localpart) |
          API 正文 UTF-8 SHA256(前16) | OnCue 正文 UTF-8 SHA256(前16) | 一致
  · 结尾：有序正文指纹一致计数
"""
import argparse
import hashlib
import json
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app-dir", required=True, help="探针落盘目录（含 body-N.txt）")
    ap.add_argument("--session", default="/srv/oncue-runtime/state/matrix-session.json")
    ap.add_argument("--room-file", default="/srv/oncue-runtime/state/test-room-id.txt")
    ap.add_argument("--limit", type=int, default=30, help="API 一次取多少条（越大越能确保不饱和）")
    ap.add_argument("--take", type=int, default=12, help="与 app 侧对照的最新 N 条（产品 limit=12）")
    a = ap.parse_args()

    app_dir = Path(a.app_dir)
    sess = json.loads(Path(a.session).read_text(encoding="utf-8"))

    # 1) app 侧：按读取顺序（body-1, body-2, …）算正文 UTF-8 SHA256
    #    注意：探针用 fs.write 逐字节落盘（index 里声明的 bytes= 与文件长度相等），
    #    所以这里直接对文件字节做哈希就等于对正文做哈希。
    app_files = sorted(app_dir.glob("body-*.txt"),
                       key=lambda p: int(p.stem.split("-")[1]))
    app_side = [(sha256_hex(p.read_bytes()), p.stat().st_size) for p in app_files]

    # 2) API 侧：取该房间的最近消息（dir=b），筛出文本消息，再按时间正序
    base = sess["homeserver"].rstrip("/")
    token = sess["access_token"]
    room_id = Path(a.room_file).read_text(encoding="utf-8").strip()
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({"https": PROXY, "http": PROXY}))
    chunk = fetch(opener, base, token,
                  f"/_matrix/client/v3/rooms/{urllib.parse.quote(room_id)}/messages"
                  f"?dir=b&limit={a.limit}")["chunk"]
    # 筛选规则：m.room.message 且正文含 "[OnCue"（与 app 读到的同批测试消息）
    msgs = [m for m in chunk
            if m.get("type") == "m.room.message"
            and "[OnCue" in m.get("content", {}).get("body", "")]
    msgs.reverse()  # dir=b 是新的在前；转成时间正序
    api_side = msgs[-a.take:]  # 取**最新** take 条（与产品 limit 对齐）

    # 3) 输出（确定性；不含 token / 正文 / 完整 room id）
    print(f"# 房间映射（可复现） 生成时间 {time.strftime('%Y-%m-%dT%H:%M:%S%z')}")
    print(f"# room_id(SHA256前16)  {sha256_hex(room_id.encode())[:16]}")
    print(f"# 筛选: type==m.room.message 且 body 含 '[OnCue'")
    print(f"# 排序: /messages?dir=b&limit={a.limit} 取回后 reverse 成时间正序")
    print(f"# 取样: 最新 {a.take} 条（产品 limit=12）；API 侧共 {len(msgs)} 条，app 侧 {len(app_side)} 条")
    print("# 未被 app 读到的是**最早**那条" if len(msgs) > len(app_side) else "# 两侧条数相同")
    print()
    print("| # | event_id(SHA256前16) | origin_server_ts | sender | API正文SHA256(前16) | OnCue正文SHA256(前16) | 一致 |")
    print("| --- | --- | --- | --- | --- | --- | --- |")
    ok = 0
    for i, (m, app) in enumerate(zip(api_side, app_side), start=1):
        eid = m["event_id"]
        ts = m["origin_server_ts"]
        sender = m["sender"].split(":")[0]          # 去 homeserver，只留 localpart
        body = m["content"]["body"]
        api_h = sha256_hex(body.encode("utf-8"))
        app_h, _ = app
        same = api_h == app_h
        ok += same
        print(f"| {i} | {sha256_hex(eid.encode())[:16]} | {ts} | {sender} | "
              f"{api_h[:16]} | {app_h[:16]} | {'✓' if same else '✗'} |")
    print()
    print(f"有序正文指纹逐条一致: {ok}/{len(app_side)}")
    print("说明: event_id / origin_server_ts 仅来自 API 侧；app 响应只暴露 sender/body，"
          "故本表是**有序正文指纹对照**，不声称 app 看到了事件元数据。")
    return 0 if ok == len(app_side) and app_side else 1


if __name__ == "__main__":
    sys.exit(main())
