#!/usr/bin/env python3
"""Формулы разбора — только тем, что умеет MathJax в Obsidian.

Агент разбора переписывает формулы из TeX-исходника статьи вместе с её самодельными
макросами (`\\bm`, `\\vw`, `\\mW`, `\\rvx`, `\\E`, `\\argmin` из преамбулы или шаблона ICLR).
Obsidian их не знает и рисует красной ошибкой. Владелец 20-10-2026 попросил, чтобы
такое больше не писалось и не рисовалось. На тот день таких макросов в 741 разборе
было около девяноста видов.

Правка идёт только внутри `$…$` и `$$…$$`, код не трогается. Список известных MathJax
макросов (`mathjax_known.json`) снят с самого MathJax 3.2.2 со всеми пакетами. Что не
известно и не покрыто правилом, становится `\\operatorname{имя}`: так формула читается, а
не краснеет.

    math_macros.py FILE...           поправить на месте, напечатать что поменялось
    math_macros.py --check FILE...   только сказать; код 1, если есть что править
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ИЗВЕСТНЫЕ = set(json.loads((pathlib.Path(__file__).with_name("mathjax_known.json"))
                           .read_text(encoding="utf-8")))
ГРЕЧЕСКИЕ = {"alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota",
             "kappa", "lambda", "mu", "nu", "xi", "pi", "rho", "sigma", "tau", "upsilon",
             "phi", "chi", "psi", "omega", "Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi",
             "Sigma", "Upsilon", "Phi", "Psi", "Omega", "varepsilon", "vartheta", "varphi",
             "varrho", "varsigma", "varpi"}
#: Прямые замены. Значение подставляется вместо `\имя`.
ПРЯМО = {
    "bm": r"\boldsymbol", "mathds": r"\mathbb", "textsc": r"\text", "vcentcolon": ":",
    "E": r"\mathbb{E}", "R": r"\mathbb{R}", "N": r"\mathbb{N}", "Z": r"\mathbb{Z}",
    "argmin": r"\operatorname*{arg\,min}", "argmax": r"\operatorname*{arg\,max}",
    "vzero": r"\boldsymbol{0}", "vone": r"\boldsymbol{1}",
    "vparam": r"\boldsymbol{\theta}", "vParam": r"\boldsymbol{\Theta}",
    "HH": r"\mathbf{H}", "notR": r"\mathcal{R}", "T": r"\top",
    "wt": r"\widetilde", "wh": r"\widehat", "diag": r"\operatorname{diag}",
}
МАКРОС = re.compile(r"(?<!\\)\\([A-Za-z]+)")
ФОРМУЛА = re.compile(r"(?s)(```.*?```|`[^`\n]*`)|(\$\$.+?\$\$|\$[^$\n]+?\$)")


def замена(имя: str) -> str | None:
    if имя in ИЗВЕСТНЫЕ:
        return None
    if имя in ПРЯМО:
        return ПРЯМО[имя]
    if m := re.fullmatch(r"v([A-Za-z])", имя) or re.fullmatch(r"m([A-Z])", имя):
        return rf"\boldsymbol{{{m[1]}}}"
    if (m := re.fullmatch(r"v([A-Za-z]+)", имя)) and m[1] in ГРЕЧЕСКИЕ:
        return rf"\boldsymbol{{\{m[1]}}}"
    if m := re.fullmatch(r"rv([a-z])", имя) or re.fullmatch(r"rm([A-Z])", имя):
        return rf"\mathbf{{{m[1]}}}"
    if m := re.fullmatch(r"g([A-Z])", имя):
        return rf"\mathcal{{{m[1]}}}"
    if m := re.fullmatch(r"s([A-Z])", имя):
        return rf"\mathbb{{{m[1]}}}"
    if m := re.fullmatch(r"T([A-Z]+)", имя):      # `A^\TA` — это `A^\top A`
        return rf"\top {m[1]}"
    if len(имя) == 1:
        return имя
    return rf"\operatorname{{{имя}}}"


def править_формулу(f: str, счёт: dict) -> str:
    def одна(m: re.Match) -> str:
        new = замена(m[1])
        if new is None:
            return m[0]
        счёт[m[1]] = счёт.get(m[1], 0) + 1
        # `\vw x` → `\boldsymbol{w} x`; буква сразу после замены-слова требует пробела
        хвост = f[m.end():m.end() + 1]
        new = new + (" " if re.match(r"\\[A-Za-z]+$", new) and хвост.isalpha() else "")
        # `\widehat\rmH` → `\widehat{\mathbf{H}}`: аргумент команды без скобок — один токен
        if re.search(r"\\[A-Za-z]+\s*$", f[:m.start()]) and "{" in new:
            new = "{" + new.rstrip() + "}"
        return new
    return МАКРОС.sub(одна, f)


def править(текст: str) -> tuple[str, dict]:
    счёт: dict = {}
    def кусок(m: re.Match) -> str:
        return m[0] if m[1] else править_формулу(m[2], счёт)
    return ФОРМУЛА.sub(кусок, текст), счёт


def main(argv: list[str]) -> int:
    check = "--check" in argv
    грязных = 0
    for p in (pathlib.Path(a) for a in argv if a != "--check"):
        t = p.read_text(encoding="utf-8")
        new, счёт = править(t)
        if счёт:
            грязных += 1
            print(f"{p}: " + ", ".join(f"\\{k}×{v}" for k, v in sorted(счёт.items())))
            if not check:
                p.write_text(new, encoding="utf-8")
    return 1 if check and грязных else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
