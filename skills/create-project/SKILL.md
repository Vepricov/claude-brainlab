---
name: create-project
description: "Creates a new lab work (one GitLab repository in its theme, cloned into ~/brainlab at the same path), or repairs an existing work's setup, after checking that no such work already exists. Use when the user says 'create a project', 'new project', 'заведи проект', 'заведи работу', 'set up a repo for a paper', or a work is missing its README, people lines, local folders or clone settings."
---

# Заведение работы

Лаборатория это GitLab как «GitHub для идей»: группы `brainlab` → направление → тема → работа,
одна работа это один репозиторий. Локально всё дерево лежит в `~/brainlab` ровно по путям
GitLab: работа `brainlab/<направление>/<тема>/<работа>` живёт в
`~/brainlab/<направление>/<тема>/<работа>`. Путь и есть привязка, файлов сопоставления нет.

`main` в работе защищён (push: никто, слияние: Maintainers). Единственное исключение это
**первый push в пустой проект**: поэтому README и каркас уходят именно им, а всё после — через
предложение (merge request).

Перед записью в базу прочитать свод `~/.claude/skills/lab-knowledge/references/canon.md`.
Иконки и цвета папок — по разделу «Иконки и цвета» в
`~/brainlab/personal/general/Knowledge/obsidian-conventions.md`.

## 0. Убедиться, что такой работы нет

**Никогда не заводить работу, не убедившись, что её нет.** Проверять по СМЫСЛУ, а не по имени:
та же работа лежит под слагом `tsd-lora`, под названием «Низкоранговая адаптация с TSD» или под
фамилией студента, и совпадения строк не будет. Одну работу в двух местах потом не склеить.

Четыре места, все обязательны:

1. **Дерево** — `ls ~/brainlab/<направление>/<тема>/` и соседние темы; `rg -i` по названию
   метода и фамилиям в `~/brainlab/*/*/*/README.md`. Папка без README тоже существующая работа.
2. **GitLab** (только GET, ключ в `~/.config/brainlab/git-token`, адрес в
   `~/.config/brainlab/git-url`):
   ```bash
   U=$(cat ~/.config/brainlab/git-url); H="PRIVATE-TOKEN: $(cat ~/.config/brainlab/git-token)"
   curl -s -H "$H" "$U/api/v4/groups/brainlab%2F<направление>%2F<тема>/projects?simple=true&per_page=100"
   curl -s -H "$H" "$U/api/v4/projects?search=<слово>&simple=true&per_page=100"
   ```
   В дереве видно только то, что уже склонировано; работа без доступа у тебя не видна вовсе.
3. **Задачи** — `GET $U/api/v4/groups/brainlab%2F<направление>/issues?search=<слово>&state=opened`:
   работа часто начинается задачей раньше, чем репозиторием.
4. **Заметки владельца** — `notes/` соседних работ: идея могла жить там до работы.

Нашлось похожее — **остановиться и показать владельцу**: что, где, чем похоже и чем отличается.
Решает он. Не нашлось — сказать одной строкой, назвав, где искал.

## 1. Собрать описание и показать предпросмотр

Сначала взять то, что уже известно, спрашивать только недостающее:

- направление и тема (существующие: `ls ~/brainlab/<направление>/`); не подходит ни одна —
  раздел 4;
- слаг работы (латиница, kebab-case) и название;
- код работы: три буквы, не занятые никем:
  `grep -h '^code:' ~/brainlab/*/*/*/README.md; ls ~/brainlab/*/*/*/claims/ | cut -d- -f2 | sort -u`;
- один абзац о том, что это за работа;
- **кто ведёт работу — спросить владельца, не угадывать по тому, кто попросил** (ведущих может
  быть двое, предложения назначаются первому), и кто в команде; логины GitLab;
- репозитории кода и рукописи, если есть.

Показать один предпросмотр: путь в GitLab и в дереве, код, README целиком, ведущие и команда.
Создавать только после согласия.

## 2. Создать работу

1. **Пустой проект в GitLab.** Это единственная запись через API в этом навыке:
   ```bash
   G=$(curl -s -H "$H" "$U/api/v4/groups/brainlab%2F<направление>%2F<тема>" | python3 -c 'import json,sys;print(json.load(sys.stdin)["id"])')
   curl -s -X POST -H "$H" "$U/api/v4/projects" \
     --data-urlencode "name=<слаг>" --data-urlencode "path=<слаг>" \
     --data "namespace_id=$G&visibility=internal&initialize_with_readme=false"
   ```
   Без README: проект с README уже имеет защищённый `main`, и шапка войдёт только предложением.
   Доступ ведущим и лаборатории даётся группой, поштучно ничего не выдаётся.
2. **Клон на место:** `lab here <слаг>`. Он кладёт работу в `~/brainlab/<направление>/<тема>/<слаг>`,
   пишет `.git/info/exclude` (`notes/`, `daily/`, `/runs/`, `paper/drafts/`, `code/local/`,
   `calls/raw/`, `.claude/`, `.DS_Store`), `push.default current` и
   `push.pushOption merge_request.create`. Ведущего он пока не знает: README ещё нет.
