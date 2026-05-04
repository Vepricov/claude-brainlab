---
name: obsidian-project
description: Manage an Obsidian project knowledge base lifecycle for the current repository: detach, archive, purge, or rebuild
args:
  - name: action
    description: Lifecycle action (detach/archive/purge/rebuild). Default: archive when the user asks to remove project knowledge.
    required: true
tags: [Research, Obsidian, Lifecycle, Archive]
---

# /obsidian-project - Project Knowledge Lifecycle

Manage the lifecycle of the current project's Obsidian knowledge base.

## Actions

- `detach` — stop syncing, keep vault knowledge
- `archive` — move the project to `Archive/` and disable syncing
- `purge` — permanently delete the project binding, memory, and vault knowledge
- `rebuild` — bootstrap again from the current repository

## Workflow

### Detach / Archive / Purge

Run:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/obsidian-project-memory/scripts/project_kb.py" lifecycle --cwd "$PWD" --mode "$action"
```

### Rebuild

Use `/obsidian-init` or rerun the bootstrap helper with `--force`.

## Final response requirements

- Report the affected binding and note/vault paths.
- For archive or rebuild, include the new destination path.
- When helpful, include optional `obsidian://open` or `obsidian open` suggestions.

## Safety

- Treat “remove this project's knowledge” as `archive` unless the user explicitly requests permanent deletion.
- Require explicit confirmation semantics for `purge` in the response.
