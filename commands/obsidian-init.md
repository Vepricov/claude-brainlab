---
name: obsidian-init
description: Bootstrap an Obsidian project knowledge base for the current research repository, either as a fresh project or by importing an existing code plus Markdown folder
args:
  - name: project
    description: Project name or topic. Defaults to the current repository name when omitted.
    required: false
  - name: vault_path
    description: Absolute Obsidian vault path. Defaults to OBSIDIAN_VAULT_PATH.
    required: false
  - name: mode
    description: Bootstrap mode (auto/new/import). Default: auto.
    required: false
    default: auto
tags: [Research, Obsidian, Project Knowledge Base, Bootstrap]
---

# /obsidian-init - Obsidian Project Knowledge Base Bootstrap

Create or import a research project knowledge base for the current repository.

## Workflow

1. Resolve the repository root from the current working directory.
2. Resolve the vault path from `$vault_path` or `OBSIDIAN_VAULT_PATH`.
3. Run the helper script from `skills/obsidian-project-memory/scripts/project_kb.py`:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/obsidian-project-memory/scripts/project_kb.py" bootstrap --cwd "$PWD" --vault-path "$vault_path"
   ```
   If `project` is provided, add `--project-name "$project"`.
4. Verify that the following exist:
   - `.claude/project-memory/registry.yaml`
   - `.claude/project-memory/<project_id>.md`
   - `Research/{project-slug}/00-Hub.md`
   - `Research/{project-slug}/01-Plan.md`
   - `Research/{project-slug}/Knowledge/Source-Inventory.md`
   - `Research/{project-slug}/Knowledge/Codebase-Overview.md`
5. If the imported project still lacks real background or experiment context, switch to an agent-first pass:
   - read the most informative repo docs and code entry points,
   - synthesize durable notes into `Knowledge/`, `Experiments/`, `Results/`, `Writing/`, or `Papers/`,
   - avoid generating placeholder notes.
6. In the final response, include:
   - the bound vault root,
   - the main created note paths,
   - optional `obsidian://open?...` links,
   - optional `obsidian open ...` suggestions when CLI is available.

## Notes

- This command never requires any Obsidian API service or API key.
- It imports structure and summaries, not raw datasets, caches, or checkpoints.
- If the current repo is already bound, prefer `/obsidian-sync` unless the user explicitly wants a rebuild.
- The current default workflow uses the compact vault structure; do not assume `Maps/`, `Views/`, `Concepts/`, or `Datasets/` exist before explicit generation.
