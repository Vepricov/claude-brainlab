#!/usr/bin/env python3
"""Где лежат разборы статей. Один ответ на всех, потому что раньше их было десять.

До 16-10-2026 хранилище было отдельной папкой в iCloud, и разборы лежали одной стопкой
`Literature/<тема>/`. Путь к ней стоял захардкоженным в каждом скрипте этого навыка, и
после переезда все десять писали в папку, которой больше нет: ошибки не было, файлы просто
уходили в пустоту.

Теперь хранилище — само дерево лаборатории, а разборы темы лежат в её репозитории:

    ~/brainlab/<направление>/<тема>/literature/<Название статьи>.md

Отсюда два следствия, из-за которых и нужен этот модуль. Единой папки `Literature` нет, и
список тем приходится собирать обходом дерева. А тема опознаётся по имени папки, но живёт
внутри направления, которое скрипту знать неоткуда, поэтому путь ищется, а не склеивается.

Корень берётся из `OBSIDIAN_VAULT`, иначе `~/brainlab`.
"""
from __future__ import annotations

import os
from pathlib import Path

VAULT = Path(os.getenv("OBSIDIAN_VAULT", "~/brainlab")).expanduser()

#: Приёмник и корзина общие на все темы и остаются НА МАШИНЕ: статья попадает в тему только
#: после того, как владелец её принял, а до этого ей в общем репозитории делать нечего.
INBOX = VAULT / "personal" / "literature" / "_inbox"
TRASH = VAULT / "personal" / "literature" / "_trash"
REJECTED = TRASH / "paper-search_rejected.md"


def temy() -> dict[str, Path]:
    """Тема → папка её разборов. Имя темы это имя папки темы, как в GitLab."""
    out: dict[str, Path] = {}
    for mesto in sorted(VAULT.glob("*/*/literature")):
        if mesto.is_dir():
            out.setdefault(mesto.parent.name, mesto)
    return out


def tema_put(tema: str) -> Path | None:
    """Папка разборов темы. `None`, если такой темы в дереве нет — молча не выдумываем."""
    if tema in ("_inbox", INBOX.name):
        return INBOX
    if tema in ("_trash", TRASH.name):
        return TRASH
    return temy().get(tema)


def vse_papki() -> list[Path]:
    """Все места, где лежат разборы: темы плюс приёмник и корзина."""
    return [*temy().values(), INBOX, TRASH]
