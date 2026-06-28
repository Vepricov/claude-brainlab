#!/usr/bin/env python3
"""Fetch Papers with Code (paperswithcode.co) metadata for an arXiv paper.

Hits the undocumented JSON API at:
    GET https://paperswithcode.co/api/v1/papers/{arxiv_id}

Caches responses in ~/.cache/pwc/ to be a good neighbor (API is undocumented,
rate limits unknown). On 404 or network error returns empty result and exits 0
so the paper-ingest pipeline can skip gracefully.

Usage
-----
Print JSON to stdout:
    pwc_fetch.py --arxiv 2106.09685

Render Markdown section to stdout:
    pwc_fetch.py --arxiv 2106.09685 --format md

Inject/replace the "## Papers with Code" section in an existing Obsidian note:
    pwc_fetch.py --arxiv 2106.09685 --inject path/to/note.md

The injector places the section between `## BibTeX` and `## AI Explanation`.
Re-running on the same note replaces the old section in place (idempotent).
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

API_URL = "https://paperswithcode.co/api/v1/papers/{arxiv_id}"
PAPER_URL = "https://paperswithcode.co/papers/{arxiv_id}"
CACHE_DIR = Path.home() / ".cache" / "pwc"
VAULT_LITERATURE = Path(
    "/Users/andrey/Library/Mobile Documents/iCloud~md~obsidian/"
    "Documents/shkodnik1917/Literature"
)
USER_AGENT = "paper-ingest/1.0 (+claude-scholar)"
REQUEST_TIMEOUT = 15
ARXIV_ID_RE = re.compile(r"\b(\d{4}\.\d{4,5})\b")
CALLOUT_OPENER = "> [!abstract] TL;DR (Papers with Code)"
FRONTMATTER_KEYS = ("pwc_url", "citations", "citations_updated", "pwc_tasks")


@dataclass(frozen=True)
class PwcResult:
    arxiv_id: str
    found: bool
    data: dict[str, Any]

    @property
    def url(self) -> str:
        return PAPER_URL.format(arxiv_id=self.arxiv_id)


def fetch(arxiv_id: str, use_cache: bool = True) -> PwcResult:
    """Fetch PwC metadata for arxiv_id. Returns empty result on 404/network failure."""
    arxiv_id = arxiv_id.strip()
    cache_path = CACHE_DIR / f"{arxiv_id}.json"

    if use_cache and cache_path.exists():
        try:
            data = json.loads(cache_path.read_text())
            return PwcResult(arxiv_id=arxiv_id, found=bool(data), data=data or {})
        except json.JSONDecodeError:
            logger.warning("corrupt cache for %s, refetching", arxiv_id)

    url = API_URL.format(arxiv_id=arxiv_id)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            logger.info("PwC has no entry for %s", arxiv_id)
            _write_cache(cache_path, {})
            return PwcResult(arxiv_id=arxiv_id, found=False, data={})
        logger.warning("PwC HTTP %s for %s: %s", exc.code, arxiv_id, exc.reason)
        return PwcResult(arxiv_id=arxiv_id, found=False, data={})
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        logger.warning("PwC network error for %s: %s", arxiv_id, exc)
        return PwcResult(arxiv_id=arxiv_id, found=False, data={})

    _write_cache(cache_path, payload)
    return PwcResult(arxiv_id=arxiv_id, found=True, data=payload)


def _write_cache(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))


def _frontmatter_patch(result: PwcResult) -> dict[str, Any]:
    """Return the key-value pairs to merge into the note's YAML frontmatter."""
    if not result.found:
        return {}
    d = result.data
    patch: dict[str, Any] = {"pwc_url": result.url}
    citations = d.get("citation_count")
    if citations is not None:
        patch["citations"] = int(citations)
    updated = (d.get("citation_updated_at") or "")[:10]
    if updated:
        patch["citations_updated"] = updated
    task_names = [t.get("name") for t in (d.get("tasks") or []) if t.get("name")]
    if task_names:
        patch["pwc_tasks"] = task_names
    return patch


def render_callout(result: PwcResult) -> str:
    """Render the standalone Obsidian callout: TL;DR + Methods used.

    Returns empty string if PwC has nothing to contribute. The callout has no
    enclosing `##` header — it sits as a standalone block between BibTeX and
    AI Explanation.
    """
    if not result.found:
        return ""
    d = result.data
    tldr = (d.get("tldr") or "").strip()
    methods = d.get("methods") or []
    if not tldr and not methods:
        return ""

    lines = [CALLOUT_OPENER]
    if tldr:
        for line in tldr.splitlines():
            lines.append(f"> {line}")
    if methods:
        parts: list[str] = []
        for m in methods:
            name = m.get("name") or m.get("slug") or "?"
            year = m.get("introduced_year")
            parts.append(f"{name} ({year})" if year else name)
        if tldr:
            lines.append(">")
        lines.append(f"> **Methods used**: {'; '.join(parts)}.")
    return "\n".join(lines) + "\n"


def _yaml_render(key: str, value: Any) -> str:
    """Render a single YAML frontmatter block for one key.

    Lists go multiline; strings get double-quoted; ints stay bare.
    """
    if isinstance(value, list):
        body = "\n".join(f"  - {item}" for item in value)
        return f"{key}:\n{body}\n"
    if isinstance(value, bool):
        return f"{key}: {'true' if value else 'false'}\n"
    if isinstance(value, int):
        return f"{key}: {value}\n"
    return f'{key}: "{value}"\n'


