#!/usr/bin/env python3
"""Сторож переезда: писать в прежние корни (`Staff`, `Papers`, `Projects`) больше нельзя.

Владелец 16-10-2026: «никто ничего не должен писать не в Staff, не в Projects, не в Paper…
чтобы когда кто-то пытался что-то записать, там была какая-то ошибка».

16-10-2026 дерево лаборатории переехало в `~/brainlab`, а прежние корни удалены. Запись по
старому пути сама по себе не падает: оболочка просто создаст папку заново, и работа молча
уедет в сторону от базы. Поэтому отказ даётся здесь, до вызова.

Запрещается только ЗАПИСЬ и только ТУДА. Сторож, который краснеет на безопасном, обходят, и
этот за первый час ошибся дважды: остановил запись правила, где прежний путь был просто
назван, и поиск `grep … 2>/dev/null`, где `>` сделал команду «пишущей». Поэтому смотрим не
на всю команду, а на цель: аргументы пишущей команды и то, что стоит сразу за `>`.
"""
from __future__ import annotations

import json
import re
import shlex
import sys

#: Корни, которых больше нет.
KORNI = ("/Users/andrey/Staff", "/Users/andrey/Papers", "/Users/andrey/Projects",
         "~/Staff", "~/Papers", "~/Projects",
         "$HOME/Staff", "$HOME/Papers", "$HOME/Projects")

#: Прежнее хранилище в iCloud. 17-10-2026 владелец перевёл Obsidian целиком на дерево
#: лаборатории: «старый, который в iCloud, вообще менять не надо», «все должно работать
#: только на моем сетапе». ЧИТАТЬ оттуда можно и нужно — там лежат заметки, которые ещё не
#: перенесены, — а писать нельзя: запись в хранилище, которое владелец не открывает, это
#: работа, сделанная в стол. Один вход оставлен нарочно: `.stignore` — служебный файл
#: синхронизации, им как раз и останавливают обмен с этим хранилищем.
ARHIV = "/Users/andrey/Library/Mobile Documents/iCloud~md~obsidian/Documents/shkodnik1917"
ARHIV_MOZNO = (f"{ARHIV}/.stignore",)

#: Команды, которые создают или меняют файлы. `ls`, `cat`, `grep`, `find` сюда не входят.
PISHUSHIE = {"mkdir", "touch", "cp", "mv", "rsync", "tee", "install", "dd",
             "ln", "chmod", "chown", "unzip", "rm", "rmdir"}

#: Тело heredoc — это текст, а не путь.
HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?.*?^\1\s*$", re.S | re.M)

KUDA = ("Дерево лаборатории живёт в `~/brainlab`: работа — "
        "`~/brainlab/<направление>/<тема>/<работа>`, заметки — в её же `notes/`, "
        "дневник — `daily/`, логи прогонов — `runs/`.")


def celi(command: str) -> list[str]:
    """Куда эта команда пишет: аргументы пишущих команд и цели перенаправления.

    Команда разбирается по частям: `&&`, `||`, `|`, `;` и перевод строки начинают новую, и
    признак «сейчас пишем» на границе сбрасывается. Без этого `rm x && grep "~/Staff" .`
    читалось как «удаляем ~/Staff», и сторож останавливал поиск.
    """
    out: list[str] = []
    for kusok in re.split(r"(?:&&|\|\||[;|\n])", HEREDOC.sub(" ", command)):
        # Разбор кавычками, а не пробелами: в прежнем хранилище путь содержит пробелы
        # («Mobile Documents»), и дробление по пробелу превращало его в четыре обрывка,
        # ни один из которых не начинался с корня. 17-10-2026 на этом `cp` в хранилище
        # проходил мимо сторожа. Если кавычки в команде не сходятся, остаётся прежний
        # разбор: пропустить команду хуже, чем разобрать её грубо.
        try:
            slova = [s.strip("'\"`,:") for s in shlex.split(kusok, posix=True) if s]
        except ValueError:
            slova = [s.strip("'\"`,:") for s in re.split(r"[\s()]+", kusok) if s]
        pishem = False
        for i, slovo in enumerate(slova):
            goloe = slovo.lstrip("0123456789")
            if goloe.startswith(">"):                      # `>файл`, `2>файл`, `>>файл`
                hvost = goloe.lstrip(">")
                out.append(hvost if hvost else (slova[i + 1] if i + 1 < len(slova) else ""))
                continue
            imya = slovo.rsplit("/", 1)[-1]
            if imya in PISHUSHIE or (imya == "git" and i + 1 < len(slova)
                                     and slova[i + 1] in ("clone", "init")):
                pishem = True
                continue
            if pishem and not slovo.startswith("-"):
                out.append(slovo)
    return [x for x in out if x]


def puti(payload: dict) -> list[str]:
    """Пути, КУДА пишут. Упоминание пути в тексте или в образце поиска сюда не попадает."""
    tool = payload.get("tool_name") or ""
    args = payload.get("tool_input") or {}
    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        return [str(args.get("file_path") or args.get("notebook_path") or "")]
    if tool == "Bash":
        return celi(str(args.get("command") or ""))
    return []


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    for put in puti(payload):
        for koren in KORNI:
            if put == koren or put.startswith(koren + "/"):
                print(f"Путь `{koren}` больше не существует: переезд закончен 16-10-2026. "
                      f"{KUDA} Если это чтение архива — читай, но не пиши: архивы лежат "
                      f"в `~/archive`.", file=sys.stderr)
                return 2
        tochnyj = put.replace("~", "/Users/andrey", 1) if put.startswith("~") else put
        if (tochnyj == ARHIV or tochnyj.startswith(ARHIV + "/")) \
                and tochnyj not in ARHIV_MOZNO:
            print("Прежнее хранилище в iCloud — читальня, писать в него нельзя: владелец "
                  f"его не открывает, и запись уедет в стол. {KUDA} Литература темы — "
                  "`~/brainlab/<направление>/<тема>/literature`, доска чтения — "
                  "`~/brainlab/personal/operon`, общие заметки — "
                  "`~/brainlab/personal/general`.", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
