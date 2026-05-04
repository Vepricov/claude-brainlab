# Customize

Most of the config lives outside the code: in `.env`, `settings.json`, `obsidian-projects.json`, and a small number of per-skill config blocks. This page walks through the common edits.

## Re-running the installer

After any change in this repo:

```bash
bash install/setup.sh
```

It backs up your current `~/.claude/` content and re-syncs from the repo. Your `~/.claude/obsidian-projects.json` and any third-party files (e.g. plugins) are preserved.

## `.env` — paths and credentials

| Variable | Effect |
|---|---|
| `VAULT_NAME`, `OBSIDIAN_VAULT` | Where Obsidian-routed skills write notes |
| `PAPERS_ROOT`, `PROJECTS_ROOT`, `STAFF_ROOT` | Filesystem roots used by `create-project` and the routing rules in `CLAUDE.md` |
| `PYTHON_BIN` | The interpreter used by hooks. Use an absolute path if your Python lives in conda/uv. |
| `ZOTERO_API_KEY`, `ZOTERO_LIBRARY_ID`, `UNPAYWALL_EMAIL` | Required for `paper-ingest` and `want-2-read`. Leaving them blank drops the Zotero MCP entry from `settings.json`. |

After editing `.env`, re-run `bash install/setup.sh` so `settings.json` is regenerated.

## `obsidian-projects.json` — project routing

`~/.claude/obsidian-projects.json` is the authoritative map from filesystem locations to vault subfolders. Skills and rules consult it before writing notes.

```json
{
  "roots": [
    { "fs": "~/Papers",   "obsidian": "Papers",   "items": {} },
    { "fs": "~/Projects", "obsidian": "Projects", "items": {} },
    { "fs": "~/Staff",    "obsidian": "Staff",    "items": {} }
  ]
}
```

`items` is auto-populated by `create-project`. To add an existing project manually, append `"<project-folder-name>": "<vault-slug>"` under the matching `items` map.

To add a new top-level root (e.g. `~/Teaching`), add a new entry under `roots[]` and create the matching subfolder in your vault.

## `CLAUDE.md` — global agent rules

`~/.claude/CLAUDE.md` is the global instruction file Claude Code loads on every session. The repo ships its version as a **sidecar** (`CLAUDE.brainlab.md`) when you already have one, so nothing of yours is overwritten.

Common edits:

- **Default response language** — adjust the `## Core` section.
- **Routing rules** (where `.md` files default to) — adjust `## Obsidian And Local Workflow` and the `HARD ROUTING RULE` block. If you're not using iCloud-Obsidian, point `${OBSIDIAN_VAULT}` to your real vault path.
- **Citation rules** — `## Literature & Citation Rules` is where the "search vault → ingest → confirm → cite" workflow lives. Disable it if your workflow does not use Zotero.
- **Date format** — switch `DD-MM-YYYY` to your preferred ISO/locale form in `## Obsidian And Local Workflow`.

## Per-skill customization

### `paper-ingest`

Open `skills/paper-ingest/SKILL.md`:

- **Library hierarchy & Zotero parent keys** — fill in the table once after install. Run the helper command in that section to discover your own keys.
- **Top-level folder taxonomy** — defaults to `Optimization | PEFT | LLM | RL | Applied | Reference | _inbox`. Rename to fit your domain. Update the table accordingly.

### `create-project`

Open `skills/create-project/SKILL.md`:

- **Form fields** — the interactive form pulls existing tag values from your vault. The 11 default questions cover org/conf/type/status/topic. Comment out lines you do not need.
- **People-card stub** — frontmatter (`тип: человек`, `роль: студент`) is in Russian by default. Change to English in step 5 of the SKILL if you write notes in English.

### `obsidian-research-log`, `obsidian-experiment-log`, `call-notes`

These write to fixed file paths inside the vault. To change the layout (e.g. `Daily/` instead of `Заметки/`), grep for the file-path templates in each `SKILL.md` and edit.

## Hooks

`~/.claude/hooks/` runs on every session. To temporarily disable a single hook, comment out its entry in `~/.claude/settings.json`. To disable permanently, edit `settings.json.template` in the repo and re-run setup.

| Hook | When | Why you might disable |
|---|---|---|
| `security-guard.js` | PreToolUse | You trust your own commands and want fewer prompts. |
| `session-start.js` | SessionStart | You don't want the directory/git banner. |
| `session-summary.js` | SessionEnd | You don't want the work-log file written under `.claude/logs/`. |
| `stop-summary.js` | Stop | You don't want a summary banner after every turn. |
| `mempalace-obsidian-hook.py` | Stop | You don't use MemPalace — see [MEMPALACE.md](MEMPALACE.md). |
| `obsidian-daily-sync.py` | Stop | You don't want auto daily-note updates. |
| `skill-forced-eval.js` | UserPromptSubmit | You prefer Claude to skip the skill activation step. |
| `export-conversation.py` | SessionEnd | You don't want full transcripts saved to disk. |

## Adding your own skill or command

Add the file to `skills/<name>/SKILL.md` (or `commands/<name>.md`) in the repo, then run `bash install/setup.sh`. The next Claude Code session will see it.

## Removing skills you don't want

Delete the folder under `skills/` (or the file under `commands/`) in the repo, then re-run setup. The previous version is preserved in the timestamped backup.

If you want to keep a skill in the repo but not install it for yourself, prefix its directory with `_` — Claude Code only auto-discovers folders without leading underscores.
