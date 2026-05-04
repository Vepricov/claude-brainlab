# Agent Orchestration

## Automatic invocation (proactive, no need to ask)
1. Code written/modified → **code-reviewer**
2. Build fails / type errors → **build-error-resolver**
3. Complex feature → **dev-planner** then **architect**
4. Bug report → **bug-analyzer**
5. New feature needing tests → **tdd-guide**

## Parallel execution
Always launch independent agents in parallel, not sequentially.

## Available agents (~/.claude/agents/)
Research: `literature-reviewer`, `rebuttal-writer`, `paper-miner`, `kaggle-miner`
Dev: `architect`, `build-error-resolver`, `code-reviewer`, `refactor-cleaner`, `tdd-guide`, `bug-analyzer`, `dev-planner`
Design: `ui-sketcher`, `story-generator`
