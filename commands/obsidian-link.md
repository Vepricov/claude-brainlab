---
name: obsidian-link
description: Repair or strengthen Obsidian wikilinks across canonical project notes without requiring canvas, bases, or extra concept/dataset trees
args:
  - name: scope
    description: Link scope (papers/experiments/results/writing/all). Default: all.
    required: false
    default: all
tags: [Research, Obsidian, Wikilinks, Canonical Notes]
---

# /obsidian-link - Repair Canonical Note Links

Use this command to strengthen cross-note navigation for the current project.

## Workflow

1. Resolve the bound project knowledge base.
2. Read only the relevant canonical notes for the requested scope:
   - `papers` -> `Papers/` plus linked `Knowledge/`, `Experiments/`, `Results/`
   - `experiments` -> `Experiments/` plus linked `Results/` and `01-Plan.md`
   - `results` -> `Results/` plus the corresponding `Experiments/`
   - `writing` -> `Writing/` plus the notes it cites
3. Prefer updating links inside existing canonical notes over creating new notes.
4. Add or repair meaningful wikilinks among:
   - `00-Hub.md`
   - `01-Plan.md`
   - `Knowledge/`
   - `Papers/`
   - `Experiments/`
   - `Results/`
   - `Writing/`
5. When deciding where a new reference belongs, first look for the best existing target note. If needed, use:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/obsidian-project-memory/scripts/project_kb.py" find-canonical-note --cwd "$PWD" --kind experiment --query "freezing"
   ```
6. Record any meaningful link repair in today's daily note and project memory.
7. In the final response, list the affected note paths and optional `obsidian://open` or `obsidian open` shortcuts.

## Notes

- This command repairs navigation and canonical cross-references; it does not rebuild `.canvas` maps.
- Do not create `Concepts/` or `Datasets/` trees by default.
