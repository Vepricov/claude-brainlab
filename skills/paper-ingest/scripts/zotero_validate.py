#!/usr/bin/env python3
"""Проверить базу Zotero на дефекты, обрывающие синхронизацию.

Зачем это существует. `paper-ingest` пишет в Zotero напрямую в SQLite, минуя
приложение, и потому не знает про ограничения, которые Zotero соблюдает сам.
Сервер такие объекты отвергает и ОБРЫВАЕТ СИНХРОНИЗАЦИЮ ЦЕЛИКОМ — молча, на
первом же битом объекте. Библиотека простояла так с 27-04 по 30-08-2026: 932
записи из 1070 не уехали, и заметили это только через четыре месяца.

Что проверяется:

* **Ключи.** Алфавит Zotero — латиница без `O` и цифры 2-9. Ни нулей, ни
  единиц: их нельзя спутать с `O` и `I`. Ключи вида `MUON0001` сервер
  отвергает.
* **Тип авторства.** Допустимые сочетания «тип записи / тип авторства» лежат в
  `itemTypeCreatorTypes`. Для `preprint` это author, contributor, editor,
  reviewedAuthor, translator. Ошибка возникает, когда `creatorTypeID` берут
  константой: 1 это `artist`, а нужный `author` под номером 10.
* **Поля.** Допустимые поля типа записи лежат в `itemTypeFields`.
* **Ссылки из Obsidian.** Переименование ключа чинит Zotero, но молча
  обрывает `zotero://select/library/items/<KEY>` в заметках: ссылка
  остаётся кликабельной и ведёт в никуда. Проверяется всё хранилище.

    python3 zotero_validate.py            # только проверить
    python3 zotero_validate.py --fix      # починить (Zotero должен быть ЗАКРЫТ)
"""
from __future__ import annotations

import pathlib
import random
import re
import sqlite3
import sys

DB = pathlib.Path.home() / "Zotero" / "zotero.sqlite"
VAULT = (pathlib.Path.home() / "Library/Mobile Documents"
         / "iCloud~md~obsidian/Documents/shkodnik1917")
ZOTERO_LINK = re.compile(r"zotero://select/library/items/([A-Z0-9]{8})")
KEY_ALPHABET = "ABCDEFGHIJKLMNPQRSTUVWXYZ23456789"
VALID_KEY = re.compile(rf"^[{KEY_ALPHABET}]{{8}}$")


def bad_keys(c: sqlite3.Cursor) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for table in ("items", "collections"):
        c.execute(f"SELECT key FROM {table}")
        bad = [r[0] for r in c.fetchall() if r[0] and not VALID_KEY.match(r[0])]
        if bad:
            out[table] = bad
    return out


def bad_creators(c: sqlite3.Cursor) -> list[tuple]:
    c.execute("""
        SELECT i.key, it.typeName, ct.creatorType, COUNT(*)
        FROM itemCreators ic
        JOIN items i         ON i.itemID = ic.itemID
        JOIN itemTypes it    ON it.itemTypeID = i.itemTypeID
        JOIN creatorTypes ct ON ct.creatorTypeID = ic.creatorTypeID
        WHERE NOT EXISTS (SELECT 1 FROM itemTypeCreatorTypes tc
                          WHERE tc.itemTypeID = i.itemTypeID
                            AND tc.creatorTypeID = ic.creatorTypeID)
        GROUP BY 1, 2, 3""")
    return c.fetchall()


def bad_fields(c: sqlite3.Cursor) -> list[tuple]:
    c.execute("""
        SELECT it.typeName, f.fieldName, COUNT(*)
        FROM itemData d
        JOIN items i      ON i.itemID = d.itemID
        JOIN itemTypes it ON it.itemTypeID = i.itemTypeID
        JOIN fields f     ON f.fieldID = d.fieldID
        WHERE NOT EXISTS (SELECT 1 FROM itemTypeFields tf
                          WHERE tf.itemTypeID = i.itemTypeID AND tf.fieldID = d.fieldID)
        GROUP BY 1, 2""")
    return c.fetchall()


