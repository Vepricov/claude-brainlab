#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_entry_header(bibtex: str):
    m = re.search(r'@(\w+)\s*\{\s*([^,\s]+)', bibtex)
    if not m:
        return 'misc', 'unknown0000unknown'
    return m.group(1).lower(), m.group(2)


def parse_fields(bibtex: str) -> dict:
    fields = {}
    body_match = re.search(r"@\w+\s*\{[^,]+,(.*)\}\s*$", bibtex, re.DOTALL)
    if not body_match:
        return fields
    body = body_match.group(1)
    i = 0
    n = len(body)
    while i < n:
        while i < n and body[i] in " \t\r\n,":
            i += 1
        if i >= n:
            break
        key_start = i
        while i < n and (body[i].isalnum() or body[i] == "_"):
            i += 1
        key = body[key_start:i]
        while i < n and body[i] in " \t\r\n=":
            i += 1
        if i >= n:
            break
        if body[i] == "{":
            depth = 0
            i += 1
            value_start = i
            while i < n:
                ch = body[i]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    if depth == 0:
                        fields[key] = body[value_start:i].strip()
                        i += 1
                        break
                    depth -= 1
                i += 1
        else:
            value_start = i
            while i < n and body[i] not in ',\n\r':
                i += 1
            fields[key] = body[value_start:i].strip()
    return fields


def derive_arxiv_id(fields: dict) -> str:
    if fields.get('eprint'):
        return normalize_whitespace(fields['eprint'])
    vol = normalize_whitespace(fields.get('volume', ''))
    if vol.startswith('abs/'):
        return vol.split('abs/', 1)[1]
    doi = normalize_whitespace(fields.get('doi', ''))
    if doi.upper().startswith('10.48550/ARXIV.'):
        return doi.split('ARXIV.', 1)[1]
    url = normalize_whitespace(fields.get('url', ''))
    m = re.search(r'arxiv\.org/abs/([^\s/]+)', url)
    if m:
        return m.group(1)
    return ''


def is_corr_style_preprint(fields: dict) -> bool:
    journal = normalize_whitespace(fields.get('journal', '')).lower()
    volume = normalize_whitespace(fields.get('volume', '')).lower()
    doi = normalize_whitespace(fields.get('doi', '')).upper()
    eprinttype = normalize_whitespace(fields.get('eprinttype', '')).lower()
    url = normalize_whitespace(fields.get('url', '')).lower()
    return (
        journal == 'corr'
        or volume.startswith('abs/')
        or doi.startswith('10.48550/ARXIV')
        or eprinttype == 'arxiv'
        or 'arxiv.org/abs/' in url
    )


def format_bibtex(entry_type: str, key: str, fields: dict) -> str:
    def line(name, value):
        return f"  {name} = {{{normalize_whitespace(value)}}},"
    lines = [f"@{entry_type}{{{key},"]
    if entry_type == 'misc':
        order = ['title', 'author', 'year', 'eprint', 'archivePrefix', 'primaryClass', 'url']
    elif entry_type == 'inproceedings':
        order = ['author', 'title', 'booktitle', 'series', 'pages', 'publisher', 'year', 'url', 'doi', 'timestamp', 'biburl', 'bibsource']
    elif entry_type == 'article':
        order = ['author', 'title', 'journal', 'volume', 'pages', 'year', 'url', 'doi', 'eprinttype', 'eprint', 'timestamp', 'biburl', 'bibsource']
    else:
        order = list(fields.keys())
    used = set()
    for f in order:
        if f in fields and normalize_whitespace(fields[f]):
            lines.append(line(f, fields[f]))
            used.add(f)
    for f, v in fields.items():
        if f not in used and normalize_whitespace(v):
            lines.append(line(f, v))
    if len(lines) > 1:
        lines[-1] = lines[-1].rstrip(',')
    lines.append('}')
    return '\n'.join(lines)


def process_file(path: Path) -> bool:
    text = path.read_text(encoding='utf-8')
    m = re.search(r'```bibtex\n(.*?)\n```', text, re.S)
    if not m:
        return False
    old_block = m.group(1)
    entry_type, key = parse_entry_header(old_block)
    fields = parse_fields(old_block)
    if not fields:
        return False
    fields = {k: normalize_whitespace(v) for k, v in fields.items() if normalize_whitespace(v)}
    fields.pop('editor', None)

    if is_corr_style_preprint(fields):
        arxiv_id = derive_arxiv_id(fields)
        new_fields = {
            'title': fields.get('title', ''),
            'author': fields.get('author', ''),
            'year': fields.get('year', ''),
            'eprint': arxiv_id,
            'archivePrefix': 'arXiv',
            'url': f'https://arxiv.org/abs/{arxiv_id}' if arxiv_id else fields.get('url', ''),
        }
        if fields.get('primaryClass'):
            new_fields['primaryClass'] = fields['primaryClass']
        new_block = format_bibtex('misc', key, new_fields)
    else:
        new_block = format_bibtex(entry_type, key, fields)

    if new_block == old_block:
        return False
    path.write_text(text[:m.start(1)] + new_block + text[m.end(1):], encoding='utf-8')
    return True


def main():
    root = Path('${OBSIDIAN_VAULT}/Literature')
    changed = []
    for p in sorted(root.rglob('*.md')):
        try:
            if process_file(p):
                changed.append(str(p))
        except Exception:
            continue
    print(f'CHANGED {len(changed)}')
    for p in changed:
        print(p)


if __name__ == '__main__':
    main()
