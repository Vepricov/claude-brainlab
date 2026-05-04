#!/usr/bin/env python3
"""
Fetch BibTeX for a paper from arXiv ID or DOI.
Replaces the citation key with Google Scholar format.
All BibTeX content comes from external APIs, never from LLM.

Usage:
  python3 bibtex_fetch.py --arxiv 1901.06053
  python3 bibtex_fetch.py --doi 10.1073/pnas.2015617118
  python3 bibtex_fetch.py --arxiv 1901.06053 --key-override simsekli2019tail
"""

import argparse
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import json


SURNAME_PREFIXES = {
    "da", "de", "del", "della", "der", "di", "du", "dos", "la", "le",
    "van", "von", "ten", "ter"
}


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


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


def google_scholar_key(authors_str: str, year: str, title: str) -> str:
    """
    Generate Google Scholar format citation key: {lastname}{year}{firsttitleword}
    """
    if not authors_str or not year or not title:
        return "unknown0000unknown"

    authors_str = re.sub(r"\s+", " ", authors_str).strip()
    first_author = authors_str.split(" and ")[0].strip()
    if "," in first_author:
        last_name = first_author.split(",")[0].strip()
    else:
        parts = first_author.split()
        last_name = parts[-1] if parts else "unknown"

    last_name = unicodedata.normalize("NFKD", last_name)
    last_name = last_name.encode("ascii", "ignore").decode("ascii")
    last_name = re.sub(r"[^a-zA-Z]", "", last_name).lower()

    clean_title = re.sub(r"[$${}\\]", "", title)
    clean_title = re.sub(r"[^a-zA-Z\s]", " ", clean_title)
    words = clean_title.split()
    skip = {"a", "an", "the"}
    first_word = ""
    for w in words:
        if w.lower() not in skip:
            first_word = w.lower()
            break

    return f"{last_name}{year}{first_word}"


def fetch_arxiv_bibtex(arxiv_id: str) -> str:
    url = f"https://arxiv.org/bibtex/{arxiv_id}"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0 (research workflow)")
    r = urllib.request.urlopen(req, timeout=15)
    return r.read().decode("utf-8")


def fetch_doi_bibtex(doi: str) -> str:
    url = f"https://doi.org/{doi}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/x-bibtex")
    req.add_header("User-Agent", "Mozilla/5.0 (research workflow)")
    r = urllib.request.urlopen(req, timeout=15)
    return r.read().decode("utf-8")


def lookup_published_ids(arxiv_id: str) -> dict:
    """Query Semantic Scholar for DOI and/or DBLP key. Returns dict with available keys."""
    url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}?fields=externalIds"
    for attempt in range(3):
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "Mozilla/5.0 (research workflow)")
            r = urllib.request.urlopen(req, timeout=10)
            ext = json.loads(r.read().decode("utf-8")).get("externalIds", {})
            doi = ext.get("DOI")
            # 10.48550 is arXiv's own preprint DOI — skip it, use DBLP/arXiv instead
            if doi and doi.startswith("10.48550"):
                doi = None
            return {"doi": doi, "dblp": ext.get("DBLP")}
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            return {}
        except Exception:
            return {}
    return {}


def fetch_dblp_bibtex(dblp_key: str) -> str:
    url = f"https://dblp.org/rec/{dblp_key}.bib"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0 (research workflow)")
    r = urllib.request.urlopen(req, timeout=15)
    return r.read().decode("utf-8")


def lookup_dblp_by_title(title: str):
    query = urllib.parse.quote(title)
    url = f"https://dblp.org/search/publ/api?q={query}&format=json&h=5"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0 (research workflow)")
    r = urllib.request.urlopen(req, timeout=15)
    data = json.loads(r.read().decode("utf-8"))
    hits = data.get("result", {}).get("hits", {}).get("hit", [])
    if isinstance(hits, dict):
        hits = [hits]

    normalized_target = normalize_title_for_match(title)
    for hit in hits:
        info = hit.get("info", {})
        hit_title = normalize_title_for_match(info.get("title", ""))
        if titles_compatible(normalized_target, hit_title):
            return info.get("key")

    return None


def parse_bibtex_fields(bibtex: str) -> dict:
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
        key = body[key_start:i].lower()
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
                        value = body[value_start:i]
                        fields[key] = value.strip()
                        i += 1
                        break
                    depth -= 1
                i += 1
        elif body[i] == '"':
            i += 1
            value_start = i
            while i < n and body[i] != '"':
                i += 1
            value = body[value_start:i]
            fields[key] = value.strip()
            if i < n:
                i += 1
        else:
            value_start = i
            while i < n and body[i] not in ",\n\r":
                i += 1
            value = body[value_start:i]
            fields[key] = value.strip()

    return fields


