#!/usr/bin/env python3
"""Сторож свода: правила одни на всех, и это проверяется, а не обещается.

Свод (`docs/lab/canon.md`) объявляет каждое правило именем и строкой «проверяется». Сторож
смотрит три вещи, каждая из которых однажды уже расходилась молча:

1. копии свода совпадают с источником — иначе агент на одной машине работает по одним
   правилам, а на другой по другим;
2. места, которые свод называет проверяющими (`sweep.py`, `проверить_числа`, проход), в коде
   существуют — иначе «проверяется» становится обещанием;
3. те, кто должен на свод ссылаться — правило сессии, навык, хук конца хода, — ссылаются.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CANON = ROOT / "docs" / "lab" / "canon.md"
HOME = pathlib.Path.home()

COPIES = (HOME / ".claude" / "rules" / "lab-canon.md",
          HOME / ".claude" / "skills" / "lab-knowledge" / "references" / "canon.md",
          HOME / ".agents" / "skills" / "lab-knowledge" / "references" / "canon.md",
          ROOT / "skills" / "lab-knowledge" / "references" / "canon.md")

MUST_POINT = (HOME / ".claude" / "rules" / "lab.md",
              HOME / ".claude" / "skills" / "lab-knowledge" / "SKILL.md",
              HOME / ".claude" / "scripts" / "mempalace-obsidian-hook.py")

#: Где искать то, что свод называет проверяющим. Серверное лежит не в репозитории, поэтому
#: ищется по копии, которая в нём есть.
CODE = (ROOT / "services" / "lab-knowledge" / "scripts",
        ROOT / "services" / "lab-knowledge" / "src" / "lab_knowledge",
        ROOT / "scripts")


def rules(text: str) -> list[tuple[str, str]]:
    found = []
    for block in re.split(r"\n### ", text)[1:]:
        name = re.match(r"`([a-z-]+)`", block)
        if name:
            found.append((name.group(1), block))
    return found


def mentioned_code(block: str) -> list[str]:
    """Имена из строки «проверяется»: `sweep.py`, `проверить_числа`, `gitlab_cards.py`."""
    line = next((row for row in block.splitlines() if row.startswith("*проверяется")), "")
    return re.findall(r"`([A-Za-zА-Яа-я_][\w.]*)`", line)


def main() -> int:
    text = CANON.read_text(encoding="utf-8")
    bad: list[str] = []

    for copy in COPIES:
        if not copy.is_file():
            bad.append(f"копии свода нет: {copy}")
        elif copy.read_text(encoding="utf-8") != text:
            bad.append(f"копия свода разошлась с источником: {copy}")

    for pointer in MUST_POINT:
        if "lab-canon.md" not in pointer.read_text(encoding="utf-8") \
                and "references/canon.md" not in pointer.read_text(encoding="utf-8"):
            bad.append(f"не ссылается на свод: {pointer}")

    haystack = ""
    for place in CODE:
        for file in place.rglob("*.py"):
            haystack += file.read_text(encoding="utf-8", errors="replace")
        for file in place.rglob("*.sh"):
            haystack += file.read_text(encoding="utf-8", errors="replace")

    all_rules = rules(text)
    unchecked = 0
    for name, block in all_rules:
        if "*не проверяется машиной" in block:
            unchecked += 1
            continue
        for thing in mentioned_code(block):
            if thing.endswith((".py", ".sh")):
                if not any((place / thing).exists() or list(place.rglob(thing))
                           for place in CODE):
                    bad.append(f"{name}: назван проверяющим `{thing}`, а такого файла нет")
            elif thing not in haystack:
                bad.append(f"{name}: назван проверяющим `{thing}`, а в коде его нет")

    print(f"правил в своде: {len(all_rules)}, из них держатся на прочтении: {unchecked}")
    for line in bad:
        print("  ✘", line)
    print("расхождений:", len(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
