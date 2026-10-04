#!/usr/bin/env python3
"""Make and check a fresh unsigned development copy, never the release bundle.

Importing performs no parsing, copying, subprocess or network activity. Preflight
uses only local paths/stat/reads; the only commands are explicit hub stamp and
hub check --allow-unsigned. A failed copy/check is left in place for inspection,
never reported ready, and never automatically deleted or reused.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess

DEFAULT_BUNDLE = Path(__file__).absolute().parents[1] / 'bundle'


def _checked_path(value, label):
    """Reject symlinks in every supplied component BEFORE resolving the path."""
    path = Path(value).absolute()
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(mode):
            raise ValueError(f'{label} must not contain symlinks: {current}')
    return path.resolve()


def _json_file(path):
    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError('non-finite JSON constant')

    try:
        return json.loads(path.read_text(encoding='utf-8'),
                          object_pairs_hook=object_pairs, parse_constant=invalid_constant)
    except (UnicodeError, ValueError):
        raise ValueError(f'Invalid JSON in {path.name}') from None


def _preflight_source(source):
    if not source.is_dir():
        raise ValueError('Source bundle must be an existing directory')
    files = {}
    pending = [source]
    while pending:
        for path in pending.pop().iterdir():
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise ValueError(f'Source bundle must not contain symlinks: {path}')
            if stat.S_ISDIR(mode):
                pending.append(path)
            elif stat.S_ISREG(mode):
                files[path.relative_to(source).as_posix()] = path
            else:
                raise ValueError(f'Source bundle contains a non-regular file: {path}')
    for name in ('manifest.json', 'listing.json', 'main.splash'):
        if name not in files:
            raise ValueError(f'Source bundle is missing required file: {name}')
    parsed = {}
    # Read every regular file before creating anything. All JSON, including
    # nested auxiliary JSON, must parse before copytree can run.
    for name, path in files.items():
        if path.suffix.lower() == '.json':
            parsed[name] = _json_file(path)
        else:
            with path.open('rb') as stream:
                while stream.read(1024 * 1024):
                    pass
    manifest, listing = parsed['manifest.json'], parsed['listing.json']
    if not isinstance(manifest, dict) or not isinstance(listing, dict):
        raise ValueError('manifest.json and listing.json must contain JSON objects')
    if 'integrity' in manifest and not isinstance(manifest['integrity'], dict):
        raise ValueError('manifest integrity must be a JSON object')
    # Hub is the authoritative schema/policy gate. Check any local asset
    # references now too, so missing files are not discovered only after copying.
    references = []
    if 'icon' in listing:
        references.append(listing['icon'])
    if 'screenshots' in listing:
        if not isinstance(listing['screenshots'], list):
            raise ValueError('listing screenshots must be an array')
        references.extend(listing['screenshots'])
    for reference in references:
        if (not isinstance(reference, str) or not reference
                or Path(reference).is_absolute() or '..' in Path(reference).parts
                or reference not in files):
            raise ValueError('listing references a missing or unsafe local asset')
    return manifest


def _hub_path(hub):
    hub = os.environ.get('OCTO_HUB') if hub is None else os.fspath(hub)
    if not isinstance(hub, str) or not hub.strip():
        raise ValueError('Specify --hub or set OCTO_HUB to a local hub executable')
    # A command name uses PATH lookup only, not --version or another execution.
    candidate = shutil.which(hub) if os.sep not in hub else hub
    if candidate is None:
        raise ValueError('Hub executable was not found on PATH')
    path = _checked_path(candidate, 'Hub path')
    if not path.is_file() or not os.access(path, os.X_OK):
        raise ValueError('Hub must be an existing executable regular file')
    return path


def prepare(destination, *, bundle=DEFAULT_BUNDLE, hub=None):
    """Preflight, copy, remove only the copy's signature, stamp and check; return Path.

    destination is the bundle root itself (no extra ``bundle`` subdirectory).
    It must not exist, must not be within the source, and neither tree/path may
    contain symlinks. No source write, directory deletion, network fetch, signing,
    or runtime execution is performed. Do not modify either tree concurrently.
    """
    source = _checked_path(bundle, 'Source path')
    out = _checked_path(destination, 'Destination path')
    if out.exists() or out == Path(out.anchor) or out == source or source in out.parents:
        raise ValueError('destination must be a NEW directory outside the source bundle')
    _preflight_source(source)
    executable = _hub_path(hub)
    # Both complete tree/JSON preflight and executable lookup precede all writes.
    shutil.copytree(source, out, symlinks=True)
    # Do not write through a copied link even if the source changed during copy.
    _checked_path(out, 'Destination path')
    manifest = _preflight_source(out)
    manifest.setdefault('integrity', {}).pop('signature', None)
    (out / 'manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for operation, args in (('stamp', []), ('check', ['--allow-unsigned'])):
        try:
            subprocess.run([str(executable), operation, str(out), *args], check=True,
                           capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f'hub {operation} failed (exit {exc.returncode}); '
                               f'copy left at {out}; source not modified') from None
        except OSError:
            raise RuntimeError(f'hub {operation} could not execute; copy left at {out}; '
                               'source not modified') from None
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--bundle', type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument('--hub', default=os.environ.get('OCTO_HUB'),
                        help='local hub executable (default: OCTO_HUB); no download')
    args = parser.parse_args(argv)
    if not args.hub:
        parser.error('Specify --hub or set OCTO_HUB to a local hub executable')
    try:
        destination = prepare(args.destination, bundle=args.bundle, hub=args.hub)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(1, f'error: {exc}\n')
    print(destination)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
