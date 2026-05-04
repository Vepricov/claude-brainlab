---
name: obsidian-sync
description: Force a filesystem rescan or incremental repair sync between the current research repository, its project memory, and the bound Obsidian knowledge base
args:
  - name: scope
    description: Sync scope (auto/daily/plan/literature/experiments/results/all). Default: auto.
    required: false
    default: auto
tags: [Research, Obsidian, Sync, Repair]
---

# /obsidian-sync - Force Project Knowledge Sync

Use this command when you want to repair, rebuild, or force an incremental sync of the current project knowledge base.

## Workflow

1. Run project detection:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/obsidian-project-memory/scripts/project_kb.py" detect --cwd "$PWD"
   ```
2. If the project is unbound but is a research-project candidate, bootstrap it first.
3. Run the real filesystem sync helper:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/obsidian-project-memory/scripts/project_kb.py" sync --cwd "$PWD" --scope "$scope"
   ```
4. The helper will always refresh:
   - `Knowledge/Source-Inventory.md`
   - `Knowledge/Codebase-Overview.md`
   - today's `Daily/`
   - `00-Hub.md`
   - `.claude/project-memory/<project_id>.md`
5. Depending on `scope` and detected repo deltas, it will also refresh:
   - `plan` -> `01-Plan.md`, `Daily/Sync-Queue.md`
   - `experiments` -> `Archive/Auto-Sync/Experiments-Latest-Sync.md`
   - `results` -> `Archive/Auto-Sync/Results-Latest-Sync.md`
   - `literature` / `writing` -> `Writing/Literature-Sync.md`
6. Summarize what changed and include refreshed note paths plus optional Obsidian CLI/URI open suggestions.

## Notes

- Sync is deterministic state maintenance, not deep semantic synthesis.
- After sync, use agent-first review when a helper note should be promoted into a durable experiment, result, paper, or knowledge note.
- In a bound repo, this is the safest manual repair entrypoint for the minimum auto-maintenance surface: `Daily/`, `00-Hub.md`, and repo-local project memory.
