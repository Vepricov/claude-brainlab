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
БАЗА = os.getenv("BRAINLAB_GIT_URL", "https://68-183-24-188.sslip.io:9445")
ТОКЕН = Path("~/.config/brainlab/git-token").expanduser()


def путь_работы(слаг: str) -> str:
    """Полный путь работы в дереве групп. Запоминается: он не меняется.

    Единица базы — работа, и у неё свой проект внутри группы темы. Слаг человек помнит, а
    полный путь нет, поэтому он ищется один раз и кладётся рядом со слепком утверждений.
    """
    помню = CACHE / f"{слаг}.path"
    if помню.is_file():
        если = помню.read_text(encoding="utf-8").strip()
        if если:
            return если
    if not ТОКЕН.is_file():
        return ""
    try:
        запрос = urllib.request.Request(
            f"{БАЗА}/api/v4/groups/brainlab/projects"
            f"?include_subgroups=true&simple=true&search={слаг}&per_page=100",
            headers={"PRIVATE-TOKEN": ТОКЕН.read_text(encoding="utf-8").strip()})
        with urllib.request.urlopen(запрос, timeout=4) as ответ:
            найдено = json.loads(ответ.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 — начало сессии не роняется из-за сети
        return ""
    точные = [п for п in найдено if п.get("path") == слаг]
    if not точные:
        return ""
    путь = str(точные[0]["path_with_namespace"])
    try:
        CACHE.mkdir(parents=True, exist_ok=True)
        помню.write_text(путь + "\n", encoding="utf-8")
    except OSError:
        pass
    return путь


def открытые_предложения(работа: str) -> list[str]:
    """Открытые предложения этой работы: номер, утверждение, заголовок.

    Это самое скоропортящееся, что агенту нужно знать перед записью, и самое дорогое,
    когда он этого не знает: 30-09-2026 агент доложил про pull request №2, давно
    закрытый, потому что взял номер из своей прошлой памяти. Карточка работы весит под
    двести килобайт, и блок про предложения в её конце до него не дошёл.

    Стоит это ноль токенов модели и один запрос к Gitea. Не ответила — молчим: сказать
    «я в работе такой-то» полезно и без этого.
    """
    полный = путь_работы(работа)
    if not полный or not ТОКЕН.is_file():
        return []
    try:
        токен = ТОКЕН.read_text(encoding="utf-8").strip()
        запрос = urllib.request.Request(
            f"{БАЗА}/api/v4/projects/{urllib.parse.quote(полный, safe='')}"
            f"/merge_requests?state=opened&per_page=20",
            headers={"PRIVATE-TOKEN": токен})
        # Сертификат выписан на sslip.io и настоящий, но хук не имеет права падать из-за
        # чужой связи, поэтому проверка мягкая и таймаут короткий.
        with urllib.request.urlopen(запрос, timeout=3) as ответ:
            открытые = json.loads(ответ.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 — начало сессии не роняется из-за сети
        return []
    строки = []
    for мр in открытые:
        ветка = str(мр.get("source_branch") or "")
        метка = ветка.removeprefix("claim/") if ветка.startswith("claim/") else ветка
        строки.append(f"!{мр.get('iid')} {метка[:14]} {str(мр.get('title') or '')[:48]}")
    return строки


#: Хранилище ключа, которое пишет сам `lab`. Хуку важно ходить ТОЛЬКО через него.
ХРАНИЛИЩЕ = Path("~/.config/brainlab/git-credentials").expanduser()
#: Почему git зовётся с собственными помощниками, а не с теми, что в глобальном конфиге:
#: на маке первым стоит связка ключей, и когда ключ в ней не подходит, её помощник может
#: встать на запросе доступа к связке. Он грандчайлд, и `timeout` у subprocess его не
#: снимает: родитель убит, труба открыта, `run` ждёт её вечно. 02-10-2026 так повисли три
#: хука (11, 5 и 2 минуты), а хук выполняется в начале КАЖДОЙ сессии. Пустое значение
#: первым сбрасывает унаследованный список, дальше остаётся файл, который пишет `lab`.
ГИТ = ["git", "-c", "credential.helper=",
       "-c", f"credential.helper=store --file={ХРАНИЛИЩЕ}"]
#: И запрещаем спрашивать что-либо интерактивно: висеть хук не должен ни при каких ключах.
БЕЗ_ВОПРОСОВ = {"GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "/usr/bin/true",
                "SSH_ASKPASS": "/usr/bin/true", "GIT_CONFIG_NOSYSTEM": "1"}

#: Помощник, который умеет клонировать тему в папку проекта и открывать pull request.
ПОМОЩНИК = Path("~/.local/bin/lab").expanduser()


def клон_проекта(cwd: str) -> Path:
    """Куда клонируется база ДЛЯ ЭТОГО проекта: `<папка проекта>/lab-base`.

    Общая папка на все проекты кончилась ровно тем, чем и должна была: агент в
    `~/Papers/wsd-muon` базы не видел вовсе, пока ему не сказали, где она, а потом
    склонировал её из чужого локального клона — и push уходил в никуда. Клон лежит там,
    где агент работает, и других мест у него нет.
    """
    здесь = Path(cwd or ".").expanduser().resolve()
    for папка in (здесь, *здесь.parents):
        if (папка / ".lab-work").is_file():
            return папка / "lab-base"
        if папка == папка.parent:
            break
    return здесь / "lab-base"


def подтянуть(работа: str, cwd: str) -> list[str]:
    """Завести или обновить клон работы в папке проекта и сказать, что изменилось.

    Это то, с чего начинается ход: агент видит чужие слияния как обычный `git pull`, а не
    выясняет их вызовами. Нет клона — он заводится сам, спрашивать не о чем.

    Свои незакоммиченные правки не трогаем: `--ff-only` откажется, и это правильно.
    """
    корень = клон_проекта(cwd)
    if not (корень / ".git").is_dir():
        if not ПОМОЩНИК.is_file():
            return [f"  клона базы нет, и помощника нет: {ПОМОЩНИК}"]
        итог = subprocess.run([str(ПОМОЩНИК), "here", работа], cwd=str(корень.parent),
                              capture_output=True, text=True, timeout=120,
                              stdin=subprocess.DEVNULL,
                              env={**os.environ, **БЕЗ_ВОПРОСОВ})
        строки = (итог.stdout + итог.stderr).strip().splitlines()
        return [f"  {с.strip()}" for с in строки[:6]] or ["  клон не вышел"]
    def гит(*что: str) -> str:
        итог = subprocess.run([*ГИТ, "-C", str(корень), *что],
                              capture_output=True, text=True, timeout=25,
                              stdin=subprocess.DEVNULL,
                              env={**os.environ, **БЕЗ_ВОПРОСОВ})
        return итог.stdout.strip()
    было = гит("rev-parse", "HEAD")
    взято = subprocess.run([*ГИТ, "-C", str(корень), "fetch", "-q", "origin"],
                           capture_output=True, text=True, timeout=25,
                           stdin=subprocess.DEVNULL,
                           env={**os.environ, **БЕЗ_ВОПРОСОВ})
    # Молчащий отказ здесь хуже устаревшей строки: 02-10-2026 после смены ключа git
    # отвечал «Access denied», хук этого не показывал, и агент видел прошлое состояние
    # как текущее. Чинит это `lab pull` — он перезаписывает ключ помощнику.
    if взято.returncode:
        беда = (взято.stderr or "").strip().splitlines()
        return ["  база не ответила, показано прошлое состояние: "
                + (беда[-1][:120] if беда else "git fetch не прошёл"),
                "  починить — `lab pull`"]
    subprocess.run([*ГИТ, "-C", str(корень), "pull", "-q", "--ff-only", "origin", "main"],
                   capture_output=True, text=True, timeout=25,
                   stdin=subprocess.DEVNULL, env={**os.environ, **БЕЗ_ВОПРОСОВ})
    стало = гит("rev-parse", "HEAD")
    if было == стало:
        return []
    строки = гит("--no-pager", "diff", "--stat", f"{было}..{стало}").splitlines()
    return [f"  {строка.strip()}" for строка in строки[-12:]]


#: Логин человека, за чьей машиной идёт работа. Одна строка, кладётся руками один раз:
#: он приходит в письме бота вместе с доступом. Без него агент всё равно видит задачи с
#: ярлыками, но не видит, что назначено лично хозяину.
ЛОГИН = Path("~/.config/brainlab/gitlab-login").expanduser()
#: Утверждение, на которое влияет задача: строка в её теле. Так задача связана со знанием,
#: а не висит рядом с ним.
УТВЕРЖДЕНИЕ = re.compile(r"^\s*(?:\*\*)?Утверждение:?(?:\*\*)?\s*([HDSEF]-[A-Z]{2,4}-\d+)",
                         re.M)


def мой_логин() -> str:
    try:
        return ЛОГИН.read_text(encoding="utf-8").strip().splitlines()[0].strip()
    except (OSError, IndexError):
        return ""


def задачи_работы(работа: str) -> tuple[list[str], list[str]]:
    """Что агенту делать в этой работе: поручено ему, назначено хозяину, уже делается.

    Без этого блока задача лежит на доске, а агент о ней не знает: сам он доску не
    смотрит. Берётся один запрос на работу, разбор местный — три запроса на то же самое
    были бы втрое дороже и ничего бы не добавили.

    Возвращает две пачки: что делать (поручено или назначено) и что уже в работе у других.
    """
    полный = путь_работы(работа)
    if not полный or not ТОКЕН.is_file():
        return [], []
    try:
        токен = ТОКЕН.read_text(encoding="utf-8").strip()
        запрос = urllib.request.Request(
            f"{БАЗА}/api/v4/projects/{urllib.parse.quote(полный, safe='')}"
            f"/issues?state=opened&per_page=100",
            headers={"PRIVATE-TOKEN": токен})
        with urllib.request.urlopen(запрос, timeout=4) as ответ:
            задачи = json.loads(ответ.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 — начало сессии не роняется из-за сети
        return [], []
    я = мой_логин()

    def строка(з: dict) -> str:
        ярлыки = [я for я in (з.get("labels") or []) if я not in ("делается", "на проверке")]
        # Своё имя и имя своего агента не печатаем: строка и так про то, что поручено
        # тебе, а место в ней дорогое — хук читается в начале каждой сессии.
        свои = {я, f"{я}-agent"} if я else set()
        кто = ", ".join(и["username"] for и in (з.get("assignees") or [])
                        if и["username"] not in свои) or "никому"
        если = УТВЕРЖДЕНИЕ.search(з.get("description") or "")
        срок = f" до {з['due_date']}" if з.get("due_date") else ""
        хвост = " ".join(filter(None, [
            f"[{','.join(ярлыки)}]" if ярлыки else "",
            f"→{если.group(1)}" if если else "",
            f"на {кто}" if кто != "никому" else "",
        ]))
        return f"#{з.get('iid')}{срок} {str(з.get('title') or '')[:60]} {хвост}"

    мне, идёт = [], []
    for з in задачи:
        ярлыки = set(з.get("labels") or [])
        мои = {и["username"] for и in (з.get("assignees") or [])}
        # Задача, назначенная учётке агента (`<логин>-agent`), тоже его: с 02-10-2026 у
        # агента своя учётная запись, и «задача агенту» выражается назначением, а не
        # только ярлыком.
        if "агенту" in ярлыки or (я and (я in мои or f"{я}-agent" in мои)):
            мне.append(строка(з))
        elif "делается" in ярлыки:
            идёт.append(строка(з))
    return мне, идёт


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


def claims_of(slug: str, клон: Path | None = None) -> tuple[str, list[str]]:
    """Репозиторий работы и её утверждения, прочитанные с диска.

    Сначала клон этой работы в папке проекта: после переезда на GitLab работа — отдельный
    репозиторий, и её утверждения лежат прямо в нём, а не в папке внутри темы.
    """
    места = []
    if клон is not None and (клон / "claims").is_dir():
        места.append((slug, клон))
    места += [(shelf.name, shelf / slug) for shelf in sorted(BASE.glob("*"))]
    for полка, home in места:
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
        return (полка if полка == slug else f"{полка}/{slug}"), said
    # Слепок: `<работа>.txt`, по строке на утверждение, как их напечатал бы каталог.
    snapshot = CACHE / f"{slug}.txt"
    if snapshot.is_file():
        lines = [line for line in snapshot.read_text(encoding="utf-8").splitlines() if line]
        return (lines[0] if lines else ""), lines[1:]
    return "", []


def прочитать_вход() -> dict:
    """Полезная нагрузка хука со stdin, но без права повиснуть на чтении.

    Claude Code передаёт JSON и закрывает поток, и тогда `read()` возвращается сразу. Но
    если поток остался открытым (а это бывает при любом запуске не из сессии), `read()`
    ждёт конца файла вечно — а хук выполняется в начале КАЖДОЙ сессии. Полсекунды на
    ожидание: пришло — читаем, не пришло — работаем по текущему каталогу.
    """
    try:
        готов = select.select([sys.stdin], [], [], 0.5)[0]
    except (OSError, ValueError):
        return {}
    if not готов:
        return {}
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except (ValueError, OSError):
        return {}


def main() -> int:
    payload = прочитать_вход()
    cwd = payload.get("cwd") or os.getcwd()
    slug = work_of(cwd)
    if slug is None:
        return 0
    место = клон_проекта(cwd)
    repo, claims = claims_of(slug, место)
    if not claims:
        print(f"\nЛаборатория: {slug}, утверждений пока нет. Клон: {место}")
        print("Как писать — `~/.claude/rules/lab.md`; главное: не мусорить.\n")
        return 0
    print(f"\nЛаборатория: {slug}, утверждений {len(claims)} — {', '.join(claims)}")
    print(f"Клон: {место}")
    if изменилось := подтянуть(slug, cwd):
        print("В main: " + "; ".join(с.strip() for с in изменилось[:4]))
    if ждут := открытые_предложения(slug):
        print("Открыто (дописывай, не заводи второе): "
              + "; ".join(с.strip() for с in ждут))
    поручено, идёт = задачи_работы(slug)
    if поручено:
        print("Поручено тебе: " + "; ".join(с.strip() for с in поручено))
    if идёт:
        print("У кого-то в работе: " + "; ".join(с.strip() for с in идёт))
    print("Как писать — `~/.claude/rules/lab.md`; главное: не мусорить.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
