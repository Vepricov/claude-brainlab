#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

SURNAME_PREFIXES = {
    "da", "de", "del", "della", "der", "di", "du", "dos", "la", "le",
    "van", "von", "ten", "ter"
}


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def repair_malformed_author(name: str) -> str:
    name = normalize_whitespace(name)
    m = re.match(r'^(.*)\{-,\s*([^}]+)\}(.*)$', name)
    if m:
        left, first, right = m.groups()
        surname = f"{left}{{-}}{right}"
        return f"{surname}, {first}"
    return name


def is_corporate_author(name: str) -> bool:
    tokens = normalize_whitespace(name).split()
    if not tokens:
        return False
    joined = " ".join(tokens)
    if any(tok.lower() in {"team", "workshop", "group", "consortium"} for tok in tokens):
        return True
    if any(tok.endswith("-AI") or tok.endswith("_AI") for tok in tokens):
        return True
    if joined in {"Kimi Team", "Tongyi DeepResearch Team", "Essential AI"}:
        return True
    return False


def normalize_single_author(name: str) -> str:
    name = repair_malformed_author(name)
    name = normalize_whitespace(name)
    if not name:
        return name
    if "," in name or is_corporate_author(name):
        return name
    parts = name.split()
    if len(parts) < 2:
        return name
    surname = [parts[-1]]
    i = len(parts) - 2
    while i >= 0:
        token = parts[i]
        token_l = token.lower()
        if (token_l in SURNAME_PREFIXES and token == token.lower()) or token.islower():
            surname.insert(0, token)
            i -= 1
            continue
        break
    first = parts[: i + 1]
    if not first:
        return name
    return f"{' '.join(surname)}, {' '.join(first)}"


def normalize_author_list(authors_str: str) -> str:
    authors_str = normalize_whitespace(authors_str)
    if not authors_str:
        return authors_str
    parts = [p.strip() for p in authors_str.split(" and ") if p.strip()]
    return " and ".join(normalize_single_author(p) for p in parts)


def replace_bibtex_author_field(bibtex_block: str) -> tuple[str, bool]:
    m = re.search(r'author\s*=\s*\{', bibtex_block, re.I)
    if not m:
        return bibtex_block, False

    start = m.end()
    depth = 0
    i = start
    end = None
    while i < len(bibtex_block):
        ch = bibtex_block[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            if depth == 0:
                end = i
                break
            depth -= 1
        i += 1

    if end is None:
        return bibtex_block, False

    old = bibtex_block[start:end]
    new = normalize_author_list(old)
    if new == old:
        return bibtex_block, False
    return bibtex_block[:start] + new + bibtex_block[end:], True


def replace_inline_author_field(bibtex_block: str) -> tuple[str, bool]:
    # Fallback for single-line or oddly formatted BibTeX fields.
    m = re.search(r'(author\s*=\s*\{)([^\n]*?)(\}\s*,?)', bibtex_block, re.I)
    if not m:
        return bibtex_block, False
    old = m.group(2)
    new = normalize_author_list(old)
    if new == old:
        return bibtex_block, False
    return bibtex_block[:m.start(2)] + new + bibtex_block[m.end(2):], True


def process_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    m = re.search(r'```bibtex\n(.*?)\n```', text, re.S)
    if not m:
        return False
    old_block = m.group(1)
    new_block, changed = replace_bibtex_author_field(old_block)
    if not changed:
        new_block, changed = replace_inline_author_field(old_block)
    if not changed:
        return False
    new_text = text[:m.start(1)] + new_block + text[m.end(1):]
    path.write_text(new_text, encoding="utf-8")
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
