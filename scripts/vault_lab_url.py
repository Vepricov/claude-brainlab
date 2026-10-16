#!/usr/bin/env python3
"""Адрес страницы базы — в свойства заметки хранилища.

У разборов в базе есть свойство `lab_url`: адрес этой же страницы в GitLab. Нужен он не
там, а здесь: читает владелец заметку в Обсидиане, и один щелчок по свойству открывает
страницу в базе. Владелец 16-10-2026: «нужно вставить brain lab knowledge link, то есть
ссылку именно в гитлабе, чтобы я мог тыкнуть и прям открыть эту ссылку в GitLab, тоже это
сделай во всех статьях».

Адрес не собирается заново, а **берётся со страницы базы**: так в этом файле нет ни адреса
базы, ни таблицы соответствия темы и полного пути, и переезд репозитория правится одним
проходом `front_matter.py`, а не двумя скриптами.

Сверка идёт по ключу цитирования: заголовки в базе и в заметке расходятся (двоеточия,
формулы, длина), и по ним получается ложная разница. Ключ есть с обеих сторон — в базе это
имя файла, в заметке ключ в блоке BibTeX.

Два случая, когда одного ключа мало, и оба настоящие. У части заметок блока BibTeX нет
вовсе (отчёты лабораторий, посты, старые книги) — тогда страница ищется по приведённому
заголовку. И тема заметки не всегда совпадает с темой её страницы: один и тот же разбор
владелец держит в `muon-convergence-theory`, а в базе он лежит в `reinforcement-learning`.
Поэтому ключ сначала ищется в своей теме, а потом во всех остальных: адрес страницы нужен
тот, по которому она открывается, а не тот, по которому ей следовало бы лежать.

    vault_lab_url.py <клон литературы>... --хранилище <папка Literature> [--fix]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FRONT = re.compile(r"\A---\n(.*?\n)---\n", re.S)
BIBKEY = re.compile(r"@\w+\{([^,\s}]+)\s*,")
LAB_URL = re.compile(r"(?m)^lab_url:.*\n")
URL_LINE = re.compile(r"(?m)^url:.*\n")
#: Строка `источник: база лаборатории, <тема>/<ключ>` стоит у заметок, приехавших из базы:
#: у них блока BibTeX может ещё не быть, а ключ уже известен.
FROM_BASE = re.compile(r"(?m)^источник: база лаборатории, [^/\n]+/(\S+)\s*$")


def flat(said: str) -> str:
    """Заголовок, приведённый к сравнимому виду: без разметки, знаков и регистра."""
    return " ".join(re.sub(r"[^0-9A-Za-zА-Яа-яЁё ]", " ", said.lower()).split())


def pages(root: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Страницы темы: ключ → адрес и приведённый заголовок → адрес."""
    by_key: dict[str, str] = {}
    by_title: dict[str, str] = {}
    for page in sorted(root.glob("*.md")):
        if page.name == "README.md":
            continue
        text = page.read_text(encoding="utf-8", errors="replace")
        head = FRONT.match(text)
        if head is None:
            continue
        address = re.search(r"(?m)^lab_url:\s*(\S+)\s*$", head.group(1))
        if not address:
            continue
        by_key[page.stem] = address.group(1)
        title = re.search(r'(?m)^title:\s*"?(.+?)"?\s*$', head.group(1))
        if title:
            by_title[flat(title.group(1))] = address.group(1)
    return by_key, by_title


def note_key(text: str) -> str | None:
    key = BIBKEY.search(text)
    if key:
        return key.group(1)
    said = FROM_BASE.search(text)
    return said.group(1) if said else None


def patched(text: str, address: str) -> str | None:
    """Свойство встаёт сразу за `url`: рядом с адресом статьи, как в базе.

    Шапки нет — и свойства не будет: заводить её этим проходом нельзя, потому что заметка
    без шапки это либо список партии, либо черновик, и порядок полей в ней неизвестен.
    """
    head = FRONT.match(text)
    if head is None:
        return None
    block = head.group(1)
    line = f"lab_url: \"{address}\"\n"
    if LAB_URL.search(block):
        fresh = LAB_URL.sub(line, block, count=1)
    elif URL_LINE.search(block):
        fresh = URL_LINE.sub(lambda hit: hit.group(0) + line, block, count=1)
    else:
        fresh = block + line
    if fresh == block:
        return None
    return "---\n" + fresh + "---\n" + text[head.end():]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("roots", type=Path, nargs="+")
    parser.add_argument("--хранилище", type=Path, dest="vault", required=True)
    parser.add_argument("--fix", action="store_true")
    args = parser.parse_args(argv)

    total = touched = 0
    no_page: list[str] = []
    no_front: list[str] = []
    # Сначала читаются все клоны: иначе заметку, чья страница лежит в другой теме, пришлось
    # бы объявить отсутствующей — а она есть, просто не там.
    read = {root.name: pages(root) for root in sorted(args.roots)}
    everywhere = {key: address for _, (by_key, _) in read.items() for key, address in by_key.items()}
    by_title = {title: address for _, (_, titles) in read.items() for title, address in titles.items()}
    for root in sorted(args.roots):
        folder = args.vault / root.name
        if not folder.is_dir():
            print(f"нет папки темы в хранилище: {folder.name}", file=sys.stderr)
            continue
        known = read[root.name][0]
        for note in sorted(folder.glob("*.md")):
            if note.name == "README.md":
                continue
            total += 1
            text = note.read_text(encoding="utf-8", errors="replace")
            key = note_key(text)
            address = (known.get(key) or everywhere.get(key)) if key else None
            if address is None:
                address = by_title.get(flat(note.stem))
            if address is None:
                no_page.append(f"{root.name}/{note.stem}")
                continue
            fresh = patched(text, address)
            if fresh is None:
                if FRONT.match(text) is None:
                    no_front.append(f"{root.name}/{note.stem}")
                continue
            touched += 1
            if args.fix:
                note.write_text(fresh, encoding="utf-8")
    tail = f", переписано: {touched}" if args.fix else ""
    print(f"заметок: {total}, без адреса базы: {touched}{tail}")
    if no_page:
        print(f"страницы в базе нет (ключ не найден): {len(no_page)}")
        for name in no_page[:20]:
            print(f"   {name}")
    if no_front:
        print(f"без шапки, пропущены: {len(no_front)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
