---
name: obsidian-notes
description: Normalize paper notes inside an Obsidian project knowledge base, enrich metadata, and connect them primarily to project knowledge plus the default literature canvas
args:
  - name: query
    description: Folder path or glob inside the project vault, defaulting to Papers/.
    required: false
  - name: format
    description: Note format (summary/detailed/comparison). Default: detailed.
    required: false
    default: detailed
tags: [Research, Obsidian, Reading Notes, Literature]
---

# /obsidian-notes - Normalize Project Paper Notes

Use this command to standardize paper notes inside the current Obsidian project knowledge base.

## Workflow

1. Read the bound project memory and resolve the project vault root.
2. Default the corpus to `Papers/` when `query` is not provided.
3. Scan note files via filesystem tools, not MCP.
4. For each paper note:
   - normalize frontmatter (`type`, `project`, `status`, `updated`, citation fields)
   - align the canonical review schema:
     - `Claim`
     - `Method`
     - `Evidence`
     - `Limitation`
     - `Direct relevance to repo`
     - `Relation to other papers`
   - link back to `[[00-Hub]]` and the most relevant canonical notes in `Knowledge/`
   - prefer updating the existing paper note over creating sibling notes
5. When the batch yields stable literature synthesis, update the matching canonical notes in `Knowledge/` instead of leaving insights stranded in `Papers/`.
6. Refresh `Maps/literature.canvas`.
7. If `format=comparison`, also prepare or update a shared comparison note in `Writing/`.
8. Update the daily note and project memory with the changes.
9. In the final response, include updated note paths and optional Obsidian CLI / URI shortcuts.

## Output targets

- `Papers/*.md` (normalized)
- linked updates to existing `Knowledge/` notes when they are the canonical destination
- `Maps/literature.canvas`
- `Writing/reading-notes.md` or `Writing/comparison-matrix.md` when comparison output is useful

## Notes

- Do not create `Concepts/*.md` or `Datasets/*.md` by default.
- Treat `Knowledge/` as the default synthesis target for literature normalization.
- If a new literature idea is still raw material, summarize it first and stage it in `Daily/` instead of creating a new durable note immediately.
