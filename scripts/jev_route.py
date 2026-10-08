#!/usr/bin/env python3
"""Куда это ложится: один вопрос классификатору на конец хода, в тень.

ЗАЧЕМ

Прерывание для сохранения стоит хода модели с перечитыванием всего контекста: измерено, что
на это уходило 8.6 % вывода сессии. Сейчас оно происходит по счётчику, раз в десять
настоящих сообщений, — то есть одинаково часто и когда записывать нечего, и когда надо.
Классификатор отвечает за 0.000025 $, появилось ли в ходе что-то, что стоит записать, и
в какое из мест. Это дёшево настолько, что можно спрашивать каждый ход.

Решение ОБРАТИМОЕ, и только поэтому его можно отдавать классификатору. Сказал «не надо» —
ничего не потеряно: стенограмма целая, счётчик идёт дальше, прерывание всё равно случится.
Статья Jev-Mem (arXiv 2609.23986) отказывается от необратимого «хранить или выбросить» на
входе, и правильно.

ПОКА ЭТО ТЕНЬ. Скрипт только пишет журнал, поведение хука не меняет. Через неделю по журналу
будет видно, совпадает ли он со счётчиком, и только тогда отдавать ему спуск.

УСТРОЙСТВО

Запускается ОТДЕЛЬНЫМ процессом из хука и к ответу хука отношения не имеет: хук не ждёт сеть.
Ключ ищется не в окружении: хуки выполняются без профиля оболочки, поэтому `OPENROUTER_API_KEY`
из `~/.zshrc` там не виден, и ключ берётся из связки ключей macOS.
"""

from __future__ import annotations

import importlib.util
import json
import os
import ssl
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

URL = "https://openrouter.ai/api/v1/systemone"
MODEL = "typesafe/jev-1.13"
LOG = Path("~/.local/state/brainlab/jev-route.jsonl").expanduser()
TIMEOUT = 25
#: Прерываем, когда сошлись три условия, а не одно. Пороги предварительные и будут
#: поправлены по журналу: сырые числа пишутся всегда.
# Откалибровано 03-10-2026 на четырёх ходах, нарочно разных: обсуждение в процессе,
# тот же вопрос с полученным выводом, он же второй раз, и ход, где ничего не произошло.
#   оценка      0.99 ничего · 1.69 обсуждение · 1.99 повтор · 2.40 вывод получен
#   устоялось   0.05 обсуждение · 0.55 вывод получен            (разница в одиннадцать раз)
#   повтор      0.38-0.43 не повтор · 0.89 повтор
# Вероятности сжаты, поэтому пороги ставятся по НАБЛЮДЁННОМУ разбросу, а не по середине шкалы.
# Порог оценки опущен 2.2 -> 1.8 по шести измеренным случаям, а не по одному: при 2.2 правило
# давало 4 верных из 6 и пропускало настоящие записи (переписанный чеклист Гермеса — оценка 1.87
# при устоялось 0.71), при 1.8 даёт 5 из 6. Сама оценка сжата в 1.0..2.6, и разделяет не она, а
# «устоялось»: 0.05 на обсуждении против 0.55-0.71 на готовом. Поэтому главный порог — второй.
SCORE_THRESHOLD = 1.8        # отделяет полученный вывод (2.40) от повтора (1.99)
READY_THRESHOLD = 0.5    # 0.05 против 0.55: обсуждение в процессе не проходит
REPEAT_THRESHOLD = 0.6       # 0.89 ловится, 0.43 нет
# Ось: 0.15 один прогон · 0.20 ещё запускаю · 0.27 разговор · 0.86-0.87 набор закрылся.
# Первое живое срабатывание 03-10-2026 13:26 было ЛОЖНЫМ при 0.62 — ход про устройство хука,
# где прогонов не было вовсе. Поэтому порог поднят выше того значения, а не поставлен между.
AXIS_THRESHOLD = 0.7
MIN_TURNS_BETWEEN = 3       # не чаще, чем раз в три хода, даже если всё созрело
FALLBACK_TURNS = 25      # столько ходов тишины — и прерываем, что бы Jev ни говорил

#: Порог «да» для места. Тоже по наблюдённому разбросу: на ходе, где не произошло ничего,
#: ни одно место не поднялось выше 0.31, а на содержательных они лежат в 0.60..0.80.
#: Семьдесят отсекало бы верное `lab=0.68`.
THRESHOLD = 0.6

