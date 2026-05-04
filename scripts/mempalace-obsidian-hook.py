#!/usr/bin/env python3
"""
MemPalace stop hook with Obsidian writing instructions appended.
Replaces: python3 -m mempalace hook run --hook stop --harness claude-code

Patches STOP_BLOCK_REASON so Claude saves to both MemPalace and Obsidian
in the same blocked turn — no extra API calls.
"""
import sys
import mempalace.hooks_cli as hooks_cli

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

hooks_cli.STOP_BLOCK_REASON = hooks_cli.STOP_BLOCK_REASON.rstrip() + OBSIDIAN_ADDENDUM
hooks_cli.SAVE_INTERVAL = 10  # default: 15
hooks_cli.run_hook("stop", "claude-code")
