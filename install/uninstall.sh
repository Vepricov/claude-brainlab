#!/usr/bin/env bash
# uninstall.sh — restore the most recent backup created by setup.sh.
#
# This rolls back claude-brainlab. It does NOT remove backups themselves.
# If no backup exists for a component, that component is removed.
#
# Usage:
#   bash install/uninstall.sh

set -euo pipefail

CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
BACKUP_ROOT="$CLAUDE_HOME/.claude-brainlab-backups"
MANIFEST="$CLAUDE_HOME/.claude-brainlab-manifest.txt"

if [[ ! -d "$BACKUP_ROOT" ]]; then
  echo "No backups found at $BACKUP_ROOT — nothing to roll back."
  exit 0
fi

LATEST_BACKUP="$(ls -1d "$BACKUP_ROOT"/*/ 2>/dev/null | sort | tail -n 1 | sed 's:/$::')"
if [[ -z "$LATEST_BACKUP" ]]; then
  echo "No backup snapshots in $BACKUP_ROOT."
  exit 0
fi

echo "Rolling back to: $LATEST_BACKUP"
read -r -p "Continue? [y/N]: " ans
case "$ans" in y|Y) ;; *) echo "Aborted."; exit 0 ;; esac

if [[ ! -f "$MANIFEST" ]]; then
  echo "WARN: manifest missing — restoring whatever is in the backup."
fi

# Restore each item that was backed up.
shopt -s dotglob nullglob
for item in "$LATEST_BACKUP"/*; do
  name="$(basename "$item")"
  target="$CLAUDE_HOME/$name"
  echo "  ↪ restore $name"
  rm -rf "$target"
  cp -R "$item" "$target"
done

# If we created a brand-new file (no prior backup), delete it.
COMPONENTS=(skills commands agents hooks scripts rules)
for c in "${COMPONENTS[@]}"; do
  if [[ ! -e "$LATEST_BACKUP/$c" && -d "$CLAUDE_HOME/$c" ]]; then
    # Heuristic: only remove if listed in the manifest — i.e. we installed it.
    if [[ -f "$MANIFEST" ]] && grep -qx "$CLAUDE_HOME/$c" "$MANIFEST"; then
      echo "  ↪ remove $c (was newly installed)"
      rm -rf "$CLAUDE_HOME/$c"
    fi
  fi
done

# Sidecar CLAUDE.brainlab.md: always remove on uninstall.
[[ -f "$CLAUDE_HOME/CLAUDE.brainlab.md" ]] && rm -f "$CLAUDE_HOME/CLAUDE.brainlab.md"

echo
echo "✓ Rolled back. Backup snapshot is preserved at $LATEST_BACKUP."