#: ВИД записи в работу. Собрано по четырём склонированным работам (dykaf, wsd-muon,
#: lab-agents, lab-knowledge-pipeline), а не по правилу: прогонов 179, серий 51, выкладок 30,
#: рисунков 26. Папки `notes/` нет ни в одной работе, поэтому её здесь нет тоже.
KIND = {
    "series": "A QUESTION was answered by comparing several runs: what was varied, along "
              "which axis, and what the comparison decided. This is the record an agent "
              "writes: one question, the axis, the verdict.",
    "run": "ONE run finished and its settings and numbers are now known: the command, the "
           "commit, the hardware, the metrics. Normally the training code writes this file "
           "itself, so the agent only moves it.",
    "theory": "A derivation or proof was worked out: assumptions, the argument, the result, "
              "and the gaps that remain.",
    "claim": "The claim itself changed: its statement, its falsification criterion, its "
             "status, or the reasoning behind why we believe it.",
    "none": "Nothing in this turn belongs in a work of the lab base.",
}

#: Куда это ложится. Три независимых «да», можно все три сразу: владелец 03-10-2026 —
#: «Можно выбрать все три варианта. Можно только два».
PLACES = {
    "lab": "This is INTERESTING TO THE LABORATORY: in a month somebody will look for it "
           "and be annoyed not to find it. Name who and why, or it is not. It counts "
           "whether or not it is science: a measured result, a derivation, an instruction "
           "others need, an error found in a paper, a dead end that cost time, a rule or "
           "tool that changed, an obligation to an outside party and its deadline, an "
           "agreement with a person. It does NOT count as: a report of what was done this "
           "turn, an intention, a retelling of what already sits in the repository.",
    "mempalace": "Worth keeping verbatim across sessions: the owner's own words, a decision "
                 "and its reason, a trap that cost time, a number that was measured.",
    "obsidian": "The durable state of the OWNER'S OWN project changed: a protocol, results, "
                "a decision, an open question. Something he will reread in his own notes.",
}

#: Внутри лаборатории: научное идёт в работу, остальное — в свой репозиторий. Разделение
#: взято с передней страницы базы: «служебное» это отдельные репозитории БЕЗ утверждений.
#: 08-10-2026 сюда добавлены гранты, обязательства наружу, студенты и публичные тексты.
#: До этого признаком было «научный результат», и владелец показал, чем это кончается:
#: агент сутки вёл инженерную работу и оформлял документы, на каждом ходе честно отвечал
#: «записывать нечего» и не написал в базу ни строки. Признак теперь — «интересно
#: лаборатории», а не «это наука».
INSIDE_LAB = {
    "handbook": "An instruction other people need in order to work: how a tool works, how "
                "a pipeline is wired, a trap anyone would hit.",
    "journal": "The way the laboratory WORKS changed: a new rule, a new place, a cancelled "
               "rule, a tool switched off or replaced.",
    "grants": "A grant: its application, its report, a commitment or deadline under it.",
    "management": "An obligation to an OUTSIDE party: a customer, a stage, an acceptance, "
                  "intellectual property paperwork, a report owed to someone.",
    "education": "Students and courses: who does what, what was handed over, what was "
                 "agreed with a student.",
    "communications": "Public text: an announcement, a post, a talk, anything that will be "
                      "read outside the laboratory.",
}

#: Одно правило на все вопросы сразу, а не оговорка в каждом. Владелец 08-10-2026, увидев
#: `grants` и `management` на ходе, который правил хуки: «Джев как будто не видит то, что мы
#: обсуждаем. Он сам без таких подсказок должен понять, что это не про грант. Это здравый
#: смысл вообще-то.» Он прав: заплатка «False when merely mentioned» в каждом вопросе — это
#: признание, что вопрос задан неверно. Спрашивать надо про предмет хода, один раз и для
#: всего.
SUBJECT_RULE = ("Judge the SUBJECT of this turn and what it actually produced, never the "
                "words it happens to contain. A thing named as an example, as background, "
                "as a reason for something else, or as a past mistake being explained is "
                "not the subject. Answer yes only if removing that thing would leave the "
                "turn without its point. ")