def normalize_title_for_key(title: str) -> str:
    title = re.sub(r"[{}]", "", title)
    title = re.sub(r"\s+", " ", title)
    return title.strip()


def normalize_field_value(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_title_for_match(title: str) -> str:
    title = normalize_title_for_key(title).lower()
    title = re.sub(r"[^a-z0-9 ]", " ", title)
    title = re.sub(r"\s+", " ", title)
    return title.strip()


def titles_compatible(a: str, b: str) -> bool:
    a_n = normalize_title_for_match(a)
    b_n = normalize_title_for_match(b)
    if not a_n or not b_n:
        return False
    if a_n == b_n:
        return True

    a_words = a_n.split()
    b_words = b_n.split()
    if not a_words or not b_words:
        return False

    # Allow only very small title drift, not generic substring containment.
    shared_prefix = 0
    for x, y in zip(a_words, b_words):
        if x == y:
            shared_prefix += 1
        else:
            break

    if shared_prefix == len(a_words) == len(b_words):
        return True

    # Require near-identical token sequences with at most one-token difference.
    if abs(len(a_words) - len(b_words)) <= 1:
        overlap = sum(1 for x, y in zip(a_words, b_words) if x == y)
        if overlap >= min(len(a_words), len(b_words)) - 1:
            return True

    return False


def replace_citation_key(bibtex: str, new_key: str) -> str:
    return re.sub(r"(@\w+\s*\{)\s*[^,\s]+", rf"\1{new_key}", bibtex, count=1)


def replace_bibtex_field(bibtex: str, field_name: str, new_value: str) -> str:
    pattern = re.compile(rf'(\b{re.escape(field_name)}\s*=\s*\{{)', re.IGNORECASE)
    m = pattern.search(bibtex)
    if not m:
        return bibtex

    start = m.end()
    depth = 0
    i = start
    while i < len(bibtex):
        ch = bibtex[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            if depth == 0:
                return bibtex[:start] + new_value + bibtex[i:]
            depth -= 1
        i += 1
    return bibtex


def remove_bibtex_field(bibtex: str, field_name: str) -> str:
    pattern = re.compile(rf'(^\s*{re.escape(field_name)}\s*=\s*\{{)', re.IGNORECASE | re.MULTILINE)
    m = pattern.search(bibtex)
    if not m:
        return bibtex

    start = m.start()
    i = m.end()
    depth = 0
    while i < len(bibtex):
        ch = bibtex[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            if depth == 0:
                i += 1
                break
            depth -= 1
        i += 1

    while i < len(bibtex) and bibtex[i] in ', \t':
        i += 1
    if i < len(bibtex) and bibtex[i] == '\n':
        i += 1

    return bibtex[:start] + bibtex[i:]


def parse_entry_header(bibtex: str):
    m = re.search(r'@(\w+)\s*\{\s*([^,\s]+)', bibtex)
    if not m:
        return 'misc', 'unknown0000unknown'
    return m.group(1).lower(), m.group(2)


def derive_arxiv_id(fields: dict) -> str:
    if fields.get('eprint'):
        return normalize_field_value(fields['eprint'])
    vol = normalize_field_value(fields.get('volume', ''))
    if vol.startswith('abs/'):
        return vol.split('abs/', 1)[1]
    doi = normalize_field_value(fields.get('doi', ''))
    if doi.upper().startswith('10.48550/ARXIV.'):
        return doi.split('ARXIV.', 1)[1]
    url = normalize_field_value(fields.get('url', ''))
    m = re.search(r'arxiv\.org/abs/([^\s/]+)', url)
    if m:
        return m.group(1)
    return ''


def is_corr_style_preprint(fields: dict) -> bool:
    journal = normalize_field_value(fields.get('journal', '')).lower()
    volume = normalize_field_value(fields.get('volume', '')).lower()
    doi = normalize_field_value(fields.get('doi', '')).upper()
    eprinttype = normalize_field_value(fields.get('eprinttype', '')).lower()
    url = normalize_field_value(fields.get('url', '')).lower()
    return (
        journal == 'corr'
        or volume.startswith('abs/')
        or doi.startswith('10.48550/ARXIV')
        or eprinttype == 'arxiv'
        or 'arxiv.org/abs/' in url
    )


def format_bibtex(entry_type: str, key: str, fields: dict) -> str:
    def line(name, value):
        return f"  {name} = {{{normalize_field_value(value)}}},"

    lines = [f"@{entry_type}{{{key},"]
    if entry_type == 'misc':
        order = ['title', 'author', 'year', 'eprint', 'archivePrefix', 'primaryClass', 'url']
    elif entry_type == 'inproceedings':
        order = ['author', 'title', 'booktitle', 'series', 'pages', 'publisher', 'year', 'url', 'doi', 'timestamp', 'biburl', 'bibsource']
    elif entry_type == 'article':
        order = ['author', 'title', 'journal', 'volume', 'pages', 'year', 'url', 'doi', 'eprinttype', 'eprint', 'timestamp', 'biburl', 'bibsource']
    else:
        order = ['author', 'title', 'journal', 'booktitle', 'volume', 'pages', 'publisher', 'year', 'url', 'doi', 'eprinttype', 'eprint', 'timestamp', 'biburl', 'bibsource']

    used = set()
    for field in order:
        if field in fields and normalize_field_value(fields[field]):
            lines.append(line(field, fields[field]))
            used.add(field)
    for field in fields:
        if field not in used and normalize_field_value(fields[field]):
            lines.append(line(field, fields[field]))
    if len(lines) > 1 and lines[-1].endswith(','):
        lines[-1] = lines[-1][:-1]
    lines.append('}')
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arxiv", help="arXiv ID (e.g. 1901.06053)")
    parser.add_argument("--doi", help="DOI (e.g. 10.1073/pnas.2015617118)")
    parser.add_argument("--key-override", help="Override the auto-generated key")
    args = parser.parse_args()

    bibtex = None
    source = None

    if args.arxiv:
        # Priority: DOI (journal) → DBLP (conference) → arXiv @misc (preprint)
        arxiv_bib = None
        title_guess = ""
        try:
            arxiv_bib = fetch_arxiv_bibtex(args.arxiv)
            arxiv_fields = parse_bibtex_fields(arxiv_bib)
            title_guess = normalize_title_for_key(arxiv_fields.get("title", ""))
        except Exception:
            arxiv_bib = None
            title_guess = ""

        ids = lookup_published_ids(args.arxiv)
        if ids.get("doi"):
            try:
                bibtex = fetch_doi_bibtex(ids["doi"])
                source = "doi"
            except Exception:
                ids["doi"] = None
        if not bibtex and ids.get("dblp"):
            try:
                candidate_bib = fetch_dblp_bibtex(ids["dblp"])
                candidate_fields = parse_bibtex_fields(candidate_bib)
                candidate_title = normalize_title_for_key(candidate_fields.get("title", ""))
                if title_guess and not titles_compatible(title_guess, candidate_title):
                    raise ValueError("Semantic Scholar DBLP title mismatch")
                bibtex = candidate_bib
                source = "dblp"
            except Exception:
                pass
        if not bibtex:
            try:
                if title_guess:
                    dblp_key = lookup_dblp_by_title(title_guess)
                    if dblp_key:
                        candidate_bib = fetch_dblp_bibtex(dblp_key)
                        candidate_fields = parse_bibtex_fields(candidate_bib)
                        candidate_title = normalize_title_for_key(candidate_fields.get("title", ""))
                        if titles_compatible(title_guess, candidate_title):
                            bibtex = candidate_bib
                            source = "dblp"
            except Exception:
                pass
        if not bibtex:
            try:
                bibtex = arxiv_bib or fetch_arxiv_bibtex(args.arxiv)
                source = "arxiv"
            except Exception as e:
                print(f"ERROR: Failed to fetch from arXiv: {e}", file=sys.stderr)
                sys.exit(1)
    elif args.doi:
        try:
            bibtex = fetch_doi_bibtex(args.doi)
            source = "doi"
        except Exception as e:
            print(f"ERROR: Failed to fetch from DOI: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("ERROR: Provide --arxiv or --doi", file=sys.stderr)
        sys.exit(1)

    entry_type, _old_key = parse_entry_header(bibtex)
    fields = parse_bibtex_fields(bibtex)
    authors = fields.get("author", "")
    normalized_authors = normalize_author_list(authors)
    year = fields.get("year", "")
    title = normalize_title_for_key(fields.get("title", ""))

    if args.key_override:
        new_key = args.key_override
    else:
        new_key = google_scholar_key(authors, year, title)

    if normalized_authors:
        fields['author'] = normalized_authors
        authors = normalized_authors
    fields = {k: normalize_field_value(v) for k, v in fields.items() if normalize_field_value(v)}
    fields.pop('editor', None)

    if args.arxiv and is_corr_style_preprint(fields):
        arxiv_id = derive_arxiv_id(fields) or args.arxiv
        clean_fields = {
            'title': title,
            'author': authors,
            'year': year,
            'eprint': arxiv_id,
            'archivePrefix': 'arXiv',
            'url': f'https://arxiv.org/abs/{arxiv_id}',
        }
        if fields.get('primaryclass'):
            clean_fields['primaryClass'] = fields['primaryclass']
        bibtex = format_bibtex('misc', new_key, clean_fields)
    else:
        bibtex = format_bibtex(entry_type, new_key, fields)

    output = {
        "source": source,
        "bibtex": bibtex,
        "citation_key": new_key,
        "title": title,
        "authors": authors,
        "year": year,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
