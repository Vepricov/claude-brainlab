---
name: create-project
description: "Creates a research project, or repairs its local and shared setup, after checking that no such project already exists. Use when the user says 'create a project', 'new project', 'заведи проект', 'set up a repo for a paper', or a project is missing its hub card, folders, or shared records."
---

# Create Project

## Shared publication contract

Before writing shared records, read `lab-knowledge/references/record-contract.md` from the
installed skills directory. Resolve the existing destination in the tree, verify what is already
written there, and keep failed publications pending.

The rules every write into the lab base must satisfy are in one place and are not
restated anywhere: `~/.claude/skills/lab-knowledge/references/canon.md`, mirrored from
`brainlab/handbook/canon.md`. Read it when the write goes into a work, the handbook
or the journal; it also says which of the three a given thing belongs in.


Create the private working layer first. For a Brain Lab project, continue with
`lab-project-onboarding`; do not reproduce its shared-system logic here.

Перед работой с хранилищем прочитать соглашения:
`general/Knowledge/obsidian-conventions.md` (темы в `Papers/`, смайлики и
цвета папок, что нельзя создавать). Папке нового проекта нужен смайлик и цвет
своей темы.


Create the private working layer first. For a Brain Lab project, continue with
`lab-project-onboarding`; do not reproduce its shared-system logic here.

Перед работой с хранилищем прочитать соглашения:
`general/Knowledge/obsidian-conventions.md` (темы в `Papers/`, смайлики и
цвета папок, что нельзя создавать). Папке нового проекта нужен смайлик и цвет
своей темы.

## 0. Prove the project does not already exist

**Никогда не заводить проект, не убедившись, что его нет.** Проверять по СМЫСЛУ, а не по имени:
та же работа лежит под слагом `tsd-lora`, под названием «Низкоранговая адаптация с TSD» или под
фамилией студента, и совпадения строк не будет. Один и тот же проект в двух местах потом не
склеить — ни доски, ни утверждения, ни задачи.

Пять мест, все пять обязательны:

1. **Каталог Brain Call** — `~/brainlab/agents/claude-brainlab/services/lab-knowledge/data/projects.json`.
   Прочитать `slug`, `legacy_labels`, `display_title`, `summary` каждой записи и сравнить по теме.
2. **Дерево базы в GitLab** — список проектов направления и темы, `list_projects` или
   страница группы. Искать по смыслу: названием метода, задачей, фамилией. `search_lab`
   со `scope: lab` для этого больше не годится — эта половина поиска отвечает отказом с
   переездом знания в git.
3. **Хранилище Obsidian** — `Papers/**`, `Projects/**`, `Staff/**`. Смотреть не только имена папок:
   `rg` по названию метода и по фамилиям участников внутри карточек проектов.
4. **Файловая система** — `~/brainlab/<направление>/<тема>/`. Папка без README — тоже
   существующий проект, просто заброшенный.
5. **Задачи в GitLab** — открытые задачи работ темы и группы `ops`: работа часто начинается
   задачей раньше, чем папкой.

Нашлось похожее — **остановиться и показать владельцу**: что нашлось, где, чем похоже и чем
отличается. Решает он. Ни одного из пяти мест не пропускать молча: «я посмотрел по имени, не нашёл»
— это не проверка, а её имитация.

Ничего не нашлось — сказать об этом одной строкой в предпросмотре, назвав, где именно искал.

## 1. Collect one project specification

Resolve existing values before asking. Collect only missing fields:

- filesystem root: `Papers`, `Projects`, or `Staff`;
- folder name and stable slug;
- code repository and paper repository, if any;
- SSH hosts, collaborators, organization, target venue, status, and topic tags;
- Kanban access is always `participants_only`; do not ask for it;
- whether this is a Brain Lab project.

Use `~/.Codex/obsidian-projects.json` as the authoritative filesystem-to-vault mapping. If it
does not exist, follow the current `AGENTS.md` routing rules and create the Codex registry only
after approval; do not silently treat a Claude registry as authoritative. Show
one preview with planned paths, clones, hub card, participants, and, for a lab project, the
shared onboarding handoff. Obtain approval before creating directories, cloning repositories,
or updating shared systems.

## 2. Create the private workspace

Create the minimum requested folder structure and a project-root `AGENTS.md`. Create or mirror
`.claude/CLAUDE.md` only when the user explicitly wants Claude compatibility. Clone only repositories
the user supplied. When an Overleaf repository exists, identify the actual main TeX file and
verify its existing build workflow; do not impose a new layout or overwrite repository config.

Write the project card to the vault path resolved from `obsidian-projects.json`. Include:

- a concise project summary;
- linked participant cards already confirmed by the user;
- local repository paths for private use;
- literature links already present in the vault;
- a `Shared systems` section with the work's GitLab repository and its Overleaf manuscript.

The vault owner is the default project lead. Do not name him in the card, do not link a person
card for him, and do not list him under `участники` — write only the other participants. Name a
lead explicitly only when someone else leads the project.