#: Готовый адрес для клонирования. Подсказка, которая называет место, но не говорит, где
#: оно лежит, заставляет агента искать — а он не найдёт и запишет не туда или не запишет
#: вовсе. Владелец 08-10-2026: «пусть он в какой-то момент скажет про это, и агент сам
#: склонирует нужные репо, если их нет».
BASE_URL = os.getenv("BRAINLAB_GIT_URL", "https://68-183-24-188.sslip.io:9445")
#: Хост нужен отдельно: клон узнаётся по нему в `.git/config`. Второй литерал в коде
#: означал бы, что у студента с другим адресом базы клоны не находятся молча.
HOST = BASE_URL.split("//", 1)[-1].split("/", 1)[0].split(":", 1)[0]
REPO_OF = {
    "handbook": "brainlab/handbook",
    "journal": "brainlab/journal",
    "grants": "grants/grants",
    "management": "ops/management",
    "education": "ops/education",
    "communications": "ops/communications",
}

#: ГЛАВНЫЙ ВОПРОС ПРО РАБОТУ. Владелец 03-10-2026: прогон пишет код сам и агента будить не
#: надо; будить надо, когда НАБОР прогонов отвечает на один вопрос и по нему можно сделать
#: вывод — вот тогда агент оформляет серию, рисует и открывает предложение. Поэтому спрашиваем
#: не «важно ли это», а «закрылась ли ось сравнения».
AXIS = {
    "closed": "Has a GROUP of runs just become complete, so that a conclusion ACROSS them "
              "can now be drawn: the comparison axis is covered and what is missing is only "
              "the write-up? False when a single run finished (the training code records that "
              "by itself and needs no agent), when runs are still being launched, or when "
              "there is no group of runs in play at all.",
}

#: ДВА ВОПРОСА, КОТОРЫЕ РЕШАЮТ ГЛАВНУЮ БЕДУ. Владелец 03-10-2026: «если мы что-то важное
#: будем обсуждать, то Джев будет говорить агенту записывай прям каждый раз… у этой информации
#: она может поменяться». Важность и готовность — разные вещи, и спрашивать надо вторую:
#: пока обсуждение идёт, вывод ещё переедет, и запись придётся переписывать. Поэтому
#: прерывание требует НЕ «это важно», а «это важно И уже не изменится И ещё не записано».
READY = {
    # Спрашиваем про СВЕРШИВШЕЕСЯ, а не про вечное. Владелец 08-10-2026: «странно ничего
    # не писать потому, что потом поменяется; на то у нас и оформлены PR и git, чтобы потом
    # если что поправить информацию за собой». Он прав: запись в базе ревизуема, и цена
    # неточной записи — ещё один коммит, а цена ненаписанного — потерянные сутки. За эту
    # сессию 121 ход из 137 был отклонён как «ещё не устоялось», при зрелой оценке в 132 из
    # них: удалена старая база, снята Gitea, легло 923 правки в литературу — и ни строки.
    "settled": "Did something ALREADY HAPPEN in this turn, as a fact of the past? True when "
               "a number was measured, a change was applied, a decision was acted on, a "
               "file was pushed, an error was found: the event is over, even if its meaning "
               "may later be refined. Records here are revisable through git, so possible "
               "future refinement is NOT a reason to answer no. False only while nothing "
               "has happened yet: a plan, a guess, 'let me check', a half-finished attempt "
               "whose outcome is still unknown.",
    "repeat": "Is this the SAME subject as something already written down earlier in this "
              "session (listed under `already_recorded`)? True if recording it again would "
              "produce a second record of one thing.",
}


def clone_state(cwd: str) -> dict:
    """Что известно про работу этой сессии из её клона. Считается, а не угадывается.

    Помощники берутся из хука начала сессии, а не переписываются: он их уже умеет и правится
    вместе с базой. Любая беда — пустое состояние, вопросы всё равно будут заданы.
    """
    try:
        place = Path.home() / ".claude" / "hooks" / "lab-where-am-i.py"
        if not place.is_file():
            return {}
        spec = importlib.util.spec_from_file_location("lab_where_am_i", place)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        slug = module.work_of(cwd or str(Path.cwd()))
        if not slug:
            return {}
        clone = module.clone_of_project(cwd or str(Path.cwd()))
        said = {"work": slug}
        if not (clone and clone.is_dir()):
            return said
        _, claims = module.claims_of(slug, clone)
        said["claims"] = claims
        said["series_written"] = len(list(clone.glob("claims/*/series/S-*.md")))
        said["runs_written"] = len(list(clone.glob("claims/*/runs/E-*.md")))
        # Прогоны, приехавшие в ветку сами и ещё не перенесённые в claims/
        arrived = subprocess.run(
            ["git", "for-each-ref", "--format=%(refname)", "refs/remotes"],
            cwd=clone, capture_output=True, text=True, timeout=10).stdout.split()
        not_described = 0
        for link in arrived:
            files = subprocess.run(["git", "ls-tree", "-r", "--name-only", link],
                                   cwd=clone, capture_output=True, text=True,
                                   timeout=10).stdout.splitlines()
            not_described = max(not_described, sum(1 for f in files if f.startswith("lab-runs/")))
        said["runs_arrived_not_described"] = max(0, not_described - said["runs_written"])
        open = module.open_proposals(slug)
        said["open_proposal"] = bool(open)
        return said
    except Exception:          # noqa: BLE001 — состояние это подспорье, а не условие работы
        return {}


