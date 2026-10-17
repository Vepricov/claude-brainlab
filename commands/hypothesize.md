---
name: hypothesize
description: Generate research hypotheses for a project by pulling its full Obsidian context (hub card + Code library + literature) and brainstorming testable ideas. Optionally writes them to Papers/<slug>/Hypotheses/.
args:
  - name: slug
    description: Project slug (e.g. warmup, sign_muon, zo-rl-peft) — must exist in ~/.claude/obsidian-projects.json
    required: true
  - name: focus
    description: Optional focus topic ("optimizer", "scheduler", "convergence proof"). Free text.
    required: false
tags: [Research, Ideation, Hypotheses]
---

# /hypothesize — Generate research hypotheses for a project

Use this when you want to brainstorm experiments or theoretical directions for a project without writing code yet. Unlike `aide-remote`, this command does not run anything — it produces a markdown brainstorm of hypotheses, each one ready to be handed to AIDE later via `aide-remote run --project <slug> --hypothesis <file>`.

## Workflow

1. Run `research-context $1` via Bash. This prints the full project context pack — hub card, upstream Code-library overview, target server.
2. Read that output carefully. Pay attention to:
   - `## Суть` (what the project is about)
   - `## Код` (which repo, which files have already been touched)
   - `## Литература` (what's already cited — do not re-propose those exact ideas)
   - `## Статус` (avoid hypotheses that conflict with current submission)
3. If `$2` (focus) is given, restrict ideation to that subarea.
4. Generate **5 testable hypotheses** with this structure each:
   - **Claim** — one sentence, falsifiable
   - **Test mode** — empirical (AIDE) / theoretical / mixed
   - **Files to touch** — concrete paths from the repo overview, only for empirical
   - **Why interesting** — connection to the project's main claim or to literature
   - **Expected outcome** — direction + magnitude if hypothesis holds
   - **Budget** — AIDE steps and wall-clock estimate (or "no compute" for theory)
   - **Risk** — what could make the test meaningless (confound, data leak, etc.)
5. Order hypotheses by cost-adjusted value: cheapest informative test first.

## Output

Write the brainstorm to:

```
~/Papers/<slug>/Hypotheses/YYYY-MM-DD-hypotheses.md
```

(Create the `Hypotheses/` folder if missing. The exact vault path can be confirmed from `research-context $1`.)

After writing the file, print to the user:
- File path
- The 5 claims as a numbered list
- Suggestion: `aide-remote run --project $1 --hypothesis <chosen-file>` once they pick one to test

## Constraints

- **Do not run AIDE.** This is pure ideation.
- **Do not invent literature.** Only reference papers already linked in the hub card. If you need a new reference, mark `[?cite needed]` instead.
- **Be realistic about cost.** A 583M-param training run is not a "cheap test". Cheap tests are `124M @ 1k iterations`, single-seed micro-ablations on existing checkpoints, or pure-derivation hypotheses.
- **Mix theoretical and empirical** unless `$2` clearly restricts to one. Empirical-only ideation is fine when the project is well into the experimental phase.
- **Each hypothesis must be testable in isolation.** No "vague gestures at directions" — each one is a self-contained brief that can be handed to AIDE or to a theorist tomorrow.

## Companion tools

- `research-context <slug>` — the context pack this command builds on
- `aide-remote run --project <slug> --hypothesis <md>` — the empirical-test path
- `~/Templates/hypothesis-template.md` — when the user wants to write a hypothesis manually
