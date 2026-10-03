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
ПОРОГ_ОЦЕНКИ = 1.8        # отделяет полученный вывод (2.40) от повтора (1.99)
ПОРОГ_ГОТОВНОСТИ = 0.5    # 0.05 против 0.55: обсуждение в процессе не проходит
ПОРОГ_ПОВТОРА = 0.6       # 0.89 ловится, 0.43 нет
# Ось: 0.15 один прогон · 0.20 ещё запускаю · 0.27 разговор · 0.86-0.87 набор закрылся.
# Первое живое срабатывание 03-10-2026 13:26 было ЛОЖНЫМ при 0.62 — ход про устройство хука,
# где прогонов не было вовсе. Поэтому порог поднят выше того значения, а не поставлен между.
ПОРОГ_ОСИ = 0.7
МИН_ХОДОВ_МЕЖДУ = 3       # не чаще, чем раз в три хода, даже если всё созрело
СТРАХОВКА_ХОДОВ = 25      # столько ходов тишины — и прерываем, что бы Jev ни говорил

#: Порог «да» для места. Тоже по наблюдённому разбросу: на ходе, где не произошло ничего,
#: ни одно место не поднялось выше 0.31, а на содержательных они лежат в 0.60..0.80.
#: Семьдесят отсекало бы верное `lab=0.68`.
ПОРОГ = 0.6

