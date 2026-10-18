#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_ROOT="$(mktemp -d)"
trap 'rm -rf "$TEST_ROOT"' EXIT

make_fixture() {
  local fixture="$1"
  mkdir -p "$fixture/install" "$fixture/skills" "$fixture/commands" \
    "$fixture/agents" "$fixture/hooks" "$fixture/scripts" "$fixture/rules"
  cp "$REPO_ROOT/settings.json.template" "$fixture/settings.json.template"
  cp "$REPO_ROOT/install/setup.sh" "$fixture/install/setup.sh"
  : > "$fixture/CLAUDE.md"
}

make_legacy_fixture() {
  local fixture="$1"
  make_fixture "$fixture"
  cp "$REPO_ROOT/scripts/setup.sh" "$fixture/scripts/setup.sh"
}

assert_servers() {
  local settings="$1" expected="$2"
  python3 - "$settings" "$expected" <<'PY'
import json
import sys

settings_path, expected_csv = sys.argv[1:]
with open(settings_path, encoding="utf-8") as handle:
    settings = json.load(handle)

actual = sorted(settings.get("mcpServers", {}))
expected = sorted(filter(None, expected_csv.split(",")))
if actual != expected:
    raise SystemExit(f"expected MCP servers {expected}, got {actual}")
PY
}

fixture="$TEST_ROOT/full"
home="$TEST_ROOT/full-home"
make_fixture "$fixture"
cat > "$fixture/.env" <<'EOF'
PYTHON_BIN="python3"
ZOTERO_API_KEY="zotero-test-secret"
ZOTERO_LIBRARY_ID="123"
UNPAYWALL_EMAIL="test@example.com"
PLANE_API_KEY="plane-test-secret"
PLANE_WORKSPACE_SLUG="brain-lab"
PLANE_BASE_URL="https://plane.example.test/api"
EOF

CLAUDE_HOME="$home" bash "$fixture/install/setup.sh" >/dev/null
assert_servers "$home/settings.json" "mempalace,plane,zotero"

python3 - "$home/settings.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    servers = json.load(handle)["mcpServers"]

assert "lab-knowledge" not in servers
assert servers["plane"] == {
    "command": "uvx",
    "args": ["plane-mcp-server", "stdio"],
    "env": {
        "PLANE_API_KEY": "plane-test-secret",
        "PLANE_WORKSPACE_SLUG": "brain-lab",
        "PLANE_BASE_URL": "https://plane.example.test/api",
    },
}
PY

fixture="$TEST_ROOT/incomplete"
home="$TEST_ROOT/incomplete-home"
make_fixture "$fixture"
cat > "$fixture/.env" <<'EOF'
PYTHON_BIN="python3"
ZOTERO_API_KEY=""
PLANE_API_KEY="plane-test-secret"
PLANE_WORKSPACE_SLUG=""
PLANE_BASE_URL="https://api.plane.so"
EOF

CLAUDE_HOME="$home" bash "$fixture/install/setup.sh" >/dev/null
assert_servers "$home/settings.json" "mempalace"
if rg -q '\$\{PLANE_' "$home/settings.json"; then
  echo "optional MCP placeholders leaked into rendered settings" >&2
  exit 1
fi

fixture="$TEST_ROOT/legacy-full"
home="$TEST_ROOT/legacy-full-home"
make_legacy_fixture "$fixture"
cat > "$fixture/.env" <<'EOF'
PLANE_API_KEY="legacy-plane-test-secret"
PLANE_WORKSPACE_SLUG="legacy-brain-lab"
PLANE_BASE_URL="https://legacy-plane.example.test/api"
EOF

HOME="$home" bash "$fixture/scripts/setup.sh" >/dev/null
assert_servers "$home/.claude/settings.json" "mempalace,plane"
python3 - "$home/.claude/settings.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    servers = json.load(handle)["mcpServers"]

assert "lab-knowledge" not in servers
assert servers["plane"]["env"] == {
    "PLANE_API_KEY": "legacy-plane-test-secret",
    "PLANE_WORKSPACE_SLUG": "legacy-brain-lab",
    "PLANE_BASE_URL": "https://legacy-plane.example.test/api",
}
PY

# A legacy reinstall must rotate managed credentials, preserve unrelated MCP
# servers, and remove managed entries when their credentials are cleared.
python3 - "$home/.claude/settings.json" <<'PY'
import json
import sys

path = sys.argv[1]
with open(path, encoding="utf-8") as handle:
    settings = json.load(handle)
settings["mcpServers"]["user-custom"] = {
    "type": "http",
    "url": "https://custom.example.test/mcp",
}
with open(path, "w", encoding="utf-8") as handle:
    json.dump(settings, handle, indent=2)
PY

cat > "$fixture/.env" <<'EOF'
PLANE_API_KEY="rotated-plane-test-secret"
PLANE_WORKSPACE_SLUG="rotated-brain-lab"
PLANE_BASE_URL="https://rotated-plane.example.test/api"
EOF
HOME="$home" bash "$fixture/scripts/setup.sh" >/dev/null
assert_servers "$home/.claude/settings.json" "mempalace,plane,user-custom"
python3 - "$home/.claude/settings.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    servers = json.load(handle)["mcpServers"]
assert servers["plane"]["env"]["PLANE_API_KEY"] == "rotated-plane-test-secret"
assert servers["plane"]["env"]["PLANE_WORKSPACE_SLUG"] == "rotated-brain-lab"
assert servers["user-custom"]["url"] == "https://custom.example.test/mcp"
PY

cat > "$fixture/.env" <<'EOF'
PLANE_API_KEY=""
PLANE_WORKSPACE_SLUG=""
PLANE_BASE_URL="https://api.plane.so"
EOF
HOME="$home" bash "$fixture/scripts/setup.sh" >/dev/null
assert_servers "$home/.claude/settings.json" "mempalace,user-custom"

fixture="$TEST_ROOT/legacy-incomplete"
home="$TEST_ROOT/legacy-incomplete-home"
make_legacy_fixture "$fixture"
cat > "$fixture/.env" <<'EOF'
PLANE_API_KEY=""
PLANE_WORKSPACE_SLUG="legacy-brain-lab"
PLANE_BASE_URL="https://api.plane.so"
EOF

HOME="$home" bash "$fixture/scripts/setup.sh" >/dev/null
assert_servers "$home/.claude/settings.json" "mempalace"
if rg -q '\$\{PLANE_' "$home/.claude/settings.json"; then
  echo "optional MCP placeholders leaked into legacy-rendered settings" >&2
  exit 1
fi

echo "settings rendering tests passed"