#: Ключ в `settings.json` — это секрет открытым текстом в настройках, чего `security.md`
#: прямо не разрешает. Поэтому порядок такой: переменная окружения, потом связка ключей
#: macOS, потом файл с правами 600. Файл нужен ради тех, у кого связки нет: на Linux и на
#: do-vpn ключ и так лежит в `~/.config/brainlab/openrouter-key`.
KEY_FILE = Path("~/.config/brainlab/openrouter-key").expanduser()


def key() -> str:
    from_env = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if from_env:
        return from_env
    try:                      # хук идёт без профиля оболочки, поэтому связка ключей
        found = subprocess.run(
            ["security", "find-generic-password", "-s", "brain-call.openrouter",
             "-a", "asr", "-w"],
            capture_output=True, text=True, timeout=10, check=True).stdout.strip()
        if found:
            return found
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        return KEY_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


#: Потолок Jev — 32 тысячи токенов на состояние с вопросом. Кириллица дорогая: токен на один-два
#: знака, поэтому прежние 50 000 знаков давали 400 Bad Request на длинном ходе. Настоящие ходы
#: этой сессии: медиана 2026 знаков, максимум 8429 — так что 12 000 не теряет ничего живого.
#: Берётся голова И хвост: вывод обычно в конце, и обрезать его было бы хуже всего.
CHAR_LIMIT = 12000


def trim(text: str) -> str:
    if len(text) <= CHAR_LIMIT:
        return text
    half = CHAR_LIMIT // 2
    lowered = len(text) - CHAR_LIMIT
    return f"{text[:half]}\n[… опущено {lowered} знаков …]\n{text[-half:]}"


def ask(text: str, api_key: str, recorded: list[str],
             clone: dict | None = None) -> dict:
    """Один запрос, все вопросы сразу: так в двенадцать раз дешевле, чем по вызову на вопрос.

    Тип называется `noul`, не `bool`: API отвечает 400 «Expected 'noul' | 'choice' | 'score'».
    И отдаёт он не да/нет, а вероятность — порог ставим мы.
    """
    questions: dict[str, dict] = {}
    for group in (PLACES, INSIDE_LAB, READY, AXIS):
        for name, description in group.items():
            questions[name] = {"type": "noul",
                               "instructions": SUBJECT_RULE + description,
                               "criteria": {"true": "yes", "false": "no"}}
    questions["вид"] = {"type": "choice", "instructions":
        "If this turn produced something that belongs in a WORK of the lab base (not the "
        "handbook, not the journal), which kind of record is it? Pick `none` otherwise.",
        "criteria": KIND}
    questions["worth"] = {
        "type": "score",
        "instructions": "How much does this turn deserve interrupting the agent to write "
                        "something down? 0 if nothing happened worth recording anywhere.",
        "criteria": ["nothing to record", "minor, can wait",
                     "worth recording", "must not be lost"],
    }
    state = {"turn": trim(text)}
    if recorded:
        state["already_recorded"] = recorded[-12:]
    if clone:
        state["work_state"] = clone
    body = json.dumps({"model": MODEL, "state": state,
                       "questions": questions}).encode()
    request = urllib.request.Request(URL, data=body, headers={
        "Authorization": f"Bearer {api_key}", "Content-Type": "application/json",
        "User-Agent": "brainlab-jev-route/1.0"})
    ctx = ssl.create_default_context()
    start = time.monotonic()
    with urllib.request.urlopen(request, timeout=TIMEOUT, context=ctx) as answer:
        data = json.load(answer)
    data["_секунд"] = round(time.monotonic() - start, 2)
    return data


def write(line: dict) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")



