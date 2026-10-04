#!/usr/bin/env bash
# Поставить себе работу с базой лаборатории: правило для агента и хук начала сессии.
#
# Запускается из клона открытого репозитория лаборатории:
#
#   bash docs/lab/install.sh
#
# Ставит пять вещей и ничего больше:
#
#   ~/.claude/rules/lab.md              КАК писать в базу. Читается один раз за сессию.
#   ~/.claude/rules/lab-canon.md        СВОД правил: на него ссылаются правило, навык и хуки.
#   ~/.claude/skills/lab-knowledge/     навык: как пишется страница утверждения и серии.
#   ~/.claude/hooks/lab-where-am-i.py   ГДЕ ты и что тебя ждёт. Печатает только состояние.
#   ~/.local/bin/lab                    ветка, задачи, вердикт — из терминала.
#
# Свод не копируется из этого репозитория: его источник лежит в базе,
# `brainlab/handbook/canon.md`, и наливает его `scripts/canon_sync.py`. Поэтому шаг со сводом
# идёт ПОСЛЕ ключа: без ключа справочник не ответит.
#
# Повторный запуск безопасен: он сверяет и доливает, а не переписывает твои настройки.
set -eu

here="$(cd "$(dirname "$0")/../.." && pwd)"
home="${HOME}"
rules="$home/.claude/rules"
hooks_dir="$home/.claude/hooks"
settings="$home/.claude/settings.json"
conf="$home/.config/brainlab"
py="${PYTHON:-python3}"

mkdir -p "$rules" "$hooks_dir" "$home/.local/bin" "$conf"

# 1. правило: как писать
cp "$here/docs/lab/lab.md" "$rules/lab.md"
echo "правило:  $rules/lab.md"

# 2. хук начала сессии
cp "$here/hooks/lab-where-am-i.py" "$hooks_dir/lab-where-am-i.py"
chmod +x "$hooks_dir/lab-where-am-i.py"
echo "хук:      $hooks_dir/lab-where-am-i.py"

# 3. навык: подробности по факту работы, не в контексте
skills="$home/.claude/skills"
mkdir -p "$skills"
rsync -a --delete --exclude __pycache__ "$here/skills/lab-knowledge/" "$skills/lab-knowledge/"
echo "навык:    $skills/lab-knowledge/"

# 4. помощник
ln -sf "$here/scripts/lab" "$home/.local/bin/lab"
echo "помощник: $home/.local/bin/lab -> $here/scripts/lab"

# Регистрация хука в настройках. Правим JSON питоном, а не руками: в settings.json лежат
# и другие хуки человека, и затирать их нельзя.
"$py" - "$settings" "$hooks_dir/lab-where-am-i.py" <<'PY'
import json, sys
from pathlib import Path

settings, hook = Path(sys.argv[1]), sys.argv[2]
data = {}
if settings.is_file():
    try:
        data = json.loads(settings.read_text(encoding="utf-8"))
    except ValueError:
        sys.exit(f"не разбирается {settings}: поправь его руками и запусти снова")
command = f"{sys.executable} {hook}"
events = data.setdefault("hooks", {}).setdefault("SessionStart", [])
for group in events:
    for entry in group.get("hooks") or []:
        if "lab-where-am-i" in str(entry.get("command", "")):
            entry["command"] = command
            settings.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                                encoding="utf-8")
            print("хук уже был зарегистрирован, путь обновлён")
            raise SystemExit
events.append({"hooks": [{"type": "command", "command": command}]})
settings.parent.mkdir(parents=True, exist_ok=True)
settings.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("хук зарегистрирован на начало сессии")
PY

