---
name: new-paper
description: Use when the user wants to track a new research idea or paper project in Obsidian without setting up a code folder. Use when user says "new paper", "new idea", "add project", or describes a research idea with students and organization. Creates Obsidian hub card + people cards. No filesystem folder created.
version: 2.0.0
tags: [Project, Obsidian, Research, Ideas]
---

# New Paper / Research Idea

> **Execution model**: spawn `Agent(model="haiku")` and delegate ALL steps including user interaction. Pass: (1) these full instructions, (2) the user's initial message, (3) today's date. The haiku agent uses AskUserQuestion for data collection and performs all file operations.

Track a new research idea in Obsidian only. No code folder setup.

## Workflow

### Step 1: Discover existing tags + show form

Run these commands first:

```bash
# Existing org/ tags
grep -rh "^  - org/" ${OBSIDIAN_VAULT}/ --include="*.md" 2>/dev/null | sed 's/[[:space:]]*- //' | sort -u

# Existing conf/ tags
grep -rh "^  - conf/" ${OBSIDIAN_VAULT}/ --include="*.md" 2>/dev/null | sed 's/[[:space:]]*- //' | sort -u

# Existing тип/ tags
grep -rh "^  - тип/" ${OBSIDIAN_VAULT}/ --include="*.md" 2>/dev/null | sed 's/[[:space:]]*- //' | sort -u

# Existing статус/ tags
grep -rh "^  - статус/" ${OBSIDIAN_VAULT}/ --include="*.md" 2>/dev/null | sed 's/[[:space:]]*- //' | sort -u

# Existing topic tags (no prefix)
grep -rh "^  - " ${OBSIDIAN_VAULT}/ --include="*.md" 2>/dev/null | sed 's/[[:space:]]*- //' | grep -vE "^(org|conf|тип|статус)/" | sort -u
```

Then ask via AskUserQuestion, showing discovered values as options:

```
Новый проект в Obsidian. Заполни:

1. Название проекта  (короткое, станет slug)
   →

2. Студенты / соавторы  (через запятую — или пусто)
   →

3. Организация  (есть: <org/ tags> — или новое значение / N/A)
   →

4. Конференция  (есть: <conf/ tags> — или новое значение / N/A)
   →

5. Тип  (<тип/ tags from vault>)
   →

6. Статус  (<статус/ tags from vault>)
   →

7. Тематические теги  (есть: <topic tags> — выбери подходящие через запятую; или добавь новые)
   →

8. Ссылка на статью  (arxiv URL — оставь пустым если нет)
   →

9. Краткая идея  (2–3 предложения — только если нет URL)
   →
```

### Step 2: Extract idea (if paper URL given)

If URL provided, fetch it and extract title + core method (2–3 sentences from abstract).
Use as `## Суть` in hub card.

### Step 3: Derive slug

Lowercase, replace spaces/`_` with `-`. Example: `LoRA Bench` → `lora-bench`.

### Step 4: Create / update people cards

For each student:
1. Check `${OBSIDIAN_VAULT}/people/<LastName>-<FirstName>.md`
2. Not exists → create:
```markdown
---
тип: человек
имя: <Full Name>
роль: студент
---
# <Full Name>

## Проекты
- [[<slug>]] — <one-line description>

## Заметки

```
3. Exists → append `- [[<slug>]] — <one-line description>` to `## Проекты`

### Step 5: Create hub card

```bash
mkdir -p ${OBSIDIAN_VAULT}/Papers/<slug>
```

Create `${OBSIDIAN_VAULT}/Papers/<slug>/<slug>.md`:

```markdown
---
обновлено: <DD-MM-YYYY>
участники:
  - "[[people/<LastName>-<FirstName>]]"
tags:
  - <topic-tag-1>
  - <topic-tag-2>
  - org/<org>
  - conf/<conf>
  - тип/<type>
  - статус/<status>
---
# <name>

<Paper title, authors, venue — if URL was given>

## Суть
<2–3 sentences>

## Участники
- [[people/<LastName>-<FirstName>]]

## Пути
- проект: `~/Papers/<fs_name>/` *(папка ещё не создана)*
- mempalace: `<fs_name>`
```

Rules:
- `tags:` array only — no `организация:`, `конференция:`, `тип:`, `название:`, `слаг:` fields
- Skip `org/<org>` if org = N/A; skip `conf/<conf>` if conf = N/A
- New tag values not in vault are fine — Obsidian picks them up automatically
- Do NOT create `## Связанные проекты` section

### Step 6: Register in obsidian-projects.json

```python
import json
from pathlib import Path
cfg_path = Path.home() / ".claude/obsidian-projects.json"
cfg = json.loads(cfg_path.read_text())
for root in cfg["roots"]:
    if root["obsidian"] == "Papers":
        root["items"]["<fs_name>"] = "<slug>"
        break
cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))
```

`<fs_name>` = anticipated filesystem folder name (snake_case or CamelCase).

### Step 7: Confirm

```
✓ Hub card: ${OBSIDIAN_VAULT}/Papers/<slug>/<slug>.md
✓ People cards: <created/updated list>
✓ Registered: "<fs_name>" → "<slug>"
```
