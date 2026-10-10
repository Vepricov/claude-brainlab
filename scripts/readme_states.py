#!/usr/bin/env python3
"""Привести таблицу состояний в README работы в соответствие со страницами утверждений.

Состояние утверждения живёт в трёх местах: поле `status` на странице, русская строка там же
и строка в таблице README работы. Главное — поле (свод, `status-by-criterion`), остальные два
пересказывают его. Этот проход переписывает третье место по первому.

Он же снимает конфликт слияния в этой таблице. Конфликт здесь возникает постоянно и по одной
причине: две ветки правят состояния разных утверждений, а строки лежат рядом. Разрешать его
руками бессмысленно — ни одна из сторон не авторитетна, авторитетны страницы.

    readme_states.py <клон>            переписать таблицу по страницам
    readme_states.py <клон> --dry-run  только сказать, что разошлось
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

#: Слово состояния. Набор закрыт и замерен по базе; он же стоит в своде.
WORD = {"draft": "черновик", "testing": "проверяется", "supported": "подтверждено",
        "refuted": "опровергнуто", "inconclusive": "без вывода"}
CODE = re.compile(r"\[([HDSEF]-[A-Z]{2,4}-\d{3})")


def states(root: pathlib.Path) -> dict[str, str]:
    out = {}
    for folder in sorted((root / "claims").glob("*")):
        page = folder / "README.md"
        if not page.is_file():
            continue
        field = re.search(r"^status:\s*(\S+)", page.read_text(encoding="utf-8"), re.M)
        if field:
            out[folder.name] = WORD.get(field.group(1), field.group(1))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", type=pathlib.Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    page = args.root / "README.md"
    if not page.is_file():
        sys.exit(f"нет {page}")
    truth = states(args.root)
    if not truth:
        sys.exit("в клоне нет ни одного утверждения")

    text = page.read_text(encoding="utf-8")
    conflict = "<<<<<<<" in text
    out, drop = [], False
    changed = []
    for line in text.splitlines(keepends=True):
        # Конфликт разрешается в пользу страниц, а не одной из сторон: обе половины
        # оставляются как есть, а состояния потом переписываются по `status`. Вторая
        # половина выбрасывается, потому что строки в ней те же самые.
        if line.startswith("<<<<<<<"):
            drop = False
            continue
        if line.startswith("======="):
            drop = True
            continue
        if line.startswith(">>>>>>>"):
            drop = False
            continue
        if drop:
            continue
        found = CODE.search(line)
        if found and line.lstrip().startswith("|") and found.group(1) in truth:
            cells = line.rstrip("\n").split("|")
            was = cells[-2].strip()
            want = truth[found.group(1)]
            # Хвост после `·` или запятой — пометка о публикации, её сохраняем.
            tail = ""
            for sep in ("·", ","):
                if sep in was:
                    tail = sep + was.split(sep, 1)[1]
                    was = was.split(sep, 1)[0].strip()
                    break
            if was != want:
                changed.append(f"{found.group(1)}: «{was}» -> «{want}»")
            cells[-2] = f" {want}{tail} "
            line = "|".join(cells) + "\n"
        out.append(line)

    for line in changed:
        print(f"  {line}")
    print(f"{'конфликт снят, ' if conflict else ''}строк поправлено: {len(changed)}")
    if not args.dry_run:
        page.write_text("".join(out), encoding="utf-8")
        assert "<<<<<<<" not in page.read_text(encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
