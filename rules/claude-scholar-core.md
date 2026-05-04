# Claude Scholar Core

## User
PhD CS researcher. Target venues: NeurIPS, ICML, ICLR, ACL, AAAI, Nature, Science. Quality bar: logical coherence, precise technical writing, natural expression (not AI-inflated), arguments that survive peer review.

## Python defaults
- package management: `uv`
- configuration: Hydra + OmegaConf
- training: Transformers Trainer when appropriate
- git: Conventional Commits, small reviewable diffs, rebase for sync

## Research lifecycle — route by stage
Ideation → ML Development → Experiment Analysis → Paper Writing → Self-Review → Submission/Rebuttal → Post-Acceptance. Match output standards to the actual stage. Do not flatten stages into one generic response.

## Obsidian project memory
If `.claude/project-memory/registry.yaml` exists → activate Obsidian behavior by default. Filesystem-first, no mandatory MCP, no extra API key required.

## Execution
- For complex/multi-file work: align on approach before executing
- Prefer non-destructive changes; keep rollback paths obvious
- After meaningful implementation: run a real verification (lint, test, smoke check)
- Prefer small coherent diffs; separate unrelated changes

## Task closeout
After each meaningful task provide:
```
📋 [What changed and in which files]
📊 [Current status]
💡 [Next steps]
```
