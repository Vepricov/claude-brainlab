# Windows setup guide

Native Windows install — no WSL, no rsync. Tested on Windows 11 with the
Claude Code desktop app and the `claude` CLI.

## TL;DR

```powershell
# 1. Prerequisites (see table below), then:
git clone https://github.com/<you>/claude-brainlab.git
cd claude-brainlab
powershell -ExecutionPolicy Bypass -File install\setup-windows.ps1
# 2. Restart Claude Code. Done.
```

The script asks for your paths on first run (writes `.env`), installs all
components into `~/.claude`, and registers the MemPalace + Zotero MCP servers.

## Prerequisites

| Tool | Install | Needed for |
|---|---|---|
| Git (incl. Git Bash) | `winget install Git.Git` | clone, hooks |
| Node.js LTS | `winget install OpenJS.NodeJS.LTS` | hooks, `claude` CLI |
| Python 3.10+ | `winget install Python.Python.3.12` | scripts, statusline |
| uv | `winget install astral-sh.uv` | MCP server installs |
| Claude Code | desktop app or `npm i -g @anthropic-ai/claude-code` | everything |
| MemPalace | `uv tool install mempalace` | memory MCP (optional) |
| zotero-mcp | `uv tool install zotero-mcp-server` | Zotero MCP (optional) |
| Zotero 7 | [zotero.org](https://www.zotero.org/download/) | literature pipeline (optional) |

`uv tool install` puts executables into `%USERPROFILE%\.local\bin`
(`mempalace-mcp.exe`, `zotero-mcp.exe`) — the installer looks for them there.

## Where the config actually lives (read this)

This is the part that silently breaks by hand-editing the wrong file:

| File | What reads it | Put here |
|---|---|---|
| `~/.claude.json` (root `mcpServers`) | **CLI and desktop app** | MCP servers — but only via `claude mcp add -s user ...`, don't hand-edit |
| `~/.claude/settings.json` | CLI and desktop app | hooks, statusline, env — **NOT MCP servers: the `mcpServers` block here is ignored by both** |
| `~/.claude/CLAUDE.md` | all sessions | global instructions |
| `~/.claude/skills,agents,commands,hooks,rules,scripts` | all sessions | components |
| `~/.claude/obsidian-projects.json` | Obsidian-routed skills | project → vault mapping |

MCP tools appear only in sessions started **after** registration — restart the
app (or start a new session) after running the installer.

## Step by step (what the installer does)

1. **`.env`** — created interactively if missing: vault path, project roots
   (`Papers/`, `Projects/`, `Staff/`), Python path, emails. All paths use
   forward slashes (`C:/Users/you/...`) so they stay JSON-safe.
2. **Components** — `skills/`, `commands/`, `agents/`, `hooks/`, `scripts/`,
   `rules/` are copied to `~/.claude/`. Anything that would be overwritten is
   backed up to `~/.claude/.claude-brainlab-backups/<timestamp>/` first.
3. **Placeholders** — `${OBSIDIAN_VAULT}` etc. inside installed skills and
   scripts are expanded to your real values (`install/render_config.py`).
4. **`settings.json`** — rendered from `settings.json.template` (hooks,
   statusline). The `mcpServers` block is intentionally stripped — see above.
5. **MCP registration** — the equivalent of:

   ```powershell
   # '--' is quoted on purpose: PowerShell 5.1 strips a bare -- from native
   # command arguments, which makes `claude mcp add` misparse the command path.
   claude mcp add mempalace -s user '--' C:/Users/<you>/.local/bin/mempalace-mcp.exe
   claude mcp add zotero -s user `
     -e ZOTERO_LOCAL=true -e ZOTERO_LIBRARY_TYPE=user `
     -e UNPAYWALL_EMAIL=<your email> -e UNSAFE_OPERATIONS=all `
     '--' C:/Users/<you>/.local/bin/zotero-mcp.exe serve
   ```

   Re-run just this part any time with:
   `powershell -ExecutionPolicy Bypass -File install\setup-windows.ps1 -McpOnly`

## Zotero specifics

- The Zotero **desktop app must be running** for local mode. Enable the local
  API: Zotero → Edit → Settings → Advanced → check *"Allow other applications
  on this computer to communicate with Zotero"* (serves on port 23119).
- First MCP start takes ~15 s. If Claude Code reports a startup timeout, set
  the env var `MCP_TIMEOUT=30000` and restart.
- Semantic search starts empty. `zotero_search_items` works immediately;
  for `zotero_semantic_search`, build the index once:
  `%USERPROFILE%\.local\bin\zotero-mcp.exe update-db`

## MemPalace specifics

- First run: `mempalace init` in the folder you want mined, or just start
  using `mempalace_add_drawer` from Claude — the palace is created on demand.
- Check health any time: `mempalace status` (drawer/wing counts) or ask
  Claude for `mempalace_status` in a session.

## Verify the install

```powershell
claude mcp list        # both servers should show "✔ Connected"
```

Then in a new Claude Code session ask: *"покажи mempalace_status"* and
*"zotero_get_collections"* — both should return real data, not
"tool not found".

## Rollback / uninstall

```powershell
powershell -ExecutionPolicy Bypass -File install\uninstall-windows.ps1
```

Restores the most recent backup snapshot from
`~/.claude/.claude-brainlab-backups/`, removes components that were newly
installed (per the install manifest), deletes the `CLAUDE.brainlab.md`
sidecar, and unregisters the `mempalace` / `zotero` MCP servers from
`~/.claude.json`. Switches: `-KeepMcp` (leave servers registered),
`-Yes` (no confirmation prompt).

Nothing destructive: backups are preserved, and the MCP server executables
and their data (your memory palace, your Zotero library) are never touched —
re-running `setup-windows.ps1` brings everything back.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `mempalace_*` tools missing in session | Session started before registration → restart. Then `claude mcp list`. |
| `claude mcp list` → zotero fails | Zotero app not running, or local API not enabled (see above). |
| `No module named mempalace` | Server registered as `python -m mempalace...` — wrong. Re-run installer: it registers the `mempalace-mcp.exe` from uv. |
| `UnicodeEncodeError ... cp1251` from a script | Console codepage. The installer sets `PYTHONIOENCODING=utf-8`; set it globally if you run scripts by hand. |
| Servers in `settings.json` ignored | Expected — that block is a decoy, nothing reads it. Use `claude mcp add`. |
| `claude mcp add` → `missing required argument 'commandOrUrl'` | You used a bare `--` in PowerShell 5.1 — it strips it. Quote it: `'--'`. |
| `zotero_semantic_search` returns nothing | Index not built — run `zotero-mcp update-db`. |
| Cyrillic/space in Windows username | Supported: keep forward slashes and quotes in `.env`; the installer handles the rest. |

## Alternative: WSL

If your Claude Code runs under WSL, use the bash installers instead
(`install/bootstrap.sh` + `install/setup.sh`, or `install/setup-windows.sh`
for the WSL-renders-for-Windows hybrid). The PowerShell path above is the
recommended one for a native Windows Claude Code.
