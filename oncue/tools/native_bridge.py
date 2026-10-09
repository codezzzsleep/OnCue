#!/usr/bin/env python3
"""Drive the existing loopback Makepad bridge, not a web app.

No credentials, provider configuration, or Matrix API calls are used here.
Rectangle/known-overlay checks are conservative; they are NOT a general native
z-order hit test and cannot prevent the UI changing after the last snapshot.
"""
import argparse
import json
import math
import re
import time
import urllib.error
import urllib.parse
import urllib.request


def _rect(row):
    rect = row.get('r')
    if (not isinstance(rect, (list, tuple)) or len(rect) != 4
            or any(isinstance(n, bool) or not isinstance(n, (int, float))
                   or not math.isfinite(n) for n in rect)
            or rect[2] <= 0 or rect[3] <= 0):
        return None
    return rect


def _visible(row):
    return isinstance(row, dict) and row.get('v', 1) != 0 and _rect(row) is not None


def _button(ty):
    return isinstance(ty, str) and (ty.startswith('Button') or ty.endswith('Button'))


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError('Bridge redirects are not allowed')


class Bridge:
    def __init__(self, port):
        if isinstance(port, bool) or not re.fullmatch(r'[0-9]+', str(port)):
            raise ValueError('Bridge port must be an integer from 1 to 65535')
        port = int(port)
        if not 1 <= port <= 65535:
            raise ValueError('Bridge port must be an integer from 1 to 65535')
        self.base = f'http://127.0.0.1:{port}'
        self.window = None
        self.http = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), _NoRedirect())

    def get(self, path, **params):
        if not isinstance(path, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_/-]*', path):
            raise ValueError('Expected a relative bridge endpoint')
        if path in ('click', 'k', 't', 'm'):
            if self.window is None:
                # Resolve from an unfiltered snapshot before the first input.
                self.snap()
            if self.window is not None:
                if 'w' in params and params['w'] != self.window:
                    raise ValueError('Input window differs from the bound bridge window')
                params['w'] = self.window
        url = self.base + '/' + path + '?' + urllib.parse.urlencode(params)
        try:
            with self.http.open(url, timeout=20) as response:
                result = json.load(response)
        except (OSError, ValueError, urllib.error.URLError) as exc:
            # Never include the request URL, typed text, or an arbitrary response
            # body in errors: these can contain the user's private draft.
            raise RuntimeError(f'Bridge {path} request failed ({type(exc).__name__})') from None
        if (not isinstance(result, dict) or result.get('err') or result.get('error')
                or result.get('ok') is False):
            raise RuntimeError(f'Bridge {path} returned an error or invalid response')
        return result

    def snap(self, query=''):
        if query:
            self.snap()  # Validate window identity using an unfiltered snapshot first.
        rows = self.get('snap', q=query).get('s')
        if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
            raise RuntimeError('Bridge snap returned an invalid widget list')
        windows = {r['w'] for r in rows if _visible(r) and 'w' in r}
        if len(windows) > 1:
            raise RuntimeError('Multiple native windows are not supported; no input was sent')
        if windows:
            window = next(iter(windows))
            if isinstance(window, bool) or not isinstance(window, int) or window < 0:
                raise RuntimeError('Invalid native window id')
            if self.window is not None and self.window != window:
                raise RuntimeError('Native window changed during this bridge session')
            self.window = window
        return [r for r in rows if _visible(r) and r.get('ty') != 'Splash']

    @staticmethod
    def _targets(rows, text=None, id=None, ty=None):
        if text is None and id is None:
            raise ValueError('Specify widget text or id')
        if ty is not None and (not isinstance(ty, str) or not ty):
            raise ValueError('Widget ty must be a nonempty type name')
        # Text selects buttons, not their coincident Label children. An explicit
        # id can select an input or other widget; fill additionally pins its type.
        return [r for r in rows if _visible(r) and r.get('ty') not in ('Label', 'Splash')
                and (text is None or r.get('t') == text)
                and (id is None or r.get('i') == id)
                and (r.get('ty') == ty if ty is not None
                     else text is None or _button(r.get('ty')))]

    @staticmethod
    def _viewport(rows):
        matches = [r for r in rows if _visible(r) and r.get('i') == 'app_scroll']
        if len(matches) != 1:
            raise ValueError(f'Expected unique visible app_scroll viewport, found {len(matches)}')
        return matches[0]['r']

    @staticmethod
    def _uncovered(rows, row):
        x, y, w, h = row['r']
        cx, cy = x + w / 2, y + h / 2
        for overlay in rows:
            if (not _visible(overlay)
                    or overlay.get('ty') not in ('Tooltip', 'CalloutTooltip', 'Modal')):
                continue
            # An empty tooltip renders nothing (its shader draws zero when no size
            # was calculated) and does not intercept clicks — empirically, hundreds
            # of bridge clicks pass through the Rinx app's persistent empty
            # CalloutTooltip. Only content-bearing overlays can block a click.
            if overlay.get('ty') in ('Tooltip', 'CalloutTooltip') and not str(overlay.get('t', '')).strip():
                continue
            ox, oy, ow, oh = overlay['r']
            if ox <= cx <= ox + ow and oy <= cy <= oy + oh:
                raise ValueError('Click point is covered by a visible known overlay '
                                 f'({overlay["ty"]}); not a general z-order hit test')

    def move(self, x, y, **mods):
        return self.get('m', k='move', x=x, y=y, **mods)

    def settle(self):
        # Park the pointer on the window title bar (no hover widgets there) so a
        # hover-owned tooltip receives HoverOut/ClearHover. Wandering inside the
        # module would only re-trigger tooltips on other widgets.
        rows = [r for r in self.snap() if _visible(r) and r.get('ty') == 'RinxModuleView']
        if not rows:
            return
        x, y, w, h = rows[0]['r']
        for px in (x + w * .25, x + w * .75):
            self.move(px, 16)
            time.sleep(.15)

    def _click_row(self, row):
        x, y, w, h = row['r']
        result = self.get('click', x=x + w / 2, y=y + h / 2, wait=1)
        time.sleep(.15)
        return {'target': row, 'result': result}

    def click(self, text=None, id=None, *, ty=None):
        """Click one shell/global widget; use click_app for app viewport checks."""
        last = None
        for attempt in range(4):
            rows = self.snap()
            matches = self._targets(rows, text=text, id=id, ty=ty)
            if len(matches) != 1:
                raise ValueError(f'Expected unique visible widget, found {len(matches)}')
            try:
                self._uncovered(rows, matches[0])
            except ValueError as exc:
                last = exc
                if 'covered' not in str(exc) or attempt == 3:
                    raise
                self.settle()
                continue
            return self._click_row(matches[0])
        raise last

    def key(self, code, **mods):
        return self.get('k', k='press', c=code, wait=1, **mods)

    def fill(self, id, text):
        if not isinstance(text, str):
            raise ValueError('Input text must be a string')
        self.click(id=id, ty='TextInput')
        self.key('KeyA', ctrl=1)
        self.key('Backspace')
        return self.get('t', t=text, wait=1)

    def scroll(self, x, y, dy):
        return self.get('m', k='scroll', x=x, y=y, dy=dy, wait=1)

    def _scroll_viewport(self, viewport, dy):
        x, y, w, h = viewport
        return self.scroll(x + max(w - 18, w / 2), y + h * .55, dy)

    def app_scroll(self, dy):
        return self._scroll_viewport(self._viewport(self.snap()), dy)

    def reveal(self, text=None, id=None, *, ty=None):
        """Find a unique target fully inside app_scroll, using one snapshot per step.

        Reset to the top, then allow up to 40 downward scrolls. Duplicate targets
        are refused even if only one is inside the viewport. Known visible overlay
        rectangles covering the target centre cause refusal, not a guessed click.
        """
        self._targets([], text=text, id=id, ty=ty)  # Validate before any input event.
        rows = self.snap()
        if len(self._targets(rows, text=text, id=id, ty=ty)) > 1:
            raise ValueError('Expected unique visible widget, found duplicate targets')
        self._scroll_viewport(self._viewport(rows), -5000)
        for step in range(41):
            rows = self.snap()
            viewport = self._viewport(rows)
            matches = self._targets(rows, text=text, id=id, ty=ty)
            if len(matches) > 1:
                raise ValueError('Expected unique visible widget, found duplicate targets')
            if matches:
                row = matches[0]
                x, y, w, h = row['r']
                vx, vy, vw, vh = viewport
                if w > vw or h > vh:
                    raise ValueError('Widget cannot fit completely inside app_scroll viewport')
                if vx <= x and x + w <= vx + vw and vy <= y and y + h <= vy + vh:
                    self._uncovered(rows, row)
                    return row
            if step < 40:
                self._scroll_viewport(viewport, 150)
        raise ValueError('Cannot reveal a unique widget fully inside app_scroll viewport')

    def click_app_visible(self, text=None, id=None, *, ty=None):
        """Click only a currently exposed app control, without scrolling or retries.

        Playback pause checks must not spend the remaining route duration walking
        back down the page. Refuse stale, clipped, duplicate or covered controls;
        use the same fresh snapshot for the target and its viewport.
        """
        rows = self.snap()
        matches = self._targets(rows, text=text, id=id, ty=ty)
        if len(matches) != 1:
            raise ValueError(f'Expected unique visible widget, found {len(matches)}')
        row = matches[0]
        x, y, w, h = row['r']
        vx, vy, vw, vh = self._viewport(rows)
        if not (vx <= x and x + w <= vx + vw and vy <= y and y + h <= vy + vh):
            raise ValueError('Control is not fully inside app_scroll; no timed input was sent')
        self._uncovered(rows, row)
        return self._click_row(row)

    def click_app(self, text=None, id=None, *, ty=None):
        # Click the exact row verified by reveal: do NOT take another snapshot or
        # repeat an unscoped text/id search that might select a different widget.
        last = None
        for attempt in range(4):
            try:
                row = self.reveal(text=text, id=id, ty=ty)
            except ValueError as exc:
                last = exc
                if 'covered' not in str(exc) or attempt == 3:
                    raise
                self.settle()
                continue
            return self._click_row(row)
        raise last


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port', type=int, default=8771)
    p.add_argument('op', choices=['snap', 'click', 'fill', 'get', 'scroll'])
    p.add_argument('args', nargs='*')
    a = p.parse_args()
    b = Bridge(a.port)
    if a.op == 'snap':
        out = b.snap(a.args[0] if a.args else '')
    elif a.op == 'click':
        out = b.click(id=a.args[0][1:]) if a.args[0].startswith('#') else b.click(text=a.args[0])
    elif a.op == 'fill':
        out = b.fill(a.args[0], a.args[1])
    elif a.op == 'scroll':
        out = b.scroll(*map(float, a.args))
    else:
        out = b.get(a.args[0], **dict(v.split('=', 1) for v in a.args[1:]))
    print(json.dumps(out, ensure_ascii=False, indent=2))
