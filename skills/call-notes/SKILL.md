---
name: call-notes
description: Use when the user wants to log meeting or call notes for a project — task assignments per student, follow-ups, deadlines. Creates Operon file-tasks in the vault (one .md per task, assigned to the person) and interleaves them on the project hub card via Task Wikilink Overlay. Trigger on: "запиши звонок", "записать встречу", "call notes", "что сделать студентам", "задачи после звонка".
version: 3.0.0
tags: [Project, Obsidian, Operon, Tasks, Students, Meetings]
---

# Call Notes

> **Execution model**: spawn `Agent(model="haiku")` and delegate ALL steps including user interaction. Pass: (1) these full instructions, (2) the user's message, (3) today's date, (4) vault path `~/Obsidian/shkodnik1917/`, (5) `~/.claude/obsidian-projects.json`. The haiku agent uses AskUserQuestion when needed.

Turn meeting/call notes into **Operon file-tasks** (one `.md` per action, assigned to the
responsible person), interleave them on the project hub card, and update each participant's
`people/` card. Tasks are real Operon tasks — they show up in the "my tasks" table, Kanban,
Calendar, and get archived by the day-boundary archiver. This skill assumes the vault is
already configured with the `operon-obsidian-setup` skill (Operon plugin + the `Operon/`
folders + the `project` field). If it is not, warn and suggest running `operon-obsidian-setup`
first.

## Workflow

### Step 1: Identify Project

1. If the user named a project in their message (slug or partial name) → use it
2. Otherwise check cwd against `~/.claude/obsidian-projects.json` → use that slug
3. If still unclear → ask via AskUserQuestion: "Для какого проекта записать?"

Read obsidian-projects.json to find the Obsidian path:
```python
import json
from pathlib import Path
cfg = json.loads(Path.home().joinpath(".claude/obsidian-projects.json").read_text())
# find matching slug → root → obsidian_dir = ~/Obsidian/shkodnik1917/<root>/<slug>/
```

### Step 2: Read the project hub card

Read `~/Obsidian/shkodnik1917/<root>/<slug>/<slug>.md` and extract the `участники:` field.
This gives you the canonical list of people in this project and their `people/` card paths.

Example — if hub card has:
```yaml
участники:
  - "[[people/Иванов-Ваня]]"
  - "[[people/Петрова-Катя]]"
```
Then the project participants are Ваня Иванов and Катя Петрова.

### Step 3: Collect Notes

If notes were not provided inline, ask via AskUserQuestion:
```
Что обсуждалось / что нужно сделать?
(Пиши свободно: "Роме дописать раздел 2, Диме запустить эксперименты на A100")
```

### Step 4: Resolve names in the notes

**Source of truth: ONLY the `участники:` list from the hub card (Step 2).** Do NOT search globally across `people/` — a person may exist in other projects but not be a participant here.

For each person mentioned in the notes:
1. Extract their `[[people/Фамилия-Имя]]` from the hub card's `участники:` field — this gives you both the file path and the canonical full name (`имя:` in that card)
2. Try to match the mentioned name to one of these participants:
   - Match by first name: "Гриша" → "Евсеев-Гриша" ✓
   - Match by last name: "Евсеев" → "Евсеев-Гриша" ✓
   - Match by common nickname only if it's unambiguous: "Катя" → "Екатерина", "Рома" → "Роман", "Валера" → "Валерий" (NOT "Владислав")
   - Do NOT guess or stretch: "Валера" ≠ "Владислав", "Саша" alone is ambiguous if multiple participants could match
3. If NO clear match found among the hub card participants → ask via AskUserQuestion:
   ```
   Не нашёл "<name>" среди участников проекта <slug>.
   Участники в карточке: <list from hub card>

   Это кто? Варианты:
   а) один из участников выше (укажи кто)
   б) новый участник — напиши "новый: Имя Фамилия"
   ```
   - If user picks an existing participant → map and use their card
   - If user says "новый: Имя Фамилия" → create a new `people/<LastName>-<FirstName>.md` stub and add `"[[people/<LastName>-<FirstName>]]"` to the hub card's `участники:` field

### Step 5: Create one Operon file-task per action

For every distinct action in the notes, create a file-task at
`~/Obsidian/shkodnik1917/Operon/Tasks/<Task title>.md`:

```markdown
---
assignees: [<Assignee>]
project: [<slug>]
status: Project.Planned
dateDue: <YYYY-MM-DD>   # only if a deadline was mentioned; otherwise omit the line
---
# <Task title>

## Описание
<Context for this task: preserve the substance of what was said — status, concerns,
parameters, decisions. Do NOT over-summarize.>

## Прогресс


## Результат
```

