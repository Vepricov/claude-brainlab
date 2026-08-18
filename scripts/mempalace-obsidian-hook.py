#!/usr/bin/env python3
"""Stop hook: one interruption, three places the session gets written down.

Replaces `python3 -m mempalace hook run --hook stop --harness claude-code`.

MemPalace blocks the end of a turn every few exchanges and asks the agent to save what
happened. That design is the reason it works: the hook does not try to understand the
session, it interrupts and demands, and the agent — which has the whole context — decides
what is worth keeping and says so out loud.

Obsidian and the lab knowledge base ride the same interruption instead of adding their
own. Two hooks blocking on two cadences would double the noise, and a second mechanism
that writes on its own turned out not to work at all: the previous lab hook parsed the
session for markup nobody was documented to write, so in real use it never fired.

The lab section appears only when a lab-knowledge MCP server is configured, so an install
without lab access is not nagged about a base it cannot reach.
"""

import json
from pathlib import Path

import mempalace.hooks_cli as hooks_cli

SETTINGS = Path.home() / ".claude" / "settings.json"

OBSIDIAN_ADDENDUM = """
4. obsidian — if the session had experiments/theory/key decisions (skip for Q&A only):
   a) Find project slug: check ~/.claude/obsidian-projects.json roots[*].items for cwd.
      If cwd is not under any root → use general/.
   b) Write to the appropriate file (append, create if missing):
      - Experiment results (loss, accuracy, AUC, metrics, convergence)
        → ${OBSIDIAN_VAULT}/<root>/<slug>/Experiments/YYYY-MM-DD.md
        Format: ## HH:MM — <name>\\n**Config**: ...\\n**Results**: ...\\n**Notes**: ...
      - Theory or algorithmic decisions
        → ${OBSIDIAN_VAULT}/<root>/<slug>/Knowledge/<topic>.md
      - Infrastructure/tooling changes
        → ${OBSIDIAN_VAULT}/general/Knowledge/<topic>.md
   c) Tell the user one line: what you wrote and where.
   Skip entirely if nothing of durable research value happened this session.
"""

LAB_ADDENDUM = """
5. lab knowledge (shared base over MCP) — only for what the lab can cite later:
   - a claim worth testing → create_hypothesis(project_id, statement, falsifier, source_ref_id)
   - a run, planned or finished → record_experiment / update_experiment_status
   - a measured outcome → record_evidence, tied to the source it came from
   - a rule the lab will follow → propose_decision
   Find the home first with get_project_by_slug: work on the lab's own tooling belongs to
   the `lab-agents` theme, lab knowledge that fits no project to `lab-general`.
   Requirements that cannot be waived: a hypothesis needs its falsifier, evidence needs its
   source, an experiment needs a status. If what you have does not meet that bar, write
   nothing here — an invented record in a citable base is worse than a missing one, and
   private or unfinished thinking belongs in Obsidian instead.
   Report in one line: the codes you wrote, or that nothing qualified.
"""


def lab_base_configured() -> bool:
    """Is a lab-knowledge MCP server wired into this install?

    Checked by reading the settings rather than the environment: the token reaches the MCP
    client through the server definition, and a hook does not necessarily inherit it.
    """
    try:
        settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    servers = settings.get("mcpServers")
    return isinstance(servers, dict) and "lab-knowledge" in servers


reason = hooks_cli.STOP_BLOCK_REASON.rstrip() + OBSIDIAN_ADDENDUM
if lab_base_configured():
    reason = reason.rstrip() + "\n" + LAB_ADDENDUM
hooks_cli.STOP_BLOCK_REASON = reason
hooks_cli.SAVE_INTERVAL = 10  # default: 15

hooks_cli.run_hook("stop", "claude-code")
