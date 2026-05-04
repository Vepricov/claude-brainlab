---
name: zotero-review
description: Read and analyze papers from a Zotero collection, then synthesize them into the bound Obsidian project knowledge base or markdown review outputs
args:
  - name: collection
    description: Zotero collection name or keyword to search
    required: true
  - name: depth
    description: Analysis depth (quick/deep)
    required: false
    default: deep
tags: [Research, Zotero, Obsidian, Literature Review, Paper Analysis]
---

# /zotero-review - Zotero Collection Literature Analysis

Read and analyze papers in the Zotero collection "$collection", with analysis depth "$depth".

## Default target

- **Preferred target**: the bound Obsidian project knowledge base
- **Fallback target**: `literature-review.md` in the current working directory

## Workflow

### Step 0: Resolve the project context

1. If the current repo is already bound to Obsidian project memory, use that vault.
2. If the repo looks like a research project but is not bound yet, bootstrap it first.
3. If there is no project binding, generate the review in the working directory.

### Step 1: Locate and read the Zotero collection

1. Call `mcp__zotero__zotero_get_collections` to find the matching collection.
2. Call `mcp__zotero__zotero_get_collection_items` to get all papers.
3. For each paper:
   - call `mcp__zotero__zotero_get_item_metadata` with `include_abstract: true`
   - call `mcp__zotero__zotero_get_item_fulltext` when available
   - use abstract metadata as fallback when PDF full text is unavailable
4. If MCP transport fails but a local `zotero-mcp` checkout is available, use the local Python fallback instead of aborting.
5. Treat Zotero `webpage` items as valid literature entries when they still expose meaningful metadata or full text.

### Step 2: Ensure detailed paper notes exist

Before high-level synthesis, ensure the collection has durable paper notes.

If the project is Obsidian-bound:
- create or update `Papers/*.md` canonical notes first
- keep one canonical paper note per paper whenever possible
- align notes to the canonical schema (`Claim / Method / Evidence / Limitation / Direct relevance to repo / Relation to other papers`)
- update the best matching `Knowledge/` literature synthesis notes
- refresh `Maps/literature.canvas`
- update a collection inventory note with item -> note mapping and coverage summary

If not Obsidian-bound:
- create intermediate `paper-notes/*.md` files in the working directory when `depth=deep`

### Step 3: Synthesize across paper notes

Create or update:
- `Knowledge/Literature-Overview.md`
- `Knowledge/Method-Families.md` when useful
- `Knowledge/Research-Gaps.md` when useful
- `Writing/literature-review.md` only when the user wants writing-facing synthesis
- `Writing/comparison-matrix.md` when useful

The synthesis should include:
- thematic grouping
- method families
- key findings and tensions
- research gaps
- direct relevance to the current project
- explicit links across `Papers/` and `Knowledge/`

### Step 4: Push downstream only when justified

- keep the default review surface in `Papers/`, `Knowledge/`, and `Maps/literature.canvas`
- update `Writing/` when the user wants a manuscript-facing review or comparison narrative
- only update `Experiments/` or `Results/` in a later project workflow when the user explicitly wants that handoff

### Step 5: Minimal write-back

Always update:
- today's `Daily/YYYY-MM-DD.md`
- repo-local project memory when project state changes

### Step 6: Final response

Include:
- collection size and coverage summary
- updated note paths
- optional `obsidian://open` links
- optional `obsidian open ...` suggestions when CLI is available

## Notes

- Prefer the Obsidian-bound project workflow over loose markdown files when available.
- Keep `Papers/` first-class; the review should be grounded in canonical paper notes rather than only one-shot synthesis.
- The default graph artifact is `Maps/literature.canvas`.
