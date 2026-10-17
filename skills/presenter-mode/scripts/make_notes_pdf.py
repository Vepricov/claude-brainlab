"""Add speaker notes to a Beamer PDF for the presenter view of Présentation.app.

Each section "## <heading word> N. <title>" of a Markdown talk script (default heading word
"Слайд", e.g. "## Слайд 12. Заголовок (2 мин)") becomes a hidden text annotation on PDF page N.
Présentation.app shows text annotations of the current page as notes; hidden ones are not drawn
on the projector. Markdown is flattened to plain text and LaTeX math ($...$) to Unicode.
The source PDF is copied and annotated incrementally, so `animate` animations keep working.

Usage:
    uv run --with pymupdf python make_notes_pdf.py deck.pdf talk-script.md [-o deck-present.pdf]
"""
from __future__ import annotations

import argparse
import logging
import re
import shutil
from pathlib import Path

import pymupdf

logger = logging.getLogger(__name__)

SYMBOLS = {
    r"\mathbb N": "ℕ", r"\mathbb R": "ℝ", r"\mathbb Z": "ℤ", r"\mathbb Q": "ℚ", r"\mathbb F": "𝔽",
    r"\mathbb E": "𝔼", r"\to": "→", r"\rightarrow": "→", r"\leftarrow": "←", r"\Rightarrow": "⇒",
    r"\le": "≤", r"\leq": "≤", r"\ge": "≥", r"\geq": "≥", r"\ne": "≠", r"\neq": "≠",
    r"\approx": "≈", r"\sim": "∼", r"\infty": "∞", r"\sum": "∑", r"\prod": "∏", r"\int": "∫",
    r"\cdot": "·", r"\times": "×", r"\in": "∈", r"\subset": "⊂", r"\subseteq": "⊆",
    r"\forall": "∀", r"\exists": "∃", r"\wedge": "∧", r"\vee": "∨", r"\neg": "¬", r"\vdash": "⊢",
    r"\nabla": "∇", r"\partial": "∂", r"\pm": "±", r"\mid": "|", r"\|": "‖", r"\langle": "⟨",
    r"\rangle": "⟩", r"\alpha": "α", r"\beta": "β", r"\gamma": "γ", r"\delta": "δ",
    r"\Delta": "Δ", r"\varepsilon": "ε", r"\epsilon": "ε", r"\eta": "η", r"\theta": "θ",
    r"\kappa": "κ", r"\lambda": "λ", r"\mu": "μ", r"\nu": "ν", r"\pi": "π", r"\rho": "ρ",
    r"\sigma": "σ", r"\tau": "τ", r"\phi": "φ", r"\varphi": "φ", r"\psi": "ψ", r"\omega": "ω",
    r"\Lambda": "Λ", r"\Sigma": "Σ", r"\Pi": "Π", r"\ell": "ℓ", r"\top": "⊤", r"\circ": "∘",
    r"\ldots": "…", r"\dots": "…", r"\cdots": "⋯", r"\quad": " ", r"\qquad": " ", r"\,": " ",
    r"\;": " ", r"\!": "", r"\max": "max", r"\min": "min", r"\log": "log", r"\ln": "ln",
    r"\tanh": "tanh", r"\cosh": "cosh", r"\sup": "sup", r"\arg": "arg", r"\exp": "exp",
}
SUP = str.maketrans("0123456789+-=()nkTtiab", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿᵏᵀᵗⁱᵃᵇ")
SUB = str.maketrans("0123456789+-=()ikjnt", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ᵢₖⱼₙₜ")


def _script(text: str, table: dict) -> str:
    """Use Unicode super/subscripts when every char has one, else fall back to ^(...)."""
    mapped = text.translate(table)
    return mapped if all(c != o or c in " " for c, o in zip(mapped, text)) and mapped != text else ""


def latex_to_unicode(expr: str) -> str:
    s = expr
    s = re.sub(r"\\(?:mathrm|text|operatorname|mathbf|textbf|mathcal|boldsymbol)\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\hat\s*\{?(\w)\}?", r"\1̂", s)
    s = re.sub(r"\\sqrt\{([^{}]*)\}", r"√(\1)", s)
    for _ in range(3):
        s = re.sub(r"\\[dt]?frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)", s)
        s = re.sub(r"\\binom\{([^{}]*)\}\{([^{}]*)\}", r"C(\1,\2)", s)
    for k in sorted(SYMBOLS, key=len, reverse=True):
        s = re.sub(re.escape(k) + r"(?![A-Za-z])", SYMBOLS[k], s)
    s = re.sub(r"\\(?:left|right|big|Big|bigg|Bigg)", "", s)

    def sup(m: re.Match) -> str:
        body = m.group(1) or m.group(2)
        return _script(body, SUP) or f"^({body})" if len(body) > 1 else (_script(body, SUP) or "^" + body)

    def sub(m: re.Match) -> str:
        body = m.group(1) or m.group(2)
        return _script(body, SUB) or f"_({body})" if len(body) > 1 else (_script(body, SUB) or "_" + body)

    s = re.sub(r"\^\{([^{}]*)\}|\^(\S)", sup, s)
    s = re.sub(r"_\{([^{}]*)\}|_(\S)", sub, s)
    s = re.sub(r"\\([A-Za-z]+)", r"\1", s)
    return s.replace("{", "").replace("}", "")


def convert_note(body: str) -> str:
    body = re.sub(r"\$\$(.+?)\$\$", lambda m: latex_to_unicode(m.group(1)), body, flags=re.S)
    body = re.sub(r"\$([^$\n]+?)\$", lambda m: latex_to_unicode(m.group(1)), body)
    body = re.sub(r"\[\[[^|\]]*\|([^\]]*)\]\]", r"\1", body)
    body = re.sub(r"\[\[([^\]]*)\]\]", r"\1", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


def parse_sections(text: str, word: str = "Слайд") -> dict[int, str]:
    parts = re.split(rf"^## {re.escape(word)} (\d+)\.(.*)$", text, flags=re.M)
    notes: dict[int, str] = {}
    for i in range(1, len(parts) - 2, 3):
        num, title, body = int(parts[i]), parts[i + 1].strip(), parts[i + 2]
        body = re.split(r"^(?:---|# |## Шпаргалка)", body, flags=re.M)[0]
        notes[num] = f"### {num}. {convert_note(title)}\n\n{convert_note(body)}"
    return notes



def to_plain(note: str) -> str:
    """Markdown note -> plain text for the notes panel."""
    s = re.sub(r"^#+\s*", "", note, flags=re.M)
    s = re.sub(r"^>\s?", "", s, flags=re.M)
    s = s.replace("**", "").replace("`", "")
    s = re.sub(r"(?<!\w)\*(?!\s)([^*\n]+?)\*(?!\w)", r"\1", s)
    return s.strip()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pdf", type=Path, help="source deck PDF")
    ap.add_argument("script", type=Path, help="Markdown talk script with '## Слайд N.' sections")
    ap.add_argument("-o", "--out", type=Path, help="output PDF (default: <deck>-present.pdf)")
    ap.add_argument("--word", default="Слайд", help="heading word before the page number")
    args = ap.parse_args()
    out = args.out or args.pdf.with_name(args.pdf.stem + "-present.pdf")
    notes = parse_sections(args.script.read_text(encoding="utf-8"), args.word)
    shutil.copyfile(args.pdf, out)
    doc = pymupdf.open(out)
    if len(doc) != len(notes):
        logger.warning("deck has %d pages, script has %d sections", len(doc), len(notes))
    for n, note in notes.items():
        if n > len(doc):
            continue
        page = doc[n - 1]
        annot = page.add_text_annot(pymupdf.Point(2, page.rect.height - 2), to_plain(note), icon="Note")
        annot.set_flags(pymupdf.PDF_ANNOT_IS_HIDDEN)
        annot.update()
    doc.save(out, incremental=True, encryption=pymupdf.PDF_ENCRYPT_KEEP)
    logger.info("%s: %d notes", out, len(notes))


if __name__ == "__main__":
    main()
