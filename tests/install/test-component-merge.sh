#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_ROOT="$(mktemp -d)"
trap 'rm -rf "$TEST_ROOT"' EXIT
TEST_PYTHON="$(command -v python3)"
TEST_BASH="$(command -v bash)"
TEST_RSYNC="$(command -v rsync || true)"

check_merge() {
  local mode="$1"
  local fixture="$TEST_ROOT/$mode/repo"
  local target="$TEST_ROOT/$mode/claude"
  local tools="$TEST_ROOT/$mode/bin"
  local tool

  mkdir -p "$fixture/install" "$fixture/skills/managed/references" "$tools" \
    "$target/skills/personal" "$target/skills/managed"
  cp "$REPO_ROOT/install/setup.sh" "$fixture/install/setup.sh"
  : > "$fixture/CLAUDE.md"
  printf '{}\n' > "$fixture/settings.json.template"
  printf '{}\n' > "$fixture/obsidian-projects.example.json"
  printf 'PYTHON_BIN="%s"\n' "$TEST_PYTHON" > "$fixture/.env"
  printf 'new managed skill version 2\n' > "$fixture/skills/managed/SKILL.md"
  printf 'new resource\n' > "$fixture/skills/managed/references/guide.md"
  printf 'hidden resource\n' > "$fixture/skills/managed/.resource"
  printf 'old managed skill\n' > "$target/skills/managed/SKILL.md"
  printf 'personal skill\n' > "$target/skills/personal/SKILL.md"
  printf 'personal supplement\n' > "$target/skills/managed/personal.md"
  printf 'personal hidden file\n' > "$target/skills/.personal"

  # Exercise the actual installer with a PATH that cannot find rsync in the
  # fallback case. No real client configuration or credentials are loaded.
  for tool in dirname date mkdir cp rm; do
    ln -s "$(command -v "$tool")" "$tools/$tool"
  done
  if [[ "$mode" == "rsync" ]]; then
    ln -s "$TEST_RSYNC" "$tools/rsync"
  fi
  env -i PATH="$tools" TMPDIR="$TEST_ROOT" CLAUDE_HOME="$target" \
    "$TEST_BASH" "$fixture/install/setup.sh" > "$TEST_ROOT/$mode.log"

  "$TEST_PYTHON" - "$target" <<'PY'
from pathlib import Path
import sys

target = Path(sys.argv[1])
expected = {
    "skills/personal/SKILL.md": "personal skill\n",
    "skills/managed/personal.md": "personal supplement\n",
    "skills/.personal": "personal hidden file\n",
    "skills/managed/SKILL.md": "new managed skill version 2\n",
    "skills/managed/references/guide.md": "new resource\n",
    "skills/managed/.resource": "hidden resource\n",
}
for relative, text in expected.items():
    path = target / relative
    assert path.is_file(), f"installer lost or misplaced {relative}"
    assert path.read_text() == text, f"unexpected contents in {relative}"
backups = list((target / ".claude-brainlab-backups").glob("*/skills/managed/SKILL.md"))
assert len(backups) == 1, "missing pre-update backup"
assert backups[0].read_text() == "old managed skill\n"
PY
  echo "$mode component merge passed"
}

check_merge fallback
if [[ -n "$TEST_RSYNC" ]]; then
  check_merge rsync
else
  echo "rsync component merge skipped: rsync is not installed"
fi
