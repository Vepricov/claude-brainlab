#!/usr/bin/env python3
"""Extract a paper PDF to plain text.

Prefers pdftotext (poppler) when it is on PATH, so the output stays byte for
byte what this pipeline produced before. Falls back to the pdf-reader skill's
extractor (PyMuPDF, then pypdf) when poppler is missing, which is the normal
state on Windows and on any macOS without Homebrew. That fallback is also why
the "pdftotext not found" troubleshooting entry no longer stops the run.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# skills/paper-ingest/scripts/ -> skills/
SKILLS_ROOT = Path(__file__).resolve().parents[2]
FALLBACK = SKILLS_ROOT / "pdf-reader" / "scripts" / "extract_pdf.py"


def via_pdftotext(pdf: Path, out: Path) -> bool:
    exe = shutil.which("pdftotext")
    if not exe:
        return False
    subprocess.run([exe, str(pdf), str(out)], check=True)
    return True


def via_pdf_reader(pdf: Path, out: Path) -> None:
    if not FALLBACK.is_file():
        raise SystemExit(
            f"ERROR: pdftotext is not on PATH and the fallback extractor is "
            f"missing: {FALLBACK}"
        )
    result = subprocess.run(
        [sys.executable, str(FALLBACK), str(pdf)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        # The extractor prints the paper text; on Windows its stdout would
        # otherwise default to the ANSI codepage and die on the first minus
        # sign or Greek letter.
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    if result.returncode != 0:
        raise SystemExit(
            "ERROR: PDF extraction failed.\n"
            "Install poppler (pdftotext) or PyMuPDF.\n"
            + result.stderr.strip()
        )
    out.write_text(result.stdout, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Extract a PDF to plain text")
    parser.add_argument("pdf", help="Path to the PDF")
    parser.add_argument("out", help="Path to write the extracted text to")
    args = parser.parse_args()

    pdf, out = Path(args.pdf), Path(args.out)
    if not pdf.is_file():
        raise SystemExit(f"ERROR: PDF not found: {pdf}")

    if not via_pdftotext(pdf, out):
        via_pdf_reader(pdf, out)
    print(f"OK {out}")


if __name__ == "__main__":
    main()
