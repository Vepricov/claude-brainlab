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
                  | механизм: <почему это верно> | условия: <модели, масштабы, режим>
    ЛАБ-РЕШЕНИЕ: <что постановили> | потому что: <обоснование>
    ЛАБ-ЧИСЛО: <название метрики> = <значение> | где: <код прогона, E-WRM-019>
               | проверить: <адрес числа: страница в W&B, путь к логу, файл прогона>
    ЛАБ-ВОПРОС: <что осталось непонятным>
    ЛАБ-КОД: <репозиторий> | шов: <что меняют> -> <файл или флаг>
    ЛАБ-КОД: <репозиторий> | грабли: <на чём теряют час>
    ЛАБ-РАБОТА: <слаг>          — над какой работой идёт эта сессия

Работа сессии объявляется один раз строкой «ЛАБ-РАБОТА: dykaf» и дальше действует до её
конца. Если в каталоге лежит файл `.lab-work` со слагом, объявлять не нужно вовсе. К
отдельной строке можно добавить хвост «| работа: <слаг>» — он перебивает объявленное, когда
одна запись про соседнюю работу. Знание живёт
под утверждением работы; если работу назвать нечем, запись откладывается, а не сваливается
в общую полку: в полке у неё нет ни репозитория, ни pull request, и увидеть её некому.
Работа берётся из этого хвоста, из каталога сессии (`~/Papers/<слаг>`) или из упоминания в
самом тексте. Строкам про код работа не нужна: карта репозитория общая для всей лаборатории.

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

#: Объявление работы: «ЛАБ-РАБОТА: dykaf». Агент говорит это один раз, и дальше вся сессия
#: пишет туда. Путь каталога для этого не годится: сессию запускают откуда угодно, а работа
#: у неё одна. Владелец 25-09-2026: «он должен куда-то сказать, над чем он сейчас работает,
#: и туда записывать».
#: Без якорей строки: расшифровка сессии это JSON, и объявление лежит внутри строки вместе
#: с экранированными переводами, а не отдельной строкой файла.
WORK_MARKER = re.compile(r"ЛАБ-РАБОТА:\s*(?P<work>[\w-]+)", re.IGNORECASE)
#: Где помнится объявленное: по файлу на сессию, рядом с очередью.
WORKS = Path("~/.local/state/brainlab/works").expanduser()
#: Файл привязки в каталоге: `.lab-work` со слагом работы внутри. Для постоянных проектов,
#: где объявлять не нужно вовсе.
PINNED = ".lab-work"


def declared(transcript: Path, session: str) -> str | None:
    """Работа, объявленная в этой сессии. Запоминается, чтобы объявить хватило одного раза."""
    remembered = WORKS / f"{session}.txt"
    said = None
    try:
        text = transcript.read_text(encoding="utf-8", errors="replace")
    except OSError:
        text = ""
    for found in WORK_MARKER.finditer(text):
        said = found.group("work").strip()
    if said:
        WORKS.mkdir(parents=True, exist_ok=True)
        remembered.write_text(said, encoding="utf-8")
        return said
    if remembered.is_file():
        return remembered.read_text(encoding="utf-8").strip() or None
    return None


def pinned(cwd: str) -> str | None:
    """Работа, привязанная к каталогу файлом `.lab-work`, здесь или выше по дереву."""
    here = Path(cwd or ".").expanduser().resolve()
    for folder in (here, *here.parents):
        mark = folder / PINNED
        if mark.is_file():
            said = mark.read_text(encoding="utf-8").strip().splitlines()
            if said:
                return said[0].strip()
        if folder == folder.parent:
            break
    return None


