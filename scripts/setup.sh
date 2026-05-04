#!/usr/bin/env bash
set -euo pipefail

CLAUDE_DIR="$HOME/.claude"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPONENTS=(skills commands agents rules hooks scripts)
CLAUDE_MD_SIDECAR="CLAUDE.scholar.md"
CLAUDE_ZH_MD_SIDECAR="CLAUDE.zh-CN.scholar.md"
BACKUP_ROOT="$CLAUDE_DIR/.claude-scholar-backups"
BACKUP_STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/$BACKUP_STAMP"
BACKUP_READY=0
BACKUP_COUNT=0
UPDATED_COUNT=0
SKIPPED_COUNT=0

info()  { echo -e "\033[1;34m[INFO]\033[0m $*"; }
warn()  { echo -e "\033[1;33m[WARN]\033[0m $*"; }
error() { echo -e "\033[1;31m[ERROR]\033[0m $*"; exit 1; }

check_deps() {
  command -v git  >/dev/null || error "Git is required. Install it first."
  command -v node >/dev/null || error "Node.js is required (hooks depend on it). Install it first."
}

ensure_backup_dir() {
  if [ "$BACKUP_READY" -eq 0 ]; then
    mkdir -p "$BACKUP_DIR"
    BACKUP_READY=1
    info "Backup directory: $BACKUP_DIR"
  fi
}

backup_path() {
  local target="$1"
  [ -e "$target" ] || return 0

  ensure_backup_dir

  local rel="${target#$CLAUDE_DIR/}"
  if [ "$rel" = "$target" ]; then
    rel="$(basename "$target")"
  fi

  mkdir -p "$BACKUP_DIR/$(dirname "$rel")"
  if [ -d "$target" ]; then
    cp -R "$target" "$BACKUP_DIR/$rel"
  else
    cp -p "$target" "$BACKUP_DIR/$rel"
  fi
  BACKUP_COUNT=$((BACKUP_COUNT + 1))
}

# Create settings.json from template
create_settings() {
  local template="$1/settings.json.template"
  local target="$CLAUDE_DIR/settings.json"
  if [ -f "$template" ] && [ ! -f "$target" ]; then
    cp "$template" "$target"
    info "Created settings.json from template."
    info "  → Edit $target to add your GITHUB_PERSONAL_ACCESS_TOKEN (optional)."
  fi
}

# Merge hooks, mcpServers, enabledPlugins from template into existing settings.json
merge_settings() {
  local template="$1/settings.json.template"
  local target="$CLAUDE_DIR/settings.json"

  [ -f "$template" ] || return 0
  [ -f "$target" ]   || { create_settings "$1"; return 0; }

  # Backup
  backup_path "$target"
  cp "$target" "${target}.bak"
  info "Backed up settings.json → settings.json.bak"

  # Merge hooks, mcpServers, enabledPlugins while preserving user env/model/API key settings.
  CLAUDE_SETTINGS_TARGET="$target" CLAUDE_SETTINGS_TEMPLATE="$template" node <<'NODE'
const fs = require('fs');

const targetPath = process.env.CLAUDE_SETTINGS_TARGET;
const templatePath = process.env.CLAUDE_SETTINGS_TEMPLATE;
const existing = JSON.parse(fs.readFileSync(targetPath, 'utf8'));
const template = JSON.parse(fs.readFileSync(templatePath, 'utf8'));

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function mergeMissing(existingValue, templateValue) {
  if (existingValue === undefined) return clone(templateValue);
  if (templateValue === null || Array.isArray(templateValue) || typeof templateValue !== 'object') {
    return existingValue;
  }

  const output = { ...existingValue };
  for (const [key, value] of Object.entries(templateValue)) {
    if (!(key in output)) {
      output[key] = clone(value);
      continue;
    }
    if (
      output[key] &&
      value &&
      !Array.isArray(output[key]) &&
      !Array.isArray(value) &&
      typeof output[key] === 'object' &&
      typeof value === 'object'
    ) {
      output[key] = mergeMissing(output[key], value);
    }
  }
  return output;
}

function mergeHooks(existingHooks, templateHooks) {
  const output = existingHooks ? clone(existingHooks) : {};
  for (const [eventName, templateMatchers] of Object.entries(templateHooks || {})) {
    const existingMatchers = Array.isArray(output[eventName]) ? output[eventName] : [];
    for (const templateMatcher of templateMatchers) {
      const matchValue = templateMatcher.matcher || '*';
      let existingMatcher = existingMatchers.find((item) => (item.matcher || '*') === matchValue);
      if (!existingMatcher) {
        existingMatchers.push(clone(templateMatcher));
        continue;
      }

      existingMatcher.hooks = Array.isArray(existingMatcher.hooks) ? existingMatcher.hooks : [];
      const seen = new Set(
        existingMatcher.hooks.map((hook) =>
          JSON.stringify({
            type: hook.type || '',
            command: hook.command || '',
            timeout: hook.timeout ?? null,
          }),
        ),
      );

      for (const hook of templateMatcher.hooks || []) {
        const signature = JSON.stringify({
          type: hook.type || '',
          command: hook.command || '',
          timeout: hook.timeout ?? null,
        });
        if (!seen.has(signature)) {
          existingMatcher.hooks.push(clone(hook));
          seen.add(signature);
        }
      }
    }
    output[eventName] = existingMatchers;
  }
  return output;
}

existing.hooks = mergeHooks(existing.hooks, template.hooks);

if (template.mcpServers) {
  existing.mcpServers = existing.mcpServers || {};
  for (const [key, value] of Object.entries(template.mcpServers)) {
    existing.mcpServers[key] = mergeMissing(existing.mcpServers[key], value);
  }
}

if (template.enabledPlugins) {
  existing.enabledPlugins = existing.enabledPlugins || {};
  for (const [key, value] of Object.entries(template.enabledPlugins)) {
    if (!(key in existing.enabledPlugins)) existing.enabledPlugins[key] = value;
  }
}

fs.writeFileSync(targetPath, JSON.stringify(existing, null, 2) + '\n');
NODE

  local merge_status=$?
  if [ "$merge_status" -ne 0 ]; then
    warn "Auto-merge failed. Please manually copy settings from settings.json.template."
    return 0
  fi

  info "Merged hooks/mcpServers/enabledPlugins into settings.json without touching env/model/API key fields."
}