def summary() -> None:
    """Что классификатор говорил и совпадало ли это со счётчиком."""
    if not LOG.exists():
        print("журнала пока нет")
        return
    lines = []
    for raw in LOG.read_text(encoding="utf-8").splitlines():
        try:
            lines.append(json.loads(raw))
        except ValueError:
            continue
    answered = [item for item in lines if "беда" not in item]
    troubles = [item for item in lines if "беда" in item]
    print(f"ходов в журнале: {len(lines)}, с ответом {len(answered)}, с бедой {len(troubles)}")
    if troubles:
        from collections import Counter
        for t, n in Counter(item["беда"][:60] for item in troubles).most_common(5):
            print(f"   {n:4d}  {t}")
    if not answered:
        return
    cost = sum(item.get("цена") or 0 for item in answered)
    sec = [item.get("секунд") or 0 for item in answered]
    print(f"цена всего: {cost:.4f} $   среднее время {sum(sec)/len(sec):.1f} с")

    fired = [item for item in answered if item.get("счётчик_сработал")]
    silent = [item for item in answered if not item.get("счётчик_сработал")]
    def mean(batch, field="оценка"):
        values = [item.get(field) or 0 for item in batch]
        return sum(values) / len(values) if values else 0
    print(f"\nсчётчик прерывал  : {len(fired):4d} ходов, средняя оценка {mean(fired):.2f}")
    print(f"счётчик молчал    : {len(silent):4d} ходов, средняя оценка {mean(silent):.2f}")
    print("Если во второй строке оценка не ниже, чем в первой, счётчик прерывает не по делу.")

    high = sorted(silent, key=lambda item: -(item.get("оценка") or 0))[:5]
    if high:
        print("\nсчётчик молчал, а оценка высокая — то, что терялось:")
        for item in high:
            print(f"   {item['когда'][5:16]}  оценка {item.get('оценка'):.2f}  "
                  f"места: {', '.join(item.get('выбраны') or []) or '—'}")

    from collections import Counter
    counter = Counter()
    for item in answered:
        for m in item.get("выбраны") or []:
            counter[m] += 1
    if counter:
        print(f"\nкуда предлагал класть (порог {THRESHOLD}):")
        for m, n in counter.most_common():
            print(f"   {n:4d}  {m}")