Rules:
- **Assignee** = the person's full name exactly as in the `имя:` field of their `people/` card
  (this is what Operon's `assignees` picker and the "my tasks" filter match on). If there is no
  card, use the plain name as written (e.g. `Андрей` for the PI/user).
- **`project: [<slug>]`** — the flat project tag. A task may carry several slugs if it spans
  projects. Never use `parentTask`.
- **`status: Project.Planned`** for a newly assigned task; use `Project.InProgress` only if the
  notes say the person already started, `Project.Finished` if it was reported done in the call.
- **Do NOT write `operonId`** — Operon assigns it when it indexes the file.
- **Title / filename** = a concise phrase from the action. Strip characters Obsidian disallows
  (`/ \ : * ? " < > |`). If a file with that name exists, append ` (2)`, ` (3)`, …
- Each distinct action = its own task file. Group nothing; one action per file.
- Preserve the original detail level — do not compress "подточил лемму, переписал акцент,
  пофиксил графики" into "правки статьи".

### Step 5b: Interleave the tasks on the hub card

Open the hub card `~/Obsidian/shkodnik1917/<root>/<slug>/<slug>.md`. If it has no `## Задачи`
section, append one before the last section or at the end of the file.

Insert a **new dated block at the top** of `## Задачи` (newest first, never remove existing
blocks). Each task created in Step 5 is referenced by a `[[Task title]]` wikilink, which Operon
renders as an interactive task row (Task Wikilink Overlay) in Reading/Live Preview:

```markdown
## Задачи

### <DD-MM-YYYY> — <topic extracted from notes, or "Синхронизация">

<Context paragraph: 2–4 sentences preserving the substance of the call — who is doing what,
status, decisions, deadlines.>

- [[<Task title 1>]]
- [[<Task title 2>]]
- [[<Task title 3>]]
```

Rules:
- One `[[Task title]]` line per created task, in the same order as the notes.
- Dates always absolute (DD-MM-YYYY). Topic: extract from content (e.g. "Правки статьи",
  "Статус экспериментов") or use "Синхронизация".
- The wikilink text must match the task filename exactly (without `.md`).

### Step 6: Update people/ cards

For each person who appears in the notes (resolved in Step 4):
1. Read their `~/Obsidian/shkodnik1917/people/<LastName>-<FirstName>.md`
2. Find or create a `## Активность` section
3. Insert a dated entry at the top of `## Активность`, describing what they did or need to do in this project:
```markdown
## Активность

- **<DD-MM-YYYY>** `[[<slug>]]` — <what they did or what was assigned to them>
```
Always insert new activity at the top of the section — never overwrite existing entries.

If the file doesn't exist (new participant added in Step 4) — create it:
```markdown
---
тип: человек
имя: <Full Name>
роль: студент
---
# <Full Name>

## Проекты
- [[<slug>]] — <one-line project description>

## Активность

- **<DD-MM-YYYY>** `[[<slug>]]` — <activity>

## Заметки

```

### Step 7: Confirm

Report:
```
✓ Создано задач Operon: N → ~/Obsidian/shkodnik1917/Operon/Tasks/
✓ Hub card обновлён: ## Задачи (блок <DD-MM-YYYY>)
✓ Обновлены карточки: [[people/X]], [[people/Y]]
```
Remind the user that tasks appear in Operon views only after a reindex
(restart Obsidian or run `operon:rebuild-index`).

## Example

**User input:**
```
/call-notes lora-bench
Роме надо дописать анализ базелайна и добавить таблицу сравнения с GaLore.
Артёму запустить QLoRA на llama-3-8b с lr=1e-4, прислать логи до пятницы.
```

**`Operon/Tasks/Дописать анализ базелайна.md`:**
```markdown
---
assignees: [Роман Кутенков]
project: [lora-bench]
status: Project.Planned
---
# Дописать анализ базелайна

## Описание
Baseline-анализ нужно доработать перед сравнением методов.

## Прогресс


## Результат
```

**`Operon/Tasks/Запустить QLoRA на llama-3-8b.md`:**
```markdown
---
assignees: [Артем Утегенов]
project: [lora-bench]
status: Project.Planned
dateDue: 2026-04-25
---
# Запустить QLoRA на llama-3-8b

## Описание
QLoRA на llama-3-8b, lr=1e-4. Прислать логи до 25 апреля.

## Прогресс


## Результат
```

**hub card `lora-bench.md` — `## Задачи` gets a new top block:**
```markdown
## Задачи

### 20-04-2026 — Анализ и эксперименты

Рома дорабатывает baseline-анализ: нужна таблица сравнения с GaLore. Артём запускает QLoRA на llama-3-8b (lr=1e-4), дедлайн по логам — 25 апреля.

- [[Дописать анализ базелайна]]
- [[Добавить таблицу сравнения с GaLore]]
- [[Запустить QLoRA на llama-3-8b]]
```

**people/Кутенков-Рома.md — appended:**
```markdown
- **20-04-2026** `[[lora-bench]]` — дописать анализ базелайна, добавить таблицу сравнения с GaLore
```

## Notes

- Requires the vault configured via `operon-obsidian-setup` (Operon plugin + `Operon/` folders +
  the `project` field). If Operon is absent, warn and suggest that skill first.
- Never delete or rewrite existing entries anywhere — new tasks are new files; hub-card and
  people-card edits only prepend.
- For any Markdown section you update, put the newest information at the top and keep older items below.
- If the project has no Obsidian hub card yet → warn and suggest `/new-paper` first.
- Do not invent tasks not mentioned in the notes.
