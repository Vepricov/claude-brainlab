#!/usr/bin/env python3
"""Refresh project-local, read-only Hermes notes. No LLM or task mutation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / 'hermes'))
from hermes_obsidian_board import fetch
from hermes_project_notes import write_project_notes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path, help='Offline test; no SSH connection')
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8'))
    vault = Path(config['vault']).expanduser().resolve()
    if not (vault / '.obsidian').is_dir():
        parser.error('Choose an existing Obsidian vault')
    routes = config['projects']
    if not isinstance(routes, dict) or not routes:
        parser.error('Map existing Hermes board slugs to existing project folders')
    for folder in routes.values():
        project = (vault / folder).resolve()
        if vault not in project.parents or not project.is_dir():
            parser.error('Each destination must be an existing project inside the vault')
    snapshot = json.loads(args.snapshot.read_text(encoding='utf-8')) if args.snapshot else fetch(
        config['ssh_host'], config['remote_root'], list(routes))
    notes = write_project_notes(vault, snapshot, routes)
    print(json.dumps({'captured_at':snapshot['captured_at'],'notes':notes,
                      'source_statuses_changed':False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