def decision(answer: dict, turns: int, past: int,
             clone: dict | None = None, cwd: str = "") -> dict:
    """Прерывать или нет. Решают ТРИ условия, и это главное в замысле.

    Важность и готовность — разные вещи. Пока тема обсуждается, вывод ещё переедет, и запись
    придётся переписывать; поэтому одного «это важно» мало. Третье условие — не записано ли
    это уже: иначе на длинном разговоре про одно дело выйдет десять записей об одном.

    Снизу подпирает страховка: если Jev молчит слишком долго, прерываем всё равно, чтобы
    сессия не кончилась без единой записи.
    """
    reply = answer.get("answers") or {}

    def verdict(name: str) -> float:
        return float((reply.get(name) or {}).get("noul") or 0.0)

    score = float((reply.get("worth") or {}).get("score") or 0.0)
    settled, repeat, axis = verdict("settled"), verdict("repeat"), verdict("closed")
    since_last = turns - past

    places = [one_item for one_item in PLACES if verdict(one_item) >= THRESHOLD]
    # Один кончившийся прогон агента не касается: его описывает код и сам отправляет в ветку.
    # Поэтому «в лабораторию» снимается, когда вид — прогон, а ось ещё не закрылась. Владелец
    # 03-10-2026: «это, по идее, должно делать автоматически… пока не надо».
    # `lab` и подместа — не независимые вопросы: «способ работы лаборатории изменился» на
    # 0.89 САМО ПО СЕБЕ отвечает, что лаборатории это интересно. Поэтому подместо проходит
    # либо вместе с базой, либо самостоятельно — но тогда по более высокой планке.
    #
    # Планка не угадана, а измерена на 53 решениях 08-10-2026. При `lab` ниже порога
    # `grants` поднимался не выше 0.66, а `journal` на ходах, которые владелец и требовал
    # записать, давал 0.70–0.89. Отсюда 0.7: ниже возвращается ложный грант, о котором он
    # сказал «нахуя тут про гранты, в чём смысл?», выше теряется журнал, о котором он
    # сказал «у нас тут столько всего произошло, и это надо вписывать всё равно».
    # Прежде подместа считались совсем независимо и грант при 0.65 попадал в подсказку
    # при невыбранной базе; потом зависели целиком и журнал при 0.89 терялся.
    ALONE = 0.7
    inside = [one_item for one_item in INSIDE_LAB
              if verdict(one_item) >= (THRESHOLD if "lab" in places else ALONE)]
    if inside and "lab" not in places:
        places.append("lab")
    kind_draft = ((reply.get("вид") or {}).get("choice")) or "none"
    if kind_draft == "run" and verdict("closed") < AXIS_THRESHOLD and "lab" in places:
        places.remove("lab")

    kind = kind_draft

    # Закрывшаяся ось — самостоятельный повод, даже при средней оценке: это ровно тот момент,
    # когда агента и надо будить, чтобы он оформил серию. В обратную сторону она не работает:
    # «ось не закрылась» не запрещает записать то, что созрело само по себе.
    ripe = (score >= SCORE_THRESHOLD and settled >= READY_THRESHOLD
               and repeat < REPEAT_THRESHOLD and places)
    # Ось имеет смысл ТОЛЬКО когда вид — серия: закрывшийся набор прогонов и есть серия.
    # На ложном срабатывании 03-10-2026 ось дала 0.62 при виде `none`, то есть два вопроса
    # противоречили друг другу. Служба об этом предупреждает прямо: разные вопросы не обязаны
    # согласовываться, и согласовывать их — наша работа, а не её.
    # Серия принадлежит работе. Если сессия ни к какой работе не привязана (нет `.lab-work`),
    # никакого набора прогонов тут быть не может, и правило про ось выключается целиком.
    # На прогоне по 120 живым ходам без работы ось дала 0.71 на разговоре про настройку Pi —
    # это и есть то ложное срабатывание, которое снимается здесь.
    with_work = bool((clone or {}).get("work"))
    axis_closed = (axis >= AXIS_THRESHOLD and repeat < REPEAT_THRESHOLD
                     and kind_draft == "series" and with_work)
    # Счётчик держит паузу, чтобы хук не долбил об одно и то же. Но «одно и то же» Jev
    # меряет сам, вопросом «повтор», и 08-10-2026 замер показал, что счётчик к содержанию
    # отношения не имеет: у 39 ходов, которые он заглушил, повтор лежал в 0.13..0.56, а у
    # 28 прошедших — в 0.15..0.51. Один и тот же диапазон, то есть прошло то, что совпало
    # по чётности хода. Ровно за это из главного решения уже выкинули прежний счётчик.
    # Владелец: «почему это не записано в журнал? почему Джев не сказал тебе остановиться?»
    # — а Джев говорил «созрело» дважды, 2.79 и 2.51, и счётчик его заглушил.
    #
    # Поэтому пауза отменяется, когда ход заведомо не повтор и в нём заведомо есть вывод.
    # Оба порога уже откалиброваны и здесь не выдуманы: REPEAT_THRESHOLD ловит 0.89 и
    # пропускает 0.43, а 2.4 — наблюдённый уровень «вывод получен» против 1.99 у повтора.
    # Замер на 394 решениях: прерываний станет 57 вместо 28, то есть 14 % ходов вместо 7 %.
    # Один ход паузы остаётся всегда: дважды на одном ходе прерывать нечего.
    fresh_result = repeat < REPEAT_THRESHOLD and score >= 2.4
    early = since_last < (1 if fresh_result else MIN_TURNS_BETWEEN)
    fallback = since_last >= FALLBACK_TURNS

    # Порядок важен: страховка проверяется ПОСЛЕДНЕЙ. Когда она стояла первой, она перебивала
    # «созрело» — прерывание происходило верно, но причина и подсказка приходили неправильные
    # («ничего зрелого не увидел» на ходе, где всё созрело), и агент получал не тот совет.
    if axis_closed and not early:
        interrupt, why = True, "набор прогонов закрылся — пора оформлять серию"
    elif ripe and not early:
        interrupt, why = True, "созрело"
    elif fallback:
        interrupt, why = True, f"страховка: {since_last} ходов без записи"
    elif ripe and early:
        interrupt, why = False, f"созрело, но прошло только {since_last} ходов"
    elif score < SCORE_THRESHOLD:
        interrupt, why = False, f"нечего записывать (оценка {score:.2f})"
    elif settled < READY_THRESHOLD:
        interrupt, why = False, f"ещё не устоялось ({settled:.2f}), переедет"
    elif repeat >= REPEAT_THRESHOLD:
        interrupt, why = False, f"про это уже записано ({repeat:.2f})"
    else:
        interrupt, why = False, "ни одно место не выбрано"

    return {"прерывать": interrupt, "почему": why, "оценка": round(score, 2),
            "устоялось": round(settled, 2), "повтор": round(repeat, 2),
            "ось": round(axis, 2),
            "места": places, "внутри_лабы": inside, "вид": kind,
            "клоны": clones_here(cwd), "с_прошлого": since_last}


