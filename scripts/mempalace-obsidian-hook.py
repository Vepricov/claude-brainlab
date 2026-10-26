#!/usr/bin/env python3
"""Stop hook: one interruption, three places the session gets written down.

Replaces `python3 -m mempalace hook run --hook stop --harness claude-code`.

MemPalace blocks the end of a turn every few exchanges and asks the agent to save what
happened. That design is the reason it works: the hook does not try to understand the
session, it interrupts and demands, and the agent — which has the whole context — decides
what is worth keeping and says so out loud.

Obsidian and the lab knowledge base ride the same interruption instead of adding their
own. Two hooks blocking on two cadences would double the noise, and a second mechanism
that writes on its own turned out not to work at all: the previous lab hook parsed the
session for markup nobody was documented to write, so in real use it never fired.

WHY THIS COUNTS ITS OWN EXCHANGES

The interval is meant to be "every N messages from the human". The upstream counter takes
every entry with role=user, and in an agentic session almost all of those are tool
results: in one long session here, 5283 such entries were 4722 tool results, 177 hook
replies and only 384 real messages. At an interval of ten that fired 552 times instead of
38, and each extra turn re-reads the whole context — 8.6% of the session's output tokens
and 8.0% of its cache reads went to saving. So the counting happens here, over genuine
turns only, and the interval means what it says.

Saving before compaction is the other obvious idea and it does not work: a blocking
PreCompact hook cancels the compaction instead of deferring it. The cadence stays on Stop.

The lab section is always printed: the base is a set of git clones, not a service, and the
section itself says what to do when no clone sits next to the work. Until 08-10-2026 it was
gated on a lab-knowledge MCP server being configured, and that server was deleted with its
database, so the rules reached nobody whose install had no lab MCP entry.
Checkpoint markers track requests only; the agent must read back writes.
"""

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import mempalace.hooks_cli as hooks_cli


#: Настоящих сообщений человека между сохранениями.
SAVE_INTERVAL = 10

#: Хук печатает ТОЛЬКО то, что меняется от хода к ходу: что записать и куда. Всё
#: постоянное — порядок вызовов MemPalace, правила Obsidian, правила базы — лежит в
#: `~/.claude/rules/checkpoint.md` и читается один раз за сессию.
#:
#: Владелец говорил это трижды. 02-10-2026: «этот хук какой-то огромный, никазистый… он
#: просто постоянно одну и ту же инфу читает, это же тупизм». 08-10-2026: «почему хук такой
#: огромный, мы же делали маленький». И в тот же день: «вообще же можно ничего не писать, то
#: есть это всё в правиле где-то записать, чтобы агент постоянно это не видел перед глазами.
#: Давай максимально маленький хук сделаем, потому что агенту одна и та же инфа поступает
#: постоянно». Замеры по пути: 3798 знаков ответа → 1794 → столько, сколько занимает сама
#: подсказка классификатора.
RULE = "~/.claude/rules/checkpoint.md"


