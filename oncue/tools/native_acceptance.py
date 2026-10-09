#!/usr/bin/env python3
"""Record an explicitly authorized Rinx-native run; never silently reuse a live app.

This tool can import a bundle, read a real room, consume model budget, and overwrite
synthetic test drafts ONLY with the corresponding command-line permissions. It does
not start a host, configure a provider, send messages, or read credentials. Account
and host-binary inputs are operator-supplied; the account marker is checked, but it
is not a cryptographic attestation of the bridge's live account or process.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

from native_bridge import Bridge
from rinx_session import module, resize

APP_ID = "oncue-screening-room"
DEFAULT_RELEASE = Path(__file__).resolve().parents[1] / "bundle"
SUCCESS = "三种说法好了。每条下面是它依据的原文，选之前对一下。"
CONSENT = "允许当前范围内的试映与修订"
CONSENT_GRANTED = "已允许。点试映或修订时，会把台词、目标和勾选的消息发给助手。"
SAVE_SUCCESS = "草稿已保存在本机，没有发到群里。"
STORE_FILE = "rehearsals-v1.json"
LEGACY_FILES = ("draft.txt", "take-a.txt", "take-b.txt")
SLOT_INDEX = {"draft": 1, "A": 2, "B": 3}
ROUTES = (("A 顺着说", "顺着这句"), ("B 换问法", "换个问法"), ("C 换玩法", "换个玩法"))


def require(condition, message):
    """Do not use assert: acceptance checks must also run under python -O."""
    if not condition:
        raise RuntimeError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def plain_path(value, *, directory=False, missing_ok=False):
    """Reject symlink components before following a caller-supplied path."""
    path = Path(value).absolute()
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        require(not current.is_symlink(), f"Symlink path is not allowed: {current}")
    path = path.resolve()
    if missing_ok and not path.exists():
        return path
    require(path.is_dir() if directory else path.is_file(), f"Missing path: {path}")
    return path


def output_path(value, *protected_roots):
    """Refuse output within an input bundle/account tree before creating anything."""
    path = Path(value).absolute()
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        require(not current.is_symlink(), "Evidence output must not traverse symlinks")
    path = path.resolve()
    require(not path.exists(), "Use a new evidence output directory")
    for root in protected_roots:
        protected = Path(root).resolve()
        require(path != protected and protected not in path.parents,
                "Evidence output must be outside development/release bundles and account data")
    return path


def bundle_files(root):
    root = plain_path(root, directory=True)
    result = {}
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), f"Bundle symlink is not allowed: {path}")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = path.read_bytes()
        else:
            require(path.is_dir(), f"Special bundle entry is not allowed: {path}")
    require("manifest.json" in result and "main.splash" in result, "Not a script bundle")
    return result


def verify_bundle_pair(bundle, release):
    """Require byte-identical resources and manifest except publisher signature."""
    dev_files, release_files = bundle_files(bundle), bundle_files(release)
    require(set(dev_files) == set(release_files), "Development/release file inventories differ")
    dev = json.loads(dev_files["manifest.json"])
    published = json.loads(release_files["manifest.json"])
    require(dev.get("id") == APP_ID, "Unexpected application id")
    require(not dev.get("integrity", {}).get("signature"), "Developer import requires an unsigned copy")
    expected = copy.deepcopy(published)
    expected.get("integrity", {}).pop("signature", None)
    require(dev == expected, "Development/release manifests differ beyond signature")
    for name in dev_files:
        if name != "manifest.json":
            require(dev_files[name] == release_files[name], f"Development resource differs: {name}")
    return {
        "id": dev["id"], "name": dev["name"], "version": dev["version"],
        "bundle_blake3": dev["integrity"]["bundle_blake3"],
        "source_sha256": sha256(dev_files["main.splash"]),
        "file_sha256": {name: sha256(data) for name, data in dev_files.items()},
        "capabilities": dev["capabilities"],
    }


def verify_account(data_dir, account):
    require(bool(re.fullmatch(r"@[^\s:]+:[^\s]+", account)), "An explicit Matrix account id is required")
    root = plain_path(data_dir, directory=True)
    marker = plain_path(root / "latest_user_id.txt")
    require(marker.read_text(encoding="utf-8").strip() == account,
            "Rinx data-directory account does not match --account")
    return root


def review_matches(notice, identity, room):
    lines = notice.splitlines()
    expected_header = f"{identity['name']} {identity['version']} · Local unsigned bundle"
    require(bool(lines) and lines[0] == expected_header, "Review does not identify the expected unsigned app")
    rooms = [line for line in lines if line.startswith("Allowed room: ")]
    require(rooms == ["Allowed room: " + (room or "None")], "Review room differs from requested room")
    services = [line[len("Services: "):] for line in lines if line.startswith("Services: ")]
    require(len(services) == 1, "Review must contain one service list")
    actual = [value.strip() for value in services[0].split(",") if value.strip()]
    require(sorted(actual) == sorted(identity["capabilities"]), "Review services differ from manifest")


def turn_state(status):
    # The native bridge exposes widget text, not cue_busy/revision. Match the
    # current production contract explicitly and fail on unknown/changed text.
    # An automatic retry is PENDING even though its text contains “未通过”.
    if status == SUCCESS:
        return "success"
    if "正在自动重试一次" in status or status.startswith(("助手正在准备三种说法", "这一幕正在展开")):
        return "pending"
    if status.startswith(("这次试映没有完成", "助手暂时不可用", "助手候选未采用：",
                          "输入或来源已变化，旧回复未应用", "请求超过宿主32 KiB限制",
                          "已停止等待", "先写一句", "先把台词缩到", "补充条件请缩到",
                          "请载入并至少勾选一条参考消息", "先看一下勾选的消息",
                          "授权已过期", "账号已经切换", "Rinx 没有登录", "没有读到群聊",
                          "当前宿主不提供", "宿主没有授权")):
        return "failure"
    if "等待超过 90 秒" in status:
        return "failure"
    return "unknown"


def room_state(status):
    if status.startswith("原消息已载入"):
        return "success"
    if status.startswith("正在读取群聊"):
        return "pending"
    if status.startswith(("没有读到群聊", "这次打开没有选房间", "宿主没有授权读取这个房间",
                          "当前宿主不提供群聊服务", "消息读取失败", "这个群聊暂时没有", "已停止等待",
                          "宿主未提供稳定房间ID", "宿主消息格式或大小异常", "当前有未保存编辑",
                          "读取期间草稿改变，未切换房间", "授权已过期", "账号已经切换", "Rinx 没有登录")) or "等待超过 90 秒" in status:
        return "failure"
    return "unknown"


def decode_store(raw):
    """Validate the production array schema without inventing a legacy fallback.

    Preserve the actual bytes separately for no-write/reopen evidence; Python's
    float serializer is not the Splash canonical JSON serializer.
    """
    if raw is None:
        return [1, 0, []]
    require(isinstance(raw, bytes) and len(raw) <= 524288, "Invalid room store size")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError):
        raise RuntimeError("Room store is not valid UTF-8 JSON") from None

    def integer(number):
        return (type(number) in (int, float) and 0 <= number <= 1000000000
                and math.isfinite(number) and number % 1 == 0)

    require(isinstance(value, list) and len(value) == 3 and type(value[0]) is int and value[0] == 1,
            "Unknown room store schema")
    require(integer(value[1]) and isinstance(value[2], list) and len(value[2]) <= 10,
            "Invalid room store revision or room list")
    seen = set()
    for room in value[2]:
        require(isinstance(room, list) and len(room) == 4 and isinstance(room[0], str)
                and 0 < len(room[0].encode("utf-8")) <= 512, "Invalid room store record")
        require(room[0] not in seen, "Duplicate room store record")
        seen.add(room[0])
        for slot in room[1:]:
            if slot is None:
                continue
            require(isinstance(slot, list) and len(slot) == 9, "Invalid room draft slot")
            require(all(isinstance(slot[i], str) for i in (0, 2, 3, 4, 5, 6, 7)),
                    "Invalid room draft text or provenance")
            require(all(len(slot[i].encode("utf-8")) <= bound for i, bound in
                        ((0, 8000), (3, 8000), (4, 1024), (5, 256), (6, 1024), (7, 1000))),
                    "Room draft exceeds production bounds")
            require(integer(slot[1]) and slot[2] in ("manual", "model", "demo", "legacy"),
                    "Invalid room draft revision or origin")
            require(type(slot[8]) in (int, float) and 0 <= slot[8] <= 100000000000000
                    and math.isfinite(slot[8]), "Invalid room draft timestamp")
    return value


def validate_permissions(args):
    require(args.allow_import, "--allow-import is required: this closes the current mini app and grants a fresh instance")
    if args.mode in ("routes", "playback"):
        require(args.allow_real_turn, "--allow-real-turn is required for a real room/model run")
        require(bool(args.room), "A nonempty --room is required for a real turn")
        require(bool(args.trial and args.trial.strip()) and len(args.trial.strip()) <= 240,
                "Supply a nonblank --trial of at most 240 characters")
    if args.mode in ("draft", "reopen"):
        require(args.allow_draft_write, "--allow-draft-write is required: selected saved test drafts will be overwritten")
        require(args.allow_room_read, "--allow-room-read is required to activate and restore the selected room drafts")
        require(bool(args.room), "A nonempty --room is required for room draft checks")
    require(bool(re.fullmatch(r":\d+(?:\.\d+)?", args.display)), "--display must be an explicit local X11 display, e.g. :99")
    require(1 <= args.port <= 65535, "Invalid bridge port")
    require(math.isfinite(args.size_tolerance) and args.size_tolerance >= 0, "Size tolerance must be finite and nonnegative")
    require(math.isfinite(args.wait_seconds) and 0 < args.wait_seconds <= 120, "Wait budget must be in (0, 120] seconds; it does not reset the app deadline")
    require(bool(re.fullmatch(r"\d+x\d+", args.size)), "--size must be WIDTHxHEIGHT")
    width, height = map(int, args.size.split("x"))
    require(width > 0 and height > 32, "Invalid requested window dimensions")
    if args.room:
        require(bool(re.fullmatch(r"![^\s]+", args.room)), "Invalid explicit room id")


class Recorder:
    def __init__(self, bridge, out, *, bundle, release, account, data_dir,
                 identity, display, xauthority=None, wait_seconds=95):
        self.b = bridge
        self.out = output_path(out, bundle, release, data_dir)
        self.out.mkdir(parents=True, exist_ok=False)
        self.actions = []
        self.bundle = Path(bundle)
        self.release = Path(release)
        self.account = account
        self.data_dir = Path(data_dir)
        self.identity = identity
        self.display = display
        self.xauthority = xauthority
        self.wait_seconds = wait_seconds
        self.loaded = False
        self.room_loaded = False
        self.real_turn_completed = False
        self.run_nonce = uuid.uuid4().hex

    def record(self, kind, **data):
        self.actions.append({"at": time.time(), "kind": kind, **data})
        (self.out / "actions.json").write_text(json.dumps(self.actions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def check_context(self):
        verify_account(self.data_dir, self.account)
        require(verify_bundle_pair(self.bundle, self.release) == self.identity,
                "Bundle changed since preflight; start a new evidence run")

    def status(self):
        rows = [r for r in self.b.snap("cue_status") if r.get("i") == "cue_status"]
        require(len(rows) == 1, "Expected exactly one OnCue status label")
        return rows[0].get("t", "")

    def click(self, text=None, *, id=None, shell=False):
        self.check_context()
        result = self.b.click(text=text, id=id) if shell else self.b.click_app(text=text, id=id)
        self.record("click", text=text, id=id, shell=shell, target=result["target"]["r"])
        return result

    def click_visible(self, text):
        return self.click(text)

    def click_control(self, text):
        """Playback input with no scroll walk that could consume the whole route."""
        self.check_context()
        result = self.b.click_app_visible(text=text, id="cue_play_button")
        self.record("click", text=text, id="cue_play_button", shell=False,
                    target=result["target"]["r"], current_viewport_only=True)
        return result

    def editor_text(self):
        self.b.reveal(id="cue_draft")
        rows = [r for r in self.b.snap() if r.get("i") == "cue_draft" and r.get("ty") == "TextInput"]
        require(len(rows) == 1 and isinstance(rows[0].get("val"), str), "Expected exactly one draft editor")
        return rows[0]["val"]

    def fill(self, id, text, *, shell=False):
        self.check_context()
        if not shell:
            self.b.reveal(id=id)
        self.b.fill(id, text)
        rows = [r for r in self.b.snap() if r.get("i") == id and r.get("ty") == "TextInput"]
        require(len(rows) == 1 and rows[0].get("val") == text, f"Input round-trip failed: {id}")
        self.record("fill", id=id, characters=len(text), text_sha256=sha256(text.encode("utf-8")))

    def capture(self, name):
        require(bool(name) and Path(name).name == name, "Invalid capture name")
        x, y, w, h = module(self.b)
        window_status = self.b.get('s').get('w', [])
        require(len(window_status) == 1, "Screenshot requires exactly one native window")
        window = window_status[0]
        require(window.get('dpi') == 1, "X11 screenshot currently supports DPI=1 only; do not guess scaled coordinates")
        bound = getattr(self.b, 'window', None)
        require(bound is None or bound == window.get('i'), "Screenshot window differs from input window")
        origin = window.get('pos', [])
        size = window.get('sz', [])
        require(len(origin) == 2 and len(size) == 2 and all(isinstance(v, (int, float)) and math.isfinite(v) for v in origin + size),
                "Invalid top-level window geometry")
        local_y = y - 32
        require(x >= 0 and local_y >= 0 and x + w <= size[0] and local_y + h + 32 <= size[1],
                "Rinx frame is outside its native window")
        x, y, w, h = map(round, (origin[0] + x, origin[1] + local_y, w, h + 32))
        require(x >= 0 and y >= 0 and w > 0 and h > 0, "Window is outside capture coordinates")
        path = self.out / (name + ".png")
        require(not path.exists(), "Capture already exists")
        env = os.environ.copy()
        env["DISPLAY"] = self.display
        if self.xauthority:
            env["XAUTHORITY"] = str(self.xauthority)
        else:
            env.pop("XAUTHORITY", None)
        subprocess.run(["ffmpeg", "-nostdin", "-n", "-v", "error", "-f", "x11grab",
                        "-video_size", f"{w}x{h}", "-i", f"{self.display}+{x},{y}",
                        "-frames:v", "1", str(path)], env=env, check=True, timeout=30)
        self.record("capture", path=path.name, frame=[x, y, w, h], display=self.display,
                    scope="caller-selected display; not bridge/display process attestation")

    def wait_status(self, classify, subject):
        deadline = time.monotonic() + self.wait_seconds
        last = None
        while True:
            self.check_context()
            status = self.status()
            state = classify(status)
            if status != last:
                self.record("status", subject=subject, state=state, text=status)
                last = status
            if state == "success":
                return status
            require(state == "pending", f"{subject} ended as {state}: {status}")
            require(time.monotonic() < deadline, f"Observer budget expired for {subject}; no new request was sent")
            time.sleep(0.25)

    def import_bundle(self):
        """Always Review/Run the same preflighted bytes; never trust app_scroll alone."""
        self.check_context()
        self.loaded = False
        self.room_loaded = False
        self.real_turn_completed = False
        for _ in range(16):
            rows = self.b.snap()
            if any(r.get("i") == "path" and r.get("ty") == "TextInput" for r in rows):
                break
            if any(r.get("i") == "app_scroll" for r in rows):
                self.click("Back", id="close", shell=True)
            elif any(r.get("i") == "import_app" for r in rows):
                self.click(id="import_app", shell=True)
            elif any(r.get("i") == "discover_mini_apps" for r in rows):
                self.click(id="discover_mini_apps", shell=True)
            elif any(r.get("i") == "discover_tab" for r in rows):
                self.click(id="discover_tab", shell=True)
            else:
                raise RuntimeError("Open the Rinx Mini apps library before running; refusing to guess navigation")
            time.sleep(0.3)
        else:
            raise RuntimeError("Import form did not open")
        self.fill("path", str(self.bundle), shell=True)
        self.fill("room", self._room, shell=True)  # Empty explicitly revokes an old form binding.
        self.click("Review bundle", id="review", shell=True)
        notices = [r.get("t", "") for r in self.b.snap("notice") if r.get("i") == "notice"]
        require(len(notices) == 1, "Expected one native review notice")
        review_matches(notices[0], self.identity, self._room)
        self.record("review", notice=notices[0], bundle=str(self.bundle), identity=self.identity,
                    account_marker=self.account, account_source="latest_user_id.txt; operator must match bridge/data-dir")
        self.check_context()
        self.click("Run", id="run", shell=True)
        deadline = time.monotonic() + 15
        while not any(r.get("i") == "cue_status" for r in self.b.snap()):
            require(time.monotonic() < deadline, "Expected app did not become visible after Run")
            time.sleep(0.25)
        self.check_context()
        self.loaded = True
        self.record("loaded", bundle=str(self.bundle), source_sha256=self.identity["source_sha256"])

    def ensure_loaded(self, *, room):
        self._room = room
        self.import_bundle()

    def load_room(self, *, allow_room_read=False):
        require(allow_room_read, "Real room reads are disabled")
        require(self.loaded and bool(self._room), "Fresh import with an explicit room required")
        self.room_loaded = False
        self.click("载入群聊")
        self.wait_status(room_state, "room read")
        self.room_loaded = True

    def ensure_turn(self, *, allow_real_turn=False, trial=None):
        require(allow_real_turn, "Real room/model operations are disabled")
        require(self.loaded and bool(self._room), "Fresh import with an explicit room required")
        require(bool(trial and trial.strip()) and len(trial.strip()) <= 240, "Explicit trial required")
        before = self.storage_snapshot()
        self.load_room(allow_room_read=allow_real_turn)
        self.fill("cue_trial", trial)
        self.click(CONSENT)
        require(self.status() == CONSENT_GRANTED, "Current source-range model consent was not confirmed")
        self.record("real_turn_start", rehearsal_clicks=1, maximum_app_turns=2,
                    note="Production may retry once within its original 90-second budget; no outer retry or R1 request")
        self.click("试映下一幕")
        self.wait_status(turn_state, "real rehearsal")
        self.overview()
        self.assert_no_save(before, "room load, consent and generation")
        self.real_turn_completed = True
        self.record("real_turn_complete", rehearsal_clicks=1)

    def overview(self):
        """Read all three suggestions before playing a single dialogue line."""
        # Native snapshots omit offscreen descendants. Walk the actual viewport;
        # three cards need not fit on one screen to be a complete overview.
        self.b.app_scroll(-5000)
        suggestions, sources = {}, {}
        for step in range(41):
            rows = self.b.snap()
            boxes = [r["r"] for r in rows if r.get("i") == "cue_overview"]
            require(len(boxes) <= 1, "Suggestion overview is ambiguous")
            if boxes:
                x, y, w, h = boxes[0]
                labels = sorted([r for r in rows if r.get("ty") == "Label"
                                 and r["r"][0] >= x and r["r"][1] >= y
                                 and r["r"][0] + r["r"][2] <= x + w + 1
                                 and r["r"][1] + r["r"][3] <= y + h + 1], key=lambda r: r["r"][1])
                for _, title in ROUTES:
                    matches = [(i, r.get("t", "")[len(title) + 1:]) for i, r in enumerate(labels)
                               if r.get("t", "").startswith(title + "：")]
                    require(len(matches) <= 1, "Duplicate overview suggestion")
                    if not matches:
                        continue
                    i, text = matches[0]
                    require(bool(text.strip()) and (title not in suggestions or suggestions[title] == text),
                            "Empty or changing overview suggestion")
                    suggestions[title] = text
                    if i + 1 < len(labels):
                        excerpt = labels[i + 1].get("t", "")
                        if excerpt.startswith("相关原文片段：\n"):
                            require(re.search(r"\n#[1-9]\d* ", excerpt) is not None, "Overview source excerpt is empty")
                            require(title not in sources or sources[title] == excerpt, "Overview source changed while reading")
                            sources[title] = excerpt
            if len(suggestions) == 3 and len(sources) == 3:
                break
            if step < 40:
                self.b.app_scroll(100)
        require(len(suggestions) == 3 and len(sources) == 3, "Missing overview suggestion or source excerpt after scrolling")
        require(len(set(suggestions.values())) == 3, "Three overview suggestions are not distinct")
        self.record("suggestion_overview", suggestions=suggestions,
                    source_excerpts=[sources[title] for _, title in ROUTES],
                    scope="native widget text across scroll positions before playback; screenshots recorded separately")
        return suggestions

    def result_index(self):
        rows = [r for r in self.b.snap() if r.get("ty") == "Label" and
                re.fullmatch(r"第 \d+ 页 / 共 \d+ 页", r.get("t", ""))]
        require(len(rows) == 1, "Result page counter is absent or ambiguous")
        current, total = map(int, re.findall(r"\d+", rows[0]["t"]))
        require(1 <= current <= total, "Invalid result page counter")
        return current, total

    def reader(self):
        rows = self.b.snap()
        boxes = [r["r"] for r in rows if r.get("i") == "readout"]
        require(len(boxes) == 1, "Reader is absent or ambiguous")
        x, y, w, h = boxes[0]
        labels = [r for r in rows if r.get("ty") == "Label" and r["r"][0] >= x and r["r"][1] >= y
                  and r["r"][0] + r["r"][2] <= x + w + 1 and r["r"][1] + r["r"][3] <= y + h + 1]
        require(bool(labels), "Reader has no visible text widgets")
        return {"rect": boxes[0], "text": "\n".join(r.get("t", "") for r in labels)}

    def collect_pages(self, name, all_screens=True, *, capture=True):
        self.b.reveal(id="readout")
        current, total = self.result_index()
        for _ in range(current - 1):
            self.click_visible("上一页")
        result = []
        for i in range(total):
            self.b.reveal(id="readout")
            require(self.result_index() == (i + 1, total), "Page did not advance or total changed")
            page = self.reader()
            result.append({"page": i + 1, **page})
            if capture and (all_screens or i in (0, total // 2, total - 1)):
                self.capture(f"{name}-{i + 1:02}")
            if i + 1 < total:
                self.click_visible("下一页")
        self.record("reader", name=name, pages=result)
        return "".join(page["text"] for page in result)

    def playback_observation(self):
        self.b.reveal(id="readout")
        return {"status": self.status(), "page": self.result_index(), "reader_text": self.reader()["text"]}

    def paused_progress(self):
        """Read the production pause counter; status-only playback changes do not count."""
        match = re.search(r"已暂停在 (\d+) / (\d+) 句", self.status())
        require(match is not None, "Pause did not expose a valid line counter")
        count, total = map(int, match.groups())
        require(0 <= count <= total and total > 0, "Invalid playback line counter")
        return count, total

    def observe_timer_progress(self, route, prior_count, expected_total):
        require(prior_count + 2 <= expected_total, "Need at least two remaining lines to distinguish play from timer")
        self.b.reveal(id="cue_play_button")
        self.click_control("播放")
        time.sleep(1.6)
        finished = self.status().startswith("这条假设路线已逐句播完。")
        if not finished:
            self.click_control("暂停")
            count, total = self.paused_progress()
            require(count >= prior_count + 2, "Only synchronous playback advanced; timed progress was not observed")
        else:
            # The total was measured before this play. Completion must also show
            # the suggestion, which production only appends after every line.
            count = total = expected_total
            complete_text = self.collect_pages("timer-" + route, capture=False)
            require("建议台词：" in complete_text, "Finished status without complete-route suggestion")
        require(total == expected_total, "Playback route total changed")
        observation = self.playback_observation()
        self.record("timed_progress", route=route, lines=count, total=total, observation=observation)
        return count

    def restart_progress(self):
        self.click("重播")
        match = re.match(r"已回到 0 / (\d+) 句；", self.status())
        require(match is not None and int(match[1]) >= 2, "Replay did not establish zero progress and at least two lines")
        return int(match[1])

    def playback(self):
        require(self.real_turn_completed, "Playback requires this run's successful real turn")
        stored = self.storage_snapshot()
        self.click("A 顺着说")
        self.restart_progress()
        self.click("下一句")
        require(re.match(r"已展开 1 / \d+ 句；", self.status()) is not None, "First-line step was not observed")
        self.b.reveal(id="cue_play_button")
        self.click_control("播放")
        time.sleep(0.5)
        self.click_control("暂停")
        self.paused_progress()  # A missed/late pause fails, never becomes a skipped pass.
        before = self.playback_observation()
        require("暂停" in before["status"], "Pause was not observed")
        time.sleep(3.1)
        require(self.playback_observation() == before, "Paused reader changed")
        self.record("pause_stable", seconds=3.1, observation=before)
        # Native scrolling and the prior pause can consume variable time. Establish
        # an independent deterministic zero-line precondition for each timer check.
        total = self.restart_progress()
        self.observe_timer_progress("A", 0, total)
        self.click("B 换问法")
        total_b = self.restart_progress()
        before_b = self.playback_observation()
        time.sleep(1.8)
        require(self.playback_observation() == before_b, "New paused route changed after switching")
        self.record("route_switch_stable", seconds=1.8,
                    scope="visible status, current reader text and page; VM suite tests epoch internals")
        self.observe_timer_progress("B", 0, total_b)
        self.restart_progress()
        self.assert_no_save(stored, "playback and route switch")

    def read_routes(self):
        require(self.real_turn_completed, "Routes require this run's successful real turn")
        stored = self.storage_snapshot()
        suggestions = self.overview()
        result = {}
        for label, title in ROUTES:
            self.click(label)
            for _ in range(20):
                self.click("下一句")
                if "全部" in self.status():
                    break
            else:
                raise RuntimeError("Dialogue did not finish within observation bound")
            result[label] = self.collect_pages(label, False)
            require(result[label].endswith("\n建议台词：" + suggestions[title]),
                    "Complete dialogue suggestion differs from overview")
            self.click("用这句")  # Unique selected-route button, not the three identical overview labels.
            require(self.status() == "已放进草稿框，可以继续修改；尚未保存或发送。",
                    "Suggestion selection did not confirm editor-only use")
            require(self.editor_text() == suggestions[title], "Selected suggestion differs from editor text")
            self.assert_no_save(stored, "select suggestion " + label)
        require(len(set(result.values())) == 3, "Three route texts are not distinct")
        self.click("相关原文")
        result["相关原文"] = self.collect_pages("相关原文", True)
        self.assert_no_save(stored, "complete routes and source reading")
        return result

    def saved_bytes(self, filename=STORE_FILE):
        require(filename in (STORE_FILE, *LEGACY_FILES), "Unexpected draft path")
        self.check_context()
        path = self.data_dir / "miniapps" / self.account.encode("utf-8").hex() / APP_ID / filename
        path = plain_path(path, missing_ok=True)
        return path.read_bytes() if path.exists() else None

    def storage_snapshot(self):
        # Read only the app-owned draft files, never credentials or unrelated data.
        # None is distinct from an existing zero-byte file for no-save checks.
        return {name: self.saved_bytes(name) for name in (STORE_FILE, *LEGACY_FILES)}

    def assert_no_save(self, before, subject):
        after = self.storage_snapshot()
        require(after == before, f"Draft storage changed without an explicit save: {subject}")
        self.record("no_save", subject=subject, exact=True,
                    files={name: {"exists": data is not None, "sha256": sha256(data) if data is not None else None}
                           for name, data in after.items()})

    def room_slot(self, store, label):
        require(label in SLOT_INDEX, "Unknown draft slot")
        require(self.room_loaded and bool(self._room), "Load the selected room before checking room drafts")
        rooms = [room for room in store[2] if room[0] == self._room]
        require(len(rooms) <= 1, "Ambiguous selected-room draft")
        return rooms[0][SLOT_INDEX[label]] if rooms else None

    def fresh_draft(self, label, text):
        # A per-run marker prevents a no-op save from passing on a prior fixture.
        text += "\n[验收标记 " + self.run_nonce + "]"
        slot = self.room_slot(decode_store(self.saved_bytes()), label)
        require(slot is None or slot[0] != text, "Fixture already exists; use a fresh evidence run")
        return text

    def save_readback(self, label, text, before):
        require(self.status() == SAVE_SUCCESS, "This run did not confirm draft save")
        after = self.storage_snapshot()
        require(after[STORE_FILE] is not None and after[STORE_FILE] != before[STORE_FILE],
                "Canonical room store did not change after save")
        for name in LEGACY_FILES:
            require(after[name] == before[name], "Room save changed a legacy draft file")
        old, new = decode_store(before[STORE_FILE]), decode_store(after[STORE_FILE])
        slot = self.room_slot(new, label)
        require(slot is not None and slot[0].encode("utf-8") == text.encode("utf-8"), "Saved UTF-8 slot bytes differ")
        require(slot[2] == "manual", "Synthetic edited draft lost manual provenance")
        expected = copy.deepcopy(old)
        rooms = [room for room in expected[2] if room[0] == self._room]
        if not rooms:
            rooms = [[self._room, None, None, None]]
            expected[2].append(rooms[0])
        rooms[0][SLOT_INDEX[label]] = slot
        expected[1] += 1
        require(new == expected, "Save changed another room/slot or did not advance the disk revision once")
        self.record("independent_readback", slot=label, exact=True, room_sha256=sha256(self._room.encode("utf-8")),
                    disk_revision=new[1], text_sha256=sha256(text.encode("utf-8")), store_sha256=sha256(after[STORE_FILE]))
        return after

    def draft(self, label, text):
        require(label in ("A", "B"), "Unknown draft slot")
        text = self.fresh_draft(label, text)
        before = self.storage_snapshot()
        self.fill("cue_draft", text)
        self.assert_no_save(before, "editing " + label)
        self.click("存 " + label)
        saved = self.save_readback(label, text, before)
        self.click("显示 " + label)
        require(self.collect_pages("draft-" + label, False) == text, "Rendered draft differs")
        self.fill("cue_draft", "")
        self.click("取 " + label)
        require(self.editor_text() == text, "Restored editor differs")
        self.assert_no_save(saved, "display and restore " + label)
        self.record("restore", slot=label, exact=True)

    def reopen_check(self, text, *, allow_room_read=False):
        require(allow_room_read, "Real room reads are disabled")
        text = self.fresh_draft("draft", text)
        before = self.storage_snapshot()
        self.fill("cue_draft", text)
        self.assert_no_save(before, "editing main draft")
        self.click("保留这句")
        saved = self.save_readback("draft", text, before)
        self.click("Back", id="close", shell=True)
        self.import_bundle()  # Same bundle, account, room and byte checks as initial import.
        require(self.editor_text() != text, "Room draft appeared before loading its room")
        self.assert_no_save(saved, "close and reimport before room load")
        self.load_room(allow_room_read=allow_room_read)
        require(self.editor_text() == text, "Room load did not restore the exact saved draft")
        self.assert_no_save(saved, "reopen and room draft restore")
        self.record("reopen_restored", exact=True, source_sha256=self.identity["source_sha256"],
                    scope="mini-app Back/reimport then explicit room load, not boot legacy restore or host process restart")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mode", choices=("routes", "playback", "draft", "reopen"), required=True)
    parser.add_argument("--bundle", type=Path, required=True, help="Unsigned copy matching --release-bundle")
    parser.add_argument("--release-bundle", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--hub", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True, help="Data directory belonging to the selected Rinx bridge")
    parser.add_argument("--account", required=True)
    parser.add_argument("--room", required=True, help="Explicit room id; all acceptance modes require a selected room")
    parser.add_argument("--host-binary", type=Path, required=True, help="Operator-selected host binary to fingerprint (not process attestation)")
    parser.add_argument("--display", required=True)
    parser.add_argument("--xauthority", type=Path)
    parser.add_argument("--size", default="990x613")
    parser.add_argument("--size-tolerance", type=float, default=0)
    parser.add_argument("--wait-seconds", type=float, default=95)
    parser.add_argument("--trial")
    parser.add_argument("--allow-import", action="store_true", help="Permit closing the current mini app and fresh Review/Run")
    parser.add_argument("--allow-real-turn", action="store_true", help="Permit one real room read and rehearsal (up to two app model turns)")
    parser.add_argument("--allow-room-read", action="store_true", help="Permit room reads for draft/reopen (twice for reopen); never starts a model turn")
    parser.add_argument("--allow-draft-write", action="store_true", help="Permit overwriting selected-room test slots in rehearsals-v1.json (A/B or main draft for reopen)")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    recorder = None
    try:
        validate_permissions(args)  # Before files, subprocesses, bridge calls or output creation.
        bundle = plain_path(args.bundle, directory=True)
        release = plain_path(args.release_bundle, directory=True)
        data_dir = verify_account(args.data_dir, args.account)
        out = output_path(args.out, bundle, release, data_dir)
        identity = verify_bundle_pair(bundle, release)
        hub = plain_path(args.hub)
        host_binary = plain_path(args.host_binary)
        require(os.access(hub, os.X_OK), "Hub is not executable")
        if args.xauthority:
            plain_path(args.xauthority)  # Only check the path; never read its content.
        checked = subprocess.run([str(hub), "check", str(bundle), "--allow-unsigned"], check=True, capture_output=True, text=True, timeout=30)
        host_hash = sha256(host_binary.read_bytes())
        bridge = Bridge(args.port)
        recorder = Recorder(bridge, out, bundle=bundle, release=release, account=args.account,
                            data_dir=data_dir, identity=identity, display=args.display,
                            xauthority=args.xauthority, wait_seconds=args.wait_seconds)
        recorder.record("preflight", identity=identity, hub_check=checked.stdout,
                        supplied_host_binary=str(host_binary), supplied_host_sha256=host_hash,
                        bridge_port=args.port, display=args.display,
                        provenance_limit="Operator must bind bridge, binary, display and data directory to the same host; not independently attested")
        recorder.ensure_loaded(room=args.room)
        geometry = resize(bridge, *map(int, args.size.split("x")), tolerance=args.size_tolerance)
        require(geometry.get("embedded_app") is not None, "No embedded app geometry after import")
        recorder.record("geometry", **geometry)
        if args.mode in ("routes", "playback"):
            recorder.ensure_turn(allow_real_turn=args.allow_real_turn, trial=args.trial)
        else:
            stored = recorder.storage_snapshot()
            recorder.load_room(allow_room_read=args.allow_room_read)
            recorder.assert_no_save(stored, "initial room draft load")
        if args.mode == "routes":
            recorder.record("complete_routes", contents=recorder.read_routes())
        elif args.mode == "playback":
            recorder.playback()
            recorder.capture("playback")
        elif args.mode == "reopen":
            recorder.reopen_check("重开验证：重新导入并载入同一房间后恢复草稿。\n第二行保留。",
                                  allow_room_read=args.allow_room_read)
        else:
            recorder.draft("A", "  草稿首行：中午再确认，尚未发送。\n中段保留空格   和组合 é、家人👩‍👩‍👧‍👦、肤色👍🏽、旗帜🇨🇳。\n最后一行 END-A  ")
            recorder.draft("B", "版本 B\n换个问法：当天回来可以吗？\n保留另一份原文 END-B")
        recorder.check_context()
        recorder.record("complete", passed=True, actual_frame=geometry["rinx_frame"], requested_size=args.size)
        print(json.dumps({"passed": True, "mode": args.mode, "actual_frame": geometry["rinx_frame"],
                          "requested_size": args.size, "out": str(args.out)}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        if recorder:
            recorder.record("complete", passed=False, error=str(error))
        print(f"Acceptance failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
