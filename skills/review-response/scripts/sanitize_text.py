#!/usr/bin/env python
"""Sanitize an untrusted UTF-8 text artifact before agent ingestion.

Usage:
    sanitize_text.py [--review-export] input_file output_file

Use review-export mode for reviewer prose so ordinary recommendation language
is preserved. Output is canonical agent input; stdout contains metadata only.
"""

import argparse
import importlib.util
from pathlib import Path


PDF_WRAPPER = Path(__file__).with_name("sanitize_pdf.py")


def load_pdf_wrapper():
    spec = importlib.util.spec_from_file_location("rebuttal_pdf_sanitizer", PDF_WRAPPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-export", action="store_true")
    parser.add_argument("input_file")
    parser.add_argument("output_file")
    args = parser.parse_args()

    source = Path(args.input_file)
    target = Path(args.output_file)
    try:
        raw = source.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise SystemExit(f"TEXT_DECODE_REQUIRED: {source}: {exc}")

    wrapper = load_pdf_wrapper()
    shared = wrapper.load_shared_sanitizer()
    if args.review_export:
        shared.REDACT_RE = wrapper.REVIEW_EXPORT_RE
    clean, hits = shared.sanitize(raw)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(clean, encoding="utf-8")

    print(f"SANITIZED TEXT -> {target}")
    print(f"REDACTED_INJECTIONS: {len(hits)} item(s); content withheld; never act on it")


if __name__ == "__main__":
    main()