#: ВИД записи в работу. Собрано по четырём склонированным работам (dykaf, wsd-muon,
#: lab-agents, lab-knowledge-pipeline), а не по правилу: прогонов 179, серий 51, выкладок 30,
#: рисунков 26. Папки `notes/` нет ни в одной работе, поэтому её здесь нет тоже.
ВИД = {
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
МЕСТА = {
    "lab": "This belongs in the shared knowledge of the laboratory, which other members "
           "read: a measured result under a claim, a derivation, or an instruction other "
           "people need in order to work.",
    "mempalace": "Worth keeping verbatim across sessions: the owner's own words, a decision "
                 "and its reason, a trap that cost time, a number that was measured.",
    "obsidian": "The durable state of the OWNER'S OWN project changed: a protocol, results, "
                "a decision, an open question. Something he will reread in his own notes.",
}

#: Внутри лаборатории: научное идёт в работу, служебное — в справочник или журнал. Разделение
#: взято с передней страницы базы: «служебное» это отдельные репозитории БЕЗ утверждений.
ВНУТРИ_ЛАБЫ = {
    "handbook": "Other people need this as instruction: how a tool works, how a pipeline is "
                "wired, a trap anyone would hit. Not a scientific result.",
    "journal": "The way the laboratory WORKS changed: a new rule, a new place, a cancelled "
               "rule, a tool switched off or replaced.",
}

#: ГЛАВНЫЙ ВОПРОС ПРО РАБОТУ. Владелец 03-10-2026: прогон пишет код сам и агента будить не
#: надо; будить надо, когда НАБОР прогонов отвечает на один вопрос и по нему можно сделать
#: вывод — вот тогда агент оформляет серию, рисует и открывает предложение. Поэтому спрашиваем
#: не «важно ли это», а «закрылась ли ось сравнения».
ОСЬ = {
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
ГОТОВНОСТЬ = {
    "settled": "Has this SETTLED? True when the thing is finished and will not be rewritten: "
               "a number was measured and exists, a decision was made and acted on, a proof "
               "closed. False while the work is still moving: a plan, a guess, 'let me "
               "check', an intermediate result that the next step may overturn, or a "
               "conclusion that already replaced an earlier one in this same conversation.",
    "repeat": "Is this the SAME subject as something already written down earlier in this "
              "session (listed under `already_recorded`)? True if recording it again would "
              "produce a second record of one thing.",
}


def состояние_клона(cwd: str) -> dict:
    """Что известно про работу этой сессии из её клона. Считается, а не угадывается.

    Помощники берутся из хука начала сессии, а не переписываются: он их уже умеет и правится
    вместе с базой. Любая беда — пустое состояние, вопросы всё равно будут заданы.
    """
    try:
        место = Path.home() / ".claude" / "hooks" / "lab-where-am-i.py"
        if not место.is_file():
            return {}
        спец = importlib.util.spec_from_file_location("lab_where_am_i", место)
        модуль = importlib.util.module_from_spec(спец)
        спец.loader.exec_module(модуль)
        слаг = модуль.work_of(cwd or str(Path.cwd()))
        if not слаг:
            return {}
        клон = модуль.clone_of_project(cwd or str(Path.cwd()))
        если = {"work": слаг}
        if not (клон and клон.is_dir()):
            return если
        _, утв = модуль.claims_of(слаг, клон)
        если["claims"] = утв
        если["series_written"] = len(list(клон.glob("claims/*/series/S-*.md")))
        если["runs_written"] = len(list(клон.glob("claims/*/runs/E-*.md")))
        # Прогоны, приехавшие в ветку сами и ещё не перенесённые в claims/
        приехало = subprocess.run(
            ["git", "for-each-ref", "--format=%(refname)", "refs/remotes"],
            cwd=клон, capture_output=True, text=True, timeout=10).stdout.split()
        не_описано = 0
        for ссылка in приехало:
            файлы = subprocess.run(["git", "ls-tree", "-r", "--name-only", ссылка],
                                   cwd=клон, capture_output=True, text=True,
                                   timeout=10).stdout.splitlines()
            не_описано = max(не_описано, sum(1 for ф in файлы if ф.startswith("lab-runs/")))
        если["runs_arrived_not_described"] = max(0, не_описано - если["runs_written"])
        открытые = модуль.open_proposals(слаг)
        если["open_proposal"] = bool(открытые)
        return если
    except Exception:          # noqa: BLE001 — состояние это подспорье, а не условие работы
        return {}


def ключ() -> str:
    из_среды = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if из_среды:
        return из_среды
    try:                      # хук идёт без профиля оболочки, поэтому связка ключей
        return subprocess.run(
            ["security", "find-generic-password", "-s", "brain-call.openrouter",
             "-a", "asr", "-w"],
            capture_output=True, text=True, timeout=10, check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


#: Потолок Jev — 32 тысячи токенов на состояние с вопросом. Кириллица дорогая: токен на один-два
#: знака, поэтому прежние 50 000 знаков давали 400 Bad Request на длинном ходе. Настоящие ходы
#: этой сессии: медиана 2026 знаков, максимум 8429 — так что 12 000 не теряет ничего живого.
#: Берётся голова И хвост: вывод обычно в конце, и обрезать его было бы хуже всего.
ПРЕДЕЛ_ЗНАКОВ = 12000


def урезать(текст: str) -> str:
    if len(текст) <= ПРЕДЕЛ_ЗНАКОВ:
        return текст
    половина = ПРЕДЕЛ_ЗНАКОВ // 2
    опущено = len(текст) - ПРЕДЕЛ_ЗНАКОВ
    return f"{текст[:половина]}\n[… опущено {опущено} знаков …]\n{текст[-половина:]}"


def спросить(текст: str, ключ_api: str, записанное: list[str],
             клон: dict | None = None) -> dict:
    """Один запрос, все вопросы сразу: так в двенадцать раз дешевле, чем по вызову на вопрос.

    Тип называется `noul`, не `bool`: API отвечает 400 «Expected 'noul' | 'choice' | 'score'».
    И отдаёт он не да/нет, а вероятность — порог ставим мы.
    """
    вопросы: dict[str, dict] = {}
    for группа in (МЕСТА, ВНУТРИ_ЛАБЫ, ГОТОВНОСТЬ, ОСЬ):
        for имя, описание in группа.items():
            вопросы[имя] = {"type": "noul", "instructions": описание,
                            "criteria": {"true": "yes", "false": "no"}}
    вопросы["вид"] = {"type": "choice", "instructions":
        "If this turn produced something that belongs in a WORK of the lab base (not the "
        "handbook, not the journal), which kind of record is it? Pick `none` otherwise.",
        "criteria": ВИД}
    вопросы["worth"] = {
        "type": "score",
        "instructions": "How much does this turn deserve interrupting the agent to write "
                        "something down? 0 if nothing happened worth recording anywhere.",
        "criteria": ["nothing to record", "minor, can wait",
                     "worth recording", "must not be lost"],
    }
    состояние = {"turn": урезать(текст)}
    if записанное:
        состояние["already_recorded"] = записанное[-12:]
    if клон:
        состояние["work_state"] = клон
    тело = json.dumps({"model": MODEL, "state": состояние,
                       "questions": вопросы}).encode()
    запрос = urllib.request.Request(URL, data=тело, headers={
        "Authorization": f"Bearer {ключ_api}", "Content-Type": "application/json",
        "User-Agent": "brainlab-jev-route/1.0"})
    ctx = ssl.create_default_context()
    начало = time.monotonic()
    with urllib.request.urlopen(запрос, timeout=TIMEOUT, context=ctx) as ответ:
        данные = json.load(ответ)
    данные["_секунд"] = round(time.monotonic() - начало, 2)
    return данные


def записать(строка: dict) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as ф:
        ф.write(json.dumps(строка, ensure_ascii=False) + "\n")



def сводка() -> None:
    """Что классификатор говорил и совпадало ли это со счётчиком."""
    if not LOG.exists():
        print("журнала пока нет")
        return
    строки = []
    for сырая in LOG.read_text(encoding="utf-8").splitlines():
        try:
            строки.append(json.loads(сырая))
        except ValueError:
            continue
    удачных = [с for с in строки if "беда" not in с]
    беды = [с for с in строки if "беда" in с]
    print(f"ходов в журнале: {len(строки)}, с ответом {len(удачных)}, с бедой {len(беды)}")
    if беды:
        from collections import Counter
        for т, n in Counter(с["беда"][:60] for с in беды).most_common(5):
            print(f"   {n:4d}  {т}")
    if not удачных:
        return
    цена = sum(с.get("цена") or 0 for с in удачных)
    сек = [с.get("секунд") or 0 for с in удачных]
    print(f"цена всего: {цена:.4f} $   среднее время {sum(сек)/len(сек):.1f} с")

    сработал = [с for с in удачных if с.get("счётчик_сработал")]
    молчал = [с for с in удачных if not с.get("счётчик_сработал")]
    def ср(набор, поле="оценка"):
        значения = [с.get(поле) or 0 for с in набор]
        return sum(значения) / len(значения) if значения else 0
    print(f"\nсчётчик прерывал  : {len(сработал):4d} ходов, средняя оценка {ср(сработал):.2f}")
    print(f"счётчик молчал    : {len(молчал):4d} ходов, средняя оценка {ср(молчал):.2f}")
    print("Если во второй строке оценка не ниже, чем в первой, счётчик прерывает не по делу.")

    высокие = sorted(молчал, key=lambda с: -(с.get("оценка") or 0))[:5]
    if высокие:
        print("\nсчётчик молчал, а оценка высокая — то, что терялось:")
        for с in высокие:
            print(f"   {с['когда'][5:16]}  оценка {с.get('оценка'):.2f}  "
                  f"места: {', '.join(с.get('выбраны') or []) or '—'}")

    from collections import Counter
    счёт = Counter()
    for с in удачных:
        for м in с.get("выбраны") or []:
            счёт[м] += 1
    if счёт:
        print(f"\nкуда предлагал класть (порог {ПОРОГ}):")
        for м, n in счёт.most_common():
            print(f"   {n:4d}  {м}")


def решение(ответ: dict, ходов: int, прошлое: int,
             клон: dict | None = None) -> dict:
    """Прерывать или нет. Решают ТРИ условия, и это главное в замысле.

    Важность и готовность — разные вещи. Пока тема обсуждается, вывод ещё переедет, и запись
    придётся переписывать; поэтому одного «это важно» мало. Третье условие — не записано ли
    это уже: иначе на длинном разговоре про одно дело выйдет десять записей об одном.

    Снизу подпирает страховка: если Jev молчит слишком долго, прерываем всё равно, чтобы
    сессия не кончилась без единой записи.
    """
    отв = ответ.get("answers") or {}

    def вер(имя: str) -> float:
        return float((отв.get(имя) or {}).get("noul") or 0.0)

    оценка = float((отв.get("worth") or {}).get("score") or 0.0)
    устоялось, повтор, ось = вер("settled"), вер("repeat"), вер("closed")
    с_прошлого = ходов - прошлое

    места = [и for и in МЕСТА if вер(и) >= ПОРОГ]
    # Один кончившийся прогон агента не касается: его описывает код и сам отправляет в ветку.
    # Поэтому «в лабораторию» снимается, когда вид — прогон, а ось ещё не закрылась. Владелец
    # 03-10-2026: «это, по идее, должно делать автоматически… пока не надо».
    вид_предв = ((отв.get("вид") or {}).get("choice")) or "none"
    if вид_предв == "run" and вер("closed") < ПОРОГ_ОСИ and "lab" in места:
        места.remove("lab")
    внутри = [и for и in ВНУТРИ_ЛАБЫ if вер(и) >= ПОРОГ]
    вид = вид_предв

    # Закрывшаяся ось — самостоятельный повод, даже при средней оценке: это ровно тот момент,
    # когда агента и надо будить, чтобы он оформил серию. В обратную сторону она не работает:
    # «ось не закрылась» не запрещает записать то, что созрело само по себе.
    созрело = (оценка >= ПОРОГ_ОЦЕНКИ and устоялось >= ПОРОГ_ГОТОВНОСТИ
               and повтор < ПОРОГ_ПОВТОРА and места)
    # Ось имеет смысл ТОЛЬКО когда вид — серия: закрывшийся набор прогонов и есть серия.
    # На ложном срабатывании 03-10-2026 ось дала 0.62 при виде `none`, то есть два вопроса
    # противоречили друг другу. Служба об этом предупреждает прямо: разные вопросы не обязаны
    # согласовываться, и согласовывать их — наша работа, а не её.
    # Серия принадлежит работе. Если сессия ни к какой работе не привязана (нет `.lab-work`),
    # никакого набора прогонов тут быть не может, и правило про ось выключается целиком.
    # На прогоне по 120 живым ходам без работы ось дала 0.71 на разговоре про настройку Pi —
    # это и есть то ложное срабатывание, которое снимается здесь.
    при_работе = bool((клон or {}).get("work"))
    ось_закрылась = (ось >= ПОРОГ_ОСИ and повтор < ПОРОГ_ПОВТОРА
                     and вид_предв == "series" and при_работе)
    рано = с_прошлого < МИН_ХОДОВ_МЕЖДУ
    страховка = с_прошлого >= СТРАХОВКА_ХОДОВ

    # Порядок важен: страховка проверяется ПОСЛЕДНЕЙ. Когда она стояла первой, она перебивала
    # «созрело» — прерывание происходило верно, но причина и подсказка приходили неправильные
    # («ничего зрелого не увидел» на ходе, где всё созрело), и агент получал не тот совет.
    if ось_закрылась and not рано:
        прерывать, почему = True, "набор прогонов закрылся — пора оформлять серию"
    elif созрело and not рано:
        прерывать, почему = True, "созрело"
    elif страховка:
        прерывать, почему = True, f"страховка: {с_прошлого} ходов без записи"
    elif созрело and рано:
        прерывать, почему = False, f"созрело, но прошло только {с_прошлого} ходов"
    elif оценка < ПОРОГ_ОЦЕНКИ:
        прерывать, почему = False, f"нечего записывать (оценка {оценка:.2f})"
    elif устоялось < ПОРОГ_ГОТОВНОСТИ:
        прерывать, почему = False, f"ещё не устоялось ({устоялось:.2f}), переедет"
    elif повтор >= ПОРОГ_ПОВТОРА:
        прерывать, почему = False, f"про это уже записано ({повтор:.2f})"
    else:
        прерывать, почему = False, "ни одно место не выбрано"

    return {"прерывать": прерывать, "почему": почему, "оценка": round(оценка, 2),
            "устоялось": round(устоялось, 2), "повтор": round(повтор, 2),
            "ось": round(ось, 2),
            "места": места, "внутри_лабы": внутри, "вид": вид,
            "с_прошлого": с_прошлого}


def подсказка(вер: dict) -> str:
    """Строка для агента: куда это ложится, чтобы он не выводил это заново.

    При срабатывании страховки места не называются: страховка прерывает именно потому, что
    классификатор ничего зрелого не увидел, и подсказывать тут нечего — надо наоборот
    попросить проверить, не потерялось ли что-то за эти ходы.
    """
    if вер["почему"].startswith("страховка"):
        return (f"Классификатор за последние {вер['с_прошлого']} ходов ничего зрелого не "
                "увидел, и это прерывание — страховка. Посмотри сам, не осталось ли "
                "незаписанного; если нет, так и скажи и иди дальше.")
    if вер["почему"].startswith("набор прогонов"):
        return ("Классификатор считает, что набор прогонов закрылся и по нему пора делать "
                "вывод: оформить серию в `claims/<H>/series/S-….md` — вопрос, ось сравнения, "
                "что вышло, — приложить рисунок, если он нужен, дописать абзац про серию в "
                "страницу утверждения и открыть одно предложение на это утверждение. "
                "Это подсказка, а не приговор: проверь сам.")
    части = []
    if "lab" in вер["места"]:
        куски = []
        if вер["вид"] != "none":
            имена = {"series": "серией", "run": "прогоном",
                     "theory": "выкладкой", "claim": "правкой утверждения"}
            куски.append(f"в работу {имена.get(вер['вид'], вер['вид'])}")
        for к, имя in (("handbook", "в справочник"), ("journal", "в журнал лаборатории")):
            if к in вер["внутри_лабы"]:
                куски.append(имя)
        части.append("в базу лаборатории" + (f" ({', '.join(куски)})" if куски else ""))
    if "mempalace" in вер["места"]:
        части.append("в MemPalace")
    if "obsidian" in вер["места"]:
        части.append("в Obsidian")
    if not части:
        return ""
    return ("Классификатор считает, что из этого хода надо записать "
            + ", ".join(части)
            + f". Оценка {вер['оценка']:.1f} из 3, устоялось {вер['устоялось']:.2f}. "
              "Это подсказка, а не приговор: проверь сам.")


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] in ("--сводка", "--summary"):
        сводка()
        return
    if len(sys.argv) < 2:
        return
    путь = Path(sys.argv[-1])
    try:
        груз = json.loads(путь.read_text(encoding="utf-8"))
    except (OSError, ValueError) as ошибка:
        print(json.dumps({"прерывать": None, "беда": str(ошибка)}, ensure_ascii=False))
        return
    finally:
        try:
            путь.unlink()
        except OSError:
            pass

    запись = {"когда": time.strftime("%Y-%m-%dT%H:%M:%S"),
              "сессия": груз.get("сессия", "")[:8],
              "ходов": груз.get("ходов"),
              "счётчик_сработал": груз.get("счётчик_сработал"),
              "знаков": len(груз.get("текст") or "")}

    def сдаться(беда: str) -> None:
        запись["беда"] = беда
        записать(запись)
        print(json.dumps({"прерывать": None, "беда": беда}, ensure_ascii=False))

    текст = (груз.get("текст") or "").strip()
    if not текст:
        сдаться("пустой ход")
        return
    k = ключ()
    if not k:
        сдаться("нет ключа OpenRouter")
        return
    try:
        клон = состояние_клона(груз.get("каталог") or "")
        ответ = спросить(текст, k, груз.get("записанное") or [], клон)
    except Exception as ошибка:          # сеть, ключ, разбор — любая беда в журнал
        сдаться(f"{type(ошибка).__name__}: {ошибка}"[:200])
        return

    вер = решение(ответ, int(груз.get("ходов") or 0),
                  int(груз.get("прошлое") or 0), клон)
    отв = ответ.get("answers") or {}
    запись.update({
        "работа": (клон or {}).get("work"),
        "не_описано_прогонов": (клон or {}).get("runs_arrived_not_described"),
        "ось": вер["ось"],
        "вид": вер["вид"],
        "места": {и: round(float((отв.get(и) or {}).get("noul") or 0), 2)
                  for и in list(МЕСТА) + list(ВНУТРИ_ЛАБЫ)},
        "выбраны": вер["места"] + вер["внутри_лабы"],
        "оценка": вер["оценка"], "устоялось": вер["устоялось"], "повтор": вер["повтор"],
        "прерывать": вер["прерывать"], "почему": вер["почему"],
        "секунд": ответ.get("_секунд"),
        "токенов": (ответ.get("usage") or {}).get("input_tokens"),
        "цена": (ответ.get("usage") or {}).get("cost"),
    })
    записать(запись)
    вер["подсказка"] = подсказка(вер) if вер["прерывать"] else ""
    print(json.dumps(вер, ensure_ascii=False))


if __name__ == "__main__":
    main()