MARKERS = {
    # Гипотеза называет ещё механизм и условия: без них предложение не проходит, и
    # правильно не проходит. Владелец 21-09-2026: «гипотеза должна быть понята и полезна
    # всем, она должна быть достаточно широкой». Утверждение без причинной истории и без
    # условий верно ровно там, где его померили, и это заметка, а не знание лаборатории.
    "hypothesis": re.compile(
        r"^\s*ЛАБ-ГИПОТЕЗА:\s*(?P<statement>.+?)\s*\|\s*опроверга\w*:\s*(?P<falsification>[^|]+?)"
        r"(?:\s*\|\s*механизм:\s*(?P<mechanism>[^|]+?))?"
        r"(?:\s*\|\s*услови\w*:\s*(?P<assumptions>[^|]+?))?\s*$",
        re.IGNORECASE),
    "decision": re.compile(
        r"^\s*ЛАБ-РЕШЕНИЕ:\s*(?P<statement>.+?)\s*\|\s*потому что:\s*(?P<rationale>.+?)\s*$",
        re.IGNORECASE),
    # «где» это прогон, «проверить» это адрес, по которому число можно открыть глазами.
    # Это разные вещи, и база требует обе: число без адреса проверить нечем, а значит оно
    # не знание лаборатории. Прежняя разметка адреса не знала вовсе.
    "metric": re.compile(
        r"^\s*ЛАБ-ЧИСЛО:\s*(?P<name>[^=]+?)\s*=\s*(?P<value>[^|]+?)\s*\|\s*где:\s*(?P<where>[^|]+?)"
        r"(?:\s*\|\s*провер\w*:\s*(?P<check>[^|]+?))?\s*$",
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
#: Хвост «| работа: <слаг>». «тема» принимается как прежнее написание: запись, помеченная
#: старым словом, не должна пропасть, но адресатом всё равно становится работа.
THEME_TAIL = re.compile(
    r"\s*\|\s*(?:работ[аеы]|тем[аеы]):\s*(?P<theme>[\w-]+)\s*(?=\||$)", re.IGNORECASE)
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


def work_of(record: dict, base: dict, hint: str | None) -> str | None:
    """Работа, к которой относится запись. `None` — работу назвать нечем.

    Знание живёт под утверждением РАБОТЫ. Тема — полка, у неё нет ни репозитория, ни pull
    request, и запись, отправленная в неё, не попадает ни в один файл: 25-09-2026 в полке
    «Общее лабораторное» так осело одиннадцать тысяч записей, которых в git не существует.
    Владелец: «мусорное вообще нужно скрыть».

    Поэтому работа берётся только оттуда, где она названа однозначно: явным полем, каталогом
    сессии или упоминанием в самом тексте. Угадывать по словам темы больше нельзя — это и
    была дорога в полку.
    """
    papers = base["papers"]
    # Порядок ответов, от самого точного к общему. Работа сессии — это то, что агент
    # объявил сам («ЛАБ-РАБОТА: dykaf»), либо привязка каталога, либо карта путей; она
    # считается один раз в `main` и приходит сюда готовой. Хвост «| работа: …» в самой
    # строке перебивает её: одна запись может быть про соседнюю работу.
    said = (record.get("theme") or "").strip()
    if said in papers:
        return said
    if hint and hint in papers:
        return hint
    named = [slug for slug in (record.get("papers") or ()) if slug in papers]
    if named:
        return named[0]
    mentioned = mentions(record.get("text_for_guess") or "", papers)
    return mentioned[0] if mentioned else None


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


#: Помеченное, которому в общей базе места нет: вопрос без утверждения и карта кода.
#: База держит знание в git, страницы для них там нет, и прежний путь записи их терял.
НЕОТПРАВЛЕННОЕ = Path("~/.local/state/brainlab/lab-hook-unsent.md").expanduser()


def отложить_в_файл(records: list[dict], причина: str) -> None:
    """Сложить в файл то, что база не принимает, и не держать это в очереди вечно.

    Очередь для того, что уйдёт при следующей попытке. Вопрос и карта кода не уйдут
    никогда: под git-хранилищем у них нет страницы, и прежняя запись исчезала при
    первом же чужом слиянии. Поэтому они ложатся рядом, где их видно глазами.
    """
    if not records:
        return
    НЕОТПРАВЛЕННОЕ.parent.mkdir(parents=True, exist_ok=True)
    сегодня = datetime.now(timezone.utc).strftime("%d-%m-%Y")
    строки = [f"\n## {сегодня} — {причина}\n"]
    for record in records:
        текст = (record.get("text") or record.get("what")
                 or record.get("statement") or "").strip()
        куда = record.get("repo") or record.get("hint") or ""
        строки.append(f"- {текст}" + (f"  ({куда})" if куда else ""))
    with НЕОТПРАВЛЕННОЕ.open("a", encoding="utf-8") as файл:
        файл.write("\n".join(строки) + "\n")


def опора(records: list[dict]) -> str:
    """Чем подтверждено помеченное: числа с их прогонами и числовые критерии.

    Предложение без проверяемой опоры служба не примет, и это правильно: ревьюер без
    опоры может только поверить на слово. Поэтому опора собирается из того, что в
    разметке уже есть, а не придумывается.
    """
    куски = []
    for record in records:
        if record["kind"] == "metric":
            где = record["where"].strip() or "прогон не назван"
            куски.append(f"{record['name'].strip()} = {record['value'].strip()} ({где})")
        elif record["kind"] == "hypothesis" and record.get("falsification"):
            куски.append(f"опровергается: {record['falsification'].strip()}")
        elif record["kind"] == "decision" and record.get("rationale"):
            куски.append(f"потому что: {record['rationale'].strip()}")
    return "; ".join(куски)


def предложить(records: list[dict], slug: str, settings: dict, base: dict) -> str:
    """Отправить помеченное за сессию ОДНИМ предложением.

    Прежде хук писал каждую строку прямо в базу. Под git-хранилищем такая запись
    принималась и исчезала при следующем чужом слиянии: знание живёт в git, а прямой
    вызов до него не доходит. Проверено 30-09-2026, служба теперь на это и отказывает.

    Поэтому путь один и тот же для человека и для агента: предложение открывает pull
    request, и слияние есть запись. Это ровно правило владельца: «в базу информация
    попадает в гипотезы только через меня и одобрение PR».

    Одно предложение на сессию, а не на строку: предложение — это мысль вместе с
    опорой, и двадцать отдельных строк ревьюер штампует, а одно дело читает.
    """
    endpoint = settings.get("endpoint") or "http://127.0.0.1:8000/mcp"
    token = settings.get("token") or os.environ.get("LAB_MCP_TOKEN") or ""
    author = settings.get("author") or os.environ.get("USER") or "неизвестный"

    # Работа названа слагом, но вызовы внутри предложения требуют её UUID: они те же
    # самые, какими их позвали бы напрямую, и служба проверяет их по подписи.
    project_id = ((base.get("papers") or {}).get(slug) or {}).get("id") or ""

    вызовы: list[dict] = []
    неполные: list[dict] = []
    заголовок = ""
    мысль = ""
    for record in records:
        if record["kind"] == "hypothesis":
            механизм = (record.get("mechanism") or "").strip()
            условия = (record.get("assumptions") or "").strip()
            if len(механизм) < 12 or len(условия) < 12:
                # Служба откажет всему предложению целиком, поэтому такую гипотезу лучше
                # отложить в файл с точной причиной, чем терять вместе с ней чужие числа.
                неполные.append(record)
                continue
            вызовы.append({"tool": "create_hypothesis", "arguments": {
                "project_id": project_id,
                "statement": record["statement"],
                "falsification_criteria": record["falsification"],
                "mechanism": механизм,
                "assumptions": [условия],
                "title": short_title(record["statement"]),
                "status_reason": f"Помечено в работе, автор {author}",
                "idempotency_key": key(record),
            }})
            заголовок = заголовок or short_title(record["statement"])
            мысль = мысль or record["statement"].strip()
        elif record["kind"] == "decision":
            вызовы.append({"tool": "propose_decision", "arguments": {
                "project_id": project_id,
                "statement": record["statement"],
                "rationale": record["rationale"],
                "idempotency_key": key(record),
            }})
            заголовок = заголовок or short_title(record["statement"])
            мысль = мысль or record["statement"].strip()
        elif record["kind"] == "metric":
            имя, значение = record["name"].strip(), record["value"].strip()
            число = None
            try:
                число = float(значение.replace(",", ".").split()[0])
            except (ValueError, IndexError):
                pass
            адрес = (record.get("check") or "").strip()
            if число is not None and len(адрес) < 4:
                # Число без адреса база не принимает, и это то самое правило, ради которого
                # она заведена: у числа в статье должно быть место, где его можно открыть.
                неполные.append(record)
                continue
            вызовы.append({"tool": "record_evidence", "arguments": {
                "where_to_check": адрес,
                "experiment_id": record["where"].strip(),
                "summary": f"{имя} = {значение}",
                "kind": "metric" if число is not None else "observation",
                "metrics": [{"name": имя, "value": число}] if число is not None else [],
                "observations": [] if число is not None else [f"{имя} = {значение}"],
                "title": имя[:120],
                "idempotency_key": key(record),
            }})
            заголовок = заголовок or f"{имя} в работе {slug}"
            мысль = мысль or (f"Измерение {имя} в прогоне "
                              f"{record['where'].strip() or 'без кода'} даёт {значение}.")
    отложить_в_файл(
        неполные,
        "не хватило обязательного: гипотезе — «| механизм: почему это верно» и "
        "«| условия: модели, масштабы, режим»; числу — «| проверить: <адрес числа>». "
        "Без этого база запись не принимает, и правильно не принимает")
    if not вызовы:
        return "defer"

    подпёрто = опора(records)
    if not подпёрто or not re.search(r"\d", подпёрто):
        note(f"{slug}: помеченное без проверяемой опоры, предложение не открыто. "
             "Добавь ЛАБ-ЧИСЛО с «где: E-код» или числовой критерий опровержения")
        return "defer"

    ответ = call(endpoint, token, "propose", {
        "project": slug,
        "title": заголовок[:120] or f"Помечено в работе {slug}",
        "claim": мысль,
        "support": f"{подпёрто}. Помечено в работе, автор {author}",
        "calls": вызовы,
    })
    адрес = (ответ or {}).get("pull_url") or (ответ or {}).get("url") or ""
    note(f"{slug}: предложение открыто, записей {len(вызовы)}"
         + (f", {адрес}" if адрес else ""))
    return "written"


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
    # Работа сессии: сперва объявленная агентом, потом привязанная к каталогу файлом
    # `.lab-work`, и только потом угаданная по карте путей. Объявление сильнее пути, потому
    # что сессию запускают откуда угодно, а работа у неё одна.
    here = (declared(Path(payload.get("transcript_path") or ""), session)
            or pinned(payload.get("cwd") or "")
            or paper_from_cwd(payload.get("cwd") or ""))
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

    # Вопрос и карта кода в эту базу не кладутся: страницы в git для них нет, и прежний
    # путь их терял молча. Они ложатся в файл рядом, а не висят в очереди навсегда.
    отложить_в_файл([r for r in queue if r["kind"] == "question"],
                    "вопросы: в общей базе для них нет страницы")
    отложить_в_файл([r for r in queue if r["kind"] in ("code_seam", "code_quirk")],
                    "карта кода: эта база её не хранит")

    # Группировка по РАБОТЕ. Одно предложение на работу, а не на строку: предложение это
    # мысль вместе с опорой, и двадцать отдельных ревьюер штампует, а одно дело читает.
    left: list[dict] = []
    по_работам: dict[str, list[dict]] = {}
    for record in queue:
        if record["kind"] not in ("hypothesis", "decision", "metric"):
            continue
        slug = work_of(record, base, record.get("hint"))
        if slug is None:
            note("работа не определилась: запись ЖДЁТ В ОЧЕРЕДИ и уйдёт сама, как только "
                 "сессия пойдёт из каталога работы. Чтобы отправить сейчас, допиши в строку "
                 "«| работа: <слаг>»")
            left.append(record)
            continue
        по_работам.setdefault(slug, []).append(record)

    done, предложений = 0, 0
    for slug, группа in по_работам.items():
        try:
            if предложить(группа, slug, settings, base) == "written":
                done += len(группа)
                предложений += 1
            else:
                left.extend(группа)
        except RuntimeError as error:
            # Отказ службы это не сбой связи, а сообщение человеку: повторять его каждую
            # сессию бессмысленно, и очередь от этого растёт. Такое ложится в файл вместе
            # с причиной, слово в слово, — чтобы было видно, чего не хватило.
            note(f"предложение не открылось ({str(error)[:140]}): работа {slug}")
            отложить_в_файл(группа, f"работа {slug}: база отказала — {str(error)[:300]}")
        except (urllib.error.URLError, TimeoutError, KeyError) as error:
            note(f"предложение не открылось ({str(error)[:140]}): работа {slug}")
            left.extend(группа)
    QUEUE.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n"
                             for item in dedupe(left)), encoding="utf-8")
    if done or left:
        note(f"в предложения ушло записей: {done} ({предложений} шт.), "
             f"осталось в очереди: {len(left)}")
    if done:
        print(f"В базу лаборатории предложено записей: {done} "
              f"({предложений} pull request, слить их — твой ход)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:  # noqa: BLE001 — хук не имеет права ронять сессию
        note(f"необработанное: {error}")
        raise SystemExit(0) from None
