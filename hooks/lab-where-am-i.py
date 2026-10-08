#!/usr/bin/env python3
"""Сказать агенту в начале сессии, ГДЕ он и ЧТО его ждёт. Только состояние, коротко.

Владелец 02-10-2026: «в хуке максимально коротко, аккуратно, чтобы он просто делал это, не
забывал. В `.claude` должно быть описано, как именно это делать аккуратно». Отсюда
разделение, и оно здесь главное: **хук печатает только то, что меняется от сессии к
сессии** — где клон, какие утверждения, что пришло в main, что открыто, что поручено. Как
писать, по каким правилам, что в теле предложения — лежит в `~/.claude/rules/lab.md` и
читается один раз. Прежний хук печатал восемь строк правил каждую сессию: это те же
токены, умноженные на число сессий.

Он же 25-09-2026: «нужно сделать так, чтобы агент тратил минимум токенов, читал минимум
информации… он один раз должен понять про гит и туда уже постоянно писать».

Работа определяется каталогом сессии по той же карте, что и заметки: `~/Papers/dykaf` — это
работа `dykaf`. Ни поиска, ни вызовов базы: файл карты и файл утверждений с диска.
"""

from __future__ import annotations

import json
import os
import time
import re
import select
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

REGISTRY = Path("~/.claude/obsidian-projects.json").expanduser()
#: Где искать файлы базы. На машине сотрудника рабочей копии обычно нет, и тогда список
#: утверждений берётся из слепка: он обновляется при каждом заходе и читается мгновенно,
#: без единого обращения к службе. Агент не должен тратить вызовы на «а где я».
BASE = Path(os.getenv("LAB_KNOWLEDGE_BASE_DIR", "~/brainlab-stack/git-base")).expanduser()
CACHE = Path("~/.local/state/brainlab/claims").expanduser()
FRONT = re.compile(r"\A---\n(.*?)\n---\n", re.S)


#: Где спрашивать про открытые предложения. Адрес публичный: хук живёт на машине человека,
#: и туннель до петли на ней может быть не поднят.
BASE_URL = os.getenv("BRAINLAB_GIT_URL", "https://68-183-24-188.sslip.io:9445")
TOKEN_FILE = Path("~/.config/brainlab/git-token").expanduser()