3. **Личные папки:** `cd` в работу, `mkdir notes daily runs`. Они только на машине и не
   коммитятся никогда.
4. **README и каркас.** `git checkout -B main` (пустой клон может стоять на `master`). README по
   образцу `~/brainlab/matrix-optimization/preconditioning-curvature/dykaf/README.md`:
   ```markdown
   ---
   code: <КОД>
   work: <слаг>
   status: active
   kind: paper
   updated: <YYYY-MM-DD>
   ---
   # <Название>

   **Состояние** заведена <DD-MM-YYYY> · **тема** <тема>

   <Один абзац: что за работа.>
   ```
   Никаких локальных путей, никаких личных заметок: README читает вся лаборатория. Код и рукопись
   называются в обратных кавычках (`code/`, `paper/`); подключаются они вложенными
   репозиториями `git submodule add <url> code/<имя>` и `paper/<имя>`. Каркас: `claims/`
   (пустая папка с `.gitkeep`, если утверждений ещё нет) и `.gitlab/` с шаблонами задачи и
   предложения, одинаковыми во всех работах:
   `git -C ~/brainlab/matrix-optimization/preconditioning-curvature/dykaf archive HEAD .gitlab | tar -x`.
   Позже рядом появятся `socials/` (посты) и `calls/` (разборы звонков, сырьё в `calls/raw/`).
5. **Ведут и Команда** пишет скрипт, руками эти строки не набирать:
   ```bash
   python3 ~/brainlab/agents/services/scripts/sostav_readme.py --работа <слаг> \
     --ведут <логин>[,<логин>] [--команда <логин>,<логин>]
   ```
   Кого нет ни в одном README дерева, назвать парой `логин:Имя Фамилия`.
6. **Первый push** — прямо в пустой `main`, без опции предложения:
   ```bash
   git add README.md claims .gitlab   # вложенные репозитории submodule add уже добавил
   git status --short                 # notes/ daily/ runs/ здесь быть не должно
   git commit -m "Работа заведена: шапка README"
   git -c push.pushOption= push -u origin main
   ```
7. **`lab here <слаг>` ещё раз.** Теперь README на `main`, и клон получает
   `merge_request.assign=<первый из «Ведут»>`. Дальше всё — веткой и `git push`, предложение
   откроется само и встанет на ведущего.
8. **Первые утверждения** — папки `claims/<КОД>/README.md`, уже предложением. Если у работы
   есть рукопись в `paper/`, каркас утверждений из неё строит
   `python3 ~/brainlab/agents/services/scripts/claims/new_work.py ~/brainlab/<направление>/<тема> <слаг>`.
   Он вызывает модель (`claude -p`), поэтому только с согласия владельца; README он не трогает.

Задачи работы это задачи (issues) этого же репозитория; начало сессии читает их само.

## 3. Проверить и доложить

- `git -C <работа> ls-tree -r --name-only HEAD` — только README, `claims/`, `.gitlab/`
  (и вложенные репозитории); ни `notes/`, ни `daily/`, ни `runs/`;
- `git -C <работа> config --get-all push.pushOption` — есть `merge_request.create` и
  `merge_request.assign=<ведущий>`; `git config push.default` — `current`;
- путь в дереве совпадает с путём в GitLab, проект `internal`, `main` защищён;
- `python3 ~/brainlab/agents/services/scripts/sostav_readme.py --работа <слаг>` показывает ведущих.

Доложить отдельно: что создано, что уже было, что пропущено и что упёрлось в права.

## 4. Новая тема, если работе нужна

Тема это группа GitLab внутри направления, и новая тема — решение владельца. Сначала проверить,
не подходит ли существующая тема направления. **Тема без ответственного это тема, на заявки
в которую некому ответить**: состав группы ведёт только её Owner, а Maintainer получает `403`.
Поэтому перед созданием спросить и без ответа не создавать:

> Кто ведёт эту тему? Их может быть несколько. Главный по теме — владелец её группы: ему
> приходят заявки на доступ в тему, и он решает, кого в неё принять.

Группа создаётся `POST /groups` с `parent_id` группы направления и `visibility=internal`, затем
владельцы ставятся так:

```bash
LAB_GITLAB_URL=$(cat ~/.config/brainlab/git-url) LAB_GITLAB_TOKEN=<ключ с правами Owner> \
  python3 ~/brainlab/agents/services/scripts/gitlab_people.py главные \
  --тема <направление>/<тема> --отвечает <логин>,<логин>
```

Без этих переменных скрипт стучится в `127.0.0.1:9080`, то есть работает только на сервере базы.

Заявка в работу идёт её ведущим, в тему — владельцам темы, в саму базу — владельцам
лаборатории. Где ведущих нет, заявка поднимается на уровень выше.

## Безопасность

- Не отдавать весь процесс более слабой модели.
- Не угадывать человека, слаг, код и права доступа.
- Ключ не печатать и не писать в файлы, логи, предпросмотр и в адрес `origin`.
- Не заводить второе место для той же работы или задачи.
- После отказа в правах остановиться и не повторять с более широким ключом.
