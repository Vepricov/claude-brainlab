#!/usr/bin/env python3
"""Сверить строку «авторы» в шапке разбора с полем author в его же BibTeX.

Авторы в шапке должны быть переписаны из BibTeX, а не набраны заново: BibTeX приходит с
arXiv детерминированно, а набранное заново пишет модель, и она ошибается правдоподобно.

Проверено 07-10-2026 по всей библиотеке: 640 разборов с шапкой и BibTeX, разошлись девять, и
три из них разошлись полностью — в шапке стояли ЧУЖИЕ люди. У `tan2025harmony` «Zeng, Guo,
Luo» вместо «Tan, Liu, Zhan, Ding, Wang, Lu, Yuan»; у `wang2024simultaneous` «Li, Luo, Bai»
вместо «Wang, Shen, Ding, Xue, Liu»; у `zhao2025second` первый автор совпал, у второго то же
имя и другая фамилия («Chen, Sizhe» против «Dang, Sizhe»), а «Zhang, Kaiqing» и «Basar,
Tamer» — люди из другой работы вовсе.

Остальные шесть расхождений были ложными или мелкими: экранирование LaTeX (`horváth` против
`horv{\\'{a`), «qwen team» против «team», и два усечённых списка, где в шапке двое из трёх.
Поэтому проверка делит находки на полные расхождения и частичные: первые чинят, вторые
смотрят глазами.

    author_check.py <клон литературы> [ещё клоны...]
    author_check.py --fix <клон>     переписать шапку из BibTeX

Чинить можно только в сторону BibTeX. Если неверен сам BibTeX, это другая беда: его правят у
источника, а не здесь.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HEAD = re.compile(r"(\*\*авторы\*\*\s*)(.+?)(\s*·)", re.S)
BIB = re.compile(r"author\s*=\s*\{(.+?)\}\s*,\s*\n", re.S)
#: Экранирование LaTeX, которое встречается в выгрузках с arXiv.
LATEX = {r"{\'{a}}": "á", r"{\'{e}}": "é", r'{\"{u}}': "ü", r'{\"{o}}': "ö",
         r"{\c{c}}": "ç", r"{\v{s}}": "š", r"{\v{c}}": "č", r"{\l}": "ł",
         r"\'a": "á", r"\'e": "é", r'\"u': "ü", r'\"o': "ö"}


def clean(text: str) -> str:
    for mark, letter in LATEX.items():
        text = text.replace(mark, letter)
    return re.sub(r"[{}\\]", "", text).strip()


def people_of_bib(text: str) -> list[str]:
    found = BIB.search(text)
    if not found:
        return []
    return [clean(p) for p in re.split(r"\s+and\s+", found.group(1)) if p.strip()]


def surname(person: str) -> str:
    """Фамилия из «Фамилия, Имя» или из «Имя Фамилия»."""
    return (person.split(",")[0] if "," in person else person.split()[-1]).strip().lower()


def surnames_of_head(line: str) -> set[str]:
    """В шапке люди записаны как «Фамилия, Имя, Фамилия, Имя», то есть через запятую подряд."""
    parts = [p.strip() for p in clean(line).split(",") if p.strip()]
    return {p.lower() for p in parts[::2]} | {p.lower() for p in parts[1::2]}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", type=Path, nargs="+", help="клоны репозиториев литературы")
    parser.add_argument("--fix", action="store_true", help="переписать шапку из BibTeX")
    args = parser.parse_args(argv)

    total = full = partial = fixed = skipped = 0
    for root in args.roots:
        for paper in sorted(root.glob("*.md")):
            if paper.name == "README.md":
                continue
            text = paper.read_text(encoding="utf-8")
            head, bib = HEAD.search(text), people_of_bib(text)
            if not head or not bib:
                skipped += 1
                continue
            total += 1
            in_head = surnames_of_head(head.group(2))
            in_bib = {surname(p) for p in bib}
            common = in_head & in_bib
            if common == in_bib and len(in_head) >= len(in_bib):
                continue
            kind = "РАСХОДЯТСЯ ПОЛНОСТЬЮ" if not common else "частично"
            full += not common
            partial += bool(common)
            print(f"  [{kind}] {paper.stem}")
            print(f"      шапка:  {head.group(2)[:72]}")
            print(f"      BibTeX: {', '.join(bib)[:72]}")
            if args.fix:
                paper.write_text(HEAD.sub(lambda m: m.group(1) + ", ".join(bib) + m.group(3),
                                          text, count=1), encoding="utf-8")
                fixed += 1
    tail = f", переписано: {fixed}" if args.fix else ""
    print(f"\nразборов проверено: {total}; расходятся полностью: {full}; "
          f"частично: {partial}; без шапки или BibTeX: {skipped}{tail}")
    return 1 if full else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
