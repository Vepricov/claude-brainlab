#!/usr/bin/env python3
"""Собрать шапку разбора статьи из её BibTeX: заголовок, авторы, год, где, ключ, ссылка.

Шапку писала модель, и она ошибалась правдоподобно. Замерено 07-10-2026 по библиотеке: у трёх
разборов в строке авторов стояли ЧУЖИЕ люди (`tan2025harmony` называл Zeng, Guo и Luo вместо
Tan, Liu, Zhan и ещё четверых), а у 86 разборов в шестнадцати темах там осталась протёкшая
заглушка вида «первые трое, et al., TBD». BibTeX при этом был верен всегда: он приходит с
arXiv как есть.

Отсюда правило: **всё, что есть в BibTeX, в шапку переписывает код, а не модель.** Это и
надёжнее, и дешевле — строка перестаёт стоить токенов.

Из BibTeX берутся: заголовок, авторы, год, место публикации, ключ цитирования и ссылка. Не
берётся только тема: её в BibTeX нет, она у репозитория, и существующее значение сохраняется.

**Авторы приводятся к виду «Имя Фамилия».** Прежняя запись «Tan, Qitao, Liu, Jun, Zhan, Zheng»
неоднозначна: по ней не видно, где кончается один человек и начинается другой, и на этом
спотыкались и читатель, и проверка.

    header_from_bib.py <клон литературы> [ещё клоны...]        показать расхождения
    header_from_bib.py --fix <клон> [...]                      переписать шапки
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

ENTRY = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,(.*?)\n\}", re.S)
FIELD_NAME = re.compile(r"(\w+)\s*=\s*\{")
TITLE_LINE = re.compile(r"^#\s+(.+)$", re.M)
#: Хвост `[^\S\n]*`, а не `\s*`: `\s` съедает перевод строки, и замена слизывала пустую
#: строку после шапки. Без неё «## BibTeX» прилипал к абзацу и перестаёт быть заголовком.
META_LINE = re.compile(r"^\*\*авторы\*\*.*?\*\*тема\*\*[^\S\n]*(.+?)[^\S\n]*$", re.M | re.S)
LINK_LINE = re.compile(r"^\[Открыть источник\]\((.*?)\)[^\S\n]*$", re.M)
#: Диакритика в BibTeX пишется по-разному: `\\'{a}`, `\\'a`, `{\\'{a}}`, `\\"{u}`, `\\"u`.
#: Поэтому ударение снимается общим правилом «команда плюс буква», а не списком написаний.
ACCENT = {"'": "\u0301", "`": "\u0300", '"': "\u0308", "^": "\u0302",
          "~": "\u0303", "c": "\u0327", "v": "\u030c", "u": "\u0306",
          "=": "\u0304", ".": "\u0307", "H": "\u030b", "r": "\u030a"}
#: Буквы, у которых нет диакритики, а есть своя команда.
LETTER = {r"\\o": "ø", r"\\O": "Ø", r"\\l": "ł", r"\\L": "Ł", r"\\ss": "ß",
          r"\\aa": "å", r"\\AA": "Å", r"\\ae": "æ", r"\\AE": "Æ",
          r"\\i": "i", r"\\j": "j"}
ACCENTED = re.compile(r"\\(['`\"^~cvu=.Hr])\s*\{?\\?([a-zA-Z])\}?")


def clean(text: str) -> str:
    """Снять разметку BibTeX: диакритику собрать в готовую букву, скобки убрать."""
    text = ACCENTED.sub(lambda m: unicodedata.normalize("NFC", m.group(2) + ACCENT[m.group(1)]), text)
    for mark, letter in sorted(LETTER.items(), key=lambda kv: -len(kv[0])):
        text = re.sub(mark + r"(?![a-zA-Z])", letter, text)
    return re.sub(r"\s+", " ", re.sub(r"[{}\\]", "", text)).strip()


def fields_of(body: str) -> dict[str, str]:
    """Разобрать поля со счётом скобок: в именах встречается `Richt{\\'{a}}rik`, и
    остановка на первой закрывающей скобке режет фамилию пополам."""
    out: dict[str, str] = {}
    for found in FIELD_NAME.finditer(body):
        depth, i = 1, found.end()
        while i < len(body) and depth:
            if body[i] == "{": depth += 1
            elif body[i] == "}": depth -= 1
            i += 1
        out[found.group(1).lower()] = body[found.end():i - 1]
    return out


def person(raw: str) -> str:
    """«Фамилия, Имя» и «Имя Фамилия» — к одному виду «Имя Фамилия»."""
    raw = clean(raw)
    if "," in raw:
        surname, _, given = raw.partition(",")
        return f"{given.strip()} {surname.strip()}".strip()
    return raw


def year_of(fields: dict[str, str]) -> str:
    """Год из BibTeX. У biblatex-записей (`@online`, посты в блогах) года нет вовсе, а есть
    `date = {2026-04-28}`, поэтому читаем и его: иначе детерминированная шапка затирает
    верный год пустотой."""
    if fields.get("year"):
        return clean(fields["year"])
    date = clean(fields.get("date", ""))
    found = re.match(r"(\d{4})", date)
    return found.group(1) if found else ""


def venue_of(kind: str, fields: dict[str, str]) -> str:
    """Где опубликовано. `organization` и `note` дописаны ради `@online`: у поста в блоге
    издателя нет, а есть площадка, и без них шапка теряла «Random Walk (Substack post)»."""
    for key in ("booktitle", "journal", "publisher", "howpublished", "organization"):
        if fields.get(key):
            place = clean(fields[key])
            note = clean(fields.get("note", ""))
            kind_note = re.match(r"([^.]+?(?:post|preprint|report|thesis))\b", note, re.I)
            return f"{place} ({kind_note.group(1)})" if kind_note else place
    if kind == "misc" and fields.get("eprint"):
        return "Unpublished (arXiv preprint)"
    return "Unpublished (arXiv preprint)" if kind == "misc" else "не указано"


def header_of(text: str) -> dict[str, str] | None:
    found = ENTRY.search(text)
    if not found:
        return None
    kind, key, body = found.group(1).lower(), found.group(2), found.group(3)
    fields = fields_of(body)
    if not fields.get("title") or not fields.get("author"):
        return None
    url = clean(fields.get("url", ""))
    if not url and fields.get("eprint"):
        url = f"https://arxiv.org/abs/{clean(fields['eprint'])}"
    return {
        "title": clean(fields["title"]),
        "authors": ", ".join(person(p) for p in re.split(r"\s+and\s+", fields["author"]) if p.strip()),
        "year": year_of(fields),
        "venue": venue_of(kind, fields),
        "key": key,
        "url": url,
    }


def rebuild(text: str, want: dict[str, str], theme: str) -> str:
    line = (f"**авторы** {want['authors']} · **год** {want['year']} · "
            f"**где** {want['venue']} · **ключ цитирования** `{want['key']}` · **тема** {theme}")
    text = TITLE_LINE.sub(lambda m: f"# {want['title']}", text, count=1)
    text = META_LINE.sub(lambda m: line, text, count=1)
    if want["url"]:
        text = LINK_LINE.sub(lambda m: f"[Открыть источник]({want['url']})", text, count=1)
    return text


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", type=Path, nargs="+")
    parser.add_argument("--fix", action="store_true", help="переписать шапки из BibTeX")
    args = parser.parse_args(argv)

    total = differ = fixed = skipped = 0
    for root in sorted(args.roots):
        for paper in sorted(root.glob("*.md")):
            if paper.name == "README.md":
                continue
            text = paper.read_text(encoding="utf-8")
            want, meta = header_of(text), META_LINE.search(text)
            if not want or not meta:
                skipped += 1
                continue
            total += 1
            fresh = rebuild(text, want, meta.group(1).strip())
            if fresh == text:
                continue
            differ += 1
            was = META_LINE.search(text).group(0)
            now = META_LINE.search(fresh).group(0)
            if was != now:
                print(f"  {root.name}/{paper.stem}")
                print(f"      было:  {was[:96]}")
                print(f"      стало: {now[:96]}")
            if args.fix:
                paper.write_text(fresh, encoding="utf-8")
                fixed += 1
    tail = f", переписано: {fixed}" if args.fix else ""
    print(f"\nразборов: {total}; шапка расходится с BibTeX: {differ}; "
          f"без BibTeX или шапки: {skipped}{tail}")
    return 1 if (differ and not args.fix) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
