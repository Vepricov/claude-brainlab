#!/usr/bin/env python3
"""Create a new Obsidian vault from the audited Lab Atlas setup (Python 3.10+)."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import urllib.request

HERE = Path(__file__).resolve().parent


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_asset(plugin: dict, asset: dict, cache: Path | None) -> bytes:
    if cache is not None:
        return (cache / plugin['id'] / asset['name']).read_bytes()
    request = urllib.request.Request(asset['url'], headers={'User-Agent':'Lab-Atlas-Obsidian-Setup'})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def apply_display_patch(data: bytes, spec: dict) -> bytes:
    if digest(data) != spec['before_sha256']:
        raise ValueError('Display patch: unexpected upstream SHA-256')
    text = data.decode('utf-8')
    boundary = len(text)
    for edit in sorted(spec['edits'], key=lambda e:e['start'], reverse=True):
        if not 0 <= edit['start'] <= edit['end'] <= boundary:
            raise ValueError('Display patch: invalid or overlapping range')
        text = text[:edit['start']] + edit['text'] + text[edit['end']:]
        boundary = edit['start']
    result = text.encode('utf-8')
    if digest(result) != spec['after_sha256']:
        raise ValueError('Display patch: unexpected result SHA-256')
    return result


def build(destination: Path, owner: str, cache: Path | None = None,
          include_disabled: bool = False, display_patches: bool = True) -> dict:
    destination = destination.expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('Choose a NEW folder; existing vaults are never overwritten')
    if not re.fullmatch(r'[\w .-]{1,80}', owner) or not owner.strip() or '..' in owner:
        raise ValueError('Owner: use 1–80 letters, numbers, spaces, dots or hyphens')
    if not destination.parent.is_dir():
        raise ValueError('The destination parent folder must already exist')
    lock = json.loads((HERE / 'plugins.lock.json').read_text(encoding='utf-8'))
    plugins = [p for p in lock['plugins'] if p['enabled'] or include_disabled]
    hashes = {}
    with tempfile.TemporaryDirectory(prefix='.obsidian-setup-', dir=destination.parent) as temp:
        staging = Path(temp) / 'vault'
        shutil.copytree(HERE / 'vault', staging)
        for folder in ['personal/daily','Literature/_inbox','Projects','Staff','Operon/Archives','Operon/Projects','Operon/Tasks']:
            (staging / folder).mkdir(parents=True, exist_ok=True)
        for path in staging.rglob('*'):
            if path.is_file():
                content = path.read_text(encoding='utf-8')
                if '{{OWNER}}' in content:
                    path.write_text(content.replace('{{OWNER}}', owner), encoding='utf-8')
        for plugin in plugins:
            target = staging / '.obsidian/plugins' / plugin['id']
            target.mkdir(parents=True, exist_ok=True)
            for asset in plugin['assets']:
                if asset['name'] not in {'main.js','manifest.json','styles.css'}:
                    raise ValueError('Unexpected plugin asset')
                data = read_asset(plugin, asset, cache)
                if digest(data) != asset['sha256']:
                    raise ValueError(f'SHA-256 mismatch: {plugin["id"]}/{asset["name"]}')
                patch = HERE / 'patches' / (plugin['id'] + '.json')
                if display_patches and asset['name'] == 'main.js' and patch.exists():
                    data = apply_display_patch(data, json.loads(patch.read_text(encoding='utf-8')))
                (target / asset['name']).write_bytes(data)
                hashes[f'{plugin["id"]}/{asset["name"]}'] = digest(data)
            manifest = json.loads((target / 'manifest.json').read_text(encoding='utf-8'))
            if manifest['id'] != plugin['id'] or manifest['version'] != plugin['version']:
                raise ValueError('Plugin manifest differs from the lock file')
        sys.path.insert(0, str(HERE / 'hermes'))
        try:
            from hermes_project_notes import write_project_notes
            snapshot = json.loads((HERE / 'examples/hermes-snapshot.json').read_text(encoding='utf-8'))
            write_project_notes(staging, snapshot, {'example-project':'Papers/example-project'})
        finally:
            sys.path.pop(0)
        receipt = {'setup':'lab-atlas-2026-09-10','owner':owner,'enabled_plugins':14,
                   'downloaded_plugins':len(plugins),'display_patches':display_patches,
                   'plugin_sha256':hashes,'hermes_sample':'synthetic; no refresh scheduled'}
        (staging / '.lab-setup-receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        # Recheck after downloads: do not replace a folder created in the meantime.
        if destination.exists():
            raise FileExistsError('Destination appeared during installation')
        staging.rename(destination)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vault', type=Path, required=True, help='New folder; must not exist')
    parser.add_argument('--owner', required=True, help='Your task assignee name')
    parser.add_argument('--cache', type=Path, help='Previously downloaded ID/asset files; hashes still checked')
    parser.add_argument('--include-disabled', action='store_true', help='Also download the two disabled navigation alternatives')
    parser.add_argument('--upstream-display', action='store_true', help='Skip the pinned Operon/Tasks display patches')
    args = parser.parse_args()
    try:
        receipt = build(args.vault, args.owner, args.cache, args.include_disabled, not args.upstream_display)
    except (OSError, ValueError) as error:
        parser.exit(1, f'Installation stopped: {error}\n')
    print(f'Created {args.vault.expanduser().absolute()} with {receipt["enabled_plugins"]} enabled plugins.')
    print('Open this folder as a vault in Obsidian; allow community plugins for this new vault.')
    print('The sample Hermes board is synthetic. No remote connection or scheduler was created.')


if __name__ == '__main__':
    main()
