#!/usr/bin/env python3
"""Native Rinx test conveniences: measure/resize its frame and opt in to dev loading.

These helpers drive normal Makepad input events, never modify host APIs, and do
not infer consent to Review/Run from a supplied bundle path.
"""
import argparse
import json
import math
import os
import time

try:
    from .native_bridge import Bridge, _visible
except ImportError:  # Direct script invocation.
    from native_bridge import Bridge, _visible

TITLE_HEIGHT = 32


def module(b):
    """Return the rectangle of exactly one visible, nonempty RinxModuleView."""
    rows = [r for r in b.snap() if _visible(r) and r.get('ty') == 'RinxModuleView']
    if len(rows) != 1:
        raise ValueError(f'Expected unique visible RinxModuleView, found {len(rows)}')
    return list(rows[0]['r'])


def _number(value):
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value))


def resize(b, width, height, *, tolerance=0):
    """Resize the native frame; default to exact geometry, never relabel a miss.

    The existing host frame has a 32-point title and no inset. Geometry is derived
    from the measured module, not the drag request. An explicit finite nonnegative
    tolerance applies independently to width and height (in native window points).
    """
    if not _number(width) or not _number(height) or width <= 0 or height <= TITLE_HEIGHT:
        raise ValueError('Frame width must be positive and height greater than 32')
    if not _number(tolerance) or tolerance < 0:
        raise ValueError('tolerance must be a finite nonnegative number')
    x, y, w, h = module(b)
    for _ in range(3):
        if (w, h + TITLE_HEIGHT) == (width, height):
            break
        # Super + right-drag is the existing host resize gesture. Do not write
        # geometry or report the requested dimensions as measurements.
        px, py = x + w * .75, y + h * .75
        dx, dy = width - w, height - TITLE_HEIGHT - h
        b.get('m', k='down', x=px, y=py, b=1, logo=1)
        b.get('m', k='move', x=px + dx, y=py + dy, b=1, logo=1)
        b.get('m', k='up', x=px + dx, y=py + dy, b=1, logo=1, wait=1)
        time.sleep(.3)
        x, y, w, h = module(b)
    actual = [w, h + TITLE_HEIGHT]
    exact = actual == [width, height]
    if abs(w - width) > tolerance or abs(actual[1] - height) > tolerance:
        raise RuntimeError(f'Resize mismatch: requested {width}x{height}, '
                           f'actual {w}x{actual[1]}, tolerance {tolerance}')
    snapshot = b.get('snap', q='card').get('s')
    if not isinstance(snapshot, list):
        raise RuntimeError('Bridge returned an invalid embedded-app snapshot')
    cards = [r for r in snapshot if _visible(r) and r.get('i') == 'card'
             and r.get('ty') == 'Splash']
    if len(cards) > 1:
        raise ValueError('Expected at most one visible embedded app, found duplicates')
    return {'requested_size': [width, height], 'actual_size': actual,
            'exact_size': exact, 'tolerance': tolerance,
            'rinx_frame': [x, y - TITLE_HEIGHT, w, h + TITLE_HEIGHT],
            'module': [x, y, w, h],
            'embedded_app': list(cards[0]['r']) if cards else None}


def load(b, path, room=None, *, allow_run=False):
    """Explicitly authorize Review/Run, or refuse before any bridge operation.

    None means no room, not reuse the prior form value. Back is the Rinx header
    button and deliberately uses shell/global click, never click_app.
    """
    if allow_run is not True:
        raise PermissionError('Developer Review/Run requires explicit allow_run=True')
    path = os.fspath(path)
    if not isinstance(path, str) or not path.strip():
        raise ValueError('Bundle path must be a nonempty string')
    if room is not None and not isinstance(room, str):
        raise ValueError('Room must be a string or None')
    selected_room = '' if room is None else room
    b.click(text='Back')  # Shell header, outside the app_scroll viewport.
    b.click(text='Import an app')
    b.fill('path', path)
    b.fill('room', selected_room)
    b.click(text='Review bundle')
    notice = [r for r in b.snap('notice') if r.get('i') == 'notice']
    b.click(text='Run')
    return {'review': notice, 'bundle': path, 'room': selected_room}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port', type=int, default=8771)
    commands = p.add_subparsers(dest='op', required=True)
    size = commands.add_parser('resize')
    size.add_argument('width', type=int)
    size.add_argument('height', type=int)
    size.add_argument('--tolerance', type=float, default=0)
    importer = commands.add_parser('load')
    importer.add_argument('path')
    importer.add_argument('room', nargs='?')
    importer.add_argument('--allow-run', action='store_true',
                          help='explicitly permit Developer Review/Run and its runtime grant')
    a = p.parse_args(argv)
    if a.op == 'load' and not a.allow_run:
        p.error('load requires --allow-run; no Review/Run was performed')
    b = Bridge(a.port)
    out = (resize(b, a.width, a.height, tolerance=a.tolerance) if a.op == 'resize'
           else load(b, a.path, a.room, allow_run=a.allow_run))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
