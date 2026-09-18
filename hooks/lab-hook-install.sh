#!/usr/bin/env bash
# Поставить хук записи в общую базу лаборатории на этой машине.
#
# Ставится одному человеку: у каждого свой ключ и своё имя, потому что в общей базе
# должно быть видно, кто что записал.
set -eu

ЗДЕСЬ="$(cd "$(dirname "$0")" && pwd)"
ХУК="$HOME/.claude/hooks/lab-knowledge-hook.py"
# Ставится из репозитория, если его там ещё нет: у нового человека каталога хуков
# может не быть вовсе, и требовать, чтобы он сам скопировал файл, — лишний шаг.
if [ ! -f "$ХУК" ] && [ -f "$ЗДЕСЬ/lab-knowledge-hook.py" ]; then
  mkdir -p "$(dirname "$ХУК")"
  cp "$ЗДЕСЬ/lab-knowledge-hook.py" "$ХУК"
  echo "хук скопирован: $ХУК"
fi
НАСТРОЙКИ="$HOME/.config/brainlab/lab-hook.json"
ПИТОН="${PYTHON:-python3}"

[ -f "$ХУК" ] || { echo "нет файла хука: $ХУК"; exit 1; }

mkdir -p "$(dirname "$НАСТРОЙКИ")"
if [ ! -f "$НАСТРОЙКИ" ]; then
  printf 'адрес базы [http://127.0.0.1:8000/mcp]: '; read -r адрес
  printf 'ключ доступа: '; read -r ключ
  printf 'ваше имя для подписи записей: '; read -r имя
  cat > "$НАСТРОЙКИ" <<JSON
{
  "enabled": true,
  "endpoint": "${адрес:-http://127.0.0.1:8000/mcp}",
  "token": "$ключ",
  "author": "$имя"
}
JSON
  chmod 600 "$НАСТРОЙКИ"
  echo "настройки записаны: $НАСТРОЙКИ"
else
  echo "настройки уже есть, оставляю: $НАСТРОЙКИ"
fi

"$ПИТОН" - "$ХУК" <<'PY'
import json, sys
from pathlib import Path
хук = sys.argv[1]
p = Path.home() / ".claude" / "settings.json"
d = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
hooks = d.setdefault("hooks", {}).setdefault("Stop", [])
команда = f"python3 {хук}"
уже_есть = any(команда in json.dumps(правило, ensure_ascii=False) for правило in hooks)
if уже_есть:
    print("хук уже прописан в settings.json")
else:
    hooks.append({"hooks": [{"type": "command", "command": команда}]})
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("хук прописан в Stop")
PY
echo "готово. Разметка: ЛАБ-ГИПОТЕЗА / ЛАБ-РЕШЕНИЕ / ЛАБ-ЧИСЛО / ЛАБ-ВОПРОС"
