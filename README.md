# claude-brainlab

A research-oriented configuration for [Claude Code](https://docs.claude.com/en/docs/claude-code) — built for an ML/AI researcher's day: ingesting papers into Zotero + Obsidian, drafting and reviewing papers, running experiments, and keeping a tightly-linked project knowledge base.

Built on top of [Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) (MIT). Adds a tighter literature pipeline (`paper-ingest`, `paper-search`, `want-2-read`), a deeper Obsidian integration (project hub cards, daily notes, experiment logs, hard-link de-duplication), and per-project SSH/GPU routing.

## What's in the box

| | What it does | Where |
|---|---|---|
| **57 skills** | research, literature, Obsidian, code, writing | `skills/` |
| **37 slash commands** | `/paper-ingest`, `/want-2-read`, `/obsidian-init`, `/analyze-results`, `/rebuttal`, … | `commands/` |
| **16 agents** | `code-reviewer`, `bug-analyzer`, `paper-miner`, `obsidian-hub-creator`, … | `agents/` |
| **6 hooks** | security guard, session start/stop, MemPalace auto-save, Obsidian daily sync, skill activation | `hooks/` |
| **Helper scripts** | statusline, conversation export, MemPalace ↔ Obsidian bridge | `scripts/` |
| **Rules** | coding style, citation rules, security, agent orchestration | `rules/` |
| **Templates** | `settings.json.template`, `.env.example`, project-mapping example | repo root |

## Highlights — what's unique to this fork

These are the parts you won't find in upstream `claude-scholar`. Full details in [`docs/FEATURES.md`](docs/FEATURES.md).

- **`paper-ingest`** — end-to-end pipeline: arXiv URL → BibTeX (external API, never LLM-generated) → PDF → Zotero parent item with PDF child attachment → Obsidian note with 7-section AI Explanation written by Haiku → mandatory final audit.
- **`want-2-read`** — process a Markdown reading queue with one fan-out agent per paper, each invoking `paper-ingest`, plus a final review agent for quality control.
- **`paper-search`** — library-aware arXiv shortlists that don't re-suggest already ingested papers.
- **`create-project`** / **`new-paper`** — set up `~/Papers/<slug>/` with `.claude/CLAUDE.md`, Overleaf `latexmkrc`, Obsidian hub card, people cards, and `obsidian-projects.json` registration.
- **Obsidian integration** — hard-link rule for the same paper in multiple folders, project-memory bootstrap, experiment log, daily research log, link-graph repair, synthesis maps.
- **MemPalace integration** — durable conversation memory with auto-save on every turn (off by default for new installs — see [`docs/MEMPALACE.md`](docs/MEMPALACE.md)).

## Install

```bash
git clone https://github.com/<you>/claude-brainlab.git
cd claude-brainlab
bash install/bootstrap.sh   # interactive — fills .env
bash install/setup.sh       # backup-aware copy to ~/.claude/
```

Restart Claude Code afterwards. To roll back: `bash install/uninstall.sh`.

See [`docs/INSTALL.md`](docs/INSTALL.md) for prerequisites and step-by-step explanation.

## Customize

Most paths and identifiers are driven by `.env`. To change a hook, skill, or rule, edit it in this repo and re-run `bash install/setup.sh` — your existing `~/.claude` is backed up first.

For per-skill customization (Zotero parent keys, vault folder taxonomy, MemPalace wing names): see [`docs/CUSTOMIZE.md`](docs/CUSTOMIZE.md).

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
