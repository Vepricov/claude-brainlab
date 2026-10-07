# Agent Orchestration

## Choose help by the task

Use a specialist when the work benefits from an independent review or a distinct area of
expertise. A code change does not require a fixed sequence of planning, architecture,
testing, and review agents. Handle small, clear edits directly.

For delegated work, name the owned files or responsibility, expected result, and checks.
Preserve other agents' edits and resources. Use the agents available in the current client;
an unavailable agent name is not a reason to abandon work that can be completed locally.

## Parallel execution
Run independent bounded tasks in parallel when delegation is allowed and useful work can
continue locally. Keep dependent operations and shared-file edits sequential.

## Available agents (~/.claude/agents/)
Research: `literature-reviewer`, `paper-miner`, `kaggle-miner`
Dev: `architect`, `build-error-resolver`, `code-reviewer`, `refactor-cleaner`, `tdd-guide`, `bug-analyzer`, `dev-planner`
Design: `ui-sketcher`, `story-generator`

Academic reviews and rebuttals use `astar-paper-review` and `review-response` directly.
Their own workflows define any specialist roles they need.
