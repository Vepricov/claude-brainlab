#!/usr/bin/env python3
"""Перенести разбор в другую тему: заметка, вложения и все ссылки на них.

    move_note.py 2609.38095 zo-estimators [--dry-run]
"""
import pathlib
import sys
import os, re, shutil, sys

# Где лежат разборы, знает один модуль: `vault_paths`. Захардкоженный путь к хранилищу
# iCloud после переезда 16-10-2026 вёл в несуществующую папку, и запись уходила в пустоту.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from vault_paths import VAULT, temy, tema_put, vse_papki  # noqa: E402

V = str(VAULT)


def адрес(тема):
    """Путь папки разборов темы от корня хранилища: так его пишут вики-ссылки."""
    return os.path.relpath(str(tema_put(тема)), V)


def найти(arxiv):
    for тема, mesto in temy().items():
        d = str(mesto)
        for f in os.listdir(d):
            if not f.endswith(".md") or f == "README.md":
                continue
            try:
                t = open(os.path.join(d, f), encoding="utf-8").read(4000)
            except OSError:
                continue
            if re.search(r"arxiv\.org/abs/" + re.escape(arxiv) + r"\b", t):
                return тема, f
    return None, None


def main():
    arxiv, куда = sys.argv[1], sys.argv[2]
    сухой = "--dry-run" in sys.argv
    откуда, имя = найти(arxiv)
    if not откуда:
        sys.exit(f"{arxiv}: заметки нет в хранилище")
    if откуда == куда:
        print(f"{arxiv}: уже в {куда}")
        return
    if tema_put(куда) is None:
        sys.exit(f"темы {куда} нет")
    print(f"{arxiv}: {откуда} -> {куда}   {имя[:60]}")
    if сухой:
        return
    из, в = str(tema_put(откуда)), str(tema_put(куда))
    shutil.move(os.path.join(из, имя), os.path.join(в, имя))
    пары = {f"{адрес(откуда)}/{имя[:-3]}": f"{адрес(куда)}/{имя[:-3]}"}
    вложения = os.path.join(из, "_attachments", arxiv)
    if os.path.isdir(вложения):
        цель = os.path.join(в, "_attachments", arxiv)
        os.makedirs(os.path.dirname(цель), exist_ok=True)
        shutil.move(вложения, цель)
        пары[f"{адрес(откуда)}/_attachments/{arxiv}/"] = f"{адрес(куда)}/_attachments/{arxiv}/"
    правок = файлов = 0
    for r, dd, fs in os.walk(V):
        dd[:] = [x for x in dd if not x.startswith(".")]
        for x in fs:
            if not x.endswith(".md"):
                continue
            p = os.path.join(r, x)
            try:
                s = open(p, encoding="utf-8").read()
            except OSError:
                continue
            новый = s
            for a, b in пары.items():
                новый = новый.replace(a, b)
            if новый != s:
                правок += sum(s.count(a) for a in пары)
                файлов += 1
                open(p, "w", encoding="utf-8").write(новый)
    print(f"   ссылок переписано {правок} в {файлов} файлах")


if __name__ == "__main__":
    main()
