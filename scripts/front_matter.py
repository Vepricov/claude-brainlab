#!/usr/bin/env python3
"""Свойства разбора — во frontmatter, как в хранилище владельца.

Владелец 07-10-2026, глядя на панель свойств Обсидиана: «давай делать, как у меня в
обсидиане… убирать этот „Открыть источник“, это хуйня. Вот видишь, там url, code_url,
project_url. Давайте всё вот это так хранить, и на GitLab тоже».

Поэтому строка `[Открыть источник](…)` из тела уходит: адрес живёт в свойстве `url`, где
его видно панелью и где по нему можно щёлкнуть. А у разборов в базе появляется тот же
набор свойств, что у заметок, и в том же порядке.

Откуда что берётся:

- `title`, `url`, `publication` — из блока BibTeX разбора, детерминированно. `url` при его
  отсутствии собирается из `eprint`, `publication` — из `booktitle`/`journal`/`publisher`/
  `howpublished`/`organization`, а у `@misc` с `eprint` это «Unpublished (arXiv preprint)».
- `zotero_key`, `zotero_link`, `code_url`, `project_url` — из заметки хранилища: в BibTeX их
  нет и быть не может. Нет заметки — поля ставятся пустыми, но ставятся: пустое свойство
  видно в панели и его заполняют, а отсутствующее не видно никому.
- `tags` — слаг темы. Ключ `tags` по-английски и значение в английском kebab-case: Обсидиан
  распознаёт только английское имя, переведённое молча становится обычным свойством.
- `updated` — в формате ДД-ММ-ГГГГ. Уже стоящее значение не трогается.

    front_matter.py <клон литературы>... [--хранилище <папка темы>] [--fix]
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from header_from_bib import header_of  # noqa: E402

FRONT = re.compile(r"\A---\n(.*?)\n---\n", re.S)
TITLE = re.compile(r"(?m)^#\s+(.+)$")
LINK_LINE = re.compile(r"(?m)^\[Открыть источник\]\([^)]*\)[^\S\n]*\n\n?")
BIBKEY = re.compile(r"@\w+\{([^,\s}]+)\s*,")
#: Порядок полей ровно такой, как в панели свойств у владельца.
ORDER = ("title", "zotero_key", "zotero_link", "url", "code_url", "project_url",
         "publication", "tags", "updated")
#: Эти четыре в BibTeX не живут: их знает только хранилище.
FROM_VAULT = ("zotero_key", "zotero_link", "code_url", "project_url")


def read_front(text: str) -> dict[str, str]:
    """Плоское чтение frontmatter. Список `tags` сводится к одной строке через запятую."""
    found = FRONT.match(text)
    if not found:
        return {}
    out: dict[str, str] = {}
    key = None
    for line in found.group(1).splitlines():
        if line.startswith("  - ") and key:
            out[key] = (out[key] + "," if out[key] else "") + line[4:].strip()
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        out[key] = value.strip().strip('"')
    return out


def quoted(value: str) -> str:
    """YAML-безопасная запись, но без кавычек там, где их нет у владельца.

    Двоеточие само по себе строку не ломает: в YAML разделителем его делает ПРОБЕЛ после
    него. Поэтому `url: https://arxiv.org/abs/2610.07497` и
    `zotero_link: zotero://select/...` пишутся без кавычек — именно так они стоят в
    хранилище, и панель свойств Обсидиана показывает их ссылками. Кавычки остаются там,
    где без них YAML читается неверно: пусто, двоеточие с пробелом, ведущий спецсимвол,
    краевые пробелы, решётка после пробела (комментарий).
    """
    if value == "":
        return '""'
    if (re.search(r":\s", value) or re.search(r"\s#", value)
            or value[0] in "#&*!|>%@`[]{}-?," or value != value.strip()):
        return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'
    return value


def render(fields: dict[str, str], theme: str) -> str:
    lines = ["---"]
    for key in ORDER:
        if key == "tags":
            tags = [tag for tag in (fields.get("tags") or theme).split(",") if tag.strip()]
            lines.append("tags:")
            lines += [f"  - {tag.strip()}" for tag in tags]
            continue
        lines.append(f"{key}: {quoted(fields.get(key, ''))}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def notes_by_key(folder: Path | None) -> dict[str, Path]:
    if folder is None or not folder.is_dir():
        return {}
    found: dict[str, Path] = {}
    for note in sorted(folder.glob("*.md")):
        if note.name == "README.md":
            continue
        key = BIBKEY.search(note.read_text(encoding="utf-8", errors="replace"))
        if key:
            found[key.group(1)] = note
    return found


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("roots", type=Path, nargs="+")
    parser.add_argument("--хранилище", type=Path, dest="vault", default=None)
    parser.add_argument("--fix", action="store_true")
    args = parser.parse_args(argv)

    today = datetime.date.today().strftime("%d-%m-%Y")
    total = touched = 0
    no_bib: list[str] = []
    for root in sorted(args.roots):
        notes = notes_by_key(args.vault)
        for paper in sorted(root.glob("*.md")):
            if paper.name == "README.md":
                continue
            total += 1
            text = paper.read_text(encoding="utf-8")
            want = header_of(text)
            fields = read_front(text)
            if want:
                fields["title"] = want["title"]
                fields["url"] = want["url"]
                fields["publication"] = want["venue"]
            else:
                # Разбор без блока BibTeX. Таких 30, и все в непройденных темах: отчёты
                # лабораторий, посты и старые статьи, у которых ключа цитирования нет
                # вовсе. Бросать их нельзя — тогда у них не будет и свойств, — поэтому
                # заголовок берётся из строки `# `, а адрес из `[Открыть источник]`,
                # которую мы как раз и убираем из тела.
                head = TITLE.search(text)
                link = LINK_LINE.search(text)
                fields.setdefault("title", head.group(1).strip() if head else paper.stem)
                fields.setdefault("url", re.search(r"\(([^)]*)\)", link.group(0)).group(1)
                               if link else "")
                fields.setdefault("publication", "")
                no_bib.append(f"{root.name}/{paper.stem}")
            fields.setdefault("updated", today)
            note = notes.get(paper.stem)
            if note is not None:
                theirs = read_front(note.read_text(encoding="utf-8", errors="replace"))
                for key in FROM_VAULT:
                    fields.setdefault(key, theirs.get(key, ""))
            for key in FROM_VAULT:
                fields.setdefault(key, "")
            body = FRONT.sub("", text)
            body = LINK_LINE.sub("", body, count=1)
            fresh = render(fields, root.name) + body.lstrip("\n")
            if fresh == text:
                continue
            touched += 1
            if args.fix:
                paper.write_text(fresh, encoding="utf-8")
    tail = f", переписано: {touched}" if args.fix else ""
    print(f"разборов: {total}, со свойствами не как надо: {touched}{tail}")
    if no_bib:
        print(f"без блока BibTeX (свойства собраны из заголовка и ссылки): {len(no_bib)}")
        for name in no_bib:
            print(f"   {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
