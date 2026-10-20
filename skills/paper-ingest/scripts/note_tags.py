#!/usr/bin/env python3
"""Теги разбора из словаря `references/tags.md`: проверить и при нужде поставить.

Первым всегда тег темы (имя папки `<тема>`), дальше 3–7 тегов из словаря, из них ровно один
тег вида работы. Свои слова агента отбрасываются. Если годных тегов меньше трёх, разбор
размечает DeepSeek по названию и разделу «Про что работа» — один запрос, доли цента.
До 20-10-2026 у 737 из 746 разборов был один тег — имя темы, и искать по тегам было нечего.

    note_tags.py FILE...            проверить и поправить на месте
    note_tags.py --check FILE...    только сказать; код 1, если есть что править
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import urllib.request

СЛОВАРЬ_MD = pathlib.Path(__file__).resolve().parent.parent / "references" / "tags.md"
ВИД = ["theory", "method", "empirical-study", "benchmark", "survey", "system"]
ENV = pathlib.Path("/root/.hermes/.env")


def словарь() -> set[str]:
    return set(re.findall(r"^\| `([a-z0-9-]+)` \|", СЛОВАРЬ_MD.read_text(encoding="utf-8"), re.M))


def части(текст: str) -> tuple[list[str], int, str]:
    """Строки шапки, индекс закрывающей `---` и тело."""
    строки = текст.split("\n")
    конец = next(k for k in range(1, len(строки)) if строки[k] == "---")
    return строки, конец, "\n".join(строки[конец + 1:])


def теги_шапки(строки: list[str], конец: int) -> tuple[list[str], int | None, int | None]:
    for i in range(1, конец):
        if m := re.match(r"tags:\s*\[(.*)\]\s*$", строки[i]):
            return [x.strip(" '\"") for x in m[1].split(",") if x.strip()], i, i + 1
        if строки[i].strip() == "tags:":
            j = i + 1
            while j < конец and re.match(r"\s+-\s", строки[j]):
                j += 1
            return [строки[k].split("-", 1)[1].strip(" '\"") for k in range(i + 1, j)], i, j
    return [], None, None


def спросить(название: str, пересказ: str) -> list[str]:
    ключ = re.search(r"^DEEPSEEK_API_KEY=(.+)$", ENV.read_text(), re.M).group(1).strip()
    задание = (
        "Ниже словарь тегов и статья. Выбери из словаря от 3 до 7 тегов: ровно один тег вида "
        f"работы из {ВИД} и 2–6 тегов содержания. Ставь то, ЧЕМУ посвящена статья, а не "
        "упомянутое мимоходом. Только теги из словаря, буква в букву.\n"
        'Ответ JSON: {"tags": ["...", ...]}\n\n'
        f"СЛОВАРЬ:\n{СЛОВАРЬ_MD.read_text(encoding='utf-8')}\n\nСТАТЬЯ:\n{название}\n{пересказ}")
    тело = {"model": "deepseek-flash", "temperature": 0, "max_tokens": 32000,
            "messages": [{"role": "user", "content": задание}],
            "response_format": {"type": "json_object"}}
    req = urllib.request.Request("https://api.deepseek.com/v1/chat/completions",
                                 data=json.dumps(тело).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {ключ}"})
    о = json.loads(urllib.request.urlopen(req, timeout=300).read())
    return json.loads(о["choices"][0]["message"]["content"]).get("tags") or []


def пересказ(тело: str) -> str:
    m = re.search(r"(?ms)^#{2,3} (Про что работа|Коротко)\s*\n(.*?)(?=^#{1,3} )", тело)
    s = m.group(2) if m else тело
    return re.sub(r"\s+", " ", re.sub(r"!\[\[.*?\]\]|!\[.*?\]\(.*?\)", "", s)).strip()[:1800]


def привести(путь: pathlib.Path, можно_спросить: bool = True) -> str | None:
    """Поправить теги файла; вернуть строку для отчёта или None, если всё было в порядке."""
    текст = путь.read_text(encoding="utf-8")
    if not текст.startswith("---\n"):
        return None
    строки, конец, тело = части(текст)
    старые, i, j = теги_шапки(строки, конец)
    тема = путь.parent.parent.name
    слова = словарь()
    годные = [т for т in dict.fromkeys(старые) if т in слова]
    откуда = "проверены"
    if len(годные) < 3 and можно_спросить and ENV.is_file():
        m = re.search(r'(?m)^title:\s*"?(.*?)"?\s*$', "\n".join(строки[:конец]))
        годные = [т for т in dict.fromkeys(спросить(m[1] if m else путь.stem, пересказ(тело)))
                  if т in слова]
        откуда = "поставлены по словарю"
    вид = [т for т in годные if т in ВИД][:1]
    новые = [тема] + вид + [т for т in годные if т not in ВИД and т != тема][:6]
    if новые == старые:
        return None
    блок = ["tags:"] + [f"  - {т}" for т in новые]
    if i is None:
        строки[конец:конец] = блок
    else:
        строки[i:j] = блок
    путь.write_text("\n".join(строки), encoding="utf-8")
    выкинуты = [т for т in старые if т not in новые]
    return (f"теги {откуда}: {' '.join(новые[1:])}"
            + (f" (выкинуты не из словаря: {' '.join(выкинуты)})" if выкинуты else ""))


def main(argv: list[str]) -> int:
    check = "--check" in argv
    грязных = 0
    for a in (x for x in argv if x != "--check"):
        p = pathlib.Path(a)
        if check:
            строки, конец, _ = части(p.read_text(encoding="utf-8"))
            старые, _, _ = теги_шапки(строки, конец)
            слова = словарь()
            if not старые or старые[0] != p.parent.parent.name or \
                    sum(т in слова for т in старые) < 3 or any(т not in слова for т in старые[1:]):
                грязных += 1
                print(f"{p}: {' '.join(старые)}")
        elif r := привести(p):
            print(f"{p}: {r}")
    return 1 if check and грязных else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