def clones_here(cwd: str) -> list[str]:
    """Клоны репозиториев базы рядом с работой: что склонировано, туда и пишем.

    Тот же признак, что у хука начала сессии: клон и есть решение о месте записи, и
    отдельного файла с решением не нужно. Смотрим саму папку и один уровень внутрь —
    глубже лежат чужие зависимости — кроме `lab-base`, куда клонировать и велено.
    """
    here = Path(cwd or ".").expanduser().resolve()
    if not here.is_dir():
        return []
    found: list[str] = []
    # `lab-base` — это документированное место клона («клон работы лежит в
    # `<папка проекта>/lab-base`»), поэтому внутрь него надо заглянуть отдельно: иначе
    # клон, сделанный по инструкции, лежит на втором уровне и не виден. 08-10-2026
    # проверено: склонировал `brainlab/handbook` и `brainlab/journal` ровно туда, куда
    # велено, и оба детектора вернули пусто — хук спрашивал бы адрес вечно.
    #
    # Коробка ищется и вверх тоже: каталог сессии гуляет, и из `lab-base/handbook` сосед
    # `lab-base/journal` иначе не виден — подсказка говорила «клона рядом нет», хотя он
    # лежал уровнем выше. Адрес записи не должен зависеть от того, куда агент зашёл.
    boxes = [here / "lab-base"]
    boxes += [parent for parent in (here, *here.parents) if parent.name == "lab-base"]
    try:
        nested = [child for child in here.iterdir() if child.is_dir()]
        for box in boxes:
            if box.is_dir():
                nested += [child for child in box.iterdir() if child.is_dir()]
    except OSError:
        return []
    folders = [here, *nested]
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
            if line.startswith("url = ") and HOST in line:
                path = line.split(HOST, 1)[1].lstrip(":0123456789/")
                path = path[:-4] if path.endswith(".git") else path
                if path and path not in found:
                    found.append(path)
    return found


