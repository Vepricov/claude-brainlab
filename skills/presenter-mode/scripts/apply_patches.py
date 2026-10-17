"""Patch Présentation.app's presenter script for comfortable talks with long speaker notes.

Reads the installed app's own script (/Applications/Présentation.app/Contents/MacOS/presentation.py)
and writes a patched copy that runs OUTSIDE the app bundle (so the signed bundle is never modified:
editing it makes macOS call the app "damaged"). Patches:

  * help overlay hidden by default (`?` still shows it)
  * notes use the full window width; smaller current slide, next slide fills the right column
  * notes font starts smaller and auto-shrinks until the note fits (>= 11 pt)
  * `j` / `k` scroll a note that is still too long; scrolling resets on page change
  * space = next slide (upstream: toggles timer / auto-animation), both screens redraw at once
  * `0` resets the notes font to the new default
  * bundled PyObjC is found from the installed app

Every patch asserts its anchor exists exactly once, so an app update that moves code fails loudly.

Usage: python3 apply_patches.py [OUT]   (default OUT: ~/.local/share/presenter-mode/presentation_brain.py)
"""
from __future__ import annotations

import sys
from pathlib import Path

APP_SCRIPT = Path("/Applications/Présentation.app/Contents/MacOS/presentation.py")
DEFAULT_OUT = Path.home() / ".local/share/presenter-mode/presentation_brain.py"

PATCHES: list[tuple[str, str]] = [
    ("#! /usr/bin/python3\n",
     "#! /usr/bin/python3\n"
     "# Patched copy of /Applications/Présentation.app/Contents/MacOS/presentation.py (BRAIn lines marked).\n"),
    ("""	sys.path.insert(0, os.path.join(
		os.path.dirname(os.path.realpath(__file__)), *path, 'packages', python_version))
""",
     """	sys.path.insert(0, os.path.join(
		os.path.dirname(os.path.realpath(__file__)), *path, 'packages', python_version))
# BRAIn: running outside the bundle, use the installed app's bundled PyObjC
sys.path.insert(0, os.path.join('/Applications/Pr\\u00e9sentation.app/Contents/Resources/packages', python_version))
"""),
    ("\tshow_help = True\n",
     "\tshow_help = False  # BRAIn: help hidden by default, '?' shows it\n"),
    ("\tnotes_scale = .75\n",
     "\tnotes_scale = .55  # BRAIn: smaller default notes font (+/-/0 still work)\n"
     "\tnotes_page, notes_offset, notes_overflow = -1, 0., 0.  # BRAIn: notes scrolling\n"),
    ("\t\tcurrent_width = (width-3*margin)*2/3.\n",
     "\t\tcurrent_width = (width-3*margin)*.56  # BRAIn: smaller current slide, more room for notes\n"),
    ("""		note.drawInRect_withAttributes_(
			((margin, font_size), (current_width, height-current_height-2.5*margin)),
			{
				NSFontAttributeName:            NSFont.labelFontOfSize_(font_size*self.notes_scale),
				NSForegroundColorAttributeName: NSColor.whiteColor(),
			}
		)
""",
     """		# BRAIn: notes use full width; font shrinks until the note fits (>= 11 pt),
		# then j/k scroll a note that is still too long; scrolling resets on page change
		notes_w, notes_h = width-2*margin, height-current_height-2.5*margin
		if self.notes_page != current_page:
			self.notes_page, self.notes_offset = current_page, 0.
		fs = font_size*self.notes_scale
		while True:
			attrs = {
				NSFontAttributeName:            NSFont.labelFontOfSize_(fs),
				NSForegroundColorAttributeName: NSColor.whiteColor(),
			}
			text_h = note.boundingRectWithSize_options_attributes_((notes_w, 1e6), 1, attrs).size.height
			if text_h <= notes_h or fs <= 11:
				break
			fs = max(11, fs*.93)
		self.notes_overflow = max(0., text_h-notes_h)
		self.notes_offset = min(self.notes_offset, self.notes_overflow)
		NSGraphicsContext.saveGraphicsState()
		NSBezierPath.clipRect_(((margin, font_size), (notes_w, notes_h)))
		note.drawInRect_withAttributes_(
			((margin, font_size-self.notes_overflow+self.notes_offset), (notes_w, notes_h+self.notes_overflow)),
			attrs
		)
		NSGraphicsContext.restoreGraphicsState()
		if self.notes_overflow > 0:
			more = "\\u2193 j / k \\u2191" if self.notes_offset < self.notes_overflow else "k \\u2191"
			_s(more).drawAtPoint_withAttributes_((margin+notes_w-60, 2), {
				NSFontAttributeName:            NSFont.labelFontOfSize_(11),
				NSForegroundColorAttributeName: NSColor.grayColor(),
			})
"""),
    ("\t\tr = current_width/2./w\n",
     "\t\tr = (width-3*margin-current_width)/w  # BRAIn: next slide fills the right column\n"),
    ("""		elif c == ' ': # play/pause video
			if movie_view.isHidden(): # or...""",
     """		elif c == ' ' and movie_view.isHidden(): # BRAIn: space = next slide
			next_page()  # no return: fall through to refresher.refresh() so both screens redraw now

		elif c == ' ': # play/pause video
			if movie_view.isHidden(): # or..."""),
    ("""		elif c in "+=-_0)": # notes or web view scale""",
     """		elif c in "jk": # BRAIn: scroll speaker notes
			step = 60. if c == 'j' else -60.
			self.notes_offset = min(max(0., self.notes_offset+step), self.notes_overflow)

		elif c in "+=-_0)": # notes or web view scale"""),
    ("""				else:
					self.notes_scale = 1.
""",
     """				else:
					self.notes_scale = .55  # BRAIn: reset to our default
"""),
]


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    if not APP_SCRIPT.exists():
        sys.stderr.write(f"Présentation.app not installed: {APP_SCRIPT} missing\n")
        return 1
    text = APP_SCRIPT.read_text(encoding="utf-8")
    for old, new in PATCHES:
        if text.count(old) != 1:
            sys.stderr.write(f"patch anchor found {text.count(old)}x (app updated?):\n{old[:120]}\n")
            return 1
        text = text.replace(old, new)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