_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def _strip_yaml_key(body: str, key: str) -> str:
    """Remove a single top-level key (and its indented continuation) from a YAML body."""
    pattern = re.compile(
        rf"(?m)^{re.escape(key)}:[^\n]*\n(?:[ \t]+[^\n]*\n)*"
    )
    return pattern.sub("", body)


def _inject_frontmatter(text: str, patch: dict[str, Any]) -> str:
    """Merge `patch` into the note's YAML frontmatter (replace-or-append per key)."""
    if not patch:
        return text
    m = _FRONTMATTER_RE.match(text)
    if not m:
        block = "".join(_yaml_render(k, v) for k, v in patch.items())
        return f"---\n{block}---\n\n{text.lstrip()}"

    body = m.group(1)
    if not body.endswith("\n"):
        body += "\n"

    last_key = next(iter(reversed(patch))) if patch else None
    insert_anchor = re.search(rf"(?m)^{re.escape(last_key)}:", body) if last_key else None
    for k in patch:
        body = _strip_yaml_key(body, k)
    appended = "".join(_yaml_render(k, v) for k, v in patch.items())
    if insert_anchor:
        body = body.rstrip() + "\n" + appended
    else:
        body = body.rstrip() + "\n" + appended
    return f"---\n{body}---\n" + text[m.end():]


_LEGACY_SECTION_RE = re.compile(
    r"(?ms)^## Papers with Code\s*\n.*?(?=^## |\Z)"
)
_CALLOUT_BLOCK_RE = re.compile(
    r"(?ms)^> \[!abstract\] TL;DR \(Papers with Code\)\s*\n(?:>.*\n)*"
)


def _inject_callout(text: str, callout: str) -> str:
    """Replace or insert the standalone callout between `## BibTeX` and `## AI Explanation`.

    Also removes any legacy `## Papers with Code` section left from earlier versions.
    """
    text = _LEGACY_SECTION_RE.sub("", text)

    if _CALLOUT_BLOCK_RE.search(text):
        if not callout.strip():
            return _CALLOUT_BLOCK_RE.sub("", text)
        return _CALLOUT_BLOCK_RE.sub(callout.rstrip() + "\n\n", text, count=1)

    if not callout.strip():
        return text

    ai_match = re.search(r"(?m)^## AI Explanation\b", text)
    if ai_match:
        idx = ai_match.start()
        return text[:idx].rstrip() + "\n\n" + callout.rstrip() + "\n\n" + text[idx:]

    related_match = re.search(r"(?m)^## Related Papers\b", text)
    if related_match:
        idx = related_match.start()
        return text[:idx].rstrip() + "\n\n" + callout.rstrip() + "\n\n" + text[idx:]

    return text.rstrip() + "\n\n" + callout.rstrip() + "\n"


def inject_into_note(note_path: Path, result: PwcResult) -> str:
    """Patch frontmatter and place the callout. Idempotent.

    Returns one of: "inserted", "replaced", "noop".
    """
    text = note_path.read_text()
    had_legacy = bool(_LEGACY_SECTION_RE.search(text) or _CALLOUT_BLOCK_RE.search(text))

    text = _inject_frontmatter(text, _frontmatter_patch(result))
    text = _inject_callout(text, render_callout(result))

    note_path.write_text(text)

    if not result.found and not had_legacy:
        return "noop"
    return "replaced" if had_legacy else "inserted"


def _normalize_arxiv_id(raw: str) -> str:
    """Accept 2106.09685, arXiv:2106.09685v3, full URLs (arxiv.org, paperswithcode.co)."""
    m = ARXIV_ID_RE.search(raw)
    if not m:
        raise SystemExit(f"could not extract arxiv id from: {raw!r}")
    return m.group(1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--arxiv", required=True, help="arXiv ID or any URL containing it")
    parser.add_argument(
        "--format",
        choices=("json", "md"),
        default="json",
        help="output format when not using --inject (default: json)",
    )
    parser.add_argument(
        "--inject",
        type=Path,
        default=None,
        help="path to an Obsidian .md note; insert/replace the PwC section in place",
    )
    parser.add_argument("--no-cache", action="store_true", help="skip on-disk cache, force refetch")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    arxiv_id = _normalize_arxiv_id(args.arxiv)
    result = fetch(arxiv_id, use_cache=not args.no_cache)

    if args.inject is not None:
        if not args.inject.exists():
            raise SystemExit(f"note not found: {args.inject}")
        outcome = inject_into_note(args.inject, result)
        report = {
            "arxiv_id": arxiv_id,
            "found": result.found,
            "outcome": outcome,
            "frontmatter_patch": _frontmatter_patch(result),
            "note": str(args.inject),
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if args.format == "json":
        print(json.dumps({"arxiv_id": arxiv_id, "found": result.found, "data": result.data},
                         ensure_ascii=False, indent=2))
    else:
        out = render_callout(result)
        if not out:
            logger.info("no PwC callout to render for %s", arxiv_id)
        else:
            print(out)
            patch = _frontmatter_patch(result)
            if patch:
                print("# frontmatter patch:")
                print("".join(_yaml_render(k, v) for k, v in patch.items()), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
