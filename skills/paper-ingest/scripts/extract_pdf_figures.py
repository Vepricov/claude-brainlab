#!/usr/bin/env python3
"""Extract figures and tables from a PDF via PyMuPDF.

Fallback path for paper-ingest Step 4b when the arXiv LaTeX source bundle
is not available.

Two complementary modes:

- Embedded image extraction (always on): pulls raster images stored inside
  the PDF via xref. Fast, lossless, preserves the original format.
  Works well for photo-like figures and screenshots.

- Caption-driven region rasterization (`--vector`): finds spans matching
  "Figure N:", "Fig. N:", "Table N:" and rasterizes the page area
  attached to each caption (above for figures, below for tables).
  Catches vector plots, diagrams, and ASCII-style tables that have no
  embedded raster.

Output naming inside `--out`:
    fig_p{page:02d}_i{idx}.{ext}         embedded raster image
    fig_p{page:02d}_{label}.png          caption-driven figure region
    tab_p{page:02d}_{label}.png          caption-driven table region

Usage:
    python3 extract_pdf_figures.py --pdf paper.pdf --out ./_attachments/2509.07972/
    python3 extract_pdf_figures.py --pdf paper.pdf --out ... --vector
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("PyMuPDF not installed. Run: pip install pymupdf")

logger = logging.getLogger(__name__)

CAPTION_RE = re.compile(r"^\s*(figure|fig\.|table)\s+\d+", re.IGNORECASE)
TABLE_RE = re.compile(r"^\s*table\s+\d+", re.IGNORECASE)


@dataclass(frozen=True)
class ExtractConfig:
    pdf: Path
    out: Path
    min_size: int
    dpi: int
    vector: bool
    expand_above: float
    expand_below: float


def _slug(text: str) -> str:
    match = CAPTION_RE.match(text)
    if match:
        head = match.group(0)
    else:
        head = text.split(":", 1)[0][:40]
    label = re.sub(r"[^a-z0-9]+", "_", head.strip().lower()).strip("_")
    return label or "caption"


def extract_embedded(doc: "fitz.Document", cfg: ExtractConfig) -> list[Path]:
    """Dump every embedded raster image larger than `min_size` per side."""
    saved: list[Path] = []
    for page_idx in range(doc.page_count):
        page = doc[page_idx]
        for img_idx, img in enumerate(page.get_images(full=True), start=1):
            xref = img[0]
            try:
                info = doc.extract_image(xref)
            except (RuntimeError, ValueError) as e:
                logger.warning(
                    "page %d img %d: extract_image failed (%s)",
                    page_idx + 1, img_idx, e,
                )
                continue
            data = info.get("image")
            width = info.get("width", 0)
            height = info.get("height", 0)
            ext = info.get("ext", "png")
            if not data or min(width, height) < cfg.min_size:
                logger.debug(
                    "page %d img %d: skipped (%dx%d, below min_size=%d)",
                    page_idx + 1, img_idx, width, height, cfg.min_size,
                )
                continue
            out_path = cfg.out / f"fig_p{page_idx + 1:02d}_i{img_idx}.{ext}"
            out_path.write_bytes(data)
            saved.append(out_path)
            logger.info(
                "embedded: %s (%dx%d, %d bytes)",
                out_path.name, width, height, len(data),
            )
    return saved


def _find_captions(page: "fitz.Page") -> list[tuple["fitz.Rect", str, str]]:
    """Return list of (bbox, slug, kind) for every Figure/Table caption span."""
    captions: list[tuple[fitz.Rect, str, str]] = []
    try:
        blocks = page.get_text("dict").get("blocks", [])
    except (RuntimeError, ValueError):
        return captions
    for blk in blocks:
        if blk.get("type") != 0:
            continue
        for line in blk.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if not CAPTION_RE.match(text):
                    continue
                rect = fitz.Rect(span["bbox"])
                kind = "table" if TABLE_RE.match(text) else "figure"
                captions.append((rect, _slug(text), kind))
    return captions


def extract_regions(doc: "fitz.Document", cfg: ExtractConfig) -> list[Path]:
    """For each caption span, rasterize the page region attached to it."""
    saved: list[Path] = []
    zoom = cfg.dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    for page_idx in range(doc.page_count):
        page = doc[page_idx]
        page_rect = page.rect
        for cap_rect, label, kind in _find_captions(page):
            cap_height = max(cap_rect.height, 1.0)
            if kind == "figure":
                top = max(page_rect.y0, cap_rect.y0 - cfg.expand_above * cap_height)
                bottom = cap_rect.y1
            else:
                top = cap_rect.y0
                bottom = min(page_rect.y1, cap_rect.y1 + cfg.expand_below * cap_height)
            crop = fitz.Rect(page_rect.x0, top, page_rect.x1, bottom)
            if crop.height <= 1.0 or crop.width <= 1.0:
                continue
            try:
                pixmap = page.get_pixmap(matrix=matrix, clip=crop, alpha=False)
            except (RuntimeError, ValueError) as e:
                logger.warning(
                    "page %d %s: get_pixmap failed (%s)",
                    page_idx + 1, label, e,
                )
                continue
            prefix = "tab" if kind == "table" else "fig"
            out_path = cfg.out / f"{prefix}_p{page_idx + 1:02d}_{label}.png"
            pixmap.save(str(out_path))
            saved.append(out_path)
            logger.info(
                "region: %s (%.0fx%.0f pt @ %d DPI)",
                out_path.name, crop.width, crop.height, cfg.dpi,
            )
    return saved


def parse_args(argv: list[str] | None = None) -> ExtractConfig:
    parser = argparse.ArgumentParser(
        description="Extract figures and tables from a PDF (paper-ingest fallback)."
    )
    parser.add_argument("--pdf", type=Path, required=True, help="input PDF path")
    parser.add_argument("--out", type=Path, required=True, help="output directory")
    parser.add_argument(
        "--min-size", type=int, default=80,
        help="min pixel side for embedded images (default: 80)",
    )
    parser.add_argument(
        "--dpi", type=int, default=200,
        help="DPI for caption-driven region crops (default: 200)",
    )
    parser.add_argument(
        "--vector", action="store_true",
        help="also run caption-driven region rasterization (catches vector figures)",
    )
    parser.add_argument(
        "--expand-above", type=float, default=20.0,
        help="figure crop height above caption, in caption-height units (default: 20)",
    )
    parser.add_argument(
        "--expand-below", type=float, default=15.0,
        help="table crop height below caption, in caption-height units (default: 15)",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    ns = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if ns.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )
    return ExtractConfig(
        pdf=ns.pdf,
        out=ns.out,
        min_size=ns.min_size,
        dpi=ns.dpi,
        vector=ns.vector,
        expand_above=ns.expand_above,
        expand_below=ns.expand_below,
    )


def main(argv: list[str] | None = None) -> int:
    cfg = parse_args(argv)
    if not cfg.pdf.exists():
        logger.error("PDF not found: %s", cfg.pdf)
        return 2
    cfg.out.mkdir(parents=True, exist_ok=True)
    try:
        doc = fitz.open(str(cfg.pdf))
    except fitz.FileDataError as e:
        logger.error("cannot open PDF: %s", e)
        return 2
    try:
        embedded = extract_embedded(doc, cfg)
        regions: list[Path] = extract_regions(doc, cfg) if cfg.vector else []
    finally:
        doc.close()
    logger.info(
        "done: %d embedded + %d region(s) -> %s",
        len(embedded), len(regions), cfg.out,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
