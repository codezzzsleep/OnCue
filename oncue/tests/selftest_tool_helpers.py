#!/usr/bin/env python3
"""Offline helper unit tests only: no native host, bridge, model, hub or network.

HTTP and subprocess are mocked; all bundle writes use TemporaryDirectory. Passing
these tests is not evidence of native interaction, a real hub check, or model use.
"""
import sys
sys.dont_write_bytecode = True

import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, call, patch
import urllib.error
import urllib.parse
import urllib.request

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
sys.path.insert(0, str(TOOLS))
# Protect even the first imports against accidental future import-time effects.
with patch('socket.socket.connect', side_effect=AssertionError('network forbidden')), \
        patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('HTTP forbidden')), \
        patch('subprocess.run', side_effect=AssertionError('subprocess forbidden')):
    import native_bridge
    import rinx_session
    import prepare_dev_bundle


def widget(ty='Button', ident='go', text='Go', rect=(20, 30, 60, 24), visible=1):
    return {'ty': ty, 'i': ident, 't': text, 'r': list(rect), 'v': visible}


def viewport(rect=(10, 20, 200, 200)):
    return widget('ScrollYView', 'app_scroll', '', rect)


class OfflineTest(unittest.TestCase):
    def setUp(self):
        for target in ('socket.socket.connect', 'socket.create_connection',
                       'urllib.request.OpenerDirector.open', 'urllib.request.urlopen'):
            blocker = patch(target, side_effect=AssertionError('real network/HTTP forbidden'))
            blocker.start()
            self.addCleanup(blocker.stop)
        blocker = patch('subprocess.run', side_effect=AssertionError('real subprocess forbidden'))
        self.run = blocker.start()
        self.addCleanup(blocker.stop)
        blocker = patch('time.sleep')
        blocker.start()
        self.addCleanup(blocker.stop)

    def bridge(self, rows):
        b = native_bridge.Bridge(12345)
        b.snap = Mock(return_value=rows)
        b.get = Mock(return_value={'ok': True})
        return b


