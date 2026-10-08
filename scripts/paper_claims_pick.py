#!/usr/bin/env python3
"""Какие разборы вообще стоит открывать, чтобы вытащить из них утверждения.

Проход по библиотеке БЕЗ модели: читает разборы из зеркала и говорит, у каких из них в
разделе «Графики и таблицы» есть конкретные числа. Статью без чисел модели показывать
незачем — она всё равно вернёт «утверждений не выделено», и это самый дорогой способ
получить ноль. Замерено 06-10-2026 на пробе из десяти статей: около 11 тысяч токенов на
статью независимо от исхода.

    paper_claims_pick.py                 сколько и где
    paper_claims_pick.py --theme <слаг>  список файлов этой темы, которые стоит открыть
    paper_claims_pick.py --thin          наоборот: разборы, где числа ПОТЕРЯНЫ при разборе

Про `--thin`. Проба показала, что в четырёх случаях из пяти статья измеряла, а числа до
разбора не дошли: в «Графиках и таблицах» стоит пересказ картинки словами. Это дефект не
статьи, а разбора, и чинится он на стороне `paper-ingest`, а не здесь.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import subprocess
import sys

#: Зеркало базы на сервере. Путь настраивается, а не вписан: репозиторий публичный,
#: и домашний каталог конкретного человека в него попадать не должен.
MIRROR = pathlib.Path(os.environ.get("LAB_KNOWLEDGE_MIRROR",
                                     "~/brainlab-stack/mirror-gitlab")).expanduser()
#: Что считается конкретным числом: десятичное, доля, кратность, крупное целое.
NUMBER = re.compile(r"\d+[.,]\d+|\d+\s*%|\\%|\d+\s*[×x]\b|\d+\s*раз|\d{3,}")
#: Признак того, что раздел есть, но числа в нём не донесены: он описывает картинку словами.
WORDS_ONLY = re.compile(r"качественн|без (?:точных )?чисел|визуальн|иллюстра", re.I)
ENOUGH = 3


def git(repo: pathlib.Path, *args: str) -> str:
    ran = subprocess.run(["git", "--git-dir", str(repo), *args],
                         capture_output=True, text=True)
    return ran.stdout if ran.returncode == 0 else ""


def look(repo: pathlib.Path) -> list[tuple[str, int, int]]:
    """Для каждой статьи темы: имя, сколько чисел в «Графиках», длина раздела."""
    out = []
    for name in git(repo, "ls-tree", "-r", "--name-only", "HEAD").splitlines():
        if not name.endswith(".md") or "/" in name:
            continue
        text = git(repo, "show", f"HEAD:{name}")
        block = re.search(r"^## Графики и таблицы(.*?)(?=^## |\Z)", text, re.S | re.M)
        body = block.group(1) if block else ""
        out.append((name, len(NUMBER.findall(body)), len(body.strip())))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--theme", help="слаг темы: напечатать её список")
    parser.add_argument("--thin", action="store_true",
                        help="разборы, потерявшие числа статьи")
    args = parser.parse_args()
    if not MIRROR.is_dir():
        sys.exit(f"нет зеркала {MIRROR}: проход запускается на brain_lab")

    worth, cheap, thin, total = 0, 0, [], 0
    for repo in sorted(MIRROR.glob("*/literature.git")):
        theme = repo.parent.name
        if args.theme and theme != args.theme:
            continue
        for name, numbers, size in look(repo):
            total += 1
            if numbers >= ENOUGH:
                worth += 1
                if args.theme:
                    print(f"  {name}")
            else:
                cheap += 1
                # Раздел есть и не пуст, а чисел нет — значит их потеряли при разборе.
                if size > 200:
                    thin.append(f"{theme}/{name}")
    if args.thin:
        print(f"разборов, где раздел есть, а чисел нет: {len(thin)}")
        for one in thin[:40]:
            print(f"  {one}")
        return 0
    if not args.theme:
        print(f"разборов всего: {total}")
        print(f"стоит открывать: {worth}")
        print(f"пропустить без модели: {cheap} — это {cheap * 11000 / 1e6:.1f} млн "
              f"токенов, которых не придётся тратить на пустой исход")
        print(f"цена прохода по оставшимся: около {worth * 11000 / 1e6:.1f} млн токенов")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
