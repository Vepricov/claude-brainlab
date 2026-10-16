#!/usr/bin/env python3
"""Проверить сторож старых путей: отказ на запись, тишина на чтении и на упоминании."""
import json
import subprocess

STOROZH = "/Users/andrey/.claude/hooks/no-old-paths.py"
P = "/Users/andrey/" + "Papers"          # склеено, чтобы не мозолить глаза самому сторожу
S = "~/" + "Staff"
PR = "/Users/andrey/" + "Projects"

SLUCHAI = [
    ("запись в старый путь", {"tool_name": "Write",
                              "tool_input": {"file_path": P + "/x.md"}}, 2),
    ("mkdir в старый путь", {"tool_name": "Bash",
                             "tool_input": {"command": f"mkdir -p {S}/zzz"}}, 2),
    ("перенаправление в старый путь", {"tool_name": "Bash",
                                       "tool_input": {"command": f"echo x > {S}/a.txt"}}, 2),
    ("cp в старый путь", {"tool_name": "Bash",
                          "tool_input": {"command": f"cp a.md {P}/b.md"}}, 2),
    ("упоминание в тексте heredoc", {"tool_name": "Bash",
                                     "tool_input": {"command": f"cat > a.md <<EOF\nписать в {S} нельзя\nEOF"}}, 0),
    ("поиск с перенаправлением ошибок", {"tool_name": "Bash",
                                         "tool_input": {"command": f'grep -rn "{PR}" skills/ 2>/dev/null | head'}}, 0),
    ("чтение старого пути", {"tool_name": "Bash", "tool_input": {"command": f"ls {P}"}}, 0),
    ("запись в новое дерево", {"tool_name": "Write",
                               "tool_input": {"file_path": "/Users/andrey/brainlab/x.md"}}, 0),
    ("архив читать можно", {"tool_name": "Bash",
                            "tool_input": {"command": "tar -tzf ~/archive/x.tar.gz"}}, 0),
    ("обычная работа в дереве", {"tool_name": "Bash",
                                 "tool_input": {"command": "cp ~/brainlab/a.md ~/brainlab/b.md"}}, 0),
]

ploho = 0
for imya, payload, zhdem in SLUCHAI:
    r = subprocess.run(["python3", STOROZH], input=json.dumps(payload),
                       capture_output=True, text=True)
    ok = r.returncode == zhdem
    ploho += 0 if ok else 1
    print(f"   {'ок    ' if ok else 'НЕ ТАК'} {imya}: код {r.returncode}, ждали {zhdem}")
print(f"не сошлось: {ploho}")
