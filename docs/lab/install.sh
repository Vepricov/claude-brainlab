#!/usr/bin/env bash
# Поставить себе работу с базой лаборатории: правило для агента и хук начала сессии.
#
# Запускается из клона открытого репозитория лаборатории:
#
#   bash docs/lab/install.sh
#
# Ставит три вещи и ничего больше:
#
#   ~/.claude/rules/lab.md              КАК писать в базу. Читается один раз за сессию.
#   ~/.claude/hooks/lab-where-am-i.py   ГДЕ ты и что тебя ждёт. Печатает только состояние.
#   ~/.local/bin/lab                    ветка, предложение, задачи, вердикт — из терминала.
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

# 3. помощник
ln -sf "$here/scripts/lab" "$home/.local/bin/lab"
echo "помощник: $home/.local/bin/lab -> $here/scripts/lab"

# Регистрация хука в настройках. Правим JSON питоном, а не руками: в settings.json лежат
# и другие хуки человека, и затирать их нельзя.
"$py" - "$settings" "$hooks_dir/lab-where-am-i.py" <<'PY'
import json, sys
from pathlib import Path

файл, хук = Path(sys.argv[1]), sys.argv[2]
данные = {}
if файл.is_file():
    try:
        данные = json.loads(файл.read_text(encoding="utf-8"))
    except ValueError:
        sys.exit(f"не разбирается {файл}: поправь его руками и запусти снова")
команда = f"{sys.executable} {хук}"
события = данные.setdefault("hooks", {}).setdefault("SessionStart", [])
for группа in события:
    for запись in группа.get("hooks") or []:
        if "lab-where-am-i" in str(запись.get("command", "")):
            запись["command"] = команда
            файл.write_text(json.dumps(данные, ensure_ascii=False, indent=2),
                            encoding="utf-8")
            print("хук уже был зарегистрирован, путь обновлён")
            raise SystemExit
события.append({"hooks": [{"type": "command", "command": команда}]})
файл.parent.mkdir(parents=True, exist_ok=True)
файл.write_text(json.dumps(данные, ensure_ascii=False, indent=2), encoding="utf-8")
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
    print("  запись в базу идёт предложением: ветка, правка, `lab pr`")
CLEANUP

echo
echo "проверка:"
"$py" -c "import ast,sys;ast.parse(open(sys.argv[1]).read())" "$hooks_dir/lab-where-am-i.py" \
  && echo "  хук разбирается"
if [ -s "$conf/git-token" ]; then
  "$home/.local/bin/lab" open >/dev/null 2>&1 \
    && echo "  ключ работает: база отвечает" \
    || echo "  ключ есть, но база не ответила — проверь адрес в $conf/git-url"
fi
echo
echo "дальше: открой свою работу — \`lab here <слаг>\` — и работай обычным git."
echo "как писать, читается один раз: $rules/lab.md"
