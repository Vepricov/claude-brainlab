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

The lab section appears only when a lab-knowledge MCP server is configured, so an install
without lab access is not nagged about an unconfigured base. Configuration is not a
reachability check. Checkpoint markers track requests only; the agent must read back writes.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import mempalace.hooks_cli as hooks_cli

SETTINGS = Path.home() / ".claude" / "settings.json"
CODEX_CONFIG = Path.home() / ".codex" / "config.toml"

#: Настоящих сообщений человека между сохранениями.
SAVE_INTERVAL = 10

OBSIDIAN_ADDENDUM = """
4. obsidian — сохранить durable-результат в уже привязанных заметках проекта. Путь берётся
   из файла сопоставления своего клиента, канонические файлы переиспользуются, general/ для
   привязанного проекта не выдумывается, приватное остаётся приватным. Записать протокол,
   результаты, решения и открытые вопросы; прочитать заметку обратно и назвать путь.
   Если durable ничего не изменилось — пропустить.
"""

#: Хук выполняется в КАЖДОМ ходе, поэтому здесь только то, что нельзя забыть в момент
#: остановки. Как писать в базу — `~/.claude/rules/lab.md`, он читается один раз за сессию.
#: Владелец 02-10-2026: «этот хук какой-то огромный, никазистый… он просто постоянно одну и
#: ту же инфу читает, это же тупизм. То, что делать, должно быть записано в CLAUDE.md». До
#: этого здесь лежало тридцать три строки, в них упоминался выключенный Postgres и пример с
#: чужой работой, а про главное — не мусорить — не было сказано ни слова.
LAB_ADDENDUM = """
5. lab knowledge — записать, что лаборатория узнала за сессию. База это git-клон работы:
   правка файлов, коммит, `git push -o merge_request.create -o merge_request.assign=<логин>`;
   слияние человеком и есть запись. Тело предложения берётся из сообщения коммита. Как
   писать — `~/.claude/rules/lab.md`.
   Куда именно: научное — в работу, под утверждение (прогон, серия, выкладка, сам текст
   утверждения). Инструкция, которая нужна другим, — в справочник `brainlab/handbook`.
   Изменился способ работы лаборатории — в журнал `brainlab/journal`. Это три разных места,
   и путать их дорого.
   **Главное: не мусорить.** Ни выдуманных чисел, ни новых папок и разделов, ни записи без
   утверждения, под которое она идёт. Чекпоинт, локальная заметка и незелёное предложение
   записью не являются — отложенное назвать вслух. Предложение не закончено, пока у него
   есть неснятые замечания: `lab checks` печатает их отдельно.
"""


def lab_base_configured(harness: str = "claude-code", cwd: str = "") -> bool:
    """Check this client's configuration, without reading or printing credentials."""
    if harness == "codex":
        try:
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib
            config = tomllib.loads(CODEX_CONFIG.read_text(encoding="utf-8"))
        except (ImportError, OSError, ValueError):
            return False
        server = config.get("mcp_servers", {}).get("lab-knowledge")
        return isinstance(server, dict) and server.get("enabled", True) is not False
    paths = [SETTINGS, Path.home() / ".claude.json"]
    if cwd:
        paths.append(Path(cwd) / ".mcp.json")
    for path in paths:
        try:
            config = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(config, dict):
            continue
        server = config.get("mcpServers", {}).get("lab-knowledge")
        if isinstance(server, dict) and server.get("disabled", False) is not True:
            return True
    return False


def transcript_harness(transcript_path: str) -> str:
    path = Path(transcript_path).expanduser()
    if path.is_file():
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if isinstance(entry, dict):
                    if entry.get("type") in ("session_meta", "response_item"):
                        return "codex"
                    if isinstance(entry.get("message"), dict):
                        return "claude-code"
    return "claude-code"


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
        handle, path = tempfile.mkstemp(suffix=".json", prefix="jev-route-")
        with open(handle, "w", encoding="utf-8") as payload:
            json.dump({"сессия": session, "ходов": turns, "прошлое": last,
                       "счётчик_сработал": fired, "текст": text,
                       "каталог": cwd, "записанное": already},
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

    harness = transcript_harness(parsed["transcript_path"])
    turns = human_turns(parsed["transcript_path"])
    state_dir = hooks_cli.STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    marker = state_dir / f"{parsed['session_id']}_last_checkpoint_turns"
    legacy = state_dir / f"{parsed['session_id']}_last_save_turns"
    try:
        last = int((marker if marker.exists() else legacy).read_text(encoding="utf-8").strip())
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

    reason = hooks_cli.STOP_BLOCK_REASON.rstrip() + OBSIDIAN_ADDENDUM
    if lab_base_configured(harness, str(data.get("cwd") or "")):
        reason = reason.rstrip() + "\n" + LAB_ADDENDUM
    подсказка = verdict.get("подсказка") or ""
    if подсказка:
        reason = reason.rstrip() + "\n\n" + подсказка + "\n"
    remember_subject(session, transcript)
    print(json.dumps({"decision": "block", "reason": reason}))


if __name__ == "__main__":
    main()
