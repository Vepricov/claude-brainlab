#!/usr/bin/env python3
"""render_config.py — config rendering helpers shared by the installers.

Subcommands (all read substitution values from environment variables):
  expand           Expand ${VAR} placeholders in files installed to ~/.claude
  render-settings  Render settings.json from settings.json.template
  projects-json    Write ~/.claude/obsidian-projects.json from *_ROOT env vars

Called by install/setup-windows.ps1 (and usable from setup.sh). Values come
from .env, exported by the calling script before invoking this helper.

NOTE on mcpServers: neither the Claude Code CLI nor the desktop app reads
`mcpServers` from ~/.claude/settings.json. MCP servers must be registered
with `claude mcp add -s user ...`, which writes ~/.claude.json. Therefore
`render-settings --strip-mcp-servers` (the default for Windows installs)
removes that block from the rendered settings.json to avoid a decoy config.
"""

import argparse
import json
import os
import pathlib
import re
import sys
from typing import Dict

PLACEHOLDER = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)\}")

EXPAND_ROOTS = ["skills", "commands", "agents", "hooks", "scripts", "rules"]
EXPAND_EXTS = {".md", ".py", ".sh", ".js", ".json", ".yaml", ".yml", ".txt"}
EXPAND_KEYS = [
    "OBSIDIAN_VAULT", "VAULT_NAME", "UNPAYWALL_EMAIL", "USER_EMAIL",
    "PAPERS_ROOT", "PROJECTS_ROOT", "STAFF_ROOT", "PYTHON_BIN", "HOME",
]


def _subs() -> Dict[str, str]:
    return {k: os.environ.get(k, "") for k in EXPAND_KEYS}


def cmd_expand(args: argparse.Namespace) -> int:
    """Expand ${VAR} placeholders in text files under ~/.claude components."""
    home = pathlib.Path(args.claude_home)
    subs = _subs()

    def rep(m: re.Match) -> str:
        v = subs.get(m.group(1))
        return v if v else m.group(0)

    n_files = n_subs = 0
    for root in EXPAND_ROOTS:
        base = home / root
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix not in EXPAND_EXTS:
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            new, k = PLACEHOLDER.subn(rep, text)
            if k:
                p.write_text(new, encoding="utf-8")
                n_files += 1
                n_subs += k
    print(f"  expanded placeholders: {n_files} files, {n_subs} substitutions")
    return 0


def _strip_comments(obj):
    if isinstance(obj, dict):
        return {k: _strip_comments(v) for k, v in obj.items()
                if not k.startswith("_")}
    if isinstance(obj, list):
        return [_strip_comments(x) for x in obj]
    return obj


def cmd_render_settings(args: argparse.Namespace) -> int:
    """Render settings.json from the template with env substitution."""
    text = pathlib.Path(args.template).read_text(encoding="utf-8")

    def sub(m: re.Match) -> str:
        v = os.environ.get(m.group(1))
        if v is None:
            return m.group(0)
        # Backslashes (Windows paths in .env, or MSYS-converted $HOME) would
        # be invalid JSON escapes; forward slashes work everywhere.
        return v.replace("\\", "/")

    text = PLACEHOLDER.sub(sub, text)
    data = _strip_comments(json.loads(text))

    if args.strip_mcp_servers:
        # See module docstring: settings.json mcpServers is a decoy.
        data.pop("mcpServers", None)
    elif not os.environ.get("ZOTERO_API_KEY"):
        data.get("mcpServers", {}).pop("zotero", None)

    out = pathlib.Path(args.output)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"  rendered {out}")
    return 0


def cmd_projects_json(args: argparse.Namespace) -> int:
    """Write obsidian-projects.json mapping FS roots -> vault folders."""
    out = pathlib.Path(args.output)
    if out.exists() and not args.force:
        print(f"  [keep] {out} (exists; use --force to overwrite)")
        return 0
    roots = []
    for env_key, vault_folder in [("PAPERS_ROOT", "Papers"),
                                  ("PROJECTS_ROOT", "Projects"),
                                  ("STAFF_ROOT", "Staff")]:
        fs = os.environ.get(env_key, "")
        if fs:
            roots.append({"fs": fs.replace("\\", "/"),
                          "obsidian": vault_folder, "items": {}})
    data = {"roots": roots}
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"  wrote {out} ({len(roots)} roots)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("expand", help="expand ${VAR} in installed files")
    p.add_argument("--claude-home", required=True)
    p.set_defaults(func=cmd_expand)

    p = sub.add_parser("render-settings", help="render settings.json")
    p.add_argument("--template", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--strip-mcp-servers", action="store_true",
                   help="drop mcpServers block (register via `claude mcp add`)")
    p.set_defaults(func=cmd_render_settings)

    p = sub.add_parser("projects-json", help="write obsidian-projects.json")
    p.add_argument("--output", required=True)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_projects_json)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
