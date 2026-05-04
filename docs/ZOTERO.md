# Zotero integration

claude-brainlab uses Zotero as the canonical bibliographic store. The literature pipeline (`paper-ingest`, `want-2-read`, `paper-search`) creates a parent paper item per arXiv ID, attaches the PDF as a child, and writes a matching Obsidian note that links back via the parent key. The "Add & Classify" rule in `CLAUDE.md` enforces this whenever you cite a paper.

## Install

```bash
brew install --cask zotero       # or download from zotero.org
pipx install zotero-mcp          # or: uv tool install zotero-mcp
zotero-mcp --version             # verify
```

## Get credentials

1. **API key** — <https://www.zotero.org/settings/keys> → "Create new private key". Tick "Allow library access" and "Allow notes access" and "Allow write access".
2. **Library ID** — open <https://www.zotero.org/users/<your-id>/items>. The numeric `<your-id>` is your `ZOTERO_LIBRARY_ID`.
3. Paste both into `.env` and re-run `bash install/setup.sh`. The `mcpServers.zotero` block in `~/.claude/settings.json` is rendered from these.

If `ZOTERO_API_KEY` is empty in `.env`, the installer skips the Zotero MCP entry — you can still install everything else.

## Local API

The desktop Zotero app exposes an HTTP API at `http://localhost:23119` while running. The MCP wraps that. Several skills (notably `paper-ingest`) call the local connector directly via `curl`, so **Zotero must be open** when you ingest a paper.

## Library hierarchy

The repo assumes a 2-level layout: `Literature/<TopLevel>/<collection>/`. Default top-levels are:

| Top-level | Use |
|---|---|
| `Optimization` | optimizers, training dynamics, scaling laws |
| `PEFT` | LoRA-style adapters, prompt/prefix tuning |
| `LLM` | architecture, pre-training, alignment-adjacent |
| `RL` | RLHF, DPO/GRPO/SimPO, preference learning |
| `Applied` | downstream tasks |
| `Reference` | textbooks, surveys |
| `_inbox` | staging area, see `paper-ingest` |

You can rename or restructure this. The skills do **not** hardcode the taxonomy — they `find Literature -mindepth 2 -maxdepth 2 -type d` at runtime to discover folders.

## Per-collection Zotero parent keys

`paper-ingest` needs the parent collection key whenever it creates a sub-collection. After install, fill in the table at the bottom of `skills/paper-ingest/SKILL.md`. To discover your own keys (Zotero must be running):

```bash
curl -s "http://localhost:23119/api/users/0/collections?format=json" | python3 -c "
import json, sys
for c in json.loads(sys.stdin.read()):
    parent = c['data'].get('parentCollection') or 'ROOT'
    print(f\"{c['key']}  parent={parent}  name={c['data']['name']}\")"
```

Rows with `parent=ROOT` are top-level collections.

## How `paper-ingest` works

Pipeline (full spec in `skills/paper-ingest/SKILL.md`):

1. Extract arXiv ID.
2. Triple duplicate check — Zotero API + local SQLite (`~/Zotero/zotero.sqlite`) + grep over the Obsidian Literature folder. Refuses to create a duplicate without explicit confirmation.
3. Fetch BibTeX from external API (arXiv → DBLP → DOI → OpenReview). LLM **never** invents BibTeX; if all sources fail the script reports the error and offers to retry.
4. Download PDF to `~/Papers/Library/<id>.pdf` (staging only — deleted after Zotero import).
5. Create Zotero parent item with `itemType: preprint` (for arXiv) or `journalArticle` / `conferencePaper`. Validates that it is **not** a `webpage` placeholder.
6. Attach PDF as child via `zotero_attach_pdf.py` (Zotero must be closed for this — script edits SQLite/storage directly).
7. Write the Obsidian note. Frontmatter `zotero_key` is the **parent** key, never the attachment key.
8. AI Explanation in 7 sections is written by Claude Haiku using the full PDF text.
9. Final audit via `zotero_check_dup.py --final-audit` — verifies parent type, title match, creators populated, collection membership, PDF child attachment, frontmatter sync.

If the audit returns `"ok": false`, the workflow stops and reports which invariant failed.

## Hard rules (enforced in `CLAUDE.md`)

- Never cite a paper not in the library — ingest first.
- Never invent a `citation_key` — copy from the BibTeX block in the note.
- Never use `connector/saveSnapshot` on an arXiv abstract URL (creates a `webpage`-type item).
- For one paper in multiple Obsidian folders: hard link, not symlink, not copy. For multiple Zotero collections: same item, multiple memberships.
- New collections require user confirmation before creation, and they must be created in both Zotero and Obsidian synchronously.

## Disabling Zotero

If you don't use Zotero:

1. Leave `ZOTERO_API_KEY` blank in `.env` and run `bash install/setup.sh`. The MCP entry is dropped.
2. Either delete or stop using these skills/commands: `paper-ingest`, `want-2-read`, `paper-search`, `zotero-notes`, `zotero-obsidian-bridge`. They will sit unused without harm.
3. Edit `## Literature & Citation Rules` in `~/.claude/CLAUDE.md` (or in the repo and re-run setup) to remove the Zotero-aware citation flow.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `paper-ingest` creates a `webpage` Zotero item | Zotero connector quirk. The skill detects this, trashes the broken item, and creates a proper `preprint` via `connector/saveItems`. If it doesn't recover, run the steps in `## Step 5` of `paper-ingest/SKILL.md` manually. |
| PDF attach fails with `database is locked` | Close Zotero before running `zotero_attach_pdf.py`. The script edits SQLite directly. |
| `pdftotext: command not found` | `brew install poppler`, or `export PATH=/opt/homebrew/bin:$PATH` if it is installed but not on PATH. |
| BibTeX fetch fails | Try `--doi` instead of `--arxiv`. The script attempts arXiv → DOI → OpenReview in order. |
