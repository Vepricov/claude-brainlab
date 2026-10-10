#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_ROOT="$(mktemp -d)"
trap 'rm -rf "$TEST_ROOT"' EXIT
TEST_PYTHON="$(command -v python3)"

for mode in compatible missing incompatible; do
  fixture="$TEST_ROOT/$mode/repo"
  test_home="$TEST_ROOT/$mode/user home"
  target="$test_home/custom claude"
  runtime="$test_home/.local/share/uv/tools/zotero-mcp-server"
  mkdir -p "$fixture/install" "$fixture/scripts" "$test_home"
  cp "$REPO_ROOT/install/setup.sh" "$fixture/install/setup.sh"
  cp "$REPO_ROOT/scripts/zotero_shared.py" "$fixture/scripts/zotero_shared.py"
  cp "$REPO_ROOT/settings.json.template" "$fixture/settings.json.template"
  printf '{}\n' > "$fixture/obsidian-projects.example.json"
  : > "$fixture/CLAUDE.md"
  printf 'PYTHON_BIN="%s"\nZOTERO_API_KEY="test-only"\n' "$TEST_PYTHON" > "$fixture/.env"
  if [[ "$mode" != missing ]]; then
    mkdir -p "$runtime/bin"
    # The installer must inspect files only, never import models or start a daemon.
    printf '#!/bin/sh\nexit 99\n' > "$runtime/bin/python"
    chmod +x "$runtime/bin/python"
    "$TEST_PYTHON" - "$runtime" "$mode" <<'PY'
from pathlib import Path
import sys
runtime, mode = Path(sys.argv[1]), sys.argv[2]
site = runtime / 'lib/python3.12/site-packages'
files = {
    'zotero_mcp/cli.py': 'def _warmup_reranker_in_background(): pass',
    'zotero_mcp/client.py': '_active_library_override = {}',
    'zotero_mcp/toolsets.py': 'def apply_toolsets(): pass',
    'fastmcp/server/http.py': 'class FastMCPStreamableHTTPSessionManager(Base): pass',
    'mcp/server/streamable_http_manager.py': 'session_idle_timeout; _server_instances; _session_owners',
}
for name, text in files.items():
    path = site / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if mode == 'compatible' else '')
PY
  fi
  HOME="$test_home" CLAUDE_HOME="$target" bash "$fixture/install/setup.sh" > "$TEST_ROOT/$mode.log"
  "$TEST_PYTHON" - "$target" "$runtime" "$mode" "$REPO_ROOT" <<'PY'
from pathlib import Path
import json, sys
target, runtime, mode, repo = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4])
zotero = json.loads((target / 'settings.json').read_text())['mcpServers']['zotero']
if mode == 'compatible':
    assert zotero['command'] == str(runtime / 'bin/python'), zotero
    assert zotero['args'] == [str(target / 'scripts/zotero_shared.py'), 'serve'], zotero
else:
    assert zotero['command'] == str(target.parent / '.local/bin/zotero-mcp'), zotero
    assert zotero['args'] == ['serve'], zotero
assert zotero['env']['ZOTERO_API_KEY'] == 'test-only'
assert (target / 'scripts/zotero_shared.py').read_bytes() == (repo / 'scripts/zotero_shared.py').read_bytes()
assert not (target.parent / '.local/bin/zotero-mcp').exists(), 'installer replaced a global launcher'
PY
  echo "$mode Zotero installation passed"
done
