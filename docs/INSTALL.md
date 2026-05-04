# Install

Two-step install. The first step writes a local `.env`. The second step copies files into `~/.claude/` with backup. Nothing outside `~/.claude/` is touched.

## 1. Prerequisites

```bash
# macOS — example
brew install node python rsync
# Optional helpers
brew install --cask obsidian
brew install --cask zotero
```

Python 3.10+ is required. Use `which python3` to confirm.

## 2. Clone the repo

```bash
git clone https://github.com/<you>/claude-brainlab.git
cd claude-brainlab
```

## 3. Bootstrap (`.env`)

```bash
bash install/bootstrap.sh
```

You will be asked for:

| Prompt | Default | What it controls |
|---|---|---|
| `VAULT_NAME` | `my-vault` | Obsidian folder name. Used wherever the vault is referenced as a relative dir. |
| `OBSIDIAN_VAULT` | `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/<VAULT_NAME>` | Absolute path to the vault root. |
| `PAPERS_ROOT` | `~/Papers` | Where research projects with papers live. |
| `PROJECTS_ROOT` | `~/Projects` | Where code-only projects live. |
| `STAFF_ROOT` | `~/Staff` | Where per-person work folders live. |
| `PYTHON_BIN` | `$(which python3)` | Used by hooks. Use an absolute path if you have a specific conda/uv Python. |
| `ZOTERO_API_KEY` | empty | From <https://www.zotero.org/settings/keys>. Leave blank to disable Zotero MCP. |
| `ZOTERO_LIBRARY_ID` | empty | Numeric user ID from your Zotero profile URL. |
| `UNPAYWALL_EMAIL` | `you@example.com` | Used by zotero-mcp for paper resolution. |
| `USER_EMAIL` | inherited | Optional — used by some skills for diary entries. |

The result is a `.env` file in the repo root with `chmod 600`. It is git-ignored.

## 4. Setup (copy to `~/.claude/`)

```bash
bash install/setup.sh           # install
bash install/setup.sh --dry-run # preview
```

What happens:

1. Existing files in `~/.claude/` that would be overwritten are copied to `~/.claude/.claude-brainlab-backups/<timestamp>/` first.
2. `skills/`, `commands/`, `agents/`, `hooks/`, `scripts/`, `rules/` are synced into `~/.claude/` with `rsync -a`.
3. If you already have `~/.claude/CLAUDE.md`, the brainlab copy is installed as `CLAUDE.brainlab.md` (sidecar) so your version stays untouched. Merge manually when ready.
4. `settings.json` is rendered from `settings.json.template` with `${VAR}` placeholders substituted from `.env`.
5. If `ZOTERO_API_KEY` was empty, the `zotero` MCP entry is dropped.
6. If `~/.claude/obsidian-projects.json` does not exist, `obsidian-projects.example.json` is copied as a starter.
7. A manifest is written to `~/.claude/.claude-brainlab-manifest.txt` so `uninstall.sh` knows what to roll back.

Restart Claude Code so it picks up the new settings.

## 5. Verify

In a fresh Claude Code session:

```text
/help
/skills
/agents
```

You should see the brainlab skills (`paper-ingest`, `want-2-read`, etc.) and agents (`paper-miner`, `obsidian-hub-creator`, etc.).

A quick smoke test:

```text
@paper-search find recent arXiv papers on LoRA fine-tuning
```

If that completes and your queue file appears in `${OBSIDIAN_VAULT}/Literature/want_2_read.md`, the install is healthy.

## 6. Optional — MemPalace

The Stop hook expects MemPalace to be importable. To enable persistent cross-session memory:

```bash
pip install mempalace
mempalace init
```

To turn the auto-save off, see [`MEMPALACE.md`](MEMPALACE.md).

## 7. Uninstall

```bash
bash install/uninstall.sh
```

Restores the most recent backup snapshot and removes any newly-added components. Backup snapshots themselves are preserved at `~/.claude/.claude-brainlab-backups/`.
