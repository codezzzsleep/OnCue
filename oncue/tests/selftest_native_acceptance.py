#!/usr/bin/env python3
"""Offline tests of the native recorder; no real bridge, model, host or accounts.

Temporary bundle/account markers are synthetic. PASS here is not Rinx acceptance.
"""
from __future__ import annotations

import ast
import contextlib
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
import native_acceptance as native


class NativeAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="oncue-offline-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.release = self.root / "release"
        self.dev = self.root / "dev"
        self.release.mkdir()
        self.dev.mkdir()
        self.manifest = {"id": native.APP_ID, "name": "OnCue · 群聊试映室", "version": "0.4.7",
                         "capabilities": ["storage", "matrix.room_info", "matrix.read_messages", "octos.session.open", "octos.turn.start", "octos.turn.interrupt"],
                         "integrity": {"bundle_blake3": "synthetic-digest", "signature": {"key_id": "synthetic", "value": "not-a-key"}}}
        for folder in (self.release, self.dev):
            (folder / "main.splash").write_text("synthetic fixture; not executed\n", encoding="utf-8")
        (self.release / "manifest.json").write_text(json.dumps(self.manifest), encoding="utf-8")
        unsigned = copy.deepcopy(self.manifest)
        unsigned["integrity"].pop("signature")
        (self.dev / "manifest.json").write_text(json.dumps(unsigned), encoding="utf-8")
        self.account = "@offline-test:example.invalid"
        self.data_dir = self.root / "rinx"
        self.data_dir.mkdir()
        (self.data_dir / "latest_user_id.txt").write_text(self.account, encoding="utf-8")
        self.identity = native.verify_bundle_pair(self.dev, self.release)

    def recorder(self, bridge=None):
        return native.Recorder(bridge or Mock(), self.root / "evidence", bundle=self.dev,
                               release=self.release, account=self.account, data_dir=self.data_dir,
                               identity=self.identity, display=":123", wait_seconds=1)

    def arguments(self, *extra):
        return native.build_parser().parse_args([
            "--port", "8123", "--out", str(self.root / "out"), "--mode", "routes",
            "--bundle", str(self.dev), "--release-bundle", str(self.release), "--hub", str(self.root / "hub"),
            "--data-dir", str(self.data_dir), "--account", self.account,
            "--room", "!offline:example.invalid", "--host-binary", str(self.root / "host"),
            "--display", ":123", "--trial", "先确认条件？", *extra])

    def test_bundle_pair_accepts_only_removed_signature(self):
        self.assertEqual(self.identity["source_sha256"], native.sha256((self.dev / "main.splash").read_bytes()))
        (self.dev / "main.splash").write_text("stale source", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "resource differs"):
            native.verify_bundle_pair(self.dev, self.release)

    def test_rejects_signature_manifest_drift_and_extra_file(self):
        for change in ("signature", "version", "extra"):
            with self.subTest(change=change):
                dev = copy.deepcopy(self.manifest)
                dev["integrity"].pop("signature")
                if change == "signature":
                    dev["integrity"]["signature"] = {"value": "synthetic"}
                elif change == "version":
                    dev["version"] = "old-version"
                (self.dev / "manifest.json").write_text(json.dumps(dev), encoding="utf-8")
                if change == "extra":
                    (self.dev / "extra.txt").write_text("unexpected", encoding="utf-8")
                with self.assertRaises(RuntimeError):
                    native.verify_bundle_pair(self.dev, self.release)

    def test_rejects_symlink_resources_and_symlink_root(self):
        (self.dev / "linked.txt").symlink_to(self.release / "main.splash")
        with self.assertRaisesRegex(RuntimeError, "symlink"):
            native.verify_bundle_pair(self.dev, self.release)
        link = self.root / "linked-root"
        link.symlink_to(self.release, target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError, "Symlink"):
            native.bundle_files(link)

    def test_account_marker_must_match_and_no_path_traversal(self):
        self.assertEqual(native.verify_account(self.data_dir, self.account), self.data_dir)
        with self.assertRaisesRegex(RuntimeError, "does not match"):
            native.verify_account(self.data_dir, "@other:example.invalid")
        with self.assertRaises(RuntimeError):
            native.verify_account(self.data_dir, "../../secret")

    def test_review_checks_exact_room_app_and_services(self):
        notice = (f"{self.identity['name']} {self.identity['version']} · Local unsigned bundle\n"
                  f"Services: {', '.join(self.identity['capabilities'])}\nAllowed room: None\nRun grants services")
        native.review_matches(notice, self.identity, "")
        for changed in (notice.replace("None", "!other:example.invalid"),
                        notice.replace("0.4.7", "0.4.4"), notice.replace("storage, ", ""),
                        notice + "\nAllowed room: None"):
            with self.assertRaises(RuntimeError):
                native.review_matches(changed, self.identity, "")

    def test_retry_status_is_pending_not_terminal_failure(self):
        self.assertEqual(native.turn_state("助手的回答没通过检查，正在自动重试一次…"), "pending")
        self.assertEqual(native.turn_state("助手的回答没通过检查，已丢弃。请再试一次。"), "failure")
        self.assertEqual(native.turn_state("助手的回答不完整，请再试一次。"), "failure")
        self.assertEqual(native.turn_state("这次试映没有完成：service error"), "failure")
        self.assertEqual(native.turn_state("助手试映等待超过 90 秒，已结束等待。"), "failure")
        self.assertEqual(native.turn_state(native.SUCCESS + "；点 A、B、C 查看。"), "success")
        self.assertEqual(native.turn_state("unrecognized production contract"), "unknown")

    def test_room_empty_errors_and_pending_are_distinct(self):
        for text in ("这个群聊暂时没有可读取的文本消息。", "没有读到群聊：denied", "消息读取失败：offline",
                     "这次打开没有选房间。请关闭应用，导入时填上房间再打开。",
                     "宿主没有授权读取这个房间。", "当前宿主不提供群聊服务，请在 Rinx 里打开。"):
            self.assertEqual(native.room_state(text), "failure")
        self.assertEqual(native.room_state("正在读取群聊最近 12 条消息…"), "pending")
        self.assertEqual(native.room_state("原消息已载入，共 12 条。"), "success")

    def test_cli_permissions_fail_before_files_or_bridge(self):
        args = self.arguments()
        with self.assertRaisesRegex(RuntimeError, "allow-import"):
            native.validate_permissions(args)
        args.allow_import = True
        with self.assertRaisesRegex(RuntimeError, "allow-real-turn"):
            native.validate_permissions(args)
        args.allow_real_turn = True
        native.validate_permissions(args)
        args.mode = "reopen"
        with self.assertRaisesRegex(RuntimeError, "allow-draft-write"):
            native.validate_permissions(args)
        args.allow_draft_write = True
        native.validate_permissions(args)
        args.display = "remote.example:0"
        with self.assertRaises(RuntimeError):
            native.validate_permissions(args)

    def test_main_denied_without_network_subprocess_or_output(self):
        argv = ["--port", "8123", "--out", str(self.root / "out"), "--mode", "draft", "--bundle", "/absent",
                "--hub", "/absent", "--data-dir", "/absent", "--account", self.account, "--room", "",
                "--host-binary", "/absent", "--display", ":123"]
        with patch.object(native, "Bridge") as bridge, patch.object(native.subprocess, "run") as run, \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(native.main(argv), 1)
        bridge.assert_not_called()
        run.assert_not_called()
        self.assertFalse((self.root / "out").exists())

    def test_waits_through_automatic_retry_and_records_status(self):
        recorder = self.recorder()
        recorder.status = Mock(side_effect=["助手正在准备三种说法…",
                                           "助手的回答没通过检查，正在自动重试一次…", native.SUCCESS + "；假设"])
        with patch.object(native.time, "sleep"), patch.object(native.time, "monotonic", return_value=0):
            recorder.wait_status(native.turn_state, "test")
        self.assertEqual([event["state"] for event in recorder.actions], ["pending", "pending", "success"])

    def test_observer_timeout_never_starts_another_turn(self):
        recorder = self.recorder()
        recorder.status = Mock(return_value="助手正在准备三种说法…")
        with patch.object(native.time, "sleep"), patch.object(native.time, "monotonic", side_effect=[0, 2]):
            with self.assertRaisesRegex(RuntimeError, "Observer budget"):
                recorder.wait_status(native.turn_state, "test")
        recorder.b.click_app.assert_not_called()

    def test_real_turn_disabled_and_exactly_one_rehearsal_click(self):
        recorder = self.recorder()
        recorder.click, recorder.fill, recorder.wait_status = Mock(), Mock(), Mock()
        recorder.loaded, recorder._room = True, "!offline:example.invalid"
        with self.assertRaisesRegex(RuntimeError, "disabled"):
            recorder.ensure_turn(trial="待确认？")
        recorder.click.assert_not_called()
        recorder.ensure_turn(allow_real_turn=True, trial="待确认？")
        self.assertEqual([c.args[0] for c in recorder.click.call_args_list], ["载入群聊", "试映下一幕"])
        self.assertTrue(recorder.real_turn_completed)

    def test_fresh_import_does_not_trust_app_scroll(self):
        recorder = self.recorder()
        recorder.b.snap.return_value = [{"i": "app_scroll", "ty": "ScrollYView"}]
        recorder.click = Mock(side_effect=RuntimeError("sentinel: closed old instance"))
        with self.assertRaisesRegex(RuntimeError, "sentinel"):
            recorder.ensure_loaded(room="")
        recorder.click.assert_called_once_with("Back", id="close", shell=True)
        self.assertFalse(recorder.loaded)

    def test_reopen_uses_same_bundle_and_checks_bytes(self):
        recorder = self.recorder()
        recorder.fill, recorder.click = Mock(), Mock()
        recorder.fresh_draft = Mock(side_effect=lambda filename, text: text)
        recorder.status = Mock(return_value="草稿已保存。")
        recorder.saved_bytes = Mock(return_value="精确原文\n".encode("utf-8"))
        recorder.import_bundle = Mock()
        recorder.b.snap.return_value = [{"i": "cue_draft", "ty": "TextInput", "val": "精确原文\n"}]
        original = recorder.bundle
        recorder.reopen_check("精确原文\n")
        recorder.import_bundle.assert_called_once_with()
        self.assertEqual(recorder.bundle, original)
        self.assertEqual(recorder.saved_bytes.call_count, 2)

    def test_capture_uses_selected_display_and_no_inherited_xauthority(self):
        recorder = self.recorder()
        recorder.b.window = 2
        recorder.b.get.return_value = {"w": [{"i": 2, "dpi": 1, "pos": [200, 100], "sz": [1180, 760]}]}
        with patch.object(native, "module", return_value=[10, 52, 990, 581]), \
                patch.object(native.subprocess, "run") as run, patch.dict(native.os.environ, {"XAUTHORITY": "/not-this-instance"}):
            recorder.capture("synthetic")
        argv = run.call_args.args[0]
        self.assertIn(":123+210,120", argv)
        self.assertNotIn("XAUTHORITY", run.call_args.kwargs["env"])
        self.assertEqual(run.call_args.kwargs["env"]["DISPLAY"], ":123")
        self.assertIn("-n", argv)

    def test_context_drift_fails_before_click(self):
        recorder = self.recorder()
        (self.data_dir / "latest_user_id.txt").write_text("@other:example.invalid", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            recorder.click("存 A")
        recorder.b.click_app.assert_not_called()

    def test_no_bare_assert_or_hardcoded_development_bundle(self):
        source = (TOOLS / "native_acceptance.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        self.assertFalse(any(isinstance(node, ast.Assert) for node in ast.walk(tree)))
        self.assertNotIn("047-final-", source)
        self.assertNotIn("/srv/", source)

    def test_output_never_mutates_bundle_or_account_tree(self):
        for root in (self.dev, self.release, self.data_dir):
            with self.subTest(root=root), self.assertRaisesRegex(RuntimeError, "outside"):
                native.Recorder(Mock(), root / "new-output", bundle=self.dev, release=self.release,
                                account=self.account, data_dir=self.data_dir, identity=self.identity, display=":123")
            self.assertFalse((root / "new-output").exists())
        link = self.root / "evidence-link"
        link.symlink_to(self.release, target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError, "symlink"):
            native.output_path(link / "new-output", self.dev, self.release, self.data_dir)
        self.assertFalse((self.release / "new-output").exists())

    def test_output_preflight_rejects_before_hub_or_bridge(self):
        args = self.arguments("--allow-import", "--allow-real-turn")
        args.out = self.release / "new-output"
        with patch.object(native, "build_parser") as parser, patch.object(native, "Bridge") as bridge, \
                patch.object(native.subprocess, "run") as run, contextlib.redirect_stderr(io.StringIO()):
            parser.return_value.parse_args.return_value = args
            self.assertEqual(native.main([]), 1)
        run.assert_not_called()
        bridge.assert_not_called()
        self.assertFalse(args.out.exists())
        native.verify_bundle_pair(self.dev, self.release)

    def test_symlink_dotdot_is_checked_before_normalizing(self):
        link = self.root / "link"
        link.symlink_to(self.release, target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError, "Symlink"):
            native.plain_path(link / ".." / "release" / "manifest.json")
        with self.assertRaisesRegex(RuntimeError, "symlink"):
            native.output_path(link / ".." / "new-evidence", self.release)

    def test_nonfinite_cli_limits_rejected_before_operations(self):
        for value in (float("inf"), float("nan"), -1):
            args = self.arguments("--allow-import", "--allow-real-turn")
            args.size_tolerance = value
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                native.validate_permissions(args)

    def test_timer_check_rejects_only_synchronous_line_or_status_change(self):
        recorder = self.recorder()
        recorder.click = Mock()
        recorder.status = Mock(side_effect=["正在逐句播放", "已暂停在 1 / 4 句"])
        recorder.playback_observation = Mock()
        with patch.object(native.time, "sleep"), self.assertRaisesRegex(RuntimeError, "synchronous"):
            recorder.observe_timer_progress("B", 0, 4)
        recorder.playback_observation.assert_not_called()
        self.assertFalse(any(e["kind"] == "timed_progress" for e in recorder.actions))

    def test_timer_check_accepts_two_advances_with_numeric_counter(self):
        recorder = self.recorder()
        recorder.click = Mock()
        recorder.status = Mock(side_effect=["正在逐句播放", "已暂停在 2 / 4 句"])
        recorder.playback_observation = Mock(return_value={"reader_text": "B1\\nB2"})
        with patch.object(native.time, "sleep"):
            self.assertEqual(recorder.observe_timer_progress("B", 0, 4), 2)

    def test_timer_completion_supports_normal_four_line_route(self):
        recorder = self.recorder()
        recorder.click = Mock()
        recorder.status = Mock(return_value="这条假设路线已逐句播完。")
        recorder.collect_pages = Mock(return_value="末句\\n建议台词：很长的建议，前缀不在最后页")
        recorder.playback_observation = Mock(return_value={"reader_text": "complete"})
        with patch.object(native.time, "sleep"):
            self.assertEqual(recorder.observe_timer_progress("A", 2, 4), 4)
        recorder.collect_pages.assert_called_once_with("timer-A", capture=False)
        recorder.collect_pages.return_value = "first line only"
        with patch.object(native.time, "sleep"), self.assertRaisesRegex(RuntimeError, "without complete"):
            recorder.observe_timer_progress("A", 2, 4)

    def test_reopen_rejects_failed_save_even_when_old_bytes_match(self):
        recorder = self.recorder()
        recorder.fill, recorder.click = Mock(), Mock()
        recorder.fresh_draft = Mock(side_effect=lambda filename, text: text)
        recorder.status = Mock(return_value="草稿 没有保存完成；编辑框内容仍在。")
        recorder.saved_bytes = Mock(return_value=b"old fixture")
        recorder.import_bundle = Mock()
        with self.assertRaisesRegex(RuntimeError, "did not confirm"):
            recorder.reopen_check("old fixture")
        recorder.import_bundle.assert_not_called()

    def test_drafts_include_unique_run_nonce_and_reject_existing_fixture(self):
        recorder = self.recorder()
        text = recorder.fresh_draft("draft.txt", "fixture")
        self.assertIn(recorder.run_nonce, text)
        path = self.data_dir / "miniapps" / self.account.encode().hex() / native.APP_ID / "draft.txt"
        path.parent.mkdir(parents=True)
        path.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            recorder.fresh_draft("draft.txt", "fixture")

    def test_capture_rejects_scaled_multiple_or_outside_window(self):
        recorder = self.recorder()
        recorder.b.window = 2
        base = {"i": 2, "dpi": 1, "pos": [200, 100], "sz": [1180, 760]}
        for windows in ([{**base, "dpi": 2}], [base, base], [{**base, "i": 3}], [{**base, "sz": [100, 100]}]):
            recorder.b.get.return_value = {"w": windows}
            with patch.object(native, "module", return_value=[10, 52, 990, 581]), \
                    patch.object(native.subprocess, "run") as run, self.assertRaises(RuntimeError):
                recorder.capture("not-created")
            run.assert_not_called()

    def test_require_stays_active_in_optimized_python(self):
        program = "import sys;sys.path.insert(0,sys.argv[1]);from native_acceptance import require;require(False,'guard-active')"
        result = subprocess.run([sys.executable, "-B", "-O", "-c", program, str(TOOLS)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("guard-active", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
