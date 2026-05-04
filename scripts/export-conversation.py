#!/usr/bin/env python3
"""
Export Claude session conversation to readable markdown.
Called from SessionEnd hook with JSON on stdin.
Saves to ~/.claude/logs/conversations/YYYY-MM-DD_<slug>.md
where <slug> is derived from the first real user message.
"""

import json
import subprocess
import re
import sys
import os
from pathlib import Path
from datetime import datetime


def extract_text(content) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                t = block.get("text", "").strip()
                if t:
                    parts.append(t)
        return "\n".join(parts)
    return ""


def skip_message(text: str, role: str) -> bool:
    """Filter out system noise."""
    if not text:
        return True
    if role == "user":
        if text.startswith("<"):
            return True
        if text.startswith("Please analyze this codebase"):
            return True
    if role == "assistant":
        if text.startswith("<function_calls>"):
            return True
    return False


def make_slug(text: str, max_words: int = 6) -> str:
    """Turn first N words of a message into a filename-safe slug."""
    # Strip markdown, punctuation
    text = re.sub(r"[`*_#\[\]()>]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    words = text.split()[:max_words]
    slug = "-".join(words).lower()
    # Keep only alphanumeric, hyphens, cyrillic
    slug = re.sub(r"[^\w\-]", "", slug, flags=re.UNICODE)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:60] if slug else "session"


def export_session(transcript_path: str, session_id: str, cwd: str):
    """Returns (content: str, slug: str) or (None, None)."""
    p = Path(transcript_path)
    if not p.exists():
        return None, None

    messages = []
    first_user_text = None

    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg = record.get("message", {})
            role = msg.get("role", "")
            if role not in ("user", "assistant"):
                continue

            text = extract_text(msg.get("content", ""))
            if skip_message(text, role):
                continue

            # Skip pure tool-result turns
            if role == "user" and isinstance(msg.get("content"), list):
                if all(
                    b.get("type") in ("tool_result", "tool_use")
                    for b in msg["content"]
                    if isinstance(b, dict)
                ):
                    continue

            if role == "user" and first_user_text is None and len(text) > 15:
                first_user_text = text

            messages.append((role, text))

    if not messages:
        return None, None

    slug = make_slug(first_user_text) if first_user_text else session_id[:8]

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d %H:%M")
    project = Path(cwd).name if cwd else "unknown"

    lines = [
        f"# {first_user_text[:80] if first_user_text else 'Session'} — {date_str}",
        f"",
        f"**Project**: `{project}` (`{cwd}`)",
        f"**Session**: `{session_id}`",
        f"",
        "---",
        "",
    ]

    for role, text in messages:
        if role == "user":
            lines.append(f"**You:** {text}")
        else:
            lines.append(f"**Claude:** {text}")
        lines.append("")

    return "\n".join(lines), slug


def sanitize_wing(project: str) -> str:
    wing = re.sub(r"[^\w.-]+", "_", project.strip(), flags=re.UNICODE)
    wing = wing.strip("._")
    return wing or "unknown"


def sync_to_mempalace(project: str, out_file: Path) -> None:
    """Stage the exported conversation into a project wing and mine it."""
    python_bin = Path("python3")
    if not python_bin.exists():
        return

    wing = sanitize_wing(project)
    stage_dir = (
        Path.home() / ".mempalace" / "staging" / "conversations_by_project" / wing
    )
    stage_dir.mkdir(parents=True, exist_ok=True)

    staged_file = stage_dir / out_file.name
    staged_file.write_text(out_file.read_text(encoding="utf-8"), encoding="utf-8")

    try:
        subprocess.run(
            [
                str(python_bin),
                "-m",
                "mempalace",
                "mine",
                str(stage_dir),
                "--mode",
                "convos",
                "--wing",
                wing,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=120,
            check=False,
        )
    except Exception:
        pass


def main():
    try:
        raw = sys.stdin.read().strip()
        hook_input = json.loads(raw) if raw else {}
    except Exception:
        hook_input = {}

    session_id = hook_input.get("session_id", "unknown")
    transcript_path = hook_input.get("transcript_path", "")
    cwd = hook_input.get("cwd", os.getcwd())
    project = Path(cwd).name if cwd else "unknown"

    # Fallback: find transcript by session_id
    if not transcript_path or not Path(transcript_path).exists():
        home = Path.home()
        project_key = cwd.replace("/", "-").lstrip("-")
        candidate = home / ".claude" / "projects" / project_key / f"{session_id}.jsonl"
        if candidate.exists():
            transcript_path = str(candidate)

    if not transcript_path:
        sys.exit(0)

    content, slug = export_session(transcript_path, session_id, cwd)
    if not content:
        sys.exit(0)

    out_dir = Path.home() / ".claude" / "logs" / "conversations"
    out_dir.mkdir(parents=True, exist_ok=True)

    date_prefix = datetime.now().strftime("%Y-%m-%d")
    out_file = out_dir / f"{date_prefix}_{slug}.md"

    # Avoid overwriting if slug collides (same day, same topic)
    counter = 1
    while out_file.exists():
        out_file = out_dir / f"{date_prefix}_{slug}_{counter}.md"
        counter += 1

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(content)

    sync_to_mempalace(project, out_file)

    # Clean up conversations older than 90 days
    cutoff = datetime.now().timestamp() - 90 * 24 * 3600
    for old in out_dir.glob("*.md"):
        if old.stat().st_mtime < cutoff:
            old.unlink(missing_ok=True)

    print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
