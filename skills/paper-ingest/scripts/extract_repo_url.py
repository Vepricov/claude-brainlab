#!/usr/bin/env python3
"""Extract the most likely code-repository URL for a paper, with zero LLM tokens.

Sources, in order of cleanliness:
  1. arXiv LaTeX source (\\url{}, \\href{}, raw URLs) — cleanest, URLs on one line
  2. pdftotext output — fallback, URLs may be split across lines

Ranking heuristic for the winning URL:
  - proximity to a "code release" keyword (code, available, implementation,
    released, reproduce, official) beats everything
  - then host preference: github > gitlab > bitbucket > 4open.science
  - then frequency in the document
  - then earliest occurrence

Usage:
    python3 extract_repo_url.py --txt /tmp/paper_2509.01440.txt [--src-dir /tmp/arxiv_src_2509.01440]
    python3 extract_repo_url.py --txt a.txt --src-dir b/ --json

Prints the single best repo URL to stdout (empty string if none found).
With --json prints {"git": "...", "candidates": [...]}.
"""
import argparse
import json
import re
import sys
from pathlib import Path

HOST_RANK = {
    "github.com": 0,
    "gitlab.com": 1,
    "bitbucket.org": 2,
    "anonymous.4open.science": 3,
}

# Repo URL: host + /owner/repo . Allow optional trailing path we trim later.
REPO_RE = re.compile(
    r"https?://(?:www\.)?(github\.com|gitlab\.com|bitbucket\.org|anonymous\.4open\.science)/"
    r"[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+(?:/[A-Za-z0-9_.\-/]*)?",
    re.IGNORECASE,
)

# Strong "this is OUR repo" announcement, expected to sit immediately before the URL
# e.g. "our code is available at", "we release our code at", "code can be found at"
OWN_RE = re.compile(
    r"(available\s+at|can\s+be\s+found\s+at|released?\s+at|hosted\s+at|find\s+(it|our\s+code)\s+at"
    r"|our\s+code[^.]{0,30}at|we\s+release[^.]{0,40}at|open[\- ]?sourced?[^.]{0,30}at)\s*[:\s]*$",
    re.IGNORECASE,
)

# Signals that the URL is a CITED BASELINE, not the paper's own repo
BASELINE_RE = re.compile(
    r"(based\s+on|original\s+codebase|official\s+(repositor|implementation|code)"
    r"|we\s+use|built\s+on|extension\s+of|provided\s+(in|by)|taken\s+from|tokenizer)",
    re.IGNORECASE,
)

# github user/repo paths that are NOT real project repos
HOST_BLOCKLIST_OWNERS = {"sponsors", "about", "features", "pricing", "marketplace"}


def _normalize(url: str) -> str:
    url = url.strip().rstrip(").,;:'\"]}>")
    # collapse to repo root: drop /blob/, /tree/, /releases, etc. for github/gitlab/bitbucket
    m = re.match(
        r"(https?://(?:www\.)?(?:github\.com|gitlab\.com|bitbucket\.org)/[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+)",
        url,
        re.IGNORECASE,
    )
    if m:
        url = m.group(1)
    # strip a trailing .git
    if url.endswith(".git"):
        url = url[:-4]
    return url


def _host(url: str) -> str:
    m = re.match(r"https?://(?:www\.)?([^/]+)/", url, re.IGNORECASE)
    return (m.group(1).lower() if m else "").replace("www.", "")


def _owner(url: str) -> str:
    m = re.match(r"https?://(?:www\.)?[^/]+/([^/]+)/", url, re.IGNORECASE)
    return m.group(1).lower() if m else ""


def _read_tex(src_dir: Path | None) -> str:
    chunks: list[str] = []
    if src_dir and src_dir.exists():
        for tex in src_dir.rglob("*.tex"):
            try:
                chunks.append(tex.read_text(errors="ignore"))
            except OSError:
                pass
    return "\n".join(chunks)


def _read_txt(txt_paths: list[Path]) -> str:
    chunks: list[str] = []
    for p in txt_paths:
        if p and p.exists():
            try:
                chunks.append(p.read_text(errors="ignore"))
            except OSError:
                pass
    return "\n".join(chunks)


def _dehyphenate(text: str) -> str:
    """pdftotext often splits a URL across a line break. Re-join when a line
    ends inside an obvious URL continuation."""
    # join "github.com/foo-\n bar" and "github.com/foo\n bar"
    text = re.sub(r"(https?://[^\s]*?)[\-­]?\n\s*([A-Za-z0-9_./\-]+)", r"\1\2", text)
    return text


def find_repo(text: str) -> tuple[str, list[str]]:
    text = _dehyphenate(text)
    total = max(len(text), 1)
    scored: dict[str, dict] = {}
    for m in REPO_RE.finditer(text):
        url = _normalize(m.group(0))
        host = _host(url)
        owner = _owner(url)
        if owner in HOST_BLOCKLIST_OWNERS:
            continue
        if not re.match(r"https?://[^/]+/[^/]+/[^/]+", url + "/"):
            continue
        start = m.start()
        # own-release phrase must sit tight before the URL; \href{ / \url{ wrappers are tolerated
        pre = re.sub(r"[\\{}\s]*(href|url)?[\\{}\s]*$", "", text[max(0, start - 70): start])
        own = 1 if OWN_RE.search(pre + " ") else 0
        baseline = 1 if BASELINE_RE.search(text[max(0, start - 160): start + 40]) else 0
        early = 1 if start < 0.04 * total else 0
        s = scored.setdefault(
            url, {"own": 0, "baseline": 0, "early": 0, "freq": 0, "first": start, "host": HOST_RANK.get(host, 9)}
        )
        s["own"] = max(s["own"], own)
        s["baseline"] = max(s["baseline"], baseline)  # any baseline-context mention disqualifies
        s["early"] = max(s["early"], early)
        s["freq"] += 1
        s["first"] = min(s["first"], start)
    if not scored:
        return "", []

    def score(item):
        _, s = item
        return s["own"] * 100 + s["early"] * 50 - s["baseline"] * 40 + min(s["freq"], 3) * 2

    ranked = sorted(scored.items(), key=lambda it: (-score(it), it[1]["host"], it[1]["first"]))
    candidates = [u for u, _ in ranked]

    # Only auto-commit `git` when confident; otherwise leave the choice to the
    # ingest agent (which already has the full paper text in context).
    top_url, top = ranked[0]
    confident = (len(ranked) == 1 and top["baseline"] == 0) or (top["own"] == 1 and top["baseline"] == 0)
    best = top_url if confident else ""
    return best, candidates


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--txt", action="append", default=[], help="extracted-text file(s)")
    ap.add_argument("--src-dir", help="arXiv LaTeX source dir (searched for *.tex)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    txt_paths = [Path(t) for t in args.txt]
    src_dir = Path(args.src_dir) if args.src_dir else None

    # Prefer the LaTeX source: URLs are clean (\url{}/\href{}), no pdftotext
    # gluing of footnote superscripts or the next word. Only fall back to the
    # pdftotext output when the source yields no repo candidates at all.
    best, candidates = find_repo(_read_tex(src_dir))
    if not candidates:
        best, candidates = find_repo(_read_txt(txt_paths))

    if args.json:
        print(json.dumps({"git": best, "candidates": candidates}, ensure_ascii=False))
    else:
        print(best)


if __name__ == "__main__":
    main()
