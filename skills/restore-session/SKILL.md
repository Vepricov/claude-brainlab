---
name: restore-session
description: Use when the user asks to "restore session", "continue previous conversation", "recall what we discussed", "load past context", or wants to resume work from a prior Claude session. Lists saved conversations and loads selected one as context.
version: 1.0.0
tags: [Session, Context, Memory, Restore]
---

# Restore Session

Load a previous conversation as context for the current session.

## When to Use

- User says "restore session", "continue from last time", "recall previous context"
- User wants to resume work on a topic from a past session
- User references something discussed in a previous conversation

## Workflow

### Step 1 — List saved conversations

Run this command and parse the output:

```bash
ls -t ~/.claude/logs/conversations/*.md 2>/dev/null | head -20
```

For each file:
- Parse filename: `YYYY-MM-DD_<topic-slug>.md`
- Read first line of file (the title) with `head -1 <file>`
- Show as numbered list

Example output to show user:
```
Recent conversations:
1. 2026-04-08 — я хочу установить вот такой репозиторий awesome-claude-code (today)
2. 2026-04-07 — как настроить SSH для нового сервера
3. 2026-04-05 — анализ результатов exp_003 не сходится с baseline
...
```

### Step 2 — User picks

Ask: "Which one? (number, or 'all' to see full list)"

### Step 3 — Load context

Read the selected file:
```bash
cat ~/.claude/logs/conversations/<filename>.md
```

Then:
1. Read the full conversation
2. Summarize what was discussed in 4-6 bullet points
3. Note any unfinished tasks or open questions
4. Say: "Context loaded. Here's what we covered last time:" + bullet points

Then ask: "What would you like to continue with?"

## Context Injection Format

When presenting the loaded context, structure it as:

```
## Previous session: <topic> (<date>)

**What we discussed:**
- ...
- ...

**Unfinished / open items:**
- ...

**Files/projects involved:**
- ...
```

## Notes

- Conversations are saved automatically at session end
- Files live at `~/.claude/logs/conversations/`
- Sessions older than 90 days are auto-deleted
- If no conversations found, tell user that history starts accumulating from now