def _text_of(content: object) -> str:
    """Plain text of a message, whatever shape the harness wrote it in."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") != "tool_result"
        )
    return ""


#: Метки записей, которые носят роль человека, но человеком не являются. Проверяются
#: вхождением, а не началом строки: часть из них приходит вместе с настоящим текстом.
NOT_A_PERSON = (
    "[Request interrupted by user]",
    "[Request interrupted by user for tool use]",
    "SYSTEM NOTIFICATION - NOT USER INPUT",
    "<task-notification>",
    "<system-reminder>",
    "<local-command-caveat>",
    "This session is being continued from a previous conversation",
    "Страховочный тик разбора работ",
)


def human_turns(transcript_path: str) -> int:
    """How many times the person actually said something.

    Tool results and the hook's own reminders wear role=user too, and counting them is what
    turned an interval of ten into a save every other tool call.
    """
    path = Path(transcript_path).expanduser()
    if not path.is_file():
        return 0
    count = 0
    seen: set = set()
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(entry, dict):
                continue
            # Подпись к картинке и прочие служебные вставки клиента носят роль человека.
            if entry.get("isMeta"):
                continue
            message = entry.get("message")
            if entry.get("type") == "response_item":
                message = entry.get("payload")
            if not isinstance(message, dict) or message.get("role") != "user":
                continue
            content = message.get("content")
            if isinstance(content, list) and any(
                isinstance(block, dict) and block.get("type") == "tool_result"
                for block in content
            ):
                continue
            text = _text_of(content)
            if text.lstrip().startswith(("<environment_context>", "<turn_aborted>",
                                         "# AGENTS.md instructions", "<permissions instructions>")):
                continue
            if "<command-message>" in text:
                continue
            if "AUTO-SAVE checkpoint" in text or "Stop hook feedback" in text:
                continue
            # Не человек, хотя роль у записи его: уведомление о фоновой задаче, напоминание
            # системы, вывод локальной команды, прерывание, сводка после сжатия контекста и
            # страховочный тик наблюдателя. 03-10-2026 они давали 213 лишних «ходов» из 2080
            # в стенограмме проекта, и страховка срабатывала чаще самого классификатора.
            if any(mark in text for mark in NOT_A_PERSON) or text.strip() == "Tool loaded.":
                continue
            # Продолжение сессии после сжатия заново дописывает в стенограмму сообщения, которые
            # оставлены дословно: с тем же временем, но новым uuid. 24-10-2026 из-за этого 8
            # настоящих сообщений сосчитались как 48, и страховка «48 ходов без записи» сработала
            # на сессии, где запись шла каждые несколько ходов. Одно сообщение — один ход.
            key = entry.get("promptId") or (entry.get("timestamp"), text[:300])
            if key in seen:
                continue
            seen.add(key)
            count += 1
    return count


#: ── Два сторожа, которые НЕ ходят к модели ────────────────────────────────────
#: Владелец 08-10-2026: «по 2 по идее просто детерминированный код может ходить по всем PR,
#: которые есть у этого агента в этой сессии, и присылать ему правки… тут вообще можно без
#: траты токенов». То же верно и про прогон: запуск виден в самой стенограмме, и спрашивать
#: про него модель незачем.

#: Чем запускают обучение. Одного этого мало: `python` зовут и для двух строк разбора,
#: поэтому рядом обязателен признак обучения из `TRAINING`.
LAUNCHERS = ("torchrun", "accelerate launch", "deepspeed", "sbatch", "srun",
             "python train", "python -m torch.distributed", "nohup python", "python main.py")
TRAINING = ("--lr", "--learning-rate", "--epochs", "--batch", "--steps", "wandb",
            "train.py", "pretrain", "finetune", "--config")
#: Признак записи: W&B или рекордер зовут из обучающего кода, а не из командной строки,
#: поэтому ищутся они В ФАЙЛЕ точки входа, а не в команде. С 26-10-2026 основной путь —
#: обычный `wandb`, а в базу прогон переносит `lab wandb <ссылка>`.
WRAPPED = ("wandb.init", "import wandb", "LabRun", "lab_run")


def _golova(command: str) -> str:
    """Сама команда, без тела heredoc и без строки, переданной через `-c`.

    Признаки запуска ищутся только в ней. 14-10-2026 сторож трижды прервал ход на правке
    файлов: в теле heredoc стояли слова `sbatch`, `wandb`, `train.py` и имя правимого
    `.py`-файла — то есть и признак запуска, и признак обучения, и «файл точки входа»,
    все три из перечней самого сторожа. Тело heredoc это данные, а не команда.
    """
    golova = re.split(r"<<-?\s*['\"]?\w+", command, maxsplit=1)[0]
    return re.split(r"\s-c\s", golova, maxsplit=1)[0]


def _entrypoints(command: str) -> list[str]:
    return [piece.strip("\"'") for piece in command.split()
            if piece.strip("\"'").endswith(".py")]


def unwrapped_runs(transcript: str, cwd: str) -> list[str]:
    """Запуски обучения этой сессии, которые не обёрнуты рекордером.

    Проверяется файл точки входа, а не команда: рекордер подключают импортом, и в командной
    строке его не видно. Нет файла рядом — ответ «не обёрнут», потому что доказать обратное
    нечем, а цена ошибки несимметрична: необёрнутый прогон приходится переносить руками, что
    запрещено и красится воротами.
    """
    found: list[str] = []
    seen: set[str] = set()
    try:
        with Path(transcript).expanduser().open(encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                # Строка стенограммы бывает не объектом: `null`, `[]`, `42`. Это поймал
                # тест `test_non_object_json_lines_are_ignored`, и поймал сразу.
                if not isinstance(entry, dict):
                    continue
                content = (entry.get("message") or {}).get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict) or block.get("type") != "tool_use":
                        continue
                    command = str((block.get("input") or {}).get("command") or "")
                    if not command or command in seen:
                        continue
                    seen.add(command)
                    # Признаки ищутся в самой команде, а не в теле heredoc: иначе сторож
                    # ловит слова из текста, который команда всего лишь пишет в файл.
                    # Скрипт, переданный на stdin, обучения не запускает — у него нет
                    # файла точки входа, и тогда проверять нечего.
                    golova = _golova(command)
                    low = golova.lower()
                    if not any(one in low for one in LAUNCHERS):
                        continue
                    if not any(one in low for one in TRAINING):
                        continue
                    if any(one in golova for one in WRAPPED):
                        continue
                    if not _entrypoints(golova):
                        continue
                    wrapped = False
                    for name in _entrypoints(golova):
                        place = (Path(cwd or ".") / name).expanduser()
                        try:
                            if place.is_file() and any(
                                    one in place.read_text(encoding="utf-8", errors="ignore")
                                    for one in WRAPPED):
                                wrapped = True
                        except OSError:
                            pass
                    if not wrapped:
                        found.append(" ".join(command.split())[:160])
    except OSError:
        return []
    return found


def red_proposals(cwd: str) -> list[str]:
    """Открытые предложения с красными воротами. Один запрос на клон, без модели."""
    try:
        place = Path.home() / ".claude" / "hooks" / "lab-where-am-i.py"
        if not place.is_file():
            return []
        spec = importlib.util.spec_from_file_location("lab_where_am_i_mr", place)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        repos = module.clones_here(cwd or str(Path.cwd()))
        if not repos or not module.TOKEN_FILE.is_file():
            return []
        token = module.TOKEN_FILE.read_text(encoding="utf-8").strip()
        bad = []
        for repo in repos[:6]:
            for row in module._open_with_verdict(repo, token):  # noqa: SLF001
                if "ЕСТЬ ЗАМЕЧАНИЯ" in row:
                    bad.append(row.strip())
        return bad
    except Exception:          # noqa: BLE001 — сторож не вправе ронять ход
        return []


def _lab_hook():
    """Хук начала сессии как библиотека: он уже умеет находить клоны, и дублировать нечего."""
    place = Path.home() / ".claude" / "hooks" / "lab-where-am-i.py"
    if not place.is_file():
        return None
    spec = importlib.util.spec_from_file_location("lab_where_am_i_git", place)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(folder: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(folder), *args], capture_output=True,
                          text=True, timeout=15)
    return done.stdout.strip() if not done.returncode else ""


def _mestnye_klony(cwd: str, module) -> list[Path]:
    """Папки клонов базы на машине. `clones_here` отдаёт адреса НА СЕРВЕРЕ
    (`brainlab/handbook`), и принять их за пути — значит смотреть в несуществующие папки.

    Смотрим то же, что и остальные: саму папку, её родителей до дерева и один уровень
    внутрь, а признак тот же — `origin` указывает на базу.
    """
    here = Path(cwd or ".").expanduser().resolve()
    kandidaty: list[Path] = []
    for folder in (here, *here.parents):
        kandidaty.append(folder)
        if folder == Path.home() or folder == folder.parent:
            break
    if here.is_dir():
        try:
            kandidaty += [c for c in here.iterdir() if c.is_dir()]
            box = here / "lab-base"
            if box.is_dir():
                kandidaty += [c for c in box.iterdir() if c.is_dir()]
        except OSError:
            pass
    nashlos: list[Path] = []
    for folder in kandidaty[:60]:
        config = folder / ".git" / "config"
        try:
            if config.is_file() and module.BASE_HOST in config.read_text(
                    encoding="utf-8", errors="replace"):
                if folder not in nashlos:
                    nashlos.append(folder)
        except OSError:
            continue
    return nashlos


def tronutoe(transcript: str) -> str:
    """Всё, что агент этой сессии передавал инструментам: пути файлов и тексты команд."""
    parts: list[str] = []
    try:
        with Path(transcript).open(encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                if '"tool_use"' not in line:
                    continue
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                content = ((entry.get("message") or {}).get("content") if isinstance(entry, dict) else None)
                for block in content if isinstance(content, list) else []:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        args = block.get("input") or {}
                        parts.append(str(args.get("file_path") or ""))
                        parts.append(str(args.get("command") or ""))
    except OSError:
        pass
    return "\n".join(parts)


def nesohranennoe(cwd: str, transcript: str = "") -> list[str]:
    """Правка лежит в клоне, но в базу не ушла. Факт, а не суждение: спрашивается git.

    Владелец 17-10-2026: «он щас должен делать так: локально менять что-то у меня и потом в
    хуке пушить то, что у меня локально поменяно… или пусть сразу пишет туда, где гитигнор».
    Второе работает само (`notes/`, `daily/`, `runs/` закрыты от git и в статусе не видны),
    а первое до сих пор держалось на памяти агента: правка оставалась в рабочем дереве, ход
    кончался, и назавтра её никто не находил.

    Считаются обе беды: не закоммиченное (`git status`, игнорируемое туда не попадает) и
    закоммиченное, но не отправленное (`origin/main..HEAD`). Говорится один раз на клон.
    """
    module = _lab_hook()
    if module is None:
        return []
    try:
        papki = _mestnye_klony(cwd or str(Path.cwd()), module)
    except Exception:          # noqa: BLE001 — сторож не вправе ронять ход
        return []
    out: list[str] = []
    for folder in papki[:8]:
        gryaz = [s for s in _git(folder, "status", "--porcelain").splitlines() if s.strip()]
        if transcript:
            # Только то, чего сессия касалась: чужая рукопись или файл соседней сессии в том же
            # клоне не её правка, и отправлять их она не вправе. 10-2026 такие жалобы были
            # большей частью остановок по фактам, и агент каждый раз отвечал «это не моё».
            seen = tronutoe(transcript)
            gryaz = [s for s in gryaz if s[2:].strip().strip('"').split(" -> ")[-1] in seen
                     or Path(s[2:].strip().strip('"')).name in seen]
        vetka = _git(folder, "rev-parse", "--abbrev-ref", "HEAD")
        # Ветка, отправленная в свою ветку в GitLab, отправлена: сравнивать её с `main` значит
        # жаловаться на каждое открытое предложение.
        verh = _git(folder, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
        if not verh and _git(folder, "rev-parse", "--verify", "-q", f"origin/{vetka}"):
            verh = f"origin/{vetka}"
        vperedi = _git(folder, "rev-list", "--count", f"{verh or 'origin/main'}..HEAD")
        rabota = (folder / "claims").is_dir()
        # Имя берётся отрезанием ровно двух знаков состояния и пробелов: срез по трём
        # знакам съедал первую букву у `M  CHANGELOG.md` (состояние в первой колонке).
        imena = ", ".join(s[2:].strip()[:48] for s in gryaz[:3])
        if gryaz:
            kak = ("ветка, `git commit -F -`, `git push` — предложение откроется само"
                   if rabota else "`git pull --rebase` и `git push` прямо в `main`")
            out.append(f"{folder.name}: не отправлено {len(gryaz)} файлов ({imena}) — {kak}")
        elif vperedi.isdigit() and int(vperedi) > 0 and vetka != "main":
            out.append(f"{folder.name}: коммитов на ветке `{vetka}` без отправки "
                       f"{vperedi} — `git push`")
    return out


ROUTER = Path.home() / ".claude" / "scripts" / "jev_route.py"


def last_turn_text(transcript: str) -> str:
    """Текст ассистента после последнего настоящего сообщения человека."""
    chunk: list[str] = []
    try:
        with Path(transcript).open(encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                content = (entry.get("message") or {}).get("content")
                if entry.get("type") == "user":
                    human = isinstance(content, str) or (
                        isinstance(content, list)
                        and not any(b.get("type") == "tool_result" for b in content))
                    if human:
                        chunk = []
                elif entry.get("type") == "assistant" and isinstance(content, list):
                    chunk += [b["text"] for b in content
                              if b.get("type") == "text" and b.get("text")]
    except OSError:
        return ""
    return "\n".join(chunk)


#: Вызовы, которые и есть запись: память, связи, отправка в git. Ход, где такой вызов уже
#: был, не прерывается: классификатор видит только текст ответа, а не вызовы, и на замере
#: 21-10-2026 95 остановок из 490 пришлись на ход, где запись уже сделана. Владелец: «он
#: слишком часто останавливает модельку, чтобы она что-то записала, а она уже на самом деле
#: эту информацию записывала».
ZAPIS_VYZOV = re.compile(r"mempalace_(add_drawer|diary_write|kg_add|update_drawer)")
ZAPIS_GIT = re.compile(r"\bgit\b[^\n|;&]*\bpush\b")


def turn_wrote(transcript: str) -> bool:
    """Был ли в ходе после последнего сообщения человека вызов, который записывает."""
    wrote = False
    try:
        with Path(transcript).open(encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(entry, dict):
                    continue
                content = (entry.get("message") or {}).get("content")
                if entry.get("type") == "user":
                    human = isinstance(content, str) or (
                        isinstance(content, list)
                        and not any(b.get("type") == "tool_result" for b in content))
                    if human:
                        wrote = False
                elif entry.get("type") == "assistant" and isinstance(content, list):
                    for block in content:
                        if block.get("type") != "tool_use":
                            continue
                        name = str(block.get("name") or "")
                        command = str((block.get("input") or {}).get("command") or "")
                        if ZAPIS_VYZOV.search(name) or (name == "Bash"
                                                         and ZAPIS_GIT.search(command)):
                            wrote = True
    except OSError:
        return False
    return wrote


#: Кто решает, когда прерывать. True — классификатор, False — счётчик, как было до
#: 03-10-2026. Одна строка на откат.
JEV_DECIDES = True

#: Сколько ждать ответа. Решение нужно здесь и сейчас, поэтому вызов синхронный: на замере
#: он занимает 1-3 с. Не ответил за это время — падаем на счётчик, а не на тишину.
JEV_TIMEOUT = 14


def recorded_subjects(session: str) -> tuple[Path, list[str]]:
    """О чём в этой сессии уже прерывались. По этому списку Jev ловит повтор."""
    path = hooks_cli.STATE_DIR / f"{session}_jev_recorded.json"
    try:
        return path, json.loads(path.read_text(encoding="utf-8"))[-12:]
    except (OSError, ValueError):
        return path, []


def held_places(session: str) -> tuple[Path, list[str]]:
    """Места, выбранные на прошлом прерывании этой сессии.

    Нужны, чтобы решение не висело на сотых: место, однажды выбранное, не снимается, пока
    его оценка держится в полосе. Без этого на одном и том же предмете база то выбиралась,
    то нет — замерено 18 таких переворотов на 149 парах подряд идущих ходов.
    """
    path = hooks_cli.STATE_DIR / f"{session}_jev_places.json"
    try:
        kept = json.loads(path.read_text(encoding="utf-8"))
        return path, [str(one) for one in kept][:12]
    except (OSError, ValueError):
        return path, []


def ask_router(session: str, transcript: str, turns: int, last: int,
               fired: bool, cwd: str = "") -> dict:
    """Спросить классификатор, прерывать ли этот ход и куда это ложится.

    Любая беда возвращает пустой ответ, и тогда решает счётчик: наблюдение не вправе
    отменить сохранение.
    """
    if not ROUTER.is_file():
        return {}
    try:
        text = last_turn_text(transcript)
        if not text.strip():
            return {}
        _, already = recorded_subjects(session)
        _, kept = held_places(session)
        handle, path = tempfile.mkstemp(suffix=".json", prefix="jev-route-")
        with open(handle, "w", encoding="utf-8") as payload:
            json.dump({"сессия": session, "ходов": turns, "прошлое": last,
                       "счётчик_сработал": fired, "текст": text,
                       "каталог": cwd, "записанное": already,
                       "удержанное": kept},
                      payload, ensure_ascii=False)
        done = subprocess.run([sys.executable, str(ROUTER), path],
                              capture_output=True, text=True, timeout=JEV_TIMEOUT)
        return json.loads(done.stdout.strip() or "{}")
    except Exception:          # noqa: BLE001 — сеть, таймаут, разбор: решит счётчик
        return {}


def remember_subject(session: str, transcript: str) -> None:
    """Запомнить, о чём прервались, чтобы второй раз об этом не прерываться."""
    try:
        path, already = recorded_subjects(session)
        head = " ".join(last_turn_text(transcript).split())[:200]
        if head:
            path.write_text(json.dumps((already + [head])[-12:], ensure_ascii=False),
                            encoding="utf-8")
    except OSError:
        pass


def remember_written(session: str, transcript: str) -> None:
    """Что именно записано в этом ходе: начало записи в память и сообщение коммита при push."""
    heads: list[str] = []
    try:
        with Path(transcript).open(encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(entry, dict):
                    continue
                content = (entry.get("message") or {}).get("content")
                if entry.get("type") == "user":
                    if isinstance(content, str) or (isinstance(content, list) and not any(
                            b.get("type") == "tool_result" for b in content)):
                        heads = []
                elif entry.get("type") == "assistant" and isinstance(content, list):
                    for block in content:
                        if block.get("type") != "tool_use":
                            continue
                        args = block.get("input") or {}
                        name = str(block.get("name") or "")
                        if ZAPIS_VYZOV.search(name):
                            body = args.get("content") or args.get("entry") or ""
                            if not body and "kg_add" in name:
                                body = " ".join(str(args.get(k, "")) for k in ("subject", "predicate", "object"))
                            heads.append(" ".join(str(body).split())[:200])
                        elif name == "Bash" and ZAPIS_GIT.search(str(args.get("command") or "")):
                            command = str(args.get("command") or "")
                            msg = re.search(r"commit[^\n]*?-q?m\s+[\"']([^\"']+)", command)
                            heads.append("отправлено в git: " + (msg.group(1)[:180] if msg else command[:180]))
    except OSError:
        return
    heads = [one for one in heads if one.strip()]
    if not heads:
        return
    try:
        path, already = recorded_subjects(session)
        path.write_text(json.dumps((already + heads)[-12:], ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    parsed = hooks_cli._parse_harness_input(data, "claude-code")  # noqa: SLF001

    # Уже внутри цикла сохранения: пропустить, иначе получится петля.
    if str(parsed["stop_hook_active"]).lower() in ("true", "1", "yes"):
        print(json.dumps({}))
        return

    turns = human_turns(parsed["transcript_path"])
    state_dir = hooks_cli.STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    marker = state_dir / f"{parsed['session_id']}_last_checkpoint_turns"
    legacy = state_dir / f"{parsed['session_id']}_last_save_turns"
    try:
        last = int((marker if marker.exists() else legacy).read_text(encoding="utf-8").strip())
        if last > turns:
            # Стенограмма стала КОРОЧЕ метки: так бывает после сжатия контекста, которое
            # переписывает `.jsonl`. Разность уходит в минус, `early` становится вечно
            # истинной, и хук перестаёт прерывать совсем. 08-10-2026 в живой сессии это
            # дало «созрело, но прошло только -1650 ходов»: классификатор видел зрелую
            # запись и каждый раз молчал. Метке верить нельзя, отсчёт начинаем заново.
            last = turns
            try:
                marker.write_text(str(turns), encoding="utf-8")
            except OSError:
                pass
    except (OSError, ValueError):
        # Стенограмма проекта накапливается через `--resume` и сжатие контекста: `turns`
        # считает ходы за всю её жизнь, а метка заводится на идентификатор сессии. У новой
        # сессии её нет, и прежний ноль означал «1867 ходов без записи» на первом же ходе —
        # страховка срабатывала сразу и потом каждый ход. Отсчёт начинается отсюда.
        last = turns
        try:
            marker.write_text(str(turns), encoding="utf-8")
        except OSError:
            pass

    session = str(parsed["session_id"])
    transcript = str(parsed["transcript_path"])
    here = str(data.get("cwd") or "")

    # Сначала то, что видно без модели: необёрнутый прогон и красные ворота. Это факты, а
    # не суждение, поэтому они прерывают сами и не ждут классификатора — и ход на них не
    # тратится. Каждый докладывается ОДИН раз: повторять одно и то же каждым ходом значит
    # ровно то, за что хук уже ругали.
    state_file = state_dir / f"{session}_seen_facts.json"
    try:
        told = set(json.loads(state_file.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        told = set()
    facts: list[str] = []
    for command in unwrapped_runs(transcript, here):
        if f"run:{command}" not in told:
            told.add(f"run:{command}")
            facts.append(f"Запуск без W&B и без рекордера: `{command}`")
    for row in red_proposals(here):
        if f"mr:{row}" not in told:
            told.add(f"mr:{row}")
            facts.append(f"Красные ворота: {row}")
    for row in nesohranennoe(here, transcript):
        # Ключ без числа файлов: иначе каждая следующая правка в том же клоне считалась бы
        # новым случаем, и строка повторялась бы ходами.
        klyuch = f"git:{row.split(':')[0]}"
        if klyuch not in told:
            told.add(klyuch)
            facts.append(f"Лежит в клоне, но не в базе — {row}")
    if facts:
        try:
            state_file.write_text(json.dumps(sorted(told), ensure_ascii=False),
                                  encoding="utf-8")
        except OSError:
            pass
        lines = "\n".join(f"  {one}" for one in facts)
        print(json.dumps({"decision": "block", "reason":
                          f"{lines}\nЧто делать — `{RULE}`."}, ensure_ascii=False))
        return
    if turn_wrote(transcript):
        # Запись в этом ходе уже была: прервать значит попросить её второй раз. Отсчёт
        # страховки идёт от записи, а не от прошлого прерывания: иначе она говорит «N ходов
        # без записи» сессии, которая писала сама, без напоминаний. И запомнить, ЧТО записано:
        # классификатор видит только текст ответа, и без этого он не знает, что тема закрыта.
        try:
            marker.write_text(str(turns), encoding="utf-8")
        except OSError:
            pass
        remember_written(session, transcript)
        print(json.dumps({}))
        return
    fired = turns > 0 and turns - last >= SAVE_INTERVAL
    verdict = (ask_router(session, transcript, turns, last, fired,
                          str(data.get("cwd") or "")) if JEV_DECIDES else {})

    # Решает классификатор, если ответил. Не ответил — старое правило по счётчику.
    if verdict.get("прерывать") is None:
        interrupt = fired
    else:
        interrupt = bool(verdict["прерывать"])

    if not interrupt:
        print(json.dumps({}))
        return

    try:
        marker.write_text(str(turns), encoding="utf-8")
    except OSError:
        pass
    hooks_cli._maybe_auto_ingest()  # noqa: SLF001 — сохраняем поведение обёртки

    # Правила записи в базу печатаются всегда. Прежде они стояли за проверкой того, что в
    # настройках клиента прописана MCP-служба `lab-knowledge`, — а служба удалена
    # 07-10-2026 вместе со своей базой. У студента `setup.sh` эту запись выбрасывает,
    # когда нет LAB_MCP_URL, так что правила базы ему не печатались никогда. База теперь
    # это git-клоны, они есть у всех, и сам текст ниже объясняет, что делать, когда клона
    # рядом нет: спросить владельца.
    # Подсказка классификатора и есть весь ответ. Молчит он только когда прерывание пришло
    # не от него (счётчик-страховка), и тогда нужна одна строка вместо неё.
    hint = (verdict.get("подсказка") or "").strip()
    reason = hint or ("Остановка на запись: посмотри, не осталось ли незаписанного за "
                      "последние ходы. Если нет, скажи это одной строкой и иди дальше.")
    reason += f" Как записывать — `{RULE}`."
    remember_subject(session, transcript)
    # Запомнить выбранные места: на следующем ходе они удерживаются полосой.
    try:
        path, _ = held_places(session)
        chosen = (verdict.get("места") or []) + (verdict.get("внутри_лабы") or [])
        path.write_text(json.dumps(chosen, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    print(json.dumps({"decision": "block", "reason": reason}))


if __name__ == "__main__":
    main()
