#!/usr/bin/env python3
"""Записать помеченное знание в общую базу лаборатории. Без модели и без токенов.

ЗАЧЕМ ИНАЧЕ, ЧЕМ У ПАМЯТИ АГЕНТА

Хук памяти работает так: он останавливает завершение хода и просит агента самому
сформулировать и записать. Значит каждый ход стоит вызова модели. Для общей базы это
неприемлемо: писать в неё надо часто, а платить за каждый ход нельзя.

Поэтому здесь решение принимает не модель, а разметка. Кто угодно, человек или агент,
помечает в своём сообщении факт одной строкой, и хук эту строку разбирает
детерминированно. Разбор стоит ноль, а точность полная: записывается ровно то, что
написано, без домыслов.

РАЗМЕТКА

    ЛАБ-ГИПОТЕЗА: <утверждение> | опровергается: <критерий>
    ЛАБ-РЕШЕНИЕ: <что постановили> | потому что: <обоснование>
    ЛАБ-ЧИСЛО: <название метрики> = <значение> | где: <код прогона, E-WRM-019>
    ЛАБ-ВОПРОС: <что осталось непонятным>
    ЛАБ-КОД: <репозиторий> | шов: <что меняют> -> <файл или флаг>
    ЛАБ-КОД: <репозиторий> | грабли: <на чём теряют час>

К любой строке можно добавить хвосты «| тема: <слаг>» и «| статьи: a, b». Строкам про код
тема не нужна: карта репозитория общая для всей лаборатории, как статья.

ПОЧЕМУ КОД ЗАПИСЫВАЕТСЯ ПО СТРОЧКЕ

Знание о коде не появляется готовой картой. Человек лезет в чужой репозиторий по своему
делу, теряет час на граблях, выясняет, где менять оптимизатор, — и это стоит ровно одной
строки, написанной тогда же. Составить карту целиком он не сядет никогда, а пересылать
её ради одной находки нельзя: неполная посылка молча сотрёт остальное. Поэтому здесь
`record_code_note`: незнакомый репозиторий заводится заготовкой, дальше карта растёт по
строчке, повтор той же находки заменяет её, а не кладётся рядом.

КУДА ПОПАДАЕТ ЗАПИСЬ

Домом знания служит ТЕМА исследования, а не статья. Утверждение про метод касается сразу
нескольких работ, и когда приходилось выбирать одну, запись выглядела лежащей не там.
Поэтому статьи здесь только теги.

Тема ищется по порядку: явный хвост «тема», затем тема названной статьи, затем догадка по
словам самой строки, затем тема каталога, из которого идёт работа. Если ничего не совпало,
запись идёт в тему «Общее лабораторное» и находится поиском: раньше она в таком случае
оставалась в очереди и до базы не доходила вовсе. Тему можно переставить потом, запись при
этом не двигается и код не меняется.

НАДЁЖНОСТЬ

Хук никогда не роняет сессию: любая беда уходит в журнал, а не в лицо. База недоступна —
запись кладётся в очередь и уходит при следующем удачном запуске, поэтому упавший VPN не
теряет ничего. Ключ идемпотентности считается от текста, поэтому повтор той же строки не
плодит дубли: на этом уже обжигались, когда за одну ночь появилось тринадцать копий одной
гипотезы.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CONFIG = Path("~/.config/brainlab/lab-hook.json").expanduser()
QUEUE = Path("~/.local/state/brainlab/lab-hook-queue.jsonl").expanduser()
LOG = Path("~/.local/state/brainlab/lab-hook.log").expanduser()
REGISTRY = Path("~/.claude/obsidian-projects.json").expanduser()
#: Тема-приёмник. Знание без определённой темы всё равно должно попасть в базу: пока оно
#: ждёт в очереди, его нет ни у кого.
GENERAL = "lab-general"

MARKERS = {
    "hypothesis": re.compile(
        r"^\s*ЛАБ-ГИПОТЕЗА:\s*(?P<statement>.+?)\s*\|\s*опроверга\w*:\s*(?P<falsification>.+?)\s*$",
        re.IGNORECASE),
    "decision": re.compile(
        r"^\s*ЛАБ-РЕШЕНИЕ:\s*(?P<statement>.+?)\s*\|\s*потому что:\s*(?P<rationale>.+?)\s*$",
        re.IGNORECASE),
    "metric": re.compile(
        r"^\s*ЛАБ-ЧИСЛО:\s*(?P<name>[^=]+?)\s*=\s*(?P<value>[^|]+?)\s*\|\s*где:\s*(?P<where>.+?)\s*$",
        re.IGNORECASE),
    "question": re.compile(r"^\s*ЛАБ-ВОПРОС:\s*(?P<text>.+?)\s*$", re.IGNORECASE),
    # Код отличается от остального тем, что у него нет темы: карта репозитория
    # общелабораторная, как статья. Одним репозиторием пользуются несколько работ, и
    # привязка к одной сделала бы находку невидимой из остальных.
    "code_seam": re.compile(
        r"^\s*ЛАБ-КОД:\s*(?P<repo>[^|]+?)\s*\|\s*шов:\s*(?P<what>.+?)\s*(?:->|→)\s*(?P<where>.+?)\s*$",
        re.IGNORECASE),
    "code_quirk": re.compile(
        r"^\s*ЛАБ-КОД:\s*(?P<repo>[^|]+?)\s*\|\s*грабли:\s*(?P<what>.+?)\s*$",
        re.IGNORECASE),
}
THEME_TAIL = re.compile(r"\s*\|\s*тем[аеы]:\s*(?P<theme>[\w-]+)\s*(?=\||$)", re.IGNORECASE)
#: «проект» оставлен как имя для статьи: так написана разметка в старых заметках, и ломать
#: её из-за переименования нельзя.
PAPERS_TAIL = re.compile(
    r"\s*\|\s*(?:стать[ьия]|проект)\w*:\s*(?P<papers>[\w\-,\s]+?)\s*(?=\||$)", re.IGNORECASE)
#: Признаки того, что строка не утверждение, а показ разметки. Без этого хук записывает
#: собственную документацию: объяснение «пиши вот так» выглядит для него утверждением.
PLACEHOLDER = re.compile(r"<[^>]{2,}>|\[\s*\||\.\.\.|…|\{[a-z_]+\}", re.IGNORECASE)

#: Слова, по которым тема узнаётся в тексте, когда её не назвали. Список нарочно короткий и
#: состоит из имён методов, а не из общих слов: «сходимость» есть в каждой второй строке и
#: темы не различает. Темы «Прочее» здесь не участвуют — у области без общего предмета не
#: может быть своих слов.
GLOSSARY: dict[str, tuple[str, ...]] = {
    "muon-sign-methods": ("muon", "мюон", "sign", "знаков", "signsgd", "lion", "softsign",
                          "ортогонализ", "newton-schulz"),
    "preconditioning-curvature": ("k-fac", "kfac", "kronecker", "кронекер", "fisher", "фишер",
                                  "предобусл", "кривизн", "shampoo", "soap", "второго порядка"),
    "rank-budget": ("бюджет ранга", "выбор ранга", "отбор адаптер", "rank budget"),
    "low-rank-step-geometry": ("низкоранг", "low-rank", "lora-pro", "геометрия шага"),
    "adapter-composition": ("композиц", "слияние адаптер", "merge adapters", "doc2lora"),
    "zo-estimators": ("безградиент", "zeroth", "нулевого порядка", "zo-", "двухточеч",
                      "одноточеч"),
    "non-euclidean-dependent": ("брегман", "bregman", "неевклид", "марков", "зависимые данные",
                                "зависимой выборк"),
    "huawei-programme": ("huawei", "хуавей", "ascend", "npu"),
    # Тема не обязана быть научной: то, чем лаборатория работает, тоже знание, и раньше оно
    # уходило в приёмник, хотя у него есть своя область.
    "lab-agents": ("хук", "скилл", "mcp", "витрин", "brain call", "yonote", "обсидиан",
                   "obsidian", "агент", "инструмент базы", "синхрониз"),
}


def ascii_segment(value: str, default: str = "session") -> str:
    """Путь в источнике обязан быть только из ASCII: база отвергает остальное.

    Проверяется правилом [A-Za-z0-9._~-]+ на каждый сегмент, поэтому кириллица,
    пробелы и слеши внутри номера сессии ломают запись целиком.
    """
    clean = re.sub(r"[^A-Za-z0-9._~-]", "", value or "")
    return clean or default


def note(message: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} {message}\n")


def config() -> dict:
    if CONFIG.is_file():
        try:
            return json.loads(CONFIG.read_text(encoding="utf-8"))
        except ValueError as error:
            note(f"настройки не разобрались: {error}")
    return {}


def paper_from_cwd(cwd: str) -> str | None:
    """Слаг работы по рабочему каталогу: то же правило, что и у заметок.

    Это только подсказка. Раньше отсюда бралось обязательное имя проекта, и знание,
    записанное из каталога вне лаборатории, до базы не доходило.
    """
    if not REGISTRY.is_file():
        return None
    try:
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except ValueError:
        return None
    path = Path(cwd or ".").expanduser().resolve()
    for root in registry.get("roots") or []:
        base = Path(root["fs"]).expanduser().resolve()
        for folder, vault in (root.get("items") or {}).items():
            if (base / folder) == path or (base / folder) in path.parents:
                return vault.rsplit("/", 1)[-1]
    return None


def harvest(transcript: Path) -> list[dict]:
    """Вынуть помеченные строки из стенограммы хода.

    Читаются только сообщения, а не вывод инструментов: инструмент может напечатать
    разметку из файла, и тогда в базу уехало бы то, чего никто не утверждал.
    """
    if not transcript.is_file():
        return []
    found: list[dict] = []
    for line in transcript.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        message = event.get("message") or {}
        if message.get("role") not in ("assistant", "user"):
            continue
        content = message.get("content")
        parts = ([content] if isinstance(content, str)
                 else [block.get("text", "") for block in content or []
                       if isinstance(block, dict) and block.get("type") == "text"])
        for text in parts:
            в_коде = False
            for raw in str(text).splitlines():
                # Внутри огороженного блока лежит пример или чужой текст, а не то, что
                # человек утверждает от себя.
                if raw.lstrip().startswith("```"):
                    в_коде = not в_коде
                    continue
                if в_коде or PLACEHOLDER.search(raw):
                    continue
                theme_tail = THEME_TAIL.search(raw)
                papers_tail = PAPERS_TAIL.search(raw)
                clean = THEME_TAIL.sub("", PAPERS_TAIL.sub("", raw))
                for kind, pattern in MARKERS.items():
                    match = pattern.match(clean)
                    if match:
                        found.append({
                            "kind": kind,
                            "theme": theme_tail.group("theme") if theme_tail else None,
                            "papers": [
                                part.strip()
                                for part in (papers_tail.group("papers").split(",")
                                             if papers_tail else [])
                                if part.strip()
                            ],
                            "text_for_guess": clean,
                            **match.groupdict(),
                        })
    return found


#: Слаги, совпадающие с обычными словами. Такое упоминание считается только при явном
#: указании вида «проект also»: иначе служебное «also» в англоязычной пометке уводило запись в
#: тему неевклидовой оптимизации и вешало ей чужой тег статьи.
AMBIGUOUS_SLUGS = frozenset({"also", "warmup"})
#: Слова, после которых название работы названо намеренно.
DELIBERATE = r"(?:проект\w*|стать\w+|работ\w+|paper|project)\s+[«\"']?"


def mentions(text: str, papers: dict) -> list[str]:
    """Работы, названные в тексте НАМЕРЕННО.

    Простая подстрока не годится: слаг «also» встречается в любом англоязычном тексте, а
    «warmup» это ещё и обычный термин. Считается упоминание, если слаг стоит отдельным словом и
    при этом либо сам похож на слаг (есть дефис или цифра), либо назван после слова «проект»,
    «статья», «работа», либо совпало отличимое короткое имя работы вида SignMuon.
    """
    found: list[str] = []
    for slug, item in papers.items():
        edge = r"(?<![\w-])" + re.escape(slug) + r"(?![\w-])"
        deliberate = re.search(DELIBERATE + edge, text, re.IGNORECASE) is not None
        looks_like_slug = ("-" in slug or any(ch.isdigit() for ch in slug))
        plain = re.search(edge, text, re.IGNORECASE) is not None
        short = item.get("short") or ""
        # Короткое имя берётся только если оно отличимо: не короче пяти знаков и не сводится к
        # обычному слову. «SignMuon» годится, «ALSO» нет.
        by_short = (
            len(short) >= 5
            and short.casefold() not in AMBIGUOUS_SLUGS
            and re.search(r"(?<![\w-])" + re.escape(short) + r"(?![\w-])", text,
                          re.IGNORECASE) is not None
        )
        if slug in AMBIGUOUS_SLUGS:
            if deliberate or by_short:
                found.append(slug)
            continue
        if deliberate or by_short or (plain and looks_like_slug) or (plain and len(slug) >= 5):
            found.append(slug)
    return found


def route(record: dict, base: dict, hint: str | None) -> tuple[str, list[str]]:
    """Тема записи и статьи-теги. Всегда возвращает существующую тему.

    Порядок нарочно такой: сказанное человеком важнее догадки, догадка по словам важнее
    каталога, а каталог это лишь подсказка. Ничего не отбрасывается: не совпало — «Общее».
    """
    themes = base["themes"]
    papers = list(record.get("papers") or [])
    known = [slug for slug in papers if slug in base["papers"]]

    named = (record.get("theme") or "").strip()
    if named in themes:
        return named, known
    if named:
        note(f"тема «{named}» не найдена, ищу по тексту")

    if known:
        return base["papers"][known[0]]["theme_slug"], known

    text = record.get("text_for_guess") or ""
    mentioned = mentions(text, base["papers"])
    if mentioned:
        return base["papers"][mentioned[0]]["theme_slug"], sorted(set(known + mentioned))

    hits = {slug: sum(word in text for word in words)
            for slug, words in GLOSSARY.items() if slug in themes}
    best = max(hits.items(), key=lambda pair: pair[1], default=(GENERAL, 0))
    if best[1] and list(hits.values()).count(best[1]) == 1:
        return best[0], known

    if hint and hint in base["papers"]:
        return base["papers"][hint]["theme_slug"], sorted(set(known + [hint]))
    return GENERAL, known


def call(endpoint: str, token: str, tool: str, arguments: dict) -> dict | None:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": tool, "arguments": arguments}}).encode("utf-8")
    request = urllib.request.Request(endpoint, data=body, headers={
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {token}",
    })
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    result = payload.get("result") or {}
    if result.get("isError"):
        text = next((block.get("text") for block in result.get("content") or []
                     if isinstance(block.get("text"), str)), "")
        raise RuntimeError(text[:200])
    structured = result.get("structuredContent") or {}
    return structured.get("result", structured)


def key(record: dict) -> str:
    """Ключ от текста: повтор той же строки не должен плодить копии."""
    payload = json.dumps(record, ensure_ascii=False, sort_keys=True)
    return "lab-hook-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def enqueue(record: dict) -> None:
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    with QUEUE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def dedupe(records: list[dict]) -> list[dict]:
    """Убрать повторы по ключу записи, сохранив порядок.

    Хук каждый ход перечитывает стенограмму целиком, поэтому при недоступной базе очередь
    дописывалась полным урожаем снова и снова и росла копиями одной пометки. Ключ считается от
    текста, так что повтор виден без обращения к базе.
    """
    seen: set[str] = set()
    out: list[dict] = []
    for record in records:
        mark = key({name: value for name, value in record.items() if name != "hint"})
        if mark in seen:
            continue
        seen.add(mark)
        out.append(record)
    return out


def pending() -> list[dict]:
    if not QUEUE.is_file():
        return []
    out = []
    for line in QUEUE.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def catalogue(endpoint: str, token: str) -> dict:
    """Темы и работы одним запросом: по ним и определяется адресат записи."""
    items = call(endpoint, token, "list_projects", {"limit": 200})["items"]
    themes, papers = {}, {}
    for item in items:
        row = {
            "id": item["id"],
            "code": (item.get("public_code") or "").upper(),
            "theme_slug": item.get("theme_slug") or "",
            # Короткое имя работы: по нему её узнают в тексте, «SignMuon» вместо слага.
            "short": (item.get("name") or "").split("—")[0].strip().casefold(),
        }
        if item.get("kind") == "theme":
            themes[item["slug"]] = row
        else:
            papers[item["slug"]] = row
    return {"themes": themes, "papers": papers}


def next_code(context: dict, code: str) -> str:
    """Свободный человекочитаемый код вида H-MSM-042.

    Без кода на запись нельзя сослаться в разговоре и в статье: люди называют
    гипотезу кодом, а не первой строкой утверждения.
    """
    used = {str(item.get("public_code") or "") for item in context.get("hypotheses") or []}
    numbers = [int(found.group(1)) for value in used
               if (found := re.fullmatch(rf"H-{code}-(\d+)", value))]
    return f"H-{code}-{max(numbers, default=0) + 1:03d}"


def short_title(statement: str) -> str:
    """Заголовок записи: то, что видно в списках и в отчётах.

    Первое предложение годится не всегда: утверждение часто пишут одной длинной фразой без
    точки, и тогда заголовком становится оно целиком, а список превращается в простыню.
    Поэтому длинную фразу режем по границе оборота, а не по буквам посередине слова.
    """
    text = re.split(r"(?<=[.!?])\s", statement.strip())[0].strip()
    if len(text) <= 80:
        return text
    for mark in (", ", " — ", ": ", "; "):
        head = text.split(mark)[0]
        if 24 <= len(head) <= 80:
            return head
    cut = text[:80].rsplit(" ", 1)[0]
    return cut + "…"


def write(record: dict, settings: dict, base: dict, hint: str | None) -> str:
    """Записать одну помеченную вещь.

    Исход один из трёх: «записано», «уже было», «отложить». Различать первые два важно, иначе
    хук сообщает о записи, когда база лишь вернула прежний ответ по тому же ключу, и по его
    словам нельзя понять, появилось ли что-то новое.
    """
    endpoint = settings.get("endpoint") or "http://127.0.0.1:8000/mcp"
    token = settings.get("token") or os.environ.get("LAB_MCP_TOKEN") or ""
    author = settings.get("author") or os.environ.get("USER") or "неизвестный"

    # Код уходит раньше разбора темы: темы у него нет, и попытка её найти кончилась бы
    # отказом «тема отсутствует» на совершенно исправной записи.
    if record["kind"] in ("code_seam", "code_quirk"):
        arguments = {
            "repo": record["repo"].strip(),
            "kind": "seam" if record["kind"] == "code_seam" else "quirk",
            "what": record["what"].strip(),
        }
        if record["kind"] == "code_seam":
            arguments["where"] = record["where"].strip()
        answer = call(endpoint, token, "record_code_note", arguments)
        # «Уже было» видно по ответу службы: она различает дописанное и заменённое.
        return "already" if (answer or {}).get("outcome") == "replaced" else "written"

    theme_slug, papers = route(record, base, hint)
    theme = base["themes"].get(theme_slug)
    if theme is None:
        note(f"тема «{theme_slug}» отсутствует в базе, запись отложена")
        return "defer"
    project_id = theme["id"]

    # Ключ идемпотентности обязателен у каждого пишущего инструмента: без него
    # повторный запуск хука создаёт вторую копию той же записи.
    source = {
        "project_id": project_id,
        "uri": f"brainlab-source://{theme_slug}/hook/{ascii_segment(record.get('session'))}",
        "title": f"Помечено в работе: {author}",
        "kind": "note",
        "idempotency_key": key({"источник": record.get("session"), "тема": theme_slug}),
    }
    tail = f", статьи: {', '.join(papers)}" if papers else ""
    if record["kind"] in ("hypothesis", "decision"):
        # Контекст темы читается один раз: он же говорит, нет ли уже такой записи, и он же
        # даёт занятые коды. Проверка до записи нужна не ради экономии: при повторе гипотеза
        # получила бы следующий свободный код, нагрузка при том же ключе изменилась бы, и база
        # справедливо отказала бы, оставив запись в очереди навсегда.
        context = call(endpoint, token, "get_project_context", {"project_id": project_id})
        section = "hypotheses" if record["kind"] == "hypothesis" else "decisions"
        said = record["statement"].strip()
        if any((item.get("statement") or "").strip() == said
               for item in context.get(section) or []):
            return "already"
    if record["kind"] == "hypothesis":
        source_id = call(endpoint, token, "publish_source_note", source)["id"]
        code = theme["code"] or theme_slug[:3].upper()
        title = short_title(record["statement"])
        call(endpoint, token, "create_hypothesis", {
            "project_id": project_id,
            "statement": record["statement"],
            "falsification_criteria": record["falsification"],
            "source_ref_id": source_id,
            "idempotency_key": key(record),
            "public_code": next_code(context, code),
            "title": title,
            "papers": papers,
            "status_reason": f"Помечено в работе, автор {author}{tail}",
        })
        return "written"
    if record["kind"] == "question":
        # Открытые вопросы это список у темы, поэтому дописываются к нему.
        context = call(endpoint, token, "get_project_context", {"project_id": project_id})
        current = ((context.get("project") or {}).get("open_questions") or [])
        line = f"{record['text']} ({author}{tail})"
        if line in current:
            return "already"
        call(endpoint, token, "set_project_open_questions", {
            "project_id": project_id, "open_questions": [*current, line],
            "idempotency_key": key(record)})
        return "written"
    if record["kind"] == "decision":
        source_id = call(endpoint, token, "publish_source_note", source)["id"]
        call(endpoint, token, "propose_decision", {
            "project_id": project_id,
            "statement": record["statement"],
            "rationale": record["rationale"],
            "source_ref_id": source_id,
            "papers": papers,
            "idempotency_key": key(record),
        })
        return "written"
    if record["kind"] == "metric":
        # Число пишется ИЗМЕРЕНИЕМ, как ему и положено. Раньше хук клал его строкой в
        # открытые вопросы с пометкой «оформить свидетельством», то есть перекладывал
        # работу на человека, и число до базы фактически не доходило. Записывать умеет
        # сама служба: record_evidence принимает прогон и по публичному коду, поэтому
        # «где: E-WRM-019» — это всё, что нужно.
        where = record["where"].strip()
        name = record["name"].strip()
        value = record["value"].strip()
        number = None
        try:
            number = float(value.replace(",", ".").split()[0])
        except (ValueError, IndexError):
            pass
        written = call(endpoint, token, "record_evidence", {
            "experiment_id": where,
            "summary": f"{name} = {value}",
            "kind": "metric" if number is not None else "observation",
            "metrics": [{"name": name, "value": number}] if number is not None else [],
            "observations": [] if number is not None else [f"{name} = {value}"],
            "title": name[:120],
            "idempotency_key": key(record),
        })
        if isinstance(written, dict) and written.get("id"):
            return "written"
        # Прогон не назван или назван так, что его не нашли. Догадываться нельзя: число,
        # приписанное чужому прогону, хуже ненаписанного. Но и терять его нельзя, поэтому
        # оно ложится открытым вопросом — как раньше, но теперь это запасной путь, а не
        # основной, и в нём сказано, чего не хватило.
        context = call(endpoint, token, "get_project_context", {"project_id": project_id})
        current = ((context.get("project") or {}).get("open_questions") or [])
        line = (f"Число из работы: {name} = {value} ({where or 'прогон не назван'}, "
                f"{author}{tail}) — прогон по этому имени не нашёлся, назовите его "
                f"публичным кодом вида E-XXX-123")
        if line in current:
            return "already"
        call(endpoint, token, "set_project_open_questions", {
            "project_id": project_id, "open_questions": [*current, line],
            "idempotency_key": key(record)})
        return "written"
    return "defer"


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except ValueError:
        return 0

    settings = config()
    if settings.get("enabled") is False:
        return 0

    records = harvest(Path(payload.get("transcript_path") or ""))
    session = str(payload.get("session_id") or "")[:12]
    # Подсказка каталога запоминается В САМОЙ записи. Раньше она считалась один раз из
    # текущего каталога и применялась ко всей очереди: отложенная из ~/Papers/sign_muon
    # запись на следующий день уезжала в тему того проекта, где человек работал сегодня, с
    # чужим тегом статьи, и журнал об этом молчал.
    here = paper_from_cwd(payload.get("cwd") or "")
    for record in records:
        record["session"] = session
        record["hint"] = here

    queue = dedupe(pending() + records)
    if not queue:
        return 0

    endpoint = settings.get("endpoint") or "http://127.0.0.1:8000/mcp"
    token = settings.get("token") or os.environ.get("LAB_MCP_TOKEN") or ""
    try:
        base = catalogue(endpoint, token)
    except (urllib.error.URLError, TimeoutError, RuntimeError, KeyError) as error:
        note(f"база недоступна ({str(error)[:80]}), в очереди {len(queue)}")
        QUEUE.parent.mkdir(parents=True, exist_ok=True)
        QUEUE.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n"
                                for item in dedupe(queue)), encoding="utf-8")
        return 0

    left, done, already = [], 0, 0
    for record in queue:
        try:
            outcome = write(record, settings, base, record.get("hint"))
            if outcome == "written":
                done += 1
            elif outcome == "already":
                already += 1
            else:
                left.append(record)
        except RuntimeError as error:
            # «Ключ уже использован» означает, что эта же запись уже лежит в базе: ключ
            # считается от её текста. Отказ приходит потому, что при повторе гипотеза
            # получает следующий свободный код, и нагрузка при том же ключе меняется. Держать
            # такую запись в очереди значит вечно повторять её и копить ошибки в журнале.
            if "idempotency key" in str(error) and "reus" in str(error):
                already += 1
                continue
            note(f"не записалось ({str(error)[:100]}): {str(record)[:100]}")
            left.append(record)
        except (urllib.error.URLError, TimeoutError, KeyError) as error:
            note(f"не записалось ({str(error)[:100]}): {str(record)[:100]}")
            left.append(record)
    QUEUE.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n"
                             for item in dedupe(left)), encoding="utf-8")
    if done or already:
        note(f"записано: {done}, уже было: {already}, осталось в очереди: {len(left)}")
    if done:
        print(f"В общую базу лаборатории записано: {done}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:  # noqa: BLE001 — хук не имеет права ронять сессию
        note(f"необработанное: {error}")
        raise SystemExit(0) from None
