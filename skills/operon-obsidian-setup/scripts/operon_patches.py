#!/usr/bin/env python3
"""Local display/behavior patches for Operon main.js (idempotent).

Usage: python3 operon_patches.py /path/to/vault
Re-run after EVERY Operon update (updates overwrite main.js).
Target version: Operon 2.2.1. On another version the anchors won't match and
the script aborts without writing. Stored data is untouched (display-only).
"""
import shutil
import sys
from pathlib import Path

if len(sys.argv) < 2:
    sys.exit("usage: operon_patches.py <vault>")
VAULT = Path(sys.argv[1]).expanduser().resolve()
MAIN = VAULT / ".obsidian/plugins/operon/main.js"
if not MAIN.exists():
    sys.exit(f"not found: {MAIN}")

_EMOJI = [
    "🤖","🧪","🔬","🧠","💡","📊","📈","📉","📋","📝","📄","📚","📖","✍️","🗂️",
    "📁","📌","📎","✅","⏳","⏰","📅","🗓️","🎯","🏁","🚩","⭐","🌟","💎","🔥",
    "⚡","🚀","🛠️","⚙️","🔧","🔩","🐛","🧩","🔁","♻️","🔒","🔑","🛡️","⚠️","❗",
    "❓","💬","📣","🔔","👀","💻","🖥️","⌨️","💾","🗄️","🌐","🔗","📡","🛰️","🧬",
    "⚗️","📐","📏","🧮","🎨","🖼️","🏗️","🧱","💰","📦","🏷️","🧭","🗺️","🎓","🏆","✨",
]
EMOJI_ARRAY = "/*emoji-icons*/[" + ",".join('"%s"' % e for e in _EMOJI) + "]"

PATCHES = [
    # 1. table cell status display (strip "Project." prefix)
    (
        '_sv=(i==="status"',
        'function rre(i,n,e){if(!ore(i,e))return[{rawValue:n,displayValue:n}];',
        'function rre(i,n,e){if(!ore(i,e)){var _sv=(i==="status"&&typeof n==="string"'
        '&&n.indexOf(".")>=0)?n.slice(n.indexOf(".")+1):n;'
        'return[{rawValue:n,displayValue:_sv}];}',
    ),
    # 2. compact chip status label
    (
        'n==="status"&&typeof e==="string"',
        'function Jn(i,n,e,t=!1,a="default",r=!0,o=null,s=null,l=null){return{key:n,label:e,',
        'function Jn(i,n,e,t=!1,a="default",r=!0,o=null,s=null,l=null)'
        '{if(n==="status"&&typeof e==="string"){var _sp=e.indexOf(".");'
        'if(_sp>=0)e=e.slice(_sp+1);}return{key:n,label:e,',
    ),
    # 3. assignees picker sourced from people/ cards (имя / name / basename)
    (
        't==="assignees"){try{for(let _pf',
        '(!g||n8(h,g))&&a.set(m,h)};for(let c of n){',
        '(!g||n8(h,g))&&a.set(m,h)};'
        'if(t==="assignees"){try{for(let _pf of i.vault.getMarkdownFiles()){'
        'if(_pf.parent&&_pf.parent.path==="people"){'
        'let _pc=i.metadataCache.getFileCache(_pf),'
        '_pm=_pc&&_pc.frontmatter,'
        '_pn=(_pm&&(_pm["имя"]||_pm.name))||_pf.basename;'
        'if(_pn)r(String(_pn));}}}catch(_e){}}'
        'for(let c of n){',
    ),
    # 4. Xp icon-chip renderer: render emoji taskIcon values as text
    (
        '/[^a-z0-9-]/.test(n.icon)',
        '(0,Dd.setIcon)(e,n.icon),e.querySelector("svg")||(0,Dd.setIcon)(e,"text"),',
        '(n.icon&&/[^a-z0-9-]/.test(n.icon)?(e.textContent=n.icon):'
        '((0,Dd.setIcon)(e,n.icon),e.querySelector("svg")||(0,Dd.setIcon)(e,"text"))),',
    ),
    # 5. Task Creator toolbar taskIcon preview: emoji as text
    (
        '/[^a-z0-9-]/.test(this.draft.taskIcon.trim())',
        'r?a.appendChild(r):(0,en.setIcon)(a,this.resolveFieldIcon(e))',
        'r?a.appendChild(r):(/[^a-z0-9-]/.test(this.draft.taskIcon.trim())'
        '?(a.textContent=this.draft.taskIcon.trim())'
        ':(0,en.setIcon)(a,this.resolveFieldIcon(e)))',
    ),
    # 6. Task Editor taskIcon preview swatch: emoji as text
    (
        'if(d&&/[^a-z0-9-]/.test(d)){r.textContent=d',
        'p=d?[d]:["obsidian-new","obsidian-logo","gem","hexagon"];for(let h of p){',
        'p=d?[d]:["obsidian-new","obsidian-logo","gem","hexagon"];'
        'if(d&&/[^a-z0-9-]/.test(d)){r.textContent=d;_(r,u("taskEditor","taskIcon"));'
        'r.classList.toggle("has-icon",!0);return;}for(let h of p){',
    ),
    # 7. Task-icon picker SOURCE: emoji palette instead of Lucide icon ids
    (
        '/*emoji-icons*/[',
        '(0,Ay.getIconIds)().slice().sort((I,C)=>I.localeCompare(C,"en"))',
        EMOJI_ARRAY,
    ),
    # 8. Task-icon picker CELL render: draw emoji as text
    (
        'R?O.appendChild(R):(O.textContent=x)',
        'R=(0,Ay.getIcon)(x);R&&O.appendChild(R)',
        'R=(0,Ay.getIcon)(x);R?O.appendChild(R):(O.textContent=x)',
    ),
    # 9. vv resolver: let an emoji taskIcon pass through instead of lucide fallback
    (
        '/[^a-z0-9-]/.test(t)?t:e)}',
        'if(i!=="taskIcon")return e;let t=Fe(n);return t&&(0,Dd.getIcon)(t)?t:e}',
        'if(i!=="taskIcon")return e;let t=Fe(n);'
        'return t&&(0,Dd.getIcon)(t)?t:(t&&/[^a-z0-9-]/.test(t)?t:e)}',
    ),
]

def main():
    src = MAIN.read_text(encoding="utf-8")
    bak = MAIN.with_suffix(".js.prepatch")
    if not bak.exists():
        shutil.copy2(MAIN, bak)
        print(f"backup: {bak.name}")
    changed = 0
    for marker, anchor, repl in PATCHES:
        if marker in src:
            print(f"already patched: {marker[:26]}…")
            continue
        if src.count(anchor) != 1:
            print(f"ERROR anchor not unique/found ({src.count(anchor)}x): {anchor[:44]}…")
            print("      Operon version differs from 2.2.1 — re-derive anchors. Aborting (no partial write).")
            return 1
        src = src.replace(anchor, repl, 1)
        changed += 1
        print(f"patched: {marker[:26]}…")
    if changed:
        MAIN.write_text(src, encoding="utf-8")
    print(f"done ({changed} new patch(es))")
    return 0

if __name__ == "__main__":
    sys.exit(main())