class BridgeTests(OfflineTest):
    def test_snap_filters_both_dimensions_hidden_splash_and_malformed(self):
        b = native_bridge.Bridge(12345)
        good = widget()
        rows = [good, widget(visible=0), widget(rect=(0, 0, 0, 20)),
                widget(rect=(0, 0, 20, 0)), widget(rect=(0, 0, 20, -1)),
                widget(rect=(float('nan'), 0, 20, 20)), widget(rect=(0, 0, True, 20)),
                widget('Splash'), {'ty': 'Button', 'r': [0]}]
        b.get = Mock(return_value={'s': rows})
        self.assertEqual(b.snap('Go'), [good])
        self.assertEqual(b.get.call_args_list, [call('snap', q=''), call('snap', q='Go')])

    def test_snap_rejects_invalid_response(self):
        for response in ({}, {'s': None}, {'s': {}}, {'s': [1]}):
            with self.subTest(response=response):
                b = native_bridge.Bridge(12345)
                b.get = Mock(return_value=response)
                with self.assertRaises(RuntimeError):
                    b.snap()

    def test_text_click_chooses_button_not_label_or_input(self):
        button = widget('NavigationBarButton')
        b = self.bridge([widget('Label'), widget('TextInput'), button])
        self.assertEqual(b.click(text='Go'), {'target': button, 'result': {'ok': True}})
        b.get.assert_called_once_with('click', x=50.0, y=42.0, wait=1)
        b.snap.assert_called_once_with()

    def test_fill_pins_input_type_and_preserves_text(self):
        target = widget('TextInput', 'draft')
        b = self.bridge([widget('Label', 'draft'), widget('Button', 'draft'), target])
        text = '  私人草稿\ne\u0301 👩‍👩‍👧‍👦  '
        b.fill('draft', text)
        self.assertEqual(b.get.call_args_list, [
            call('click', x=50.0, y=42.0, wait=1),
            call('k', k='press', c='KeyA', wait=1, ctrl=1),
            call('k', k='press', c='Backspace', wait=1),
            call('t', t=text, wait=1)])

    def test_explicit_type_disambiguates_button_types_but_never_label(self):
        target = widget('NavigationBarButton')
        b = self.bridge([widget(), target, widget('Label')])
        self.assertIs(b.click(text='Go', ty='NavigationBarButton')['target'], target)
        b.get.reset_mock()
        with self.assertRaises(ValueError):
            b.click(text='Go', ty='Label')
        b.get.assert_not_called()

    def test_ambiguous_target_does_not_click_or_leak_private_text(self):
        private = 'DO-NOT-ECHO-PRIVATE-DRAFT'
        b = self.bridge([widget(text=private), widget(text=private, rect=(40, 50, 60, 24))])
        with self.assertRaises(ValueError) as error:
            b.click(text=private)
        self.assertNotIn(private, str(error.exception))
        b.get.assert_not_called()
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            b.reveal(text=private)
        b.get.assert_not_called()

    def test_missing_selector_refused_without_scroll_or_click(self):
        b = self.bridge([viewport(), widget()])
        with self.assertRaises(ValueError):
            b.reveal()
        b.snap.assert_not_called()
        b.get.assert_not_called()

    def test_reveal_uses_same_snapshot_for_viewport_target_and_overlay(self):
        b = self.bridge([])
        target = widget(rect=(110, 130, 60, 24))
        b.snap.side_effect = [[viewport()], [viewport((100, 100, 200, 200)), target]]
        self.assertIs(b.reveal(text='Go'), target)
        self.assertEqual(b.snap.call_count, 2)  # reset observation + one reveal step
        self.assertEqual(b.get.call_args_list, [
            call('m', k='scroll', x=192, y=130.0, dy=-5000, wait=1)])

    def test_reveal_requires_entire_rectangle_in_both_axes(self):
        for rect in ((0, 30, 60, 24), (180, 30, 60, 24),
                     (20, 10, 60, 24), (20, 210, 60, 24)):
            with self.subTest(rect=rect):
                b = self.bridge([viewport(), widget(rect=rect)])
                with self.assertRaisesRegex(ValueError, 'fully inside'):
                    b.click_app(text='Go')
                self.assertFalse(any(c.args[0] == 'click' for c in b.get.call_args_list))
                self.assertEqual(sum(c.kwargs.get('dy') == 150 for c in b.get.call_args_list), 40)

    def test_reveal_rejects_oversized_zero_area_or_hidden_targets(self):
        for rect, visible in (((20, 30, 201, 24), 1), ((20, 30, 60, 201), 1),
                              ((20, 30, 60, 0), 1), ((20, 30, 60, 24), 0)):
            with self.subTest(rect=rect, visible=visible):
                b = self.bridge([viewport(), widget(rect=rect, visible=visible)])
                with self.assertRaises(ValueError):
                    b.click_app(text='Go')
                self.assertFalse(any(c.args[0] == 'click' for c in b.get.call_args_list))

    def test_reveal_rejects_duplicate_even_if_second_is_outside_viewport(self):
        b = self.bridge([viewport(), widget(), widget(rect=(300, 300, 60, 24))])
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            b.reveal(text='Go')
        b.get.assert_not_called()

    def test_reveal_preserves_full_forty_scroll_capacity(self):
        target = widget()
        b = self.bridge([])
        # One reset snapshot, then 40 misses, then visible after the 40th scroll.
        b.snap.side_effect = [[viewport()]] + [[viewport()] for _ in range(40)] + [[viewport(), target]]
        self.assertIs(b.reveal(text='Go'), target)
        self.assertEqual(b.snap.call_count, 42)
        self.assertEqual([c.kwargs['dy'] for c in b.get.call_args_list], [-5000] + [150] * 40)

    def test_visible_known_overlays_block_target_centre(self):
        for ty in ('Tooltip', 'CalloutTooltip', 'Modal'):
            for operation in ('click', 'click_app'):
                with self.subTest(ty=ty, operation=operation):
                    overlay = widget(ty, 'overlay', 'PRIVATE', (45, 35, 20, 20))
                    b = self.bridge([viewport(), widget(), overlay])
                    with self.assertRaisesRegex(ValueError, 'visible known overlay'):
                        getattr(b, operation)(text='Go')
                    self.assertFalse(any(c.args[0] == 'click' for c in b.get.call_args_list))
                    # A parked overlay is dismissible: once the snapshot no longer
                    # shows it, the same call proceeds (settle moved the pointer).
                    clear_target = widget()
                    b.snap = Mock(return_value=[viewport(), clear_target])
                    if operation == 'click':
                        self.assertIs(b.click(text='Go')['target'], clear_target)

    def test_empty_tooltip_does_not_block_clicks(self):
        # Rinx parks an empty CalloutTooltip over the module; it renders and
        # intercepts nothing, so clicks pass through (verified empirically).
        for operation in ('click', 'click_app'):
            with self.subTest(operation=operation):
                target = widget()
                empty_tip = widget('CalloutTooltip', 'overlay', '', (45, 35, 400, 400))
                b = self.bridge([viewport(), target, empty_tip])
                result = getattr(b, operation)(text='Go')
                self.assertIs(result['target'], target)

    def test_hidden_zero_area_or_nonintersecting_overlays_do_not_block(self):
        for overlay in (widget('Modal', 'overlay', visible=0),
                        widget('Tooltip', 'overlay', rect=(20, 30, 0, 24)),
                        widget('CalloutTooltip', 'overlay', rect=(150, 150, 30, 30))):
            with self.subTest(overlay=overlay):
                target = widget()
                b = self.bridge([viewport(), target, overlay])
                self.assertIs(b.click_app(text='Go')['target'], target)

    def test_click_app_clicks_reveal_row_without_second_arbitrary_match(self):
        target = widget(rect=(80, 100, 70, 20))
        b = self.bridge([])
        b.reveal = Mock(return_value=target)
        b.snap.side_effect = AssertionError('must not resnapshot after reveal')
        result = b.click_app(text='Go', ty='Button')
        b.reveal.assert_called_once_with(text='Go', id=None, ty='Button')
        self.assertIs(result['target'], target)
        b.get.assert_called_once_with('click', x=115.0, y=110.0, wait=1)

    def test_app_scroll_requires_unique_nonempty_viewport(self):
        for rows in ([], [viewport(), viewport()], [viewport((0, 0, 0, 30))]):
            b = self.bridge(rows)
            with self.assertRaisesRegex(ValueError, 'unique visible app_scroll'):
                b.app_scroll(150)
            b.get.assert_not_called()

    def test_app_scroll_point_stays_inside_narrow_viewport(self):
        b = self.bridge([viewport((0, 0, 8, 10))])
        b.app_scroll(150)
        self.assertEqual(b.get.call_args.kwargs['x'], 4)

    def test_http_query_encoding_and_proxy_disabled(self):
        with patch('urllib.request.build_opener') as build:
            b = native_bridge.Bridge(12345)
        self.assertEqual(build.call_args.args[0].proxies, {})
        self.assertIsInstance(build.call_args.args[1], native_bridge._NoRedirect)
        b.http = Mock()
        b.window = 2
        b.http.open.return_value = io.BytesIO(b'{"ok":true}')
        self.assertEqual(b.get('t', t='a&b\n中文'), {'ok': True})
        url = b.http.open.call_args.args[0]
        parsed = urllib.parse.urlsplit(url)
        self.assertEqual(parsed.netloc, '127.0.0.1:12345')
        self.assertEqual(urllib.parse.parse_qs(parsed.query), {'t': ['a&b\n中文'], 'w': ['2']})

    def test_http_errors_do_not_expose_payload_or_request_url(self):
        secret = 'PRIVATE-DRAFT'
        for body in (b'{"err":"PRIVATE-DRAFT"}', b'{"error":"PRIVATE-DRAFT"}',
                     b'{"ok":false}', b'[]', b'PRIVATE-DRAFT'):
            b = native_bridge.Bridge(12345)
            b.http = Mock()
            b.http.open.return_value = io.BytesIO(body)
            with self.assertRaises(RuntimeError) as error:
                b.get('t', t=secret)
            self.assertNotIn(secret, str(error.exception))
        b.http.open.side_effect = urllib.error.URLError(secret)
        with self.assertRaises(RuntimeError) as error:
            b.get('t', t=secret)
        self.assertNotIn(secret, str(error.exception))

    def test_multiwindow_snapshot_refused_before_input(self):
        b = native_bridge.Bridge(12345)
        b.get = Mock(return_value={'s': [{**widget(), 'w': 1}, {**widget('View'), 'w': 2}]})
        with self.assertRaisesRegex(RuntimeError, 'Multiple native windows'):
            b.snap()
        self.assertEqual(b.get.call_args_list, [call('snap', q='')])

    def test_all_input_endpoints_carry_bound_window_id(self):
        b = native_bridge.Bridge(12345)
        b.window = 2
        for endpoint in ('click', 't', 'k', 'm'):
            b.http = Mock()
            b.http.open.return_value = io.BytesIO(b'{"ok":true}')
            b.get(endpoint)
            query = urllib.parse.urlsplit(b.http.open.call_args.args[0]).query
            self.assertEqual(urllib.parse.parse_qs(query)['w'], ['2'])
        with self.assertRaisesRegex(ValueError, 'differs'):
            b.get('click', w=1)

    def test_no_external_endpoint_redirect_or_injected_port(self):
        for port in ('1/path', '123@external', 0, 65536, True):
            with self.assertRaises(ValueError):
                native_bridge.Bridge(port)
        b = native_bridge.Bridge(12345)
        for path in ('https://external/', '//external', '../t', 't?x=1', 't#frag'):
            with self.assertRaises(ValueError):
                b.get(path)
        with self.assertRaisesRegex(RuntimeError, 'redirects'):
            native_bridge._NoRedirect().redirect_request(None, None, 302, '', {}, 'https://external/')


