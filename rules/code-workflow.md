# Code Workflow (applies to ALL agents, ALL sessions)

The user delegates code execution to agents and reads the logs. For that to work, code must be documented in a shared library and every project must declare what code it uses and how it changed it. Full reference: the **`code-library`** skill (load it when working with a project that has code).

## HARD RULES

1. **Code library is the source of truth for *how a repo works*.**
   Location: `~/brainlab/personal/code-library/<repo>/`, with a canonical overview `code-library/<repo>/<repo>.md` (read first) + module notes.
   - Before doing non-trivial work on an external repo, read its `personal/code-library/<repo>/` notes.
   - If a project uses a repo that is **not yet** in `code-library/`, run the **`code-ingest`** skill (give it the repo URL/path) to create it. One-time deep analysis; never copy code, only map it (cite `path:line` + GitHub permalink).

2. **Project hub card declares its code.**
   Every project (`~/brainlab/<направление>/<тема>/<работа>/README.md`) that uses code MUST have a `## Код` section: which repo (wikilink into `personal/code-library/<repo>`), local + server paths and branch, and the **project-specific edits** (new files / patched files + why / new flags). The Code library holds the upstream map; the card holds this project's delta. Keep the delta updated when you change the code.

3. **Experiments are monitored, never lost.**
   Per experiment series, in the work itself: `runs/<name>.md` (log + timestamped `## Progress snapshots` table) and `runs/<name>-table.md` (final tables + embedded loss-curve plot); both stay on the machine, git them not. Long runs go in `tmux` on the server; a `/loop` checks liveness, appends snapshots, and refreshes a versioned plot PNG. House-style plotting + the iCloud/cache gotchas: see `personal/Knowledge/warmup-loss-plot-tool.md`.

4. **Every training run is wrapped in the lab recorder, before it starts.**
   `lab_run.py` from the `lab-knowledge` skill (`~/.claude/skills/lab-knowledge/scripts/lab_run.py`)
   writes the run's own page — hyperparameters, metrics,
   environment, commit, hardware — into one folder per run and pushes it to a branch, from
   which the agent later moves it under a claim and builds a series. Copy it into the repo
   that holds the training code; no dependencies, stdlib only.
   A run that finished without the recorder has to be transcribed by hand, which the base
   forbids and its gates fail: a number absent from the corpus turns the verdict red.
   The named rules are `run-is-written-by-code`, `run-says-what-is-seen` and
   `shelf-must-be-empty` in `~/.claude/skills/lab-knowledge/references/canon.md`.

5. **Coding standards still apply** — `~/.claude/rules/coding-style.md`, `agents.md`, `security.md`, and the Karpathy principles in `CLAUDE.md` (surgical changes, frozen-dataclass config, type hints, no globals, factory/registry, files 200-400 lines).

## Quick map
- "how does repo X work?" → `personal/code-library/X/X.md`
- "add repo X to the library" → skill `code-ingest`
- "how do we work with code here / what skills exist" → skill `code-library`
- "what did THIS project change in repo X" → project hub card `## Код`
