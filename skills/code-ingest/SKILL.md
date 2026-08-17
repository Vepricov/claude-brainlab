---
name: code-ingest
description: Use when the user gives a code repository (a GitHub URL or a local/server path) and wants it added to the Obsidian Code library — a one-time deep analysis that produces a structured set of Markdown notes mapping how the repo works (entrypoint, modules, where to look to change X), without copying the code. Trigger on "add this repo to the code library", "разбери этот репозиторий", "code-ingest <url>", "задокументируй код", or when a project starts using an external repo that is not yet in Code/.
version: 1.0.0
tags: [Coding, Obsidian, CodeLibrary, Onboarding]
---

# code-ingest — add a repository to the Obsidian Code library

Turns a repo into a **map you can read in 2 minutes and instantly recall how the
code is organized and where to look to change something** — without duplicating
the source. The code itself stays in git / on the server; these notes are the index.

## When to use
- The user hands you a repo URL or path and says "add to the code library" / "разбери репо".
- A project starts depending on external code that has no `Code/<repo>/` folder yet.
- Before heavily editing an unfamiliar repo (build the map first).

## When NOT to use
- The repo is already in `Code/<repo>/` and unchanged → just read it. Re-run only to refresh after large upstream changes.
- For per-project edits/diffs → those go in the **project hub card** `## Код` section, not here (see [[code-library]]).

## Where it lives
Obsidian vault: `${OBSIDIAN_VAULT}/Code/`
One folder per repo: `Code/<repo-slug>/`. The slug is the repo name, kebab-case.

## Output structure (always)
```
Code/<repo>/
  <repo>.md          ← CANONICAL OVERVIEW. Always this exact name. Read this first.
  architecture.md    ← entrypoint, control/data flow, how a run executes end-to-end
  <module>.md        ← one note per major module/package (group tiny files)
  ...
```
- The overview `<repo>.md` is mandatory and always named after the folder, so any agent knows which file to open first.
- Split into module notes when the repo is large; for a tiny repo a single `<repo>.md` is fine.
- Update `Code/README.md` (the library index) with a one-line entry for the new repo.

## Procedure
1. **Get the source.** Prefer reading a local clone or the server copy if one exists (ask / check the project card). Otherwise fetch file listing + key files from GitHub (raw URLs / `gh`). Note the canonical git URL and default branch.
2. **Map the layout.** List top-level dirs and the role of each. Identify: entrypoint(s), config system, the main loop, the factory/registry or dispatch points (where names map to classes), data path, outputs/checkpoints.
3. **Trace one full run** end-to-end (what `main` does, in order) — this becomes `architecture.md`.
4. **Write module notes** using the template below. For each module: what it's for, key files with **GitHub permalinks and line anchors**, key classes/functions, and an explicit **"where to edit to change X"** list. Do not paste code bodies — cite `path:line` + a one-line description.
5. **Write the overview `<repo>.md`** using its template.
6. **Index it** in `Code/README.md`.
7. Tell the user what was created and link the overview.

## Overview template (`<repo>.md`)
```markdown
---
tags: [code, <repo-slug>]
repo: <git url>
default_branch: <branch>
created: DD-MM-YYYY
---
# <repo> — code map

One-paragraph: what this repo is and what you use it for.

## At a glance
- **Entrypoint:** `path` (`func`)
- **Config:** how runs are parametrized (flags / yaml / hydra)
- **Run a job:** the minimal command
- **Data:** where data lives / how it's loaded
- **Outputs:** where checkpoints / logs / metrics go
- **Dispatch points:** where a name (optimizer/model/dataset) maps to a class

## Directory map
| path | role | note |
|------|------|------|
| ... | ... | [[architecture]] / [[<module>]] |

## Where to look to change X
- change the model arch → [[models]] (`...`)
- add an optimizer → [[optimizers]] (`...`)
- change the schedule → ...
- change data → ...

## Notes
- [[architecture]] · [[optimizers]] · [[models]] · [[data]] · ...

## Used by projects
- [[Papers/<slug>/<slug>|<project>]] — <fork/branch + what's changed>
```

## Module note template (`<module>.md`)
```markdown
# <module>

What this module is responsible for, in 2-3 sentences.

## Key files
- `path/to/file.py` — role. [GitHub](permalink)
  - `ClassOrFunc` (`file.py:LINE`) — what it does.

## How it fits the run
Where this is called from (link [[architecture]]), inputs/outputs.

## Where to edit to change X
- ... → `file.py:LINE`
```

## Rules
- **Never copy large code blocks.** Cite `path:line` + GitHub permalink + a sentence. The notes are a map, not a mirror.
- Keep each note focused; 200-400 lines max, split if larger.
- Pin permalinks to the analyzed commit/branch so line anchors stay valid; note the branch.
- Use Obsidian wikilinks between the overview and module notes.
- After ingesting, remind the user to add a `## Код` section to the relevant project hub card (see [[code-library]]).
