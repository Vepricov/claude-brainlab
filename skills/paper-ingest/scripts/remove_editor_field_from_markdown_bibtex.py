#!/usr/bin/env python3
import pathlib
import sys
from __future__ import annotations

import re
from pathlib import Path

# Где лежат разборы, знает один модуль: `vault_paths`. Захардкоженный путь к хранилищу
# iCloud после переезда 16-10-2026 вёл в несуществующую папку, и запись уходила в пустоту.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from vault_paths import VAULT, temy, tema_put, vse_papki  # noqa: E402


def remove_field(block: str, field_name: str) -> tuple[str, bool]:
    pattern = re.compile(rf'(^\s*{re.escape(field_name)}\s*=\s*\{{)', re.IGNORECASE | re.MULTILINE)
    m = pattern.search(block)
    if not m:
        return block, False

    start = m.start()
    i = m.end()
    depth = 0
    while i < len(block):
        ch = block[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            if depth == 0:
                i += 1
                break
            depth -= 1
        i += 1

    while i < len(block) and block[i] in ', \t':
        i += 1
    if i < len(block) and block[i] == '\n':
        i += 1
    return block[:start] + block[i:], True


def process_file(path: Path) -> bool:
    text = path.read_text(encoding='utf-8')
    m = re.search(r'```bibtex\n(.*?)\n```', text, re.S)
    if not m:
        return False
    block = m.group(1)
    new_block, changed = remove_field(block, 'editor')
    if not changed:
        return False
    new_text = text[:m.start(1)] + new_block + text[m.end(1):]
    path.write_text(new_text, encoding='utf-8')
    return True


def main():
    puti = sorted(p for mesto in vse_papki() for p in mesto.rglob('*.md'))
    changed = []
    for path in puti:
        try:
            if process_file(path):
                changed.append(str(path))
        except Exception:
            continue
    print(f'CHANGED {len(changed)}')
    for p in changed:
        print(p)


if __name__ == '__main__':
    main()
