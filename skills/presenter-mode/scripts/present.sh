#!/bin/zsh
# present.sh DECK.pdf [NOTES.md]
#   Presenter view on macOS via Présentation.app (patched, run outside the bundle).
#   With NOTES.md: builds DECK-present.pdf with one hidden note per page from "## Слайд N." sections.
#   Then: press f (ENGLISH layout) -> slides fullscreen on projector, presenter view on laptop.
set -e
HERE="${0:A:h}"
DECK="${1:?usage: present.sh DECK.pdf [NOTES.md]}"; DECK="${DECK:A}"
NOTES="${2:-}"
APP="/Applications/Présentation.app"
PATCHED="$HOME/.local/share/presenter-mode/presentation_brain.py"
[[ -d "$APP" ]] || { echo "Install Présentation.app first (see SKILL.md)"; exit 1; }
# re-patch when missing or when the app was updated
if [[ ! -f "$PATCHED" || "$APP/Contents/MacOS/presentation.py" -nt "$PATCHED" ]]; then
  /usr/bin/python3 "$HERE/apply_patches.py" "$PATCHED" >/dev/null
fi
SHOW="$DECK"
if [[ -n "$NOTES" ]]; then
  SHOW="${DECK:r}-present.pdf"
  export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
  uv run -q --with pymupdf python "$HERE/make_notes_pdf.py" "$DECK" "${NOTES:A}" -o "$SHOW" 2>&1 | grep -v 'MuPDF error' || true
fi
pkill -f 'presentation_brain.py' 2>/dev/null || true
(/usr/bin/python3 "$PATCHED" "$SHOW" >/dev/null 2>&1 &)
echo "opened $SHOW  (press f in ENGLISH layout for two screens)"