class SessionTests(OfflineTest):
    def host(self, width=412, height=892, cards=None):
        b = Mock()
        b.snap.return_value = [widget('RinxModuleView', 'rinx', '', (100, 132, width, height - 32))]
        b.get.return_value = {'s': cards or []}
        return b

    def test_module_requires_exactly_one_visible_nonempty_instance(self):
        target = widget('RinxModuleView', rect=(100, 132, 412, 860))
        b = Mock()
        for rows in ([], [target, target], [widget('RinxModuleView', visible=0)],
                     [widget('RinxModuleView', rect=(0, 0, 20, 0))]):
            b.snap.return_value = rows
            with self.assertRaises(ValueError):
                rinx_session.module(b)
        b.snap.return_value = [target, widget('RinxModuleView', visible=0)]
        self.assertEqual(rinx_session.module(b), [100, 132, 412, 860])

    def test_exact_geometry_reports_measurements_and_app(self):
        card = widget('Splash', 'card', '', (100, 164, 412, 828))
        b = self.host(cards=[card])
        result = rinx_session.resize(b, 412, 892)
        self.assertEqual(result, {'requested_size': [412, 892], 'actual_size': [412, 892],
                                 'exact_size': True, 'tolerance': 0,
                                 'rinx_frame': [100, 100, 412, 892],
                                 'module': [100, 132, 412, 860], 'embedded_app': card['r']})
        b.get.assert_called_once_with('snap', q='card')

    def test_default_strict_geometry_never_calls_850_an_892(self):
        b = self.host(height=850)
        with self.assertRaisesRegex(RuntimeError, 'requested 412x892, actual 412x850'):
            rinx_session.resize(b, 412, 892)
        self.assertEqual(b.get.call_count, 9)  # three failed physical drags
        self.assertTrue(all(c.args[0] == 'm' for c in b.get.call_args_list))
        with self.assertRaises(RuntimeError):
            rinx_session.resize(self.host(height=891), 412, 892)

    def test_explicit_tolerance_reports_actual_size_and_false_exact(self):
        result = rinx_session.resize(self.host(height=850), 412, 892, tolerance=42)
        self.assertEqual(result['requested_size'], [412, 892])
        self.assertEqual(result['actual_size'], [412, 850])
        self.assertEqual(result['rinx_frame'], [100, 100, 412, 850])
        self.assertFalse(result['exact_size'])
        self.assertEqual(result['tolerance'], 42)
        for b in (self.host(height=850), self.host(width=454)):
            with self.assertRaises(RuntimeError):
                rinx_session.resize(b, 412, 892, tolerance=41)

    def test_invalid_geometry_or_tolerance_refused_before_bridge(self):
        b = Mock()
        for tolerance in (-1, float('nan'), float('inf'), True, '42', None):
            with self.assertRaises(ValueError):
                rinx_session.resize(b, 412, 892, tolerance=tolerance)
        for width, height in ((0, 892), (412, 32), (True, 892), (float('inf'), 892)):
            with self.assertRaises(ValueError):
                rinx_session.resize(b, width, height)
        self.assertEqual(b.mock_calls, [])

    def test_resize_remeasures_after_drag(self):
        b = self.host()
        b.snap.side_effect = [[widget('RinxModuleView', rect=(100, 132, 400, 800))],
                              [widget('RinxModuleView', rect=(100, 132, 412, 860))]]
        result = rinx_session.resize(b, 412, 892)
        self.assertTrue(result['exact_size'])
        self.assertEqual(b.get.call_count, 4)
        self.assertEqual([c.kwargs.get('k') for c in b.get.call_args_list[:3]], ['down', 'move', 'up'])

    def test_duplicate_embedded_apps_refused(self):
        card = widget('Splash', 'card')
        with self.assertRaisesRegex(ValueError, 'duplicates'):
            rinx_session.resize(self.host(cards=[card, card]), 412, 892)

    def test_load_default_deny_has_no_bridge_side_effect(self):
        b = Mock()
        for kwargs in ({}, {'allow_run': False}, {'allow_run': 1}, {'allow_run': 'yes'}):
            with self.assertRaises(PermissionError):
                rinx_session.load(b, '/synthetic/bundle', **kwargs)
        self.assertEqual(b.mock_calls, [])

    def test_load_always_fills_room_and_back_is_shell_click(self):
        for room in (None, '', '!synthetic:example.invalid'):
            with self.subTest(room=room):
                b = Mock()
                notice = widget('Label', 'notice', 'Synthetic review')
                b.snap.return_value = [notice]
                result = rinx_session.load(b, Path('/synthetic/bundle'), room, allow_run=True)
                expected_room = '' if room is None else room
                self.assertEqual(b.mock_calls, [call.click(text='Back'), call.click(text='Import an app'),
                                               call.fill('path', '/synthetic/bundle'),
                                               call.fill('room', expected_room),
                                               call.click(text='Review bundle'), call.snap('notice'),
                                               call.click(text='Run')])
                b.click_app.assert_not_called()
                self.assertEqual(result['room'], expected_room)
                self.assertEqual(result['review'], [notice])

    def test_load_cli_requires_explicit_opt_in_before_bridge_construction(self):
        with patch.object(rinx_session, 'Bridge') as constructor, \
                patch('sys.stderr', new_callable=io.StringIO) as err:
            with self.assertRaises(SystemExit) as exit_status:
                rinx_session.main(['load', '/synthetic/bundle'])
            self.assertEqual(exit_status.exception.code, 2)
            self.assertIn('--allow-run', err.getvalue())
            constructor.assert_not_called()


