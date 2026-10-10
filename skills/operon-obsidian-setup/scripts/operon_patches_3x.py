#!/usr/bin/env python3
"""Display patches for Operon 3.x main.js (idempotent).

Usage: python3 operon_patches_3x.py /path/to/vault [--revert]

Обновление плагина перезаписывает main.js, поэтому скрипт нужно прогонять заново после
каждого обновления. Якоря привязаны к минифицированному коду 3.0.1: на другой версии они
не совпадут, и скрипт откажется писать вообще, а не наполовину.

`operon_patches.py` рядом — это патчи под 2.2.1, они на 3.x не встают. Держим два файла,
потому что якоря разные, а смешивать версии в одном списке значит получать частичные
применения.
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

TARGET_VERSION = "3.0.1"

#: Подпись пункта статуса: «→ <следующий столбец>».
#
# Плагин подписывает пункт ТЕКУЩИМ статусом («Personal.Передал на проверку»), хотя клик
# переводит задачу на СЛЕДУЮЩИЙ столбец, и это читается как «задача уже там». Название
# следующего столбца известно только там, где на руках полные настройки: сама функция
# подписи их не получает. Поэтому список действий пропускается через свой хелпер в двух
# местах, где меню собирается, а имя конвейера («Personal.») из подписи убирается.
_HELPER = (
    'function _opNextStatusLabel(u,c,d){try{'
    'var cur=((c&&c.task&&c.task.fieldValues&&c.task.fieldValues.status)||"").trim();'
    'if(!cur)return u;'
    'var dot=cur.indexOf("."),pn=dot>=0?cur.slice(0,dot):"",sn=dot>=0?cur.slice(dot+1):cur;'
    'var pls=(d&&d.pipelines)||[],pl=null;'
    'for(var i=0;i<pls.length;i++){if(pls[i]&&pls[i].name===pn){pl=pls[i];break;}}'
    'if(!pl||!pl.statuses||!pl.statuses.length)return u;'
    'var idx=-1;'
    'for(var j=0;j<pl.statuses.length;j++){if(pl.statuses[j].label===sn){idx=j;break;}}'
    'if(idx<0)return u;'
    'var nx=pl.statuses[(idx+1)%pl.statuses.length];'
    'return u.map(function(a){return a&&a.id==="taskStatus"'
    '?Object.assign({},a,{label:"\\u2192 "+nx.label}):a;});'
    '}catch(e){return u;}}'
)

#: (маркер уже применённого патча, якорь, замена)
PATCHES: list[tuple[str, str, str]] = [
    ("function _opNextStatusLabel(", "function Ld(i,t,e,n=[])", _HELPER + "function Ld(i,t,e,n=[])"),
    (
        "_opNextStatusLabel(Ld(c,d.contextualMenuActionAllowlist",
        "=Ld(c,d.contextualMenuActionAllowlist,d.contextualMenuSurfaceActionMatrix,"
        "d.keyMappings)",
        "=_opNextStatusLabel(Ld(c,d.contextualMenuActionAllowlist,"
        "d.contextualMenuSurfaceActionMatrix,d.keyMappings),c,d)",
    ),
    (
        "_opNextStatusLabel(Ld(a,o.contextualMenuActionAllowlist",
        "=Ld(a,o.contextualMenuActionAllowlist,o.contextualMenuSurfaceActionMatrix,"
        "o.keyMappings)",
        "=_opNextStatusLabel(Ld(a,o.contextualMenuActionAllowlist,"
        "o.contextualMenuSurfaceActionMatrix,o.keyMappings),a,o)",
    ),
]


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit("usage: operon_patches_3x.py <vault> [--revert]")
    vault = Path(sys.argv[1]).expanduser().resolve()
    main_js = vault / ".obsidian/plugins/operon/main.js"
    if not main_js.exists():
        sys.exit(f"не найден: {main_js}")

    manifest = (vault / ".obsidian/plugins/operon/manifest.json").read_text(encoding="utf-8")
    if f'"version": "{TARGET_VERSION}"' not in manifest:
        print(f"ВНИМАНИЕ: патчи писались под Operon {TARGET_VERSION}, "
              f"в манифесте другая версия. Проверяю якоря — если не совпадут, ничего не пишу.")

    source = main_js.read_text(encoding="utf-8")
    if "--revert" in sys.argv:
        restored = source
        for marker, anchor, replacement in PATCHES:
            if replacement in restored:
                restored = restored.replace(replacement, anchor)
        if restored == source:
            print("нечего откатывать")
            return 0
        main_js.write_text(restored, encoding="utf-8")
        print("патчи откачены")
        return 0

    patched, applied, already = source, [], []
    for index, (marker, anchor, replacement) in enumerate(PATCHES, start=1):
        if marker in patched:
            already.append(index)
            continue
        if patched.count(anchor) != 1:
            sys.exit(f"патч {index}: якорь встречается {patched.count(anchor)} раз, "
                     f"ожидался ровно один. Ничего не записано.")
        patched = patched.replace(anchor, replacement)
        applied.append(index)

    if not applied:
        print(f"всё уже применено: {already}")
        return 0

    backup = main_js.with_suffix(f".js.bak-{datetime.now():%Y%m%d-%H%M%S}")
    shutil.copy2(main_js, backup)
    main_js.write_text(patched, encoding="utf-8")
    print(f"применено: {applied}" + (f", уже стояло: {already}" if already else ""))
    print(f"копия до правки: {backup.name}")
    print("перезапустить Obsidian, чтобы плагин перечитал main.js")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
