---
name: obsidian-ingest
description: Ingest a new Markdown file or folder into the bound Obsidian project knowledge base by classifying it, deciding durable vs raw, and routing it to the right canonical destination
args:
  - name: path
    description: File or directory path to ingest
    required: true
tags: [Research, Obsidian, Ingestion, Knowledge Base]
---

# /obsidian-ingest - Ingest New Markdown Into the Project Knowledge Base

Use this command when a new Markdown file or folder should be absorbed into the bound Obsidian knowledge base.

## Workflow

1. Resolve the bound project knowledge base.
2. Inspect the target path and classify the content into one of:
   - `knowledge`
   - `paper`
   - `experiment`
   - `result`
   - `writing`
   - `daily`
3. Decide whether the content is:
   - durable knowledge
   - raw material
4. Apply the default rule: **summarize first, then route**.
5. Choose one action:
   - `promote` -> create or update the canonical destination note
   - `merge` -> update the best existing canonical note
   - `stage-to-daily` -> summarize into today's `Daily/` note first
6. When helpful, use:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/obsidian-project-memory/scripts/project_kb.py" find-canonical-note --cwd "$PWD" --kind paper --query "keyword"
   ```
7. Update project memory and today's daily note with what was promoted, merged, or staged.

## Routing defaults

- background / method / protocol / overview -> `Knowledge/`
- literature summary / related work / reading note -> `Papers/`
- experiment design / ablation plan / runbook -> `Experiments/`
- stable findings / interpreted analysis -> `Results/`
- internal experiment summary report -> `Results/Reports/`
- manuscript draft / slide material / rebuttal text -> `Writing/`
- temporary memo / meeting raw notes / scratch ideas -> `Daily/`

## Results report naming

If the note is an internal experiment summary report, prefer:

```text
Results/Reports/YYYY-MM-DD--{experiment-line}--r{round}--{purpose}.md
```

## Final response

Include:
- classification result
- promote / merge / stage decision
- affected canonical note paths
- optional Obsidian open/URI shortcuts
