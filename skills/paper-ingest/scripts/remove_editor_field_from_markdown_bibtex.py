#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path


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
    root = Path('${OBSIDIAN_VAULT}/Literature')
    changed = []
    for path in sorted(root.rglob('*.md')):
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
