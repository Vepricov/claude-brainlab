#!/usr/bin/env python3
"""Убрать строку «авторы · год · где · ключ цитирования · тема» из разборов и заметок.

Строку собирал детерминированный проход из BibTeX. Владелец 07-10-2026: «нахуя ты пишешь
авторы, год, где, ключ цитирования? У тебя же просто это в биптехе написано». Это правда:
блок BibTeX стоит на три строки ниже и несёт те же сведения в машинном виде, а шапка
повторяла их словами и расходилась с ними при любой правке.

Что остаётся: заголовок статьи `# ...` и ссылка `[Открыть источник](...)`. Ссылки в BibTeX
нет в виде, по которому можно щёлкнуть, поэтому она нужна.

Что уходит вместе со строкой: поле `тема`. В BibTeX его нет, но тема и так видна из того,
в какой папке лежит разбор, и дублировать её в тексте незачем.

    drop_header_line.py <папка с .md>... [--fix]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

#: Строка целиком, вместе с пустой строкой за ней. Начинается с `**авторы**` и тянется до
#: конца своей строки: внутри неё `·`, поля в звёздочках и ключ в обратных кавычках.
LINE = re.compile(r"(?m)^\*\*авторы\*\*[^\n]*\n\n?")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("roots", type=Path, nargs="+")
    parser.add_argument("--fix", action="store_true")
    args = parser.parse_args(argv)

    total = touched = 0
    for root in sorted(args.roots):
        for paper in sorted(root.glob("*.md")):
            if paper.name == "README.md":
                continue
            total += 1
            text = paper.read_text(encoding="utf-8")
            found = LINE.search(text)
            if not found:
                continue
            fixed = LINE.sub("", text, count=1)
            if LINE.search(fixed):
                print(f"  {root.name}/{paper.stem}: строк больше одной, не трогаю")
                continue
            touched += 1
            if args.fix:
                paper.write_text(fixed, encoding="utf-8")
    tail = f", переписано: {touched}" if args.fix else ""
    print(f"файлов: {total}, со строкой шапки: {touched}{tail}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
