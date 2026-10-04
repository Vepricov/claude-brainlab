#!/usr/bin/env python3
"""Перенести разбор в другую тему: заметка, вложения и все ссылки на них.

    move_note.py 2609.38095 zo-estimators [--dry-run]
"""
import os, re, shutil, sys

V = os.path.expanduser("~/Library/Mobile Documents/iCloud~md~obsidian/Documents/shkodnik1917")
LIB = os.path.join(V, "Literature")


def найти(arxiv):
    for тема in sorted(os.listdir(LIB)):
        d = os.path.join(LIB, тема)
        if not os.path.isdir(d):
            continue
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
    if not os.path.isdir(os.path.join(LIB, куда)):
        sys.exit(f"темы {куда} нет")
    print(f"{arxiv}: {откуда} -> {куда}   {имя[:60]}")
    if сухой:
        return
    shutil.move(os.path.join(LIB, откуда, имя), os.path.join(LIB, куда, имя))
    пары = {f"Literature/{откуда}/{имя[:-3]}": f"Literature/{куда}/{имя[:-3]}"}
    вложения = os.path.join(LIB, откуда, "_attachments", arxiv)
    if os.path.isdir(вложения):
        цель = os.path.join(LIB, куда, "_attachments", arxiv)
        os.makedirs(os.path.dirname(цель), exist_ok=True)
        shutil.move(вложения, цель)
        пары[f"Literature/{откуда}/_attachments/{arxiv}/"] = f"Literature/{куда}/_attachments/{arxiv}/"
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
