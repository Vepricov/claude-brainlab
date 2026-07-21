---
name: operon-obsidian-setup
description: Use when the user wants to set up the Operon task manager in their Obsidian vault the way this lab does it, or reproduce that setup on a fresh machine — flat project tags (no parentTask hierarchy), a "my tasks" table dashboard, service-link badges on project pages, emoji task icons, and day-boundary auto-archiving. Applies plugin settings (data.json), templates, a CSS snippet, optional main.js display patches, and an optional macOS launchd archiver. Trigger on "set up Operon", "настрой Operon как у тебя", "operon setup", "воспроизведи таск-систему Obsidian", "как у тебя задачи и страницы проектов в Obsidian".
version: 1.0.0
tags: [Obsidian, Operon, Tasks, Setup, ProjectPages]
---

# Operon + Project Pages setup

Reproduce the lab's Operon task-manager setup and project-page conventions in an Obsidian
vault: flat `project` tags, a "my tasks" table dashboard, service-link badges, emoji task
icons, and external day-boundary archiving. Target Operon version **2.2.1** (code patches
in step 6 are version-gated; everything else is version-independent).

## Required input

Resolve before starting:
- **VAULT** — absolute path to the vault. From explicit user input, else `${OBSIDIAN_VAULT}`.
- **OWNER** — task owner name/handle (used for `assignees` and the "my tasks" filter). Ask if unknown.
- **OS** — macOS / Windows / Linux (only step 7 differs; launchd is macOS-only).

Bundled files live under `${CLAUDE_PLUGIN_ROOT}/skills/operon-obsidian-setup/` in `scripts/` and `assets/`.
Read `references/OPERON-SETUP-RUNBOOK.md` for full rationale, the data model, and troubleshooting.

## GUI-only steps (hand to the user, wait for confirmation)

Some steps cannot be done from the filesystem — surface exact clicks and wait:
1. Settings → Community plugins → install & enable **Operon** (2.2.1) and **Dataview**.
2. Dataview → enable **Enable JavaScript Queries** (`enableDataviewJs`).
3. Settings → Appearance → CSS snippets → refresh → enable `project-link-badges` (after step 3 below).
4. Final full **restart** of Obsidian (config is read at startup; live edits do not apply).

## Procedure

1. **Folders.** Create `VAULT/Operon/{Projects,Archives,Templates,Tasks}` and `VAULT/_System/Templates`.

2. **Templates.** Copy into the vault, substituting `<OWNER>` and `<PROJECT>`:
   - `assets/Task.template.md` → `VAULT/Operon/Templates/Task.md` (replace `<OWNER>`).
   - `assets/Project-Page.template.md` → `VAULT/_System/Templates/Project Page.md`.
   - `assets/Project-Literature.template.md` → `VAULT/_System/Templates/Project Literature.md`.

3. **CSS badges.** Copy `assets/project-link-badges.css` → `VAULT/.obsidian/snippets/project-link-badges.css`,
   then trigger the GUI enable step above.

4. **Plugin config.** Run the idempotent configurator (backs up `data.json`, sets the Project status
   pipeline, the `project` custom list field, excluded folders, Task Creator folders/template, disables
   native auto-archive, and adds the `fs_mytasks` filter for OWNER):
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/operon-obsidian-setup/scripts/operon_configure.py" "<VAULT>" "<OWNER>"
   ```

5. **Table preset.** Copy `assets/table-preset.json` →
   `VAULT/.obsidian/plugins/operon/data/table-presets/table-preset-my-first-table.json`
   (back up any existing file first). Ensure its id is listed in the sibling `index.json`.

6. **Dashboard.** Create `VAULT/Dashboard.md` per the runbook (a `dataviewjs` button row that opens
   Kanban/Calendar/Finder + an embedded Operon table `presetId: "table-preset-my-first-table"`).

7. **Display patches (optional).** Status shown without the `Project.` prefix, `assignees` picker
   sourced from `people/` cards, and emoji task icons. Version-gated to Operon 2.2.1; aborts cleanly
   otherwise. Re-run after every Operon update (updates overwrite `main.js`):
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/operon-obsidian-setup/scripts/operon_patches.py" "<VAULT>"
   ```

8. **Auto-archive (optional, macOS).** Install `scripts/operon_daily_archive.py` (dry-run test:
   `--vault "<VAULT>" --dry-run`), then render `assets/com.OWNER.operon-archive.plist.template`
   (substitute `<OWNER>`, `<SCRIPT_PATH>`, `<VAULT>`) into `~/Library/LaunchAgents/` and
   `launchctl load` it. Windows/Linux: schedule the same command via Task Scheduler / cron.

9. **Restart & verify** (GUI restart above), then check: Task Creator writes file-tasks to `Operon/Tasks`
   with the Описание/Прогресс/Результат body and `assignees: [OWNER]`; statuses show without the
   `Project.` prefix; the `project` column is present; `Dashboard.md` renders the table + working buttons;
   external links render as service badges; (if patched) `taskIcon: 🤖` renders as emoji.

## Data model (essentials)

- Every task is an Operon task (`operonId`, `status: Project.<Label>`, `priority: A/B/C`, `dateDue`…).
- **A project is a flat `project` tag, not a `parentTask` hierarchy.** Work tasks carry `project: [Name]`
  (file-task frontmatter) or `{{project:: Name}}` (inline); a task may carry several project tags.
- **Project root tasks** `[PROJECT] <name>.md` live in `Operon/Projects/` (excluded from the index) so
  they never appear in Table/Kanban/Calendar/Finder.
- **Project pages** are prose notes with tasks interleaved via Task Wikilink Overlay
  ("Operon: Add Task Wikilink Overlay"); tasks stay file-tasks in the project folder.

See `references/OPERON-SETUP-RUNBOOK.md` for the full breakdown, the patch table, and maintenance notes.
