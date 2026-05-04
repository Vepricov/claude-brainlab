# MemPalace integration

[MemPalace](https://github.com/MemPalace/mempalace) is a local-first memory MCP. claude-brainlab plugs into it in two ways:

1. **As an MCP server** — Claude Code can read/write memory through `mempalace_search`, `mempalace_diary_write`, `mempalace_kg_add`, etc. (29 tools total).
2. **As a Stop hook** — `scripts/mempalace-obsidian-hook.py` runs after every turn and asks Claude to summarize the session into MemPalace + Obsidian.

**Both are enabled by default** in the brainlab `settings.json`. This is opinionated; the rest of this document explains what that means and how to adjust.

## What the auto-save hook actually does

After every Stop event, the hook prints an instruction block to the model. It is not a fully autonomous saver — Claude reads the instruction and decides what to do. The instruction is roughly:

> Save this session's content to MemPalace via `mempalace_diary_write` (compressed summary), `mempalace_add_drawer` (verbatim quotes / decisions / code), and optionally `mempalace_kg_add` (entities and relationships).
> If the session contained experiments, theory, or infrastructure decisions, also append a note to the matching Obsidian project (`Experiments/YYYY-MM-DD.md`, `Knowledge/<topic>.md`, or `general/Knowledge/<topic>.md`).
> Skip entirely for pure Q&A sessions.

In practice, Claude usually skips Q&A turns and writes durable content for non-trivial work.

## Install MemPalace

```bash
pip install mempalace
mempalace init                   # default storage at ~/.mempalace
```

Then verify the MCP entry in `~/.claude/settings.json` points to your Python:

```json
"mempalace": {
  "command": "/path/to/python3",
  "args": ["-m", "mempalace.mcp_server"]
}
```

The `setup.sh` installer fills `${PYTHON_BIN}` from your `.env` automatically.

## Restart Claude Code

After installing MemPalace, restart Claude Code so the new MCP server is loaded. Ask it `list my mempalace tools` to confirm.

## Disabling the auto-save hook

If you find the per-turn save too chatty, or you do not want any auto-write to MemPalace/Obsidian, edit `~/.claude/settings.json` and remove **only** the MemPalace entry from the `Stop` hook list:

```jsonc
"Stop": [
  {
    "matcher": "*",
    "hooks": [
      { "type": "command", "command": "...stop-summary.js..." },
      // delete the next entry to disable auto-save:
      { "type": "command", "command": "${PYTHON_BIN} ${HOME}/.claude/scripts/mempalace-obsidian-hook.py" },
      { "type": "command", "command": "${PYTHON_BIN} ${HOME}/.claude/scripts/obsidian-daily-sync.py" }
    ]
  }
]
```

The MemPalace MCP itself stays available — Claude can still search and write to memory on demand. You only lose the per-turn auto-prompt.

To make the disable permanent across `bash install/setup.sh` runs: edit `settings.json.template` in the repo before running setup.

## Disabling MemPalace entirely

Two-step:

1. Delete the `mempalace` block from `mcpServers` in `settings.json` (and in `settings.json.template` if you want it persistent).
2. Delete the `mempalace-obsidian-hook.py` entry from the `Stop` hooks (above).

Optionally `pip uninstall mempalace` and remove `~/.mempalace`.

## Where things get written

| What | Where |
|---|---|
| Compressed session summary | MemPalace `diary` (per project wing) |
| Verbatim quotes / decisions / code | MemPalace `drawers` |
| Entity/relationship graph | MemPalace `kg` (knowledge graph) |
| Experiment results note | `${OBSIDIAN_VAULT}/<root>/<slug>/Experiments/YYYY-MM-DD.md` |
| Theory / algorithmic decision | `${OBSIDIAN_VAULT}/<root>/<slug>/Knowledge/<topic>.md` |
| Infrastructure / tooling change | `${OBSIDIAN_VAULT}/general/Knowledge/<topic>.md` |

The Obsidian destinations are resolved via `~/.claude/obsidian-projects.json`. If the cwd is not under any registered root, the hook falls back to `${OBSIDIAN_VAULT}/general/`.

## Project wings

MemPalace organizes content into hierarchical "wings" (people/projects), "rooms" (topics), and "drawers" (content). claude-brainlab uses one wing per research project, named after the project slug. The legacy archive wing is `conversations`.

Skills and the global rule in `CLAUDE.md` consult the active project wing before answering questions about prior decisions, experiments, bugs, or project history. To set the active wing, point Claude at the project folder before asking.

## Troubleshooting

- **"mempalace command not found"** — the MCP entry uses `python3 -m mempalace.mcp_server`, so `pip install mempalace` is enough. You don't need a separate CLI.
- **Hook timeout** — `mempalace-obsidian-hook.py` has a 30-second timeout in `settings.json`. If your sessions reliably hit it, raise the timeout there.
- **Sessions don't get saved** — the hook only emits an instruction; Claude skips Q&A by design. Force a save by saying `save this session to mempalace` in chat.
