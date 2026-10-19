---
name: presenter-mode
description: Use when the user wants to present a PDF/Beamer deck on macOS with a presenter view on the laptop (current + next slide, timer, speaker notes) and clean slides on the projector or second monitor, or wants speaker notes from a talk script (md) attached to slides, or asks why the second screen lags / notes don't fit / animations don't play while presenting. Private workflow built around Présentation.app; not part of the public presentation skill.
---

# Presenter mode (Présentation.app, patched)

Private, owner-only workflow (01–03.10.2026, lecture «Модели для доказательства теорем»).
Keep it out of the public `presentation` skill: it depends on a third-party app installed
only on the owner's Mac.

## What it gives

- **Projector:** clean slides, fullscreen. `animate`-package animations PLAY (unlike Preview).
- **Laptop:** current slide, next slide, clock/timer, slide strip, **speaker notes** = the text of
  the talk script for that slide; long notes auto-shrink (≥ 11 pt) and scroll with `j`/`k`.
- Notes live in a Markdown script (Obsidian), one section per page:
  `## Слайд N. Заголовок (время)` — page N gets everything until the next section.

## One-time setup

1. Install **Présentation.app** (free, notarized, by R. Blanch):
   download `http://iihm.imag.fr/blanch/software/osx-presentation/releases/osx-presentation-latest.pkg`,
   `open` it, the user types the admin password. Ends up in `/Applications/Présentation.app`.
2. Nothing else: `scripts/present.sh` patches on first run (and again after an app update).

## Use

```bash
~/.claude/skills/presenter-mode/scripts/present.sh DECK.pdf [TALK-SCRIPT.md]
```

With a script it writes `DECK-present.pdf` (deck + one hidden text annotation per page), then
opens it. Then, with the **English keyboard layout**, press `f`: slides go fullscreen on the last
screen (projector), presenter view on the main screen. `x` swaps screens if reversed.
Display settings: mirroring OFF.

Keys: →/←/space next/prev · `f`/Esc fullscreen on/off · `x` swap screens · `j`/`k` scroll notes ·
`+`/`-`/`0` notes size · `t` timer start/stop · `.` black screen · `l` laser · `?` all keys.

Example project using it: `~/brainlab/ops/lectures/ai-for-research/slides/` (`present.sh` there wraps this flow;
script = `ops/lectures/ai-for-research/talk-script.md` in the vault).

## Files

| File | Role |
|---|---|
| `scripts/present.sh` | build notes PDF (optional), (re)patch app script, launch |
| `scripts/make_notes_pdf.py` | md sections → hidden text annots; LaTeX `$...$` → Unicode; needs pymupdf (`uv run --with pymupdf`) |
| `scripts/apply_patches.py` | patches the app's own `presentation.py` into `~/.local/share/presenter-mode/presentation_brain.py` |

Patches (all marked `BRAIn` in the output): help overlay hidden; notes full width + smaller,
auto-fitting font; `j`/`k` scrolling; next slide fills the right column; space = next slide;
`0` resets to the new default; bundled PyObjC path. Each anchor must match exactly once, so if
the app updates and the code moved, `apply_patches.py` stops with the failing anchor: re-diff
against the new upstream and fix that one replacement.

## Gotchas (each cost time once)

- **Never edit inside the app bundle.** Changing `Présentation.app/Contents/...` breaks its
  signature → macOS: "is damaged and can't be opened, move to Trash". The patched script runs
  outside the bundle with `/usr/bin/python3` and imports the app's bundled PyObjC
  (`Contents/Resources/packages/<py-version>`). Without that path: "can not import the PyObjC package".
- **Russian keyboard layout** silently breaks one-letter keys (`f`, `x`, `t`, `j`/`k`). Arrows work.
- **Every key path must end in `refresher.refresh()`** inside `keyDown_`. An early `return` after
  changing page updates only the laptop (1-s clock timer) and leaves the projector 2–3 s behind —
  this was the "lag" bug of the first space patch.
- Notes source must have exactly one section per PDF page (overlays count as pages); the builder
  warns when counts differ.
- `animate` animations play only when the page is entered by navigation (not on the start page
  given by `--page`).
- **pdfpc does not work** on macOS with two Retina displays (presenter window lands behind the
  projector window; monitor names are `(null)`, so `-1/-2` cannot fix it). Its first start also
  hangs on `gst-plugin-scanner` until `gst-inspect-1.0` builds the GStreamer cache. Do not retry it.
- Acrobat Reader plays the animations but has no presenter view.
