# Operon + Project Pages — full runbook

Detailed reference for the `operon-obsidian-setup` skill. Reproduces the lab's Operon
task-manager configuration and project-page conventions in an Obsidian vault. Target
Operon version **2.2.1**.

Placeholders: `<VAULT>` = absolute vault path, `<OWNER>` = task owner name/handle.
All config changes apply **only after a full Obsidian restart** (Operon reads settings at startup;
editing its files live does not auto-apply — or use `operon:reload-settings-from-storage` +
`operon:rebuild-index`).

Bundled files (relative to the skill folder): `scripts/operon_configure.py`,
`scripts/operon_patches.py`, `scripts/operon_daily_archive.py`, `assets/project-link-badges.css`,
`assets/table-preset.json`, `assets/Task.template.md`, `assets/Project-Page.template.md`,
`assets/Project-Literature.template.md`, `assets/com.OWNER.operon-archive.plist.template`.

---

## 1. Data model

- All tasks are Operon tasks (`operonId` + `status: Project.<Label>` + `priority: A/B/C` + `dateDue`…).
- **A project is a flat `project` tag, not a hierarchy.** Work tasks do NOT use `parentTask`; project
  membership is the custom `project` list field (several values allowed).
- **Project root tasks** `[PROJECT] <name>.md` are file-task "entities" kept in `Operon/Projects/`, which
  is excluded from the index, so they never show up in Table/Kanban/Calendar/Finder.

## 2. Taxonomy

