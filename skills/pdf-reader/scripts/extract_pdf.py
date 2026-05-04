#!/usr/bin/env python3
"""Extract text from PDF files using PyMuPDF (fitz) with pypdf fallback."""

import argparse
import sys
import json
from pathlib import Path


def extract_with_fitz(pdf_path: str, pages: str | None = None) -> dict:
    import fitz

    doc = fitz.open(pdf_path)
    metadata = {
        "title": doc.metadata.get("title", ""),
        "author": doc.metadata.get("author", ""),
        "subject": doc.metadata.get("subject", ""),
        "page_count": len(doc),
    }

    if pages:
        if "-" in pages:
            start, end = pages.split("-", 1)
            page_nums = range(int(start) - 1, int(end))
        else:
            page_nums = [int(p) - 1 for p in pages.split(",")]
    else:
        page_nums = range(len(doc))

    texts = []
    for i in page_nums:
        if i < 0 or i >= len(doc):
            continue
        page = doc[i]
        blocks = page.get_text("dict")["blocks"]
        page_parts = []
        for block in blocks:
            if block["type"] == 0:  # text block
                lines = []
                for line in block["lines"]:
                    spans_text = []
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text:
                            continue
                        size = span["size"]
                        flags = span["flags"]
                        if flags & 2**4:  # bold
                            text = f"**{text}**"
                        if size > 16:
                            text = f"# {text}"
                        elif size > 13:
                            text = f"## {text}"
                        elif size > 11:
                            text = f"### {text}"
                        spans_text.append(text)
                    if spans_text:
                        lines.append(" ".join(spans_text))
                if lines:
                    page_parts.append("\n".join(lines))
            elif block["type"] == 1:  # image block
                page_parts.append("[image]")
        if page_parts:
            texts.append(f"--- Page {i + 1} ---\n\n" + "\n\n".join(page_parts))

    doc.close()
    return {"metadata": metadata, "text": "\n\n".join(texts)}


def extract_with_pypdf(pdf_path: str, pages: str | None = None) -> dict:
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    metadata = {
        "title": reader.metadata.title if reader.metadata else "",
        "author": reader.metadata.author if reader.metadata else "",
        "page_count": len(reader.pages),
    }

    if pages:
        if "-" in pages:
            start, end = pages.split("-", 1)
            page_nums = range(int(start) - 1, int(end))
        else:
            page_nums = [int(p) - 1 for p in pages.split(",")]
    else:
        page_nums = range(len(reader.pages))

    texts = []
    for i in page_nums:
        if i < 0 or i >= len(reader.pages):
            continue
        page_text = reader.pages[i].extract_text()
        if page_text and page_text.strip():
            texts.append(f"--- Page {i + 1} ---\n\n{page_text}")

    return {"metadata": metadata, "text": "\n\n".join(texts)}


def extract(pdf_path: str, pages: str | None = None, method: str = "auto") -> dict:
    if method == "pypdf":
        return extract_with_pypdf(pdf_path, pages)

    try:
        return extract_with_fitz(pdf_path, pages)
    except Exception as e:
        if method == "fitz":
            raise
        print(f"PyMuPDF failed ({e}), falling back to pypdf...", file=sys.stderr)
        return extract_with_pypdf(pdf_path, pages)


def main():
    parser = argparse.ArgumentParser(description="Extract text from PDF")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument(
        "-p", "--pages", help="Pages to extract (e.g. '1-5' or '1,3,7')"
    )
    parser.add_argument(
        "-m", "--method", choices=["auto", "fitz", "pypdf"], default="auto"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--metadata-only", action="store_true", help="Only print metadata"
    )
    args = parser.parse_args()

    if not Path(args.pdf_path).exists():
        print(f"Error: file not found: {args.pdf_path}", file=sys.stderr)
        sys.exit(1)

    result = extract(args.pdf_path, args.pages, args.method)

    if args.metadata_only:
        print(json.dumps(result["metadata"], indent=2, ensure_ascii=False))
    elif args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if result["metadata"]["title"]:
            print(f"# {result['metadata']['title']}\n")
        if result["metadata"]["author"]:
            print(f"Author: {result['metadata']['author']}\n")
        print(result["text"])


if __name__ == "__main__":
    main()
