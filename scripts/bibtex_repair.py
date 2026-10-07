#!/usr/bin/env python3
"""Починить имена в BibTeX, где имя человека втянуто внутрь скобок диакритики.

Найдено 07-10-2026 при сборке шапки разбора из BibTeX. У девяти записей библиотеки поле
`author` испорчено одинаково: имя переехало внутрь группы ударения, а хвост фамилии остался
снаружи.

    было:  Richt{\\'{a, Peter}}rik
    надо:  Richt{\\'{a}}rik, Peter

Из-за этого разбор поля даёт «Peterrik Richt» вместо «Peter Richtárik», и так же криво
выглядели шапки. Ошибка машинная и повторяется буква в букву, поэтому чинится правилом, а не
руками. Задеты, в частности, Richtárik, Horváth, Takáč, von Rütte и Sáez de Ocáriz Borde,
то есть люди, с которыми лаборатория работает.

    bibtex_repair.py <клон литературы> [ещё клоны...]      показать
    bibtex_repair.py --fix <клон> [...]                    починить
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

#: `Фамилия{\'{б, Имя}}хвост` → `Фамилия{\'{б}}хвост, Имя`. Запятая ставится В КОНЕЦ
#: фамилии, а не сразу за скобкой: фамилия бывает из нескольких слов и со вторым ударением
#: («Sáez de Ocáriz Borde»), и тогда имя оказывалось в её середине.
SWALLOWED = re.compile(r"(\\[\'`\"^~cvu=.Hr]\s*\{)([a-zA-Z])\s*,\s*([^{}]+?)\}\}")
TAIL = re.compile(r"^((?:[^\s]|\s(?!and\s))*)")


def repair(author: str) -> str:
    """Вынести имя из скобок ударения в конец фамилии."""
    while True:
        found = SWALLOWED.search(author)
        if not found:
            return author
        tail = TAIL.match(author[found.end():]).group(1)
        author = (author[:found.start()] + found.group(1) + found.group(2) + "}}"
                  + tail + ", " + found.group(3) + author[found.end() + len(tail):])


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", type=Path, nargs="+")
    parser.add_argument("--fix", action="store_true")
    args = parser.parse_args(argv)

    found = fixed = 0
    for root in sorted(args.roots):
        for paper in sorted(root.glob("*.md")):
            if paper.name == "README.md":
                continue
            text = paper.read_text(encoding="utf-8")
            whole = re.search(r"(author\s*=\s*\{)(.*?)(\}\s*,?\s*\n)", text, re.S)
            if not whole:
                continue
            fresh = repair(whole.group(2))
            if fresh == whole.group(2):
                continue
            found += 1
            print(f"  {root.name}/{paper.stem}")
            print(f"      было:  {whole.group(2)[:92]}")
            print(f"      стало: {fresh[:92]}")
            if args.fix:
                paper.write_text(text[:whole.start(2)] + fresh + text[whole.end(2):],
                                 encoding="utf-8")
                fixed += 1
    tail = f", починено: {fixed}" if args.fix else ""
    print(f"\nзаписей с втянутым именем: {found}{tail}")
    return 1 if (found and not args.fix) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