class PrepareTests(OfflineTest):
    def setUp(self):
        super().setUp()
        self.tmp = tempfile.TemporaryDirectory(prefix='oncue-helper-unit-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'release'
        self.source.mkdir()
        self.manifest = {'schema': 1, 'id': 'synthetic-test',
                         'integrity': {'signature': {'value': 'synthetic-not-a-key'},
                                       'bundle_blake3': 'synthetic-old-digest'}}
        (self.source / 'manifest.json').write_text(json.dumps(self.manifest), encoding='utf-8')
        (self.source / 'listing.json').write_text(json.dumps({'icon': 'icon.svg', 'screenshots': []}), encoding='utf-8')
        (self.source / 'main.splash').write_text('// synthetic fixture only\n', encoding='utf-8')
        (self.source / 'icon.svg').write_text('<svg/>', encoding='utf-8')
        self.hub = self.root / 'mock-hub'
        self.hub.write_text('MUST NEVER EXECUTE\n', encoding='utf-8')
        self.hub.chmod(0o700)
        self.destination = self.root / 'fresh'
        self.run.side_effect = None
        self.run.return_value = subprocess.CompletedProcess([], 0, stdout='mock', stderr='')

    def prepare(self, **kwargs):
        return prepare_dev_bundle.prepare(kwargs.pop('destination', self.destination),
                                          bundle=kwargs.pop('bundle', self.source),
                                          hub=kwargs.pop('hub', self.hub), **kwargs)

    def source_bytes(self):
        return {p.relative_to(self.source).as_posix(): p.read_bytes()
                for p in self.source.rglob('*') if p.is_file() and not p.is_symlink()}

    def assert_preflight_rejected(self, **kwargs):
        with patch.object(prepare_dev_bundle.shutil, 'copytree') as copy:
            with self.assertRaises((ValueError, OSError)):
                self.prepare(**kwargs)
            copy.assert_not_called()
        self.run.assert_not_called()
        self.assertFalse(self.destination.exists())

    def test_prepares_exact_destination_source_preserved_and_explicit_hub_commands(self):
        before = self.source_bytes()
        def hub_result(args, **kwargs):
            self.assertEqual(self.source_bytes(), before)
            self.assertNotIn('signature', json.loads((self.destination / 'manifest.json').read_text())['integrity'])
            return subprocess.CompletedProcess(args, 0, '', '')
        self.run.side_effect = hub_result
        result = self.prepare()
        self.assertEqual(result, self.destination)
        self.assertEqual(self.source_bytes(), before)
        self.assertFalse((result / 'bundle').exists())
        self.assertEqual(self.run.call_args_list, [
            call([str(self.hub), 'stamp', str(result)], check=True, capture_output=True, text=True),
            call([str(self.hub), 'check', str(result), '--allow-unsigned'], check=True, capture_output=True, text=True)])

    def test_rejects_source_itself_source_descendant_existing_or_root_destination(self):
        for destination in (self.source, self.source / 'child', self.root, Path('/')):
            with self.subTest(destination=destination):
                self.assert_preflight_rejected(destination=destination)

    def test_rejects_source_root_symlink_and_component_symlink(self):
        alias = self.root / 'source-link'
        alias.symlink_to(self.source, target_is_directory=True)
        self.assert_preflight_rejected(bundle=alias)
        directory_alias = self.root / 'parent-link'
        directory_alias.symlink_to(self.root, target_is_directory=True)
        self.assert_preflight_rejected(bundle=directory_alias / 'release')
        # Resolving first would erase this dangerous component via '..'.
        self.assert_preflight_rejected(bundle=directory_alias / '..' / self.root.name / 'release')

    def test_rejects_destination_symlink_components_and_dangling_link(self):
        alias = self.root / 'destination-link'
        alias.symlink_to(self.root, target_is_directory=True)
        self.assert_preflight_rejected(destination=alias / 'fresh')
        broken = self.root / 'broken'
        broken.symlink_to(self.root / 'not-there', target_is_directory=True)
        self.assert_preflight_rejected(destination=broken)
        self.assert_preflight_rejected(destination=broken / 'fresh')

    def test_rejects_manifest_symlink_without_touching_external_source(self):
        outside = self.root / 'external-manifest.json'
        outside.write_text(json.dumps(self.manifest), encoding='utf-8')
        # Build another fixture rather than delete any pre-existing file.
        source = self.root / 'linked-release'
        source.mkdir()
        (source / 'manifest.json').symlink_to(outside)
        before = outside.read_bytes()
        self.assert_preflight_rejected(bundle=source)
        self.assertEqual(outside.read_bytes(), before)

    def test_rejects_nested_directory_and_file_symlinks(self):
        for directory in (False, True):
            with self.subTest(directory=directory):
                source = self.root / ('directory-link-fixture' if directory else 'file-link-fixture')
                source.mkdir()
                nested = source / 'nested'
                nested.mkdir()
                (nested / 'link').symlink_to(
                    self.source if directory else self.source / 'manifest.json',
                    target_is_directory=directory)
                self.assert_preflight_rejected(bundle=source)

    def test_copied_manifest_symlink_is_rechecked_before_writing(self):
        before = self.source_bytes()
        def changed_copy(source, destination, **kwargs):
            destination.mkdir()
            # Simulate a link appearing during copy, after clean source preflight.
            (destination / 'manifest.json').symlink_to(source / 'manifest.json')
        with patch.object(prepare_dev_bundle.shutil, 'copytree', side_effect=changed_copy):
            with self.assertRaisesRegex(ValueError, 'symlinks'):
                self.prepare()
        self.assertEqual(self.source_bytes(), before)
        self.run.assert_not_called()

    def test_rejects_special_files_before_copy(self):
        os.mkfifo(self.source / 'named-pipe')
        self.assert_preflight_rejected()

    def test_rejects_all_malformed_json_before_copy(self):
        bad = self.source / 'auxiliary.json'
        for content in ('{', '{"duplicate":1,"duplicate":2}', '{"x":NaN}', '\udcff'):
            bad.write_bytes(content.encode('utf-8', errors='surrogatepass'))
            self.assert_preflight_rejected()

    def test_rejects_invalid_manifest_integrity_and_missing_required_files(self):
        for value in ({'integrity': None}, {'integrity': []}, []):
            (self.source / 'manifest.json').write_text(json.dumps(value), encoding='utf-8')
            self.assert_preflight_rejected()
        empty = self.root / 'empty-source'
        empty.mkdir()
        self.assert_preflight_rejected(bundle=empty)

    def test_rejects_missing_unsafe_listing_assets(self):
        for listing in ({'icon': 'missing.svg'}, {'icon': '../external.svg'},
                        {'screenshots': 'not-an-array'}, {'screenshots': ['/absolute.png']}):
            (self.source / 'listing.json').write_text(json.dumps(listing), encoding='utf-8')
            self.assert_preflight_rejected()

    def test_unavailable_hub_preflight_does_not_copy_or_execute(self):
        self.assert_preflight_rejected(hub=self.root / 'absent')
        self.hub.chmod(0o600)
        self.assert_preflight_rejected()
        with patch.dict(os.environ, {}, clear=True):
            self.assert_preflight_rejected(hub=None)

    def test_hub_path_lookup_never_runs_version_or_download(self):
        with patch.dict(os.environ, {'PATH': str(self.root), 'OCTO_HUB': self.hub.name}):
            self.assertEqual(self.prepare(hub=None), self.destination)
        self.assertEqual([c.args[0][1] for c in self.run.call_args_list], ['stamp', 'check'])

    def test_hub_failure_preserves_source_and_failed_directory_no_ready_output(self):
        before = self.source_bytes()
        for operation in ('stamp', 'check'):
            with self.subTest(operation=operation):
                destination = self.root / ('failure-' + operation)
                def fail(args, **kwargs):
                    if args[1] == operation:
                        raise subprocess.CalledProcessError(7, args, output='PRIVATE', stderr='PRIVATE')
                    return subprocess.CompletedProcess(args, 0, '', '')
                self.run.side_effect = fail
                with patch('sys.stdout', new_callable=io.StringIO) as stdout:
                    with self.assertRaisesRegex(RuntimeError, f'hub {operation} failed') as error:
                        self.prepare(destination=destination)
                self.assertNotIn('PRIVATE', str(error.exception))
                self.assertEqual(stdout.getvalue(), '')
                self.assertTrue(destination.is_dir())
                self.assertEqual(self.source_bytes(), before)

    def test_existing_destination_never_deleted_or_overwritten(self):
        self.destination.mkdir()
        marker = self.destination / 'keep.txt'
        marker.write_text('keep me', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertEqual(marker.read_text(), 'keep me')
        self.run.assert_not_called()

    def test_cli_hub_environment_fallback_and_exact_printed_destination(self):
        with patch.dict(os.environ, {'OCTO_HUB': str(self.hub)}), \
                patch('sys.stdout', new_callable=io.StringIO) as stdout:
            result = prepare_dev_bundle.main([str(self.destination), '--bundle', str(self.source)])
        self.assertEqual(result, 0)
        self.assertEqual(stdout.getvalue(), str(self.destination) + '\n')

    def test_cli_missing_hub_is_clear_argparse_error_before_preflight(self):
        with patch.dict(os.environ, {}, clear=True), \
                patch('sys.stderr', new_callable=io.StringIO) as err, \
                patch.object(prepare_dev_bundle, 'prepare') as prepare:
            with self.assertRaises(SystemExit) as status:
                prepare_dev_bundle.main([str(self.destination)])
            self.assertEqual(status.exception.code, 2)
            self.assertIn('--hub', err.getvalue())
            self.assertIn('OCTO_HUB', err.getvalue())
            prepare.assert_not_called()

    def test_cli_hub_failure_returns_nonzero_without_success_output(self):
        self.run.side_effect = subprocess.CalledProcessError(3, ['mock-hub'])
        with patch('sys.stdout', new_callable=io.StringIO) as stdout, \
                patch('sys.stderr', new_callable=io.StringIO) as err:
            with self.assertRaises(SystemExit) as status:
                prepare_dev_bundle.main([str(self.destination), '--bundle', str(self.source), '--hub', str(self.hub)])
            self.assertEqual(status.exception.code, 1)
            self.assertEqual(stdout.getvalue(), '')
            self.assertIn('hub stamp failed', err.getvalue())

    def test_import_is_safe_with_unrelated_command_line(self):
        with patch.object(sys, 'argv', ['other-tool', '--unrelated']), \
                patch('argparse.ArgumentParser.parse_args', side_effect=AssertionError('import parsed CLI')), \
                patch('shutil.copytree', side_effect=AssertionError('import copied bundle')):
            for name in ('native_bridge', 'rinx_session', 'prepare_dev_bundle'):
                spec = importlib.util.spec_from_file_location('offline_' + name, TOOLS / (name + '.py'))
                imported = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(imported)
        self.run.assert_not_called()
        self.assertTrue(sys.dont_write_bytecode)


if __name__ == '__main__':
    unittest.main(verbosity=2)