def hint(verdict: dict) -> str:
    """Строка для агента: куда это ложится, чтобы он не выводил это заново.

    При срабатывании страховки места не называются: страховка прерывает именно потому, что
    классификатор ничего зрелого не увидел, и подсказывать тут нечего — надо наоборот
    попросить проверить, не потерялось ли что-то за эти ходы.
    """
    if verdict["почему"].startswith("страховка"):
        return (f"Классификатор за последние {verdict['с_прошлого']} ходов ничего зрелого не "
                "увидел, и это прерывание — страховка. Посмотри сам, не осталось ли "
                "незаписанного; если нет, так и скажи и иди дальше.")
    if verdict["почему"].startswith("набор прогонов"):
        return ("Классификатор считает, что набор прогонов закрылся и по нему пора делать "
                "вывод: оформить серию в `claims/<H>/series/S-….md` по правилам "
                "`series-answers-one-question` и `series-needs-verdict`, дописать абзац в "
                "страницу утверждения (`claim-gets-a-paragraph`) и открыть одно предложение "
                "на это утверждение (`one-proposal-per-claim`). Правила с именами и с тем, "
                "чем каждое проверяется, — в своде `~/.claude/rules/lab-canon.md`; "
                "пересказывать их здесь нельзя, поэтому они только названы. "
                "Это подсказка, а не приговор: проверь сам.")
    parts = []
    if "lab" in verdict["места"]:
        chunks = []
        if verdict["вид"] != "none":
            names = {"series": "серией", "run": "прогоном",
                     "theory": "выкладкой", "claim": "правкой утверждения"}
            chunks.append(f"в работу {names.get(verdict['вид'], verdict['вид'])}")
        # Все места, а не только научные. До 08-10-2026 здесь стояли два: справочник и
        # журнал, и агент с грантовой или договорной работой не слышал про свой адрес
        # вовсе — он честно отвечал «записывать нечего» и молчал сутками.
        names = {"handbook": "в справочник", "journal": "в журнал лаборатории",
                 "grants": "в гранты", "management": "в обязательства наружу",
                 "education": "в студентов и курсы", "communications": "в публичные тексты"}
        for one in REPO_OF:
            if one in verdict["внутри_лабы"]:
                chunks.append(f"{names[one]} (`{REPO_OF[one]}`)")
        parts.append("в базу лаборатории" + (f" ({', '.join(chunks)})" if chunks else ""))
    if "mempalace" in verdict["места"]:
        parts.append("в MemPalace")
    if "obsidian" in verdict["места"]:
        parts.append("в Obsidian")
    if not parts:
        return ""
    tail = ""
    if "lab" in verdict["места"]:
        need = [REPO_OF[one] for one in REPO_OF if one in verdict["внутри_лабы"]]
        missing = [repo for repo in need if repo not in (verdict.get("клоны") or [])]
        if missing:
            cmds = "  ".join(f"`git clone {BASE_URL}/{repo}.git`" for repo in missing)
            tail = (f" Клона рядом нет — заведи его здесь же: {cmds}. Дальше клон и будет "
                    "адресом, и спрашивать больше не придётся.")
        else:
            tail = " Клон уже рядом, пиши в него предложением."
    return ("Классификатор считает, что из этого хода надо записать "
            + ", ".join(parts)
            + f". Оценка {verdict['оценка']:.1f} из 3, устоялось {verdict['устоялось']:.2f}."
            + tail
            + " Это подсказка, а не приговор: проверь сам.")


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] in ("--сводка", "--summary"):
        summary()
        return
    if len(sys.argv) < 2:
        return
    path = Path(sys.argv[-1])
    # Удаляется ТОЛЬКО свой временный файл, и это не придирка. Прежде здесь стояло
    # `finally: path.unlink()` на любой аргумент, и 04-10-2026 этим был удалён транскрипт
    # живой сессии: его передали сюда руками, проверяя классификатор. Файл восстановить
    # было нечем — локальных снимков нет, Time Machine отключена. Признак своего файла:
    # имя, которое пишет хук (`tempfile.mkstemp(prefix="jev-route-")`), и каталог temp.
    own = path.name.startswith("jev-route-") and path.suffix == ".json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print(json.dumps({"прерывать": None, "беда": str(error)}, ensure_ascii=False))
        return
    finally:
        if own:
            try:
                path.unlink()
            except OSError:
                pass

    record = {"когда": time.strftime("%Y-%m-%dT%H:%M:%S"),
              "сессия": payload.get("сессия", "")[:8],
              "ходов": payload.get("ходов"),
              "счётчик_сработал": payload.get("счётчик_сработал"),
              "знаков": len(payload.get("текст") or "")}

    def give_up(trouble: str) -> None:
        record["беда"] = trouble
        write(record)
        print(json.dumps({"прерывать": None, "беда": trouble}, ensure_ascii=False))

    text = (payload.get("текст") or "").strip()
    if not text:
        give_up("пустой ход")
        return
    k = key()
    if not k:
        give_up("нет ключа OpenRouter")
        return
    try:
        clone = clone_state(payload.get("каталог") or "")
        answer = ask(text, k, payload.get("записанное") or [], clone)
    except Exception as error:          # сеть, ключ, разбор — любая беда в журнал
        give_up(f"{type(error).__name__}: {error}"[:200])
        return

    verdict = decision(answer, int(payload.get("ходов") or 0),
                  int(payload.get("прошлое") or 0), clone,
                  str(payload.get("каталог") or ""))
    reply = answer.get("answers") or {}
    record.update({
        "работа": (clone or {}).get("work"),
        "не_описано_прогонов": (clone or {}).get("runs_arrived_not_described"),
        "ось": verdict["ось"],
        "вид": verdict["вид"],
        "места": {one_item: round(float((reply.get(one_item) or {}).get("noul") or 0), 2)
                  for one_item in list(PLACES) + list(INSIDE_LAB)},
        "выбраны": verdict["места"] + verdict["внутри_лабы"],
        "оценка": verdict["оценка"], "устоялось": verdict["устоялось"], "повтор": verdict["повтор"],
        "прерывать": verdict["прерывать"], "почему": verdict["почему"],
        "секунд": answer.get("_секунд"),
        "токенов": (answer.get("usage") or {}).get("input_tokens"),
        "цена": (answer.get("usage") or {}).get("cost"),
    })
    write(record)
    verdict["подсказка"] = hint(verdict) if verdict["прерывать"] else ""
    print(json.dumps(verdict, ensure_ascii=False))


if __name__ == "__main__":
    main()
