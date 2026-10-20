#!/usr/bin/env python3
"""Где лежат разборы статей. Один ответ на все скрипты навыка.

Разборы темы лежат в её репозитории литературы в дереве лаборатории:

    ~/brainlab/<направление>/<тема>/literature/<Название статьи>.md

Единой папки нет, поэтому список тем собирается обходом дерева. Тема опознаётся по имени
папки, но живёт внутри направления, которое скрипту знать неоткуда, поэтому путь ищется, а
не склеивается.

Корень берётся из `OBSIDIAN_VAULT`, иначе `~/brainlab`.
"""
from __future__ import annotations

import os
from pathlib import Path

VAULT = Path(os.getenv("OBSIDIAN_VAULT", "~/brainlab")).expanduser()

def temy() -> dict[str, Path]:
    """Тема → папка её разборов. Имя темы это имя папки темы, как в GitLab."""
    out: dict[str, Path] = {}
    for mesto in sorted(VAULT.glob("*/*/literature")):
        if mesto.is_dir():
            out.setdefault(mesto.parent.name, mesto)
    return out


def tema_put(tema: str) -> Path | None:
    """Папка разборов темы. `None`, если такой темы в дереве нет — молча не выдумываем."""
    return temy().get(tema)


def vse_papki() -> list[Path]:
    """Все места, где лежат разборы: литература тем."""
    return list(temy().values())
