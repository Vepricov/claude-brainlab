#!/usr/bin/env python3
"""Register the configured Lab MCP through Claude's native user configuration."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def register(settings: Path, backup: Path) -> int:
    server = json.loads(settings.read_text(encoding="utf-8")).get("mcpServers", {}).get("lab-knowledge")
    if not server:
        return 0
    settings.chmod(0o600)
    cli = shutil.which("claude")
    if not cli:
        print("  Lab MCP: install Claude Code, then follow docs/onboarding.md to connect.")
        return 0
    default_home = Path.home() / ".claude"
    target = Path(os.environ.get("CLAUDE_HOME", str(default_home))).expanduser().resolve()
    explicit_config = os.environ.get("CLAUDE_CONFIG_DIR")
    env = dict(os.environ)
    if explicit_config:
        config = Path(explicit_config).expanduser() / ".claude.json"
    elif target != default_home.resolve():
        env["CLAUDE_CONFIG_DIR"] = str(target)
        config = target / ".claude.json"
    else:
        config = Path.home() / ".claude.json"
    original = json.loads(config.read_text(encoding="utf-8")) if config.exists() else {}
    if "lab-knowledge" in original.get("mcpServers", {}):
        print("  Lab MCP: existing client connection kept; update it manually if needed.")
        return 0
    if config.exists():
        backup.mkdir(parents=True, exist_ok=True, mode=0o700)
        saved = backup / "claude-user-config.json"
        shutil.copy2(config, saved)
        saved.chmod(0o600)
    try:
        completed = subprocess.run(
            [cli, "mcp", "add-json", "--scope", "user", "lab-knowledge", json.dumps(server)],
            env=env, capture_output=True, text=True, timeout=30, check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        # A timeout traceback includes command arguments and the personal key.
        print("  Lab MCP: native registration did not finish; see docs/onboarding.md.", file=sys.stderr)
        return 1
    # Native CLI output may contain credentials; report only our own status.
    if completed.returncode:
        print("  Lab MCP: native registration failed; see docs/onboarding.md.", file=sys.stderr)
        return 1
    updated = json.loads(config.read_text(encoding="utf-8"))
    if updated.get("mcpServers", {}).get("lab-knowledge") != server:
        print("  Lab MCP: native configuration read-back did not match.", file=sys.stderr)
        return 1
    config.chmod(0o600)
    print("  Lab MCP: registered in Claude Code; configuration read-back passed.")
    if not explicit_config and target != default_home.resolve():
        print("  Custom install: launch Claude with CLAUDE_CONFIG_DIR set to this install directory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(register(Path(sys.argv[1]), Path(sys.argv[2])))
