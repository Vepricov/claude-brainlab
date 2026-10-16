#!/usr/bin/env python3
"""Сторож переезда: писать в прежние корни (`Staff`, `Papers`, `Projects`) больше нельзя.

Владелец 16-10-2026: «никто ничего не должен писать не в Staff, не в Projects, не в Paper…
чтобы когда кто-то пытался что-то записать, там была какая-то ошибка».

16-10-2026 дерево лаборатории переехало в `~/brainlab`, а прежние корни удалены. Запись по
старому пути сама по себе не падает: оболочка просто создаст папку заново, и работа молча
уедет в сторону от базы. Поэтому отказ даётся здесь, до вызова.

Запрещается только ЗАПИСЬ и только ТУДА. Чтение архива и упоминание пути в тексте —
законны: сторож, который краснеет на безопасном, обходят, и в первый же час этот сторож
остановил запись правила, в котором прежний путь был просто назван.
"""
from __future__ import annotations

import json
import re
import sys

#: Корни, которых больше нет. `~/Obsidian` сюда не входит: пока хранилище не переведено
#: целиком, читать и писать туда законно.
KORNI = ("/Users/andrey/Staff", "/Users/andrey/Papers", "/Users/andrey/Projects",
         "~/Staff", "~/Papers", "~/Projects",
         "$HOME/Staff", "$HOME/Papers", "$HOME/Projects")

#: Команды оболочки, которые создают или меняют файлы. `ls`, `cat`, `grep` сюда не входят.
PISHET = re.compile(
    r"\b(?:mkdir|touch|cp|mv|rsync|tee|install|dd|git\s+clone|git\s+init|"
    r"ln|chmod|chown|unzip|tar\s+-?x)\b|>\s*|>>\s*")

#: Тело heredoc — это текст, а не путь.
HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?.*?^\1\s*$", re.S | re.M)

KUDA = ("Дерево лаборатории живёт в `~/brainlab`: работа — "
        "`~/brainlab/<направление>/<тема>/<работа>`, заметки — в её же `notes/`, "
        "дневник — `daily/`, логи прогонов — `runs/`.")


def celi(command: str) -> list[str]:
    """Слова команды, похожие на путь: тело heredoc снято, кавычки обрезаны."""
    out = []
    for slovo in re.split(r"[\s;|&()]+", HEREDOC.sub(" ", command)):
        out.append(slovo.strip("'\"`,:"))
    return out


def puti(payload: dict) -> list[str]:
    """Пути, КУДА пишут. Упоминание пути в тексте сюда не попадает."""
    tool = payload.get("tool_name") or ""
    args = payload.get("tool_input") or {}
    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        return [str(args.get("file_path") or args.get("notebook_path") or "")]
    if tool == "Bash":
        command = str(args.get("command") or "")
        return celi(command) if PISHET.search(command) else []
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
