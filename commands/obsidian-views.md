---
name: obsidian-views
description: Generate optional Obsidian .base views and, when explicitly requested, project or experiments canvas files for the bound project knowledge base
args:
  - name: mode
    description: bases or all. Default: bases.
    required: false
    default: bases
tags: [Research, Obsidian, Bases, Canvas]
---

# /obsidian-views - Generate Optional Bases and Canvas Helpers

Generate optional project-facing `.base` and `.canvas` artifacts for the bound Obsidian knowledge base.

## Default stance

- `.base` is **explicitly enabled**, not a default artifact.
- `Maps/literature.canvas` remains the only default graph artifact in the literature workflow.
- `project.canvas` and `experiments.canvas` should be generated only on explicit request.

## Workflow

1. Resolve the bound project knowledge base.
2. Run:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/obsidian-project-memory/scripts/project_views.py" --cwd "$PWD"
   ```
3. If `mode=all`, run:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/obsidian-project-memory/scripts/project_views.py" --cwd "$PWD" --include-canvases
   ```
4. Verify outputs:
   - `Views/papers.base`
   - `Views/experiments.base`
   - `Views/results.base`
   - `Views/tasks.base`
5. If `mode=all`, also verify:
   - `Maps/project.canvas`
   - `Maps/experiments.canvas`

## Final response

Include:
- generated file paths
- reminder that these are optional helper surfaces
- optional Obsidian open/URI shortcuts
