---
description: List and browse saved conversation history
---

List recent saved conversations from `~/.claude/logs/conversations/`.

## Steps

1. Run this command to get all conversation files sorted by date:

```bash
ls -t ~/.claude/logs/conversations/*.md 2>/dev/null | head -30
```

2. For each file, read its content:

```bash
cat <filepath>
```

3. Build a numbered list. For each conversation extract:
   - **Date**: from filename prefix `YYYY-MM-DD`
   - **Project**: from `**Project**:` line in the file
   - **Topic**: read the actual **You:** messages (lines starting with `**You:**`) and the first **Claude:** response, then write a 5-10 word summary of *what was actually done or discussed* — not the filename slug. Examples of good summaries:
     - "Установка awesome-claude-code, конфликты с claude-scholar"
     - "Починка YAML frontmatter в агентах"
     - "Настройка сохранения истории сессий"
     - "Анализ результатов exp_003, падение loss"
   - **Messages**: count of `**You:**` lines = number of user turns

4. Display as a table:

```
#  Date        Project    Topic                                        Turns
─────────────────────────────────────────────────────────────────────────────
1  2026-04-08  andrey     Установка awesome-claude-code, починка YAML   12
2  2026-04-07  ZO-RL      Анализ результатов exp_003                     8
...
```

5. Ask: "Which one? (number to read, 'restore N' to load as context, 'all' for full list)"

6. If user says a number — display the full conversation file.

7. If user says `restore N` — read the full file, then say:
   "Loaded. Here's what we covered:" followed by 4-6 bullet points summarizing the key decisions, changes made, and open questions. Then ask what to continue with.
