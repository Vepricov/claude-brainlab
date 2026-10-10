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
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(entry, dict):
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
            if any(mark in text for mark in NOT_A_PERSON):
                continue
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
#: Признак обёртки: рекордер зовут из обучающего кода, а не из командной строки, поэтому
#: ищется он В ФАЙЛЕ точки входа, а не в команде.
WRAPPED = ("LabRun", "lab_run")


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
                    low = command.lower()
                    if not any(one in low for one in LAUNCHERS):
                        continue
                    if not any(one in low for one in TRAINING):
                        continue
                    if any(one in command for one in WRAPPED):
                        continue
                    wrapped = False
                    for name in _entrypoints(command):
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
            facts.append(f"Запуск без рекордера: `{command}`")
    for row in red_proposals(here):
        if f"mr:{row}" not in told:
            told.add(f"mr:{row}")
            facts.append(f"Красные ворота: {row}")
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
