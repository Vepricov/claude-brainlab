#!/usr/bin/env python3
"""Налить машине свод правил базы из справочника.

Источник один и лежит в GitLab: `brainlab/handbook/canon.md`. У машины одна копия,
`~/.claude/skills/lab-knowledge/references/canon.md`, и её читают агент, хуки и навык. Второй копии нет нарочно:
копии совпадают только пока их не правят.

    canon_sync.py            налить (ничего не делает, если уже совпадает)
    canon_sync.py --check    только сказать, совпадает ли; ничего не писать

Сети нет — говорит об этом и выходит с кодом 2, не трогая лежащую копию: устаревший свод
полезнее отсутствующего.
"""
from __future__ import annotations

import argparse
import pathlib
import ssl
import sys
import urllib.error
import urllib.request

SOURCE = "brainlab/handbook/canon.md"
# Свод лежит У НАВЫКА, а не в правилах сессии. В `~/.claude/rules/` файлы грузятся в
# контекст КАЖДОГО хода, и свод на 31 тысячу знаков съедал там 37% всей подложки —
# при том что нужен он ровно тогда, когда пишут в базу. Теперь его читают по факту
# работы, через навык `lab-knowledge`, а правило сессии только велит это сделать.
MIRROR = (pathlib.Path.home() / ".claude" / "skills" / "lab-knowledge"
          / "references" / "canon.md")
CONF = pathlib.Path.home() / ".config" / "brainlab"
TIMEOUT = 15


def fetch() -> str:
    """Свод из справочника. Сертификат базы самоподписанный, поэтому цепочка не проверяется."""
    url = CONF.joinpath("git-url").read_text(encoding="utf-8").strip()
    token = CONF.joinpath("git-token").read_text(encoding="utf-8").strip()
    address = (f"{url}/api/v4/projects/brainlab%2Fhandbook"
               "/repository/files/canon.md/raw?ref=main")
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    request = urllib.request.Request(address, headers={"PRIVATE-TOKEN": token})
    with urllib.request.urlopen(request, timeout=TIMEOUT, context=context) as answer:
        return answer.read().decode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="только сверить, ничего не писать")
    args = parser.parse_args()

    for name in ("git-url", "git-token"):
        if not CONF.joinpath(name).is_file():
            print(f"нет {CONF / name}: поставь доступ к базе, bash docs/lab/install.sh")
            return 2
    try:
        source = fetch()
    except (urllib.error.URLError, OSError) as beda:
        print(f"справочник не ответил ({beda}); копия на месте не тронута: {MIRROR}")
        return 2

    here = MIRROR.read_text(encoding="utf-8") if MIRROR.is_file() else None
    if here == source:
        print(f"свод совпадает с источником {SOURCE}")
        return 0
    if args.check:
        print(f"копия разошлась с источником {SOURCE}: {MIRROR}")
        return 1
    MIRROR.parent.mkdir(parents=True, exist_ok=True)
    MIRROR.write_text(source, encoding="utf-8")
    print(f"налит свод из {SOURCE}: {MIRROR}"
          + ("" if here is None else " (копия обновлена)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