# Copy one file with backup-aware overwrite
copy_file_safely() {
  local src_file="$1"
  local target_file="$2"

  mkdir -p "$(dirname "$target_file")"

  if [ -f "$target_file" ] && cmp -s "$src_file" "$target_file"; then
    SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
    return 0
  fi

  if [ -e "$target_file" ]; then
    backup_path "$target_file"
    [ -d "$target_file" ] && rm -rf "$target_file"
  fi

  cp -p "$src_file" "$target_file"
  UPDATED_COUNT=$((UPDATED_COUNT + 1))
}

# Copy component directories with per-file backup
copy_dir_safely() {
  local src_dir="$1"
  local target_dir="$2"

  if [ -e "$target_dir" ] && [ ! -d "$target_dir" ]; then
    backup_path "$target_dir"
    rm -f "$target_dir"
  fi
  mkdir -p "$target_dir"

  while IFS= read -r -d '' src_file; do
    local rel="${src_file#$src_dir/}"
    local target_file="$target_dir/$rel"
    copy_file_safely "$src_file" "$target_file"
  done < <(find "$src_dir" -type f -print0)
}

install_claude_md() {
  local src_file="$1"
  local target_file="$CLAUDE_DIR/CLAUDE.md"
  local sidecar_file="$CLAUDE_DIR/$CLAUDE_MD_SIDECAR"

  if [ -f "$target_file" ]; then
    warn "Preserving existing CLAUDE.md"
    copy_file_safely "$src_file" "$sidecar_file"
    info "Installed repository CLAUDE.md as $CLAUDE_MD_SIDECAR"
    return 0
  fi

  copy_file_safely "$src_file" "$target_file"
}

install_claude_zh_md() {
  local src_file="$1"
  local target_file="$CLAUDE_DIR/CLAUDE.zh-CN.md"
  local sidecar_file="$CLAUDE_DIR/$CLAUDE_ZH_MD_SIDECAR"

  if [ -f "$target_file" ]; then
    warn "Preserving existing CLAUDE.zh-CN.md"
    copy_file_safely "$src_file" "$sidecar_file"
    info "Installed repository CLAUDE.zh-CN.md as $CLAUDE_ZH_MD_SIDECAR"
    return 0
  fi

  copy_file_safely "$src_file" "$target_file"
}

copy_components() {
  local src="$1"

  if [ -f "$src/CLAUDE.md" ]; then
    install_claude_md "$src/CLAUDE.md"
  fi

  if [ -f "$src/CLAUDE.zh-CN.md" ]; then
    install_claude_zh_md "$src/CLAUDE.zh-CN.md"
  fi

  for comp in "${COMPONENTS[@]}"; do
    if [ -e "$src/$comp" ]; then
      if [ -d "$src/$comp" ]; then
        copy_dir_safely "$src/$comp" "$CLAUDE_DIR/$comp"
      else
        copy_file_safely "$src/$comp" "$CLAUDE_DIR/$comp"
      fi
    fi
  done
  info "Updated components: ${COMPONENTS[*]}"
}

main() {
  echo ""
  echo "╔══════════════════════════════════════╗"
  echo "║       Claude Scholar Installer       ║"
  echo "╚══════════════════════════════════════╝"
  echo ""

  check_deps

  info "Installing from: $SRC_DIR"
  copy_components "$SRC_DIR"
  merge_settings "$SRC_DIR"
  info "Your existing env/model/API key/permissions settings are preserved."
  info "Updated files: $UPDATED_COUNT | Unchanged files skipped: $SKIPPED_COUNT | Backups created: $BACKUP_COUNT"
  if [ "$BACKUP_READY" -eq 1 ]; then
    info "Recover previous files from: $BACKUP_DIR"
  fi

  echo ""
  info "Done! Restart Claude Code CLI to activate."
  echo ""
}

main "$@"
