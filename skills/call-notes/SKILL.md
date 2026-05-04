---
name: call-notes
description: Use when the user wants to log meeting or call notes for a project — task assignments per student, follow-ups, deadlines. Creates or updates Задачи.md in the project's Obsidian folder. Trigger on: "запиши звонок", "записать встречу", "call notes", "что сделать студентам", "задачи после звонка".
version: 2.2.0
tags: [Project, Obsidian, Students, Meetings]
---

# Call Notes

> **Execution model**: spawn `Agent(model="haiku")` and delegate ALL steps including user interaction. Pass: (1) these full instructions, (2) the user's message, (3) today's date, (4) vault path `${OBSIDIAN_VAULT}/`, (5) `~/.claude/obsidian-projects.json`. The haiku agent uses AskUserQuestion when needed.

Log meeting/call notes into the project's Obsidian folder and update each participant's people/ card.

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
# find matching slug → root → obsidian_dir = ${OBSIDIAN_VAULT}/<root>/<slug>/
```

### Step 2: Read the project hub card

Read `${OBSIDIAN_VAULT}/<root>/<slug>/<slug>.md` and extract the `участники:` field.
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
1. Extract their `[[people/Фамилия-Имя]]` from the hub card's `участники:` field — this gives you both the file path and the canonical full name
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
   - If user picks an existing participant → map and use their wikilink
   - If user says "новый: Имя Фамилия" → create a new `people/<LastName>-<FirstName>.md` stub and add `"[[people/<LastName>-<FirstName>]]"` to the hub card's `участники:` field

### Step 5: Write to Задачи.md

**If file doesn't exist** — create it:
```markdown
---
тип: задачи
проект: <slug>
---
# Задачи — <Project Name>

```

**Insert a new entry at the top of the notes list** (place the newest entry immediately under the `# Задачи — ...` heading, never overwrite existing content):
```markdown
## <DD-MM-YYYY> — <topic extracted from notes, or "Синхронизация">

<Context paragraph: preserve the key content from the notes in 2–4 sentences. Do NOT over-summarize — keep the substance of what was said. If someone described what they did, write it out fully. Include any status info, concerns, or decisions mentioned.>

### Задачи

- [ ] [[people/<LastName>-<FirstName>]] — <specific task>
- [ ] [[people/<LastName>-<FirstName>]] — <specific task>
- [ ] <Plain Name> — <specific task>  ← only if no people/ card

```

Rules:
- Preserve the original detail level — do not compress "подточил лемму, переписал акцент, пофиксил графики" into "правки статьи"
- Each distinct action = its own `- [ ]` checkbox
- Group multiple tasks under the same person
- Dates always absolute (DD-MM-YYYY)
- Topic: extract from content (e.g. "Правки статьи", "Статус экспериментов") or use "Синхронизация"
- Newest call entry goes first. Insert the whole new `## DD-MM-YYYY ...` block above older call entries

### Step 5b: Update hub card ## Задачи

Open the hub card `${OBSIDIAN_VAULT}/<root>/<slug>/<slug>.md`.

If it has no `## Задачи` section — append one before the last section or at the end of the file.

Insert each task from this call as a new checkbox line at the top of the `## Задачи` section (never remove existing ones):
```markdown
## Задачи

- [ ] [[people/<LastName>-<FirstName>]] — <task> (<DD-MM-YYYY>)
- [ ] <Plain Name> — <task> (<DD-MM-YYYY>)  ← if no people/ card
```

Rules:
- One line per task
- Always include the date in parentheses at the end
- Use wikilinks where available, plain name otherwise (e.g. Андрей for the PI/user if not in participants)
- Newest tasks go first within `## Задачи`

### Step 6: Update people/ cards

For each person who appears in the notes (resolved in Step 4):
1. Read their `${OBSIDIAN_VAULT}/people/<LastName>-<FirstName>.md`
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
✓ Задачи.md: ${OBSIDIAN_VAULT}/<root>/<slug>/Задачи.md (N задач)
✓ Обновлены карточки: [[people/X]], [[people/Y]]
```

## Example

**User input:**
```
/call-notes lora-bench
Роме надо дописать анализ базелайна и добавить таблицу сравнения с GaLore.
Артёму запустить QLoRA на llama-3-8b с lr=1e-4, прислать логи до пятницы.
```

**Задачи.md entry:**
```markdown
## 20-04-2026 — Анализ и эксперименты

Рома дорабатывает baseline-анализ: нужна таблица сравнения с GaLore. Артём запускает QLoRA на llama-3-8b (lr=1e-4), дедлайн по логам — 25 апреля.

### Задачи

- [ ] [[people/Кутенков-Рома]] — дописать анализ базелайна
- [ ] [[people/Кутенков-Рома]] — добавить таблицу сравнения с GaLore
- [ ] [[people/Утегенов-Артем]] — запустить QLoRA на llama-3-8b (lr=1e-4), прислать логи до 25-04-2026
```

**people/Кутенков-Рома.md — appended:**
```markdown
- **20-04-2026** `[[lora-bench]]` — дописать анализ базелайна, добавить таблицу сравнения с GaLore
```

## Notes

- Never delete or rewrite existing entries anywhere
- For any Markdown section you update, put the newest information at the top and keep older items below
- If the project has no Obsidian hub card yet → warn and suggest `/new-paper` first
- Do not invent tasks not mentioned in the notes
