#!/usr/bin/env python3
"""Batch-enrich every Obsidian paper note in Literature/ with Papers with Code metadata.

Walks the vault Literature tree, extracts each note's arXiv ID from frontmatter
`url:`, and runs the same injection that paper-ingest's Step 6b does — frontmatter
patch (`pwc_url`, `citations`, `citations_updated`, `pwc_tasks`) plus the standalone
TL;DR callout. Idempotent: re-running only updates fields that changed.

REST calls run on a ThreadPoolExecutor (default 8 workers). Per-paper cache lives
in ~/.cache/pwc/ so subsequent runs are mostly hits.

Usage
-----
    pwc_batch_inject.py                 # walk full Literature/ tree
    pwc_batch_inject.py --root PEFT     # limit to one top-level folder
    pwc_batch_inject.py --workers 4     # throttle concurrency
    pwc_batch_inject.py --no-cache      # force refetch (bypasses ~/.cache/pwc/)
    pwc_batch_inject.py --dry-run       # print what would change, write nothing
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import logging
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pwc_fetch import (  # noqa: E402
    ARXIV_ID_RE,
    VAULT_LITERATURE,
    PwcResult,
    fetch,
    inject_into_note,
)

logger = logging.getLogger(__name__)

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---", re.DOTALL)
_URL_LINE_RE = re.compile(r'^\s*url:\s*"?([^"\n]+)"?\s*$', re.MULTILINE)


@dataclass
class Outcome:
    note: Path
    arxiv_id: Optional[str]
    found: bool
    status: str  # "updated", "no_arxiv", "no_pwc", "error"
    detail: str = ""


def _extract_arxiv_id(note: Path) -> Optional[str]:
    try:
        head = note.read_text(errors="replace")[:4096]
    except OSError:
        return None
    fm = _FRONTMATTER_RE.match(head)
    if not fm:
        return None
    url_match = _URL_LINE_RE.search(fm.group(1))
    if not url_match:
        return None
    arxiv_match = ARXIV_ID_RE.search(url_match.group(1))
    return arxiv_match.group(1) if arxiv_match else None


def _process(note: Path, use_cache: bool, dry_run: bool) -> Outcome:
    arxiv_id = _extract_arxiv_id(note)
    if not arxiv_id:
        return Outcome(note=note, arxiv_id=None, found=False, status="no_arxiv")
    try:
        result = fetch(arxiv_id, use_cache=use_cache)
    except Exception as exc:  # network/parse failures must not kill the batch
        return Outcome(note=note, arxiv_id=arxiv_id, found=False, status="error", detail=str(exc))

    if not result.found:
        return Outcome(note=note, arxiv_id=arxiv_id, found=False, status="no_pwc")

    if dry_run:
        return Outcome(note=note, arxiv_id=arxiv_id, found=True, status="updated", detail="(dry-run)")

    try:
        inject_into_note(note, result)
    except Exception as exc:
        return Outcome(note=note, arxiv_id=arxiv_id, found=False, status="error", detail=str(exc))
    return Outcome(note=note, arxiv_id=arxiv_id, found=True, status="updated")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=None, help="restrict to a sub-tree (e.g. PEFT or PEFT/lora_base)")
    parser.add_argument("--workers", type=int, default=8, help="thread pool size (default 8)")
    parser.add_argument("--no-cache", action="store_true", help="bypass ~/.cache/pwc/")
    parser.add_argument("--dry-run", action="store_true", help="report only, do not write")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    base = VAULT_LITERATURE / args.root if args.root else VAULT_LITERATURE
    if not base.exists():
        raise SystemExit(f"path does not exist: {base}")

    notes = sorted(p for p in base.rglob("*.md") if p.is_file())
    total = len(notes)
    print(f"scanning {total} .md files under {base.relative_to(VAULT_LITERATURE.parent)}", file=sys.stderr)

    started = time.monotonic()
    outcomes: list[Outcome] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(_process, n, not args.no_cache, args.dry_run): n for n in notes}
        for i, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            o = fut.result()
            outcomes.append(o)
            if o.status == "error":
                print(f"  [{i}/{total}] ERROR {o.note.name}: {o.detail}", file=sys.stderr)
            elif args.verbose:
                print(f"  [{i}/{total}] {o.status:9s} {o.arxiv_id or '-':12s} {o.note.name}", file=sys.stderr)
            elif i % 25 == 0 or i == total:
                print(f"  [{i}/{total}] processed", file=sys.stderr)

    elapsed = time.monotonic() - started
    counts: dict[str, int] = {}
    for o in outcomes:
        counts[o.status] = counts.get(o.status, 0) + 1

    print(file=sys.stderr)
    print(f"done in {elapsed:.1f}s — {total} notes", file=sys.stderr)
    for status in ("updated", "no_pwc", "no_arxiv", "error"):
        if status in counts:
            print(f"  {status:9s} {counts[status]}", file=sys.stderr)

    errs = [o for o in outcomes if o.status == "error"]
    if errs:
        print("\nerrors:", file=sys.stderr)
        for o in errs[:20]:
            print(f"  {o.note.name}: {o.detail}", file=sys.stderr)

    print(json.dumps({"total": total, "elapsed_s": round(elapsed, 1), "counts": counts}, ensure_ascii=False))
    return 0 if not errs else 1


if __name__ == "__main__":
    sys.exit(main())
