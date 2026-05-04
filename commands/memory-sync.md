---
description: Sync conversation logs into MemPalace project wings
argument-hint: [project|all]
allowed-tools: Bash(python3 *), Bash(mempalace mine:*), Bash(mempalace status), Read
---

Sync exported Claude conversation markdown logs into project-specific MemPalace wings.

## Steps

1. If `$ARGUMENTS` is empty, use `all`.

2. If the argument is `all`, run:

```bash
python3 ~/.claude/projects/-Users-andrey/memory/migrate_conversations_to_project_wings.py --mine
```

3. If the argument is not `all`, run:

```bash
python3 ~/.claude/projects/-Users-andrey/memory/migrate_conversations_to_project_wings.py --project "$ARGUMENTS" --mine
```

4. After sync, run:

```bash
mempalace status
```

5. Summarize:
- which wing(s) were synced
- how many staged markdown files were processed
- whether `archive: conversations` was left untouched

6. If the requested project does not exist in staged conversations, say that explicitly.
