---
name: create-project
description: "Create a research project or repair its local and shared setup after checking for an existing project."
---

# Create Project

## Shared publication contract

Before writing shared records, read `lab-knowledge/references/record-contract.md` from the
installed skills directory and the live MCP schema. Use the already authorized scope,
resolve the existing destination, and verify stored content. Keep failed publications pending.


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
склеить — ни доски, ни гипотезы, ни задачи.

Пять мест, все пять обязательны:

1. **Каталог Brain Call** — `~/Staff/BRAIn Lab/claude-brainlab/services/lab-knowledge/data/projects.json`.
   Прочитать `slug`, `legacy_labels`, `display_title`, `summary` каждой записи и сравнить по теме.
2. **Lab Knowledge MCP** — `search_lab` со `scope: lab` по двум-трём разным формулировкам темы
   (название, метод, задача). Поиск отвечает по смыслу, поэтому спрашивать надо словами, а не слагом.
3. **Хранилище Obsidian** — `Papers/**`, `Projects/**`, `Staff/**`. Смотреть не только имена папок:
   `rg` по названию метода и по фамилиям участников внутри карточек проектов.
4. **Файловая система** — `~/Papers`, `~/Projects`, `~/Staff`. Папка без карточки в хранилище — тоже
   существующий проект, просто заброшенный.
5. **Yonote** — страницы коллекции по названию темы, через тот же брокер, что и онбординг.

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
- a `Shared systems` section reserved for stable Lab Knowledge and Yonote links.

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
Any optional Claude registry is a compatibility mirror, never the canonical mapping. Local
paths belong only in the private Obsidian card and agent config. Never publish them to Lab
Knowledge or Yonote.

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
append one entry to `~/Staff/BRAIn Lab/claude-brainlab/services/lab-knowledge/data/projects.json`
with `slug`, unique `public_code`, `legacy_labels` (the filesystem folder name), `display_title`,
an existing `direction`, `summary`, `problem`, `approach`, `status`, `leads`, `members`. Omit the
`lab_knowledge_project_id`, `lab_knowledge_url`, and `yonote` keys until provisioning returns
them.

A paper also needs a research theme: `theme` and `theme_slug`, taken from an existing theme
(`list_themes` on the Lab Knowledge MCP shows the ten of them). The theme is the home of
knowledge in the shared base, so a paper without one leaves its hypotheses invisible to every
question asked at the level of a research area. When no theme fits, use the `Прочее` theme of
the matching direction (`misc-matrix`, `misc-lora`) rather than inventing a new one, and say so
to the owner: a new theme is his call. The onboarding scripts pass the theme into `create_project` and copy it into the catalogue
entry, so nothing has to be remembered here; a project without a theme makes provisioning say
so out loud.

Provisioning then puts the project page **inside its theme card** in Yonote: the collection
root holds theme cards, and a page created there stands next to them and has to be moved by
hand. The card is found by the theme name, and its address is remembered on the theme row. When
the theme is declared but its card does not exist in that collection, provisioning refuses and
names the remedy rather than dropping the page at the root; create the card, or pass
`allow_root_page` when the root is what you actually want. Participants missing from the catalogue go into the owner's own
`~/.config/brain-call/directory.json` under `people` (and `aliases` when the first name is
unambiguous), never hardcoded into the shared repository. Verify with
`brain_call_directory.offered_projects` that the new slug is actually offered.

## 3. Bind Brain Lab projects

For a Brain Lab project, load and execute `lab-project-onboarding` after the private workspace
exists. Pass it the confirmed title, slug, project code, collection, leads, members, status,
paper/repository sources, description inputs, and the private hub location.

The onboarding result must provide stable references for:

- the shared Lab Knowledge project;
- the human-facing Yonote project page;
- the named Yonote Kanban, provisioned `participants_only`.

Write those returned references into the private project card. Do not store a shared Yonote
token, duplicate tasks, hypotheses, evidence, or decisions in Obsidian.

Show the Yonote project and task-board links alongside GitHub and Overleaf. Include the
returned board ID in the private shared-system context and point the repository's agent
instructions to it. Verify discovery from a fresh agent's entry point; a chat-only link does
not complete setup.

For Hermes or another agent performing shared tasks, load
`lab-knowledge/references/yonote-tasks.md` from the installed skills directory. Resolve the
human owner's stable Yonote identity separately from the agent service account. Only tasks
assigned to that owner are eligible. Verify task reading and preserving updates before
declaring the capability ready. Report missing or stale bindings explicitly; do not substitute
a similarly named project's board.

An agent profile or experiment-track name is not automatically a new research project.
Resolve the article the execution belongs to and reuse its page and board. Keep private
execution steps separate from the team's readable milestones; do not create a Yonote board
for Hermes itself.

## 3а. Когда проект заводится по итогам созвона

Разбор созвона умеет сказать, что созвон начинает работу, которой в каталоге нет: в предложении
о месте появляется `new_work` со слагом, названием и одной фразой о сути, а сам созвон при этом
привязан к теме. Это готовая спецификация — не спрашивать её заново:

- `new_work.slug` → слаг проекта, `new_work.title` → `display_title`, `new_work.summary` → `summary`;
- `match_theme_slug` → тема, под которой работа живёт (`theme`, `theme_slug`);
- участники — из состава созвона, включая гостей с плиток; человека, которого нет в каталоге
  лаборатории, завести в `~/.config/brain-call/directory.json`, а не хардкодить в общий репозиторий;
- корень файловой системы и репозитории созвон не знает — их спросить.

Проверку из раздела 0 это НЕ отменяет: модель предлагает слаг по разговору и о соседних работах
лаборатории не знает.

После того как проект заведён, вернуться к созвону и перепривязать его к новой работе
(`brain_call.py --rebind MANIFEST --to-slug <slug>`), иначе разбор так и останется на теме, а
задачам будет некуда лечь: доска принадлежит работе.

## 4. Verify and report

Verify the local folders, repository state, Obsidian mapping, and every returned shared ID/link.
For lab projects, rerun the shared resolution step to prove it returns the same project, page,
and board rather than creating duplicates.

Отчёт — таблицей по местам, а не рассказом. Каждое место называет своё состояние и свой адрес:

| место | состояние | адрес |
|---|---|---|
| Obsidian `Papers/<тема>/<slug>/` | создано / было | путь в хранилище |
| `~/Papers/<slug>/` | создано / было | путь |
| `obsidian-projects.json` | запись добавлена / была | — |
| каталог Brain Call `projects.json` | запись добавлена / была | слаг и код |
| Lab Knowledge | проект создан / найден | `project_id` |
| Yonote страница | создана / найдена | ссылка |
| Yonote доска | создана / найдена | ссылка |
| участники | заведены / были | имена |

Место, до которого не дошли, называется отдельной строкой «не сделано» с причиной. Молчание о
месте читается как «сделано» и однажды оставит проект без доски.

## Safety

- Never delegate the whole workflow to a weaker model.
- Never guess a person, project slug, project code, or access scope.
- Never expose credentials in files, logs, previews, or chat.
- Never create a second writable source for a task or shared research object.
- Stop after a permission error; do not retry with broader credentials.
