#!/usr/bin/env bash
# setup.sh — backup-aware installer for claude-brainlab.
#
# Copies skills/, commands/, agents/, hooks/, scripts/, rules/, CLAUDE.md
# into ~/.claude/. Existing user files that differ are backed up first to a
# timestamped folder. Renders settings.json from settings.json.template using
# values from .env.
#
# Run AFTER bash install/bootstrap.sh.
#
# Usage:
#   bash install/setup.sh           # install/update
#   bash install/setup.sh --dry-run # show what would change

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
ENV_FILE="$REPO_ROOT/.env"
TEMPLATE="$REPO_ROOT/settings.json.template"
TS="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$CLAUDE_HOME/.claude-brainlab-backups/$TS"
MANIFEST="$CLAUDE_HOME/.claude-brainlab-manifest.txt"

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
  echo "[dry-run] Showing planned changes only."
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: .env not found. Run install/bootstrap.sh first." >&2
  exit 1
fi

# ── Load .env ──
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

mkdir -p "$CLAUDE_HOME"

run() {
  if (( DRY_RUN )); then
    echo "[dry-run] $*"
  else
    eval "$@"
  fi
}

backup_if_exists() {
  local target="$1"
  if [[ -e "$target" ]]; then
    local rel="${target#$CLAUDE_HOME/}"
    local dest="$BACKUP_DIR/$rel"
    run "mkdir -p \"$(dirname "$dest")\""
    run "cp -R \"$target\" \"$dest\""
  fi
}

# ── Components to install ──
COMPONENTS=(skills commands agents hooks scripts rules)

echo "→ Installing claude-brainlab into $CLAUDE_HOME"
echo "  Backups will go to: $BACKUP_DIR"
echo

for c in "${COMPONENTS[@]}"; do
  src="$REPO_ROOT/$c"
  dst="$CLAUDE_HOME/$c"
  if [[ ! -d "$src" ]]; then
    echo "  [skip] $c (not in repo)"
    continue
  fi
  echo "  ↪ $c"
  backup_if_exists "$dst"
  # Use rsync so we merge instead of clobber.
  if command -v rsync >/dev/null 2>&1; then
    run "rsync -a \"$src/\" \"$dst/\""
  else
    run "rm -rf \"$dst\""
    run "cp -R \"$src\" \"$dst\""
  fi
done

# ── Substitute placeholders in installed text files ──
# Skills/scripts contain ${OBSIDIAN_VAULT}, ${VAULT_NAME}, ${UNPAYWALL_EMAIL}
# placeholders. Markdown is read literally by the agent, not by a shell, so we
# must expand these to real values at install time. Use the values from .env.
echo "  ↪ expanding placeholders in installed files"
if (( ! DRY_RUN )); then
  export CLAUDE_HOME
  "${PYTHON_BIN:-python3}" - <<'PYEOF'
import os, pathlib, re
home = pathlib.Path(os.environ["CLAUDE_HOME"])
roots = ["skills", "commands", "agents", "hooks", "scripts", "rules"]
exts = {".md", ".py", ".sh", ".js", ".json", ".yaml", ".yml", ".txt"}
keys = ["OBSIDIAN_VAULT", "VAULT_NAME", "UNPAYWALL_EMAIL", "USER_EMAIL",
        "PAPERS_ROOT", "PROJECTS_ROOT", "STAFF_ROOT", "PYTHON_BIN"]
subs = {k: os.environ.get(k, "") for k in keys}
pattern = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)\}")
def rep(m):
    v = subs.get(m.group(1))
    return v if v else m.group(0)
n_files = n_subs = 0
for root in roots:
    base = home / root
    if not base.exists(): continue
    for p in base.rglob("*"):
        if not p.is_file() or p.suffix not in exts: continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        new, k = pattern.subn(rep, text)
        if k:
            p.write_text(new, encoding="utf-8")
            n_files += 1
            n_subs  += k
print(f"    {n_files} files, {n_subs} substitutions")
PYEOF
fi

# ── CLAUDE.md ──
if [[ -f "$CLAUDE_HOME/CLAUDE.md" ]]; then
  echo "  ↪ CLAUDE.md → CLAUDE.brainlab.md (sidecar — your existing CLAUDE.md kept)"
  run "cp \"$REPO_ROOT/CLAUDE.md\" \"$CLAUDE_HOME/CLAUDE.brainlab.md\""
else
  echo "  ↪ CLAUDE.md (new)"
  run "cp \"$REPO_ROOT/CLAUDE.md\" \"$CLAUDE_HOME/CLAUDE.md\""
fi

# ── settings.json (render from template) ──
SETTINGS_DST="$CLAUDE_HOME/settings.json"
echo "  ↪ settings.json"
backup_if_exists "$SETTINGS_DST"

# Render template with envsubst-like substitution. Uses python because
# envsubst is not installed everywhere.
if (( ! DRY_RUN )); then
  "${PYTHON_BIN:-python3}" - "$TEMPLATE" "$SETTINGS_DST" <<'PYEOF'
import json, os, re, sys
src, dst = sys.argv[1], sys.argv[2]
with open(src) as f:
    text = f.read()
def sub(m):
    var = m.group(1)
    return os.environ.get(var, m.group(0))
text = re.sub(r"\$\{([A-Z_][A-Z0-9_]*)\}", sub, text)
data = json.loads(text)
def strip_comments(obj):
    if isinstance(obj, dict):
        return {k: strip_comments(v) for k, v in obj.items() if not k.startswith("_")}
    if isinstance(obj, list):
        return [strip_comments(x) for x in obj]
    return obj
data = strip_comments(data)
# Drop zotero MCP entry if no API key was provided.
if not os.environ.get("ZOTERO_API_KEY"):
    data.get("mcpServers", {}).pop("zotero", None)
with open(dst, "w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print(f"  rendered {dst}")
PYEOF
fi

# ── obsidian-projects.json ──
OPJ_DST="$CLAUDE_HOME/obsidian-projects.json"
if [[ ! -f "$OPJ_DST" ]]; then
  echo "  ↪ obsidian-projects.json (from example)"
  run "cp \"$REPO_ROOT/obsidian-projects.example.json\" \"$OPJ_DST\""
else
  echo "  [keep] obsidian-projects.json (yours)"
fi

# ── Manifest ──
if (( ! DRY_RUN )); then
  {
    echo "# claude-brainlab install manifest — $TS"
    for c in "${COMPONENTS[@]}"; do echo "$CLAUDE_HOME/$c"; done
    echo "$CLAUDE_HOME/settings.json"
    echo "$CLAUDE_HOME/CLAUDE.brainlab.md"
  } > "$MANIFEST"
fi

echo
echo "✓ Done."
[[ -d "$BACKUP_DIR" ]] && echo "  Old files backed up at: $BACKUP_DIR"
echo "  Restart Claude Code to pick up new settings."
echo
echo "Optional next steps:"
echo "  • Install MemPalace:  pip install mempalace && mempalace init"
echo "  • Edit obsidian-projects.json to map your project folders."
echo "  • To uninstall: bash install/uninstall.sh"