**Status pipeline** (single, named `Project`):
`Brainstorming · Planned · InProgress · Finished · Paused · Dropped`
Stored as `Project.Planned`, `Project.Finished`, … The pipeline-name prefix cannot be removed natively
(display patch #1/#2 in §6 strips it for display only).

**Custom field** `project` (`taxonomy.keyMappings.custom` in `data.json`): type `list`, icon `folders`.
Value format: file-task `project: [MultiAgents, Zero-order]`; inline `{{project:: MultiAgents, Zero-order}}`.

The configurator (`scripts/operon_configure.py`) writes both.

## 3. Folder structure

| Folder | Role | In Operon index? |
|---|---|---|
| `Papers/`, `Projects/` (user projects) | work tasks (file + inline) | yes |
| `Operon/Projects/` | project roots `[PROJECT] <name>.md` | **no** (excluded) |
| `Operon/Archives/` | archive (parked / finished) | **no** (excluded) |
| `Operon/Templates/` | file-task templates | templates, not tasks |
| `Operon/Tasks/` | new file-tasks from Task Creator | yes |

Create: `VAULT/Operon/{Projects,Archives,Templates,Tasks}` and `VAULT/_System/Templates`.

## 4. Plugin config (`operon_configure.py`)

Idempotent; backs up `data.json` before writing. Run:
```bash
python3 scripts/operon_configure.py "<VAULT>" "<OWNER>"
```
It sets:
- `taxonomy.pipelines` — the single `Project` pipeline (six statuses above).
- `taxonomy.keyMappings.custom` — appends the `project` list field if absent.
- `settings.excludedFolders` — `["Operon/Archives", "Operon/Projects"]`.
- `ui.taskCreationProfile` — `fileTasksFolder: Operon/Tasks`, `fileTaskTemplateFolder: Operon/Templates`,
  `taskCreatorDefaultFileTemplateId: folder-file-task-template:Operon/Templates/Task.md`.
- `automation.taskAutomationPolicy.fileTaskAutoArchiveEnabled: false` (external cron does day-boundary archiving).
- `views.filters.fs_mytasks` — `assignees anyContains <OWNER>` (the "my tasks" filter used by the table preset).

Applies cleanly to a fresh Operon install; on an existing install it MERGES (replaces the status pipeline,
appends the field/filter only if missing). Restart Obsidian afterwards.

## 5. Table preset "tasks"

Copy `assets/table-preset.json` → `VAULT/.obsidian/plugins/operon/data/table-presets/table-preset-my-first-table.json`
(back up any existing one). Key points: `name: "tasks"`, `filterSetId: "fs_mytasks"` (only OWNER's tasks),
`project` column added at the end of the visible columns. Make sure the sibling `index.json` lists the preset id.

## 6. Code patches (`operon_patches.py`) — optional, display-only

Single idempotent script. Backup of the original: `main.js.prepatch` in the plugin dir. Patches change only
display/suggestions; stored data is untouched. Bound to Operon **2.2.1**: on another version the anchors won't
match and the script aborts without a partial write.

```bash
python3 scripts/operon_patches.py "<VAULT>"
```

| # | Function | Effect |
|---|---|---|
| 1 | `rre` | table status without the pipeline prefix (`Project.Finished` → `Finished`) |
| 2 | `Jn` | same for compact chips (Finder / overlays) |
| 3 | `e8` | `assignees` suggestions also sourced from `people/` cards (`имя` → `name` → basename) |
| 4 | `Xp` | **emoji as task icon**: a non-Lucide `taskIcon` (has chars outside `[a-z0-9-]`) is drawn as text |
| 5 | Task Creator toolbar | icon preview in the creator draws emoji |
| 6 | Task Editor swatch | icon preview in the editor draws emoji |
| 7 | icon picker source | the task-icon grid picker offers an emoji palette instead of Lucide (`_EMOJI` in the script) |
| 8 | icon picker cell | picker cells draw emoji as text |
| 9 | `vv` resolver | lets an emoji `taskIcon` pass through instead of being swapped for a Lucide fallback |

- ⚠️ **Any Operon update overwrites all patches** → re-run the script after each update.
- Emoji icon is set by value, not the picker: `taskIcon: 🤖` (frontmatter) or `{{taskIcon:: 🤖}}` (inline).
  Lucide names (`network`, `shield-alert`) still render as SVG.
- Patch #3 reads top-level cards in `people/` (frontmatter `имя:`/`name:`, else the filename). Add a
  collaborator by creating `VAULT/people/<name>.md`.
- The status patch does not affect Obsidian's native Properties panel (still raw `Project.Finished` there).
- The emoji set is edited in the `_EMOJI` list inside `operon_patches.py`.

## 7. Templates

### `Operon/Templates/Task.md` (from `assets/Task.template.md`, replace `<OWNER>`)
```markdown
---
assignees: [<OWNER>]
---
# {{taskDescription}}

## Описание


## Прогресс


## Результат
```
`assignees: [<OWNER>]` defaults new file-tasks to the owner (required for the "my tasks" filter).
Supported vars: `{{taskDescription}}`, `{{date}}`, `{{datetime}}`, `{{note}}`, `{{dateStarted}}`,
`{{dateScheduled}}`, `{{dateDue}}`. (Applies to file-tasks only; inline tasks are single lines.)

### Project page & literature templates
`assets/Project-Page.template.md` → `_System/Templates/Project Page.md`,
`assets/Project-Literature.template.md` → `_System/Templates/Project Literature.md`.
If the vault is not Russian, translate the section headers; keep the frontmatter schema.

## 8. Project-page convention

A project = folder `Papers/<project>/` (or `Projects/<project>/`) with:
- `<Project> (проект).md` — the project page (template above). Order: **links block → description →
  link to literature → Work history → Problems → Reports**.
- `<Project> — литература.md` — a MOC of the project's papers, linking into the global `Literature/`.
- `Reports/` — weekly reports. `Проблемы/` — problem / inconsistency notes.
- work/analysis notes live in the folder root, linked from Work history.

The page is a **prose note with tasks interleaved via Task Wikilink Overlay** (Operon v1.8+). A
`[[Task name]]` link to a file-task renders in Reading/Live Preview as an interactive task row (checkbox,
status, emoji icon, chips); the edit action opens the Task Editor with the full body
(Описание/Прогресс/Результат). Insert one via the command **"Operon: Add Task Wikilink Overlay"**
(Task Finder → pick or create → link inserted at the cursor). Tasks remain file-tasks in the project folder.

**Service-link badges** (`assets/project-link-badges.css` → `VAULT/.obsidian/snippets/`): a normal external
link to github/arxiv/huggingface/overleaf/wandb/google-docs auto-renders as a badge with that service's logo
(Reading/Live Preview). Add a new service with an `a.external-link[href*="domain"]` selector. Enable the
snippet in Settings → Appearance → CSS snippets.

## 9. Dashboard

Operon embeds **only Table and Filter** in a note (Kanban/Calendar are full panes). So the dashboard is an
embedded table plus a button row that opens the other surfaces. Create `VAULT/Dashboard.md`:

````markdown
---
type: dashboard
---
# Дашборд

```dataviewjs
const cmds = [
  ["📋 Kanban", "operon:open-kanban-view"],
  ["📅 Calendar", "operon:open-calendar-view"],
  ["🔍 Task Finder", "operon:open-task-finder"],
  ["📌 Pinned dock", "operon:toggle-pinned-dock"],
  ["♻️ Rebuild index", "operon:rebuild-index"],
];
const bar = dv.el("div", "", { cls: "operon-dash-bar" });
bar.style.cssText = "display:flex;gap:8px;flex-wrap:wrap;margin:.5em 0";
for (const [label, id] of cmds) {
  const b = bar.createEl("button", { text: label });
  b.style.cssText = "padding:4px 10px;border-radius:7px;cursor:pointer";
  b.onclick = () => app.commands.executeCommandById(id);
}
```

## Все задачи

```operon
presetId: "table-preset-my-first-table"
```
````

> Command ids may differ between Operon versions. If a button does nothing, open the command palette
> (⌘/Ctrl-P), type "Operon", and substitute the current `commandId` (inspect `app.commands.commands` in the
> developer console). Requires Dataview with `enableDataviewJs`.

## 10. Auto-archive (optional, macOS — launchd)

Operon can archive only with a fixed delay ≤ 1 hour; "at the new day boundary" is not native. The external
cron (`scripts/operon_daily_archive.py`) moves file-tasks with status `Project.Finished`/`Project.Cancelled`
whose completion date is **strictly before today** into `Operon/Archives`. Inline checkboxes and tasks without
`operonId` are never touched. Test first:
```bash
python3 scripts/operon_daily_archive.py --vault "<VAULT>" --dry-run
```
Install the script (e.g. `~/.local/bin/`), then render `assets/com.OWNER.operon-archive.plist.template`
(substitute `<OWNER>`, `<SCRIPT_PATH>`, `<VAULT>`) into `~/Library/LaunchAgents/com.<OWNER>.operon-archive.plist`
and load it:
```bash
launchctl unload "$HOME/Library/LaunchAgents/com.<OWNER>.operon-archive.plist" 2>/dev/null
launchctl load  "$HOME/Library/LaunchAgents/com.<OWNER>.operon-archive.plist"
```
Runs daily at 00:05 **and** at each login (`RunAtLoad` catches up if the Mac slept at 00:05). Logs:
`~/Library/Logs/operon-archive.{log,err}`. After files move into the excluded `Operon/Archives`, Obsidian must
reindex (restart or `operon:rebuild-index`) to drop them from open views.

**Windows/Linux:** no launchd. Schedule the same `python3 operon_daily_archive.py --vault "<VAULT>"` daily via
Task Scheduler (Windows) or cron / systemd-timer (Linux). The script is cross-platform.

## 11. Verification checklist

- [ ] Task Creator makes file-tasks in `Operon/Tasks/` from the template (Описание/Прогресс/Результат), `assignees: [<OWNER>]`.
- [ ] Statuses are `Brainstorming/Planned/InProgress/Finished/Paused/Dropped`, shown in the table **without** the `Project.` prefix.
- [ ] The table has a `project` column; the `project` field is available in Creator/Editor.
- [ ] `Dashboard.md` shows the table (OWNER's tasks only) + a working button row.
- [ ] An external github/arxiv/… link renders as a logo badge in Reading view.
- [ ] (If patched) `taskIcon: 🤖` renders as emoji in the table.
- [ ] (macOS) `operon_daily_archive.py --vault "<VAULT>" --dry-run` runs without error.

## 12. Maintenance

- **After every Operon update**: re-run `operon_patches.py "<VAULT>"` — updates overwrite `main.js`.
  `data.json` settings/presets/fields survive updates.
- **New active project**: create `Operon/Projects/[PROJECT] <name>.md` (a file-task with `operonId`); tag its
  tasks `project: [<name>]`. Do not use `parentTask`.
- **New collaborator** (for assignee suggestions): create `people/<name>.md` with frontmatter `имя:` (or `name:`).
- **Change archive timing**: edit `StartCalendarInterval` in the plist, then `launchctl unload/load`.
- **Backups**: `operon_configure.py` writes `data.json.bak-*`; `operon_patches.py` writes `main.js.prepatch`.