def fix(con: sqlite3.Connection) -> None:
    c = con.cursor()

    c.execute("SELECT key FROM items UNION SELECT key FROM collections")
    taken = {r[0] for r in c.fetchall() if r[0]}
    rng = random.Random()
    for table, keys in bad_keys(c).items():
        for old in keys:
            while True:
                new = "".join(rng.choice(KEY_ALPHABET) for _ in range(8))
                if new not in taken:
                    taken.add(new)
                    break
            c.execute(f"UPDATE {table} SET key=?, version=0, synced=0 WHERE key=?", (new, old))
            print(f"  ключ {table}: {old} -> {new}")
            print("    ВНИМАНИЕ: ссылки zotero:// на старый ключ в хранилище надо переписать вручную")

    # тип авторства: всё недопустимое сводим к author, это всегда авторы статей
    c.execute("SELECT creatorTypeID FROM creatorTypes WHERE creatorType='author'")
    author = c.fetchone()[0]
    c.execute("""SELECT ic.rowid FROM itemCreators ic JOIN items i ON i.itemID=ic.itemID
                 WHERE NOT EXISTS (SELECT 1 FROM itemTypeCreatorTypes tc
                   WHERE tc.itemTypeID=i.itemTypeID AND tc.creatorTypeID=ic.creatorTypeID)""")
    rows = [r[0] for r in c.fetchall()]
    if rows:
        c.executemany("UPDATE itemCreators SET creatorTypeID=? WHERE rowid=?",
                      [(author, r) for r in rows])
        print(f"  тип авторства приведён к author: строк {len(rows)}")
    con.commit()


def dead_links(c: sqlite3.Cursor) -> list[tuple[str, str]]:
    """Ссылки zotero:// в хранилище, ведущие на несуществующую запись."""
    if not VAULT.is_dir():
        return []
    live = {k for (k,) in c.execute(
        "SELECT key FROM items WHERE itemID NOT IN (SELECT itemID FROM deletedItems)")}
    out: list[tuple[str, str]] = []
    for note in VAULT.rglob("*.md"):
        if "/.trash/" in str(note):
            continue
        try:
            text = note.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for key in ZOTERO_LINK.findall(text):
            # XXXXXXXX и подобное — плейсхолдеры в документации, а не ссылки:
            # настоящий ключ Zotero случаен, из одного символа не состоит
            if key not in live and VALID_KEY.match(key) and len(set(key)) > 1:
                out.append((str(note.relative_to(VAULT)), key))
    return out


def main() -> int:
    if not DB.is_file():
        print("базы Zotero нет:", DB)
        return 2
    do_fix = "--fix" in sys.argv
    con = sqlite3.connect(DB if do_fix else f"file:{DB}?immutable=1", uri=not do_fix)
    c = con.cursor()

    problems = 0
    keys = bad_keys(c)
    for table, bad in keys.items():
        problems += len(bad)
        print(f"НЕВАЛИДНЫЕ КЛЮЧИ в {table}: {len(bad)} — {', '.join(bad[:5])}"
              f"{' …' if len(bad) > 5 else ''}")
    for key, tname, ctype, n in bad_creators(c):
        problems += n
        print(f"НЕДОПУСТИМЫЙ ТИП АВТОРСТВА: {key} {tname} <- {ctype} ({n})")
    for tname, fname, n in bad_fields(c):
        problems += n
        print(f"НЕДОПУСТИМОЕ ПОЛЕ: {tname} <- {fname} ({n})")

    # Битые ссылки чинить автоматически нельзя: нужный ключ ищется по названию,
    # и подставить не тот хуже, чем оставить обрыв. Сообщаем владельцу.
    for note, key in dead_links(c):
        print(f"БИТАЯ ССЫЛКА zotero://: {key} <- {note}")

    if not problems:
        print("Zotero: дефектов, ломающих синхронизацию, не найдено")
        con.close()
        return 0

    if do_fix:
        print("\nчиню…")
        fix(con)
        print("готово")
    else:
        print(f"\nвсего дефектов: {problems}. Запусти с --fix при ЗАКРЫТОМ Zotero.")
    con.close()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
