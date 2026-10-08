# Code Workflow (applies to ALL agents, ALL sessions)

The user delegates code execution to agents and reads the logs. For that to work, code must be documented in a shared library and every project must declare what code it uses and how it changed it. Full reference: the **`code-library`** skill (load it when working with a project that has code).

## HARD RULES

1. **Code library is the source of truth for *how a repo works*.**
   Location: `${OBSIDIAN_VAULT}/Code/<repo>/`, with a canonical overview `Code/<repo>/<repo>.md` (read first) + module notes.
   - Before doing non-trivial work on an external repo, read its `Code/<repo>/` notes.
   - If a project uses a repo that is **not yet** in `Code/`, run the **`code-ingest`** skill (give it the repo URL/path) to create it. One-time deep analysis; never copy code, only map it (cite `path:line` + GitHub permalink).

2. **Project hub card declares its code.**
   Every project (`Papers|Projects|Staff/<slug>/<slug>.md`) that uses code MUST have a `## Код` section: which repo (wikilink into `Code/<repo>`), local + server paths and branch, and the **project-specific edits** (new files / patched files + why / new flags). The Code library holds the upstream map; the card holds this project's delta. Keep the delta updated when you change the code.

3. **Experiments are monitored, never lost.**
   Per experiment series, in the project folder: `Experiments/<name>.md` (log + timestamped `## Progress snapshots` table) and `Results/<name>-table.md` (final tables + embedded loss-curve plot). Long runs go in `tmux` on the server; a `/loop` checks liveness, appends snapshots, and refreshes a versioned plot PNG. House-style plotting + the iCloud/cache gotchas: see `general/Knowledge/warmup-loss-plot-tool.md`.

4. **Coding standards still apply** — `~/.claude/rules/coding-style.md`, `agents.md`, `security.md`, and the Karpathy principles in `CLAUDE.md` (surgical changes, frozen-dataclass config, type hints, no globals, factory/registry, files 200-400 lines).

## Quick map
- "how does repo X work?" → `Code/X/X.md`
- "add repo X to the library" → skill `code-ingest`
- "how do we work with code here / what skills exist" → skill `code-library`
- "what did THIS project change in repo X" → project hub card `## Код`
