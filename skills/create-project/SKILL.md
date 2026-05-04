---
name: create-project
description: Use when the user wants to create a new research project, set up a new paper project, initialize a project folder, or says "create project", "new project", "setup project". Creates the standard ~/Papers/<project>/ folder structure with .claude/CLAUDE.md configured for SSH servers and code paths.
version: 2.0.0
tags: [Project, SSH, Research, Setup]
---

# Create Project

> **Execution model**: spawn `Agent(model="haiku")` and delegate ALL steps including user interaction. Pass: (1) these full instructions, (2) the user's initial message, (3) today's date. The haiku agent uses AskUserQuestion for data collection and performs all file operations.

Set up a new research project with the standard folder structure and SSH server configuration.

## Workflow

### Step 1: Discover context + show form

Run these commands first (before showing the form):

```bash
# Available SSH hosts
grep "^Host " ~/.ssh/config | grep -v "Host \*" | awk '{print $2}'

# Existing org/ tags in vault
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

Then present the form using AskUserQuestion with discovered values as options:

```
Let's set up the project. Please fill in:

1. Root folder  (Papers / Projects / Staff)
   →

2. Project folder name  (will be ~/<root>/<name>/)
   →

3. Code repo  (GitHub URL or folder name — leave blank if none)
   →

4. Overleaf git URL  (https://git.overleaf.com/... — leave blank if not yet)
   →

5. SSH servers  (available: <from grep above> — pick one or more, or leave blank)
   →

6. Students / collaborators  (comma-separated names — leave blank if none)
   →

7. Organization  (existing: <org/ tags from vault> — or type new value / N/A)
   →

8. Target conference  (existing: <conf/ tags from vault> — or type new value / N/A)
   →

9. Status  (<статус/ tags from vault>)
   →

10. Type  (<тип/ tags from vault>)
    →

11. Topic tags  (existing: <topic tags from vault> — pick relevant ones, comma-separated; or add new)
    →
```

Wait for the user to fill in all fields before proceeding.

### Step 2: Create Folder Structure

```bash
mkdir -p ~/<root>/<project>/.claude
```

**Code folder** (only if user gave URL or name):
- GitHub URL: `git clone <url> ~/<root>/<project>/<code_name>`
- Just a name: `mkdir -p ~/<root>/<project>/<code_name>`

**Paper folder** (only if Overleaf URL given):
```bash
git clone <overleaf_url> ~/<root>/<project>/paper
```
Then run Overleaf local setup (Step 3).

### Step 3: Overleaf Local Setup (only when paper/ was cloned)

Find main `.tex` file:
```bash
find ~/<root>/<project>/paper -name "*.tex" -not -path "*/.*" | head -20
```
Find the file with `\documentclass` — its parent is `<subdir>`.

For each `<subdir>` with a main `.tex`:
```bash
cd ~/<root>/<project>/paper/<subdir>
ln -sf ../refs.bib refs.bib
ln -sf . <subdir>
cat > .latexmkrc << 'EOF'
$pdflatex = 'pdflatex -shell-escape -interaction=nonstopmode %O %S';
$pdf_mode = 1;
$bibtex_use = 1;
EOF
```

Verify:
```bash
cd ~/<root>/<project>/paper/<subdir>
latexmk -pdf <main>.tex 2>&1 | grep -E "^!|Error|Citation.*undefined|No file"
```

### Step 4: Generate .claude/CLAUDE.md

Create `~/<root>/<project>/.claude/CLAUDE.md`:

```markdown
# Project: <project>

## Paths
- root: ~/<root>/
- project_root: ~/<root>/<project>
- code_name: <code_name>
- local_code: ~/<root>/<project>/<code_name>
- remote_code: ~/<code_name>

## SSH Servers
servers:
  - <host1>
  - <host2>

## Paper (Overleaf)
- local: ~/<root>/<project>/paper/
- sync: git pull

## Running Code
- Single: `ssh <host> "cd <code_name> && <command>"`
- Long run: `ssh <host> "tmux new-session -d -s <session> 'cd <code_name> && <command>'"`
- GPU load: `ssh <host> "nvidia-smi --query-gpu=index,memory.used,memory.free,utilization.gpu --format=csv,noheader"`

## Obsidian
- vault: ${OBSIDIAN_VAULT}/<obsidian_root>/<slug>/

## Project Memory
- Wing in MemPalace: `<project>`
- Archive: `conversations`

## Agent Instructions
- If user says "run this" without server → check GPU load on all listed servers, then ask
- Remote path is always ~/<code_name>/
- Never ask which server again if already specified in this session
- To get latest paper: cd ~/<root>/<project>/paper && git pull
```

Omit sections for missing info (no Overleaf → no Paper section; no SSH → no SSH/Running Code sections).

### Step 5: Create Obsidian hub card

Derive slug: lowercase, replace `_` and spaces with `-`.
Vault: `${OBSIDIAN_VAULT}/`
Obsidian root matches filesystem root (Papers/Projects/Staff).

**Get description:**
- If paper was cloned: `grep -A 30 '\\begin{abstract}' ~/<root>/<project>/paper/**/*.tex | head -40`
- Otherwise: ask user via AskUserQuestion: "Brief project description (2–3 sentences)?"

**Create folder:**
```bash
mkdir -p ${OBSIDIAN_VAULT}/<obsidian_root>/<slug>
```

**For each student** — check `${OBSIDIAN_VAULT}/people/<LastName>-<FirstName>.md`:
- Not exists → create stub:
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
- Exists → append `- [[<slug>]] — <one-line description>` to `## Проекты`

**Create `${OBSIDIAN_VAULT}/<obsidian_root>/<slug>/<slug>.md`:**

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
# <project>

<Paper title, authors, venue — if applicable>

## Суть
<1–2 sentences>

## Участники
- [[people/<LastName>-<FirstName>]]

## Пути
- проект: `~/<root>/<project>/`
- mempalace: `<project>`

## Литература
<2-10 most relevant links from the Obsidian literature library>
```

Rules:
- `tags:` array only — no `организация:`, `конференция:`, `тип:`, `название:` fields
- Skip `org/<org>` tag if org = N/A; skip `conf/<conf>` if conf = N/A
- New tag values (not in vault yet) are allowed — they will appear in Obsidian automatically
- Do NOT create `## Связанные проекты` section
- `## Литература` is mandatory in every main project card

### Step 5.5: Auto-populate literature

Before writing the project hub card, search the Obsidian literature library and select 2-10 relevant papers.

Library root:
`${OBSIDIAN_VAULT}/Literature/`

Selection policy:
- Prefer exact topical matches from the user's project title, code repo name, Overleaf title, and short description
- If the project is a paper extension, include the direct base paper first
- If the user gave no paper title, infer relevance from the 2-3 sentence project description
- Prefer canonical literature notes already present in the library over creating anything new
- Use only existing Obsidian note links at this stage

Suggested retrieval workflow:
```bash
# broad keyword search in the library
grep -Rin "<keyword1>\|<keyword2>\|<keyword3>" ${OBSIDIAN_VAULT}/Literature --include="*.md"

# list candidate note paths
find ${OBSIDIAN_VAULT}/Literature -name "*.md"
```

Output format in the project card:
```markdown
## Литература

- [[Literature/<TopLevel>/<Subfolder>/<Paper Note Title>]] — one-line reason this paper matters for the project
```

Constraints:
- Add between 2 and 10 bullets
- The reason after each link must be short and project-specific
- If literature is uncertain, still pick the best available nearby papers rather than leaving the section empty

**Register in `~/.claude/obsidian-projects.json`:**
```python
import json
from pathlib import Path
cfg_path = Path.home() / ".claude/obsidian-projects.json"
cfg = json.loads(cfg_path.read_text())
for root in cfg["roots"]:
    if root["obsidian"] == "<obsidian_root>":
        root["items"]["<project>"] = "<slug>"
        break
cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))
```

### Step 6: Confirm

```
✓ ~/Papers/<project>/.claude/CLAUDE.md
✓ Cloned: <code repo> (if any)
✓ Obsidian: ${OBSIDIAN_VAULT}/<obsidian_root>/<slug>/<slug>.md
✓ People cards: <created/updated list>
✓ Registered in obsidian-projects.json
```
