#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_VAULT_DEFAULT="$REPO_ROOT/obsidian-vault"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/sync_obsidian_to_windows.sh --windows-path /mnt/c/Users/<You>/Documents/Obsidian/claude-scholar-vault

Options:
  --windows-path PATH   Windows-local vault path mounted in WSL, e.g. /mnt/c/Users/Alice/Documents/Obsidian/claude-scholar-vault
  --source-path PATH    Source vault path inside WSL. Default: ./obsidian-vault
  --dry-run             Show what would change without copying
  --no-delete           Do not delete files in the Windows mirror that no longer exist in the source
  -h, --help            Show this help

Notes:
  - Use a Windows-local path under /mnt/<drive>/... as the mirror target.
  - Open the mirrored target directory with Windows Obsidian, not the WSL path.
  - This script treats the WSL vault as the source of truth.
EOF
}

WINDOWS_PATH=""
SOURCE_PATH="$SOURCE_VAULT_DEFAULT"
DRY_RUN=0
DELETE_MODE=1

while [ "$#" -gt 0 ]; do
  case "$1" in
    --windows-path)
      WINDOWS_PATH="${2:-}"
      shift 2
      ;;
    --source-path)
      SOURCE_PATH="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --no-delete)
      DELETE_MODE=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [ -z "$WINDOWS_PATH" ]; then
  echo "Missing required --windows-path" >&2
  usage >&2
  exit 1
fi

if ! command -v rsync >/dev/null 2>&1; then
  echo "rsync is required but not installed." >&2
  exit 1
fi

SOURCE_PATH="$(realpath "$SOURCE_PATH")"
WINDOWS_PATH="$(realpath -m "$WINDOWS_PATH")"

if [ ! -d "$SOURCE_PATH" ]; then
  echo "Source vault does not exist: $SOURCE_PATH" >&2
  exit 1
fi

case "$WINDOWS_PATH" in
  /mnt/[a-zA-Z]/*) ;;
  *)
    echo "Target must be a Windows-local path mounted in WSL, for example /mnt/c/Users/<You>/Documents/Obsidian/claude-scholar-vault" >&2
    echo "Received: $WINDOWS_PATH" >&2
    exit 1
    ;;
esac

mkdir -p "$WINDOWS_PATH"

RSYNC_ARGS=(-a --info=stats2,progress2)

if [ "$DELETE_MODE" -eq 1 ]; then
  RSYNC_ARGS+=(--delete)
fi

if [ "$DRY_RUN" -eq 1 ]; then
  RSYNC_ARGS+=(--dry-run)
fi

echo "Source vault : $SOURCE_PATH"
echo "Windows copy : $WINDOWS_PATH"
echo "Delete extra : $DELETE_MODE"
echo "Dry run      : $DRY_RUN"

rsync "${RSYNC_ARGS[@]}" "$SOURCE_PATH"/ "$WINDOWS_PATH"/

echo
echo "Done."
echo "Open this directory with Windows Obsidian:"
echo "  $WINDOWS_PATH"
