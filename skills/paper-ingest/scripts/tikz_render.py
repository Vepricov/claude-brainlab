#!/usr/bin/env python3
"""Собрать рисунок, нарисованный в TikZ, в PNG прямо из исходника arXiv.

Рисунки TikZ не лежат файлами, и из исходников их не извлечь копированием: они
вычисляются при сборке. Здесь берётся преамбула статьи и тело нужного окружения
`figure`, собирается отдельный документ классом `standalone` и переводится в PNG.

    tikz_render.py src_dir out_dir fig:label [fig:label ...]
"""
import re, subprocess, sys, pathlib, glob, os

DPI = 200

#: Стили конференций — именно они ломали сборку. Такой стиль ставит свою ширину
#: полосы (`\textwidth 5.5 true in` у iclr2027), подключает `fancyhdr` и
#: `\pagestyle{fancy}`. В отдельном документе от этого остаются номер страницы
#: прямо на картинке и обрезка по ширине полосы: у 2609.37899 так обрезало обзор
#: метода, пропали «context», «centroid router» и «sample next token».
ВЕНЮ = (r"icml|iclr|neurips|nips|aaai|acl|emnlp|naacl|cvpr|iccv|eccv|colm|tmlr"
        r"|jmlr|aistats|uai|kdd|sigir|www|coling|interspeech|miccai")
РАСТЯЖКА = re.compile(r"\\resizebox\s*\{[^}]*\}\s*\{[^}]*\}\s*\{%?\s*")


def без_стиля_венью(голова):
    """Убрать стиль конференции вместе с его собственными командами.

    Мало выкинуть `\\usepackage{iclr2027_conference}`: в преамбуле остаётся
    `\\iclrfinalcopy`, и сборка падает на неопределённой команде.
    """
    голова = re.sub(r"(?mi)^\s*\\usepackage(?:\[[^\]]*\])?\{[^}]*(?:" + ВЕНЮ
                    + r")[^}]*\}[^\n]*\n", "", голова)
    return re.sub(r"(?mis)^\s*\\(?:" + ВЕНЮ + r")[a-z@]*(?:\[[^\]]*\])?(?:\{.*?\})?\s*$\n?",
                  "", голова)


def без_растяжки(тело):
    """Снять `\\resizebox{\\linewidth}{!}{...}` вокруг рисунка.

    В отдельном документе ширина полосы статьи смысла не имеет, а рисунок по ней
    ужимается и обрезается: `standalone` меряет коробку растяжки, а TikZ рисует
    шире неё. Без растяжки рисунок сам задаёт свои границы, обрезка выходит тугой,
    и заодно пропадает потеря чёткости от уменьшения.
    """
    m = РАСТЯЖКА.search(тело)
    if not m:
        return тело
    начало, глубина, i = m.end(), 1, m.end()
    while i < len(тело) and глубина:
        if тело[i] == "{" and тело[i - 1] != "\\":
            глубина += 1
        elif тело[i] == "}" and тело[i - 1] != "\\":
            глубина -= 1
        i += 1
    return (тело[:m.start()] + тело[начало:i - 1] + тело[i:]).strip()


def исходник(каталог):
    куски = []
    # Рисунки часто вынесены в подкаталог (`figures_iclr/architecture.tex`),
    # поэтому обходим дерево, а не только верхний каталог.
    for f in sorted(glob.glob(os.path.join(каталог, "**", "*.tex"), recursive=True)):
        куски.append(open(f, encoding="utf-8", errors="ignore").read())
    return "\n".join(куски)


def преамбула(каталог):
    """Преамбула статьи целиком, без её класса и стиля конференции.

    Берётся из того файла, где стоит `\\documentclass`, а не из склейки всех: файлы
    обходятся по алфавиту, и `figures_iclr/architecture.tex` идёт раньше `main.tex`,
    так что «всё до первого \\begin{document}» оказывается телом рисунка, а сборка
    падает с `Missing \\begin{document}`.

    Построчная выборка «только нужных строк» тоже не работает: многострочный
    `\\newcommand` обрезается на первой строке, и сборка падает с
    `File ended while scanning use of \\@xargdef`. Поэтому берём всё целиком.
    """
    текст = ""
    for f in sorted(glob.glob(os.path.join(каталог, "**", "*.tex"), recursive=True)):
        т = open(f, encoding="utf-8", errors="ignore").read()
        if "\\documentclass" in т:
            текст = т
            break
    i = текст.find("\\begin{document}")
    голова = текст[:i] if i > 0 else текст
    голова = re.sub(r"(?m)^\s*\\documentclass[^\n]*\n", "", голова)
    return без_стиля_венью(голова)


def тело(текст, метка):
    # `[!t]` — указание вёрстки, куда поставить плавающий блок. В отдельном
    # документе смысла не имеет и печатается как текст прямо на рисунке.
    for m in re.finditer(r"\\begin\{figure\*?\}\s*(?:\[[^\]]*\])?(.*?)\\end\{figure\*?\}",
                         текст, re.S):
        блок = m.group(1)
        if "\\label{" + метка + "}" in блок:
            блок = re.sub(r"\\caption\{.*?\n\s*\}", "", блок, flags=re.S)
            блок = re.sub(r"\\caption\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", "", блок, flags=re.S)
            блок = re.sub(r"\\label\{[^}]*\}", "", блок)
            блок = re.sub(r"\\centering|\\vskip[^\n]*|\\vspace\{[^}]*\}", "", блок)
            return без_растяжки(блок.strip())
    return None


def main():
    # Пути делаем абсолютными: pdflatex запускается из каталога исходников, чтобы
    # найти данные к графикам, и относительный путь до сборки там уже не тот.
    каталог = str(pathlib.Path(sys.argv[1]).resolve())
    вывод = pathlib.Path(sys.argv[2]).resolve()
    вывод.mkdir(parents=True, exist_ok=True)
    текст = исходник(каталог)
    шапка = преамбула(каталог)
    работа = pathlib.Path(вывод, "_сборка")
    работа.mkdir(exist_ok=True)
    for метка in sys.argv[3:]:
        т = тело(текст, метка)
        if т is None:
            print(f"{метка}: окружения с такой меткой нет"); continue
        имя = метка.replace(":", "_")
        док = ("\\documentclass[border=4pt]{standalone}\n" + шапка +
               "\n\\begin{document}\n" + т + "\n\\end{document}\n")
        tex = работа / (имя + ".tex")
        tex.write_text(док, encoding="utf-8")
        r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                            "-output-directory", str(работа), str(tex)],
                           capture_output=True, text=True, errors="replace",
                           cwd=каталог, timeout=180)
        pdf = работа / (имя + ".pdf")
        if r.returncode or not pdf.exists():
            беда = [l for l in r.stdout.splitlines() if l.startswith("!")][:2]
            print(f"{метка}: собрать не удалось — {'; '.join(беда) or 'см. журнал'}")
            continue
        png = вывод / (имя + ".png")
        subprocess.run(["pdftoppm", "-png", "-r", str(DPI), "-singlefile",
                        str(pdf), str(png)[:-4]], check=True)
        print(f"{метка}: собрано -> {png.name}")


if __name__ == "__main__":
    main()
