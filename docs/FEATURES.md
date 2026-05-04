# Features unique to claude-brainlab

claude-brainlab forks [Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) and adds a literature pipeline, Obsidian project memory, and per-project SSH/GPU routing. This page is a tour of what's different.

## 1. Literature pipeline (Zotero ↔ Obsidian)

claude-scholar treats literature loosely. claude-brainlab adds a strict pipeline with three skills that work together:

```
paper-search  →  want_2_read.md  →  want-2-read  →  paper-ingest  →  Zotero + Obsidian
```

### `paper-search` — library-aware shortlists
Searches arXiv with awareness of what's already in your Obsidian `Literature/` library. Will not re-suggest papers you already have. Output: a daily block in `${OBSIDIAN_VAULT}/Literature/want_2_read.md`.

### `want-2-read` — process the queue
Reads `want_2_read.md`, fans out **one agent per paper**, and each agent invokes `paper-ingest` on its assigned paper. After the fan-out completes a final review agent re-reads every new note and strengthens any that are too shallow.

### `paper-ingest` — strict end-to-end ingest
- BibTeX from external API (arxiv/DBLP/DOI/OpenReview), never LLM-generated.
- Triple duplicate check (Zotero API + SQLite + Obsidian grep) before creating anything.
- Real bibliographic Zotero parent item (`preprint` / `journalArticle` / `conferencePaper`), never `webpage`.
- PDF attached as child via direct SQLite write.
- Obsidian note with 7 sections written by Haiku from the full PDF text:
  - Общий обзор / посекционный разбор / математика и формулы / архитектуры / методология / графики и таблицы / критическая оценка
- Mandatory final audit verifies all invariants.

Full pipeline spec: `skills/paper-ingest/SKILL.md`. Configuration: [`docs/ZOTERO.md`](ZOTERO.md).

## 2. Project bootstrapping

### `create-project`
Initializes `~/Papers/<slug>/` with:
- `.claude/CLAUDE.md` configured for SSH servers and code paths
- Optional Overleaf clone with `latexmkrc` and bib symlinks
- Obsidian hub card with frontmatter tags (`org/`, `conf/`, `тип/`, `статус/`)
- People stub cards for each collaborator
- Auto-populated `## Литература` section with 2-10 relevant papers grep'd from your existing library
- Registration in `~/.claude/obsidian-projects.json`

Delegates the entire flow to a Haiku sub-agent for cost efficiency. Form discovery (existing tags, available SSH hosts) runs first so the interactive prompts surface real options instead of free-form text.

### `new-paper`
Lighter-weight version: creates only the Obsidian hub card and people cards, no filesystem folder. Use for early-stage ideas.

## 3. Obsidian integration

claude-scholar has Obsidian as a side feature. claude-brainlab makes it the default sink for `.md` files and adds:

- **Hard-routing rule** in `CLAUDE.md` — when the user says "create md file", default destination is the vault, never the local repo, mapped via `obsidian-projects.json`.
- **Hard-link de-duplication** — same paper in multiple folders shares one file via `ln`, not symlink, not copy.
- **`obsidian-project-bootstrap`** — bind a code repo to a vault subfolder.
- **`obsidian-project-memory`** — keep `Plans/`, `Experiments/`, `Results/`, `Literature/`, `Writing/`, daily research log in sync with code activity.
- **`obsidian-experiment-log`** — write experiment runs (config, metrics, observations) into `Experiments/YYYY-MM-DD.md`.
- **`obsidian-research-log`** — daily research notes, plans, standups, milestones into the project's daily folder.
- **`obsidian-link-graph`** — find and repair broken wiki-links between Papers/Knowledge/Experiments/Results.
- **`obsidian-synthesis-map`** — generate cross-note synthesis (lit reviews, comparison matrices, project summaries).
- **`call-notes`** — log meeting notes and per-student tasks into `Задачи.md`.

## 4. MemPalace auto-save

The Stop hook (`scripts/mempalace-obsidian-hook.py`) prompts Claude to save durable session content into MemPalace and Obsidian after every turn. Q&A turns are skipped automatically; substantive work (experiments, theory, infrastructure decisions) gets written to:

- `MemPalace.diary` — compressed summary
- `MemPalace.drawer` — verbatim quotes / decisions / code
- `MemPalace.kg` — entity-relationship graph
- `Obsidian Experiments/Knowledge/general` — the human-readable counterpart

See [`MEMPALACE.md`](MEMPALACE.md) for how to disable.

## 5. SSH-aware code routing

The repo includes a (disabled-by-default) `rules/disabled/ssh-servers.md` rule. When enabled, it teaches the agent to:

- Read `~/.ssh/config` to discover hosts.
- For projects under `~/Papers/<slug>/`, read `<slug>/.claude/CLAUDE.md` for the per-project SSH host list.
- Default to running training and experiments via `ssh <host> "cd <code> && <cmd>"` instead of locally.
- Use `tmux new-session -d -s <name>` for long-running jobs.
- Check GPU load (`nvidia-smi --query-gpu=...`) across listed servers before choosing where to run.

Adapt this to your hardware by editing `rules/disabled/ssh-servers.md`, replacing the host stubs with names from your `~/.ssh/config`, and renaming the file to drop `disabled/`.

## 6. Russian-language defaults

CLAUDE.md and several skills default to Russian for human-facing prose (Obsidian notes, AI Explanations in `paper-ingest`, project hub cards). English is preserved for code, formulas, technical terms, and academic prose. To switch defaults, edit `CLAUDE.md` § Core (response language) and the per-skill writing rules.

## What is NOT customized vs upstream

These come straight from claude-scholar (or its dependencies) and behave the same:

- Coding-style rules (`@dataclass(frozen=True)`, factory/registry, no `print()` in debug)
- Hooks (`security-guard.js`, `session-start.js`, `stop-summary.js`, `skill-forced-eval.js`) — minor tweaks only
- Most skills: `ml-paper-writing`, `results-analysis`, `results-report`, `research-ideation`, `citation-verification`, `paper-self-review`, `code-review-excellence`, `bug-detective`, `git-workflow`, `uv-package-manager`, `kaggle-learner`, `presentation`, `post-acceptance`, `review-response`, etc.
- Vendored from [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills): `obsidian-markdown`, `obsidian-cli`, `obsidian-bases`, `json-canvas`, `defuddle`.

If a skill's behavior surprises you, check upstream first.
