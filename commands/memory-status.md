---
description: Show MemPalace archive and project memory status
allowed-tools: Bash(mempalace status), Bash(ls *), Bash(python3 *), Read
---

Inspect the current MemPalace layout and report it briefly.

## Steps

1. Read `./.claude/CLAUDE.md` if it exists and extract the `Wing in MemPalace` value.

2. Run:

```bash
mempalace status
```

3. Run:

```bash
ls -1 ~/.mempalace/staging/conversations_by_project
```

4. If the current project has a configured wing, also run one focused search inside that wing for a short project-specific keyword from the current repo name.

5. Return a compact status with exactly these sections:
- `Current project`
- `Project wing`
- `Archive wing`: always report `archive: conversations`
- `Staged project dirs`
- `Notes`

6. In `Notes`, mention whether new session markdown logs should auto-sync into the current project wing.
