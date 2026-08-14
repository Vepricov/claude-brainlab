# claude-brainlab

A research-oriented configuration for [Claude Code](https://docs.claude.com/en/docs/claude-code) — built for an ML/AI researcher's day: ingesting papers into Zotero + Obsidian, drafting and reviewing papers, running experiments, and keeping a tightly-linked project knowledge base.

Built on top of [Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) (MIT). Adds a tighter literature pipeline (`paper-ingest`, `paper-search`, `want-2-read`), a deeper Obsidian integration (project hub cards, daily notes, experiment logs, hard-link de-duplication), and per-project SSH/GPU routing.

## What's in the box

| | What it does | Where |
|---|---|---|
| **72 skills** | research, literature, Obsidian, code, writing — full list in [`SKILLS.md`](SKILLS.md) | `skills/` |
| **37 slash commands** | `/paper-ingest`, `/want-2-read`, `/obsidian-init`, `/analyze-results`, `/rebuttal`, … | `commands/` |
| **16 agents** | `code-reviewer`, `bug-analyzer`, `paper-miner`, `obsidian-hub-creator`, … | `agents/` |
| **6 hooks** | security guard, session start/stop, MemPalace auto-save, Obsidian daily sync, skill activation | `hooks/` |
| **Helper scripts** | statusline, conversation export, MemPalace ↔ Obsidian bridge | `scripts/` |
| **Rules** | coding style, citation rules, security, agent orchestration | `rules/` |
| **Templates** | `settings.json.template`, `.env.example`, project-mapping example | repo root |

## Highlights — what's unique to this fork

These are the parts you won't find in upstream `claude-scholar`. Per-skill detail for all
72 skills is in [`SKILLS.md`](SKILLS.md).

- **`paper-ingest`** — end-to-end pipeline: arXiv URL → BibTeX (external API, never LLM-generated) → PDF → Zotero parent item with PDF child attachment → Obsidian note with 8-section AI Explanation written by Haiku → mandatory final audit.
- **`want-2-read`** — process a Markdown reading queue with one fan-out agent per paper, each invoking `paper-ingest`, plus a final review agent for quality control.
- **`paper-search`** — library-aware arXiv shortlists that don't re-suggest already ingested papers.
- **`astar-paper-review`** — top-venue-grade peer review: reviewer + theoretician (proofs) + literature-scout + experiments-auditor, prompt-injection-safe, one review file per paper.
- **`paper-to-social`** — turn a paper into copy-paste-ready Telegram / X / Habr posts with arXiv figures, in your own voice.
- **`code-ingest`** / **`code-library`** — map an external repo into Obsidian Code-library notes (`path:line`, no code copied) and document the whole code workflow.
- **`create-project`** / **`new-paper`** — set up `~/Papers/<slug>/` with `.claude/CLAUDE.md`, Overleaf `latexmkrc`, Obsidian hub card, people cards, and `obsidian-projects.json` registration.
- **`operon-obsidian-setup`** / **`call-notes`** — task tracking runs on the Operon plugin: `operon-obsidian-setup` reproduces the lab's task-manager setup (flat `project` tags, "my tasks" dashboard, service-link badges, emoji icons, day-boundary auto-archiving), and `call-notes` turns a call into Operon file-tasks assigned per person. This replaces the old ad-hoc `Задачи.md` convention.
- **Obsidian integration** — hard-link rule for the same paper in multiple folders, project-memory bootstrap, experiment log, daily research log, link-graph repair, synthesis maps.
- **MemPalace integration** — durable conversation memory with auto-save on every turn (off by default for new installs).
- **`presentation`** — Beamer-first slide skill with a built-in **terminal-style** theme (dark, monospace, bright-green accent). One source of truth for both `presentation` and `post-acceptance`.

## Evidence-first paper review and rebuttal

The repository includes two related skills for internal A* conference work. Both ship native Codex metadata in `agents/openai.yaml` and keep their detailed procedures inside the skill directory.

### `astar-paper-review`

Use `$astar-paper-review` to review an ML paper from the submission PDF, supplement, and optional code. The workflow:

1. sanitizes untrusted PDFs and preserves page-level evidence locations;
2. builds a claim and evidence ledger before assigning scores;
3. runs a theory coordinator with separate proof and rate/prior-art checks;
4. audits experiments from reported claim through configuration and raw evidence;
5. produces a severity-ranked review with explicit uncertainty and incomplete checks.

The theory comparison normalizes assumptions, convergence criteria, oracle cost, dimension, and limiting cases before calling one rate better than another. The empirical audit distinguishes a plausible number from a verified result and never treats a one-seed smoke test as reproduction.

```text
Use $astar-paper-review to review this submission and audit its theory,
closest prior work, experiments, and reproducibility.
```

### `review-response`

Use `$review-response` with the submitted paper, reviewer reports, and any available experiment artifacts. It maps every review into atomic concerns, grounds each response in the frozen submission, and selects the smallest experiment that can resolve a decision-critical objection.

The skill tracks evidence from E0, a proposal without artifacts, through E5, an independently auditable replication. It separates post-hoc rescoring from reward-model re-optimization, checks paper-to-code parameterization, and quarantines results from a changed core method. A revised pipeline can be discussed, but it cannot silently defend the submitted one.

Drafts pass two adversarial checks before release: a skeptical reviewer/AC pass and an evidence-consistency audit across all reviewer threads.

```text
Use $review-response to map these reviews, triage the available runs,
and prepare an evidence-grounded rebuttal strategy.
```

These skills are designed to improve scientific coverage and response discipline. They do not promise acceptance or replace the authors' judgment.

## The `presentation` skill

A LaTeX Beamer skill for theory talks, mathematical decks, and conference presentations. It enforces:

- **One mathematical chain** — every new formula must be motivated by the previous slide. No fact-bag decks.
- **Stable notation** across the whole talk; if you reject a notation choice once, the skill keeps the preferred one in later edits.
- **Russian prose by default** for slide bodies (English for code, method names, file paths). Configurable in `skills/presentation/references/user-presentation-preferences.md`.
- **Overflow is an error** — `Overfull \hbox/\vbox` and `Frame text is shrunk` warnings are treated as layout failures. The skill cuts text, splits frames, or rebalances columns instead of shrinking aggressively.

### Terminal style (the dark theme)

When you say `terminal style` or `терминальный стиль`, the skill applies a custom Beamer theme defined in [`skills/presentation/examples/terminal-style-mini.tex`](skills/presentation/examples/terminal-style-mini.tex). Compile that file to preview the look.

Visual contract (also documented in [`skills/presentation/examples/terminal-style-notes.md`](skills/presentation/examples/terminal-style-notes.md)):

| Element | Value |
|---|---|
| Theme base | `\usetheme{metropolis}` |
| Aspect ratio | 16:9 (`aspectratio=169`) |
| Background | `#0D1117` |
| Card / title bar | `#161B22` |
| Primary accent (titles, frame headers) | `#00FF88` |
| Secondary accent (subtitles) | `#58A6FF` |
| Theorem / proof accent | `#FF7B54` |
| Body text | `#E6EDF3` |
| Muted text | `#8B949E` |
| Title font | monospace bold (`\ttfamily\bfseries`) |
| Frame title font | monospace bold |
| Theorem/idea blocks | `tcolorbox` with thin colored left rule |
| Title slide | `// header` line + thin rules + large title + terminal-like `$ run --topic ...` footer |
| Section dividers | `// 01`, `// 02`, ... + one large title, no other content |
| Final slide | `Спасибо!` + optional `Вопросы?`, same visual language as title |

The `post-acceptance` skill (conference prep workflow) routes `terminal style` requests to the same canonical example, so a request for "make me a NeurIPS talk in terminal style" produces a deck with this exact look.

To customize the theme: edit `skills/presentation/examples/terminal-style-mini.tex` (or fork it into your project), rerun `bash install/setup.sh` if you want it propagated to `~/.claude/`.

## Install

```bash
git clone https://github.com/<you>/claude-brainlab.git
cd claude-brainlab
bash install/bootstrap.sh   # interactive — fills .env
bash install/setup.sh       # backup-aware copy to ~/.claude/
```

Restart Claude Code afterwards. To roll back: `bash install/uninstall.sh`.

See the prerequisites table below before installing.

## Customize

Most paths and identifiers are driven by `.env`. To change a hook, skill, or rule, edit it in this repo and re-run `bash install/setup.sh` — your existing `~/.claude` is backed up first. Per-skill customization (Zotero parent keys, vault folder taxonomy, MemPalace wing names) lives in each skill's `SKILL.md`.

## Prerequisites

| | Required | Optional |
|---|---|---|
| Claude Code | ✓ | |
| Python 3.10+ | ✓ | |
| Node.js (for hooks) | ✓ | |
| `rsync` | ✓ | |
| Obsidian | | recommended (Obsidian-routed skills no-op without it) |
| Zotero + zotero-mcp | | recommended for `paper-ingest` / `want-2-read` |
| MemPalace | | recommended for cross-session memory |

## Credits

- [Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) — foundation: skill catalog, agent set, install pattern.
- [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) — vendored Obsidian utility skills (`obsidian-markdown`, `obsidian-cli`, `obsidian-bases`, `json-canvas`, `defuddle`). See `skills/obsidian-skills.UPSTREAM-LICENSE.txt`.
- [MemPalace](https://github.com/MemPalace/mempalace) — the local-first memory MCP this config plugs into.

## License

MIT. See [`LICENSE`](LICENSE).
