#!/usr/bin/env python3
"""Package only the reviewed public Obsidian starter files for Atlas."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / 'obsidian-setup'


def main():
    for name in ['hermes_obsidian_board.py','hermes_project_notes.py']:
        if (ROOT/'scripts'/name).read_bytes() != (KIT/'hermes'/name).read_bytes():
            raise SystemExit(f'Review and sync the portable Hermes source before packaging: {name}')
    files = sorted(p for p in KIT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc')
    for p in files:
        if p.is_symlink():
            raise SystemExit('Symlinks are not packaged')
        text = p.read_text(encoding='utf-8')
        if any(private in text for private in ['/Users/andrey','shkodnik1917','Веприков-Андрей']):
            raise SystemExit(f'Private identifier found: {p.relative_to(KIT)}')
    target = ROOT/'docs/lab-atlas/assets/obsidian-setup'
    target.mkdir(parents=True, exist_ok=True)
    archive = target/'lab-obsidian-setup.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files:
            item = zipfile.ZipInfo('lab-obsidian-setup/'+p.relative_to(KIT).as_posix(),(2026,9,10,0,0,0))
            item.compress_type=zipfile.ZIP_DEFLATED
            item.external_attr=0o644 << 16
            z.writestr(item,p.read_bytes())
    receipt={'files':len(files),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'plugins':16,'enabled':14}
    (target/'manifest.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))


if __name__=='__main__':
    main()
