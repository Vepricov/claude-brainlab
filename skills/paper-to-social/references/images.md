# Pulling clean figures from the paper

Figures come from the **arXiv / published version**, not a local draft. Download the arXiv PDF and render crisp crops. View every render before describing it.

```python
# download once
# curl -sL -A "Mozilla/5.0" -o paper.pdf "https://arxiv.org/pdf/<id>"
import fitz  # PyMuPDF
doc = fitz.open("paper.pdf")
```

## Whole figures

Render the figure's page region at 3–4× zoom into the project's assets folder:
```python
pg = doc[PAGE]
pix = pg.get_pixmap(matrix=fitz.Matrix(3,3), clip=fitz.Rect(x0,y0,x1,y1), alpha=False)
pix.save("social-assets/figure.png")
```

## Equation / theorem / definition snippets (content-aware crop)

Anchor on a **specific** marker (not a generic phrase that also appears in the intro), take the union bbox of the words in that y-range **within one column** (avoid two-column bleed), pad ~12pt, render at 4×:
```python
pg = doc[PAGE]; Z=4; PAD=12
rs = pg.search_for("(i) Euclidean")[0]            # START anchor — be specific
re_ = pg.search_for("is provided in Appendix")[0] # END anchor
colmid = pg.rect.x0 + pg.rect.width/2
side = 'L' if rs.x0 < colmid else 'R'
ws = [w for w in pg.get_text("words")
      if w[1] >= rs.y0-1 and w[3] <= re_.y0-4
      and ((w[0] < colmid) if side=='L' else (w[0] >= colmid-2))]
x0=min(w[0] for w in ws); x1=max(w[2] for w in ws)
y0=min(w[1] for w in ws); y1=max(w[3] for w in ws)
clip = fitz.Rect(x0-PAD, y0-3, x1+PAD, y1+10)
pg.get_pixmap(matrix=fitz.Matrix(Z,Z), clip=clip, alpha=False).save("social-assets/theorem.png")
```
Gotcha: if a search hits the wrong occurrence (e.g. "Euclidean norm" appears in the intro too), re-anchor on `(i) Euclidean`, `Theorem 3.4`, etc. Always view the output and re-crop if a stray line of the paragraph above/below or the adjacent column leaked in.

## Cover image (two good options)

1. **Rendered PDF title page** — render the top of page 0 up to the "Introduction" heading (title + authors + abstract), trim to the words bbox + padding. Shows the arXiv stamp on the side.
2. **Screenshot of the arXiv abstract page** (often what "скрин arxiv версии" means) — headless Chrome, then crop off the lower "Bibliographic Tools" with PIL:
```bash
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$CHROME" --headless=new --hide-scrollbars --force-device-scale-factor=2 \
  --window-size=1100,1300 --virtual-time-budget=10000 \
  --screenshot=arxiv_abs.png "https://arxiv.org/abs/<id>"
```
```python
from PIL import Image
im = Image.open("arxiv_abs.png"); w,h = im.size
im.crop((0,0,w,int(h*0.63))).save("social-assets/paper_cover_from_arxiv.png")
```

## Carousel / document export (LinkedIn, and TG "Карточки")

Build the cards as one HTML file, render to a multi-page PDF with Chrome, then to per-card PNGs. This produces a polished, on-brand deck (the user's BRAIn Lab style: white + lavender blobs, brain wordmark, purple ✓-blocks, chat bubbles, real QR codes).

- **Cards:** one `<section class="card">` per page, `1080×1350` (LinkedIn 4:5). CSS `@page{size:1080px 1350px;margin:0}` and `.card:not(:last-child){page-break-after:always}`.
- **Real QR codes:** generate with python `qrcode` (purple modules), embed as base64 data URIs. Encode the arXiv abstract URL and the GitHub URL.
- **Fonts:** use an installed distinctive sans (e.g. `"Avenir Next"` on macOS), not Inter/Arial.
- **Render (use OLD headless — it exits cleanly; `--headless=new` lingers and hangs the shell):**
  ```bash
  CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  "$CHROME" --headless --disable-gpu --no-pdf-header-footer \
    --print-to-pdf=out.pdf "file://$PWD/carousel.html"
  ```
  Then split to PNGs with PyMuPDF: `for pg in doc: pg.get_pixmap(matrix=fitz.Matrix(1.333,1.333)).save(...)`.
- **Gotchas learned:**
  - Set `-webkit-print-color-adjust:exact; print-color-adjust:exact` on `*` so backgrounds print.
  - Do NOT use `background-clip:text` for gradient titles — it leaves a stray rectangle in Chrome print. Use a solid color.
  - In a flex list item, an inline `<b>` becomes a separate flex item (splits the line with the gap). Wrap the whole label, including the `<b>`, in a single `<span>`.
  - Verify by viewing every rendered card before delivering.

## Conventions

- Store images in `Papers/<slug>/social-assets/` (or `<platform>-assets/`).
- In the post note, mark `[IMG: name]` where the image attaches, and at the bottom embed `![[...]]` previews with **paste-ready alt text** for accessibility and reach.
- If PyMuPDF is absent, `sips -s format png in.pdf --out out.png` works but only at 72 dpi (low res) — prefer PyMuPDF.
