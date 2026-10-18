#!/usr/bin/env python3
"""
PreToolUse hook: validates LaTeX citation keys against the project's references.bib.

Blocks Edit/Write to *.tex files when the change introduces a \\cite-style key
that does not appear as `@type{KEY,` in any references.bib reachable from the
edited file (walking up parent directories).

This enforces the global rule: never invent placeholder citation keys.
Citations must be resolved against the Obsidian library or paper-ingest
*before* writing them.
"""

import json
import os
import re
import sys
from pathlib import Path

CITE_CMDS = (
    "cite", "citep", "citet", "citeauthor", "citeyear",
    "citealt", "citealp", "citenum", "Citep", "Citet",
)
CITE_RE = re.compile(
    r"\\(?:" + "|".join(CITE_CMDS) + r")\*?\s*(?:\[[^\]]*\])?\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}"
)
BIB_KEY_RE = re.compile(r"^\s*@\w+\s*\{\s*([^,\s]+)\s*,", re.MULTILINE)


def read_stdin_json():
    try:
        data = sys.stdin.read()
        return json.loads(data) if data.strip() else {}
    except Exception:
        return {}


def strip_tex_comments(text: str) -> str:
    """Remove LaTeX comments (lines after unescaped %)."""
    out_lines = []
    for line in text.splitlines():
        stripped = []
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == "\\" and i + 1 < len(line):
                stripped.append(line[i:i + 2])
                i += 2
                continue
            if ch == "%":
                break
            stripped.append(ch)
            i += 1
        out_lines.append("".join(stripped))
    return "\n".join(out_lines)


def extract_keys(text: str) -> list[str]:
    keys = []
    for m in CITE_RE.finditer(text):
        for k in m.group(1).split(","):
            k = k.strip()
            if k:
                keys.append(k)
    return keys


def find_bib_files(start_dir: Path, max_up: int = 6) -> list[Path]:
    """Walk up from start_dir looking for *.bib files; also probe common subdirs."""
    bibs: list[Path] = []
    found: set[Path] = set()

    def _add(p: Path) -> None:
        rp = p.resolve()
        if rp not in found:
            found.add(rp)
            bibs.append(rp)

    cur = start_dir
    for _ in range(max_up):
        if not cur.exists():
            break
        for p in cur.glob("*.bib"):
            _add(p)
        for sub in ("paper", "papers", "tex", "manuscript"):
            d = cur / sub
            if d.is_dir():
                for p in d.glob("*.bib"):
                    _add(p)
        if cur.parent == cur:
            break
        cur = cur.parent
    return bibs


def collect_bib_keys(bib_files: list[Path]) -> set[str]:
    keys: set[str] = set()
    for bf in bib_files:
        try:
            text = bf.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in BIB_KEY_RE.finditer(text):
            keys.add(m.group(1).strip())
    return keys


def main() -> int:
    payload = read_stdin_json()
    tool = payload.get("tool_name", "")
    if tool not in ("Edit", "Write", "MultiEdit"):
        return 0

    tool_input = payload.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path") or ""
    if not file_path.endswith(".tex"):
        return 0

    if tool == "Edit":
        new_text = tool_input.get("new_string", "") or ""
        old_text = tool_input.get("old_string", "") or ""
    elif tool == "MultiEdit":
        edits = tool_input.get("edits", []) or []
        new_text = "\n".join(e.get("new_string", "") for e in edits)
        old_text = "\n".join(e.get("old_string", "") for e in edits)
    else:  # Write
        new_text = tool_input.get("content", "") or ""
        old_text = ""

    new_keys = set(extract_keys(strip_tex_comments(new_text)))
    if not new_keys:
        return 0
    old_keys = set(extract_keys(strip_tex_comments(old_text)))
    introduced = new_keys - old_keys
    if not introduced:
        return 0

    file_dir = Path(file_path).resolve().parent
    bib_files = find_bib_files(file_dir)
    if not bib_files:
        # No bib found — likely not a paper project; let it through.
        return 0

    bib_keys = collect_bib_keys(bib_files)
    missing = sorted(k for k in introduced if k not in bib_keys)
    if not missing:
        return 0

    bib_listing = ", ".join(str(p) for p in bib_files)
    msg = (
        "Citation validator BLOCKED this write.\n\n"
        f"File: {file_path}\n"
        f"Bibliography searched: {bib_listing}\n"
        f"Missing cite keys: {', '.join(missing)}\n\n"
        "Hard rule (from ~/.claude/CLAUDE.md, Literature & Citation Rules):\n"
        "  Never invent placeholder citation keys. Before writing \\cite{X}:\n"
        "    1. Search ~/brainlab/<direction>/<theme>/literature/ for the paper.\n"
        "    2. If found, copy the exact key from its `## BibTeX` block and\n"
        "       append the bibtex entry to references.bib first.\n"
        "    3. If not found, run the paper-ingest skill to add it, then cite.\n"
        "  Do not commit a `% TODO: add bibtex` placeholder.\n"
    )
    sys.stderr.write(msg)
    return 2


if __name__ == "__main__":
    sys.exit(main())
