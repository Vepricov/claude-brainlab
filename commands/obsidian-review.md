---
name: obsidian-review
description: Generate a literature review and project-linked synthesis from paper notes already stored in the Obsidian project knowledge base
args:
  - name: query
    description: Optional folder or filter target within the project knowledge base. Defaults to Papers/.
    required: false
  - name: depth
    description: Analysis depth (quick/deep). Default: deep.
    required: false
    default: deep
tags: [Research, Obsidian, Literature Review, Synthesis]
---

# /obsidian-review - Project Literature Synthesis

Create a project-linked literature review from the current Obsidian knowledge base.

## Workflow

1. Resolve the bound project and locate `Papers/`, the relevant `Knowledge/` notes, and `Writing/` only when a prose deliverable is requested.
2. Read note content directly from the filesystem.
3. Query narrowly first:
   - read the relevant paper notes,
   - then the most relevant canonical project notes,
   - only then synthesize across them.
4. Group papers by research question, method family, finding, or project relevance.
5. Generate or update:
   - `Knowledge/Literature-Overview.md`
   - `Knowledge/Method-Families.md` when useful
   - `Knowledge/Research-Gaps.md` when useful
   - `Writing/literature-review.md` or `Writing/comparison-matrix.md` only when needed
6. Refresh `Maps/literature.canvas`.
7. Link the synthesis back to key paper and knowledge notes.
8. Record the synthesis in today's daily note and project memory.
9. In the final response, provide the updated note paths and optional Obsidian CLI / URI shortcuts.

## Notes

- Prefer filesystem discovery over tags unless the repository already uses a stable tag taxonomy.
- This command is part of the project knowledge base, not a separate API-based Obsidian integration.
- Refresh `Maps/literature.canvas` by default after substantial literature-note changes.
