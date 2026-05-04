---
name: pdf-reader
description: This skill should be used when the user asks to "read this PDF", "extract text from PDF", "what's in this PDF", or provides a PDF file path and wants to understand its contents. Extracts structured text from PDF files using PyMuPDF with pypdf fallback.
---

# PDF Reader

Extract text from PDF files using open-source tools. PyMuPDF (fitz) is the primary engine with pypdf as fallback.

## When to use

- User provides a `.pdf` file path and asks to read or extract its contents
- User asks to summarize a PDF
- User asks what a PDF document contains
- Academic papers, reports, or any PDF documents

## When NOT to use

- URLs pointing to web pages (use `defuddle` skill instead)
- Image files (use image analysis tools)
- Already-extracted text files

## Workflow

### 1. Extract text

Run the extraction script:

```bash
python3 ~/.claude/skills/pdf-reader/scripts/extract_pdf.py <pdf_path>
```

Options:
- `-p, --pages` — extract specific pages, e.g. `1-5` or `1,3,7`
- `-m, --method` — force `fitz` or `pypdf` (default: auto)
- `--json` — output structured JSON with metadata
- `--metadata-only` — print only title, author, page count

### 2. For large PDFs

Extract in chunks to avoid token overflow:
- First run with `--metadata-only` to check page count
- Then extract page ranges with `-p 1-10`, `-p 11-20`, etc.

### 3. For scanned PDFs (image-based)

If extracted text is empty or garbled, the PDF is likely scanned. Inform the user that OCR is needed. Consider suggesting `marker` or `ocrmypdf` as next steps.

## Quality notes

- PyMuPDF preserves font size and bold formatting as markdown headers and bold text
- pypdf is the fallback and produces plain text only
- Both handle multi-column layouts as single-column output (reading order)
- Tables are extracted as plain text, not as structured tables
