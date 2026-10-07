#!/usr/bin/env python3
"""Сверить утверждения статей в базе и в хранилище Обсидиана, и при просьбе — выровнять.

Разбор статьи живёт в двух местах: файлом `<ключ цитирования>.md` в репозитории литературы
темы и заметкой `<Заголовок статьи>.md` в хранилище. Владелец требует, чтобы они совпадали,
и раздел «Что статья утверждает» — та часть, которая расходится первой: её пишут в базу, а в
заметку забывают.

**Сверять по ключу цитирования, а не по заголовку.** 07-10-2026 замерено на теме
`muon-sign-methods`: из семнадцати разборов три имеют разные заголовки в базе и в хранилище.
У `kornilov2025sign` в базе заголовок без подзаголовка, а заметка названа полностью. У
`tao2026when` в базе `$\\ell_1$-norm`, в заметке `ell_1-norm`. У `wang2026olion` в базе
`$\\ell_\\infty$`, в заметке `$\\ell_{\\infty}$`. Сверка по заголовку объявила бы их
отсутствующими, а блоки у всех трёх совпадали слово в слово.

Ключ есть с обеих сторон: в базе это имя файла, в заметке — ключ в блоке BibTeX. Проверено:
у всех семнадцати заметок он на месте.

    literature_mirror.py <клон литературы> <папка темы в хранилище>
    literature_mirror.py ... --apply      перенести блок из базы в заметку
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CLAIMS = re.compile(r"## Что статья утверждает(.*?)(?=\n## |\Z)", re.S)
SHORT = re.compile(r"## Коротко(.*?)(?=\n## |\Z)", re.S)
#: Порядок, которого требует владелец: BibTeX, «Коротко», утверждения, и только потом разбор.
#: В заметках хранилища раздела «Коротко» не было вовсе, а утверждения стояли сразу за BibTeX.
AFTER_BIB = re.compile(r"(## BibTeX.*?```\s*\n)", re.S)
BIBKEY = re.compile(r"@\w+\{([^,\s}]+)\s*,")
TITLE_FIELD = re.compile(r"(?m)^\s*title\s*=\s*\{+(.+?)\}*,?\s*$")
#: Куда вставлять блок, если его в заметке нет: перед первым из этих разделов. Порядок
#: важен — в хранилище тело разложено иначе, чем в базе, и «AI Explanation» встречается
#: раньше плоских разделов.
BEFORE = ("## AI Explanation", "## Посекционный разбор", "## 1. Общий обзор",
          "## Критическая оценка", "## Математика и формулы")
#: Врезка Papers with Code, которую в заметки хранилища ставит pwc_batch_inject.py из навыка
#: paper-ingest. Она стоит перед «AI Explanation», то есть после вставленного нами «Коротко»
#: и внутри его участка: до следующего «## » её ничто не отделяет. Поэтому замена «Коротко»
#: целиком стирала её, и 17 заметок потеряли врезку молча. Врезку вынимаем из текста до
#: правки и возвращаем перед разбором, где её и ждёт сам навык.
PWC = re.compile(r"(?ms)^> \[!abstract\] TL;DR \(Papers with Code\)\s*\n(?:>.*\n)*")


def claims(text: str) -> str | None:
    found = CLAIMS.search(text)
    return found.group(0).rstrip() if found else None


def short(text: str) -> str | None:
    found = SHORT.search(text)
    return found.group(0).rstrip() if found else None


#: Порядок разделов, который требует владелец. Сверять его обязательно: содержимое может
#: совпадать с базой дословно, а утверждения при этом стоять выше «Коротко». Именно так и
#: вышло в 16 заметках — сверка говорила «совпадает», потому что смотрела только текст.
ORDER = ("## BibTeX", "## Коротко", "## Что статья утверждает")


def in_order(text: str) -> bool:
    present = [head for head in ORDER if head in text]
    return present == sorted(present, key=text.find)


def same(one: str | None, two: str | None) -> bool:
    """Сравнение без оглядки на то, как расставлены пробелы и переводы строк."""
    flat = lambda text: re.sub(r"\s+", " ", text).strip() if text else text
    return flat(one) == flat(two)


def letters(text: str) -> str:
    return re.sub(r"[^0-9a-zA-Zа-яёА-ЯЁ]+", "", text).lower()


def title_of(text: str) -> str:
    found = TITLE_FIELD.search(text)
    return letters(found.group(1)) if found else ""


def notes_by_key(folder: Path) -> tuple[dict[str, list[Path]], list[str]]:
    """Заметки по ключу цитирования; у ключа может быть больше одной заметки.

    Два разных случая, и путать их нельзя. Ключ собирается как
    `{фамилия}{год}{первое слово}`, поэтому у разных статей он совпадает: «Parametric
    Retrieval Augmented Generation» Weihang Su и «Parametric Retrieval-Augmented
    Generation using Latent Routing of LoRA Adapters» Zhan Su оба дают
    `su2025parametric`. А рядом с настоящим разбором может лежать черновик с тем же
    BibTeX: в `muon-at-scale` это «— разбор Opus» и «— разбор codex». Поэтому ключ
    ведёт к списку, а выбирает уже `pick`, по заголовку статьи.
    """
    found: dict[str, list[Path]] = {}
    clash: list[str] = []
    for note in sorted(folder.glob("*.md")):
        if note.name == "README.md":
            continue
        text = note.read_text(encoding="utf-8")
        key = BIBKEY.search(text)
        if not key:
            continue
        name = key.group(1)
        if name in found:
            clash.append(f"{name}: один ключ у «{found[name][0].name}» и «{note.name}»")
        found.setdefault(name, []).append(note)
    return found, clash


def pick(notes: list[Path], want_title: str) -> Path | None:
    """Какая из заметок с одним ключом отвечает этому разбору.

    Сначала по полю `title` из BibTeX: так разводятся две разные статьи с одним ключом.
    Среди оставшихся основная та, что названа заголовком статьи, а не «— разбор Opus»:
    двоеточие в имени файла невозможно, поэтому сверяем по буквам и цифрам. Если
    основной нет, берётся первая, и столкновение всё равно напечатано выше.
    """
    same_paper = [n for n in notes if title_of(n.read_text(encoding="utf-8")) == want_title]
    pool = same_paper or (notes if len(notes) == 1 else [])
    if not pool:
        return None
    for note in pool:
        if letters(note.stem) == want_title:
            return note
    return pool[0]


def put(note: Path, block: str, head: str | None) -> str:
    """Вписать «Коротко» и утверждения в заметку, всегда в требуемом порядке.

    Порядок задан владельцем: BibTeX, «Коротко», «Что статья утверждает», затем разбор.
    Прежняя правка меняла каждый раздел НА МЕСТЕ, если он в заметке уже был, и потому
    сохраняла неверный порядок: в 16 заметках утверждения стояли выше «Коротко», а в
    одной выше самого BibTeX. Поэтому оба раздела сначала вырезаются, а потом ставятся
    заново за блоком BibTeX. Врезку Papers with Code вынимаем до правки и возвращаем
    перед разбором: она стоит внутри участка «Коротко» и иначе стиралась.
    """
    text = note.read_text(encoding="utf-8")
    how = []

    keep = PWC.search(text)
    pwc = keep.group(0).rstrip() if keep else None
    if pwc:
        text = PWC.sub("", text, count=1)

    was_short = SHORT.search(text)
    was_claims = CLAIMS.search(text)
    if was_short:
        text = SHORT.sub("", text, count=1)
    if was_claims:
        text = CLAIMS.sub("", text, count=1)

    wedge = "\n\n".join(part for part in (head, block) if part) + "\n"
    bib = AFTER_BIB.search(text)
    if bib:
        text = text[:bib.end()].rstrip() + "\n\n" + wedge + "\n" + text[bib.end():].lstrip("\n")
        where = "за BibTeX"
    else:
        for head_name in BEFORE:
            if head_name in text:
                text = text.replace(head_name, wedge + "\n" + head_name, 1)
                where = f"перед «{head_name[3:]}»"
                break
        else:
            text = text.rstrip() + "\n\n" + wedge
            where = "в конец"
    how.append(f"«Коротко» и утверждения поставлены {where}"
               if head else f"утверждения поставлены {where}")
    if was_short and was_claims and was_short.start() > was_claims.start():
        how.append("порядок исправлен: «Коротко» было ниже утверждений")

    if pwc:
        for head_name in BEFORE:
            if head_name in text:
                text = text.replace(head_name, pwc + "\n\n" + head_name, 1)
                break
        else:
            text = text.rstrip() + "\n\n" + pwc + "\n"
        how.append("врезка Papers with Code сохранена")

    text = re.sub(r"\n{4,}", "\n\n\n", text)
    note.write_text(text, encoding="utf-8")
    return ", ".join(how)



FRONT = re.compile(r"\A---\n.*?\n---\n", re.S)


def whole(note: Path, source: str) -> str:
    """Переписать заметку целиком телом разбора из базы.

    Раздельный перенос «Коротко» и утверждений оставлял тело заметки прежним, а оно у
    хранилища своё и давно отстало: у `mcgee2026trust` в базе 76 КБ разбора по разделам,
    написанным под статью, а в заметке висел прежний «AI Explanation», и в пятнадцати
    заметках он к тому же оказался пустым — остался заголовок и одинокая решётка.
    Поэтому тело берётся из базы целиком.

    Сохраняется только то, чего в базе нет и быть не может: frontmatter хранилища (теги,
    ключи Zotero, поля Papers with Code) и сама врезка Papers with Code.
    """
    text = note.read_text(encoding="utf-8")
    front = FRONT.match(text)
    keep = PWC.search(text)
    body = source[source.index("# "):] if "# " in source else source
    # Заметка не имеет права похудеть. Замерено на 267 разборах: при переносе целиком 191
    # из них стала БОЛЬШЕ ОДНОГО РАЗА меньше — в хранилище лежит свой «AI Explanation» и
    # свои «Прериквизиты», которых в базе нет вовсе. Один такой проход уже стоил 11 тысяч
    # удалённых строк. Поэтому тело переносится только туда, где его в заметке нет.
    if len(body.encode()) <= len(text.encode()):
        return (f"тело НЕ перенесено: в заметке {len(text.encode())} б, в базе "
                f"{len(body.encode())} б — перенос только дописывает, но не урезает")
    out = (front.group(0) if front else "") + body.rstrip() + "\n"
    if keep:
        pwc = keep.group(0).rstrip()
        for head_name in BEFORE + ("## Рядом в библиотеке",):
            if head_name in out:
                out = out.replace(head_name, pwc + "\n\n" + head_name, 1)
                break
        else:
            out = out.rstrip() + "\n\n" + pwc + "\n"
    note.write_text(out, encoding="utf-8")
    return f"тело перенесено из базы целиком ({len(body)} б)"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=Path, help="клон репозитория литературы темы")
    parser.add_argument("vault", type=Path, help="папка темы в хранилище Обсидиана")
    parser.add_argument("--apply", action="store_true",
                        help="перенести блок из базы в заметку")
    parser.add_argument("--body", action="store_true",
                        help="переносить разбор целиком, а не только «Коротко» и утверждения")
    args = parser.parse_args(argv)

    notes, clash = notes_by_key(args.vault)
    papers = [p for p in sorted(args.base.glob("*.md")) if p.name != "README.md"]
    if not papers:
        sys.exit(f"в {args.base} нет разборов")

    agree = fixed = 0
    trouble: list[str] = list(clash)
    for paper in papers:
        key = paper.stem
        source = paper.read_text(encoding="utf-8")
        block, head = claims(source), short(source)
        if block is None:
            trouble.append(f"{key}: в базе нет раздела «Что статья утверждает»")
            continue
        note = pick(notes.get(key, []), title_of(source))
        if note is None:
            trouble.append(f"{key}: в хранилище нет заметки с этим ключом и этим заголовком")
            continue
        # Врезку Papers with Code убираем перед сверкой: она есть только в хранилище, стоит
        # внутри участка утверждений, и иначе каждая обогащённая заметка читается как
        # разошедшаяся с базой.
        there = PWC.sub("", note.read_text(encoding="utf-8"))
        if args.body:
            mine = FRONT.sub("", PWC.sub("", there)).strip()
            theirs = source[source.index("# "):].strip() if "# " in source else source.strip()
            if same(mine, theirs):
                agree += 1
                continue
        elif (same(block, claims(there)) and (head is None or same(head, short(there)))
                and in_order(there)):
            agree += 1
            continue
        if note.stat().st_nlink > 1:
            # Статья, попавшая в две темы, по правилу хранилища лежит одной заметкой с
            # жёсткой ссылкой. В базе же у каждой темы свой репозиторий и своя копия
            # разбора, и копии расходятся: у `allaire2026zeroth` заголовки утверждений
            # переписаны дважды и независимо, а «тема» в шапке по построению разная.
            # Одна заметка не может быть равна обеим, поэтому её не трогаем и говорим вслух.
            trouble.append(f"{key}: «{note.name}» — одна заметка на несколько тем "
                           f"(жёсткая ссылка), выравнивать нечем, нужно решение владельца")
            continue
        if args.apply:
            how = whole(note, source) if args.body else put(note, block, head)
            trouble.append(f"{key}: {how} в «{note.name}»")
            fixed += 1
        else:
            trouble.append(f"{key}: блок в заметке «{note.name}» расходится с базой")

    for line in trouble:
        print(" ", line)
    tail = f", выровнено: {fixed}" if args.apply else ""
    print(f"разборов: {len(papers)}, совпадают: {agree}, расходятся или без пары: "
          f"{len(trouble) - fixed if args.apply else len(trouble)}{tail}")
    return 1 if (len(trouble) - fixed if args.apply else trouble) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