# Ключ и логин. Их выдаёт бот вместе с доступом к базе; без них помощник не работает.
for name in git-url git-token gitlab-login; do
  if [ ! -s "$conf/$name" ]; then
    case "$name" in
      git-url) hint="адрес базы [https://68-183-24-188.sslip.io:9445]";;
      git-token) hint="ключ агента (его присылает бот вместе с доступом)";;
      gitlab-login) hint="твой логин в GitLab (он же в письме бота)";;
    esac
    printf '%s: ' "$hint"
    read -r value
    if [ "$name" = git-url ] && [ -z "$value" ]; then
      value="https://68-183-24-188.sslip.io:9445"
    fi
    [ -n "$value" ] || { echo "пусто — пропускаю $name"; continue; }
    printf '%s\n' "$value" > "$conf/$name"
    chmod 600 "$conf/$name"
    echo "записал: $conf/$name"
  fi
done

# Личный ключ принадлежит учётке агента `<логин>-agent`, и под этим именем он ходит в git.
# Спрашивать это незачем: имя выводится из логина человека.
if [ ! -s "$conf/git-login" ] && [ -s "$conf/gitlab-login" ]; then
  printf '%s-agent\n' "$(cat "$conf/gitlab-login")" > "$conf/git-login"
  chmod 600 "$conf/git-login"
  echo "записал: $conf/git-login"
fi

# Прежний хук записи по разметке убирается ЦЕЛИКОМ, а не выключается.
#
# Он разбирал в стенограмме строки вида `ЛАБ-ГИПОТЕЗА: ... | опровергается: ...` и писал в
# базу вызовом MCP. С переездом знания в git этот путь отклоняется по построению: запись —
# только слиянием предложения. Раньше установщик лишь снимал включатель, и вышло хуже, чем
# ничего: файл оставался на месте, оставался зарегистрирован на Stop, и агент, прочитав его
# шапку, продолжал уверять, что разметка работает. Поэтому теперь снимается регистрация,
# удаляется файл и удаляется его настройка - в ней ещё и лежал ключ к мёртвой службе.
"$py" - "$home" <<'CLEANUP'
import json, sys
from pathlib import Path

home = Path(sys.argv[1])
settings = home / ".claude" / "settings.json"
hook_file = home / ".claude" / "hooks" / "lab-knowledge-hook.py"
config = home / ".config" / "brainlab" / "lab-hook.json"
removed = []

if settings.is_file():
    try:
        data = json.loads(settings.read_text(encoding="utf-8"))
    except ValueError:
        data = None
    if isinstance(data, dict) and isinstance(data.get("hooks"), dict):
        changed = 0
        for event, groups in list(data["hooks"].items()):
            kept_groups = []
            for group in groups:
                kept = [h for h in group.get("hooks", [])
                        if "lab-knowledge-hook.py" not in (h.get("command") or "")]
                changed += len(group.get("hooks", [])) - len(kept)
                if kept:
                    group["hooks"] = kept
                    kept_groups.append(group)
            if kept_groups:
                data["hooks"][event] = kept_groups
            else:
                del data["hooks"][event]
        if changed:
            settings.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8")
            removed.append("снята регистрация хука разметки: " + str(changed))

for path in (hook_file, config):
    if path.exists():
        path.unlink()
        removed.append("удалён " + str(path))

for line in removed:
    print("  " + line)
if removed:
    print("  запись в базу идёт предложением: ветка, правка, коммит, push")
CLEANUP

echo
echo "проверка:"
"$py" -c "import ast,sys;ast.parse(open(sys.argv[1]).read())" "$hooks_dir/lab-where-am-i.py" \
  && echo "  хук разбирается"
if [ -s "$conf/git-token" ]; then
  # Свод наливается здесь: ключ уже есть, и ответ справочника заодно проверяет ключ.
  if "$py" "$here/scripts/canon_sync.py"; then
    echo "  ключ работает: справочник ответил"
  else
    echo "  ключ есть, но справочник не ответил — проверь адрес в $conf/git-url"
  fi
fi
echo
echo "дальше: открой свою работу — \`lab here <слаг>\` — и работай обычным git."
echo "как писать, читается один раз: $rules/lab.md"
echo "свод правил, на него ссылается всё: $rules/lab-canon.md"