Copy the frontmatter shape from an existing card such as `Papers/Матричная оптимизация/dykaf/dykaf.md`: the same key
order, one existing person-link style, and no key whose value is unknown. An unresolved binding
is an absent key, never an empty string or a status sentence; record what is still missing in the
`Shared systems` section instead.

Project status lives in the `статус/…` tag and nowhere else. Do not add a `brainlab_status` key.
Read the tag when the lab catalogue or an onboarding call needs a status: `статус/завершён` is
finished, and everything before it — `статус/идея`, `статус/планирование`, `статус/черновик`,
`статус/активный`, `статус/почти-готово`, `статус/подано` — is an active project.

Register the project in the Codex `obsidian-projects.json` without replacing unrelated entries.
Local paths belong only in the private card and the agent config: the tree is the same on no
other machine, so a path published into the base is noise for everyone who reads it.

Give the vault folder its icon and colour, the way every other project folder has one. Both
plugins live in `<vault>/.obsidian/plugins`:

- `iconic/data.json` → `fileIcons`: one emoji for `<Root>/<slug>` and the same emoji for
  `<Root>/<slug>/<slug>.md`. Pick an emoji that is not already used by another project and that
  says what the project is about.
- `obsidian-file-color/data.json` → `fileColors`: append `{"path": "<Root>/<slug>", "color":
  "<paletteId>"}` reusing the palette id of the project's topic — `optimMint01` for optimizer
  work, `loraBlueSoft01` for LoRA and PEFT, `zoCoral01` for ZO, `rlViolet01` for RL. Read the
  palette before choosing; never invent a colour value.

Obsidian caches plugin settings in memory, so tell the user to reload the app for the icon and
colour to appear, and write both files while Obsidian is idle.

Register the project in the Brain Call catalogue so it can be picked when recording a call:
append one entry to `~/brainlab/agents/claude-brainlab/services/lab-knowledge/data/projects.json`
with `slug`, unique `public_code`, `legacy_labels` (the filesystem folder name), `display_title`,
an existing `direction`, `summary`, `problem`, `approach`, `status`, `leads`, `members`.

A paper also needs a research theme: `theme` and `theme_slug`, taken from an existing theme —
the themes are the directories of the tree, `~/brainlab/<area>/<theme>/`. The theme is the home of
knowledge in the shared base, so a paper without one leaves its hypotheses invisible to every
question asked at the level of a research area. When no theme fits, use the `Прочее` theme of
the matching direction (`misc-matrix`, `misc-lora`) rather than inventing a new one, and say so
to the owner: a new theme is his call. The onboarding scripts pass the theme into `create_project` and copy it into the catalogue
entry, so nothing has to be remembered here; a project without a theme makes provisioning say
so out loud.

Participants missing from the catalogue go into the owner's own
`~/.config/brain-call/directory.json` under `people` (and `aliases` when the first name is
unambiguous), never hardcoded into the shared repository. Verify with
`brain_call_directory.offered_projects` that the new slug is actually offered.

## 3. Create the work in the base

A work of the base is one GitLab repository inside its theme group, and the local clone lives in
the tree at `~/brainlab/<area>/<theme>/<work>`. Nothing else binds them: the path is the binding.

1. Create the project in the theme group of `brainlab` (the lead and the lab get access by the
   group, so no per-repository grant is needed).
2. Clone it into the tree at its path, next to the other works of that theme.
3. Write the root `README.md`: the title, one paragraph of what the work is about, the line
   `**Ведёт** [Name](<GitLab profile>)` — the lead's login is what every proposal is assigned to
   — and the participants.
4. Configure the clone so a push opens a proposal:
   `git config --add push.pushOption merge_request.create` and
   `git config --add push.pushOption merge_request.assign=<lead login>`.
5. The first claims are folders: `claims/<CODE>/README.md`. For a work that already exists on
   disk with a manuscript, `services/scripts/claims/new_work.py` builds the skeleton from the
   paper instead of writing it by hand.

Tasks live as issues in that same repository, and the session-start hook reads them back.

## 4. Verify and report

Verify the local folders, the repository state and the clone's remote. For a lab work, check that
the path in the tree matches the GitLab path, that the README names the lead, and that a push
opens a proposal assigned to them. Report created, reused, skipped, and blocked items separately.

## Safety

- Never delegate the whole workflow to a weaker model.
- Never guess a person, project slug, project code, or access scope.
- Never expose credentials in files, logs, previews, or chat.
- Never create a second writable source for a task or shared research object.
- Stop after a permission error; do not retry with broader credentials.

## Tasks assigned to the human owner

Tasks are issues in the work's own GitLab repository. Work only on issues assigned to the
confirmed human owner, keep the assignee and the issue number, and name in the issue body the
claim it affects — that is what ties a task to knowledge. Keep the repository link alongside
GitHub and Overleaf in the private project context.
