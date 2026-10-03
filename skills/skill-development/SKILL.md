---
name: skill-development
description: Create or repair Claude skills, including their triggers, workflow boundaries, and supporting files.
version: 0.2.0
---

# Skill Development

Use this skill to create or repair Claude skills in the **current local environment**, not in an abstract plugin template.

## Goal

Produce a skill that is:
- easy to trigger,
- lean at the `SKILL.md` layer,
- backed by real `references/`, `examples/`, and `scripts/` files when they are mentioned,
- free of dead local references.

## Core rules

- Keep **one skill = one durable job**.
- Treat the frontmatter description as the main trigger surface.
- Keep `SKILL.md` focused on workflow and boundaries.
- Move detailed catalogs, templates, and long explanations into `references/` or `examples/`.
- Do not mention files that do not exist.
- Do not inherit stale names, agents, or sibling skill references without verifying they exist locally.

Keep project-specific facts and correctness constraints. Remove generic advice and repeated
permission gates that add no protection. Load only references needed for the current mode.
For Codex skills, use the current `skill-creator` when available rather than copying old
Claude tool names or model assumptions into the workflow.

## Default workflow

### 1. Inspect the current environment first

Before writing anything:
- inspect the target skill directory,
- inspect neighboring skills that already solve a similar problem,
- verify which agents, commands, and sibling skills actually exist,
- identify stale references before adding new ones.

Use the local inventory as the authority. Do not write guidance against an imagined plugin layout.

### 2. Lock the skill contract

Define four things before editing:
1. what the skill does,
2. what triggers it,
3. what it explicitly does **not** do,
4. which bundled resources are actually needed.

If the skill only needs a short workflow, keep it short. Do not create `references/`, `examples/`, or `scripts/` just because the directories are conventional.

### 3. Write or repair the frontmatter

The frontmatter should:
- use the real skill identifier in `name`,
- name the task for which the skill changes the agent's decisions,
- distinguish it from neighboring skills,
- use a short description without a required grammatical template or keyword list.

Example:

```yaml
---
name: skill-name
description: Extract verified experiment results into a project report.
---
```

### 4. Keep the main file lean

A good `SKILL.md` should usually contain:
- a short goal section,
- role boundaries,
- a default workflow,
- safety or quality rules,
- a short list of additional resources.

Move these out of the main file when they get long:
- templates,
- exhaustive checklists,
- edge-case catalogs,
- sample outputs,
- long examples.

### 5. Add only real bundled resources

Use bundled resources deliberately:
- `references/` for detailed guidance that may be loaded selectively,
- `examples/` for real example outputs or scaffolds,
- `scripts/` for deterministic helper logic.

If a resource is mentioned in `SKILL.md`, it must exist.
Before removing a resource, inspect its callers, purpose, and history. An absent reference or
usage trace is not proof that it is obsolete. Archive owner-approved retired components
outside every skill discovery root and verify their contents before removing active entries.

### 6. Run integrity checks before closing

At minimum, verify:
- frontmatter parses,
- referenced local files exist,
- sibling skill or agent references are real,
- `SKILL.md` is not overloaded with material that belongs in references,
- temporary logs, caches, and editor artifacts are not left inside the skill directory.

## Typical repair patterns

### When the skill is too long
- keep the trigger and workflow in `SKILL.md`,
- move catalogs and deep detail into `references/`,
- keep a short read order so another model knows what to load first.

### When the skill is too thin
- add a default workflow,
- add at least one concrete example or checklist,
- make the boundaries explicit so the skill is not just a slogan.

### When the skill has stale references
- remove dead paths immediately,
- replace historical names with current local names,
- re-check neighboring agents/commands/skills against the live directory.

## Recommended output shape

When creating or repairing a skill, prefer ending with:
- what changed,
- which files were created or updated,
- what integrity checks were run,
- what still needs manual follow-up, if anything.

## References

Load only what is needed:
- `references/checklist.md` - compact quality checklist before closing a skill edit
- `references/integrity-checks.md` - concrete local checks for missing files, dead references, and drift
- `references/skill-creator-original.md` - legacy background reference; use for context, not as the live source of truth
