#!/usr/bin/env bash
# One-shot Windows install: run setup from WSL, but render artifacts for
# native Windows Claude Code (C:/Users/... paths, Windows py.exe).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Detect the Windows home from inside WSL (override with WIN_USER_HOME env var).
if [[ -z "${WIN_USER_HOME:-}" ]]; then
  WIN_USER_HOME="$(cmd.exe /c 'echo %USERPROFILE%' 2>/dev/null | tr -d '\r' | sed 's#\\#/#g')"
fi
if [[ -z "$WIN_USER_HOME" ]]; then
  echo "ERROR: could not detect Windows home; set WIN_USER_HOME=C:/Users/<you>" >&2
  exit 1
fi
WIN_CLAUDE_MNT="/mnt/c/${WIN_USER_HOME#C:/}/.claude"

export CLAUDE_HOME="$WIN_CLAUDE_MNT"
# ${HOME} in settings.json.template must become the Windows home, not WSL's.
export HOME="$WIN_USER_HOME"

# Load .env (Windows PYTHON_BIN etc.) then force installer interpreter to WSL python.
set -a
# shellcheck disable=SC1091
source "$REPO_ROOT/.env"
set +a

INSTALLER_PY="/usr/bin/python3"
if [[ ! -x "$INSTALLER_PY" ]]; then
  echo "ERROR: need $INSTALLER_PY to run setup from WSL" >&2
  exit 1
fi

echo "→ Windows-targeted install"
echo "  CLAUDE_HOME=$CLAUDE_HOME"
echo "  HOME(for templates)=$HOME"
echo "  PYTHON_BIN(for artifacts)=$PYTHON_BIN"
echo "  installer python=$INSTALLER_PY"
echo

# Run setup, but rewrite its python invocations to use WSL python while
# keeping PYTHON_BIN from .env for placeholder/settings substitution.
# Patch a temp copy: fix interpreter + hardcode REPO_ROOT (temp file breaks BASH_SOURCE).
TMP_SETUP="$(mktemp)"
sed -E \
  -e "s#^REPO_ROOT=.*#REPO_ROOT=\"$REPO_ROOT\"#" \
  -e "s#\"\\\$\{PYTHON_BIN:-python3\}\"#\"$INSTALLER_PY\"#g" \
  "$REPO_ROOT/install/setup.sh" > "$TMP_SETUP"
chmod +x "$TMP_SETUP"
bash "$TMP_SETUP"
rm -f "$TMP_SETUP"

# Point obsidian-projects.json at the real Documents folders.
OPJ="$CLAUDE_HOME/obsidian-projects.json"
"$INSTALLER_PY" - "$OPJ" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
data = {
  "roots": [
    {"fs": "C:/Users/Роман/Documents/Papers", "obsidian": "Papers", "items": {}},
    {"fs": "C:/Users/Роман/Documents/Projects", "obsidian": "Projects", "items": {}},
    {"fs": "C:/Users/Роман/Documents/Staff", "obsidian": "Staff", "items": {}},
  ]
}
path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"  updated {path}")
PY

# Strip mcpServers from settings.json: neither the Claude Code CLI nor the
# desktop app reads MCP servers from there. Servers must be registered with
# `claude mcp add -s user ...` (writes ~/.claude.json). See docs/WINDOWS.md.
SETTINGS="$CLAUDE_HOME/settings.json"
"$INSTALLER_PY" - "$SETTINGS" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))
data.pop("mcpServers", None)
path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"  stripped decoy mcpServers from {path}")
PY

echo
echo "✓ Windows install complete → $CLAUDE_HOME"
echo "  Restart Claude Code to pick up new settings."
echo
echo "Now register the MCP servers (from Windows, not WSL):"
echo "  powershell -ExecutionPolicy Bypass -File install\\setup-windows.ps1 -McpOnly"
echo "or by hand:"
echo "  claude mcp add mempalace -s user -- $WIN_USER_HOME/.local/bin/mempalace-mcp.exe"
echo "  claude mcp add zotero -s user -e ZOTERO_LOCAL=true -e ZOTERO_LIBRARY_TYPE=user \\"
echo "    -e UNPAYWALL_EMAIL=${UNPAYWALL_EMAIL:-you@example.com} -e UNSAFE_OPERATIONS=all \\"
echo "    -- $WIN_USER_HOME/.local/bin/zotero-mcp.exe serve"
