#!/usr/bin/env python3
"""
Obsidian daily note sync — Claude Code Stop hook.
Reads project registry from ~/.claude/obsidian-projects.json.
Maps cwd → root (Papers/Projects/Staff) → slug → Obsidian <root>/<slug>/Daily/YYYY-MM-DD.md
Falls back to general/ if cwd is not under any known root.
"""
import json
import sys
import os
from datetime import datetime
from pathlib import Path

CONFIG_PATH = Path.home() / ".claude/obsidian-projects.json"


def load_config():
    if not CONFIG_PATH.exists():
        return None
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    vault = Path(cfg["vault"].replace("~", str(Path.home())))
    general_slug = cfg.get("general_slug", "general")
    general_root = cfg.get("general_root", "")

    roots = []
    for r in cfg.get("roots", []):
        fs_path = Path(r["fs"].replace("~", str(Path.home())))
        roots.append({
            "fs": fs_path,
            "obsidian": r["obsidian"],
            "items": r.get("items", {}),
        })

    return {
        "vault": vault,
        "general_slug": general_slug,
        "general_root": general_root,
        "roots": roots,
    }


def get_location(cwd: str, cfg: dict) -> tuple[str, str]:
    """Return (slug, obsidian_folder) for the given cwd.
    Falls back to (general_slug, general_root) if no root matches.
    """
    p = Path(cwd).resolve()
    for root in cfg["roots"]:
        try:
            rel = p.relative_to(root["fs"].resolve())
            folder = rel.parts[0] if rel.parts else None
            if folder:
                items = root["items"]
                slug = items.get(folder) or folder.lower().replace("_", "-").replace(" ", "-")
                return slug, root["obsidian"]
        except ValueError:
            continue
    return cfg["general_slug"], cfg.get("general_root", "")


def extract_last_exchange(transcript_path: str) -> tuple[str, str]:
    if not transcript_path or not os.path.exists(transcript_path):
        return "", ""
    try:
        with open(transcript_path) as f:
            msgs = [json.loads(l) for l in f if l.strip()]
    except Exception:
        return "", ""

    last_human = last_assistant = ""
    for msg in reversed(msgs):
        t = msg.get("type", "")
        content = msg.get("message", {}).get("content", "")

        if not last_assistant and t == "assistant":
            if isinstance(content, list):
                texts = [c["text"] for c in content if isinstance(c, dict) and c.get("type") == "text"]
                last_assistant = " ".join(texts)
            elif isinstance(content, str):
                last_assistant = content

        if not last_human and t == "user":
            if isinstance(content, str) and content.strip():
                last_human = content
            elif isinstance(content, list):
                texts = [c["text"] for c in content if isinstance(c, dict) and c.get("type") == "text"]
                if texts:
                    last_human = texts[0]

        if last_human and last_assistant:
            break

    return last_human[:300].strip(), last_assistant[:500].strip()


def write_daily(project_dir: Path, human: str, assistant: str):
    today = datetime.now().strftime("%Y-%m-%d")
    now_str = datetime.now().strftime("%H:%M")
    slug = project_dir.name

    daily_dir = project_dir / "Daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    daily_file = daily_dir / f"{today}.md"

    if not daily_file.exists():
        daily_file.write_text(f"---\ndate: {today}\nproject: {slug}\n---\n# {today}\n\n")

    parts = [f"\n## {now_str}"]
    if human:
        parts.append(f"**Task**: {human}")
    if assistant:
        parts.append(f"**Done**: {assistant}")
    parts.append("")

    with open(daily_file, "a") as f:
        f.write("\n".join(parts) + "\n")


def main():
    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        data = {}

    if data.get("stop_hook_active"):
        sys.exit(0)

    cfg = load_config()
    if not cfg:
        sys.exit(0)

    cwd = data.get("cwd", os.getcwd())
    slug, obsidian_folder = get_location(cwd, cfg)

    # Resolve project_dir
    if slug == cfg["general_slug"]:
        gr = cfg.get("general_root", "")
        project_dir = cfg["vault"] / gr / slug if gr else cfg["vault"] / slug
    else:
        project_dir = cfg["vault"] / obsidian_folder / slug

    if not project_dir.exists():
        sys.exit(0)

    human, assistant = extract_last_exchange(data.get("transcript_path", ""))
    write_daily(project_dir, human, assistant)


if __name__ == "__main__":
    main()