def path_of_work(slug: str) -> str:
    """Полный путь работы в дереве групп. Запоминается: он не меняется.

    Единица базы — работа, и у неё свой проект внутри группы темы. Слаг человек помнит, а
    полный путь нет, поэтому он ищется один раз и кладётся рядом со слепком утверждений.
    """
    remembered = CACHE / f"{slug}.path"
    if remembered.is_file():
        found = remembered.read_text(encoding="utf-8").strip()
        if found:
            return found
    if not TOKEN_FILE.is_file():
        return ""
    try:
        request = urllib.request.Request(
            f"{BASE_URL}/api/v4/groups/brainlab/projects"
            f"?include_subgroups=true&simple=true&search={slug}&per_page=100",
            headers={"PRIVATE-TOKEN": TOKEN_FILE.read_text(encoding="utf-8").strip()})
        with urllib.request.urlopen(request, timeout=4) as answer:
            found_items = json.loads(answer.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 — начало сессии не роняется из-за сети
        return ""
    exact = [project for project in found_items if project.get("path") == slug]
    if not exact:
        return ""
    path = str(exact[0]["path_with_namespace"])
    try:
        CACHE.mkdir(parents=True, exist_ok=True)
        remembered.write_text(path + "\n", encoding="utf-8")
    except OSError:
        pass
    return path


def open_proposals(work: str) -> list[str]:
    """Открытые предложения этой работы: номер, утверждение, заголовок.

    Это самое скоропортящееся, что агенту нужно знать перед записью, и самое дорогое,
    когда он этого не знает: 30-09-2026 агент доложил про pull request №2, давно
    закрытый, потому что взял номер из своей прошлой памяти. Карточка работы весит под
    двести килобайт, и блок про предложения в её конце до него не дошёл.

    Стоит это ноль токенов модели и один запрос к базе. Не ответила — молчим: сказать
    «я в работе такой-то» полезно и без этого.
    """
    full_path = path_of_work(work)
    if not full_path or not TOKEN_FILE.is_file():
        return []
    try:
        token = TOKEN_FILE.read_text(encoding="utf-8").strip()
        request = urllib.request.Request(
            f"{BASE_URL}/api/v4/projects/{urllib.parse.quote(full_path, safe='')}"
            f"/merge_requests?state=opened&per_page=20",
            headers={"PRIVATE-TOKEN": token})
        # Сертификат выписан на sslip.io и настоящий, но хук не имеет права падать из-за
        # чужой связи, поэтому проверка мягкая и таймаут короткий.
        with urllib.request.urlopen(request, timeout=3) as answer:
            opened = json.loads(answer.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 — начало сессии не роняется из-за сети
        return []
    lines = []
    for proposal in opened:
        branch = str(proposal.get("source_branch") or "")
        label = branch.removeprefix("claim/") if branch.startswith("claim/") else branch
        # Неснятое замечание — главное, что надо знать о своём предложении: зелёный вердикт
        # про него молчит, а предложение с ним не готово. Владелец 03-10-2026: «агент должен
        # видеть их и, если что, поправить».
        left = unresolved_count(full_path, token, int(proposal.get("iid") or 0))
        tail = f" — замечаний к снятию: {left}" if left else ""
        lines.append(f"!{proposal.get('iid')} {label[:14]} "
                     f"{str(proposal.get('title') or '')[:48]}{tail}")
    return lines


def unresolved_count(full_path: str, token: str, number: int) -> int:
    """Сколько нитей обсуждения ждут правки. Вердикт службы за замечание не считается."""
    if not number:
        return 0
    try:
        request = urllib.request.Request(
            f"{BASE_URL}/api/v4/projects/{urllib.parse.quote(full_path, safe='')}"
            f"/merge_requests/{number}/discussions?per_page=100",
            headers={"PRIVATE-TOKEN": token})
        with urllib.request.urlopen(request, timeout=3) as answer:
            threads = json.loads(answer.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 — начало сессии не роняется из-за сети
        return 0
    left = 0
    for thread in threads:
        notes = [note for note in (thread.get("notes") or []) if not note.get("system")]
        if not notes or "Проверка базы" in (notes[0].get("body") or ""):
            continue
        if not notes[0].get("resolved"):
            left += 1
    return left


#: Хранилище ключа, которое пишет сам `lab`. Хуку важно ходить ТОЛЬКО через него.
CREDENTIALS_FILE = Path("~/.config/brainlab/git-credentials").expanduser()
#: Почему git зовётся с собственными помощниками, а не с теми, что в глобальном конфиге:
#: на маке первым стоит связка ключей, и когда ключ в ней не подходит, её помощник может
#: встать на запросе доступа к связке. Он грандчайлд, и `timeout` у subprocess его не
#: снимает: родитель убит, труба открыта, `run` ждёт её вечно. 02-10-2026 так повисли три
#: хука (11, 5 и 2 минуты), а хук выполняется в начале КАЖДОЙ сессии. Пустое значение
#: первым сбрасывает унаследованный список, дальше остаётся файл, который пишет `lab`.
GIT = ["git", "-c", "credential.helper=",
       "-c", f"credential.helper=store --file={CREDENTIALS_FILE}"]
#: И запрещаем спрашивать что-либо интерактивно: висеть хук не должен ни при каких ключах.
NO_PROMPT_ENV = {"GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "/usr/bin/true",
                "SSH_ASKPASS": "/usr/bin/true", "GIT_CONFIG_NOSYSTEM": "1"}

#: Помощник, который умеет клонировать тему в папку проекта и открывать pull request.
LAB_CLI = Path("~/.local/bin/lab").expanduser()


def clone_of_project(cwd: str) -> Path:
    """Куда клонируется база ДЛЯ ЭТОГО проекта: `<папка проекта>/lab-base`.

    Общая папка на все проекты кончилась ровно тем, чем и должна была: агент в
    `~/Papers/wsd-muon` базы не видел вовсе, пока ему не сказали, где она, а потом
    склонировал её из чужого локального клона — и push уходил в никуда. Клон лежит там,
    где агент работает, и других мест у него нет.
    """
    here = Path(cwd or ".").expanduser().resolve()
    for folder in (here, *here.parents):
        if (folder / ".lab-work").is_file():
            return folder / "lab-base"
        if folder == folder.parent:
            break
    return here / "lab-base"


def branch_of(root: Path) -> str:
    """На какой ветке стоит рабочее дерево клона. Пусто, если спросить не удалось."""
    if not (root / ".git").is_dir():
        return ""
    try:
        done = subprocess.run([*GIT, "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"],
                              capture_output=True, text=True, timeout=10,
                              stdin=subprocess.DEVNULL,
                              env={**os.environ, **NO_PROMPT_ENV})
    except (OSError, subprocess.SubprocessError):
        return ""
    return done.stdout.strip() if not done.returncode else ""


def pull_clone(work: str, cwd: str) -> list[str]:
    """Завести или обновить клон работы в папке проекта и сказать, что изменилось.

    Это то, с чего начинается ход: агент видит чужие слияния как обычный `git pull`, а не
    выясняет их вызовами. Нет клона — он заводится сам, спрашивать не о чем.

    Свои незакоммиченные правки не трогаем: `--ff-only` откажется, и это правильно.
    """
    root = clone_of_project(cwd)
    if not (root / ".git").is_dir():
        if not LAB_CLI.is_file():
            return [f"  клона базы нет, и помощника нет: {LAB_CLI}"]
        done = subprocess.run([str(LAB_CLI), "here", work], cwd=str(root.parent),
                              capture_output=True, text=True, timeout=120,
                              stdin=subprocess.DEVNULL,
                              env={**os.environ, **NO_PROMPT_ENV})
        lines = (done.stdout + done.stderr).strip().splitlines()
        return [f"  {text_line.strip()}" for text_line in lines[:6]] or ["  клон не вышел"]
    def git_out(*args: str) -> str:
        done = subprocess.run([*GIT, "-C", str(root), *args],
                              capture_output=True, text=True, timeout=25,
                              stdin=subprocess.DEVNULL,
                              env={**os.environ, **NO_PROMPT_ENV})
        return done.stdout.strip()
    was = git_out("rev-parse", "HEAD")
    fetched = subprocess.run([*GIT, "-C", str(root), "fetch", "-q", "origin"],
                           capture_output=True, text=True, timeout=25,
                           stdin=subprocess.DEVNULL,
                           env={**os.environ, **NO_PROMPT_ENV})
    # Молчащий отказ здесь хуже устаревшей строки: 02-10-2026 после смены ключа git
    # отвечал «Access denied», хук этого не показывал, и агент видел прошлое состояние
    # как текущее. Чинит это `lab pull` — он перезаписывает ключ помощнику.
    if fetched.returncode:
        trouble = (fetched.stderr or "").strip().splitlines()
        return ["  база не ответила, показано прошлое состояние: "
                + (trouble[-1][:120] if trouble else "git fetch не прошёл"),
                "  починить — `lab pull`"]
    subprocess.run([*GIT, "-C", str(root), "pull", "-q", "--ff-only", "origin", "main"],
                   capture_output=True, text=True, timeout=25,
                   stdin=subprocess.DEVNULL, env={**os.environ, **NO_PROMPT_ENV})
    became = git_out("rev-parse", "HEAD")
    if was == became:
        return []
    lines = git_out("--no-pager", "diff", "--stat", f"{was}..{became}").splitlines()
    return [f"  {line.strip()}" for line in lines[-12:]]


#: Логин человека, за чьей машиной идёт работа. Одна строка, кладётся руками один раз:
#: он приходит в письме бота вместе с доступом. Без него агент всё равно видит задачи с
#: ярлыками, но не видит, что назначено лично хозяину.
LOGIN_FILE = Path("~/.config/brainlab/gitlab-login").expanduser()
#: Утверждение, на которое влияет задача: строка в её теле. Так задача связана со знанием,
#: а не висит рядом с ним.
CLAIM_LINE = re.compile(r"^\s*(?:\*\*)?Утверждение:?(?:\*\*)?\s*([HDSEF]-[A-Z]{2,4}-\d+)",
                         re.M)


def my_login() -> str:
    try:
        return LOGIN_FILE.read_text(encoding="utf-8").strip().splitlines()[0].strip()
    except (OSError, IndexError):
        return ""


def tasks_of_work(work: str) -> tuple[list[str], list[str]]:
    """Что агенту делать в этой работе: поручено ему, назначено хозяину, уже делается.

    Без этого блока задача лежит на доске, а агент о ней не знает: сам он доску не
    смотрит. Берётся один запрос на работу, разбор местный — три запроса на то же самое
    были бы втрое дороже и ничего бы не добавили.

    Возвращает две пачки: что делать (поручено или назначено) и что уже в работе у других.
    """
    full_path = path_of_work(work)
    if not full_path or not TOKEN_FILE.is_file():
        return [], []
    try:
        token = TOKEN_FILE.read_text(encoding="utf-8").strip()
        request = urllib.request.Request(
            f"{BASE_URL}/api/v4/projects/{urllib.parse.quote(full_path, safe='')}"
            f"/issues?state=opened&per_page=100",
            headers={"PRIVATE-TOKEN": token})
        with urllib.request.urlopen(request, timeout=4) as answer:
            issues = json.loads(answer.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 — начало сессии не роняется из-за сети
        return [], []
    me = my_login()

    def line(issue: dict) -> str:
        labels = [me for me in (issue.get("labels") or []) if me not in ("делается", "на проверке")]
        # Своё имя и имя своего агента не печатаем: строка и так про то, что поручено
        # тебе, а место в ней дорогое — хук читается в начале каждой сессии.
        own = {me, f"{me}-agent"} if me else set()
        assignees = ", ".join(person["username"] for person in (issue.get("assignees") or [])
                        if person["username"] not in own) or "никому"
        found = CLAIM_LINE.search(issue.get("description") or "")
        due = f" до {issue['due_date']}" if issue.get("due_date") else ""
        tail = " ".join(filter(None, [
            f"[{','.join(labels)}]" if labels else "",
            f"→{found.group(1)}" if found else "",
            f"на {assignees}" if assignees != "никому" else "",
        ]))
        return f"#{issue.get('iid')}{due} {str(issue.get('title') or '')[:60]} {tail}"

    mine, in_progress = [], []
    for issue in issues:
        labels = set(issue.get("labels") or [])
        my_names = {person["username"] for person in (issue.get("assignees") or [])}
        # Задача, назначенная учётке агента (`<логин>-agent`), тоже его: с 02-10-2026 у
        # агента своя учётная запись, и «задача агенту» выражается назначением, а не
        # только ярлыком.
        if "агенту" in labels or (me and (me in my_names or f"{me}-agent" in my_names)):
            mine.append(line(issue))
        elif "делается" in labels:
            in_progress.append(line(issue))
    return mine, in_progress


PINNED = ".lab-work"


def pinned(cwd: str) -> str | None:
    """Работа, привязанная к каталогу файлом `.lab-work`, здесь или выше по дереву."""
    here = Path(cwd or ".").expanduser().resolve()
    for folder in (here, *here.parents):
        mark = folder / PINNED
        if mark.is_file():
            said = mark.read_text(encoding="utf-8").strip().splitlines()
            if said:
                return said[0].strip()
    return None


def work_of(cwd: str) -> str | None:
    """Слаг работы: сперва привязка каталога, потом карта путей."""
    if said := pinned(cwd):
        return said
    if not REGISTRY.is_file():
        return None
    try:
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except ValueError:
        return None
    here = Path(cwd or ".").expanduser().resolve()
    for root in registry.get("roots") or []:
        base = Path(root["fs"]).expanduser().resolve()
        for folder, vault in (root.get("items") or {}).items():
            if (base / folder) == here or (base / folder) in here.parents:
                return vault.rsplit("/", 1)[-1]
    return None


def claims_of(slug: str, clone: Path | None = None) -> tuple[str, list[str]]:
    """Репозиторий работы и её утверждения, прочитанные с диска.

    Сначала клон этой работы в папке проекта: после переезда на GitLab работа — отдельный
    репозиторий, и её утверждения лежат прямо в нём, а не в папке внутри темы.
    """
    places = []
    if clone is not None and (clone / "claims").is_dir():
        places.append((slug, clone))
    places += [(shelf.name, shelf / slug) for shelf in sorted(BASE.glob("*"))]
    for shelf, home in places:
        if not (home / "claims").is_dir():
            continue
        said = []
        for page in sorted((home / "claims").glob("*/README.md")):
            text = page.read_text(encoding="utf-8", errors="replace")
            head = FRONT.match(text)
            status = ""
            if head:
                for line in head.group(1).splitlines():
                    if line.startswith("status:"):
                        status = line.partition(":")[2].strip()
            # Только код и состояние. Заголовок лежит в самом файле, а в хуке он стоил
            # строки на каждое утверждение: у работы с двадцатью двумя это двадцать две
            # строки в каждой сессии. Владелец 02-10-2026: «он просто постоянно одну и ту
            # же инфу читает, это же тупизм».
            said.append(f"{page.parent.name}{(' ' + status) if status else ''}")
        return (shelf if shelf == slug else f"{shelf}/{slug}"), said
    # Запасного слепка здесь больше нет. Он лежал в `~/.local/state/brainlab/claims`,
    # обновлялся отдельным скриптом, который ни в расписании, ни в настройках не был
    # зарегистрирован, — и к 03-10-2026 показывал список утверждений восьмидневной
    # давности как текущий. Источник один: клон работы. Нет клона — хук его заводит сам.
    return "", []


def read_payload() -> dict:
    """Hook payload from stdin, without the right to hang on the read.

    Claude Code sends JSON and closes the stream, so `read()` returns at once. But if the
    stream stays open — and it does on any launch outside a session — `read()` waits for
    EOF forever, and this hook runs at the start of EVERY session. Half a second of
    waiting: arrived — read it, did not — work from the current directory.
    """
    try:
        ready = select.select([sys.stdin], [], [], 0.5)[0]
    except (OSError, ValueError):
        return {}
    if not ready:
        return {}
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except (ValueError, OSError):
        return {}


#: Места базы, которые НЕ являются научной работой. Агент, правящий правило, инструмент
#: или что-то наружу, обязан знать, что запись идёт не только в код. До 08-10-2026 он об
#: этом не знал вовсе: правила жили в README самих репозиториев, то есть читались, только
#: если репозиторий случайно склонировали. За сутки с 923 правками в базе не появилось ни
#: одной записи в журнал.
#:
#: Список НЕ зашит: он собирается из самого GitLab, по описаниям групп и проектов. Иначе он
#: протухнет ровно так же, как протухали все зашитые списки до него.
PLACES_CACHE = Path("~/.cache/brainlab/places.json").expanduser()
PLACES_TTL = 12 * 3600
#: Что писать в каждое место. Ключ — путь проекта, значение — когда туда идут.
WHEN_TO_WRITE = {
    "brainlab/journal": "менялся СПОСОБ РАБОТЫ: правило, место, инструмент, что-то выключено",
    "brainlab/handbook": "менялось УСТРОЙСТВО: чем работаем, что умеют навыки, как заведено",
    "brainlab/tools": "менялся общий код, который берут себе в репозиторий с обучением",
    "grants/grants": "менялось что-то по гранту: заявка, отчёт, обязательство",
    "ops/management": "менялось обязательство НАРУЖУ: заказчик, этап, приёмка, отчёт",
    "ops/education": "менялось про студентов и курсы",
    "ops/communications": "менялось про анонсы и публичные тексты",
}


def _ask(path: str, token: str, seconds: int = 4):
    """Один вызов к GitLab. Молчит при любой беде: хук не должен мешать работе."""
    try:
        request = urllib.request.Request(
            f"{BASE_URL}/api/v4/{path}",
            headers={"PRIVATE-TOKEN": token})
        with urllib.request.urlopen(request, timeout=seconds) as answer:
            return json.loads(answer.read().decode("utf-8"))
    except Exception:
        return None


def places() -> list[tuple[str, str]]:
    """Места базы вне научных работ: путь и когда туда писать.

    Ответ кладётся в кеш на полсуток: хук выполняется при каждом старте, и ходить за этим
    в сеть каждый раз незачем. Нет сети и нет кеша — остаётся список рядом: промолчать здесь хуже, чем
    назвать место, которого у студента может не оказаться.
    """
    try:
        if PLACES_CACHE.is_file() and time.time() - PLACES_CACHE.stat().st_mtime < PLACES_TTL:
            return [tuple(row) for row in json.loads(PLACES_CACHE.read_text(encoding="utf-8"))]
    except (OSError, ValueError):
        pass
    known = sorted(WHEN_TO_WRITE.items())
    if not TOKEN_FILE.is_file():
        return known
    try:
        token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return known
    found = []
    for project in _ask("projects?per_page=100", token) or []:
        path = project["path_with_namespace"]
        # Научная работа лежит на третьем уровне (направление/тема/работа) — её не берём,
        # как и переднюю страницу группы и литературу темы.
        if path.count("/") >= 2 or project["path"] in ("gitlab-profile", "literature"):
            continue
        when = WHEN_TO_WRITE.get(path)
        if when:
            found.append((path, when))
    if not found:
        return known
    try:
        PLACES_CACHE.parent.mkdir(parents=True, exist_ok=True)
        PLACES_CACHE.write_text(json.dumps(found, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    return found


#: Куда пишет ИМЕННО ЭТА работа, видно по клонам рядом с ней: склонировал `grants/grants` —
#: значит пишешь туда. Два клона — два адреса. Отдельного файла с решением не нужно, и
#: владелец 08-10-2026 это сказал прямо: «почему нельзя просто сделать git clone один раз,
#: и потом агент уже будет видеть: ага, есть клон, работаю там».
#:
#: Решение всё равно остаётся за владельцем: клонов нет — агент спрашивает, а не выбирает
#: сам. 07-10-2026 один агент сутки отвечал «записывать нечего», потому что его инженерная
#: работа не подходила ни под один научный адрес; угадать было бы не лучше, владелец убрал
#: бы её в `grants/grants` отдельной папкой.
BASE_HOST = BASE_URL.split("//", 1)[-1].split("/", 1)[0].split(":", 1)[0]


def clones_here(cwd: str) -> list[str]:
    """Клоны репозиториев базы рядом с работой: что склонировано, туда и пишем.

    Смотрим саму папку и один уровень внутрь: глубже лежат чужие зависимости, и принимать
    их за адрес записи незачем.
    """
    here = Path(cwd or ".").expanduser().resolve()
    found: list[str] = []
    folders = [here, *[child for child in here.iterdir() if child.is_dir()]] \
        if here.is_dir() else [here]
    for folder in folders[:60]:
        config = folder / ".git" / "config"
        try:
            if not config.is_file():
                continue
            text = config.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("url = ") and BASE_HOST in line:
                path = line.split(BASE_HOST, 1)[1].lstrip(":0123456789/")
                path = path[:-4] if path.endswith(".git") else path
                if path and path not in found:
                    found.append(path)
    return found


def tell_places(cwd: str) -> None:
    """Сказать, куда идёт запись отсюда, или что это надо спросить у владельца.

    Зовётся из КАЖДОГО пути, где научной работы базы нет. Два исхода, и только два: клоны
    базы рядом есть — печатаем их и молчим про остальное; клонов нет — печатаем список мест
    и требуем СПРОСИТЬ, а не выбрать самому.
    """
    mine = clones_here(cwd)
    if mine:
        print("\nЗапись отсюда идёт в " + ", ".join(f"`{path}`" for path in mine)
              + " — это клоны базы рядом с работой.")
        print("Предложением, сливает человек. Нужен ещё адрес — склонируй его сюда же.\n")
        return
    known = places()
    if not known:
        return
    print("\nКлонов базы рядом нет, значит адреса у записи пока нет. Выбирать его самому")
    print("нельзя: это решает владелец. Спроси его, назвав, что именно получилось. Места:")
    for path, when in known:
        print(f"  `{path}` — {when}")
    print("Его ответ — это `git clone <адрес>` сюда же: дальше клон и будет ответом, и")
    print("вопрос не повторится. Запись идёт предложением, сливает человек.\n")


def main() -> int:
    payload = read_payload()
    cwd = payload.get("cwd") or os.getcwd()
    slug = work_of(cwd)
    if slug is None:
        tell_places(cwd)
        return 0
    place = clone_of_project(cwd)
    repo, claims = claims_of(slug, place)
    if not claims:
        # Ни утверждений, ни клона — значит это и не работа базы. Каталог сопоставляется
        # работе по карте путей, а в карте лежат ВСЕ проекты, не только научные: этот
        # репозиторий, например, инфраструктурный, и работы в базе у него нет. Прежде
        # здесь печаталась строка «утверждений пока нет», и 07-10-2026 выяснилось, чем
        # это плохо: работа `lab-knowledge-pipeline` была удалена, а хук продолжал звать
        # её каждую сессию и печатать ошибку клонирования. Строка, которая не меняется от
        # сессии к сессии, — это ровно то, против чего хук и написан.
        if not (place / "claims").is_dir():
            tell_places(cwd)
            return 0
        print(f"\nЛаборатория: {slug}, утверждений пока нет. Клон: {place}")
        print("Как писать — `~/.claude/rules/lab.md`; главное: не мусорить.\n")
        return 0
    print(f"\nЛаборатория: {slug}, утверждений {len(claims)} — {', '.join(claims)}")
    print(f"Клон: {place}")
    # Утверждения прочитаны из рабочего дерева, а обновляется `origin main`. Если дерево
    # стоит на ветке предложения, хук покажет её состояние, назвав его состоянием базы.
    # Проверено 07-10-2026 на `wsd-muon`: клон остался на `claim/H-WSD-017-audit`, ветку
    # при слиянии удалили, и хук печатал `H-WSD-020 confirmed` — состояние, которого в
    # закрытом наборе свода уже нет, и которого в `main` нет полгода.
    if (branch := branch_of(place)) and branch != "main":
        print(f"Дерево стоит на ветке `{branch}`, и состояния выше — её, не из main.")
    if changed := pull_clone(slug, cwd):
        print("В main: " + "; ".join(text_line.strip() for text_line in changed[:4]))
    if waiting := open_proposals(slug):
        print("Открыто (дописывай, не заводи второе): "
              + "; ".join(text_line.strip() for text_line in waiting))
    assigned_to_me, in_progress = tasks_of_work(slug)
    if assigned_to_me:
        print("Поручено тебе: " + "; ".join(text_line.strip() for text_line in assigned_to_me))
    if in_progress:
        print("У кого-то в работе: " + "; ".join(text_line.strip() for text_line in in_progress))
    print("Как писать — `~/.claude/rules/lab.md`; главное: не мусорить.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
