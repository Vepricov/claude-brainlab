#!/usr/bin/env python3
"""Сверить каждое число из «Что статья утверждает» с текстом самой статьи.

Это не доказательство правильности: число может стоять в статье и быть приписано не тому
месту. Но обратное ловится надёжно — число, которого в статье нет вовсе, и есть выдумка.

**Правило, которое проверка и охраняет.** В строке «на чём держится» место только числам,
напечатанным в статье. Наша арифметика — разности, проценты, пересчитанные средние — живёт в
«нашей оценке» и в «чем опровергается», где она по определению наша. Поэтому проверка смотрит
на строку, в которой число стоит, и ругается только на «на чём держится».

Замерено 07-10-2026 на теме `muon-sign-methods`: 439 чисел в семнадцати разборах, 23 не
нашлись дословно, и из них 21 оказались законными (наши пороги, наши гиперпараметры,
арифметика по напечатанным числам). Два были настоящими ошибками, и оба стояли именно в «на
чём держится»: `0.86-0.90` вместо `0.8948, 0.8926, 0.8965, 0.892` и `23.7-31.3` вместо
`28.7` и `23.7`.

    paper_claims_verify.py <клон литературы> <папка с текстами статей>

Тексты статей — это `<ключ цитирования>.txt`, полученные из PDF (`pdftotext`). Чего нет на
диске, проверка честно называет непроверенным, а не считает сошедшимся.

**Чего она не видит, и поэтому её «нет в статье» не приговор.** Числа, напечатанные ВНУТРИ
растрового рисунка, в текстовый слой PDF не попадают. Проверено 07-10-2026 на
`allaire2026zeroth`: значения `5.395` и `2.743` отсутствуют и в `.txt`, и в самом PDF при
прямом `pdftotext -layout`, а на картинке рисунка 5 они напечатаны в легенде целиком —
«Averaging update (‖error‖=5.395)» и «Directional update (‖error‖=2.743)». По своду это
напечатанные числа, и записывать их можно. Такой же слепотой объясняются таблицы, отрисованные
из tex-исходника (`liu2026rethinking`), и доли, переведённые в проценты: в статье стоит `.351`,
в разборе `35.1`.

Поэтому проверка называет подозрительное, а решает человек, посмотрев на рисунок. Удалять
число только потому, что скрипт его не нашёл, нельзя.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CLAIMS = re.compile(r"## Что статья утверждает(.*?)(?=\n## |\Z)", re.S)
NUMBER = re.compile(r"(?<![\w.])\d+\.\d+(?![\w.])")
#: Номер раздела, таблицы, рисунка, теоремы — адрес, а не величина.
ADDRESS = re.compile(r"(Табл|Рисун|Раздел|Приложен|Теорем|Лемм|Следстви|Уравнени|§)\w*"
                     r"\s*[\d.,\s–-]*$")
#: Четыре строки формы. Числа статьи обязаны стоять в первой; в остальных они наши.
LINES = ("**на чём держится.**", "**сетап.**", "**чем опровергается.**", "**наша оценка.**")
STRICT = LINES[0]


def which_line(block: str, at: int) -> str:
    """В какой из четырёх строк формы стоит число."""
    best, name = -1, "(вне формы)"
    for line in LINES:
        found = block.rfind(line, 0, at)
        if found > best:
            best, name = found, line
    return name


def numbers_of(block: str) -> list[tuple[str, str]]:
    out = []
    for found in NUMBER.finditer(block):
        if ADDRESS.search(block[max(0, found.start() - 24):found.start()]):
            continue
        out.append((found.group(0), which_line(block, found.start())))
    return out


def present(number: str, text: str, flat: str) -> bool:
    """Есть ли это число в тексте статьи.

    Кроме запятой как разделителя, принимаем запись без ведущего нуля: `kaya2026eggroll`
    печатает интервал как `+2.50% [−.82, 5.82]`, и `0.82` из разбора иначе не находилось,
    хотя число то же. В этой же статье так же напечатаны `.0081`, `.9825`, `+.04%`, так
    что речь о стиле издания, а не об одном месте.
    """
    shapes = [number, number.replace(".", ",")]
    if number.startswith("0."):
        shapes += [number[1:], number[1:].replace(".", ",")]
    return any(s in text for s in shapes) or any(s in flat for s in shapes)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=Path, help="клон репозитория литературы темы")
    parser.add_argument("texts", type=Path, help="папка с <ключ>.txt статей")
    parser.add_argument("--all", action="store_true",
                        help="показывать и законные несовпадения в остальных трёх строках")
    args = parser.parse_args(argv)

    papers = [p for p in sorted(args.base.glob("*.md")) if p.name != "README.md"]
    if not papers:
        sys.exit(f"в {args.base} нет разборов")

    total = strict_bad = loose_bad = 0
    unchecked: list[str] = []
    print("%-26s %6s %9s %s" % ("разбор", "чисел", "в «на чём»", "каких"))
    for paper in papers:
        found_block = CLAIMS.search(paper.read_text(encoding="utf-8"))
        block = found_block.group(1) if found_block else None
        if block is None:
            print("%-26s %6s %9s нет раздела «Что статья утверждает»" % (paper.stem, "-", "-"))
            continue
        source = args.texts / f"{paper.stem}.txt"
        if not source.exists():
            unchecked.append(paper.stem)
            continue
        text = source.read_text(encoding="utf-8", errors="replace")
        flat = re.sub(r"[\s,]", "", text)
        seen: dict[str, str] = {}
        for number, line in numbers_of(block):
            seen.setdefault(number, line)
        total += len(seen)
        hard = sorted(n for n, line in seen.items()
                      if line == STRICT and not present(n, text, flat))
        soft = sorted(n for n, line in seen.items()
                      if line != STRICT and not present(n, text, flat))
        strict_bad += len(hard)
        loose_bad += len(soft)
        tail = " ".join(hard) if hard else "—"
        if args.all and soft:
            tail += f"   (наши: {' '.join(soft)})"
        print("%-26s %6d %9d %s" % (paper.stem, len(seen), len(hard), tail))

    print(f"\nвсего чисел: {total}; нет в статье и стоят в «на чём держится»: {strict_bad}; "
          f"нет в статье, но стоят в наших строках: {loose_bad}")
    if unchecked:
        print("текста статьи нет на диске, проверить нечем: " + ", ".join(unchecked))
    return 1 if strict_bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
