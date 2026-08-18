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

WHY THIS COUNTS ITS OWN EXCHANGES

The interval is meant to be "every N messages from the human". The upstream counter takes
every entry with role=user, and in an agentic session almost all of those are tool
results: in one long session here, 5283 such entries were 4722 tool results, 177 hook
replies and only 384 real messages. At an interval of ten that fired 552 times instead of
38, and each extra turn re-reads the whole context — 8.6% of the session's output tokens
and 8.0% of its cache reads went to saving. So the counting happens here, over genuine
turns only, and the interval means what it says.

Saving before compaction is the other obvious idea and it does not work: a blocking
PreCompact hook cancels the compaction instead of deferring it. The cadence stays on Stop.

The lab section appears only when a lab-knowledge MCP server is configured, so an install
without lab access is not nagged about a base it cannot reach.
"""

import json
import sys
from pathlib import Path

import mempalace.hooks_cli as hooks_cli

SETTINGS = Path.home() / ".claude" / "settings.json"

#: Настоящих сообщений человека между сохранениями.
SAVE_INTERVAL = 10

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

Keep each save short: one drawer under ~1500 characters, one diary line, no transcript
dumps and no code blocks unless the code is the finding itself.
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


def _text_of(content: object) -> str:
    """Plain text of a message, whatever shape the harness wrote it in."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") != "tool_result"
        )
    return ""


def human_turns(transcript_path: str) -> int:
    """How many times the person actually said something.

    Tool results and the hook's own reminders wear role=user too, and counting them is what
    turned an interval of ten into a save every other tool call.
    """
    path = Path(transcript_path).expanduser()
    if not path.is_file():
        return 0
    count = 0
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            message = entry.get("message")
            if not isinstance(message, dict) or message.get("role") != "user":
                continue
            content = message.get("content")
            if isinstance(content, list) and any(
                isinstance(block, dict) and block.get("type") == "tool_result"
                for block in content
            ):
                continue
            text = _text_of(content)
            if "<command-message>" in text:
                continue
            if "AUTO-SAVE checkpoint" in text or "Stop hook feedback" in text:
                continue
            count += 1
    return count


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        data = {}
    parsed = hooks_cli._parse_harness_input(data, "claude-code")  # noqa: SLF001

    # Уже внутри цикла сохранения: пропустить, иначе получится петля.
    if str(parsed["stop_hook_active"]).lower() in ("true", "1", "yes"):
        print(json.dumps({}))
        return

    turns = human_turns(parsed["transcript_path"])
    state_dir = hooks_cli.STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    marker = state_dir / f"{parsed['session_id']}_last_save_turns"
    try:
        last = int(marker.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        last = 0

    if turns - last < SAVE_INTERVAL or turns <= 0:
        print(json.dumps({}))
        return

    try:
        marker.write_text(str(turns), encoding="utf-8")
    except OSError:
        pass
    hooks_cli._maybe_auto_ingest()  # noqa: SLF001 — сохраняем поведение обёртки

    reason = hooks_cli.STOP_BLOCK_REASON.rstrip() + OBSIDIAN_ADDENDUM
    if lab_base_configured():
        reason = reason.rstrip() + "\n" + LAB_ADDENDUM
    print(json.dumps({"decision": "block", "reason": reason}))


if __name__ == "__main__":
    main()
