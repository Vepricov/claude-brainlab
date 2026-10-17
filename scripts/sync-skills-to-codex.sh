#!/bin/bash
# Держать скиллы Codex такими же, как у Claude Code.
#
# Зачем. Скиллы живут в двух каталогах: ~/.claude/skills читает Claude Code, ~/.agents/skills —
# Codex. Второй собрали один раз 09-06-2026 копией с заменой слова «Claude» на «Codex» и больше не
# обновляли. К 08-09-2026 разошлись 35 из 73 общих скиллов, и Codex работал по июньским снимкам:
# handoff-to-jarvis у него был версии 06-08 (135 строк против 280), с прошлым транспортом через
# jarvis-handoff-ingress, где разрешён ровно один проект. Из-за этого передача экспериментов
# упиралась в profile_missing, а агент вместо работы объяснял, что «адаптер не установлен».
#
# Почему копией, а не симлинком. Неизвестно, ходит ли загрузчик скиллов Codex по символическим
# ссылкам; если нет — он потеряет разом все скиллы. Копия гарантированно обнаруживается так же,
# как сейчас.
#
# Почему без замены «Claude»→«Codex». Та замена уже родила битые пути вида ~/.Codex/skills/... и
# ничего не даёт: скилл описывает, ЧТО делать, а не кто его читает. Содержимое переносится дословно.
#
# Что НЕ трогается: скиллы, которых нет у Claude Code (у Codex это 16 штук source-command-*) —
# они его собственные. Ничего в целевом каталоге не удаляется, кроме содержимого тех скиллов,
# которые переносятся.
set -uo pipefail

SRC="$HOME/.claude/skills"
DST="$HOME/.agents/skills"
BACKUP="$HOME/.agents/_stale/skills-before-sync-$(date +%d-%m-%Y)"
# Снимок нужен ровно для одного откатa, а копились они бесконечно: 16-10-2026 их было 31 на
# 180 МБ, и среди них по пятнадцать версий одного навыка. Держим только последний: источник
# навыков — git, и настоящий откат там.
rm -rf "$HOME/.agents/_stale" 2>/dev/null
DRY=${DRY:-}

[ -d "$SRC" ] || { echo "нет источника $SRC"; exit 1; }
[ -d "$DST" ] || { echo "нет цели $DST"; exit 1; }

changed=0; same=0; added=0
for path in "$SRC"/*/; do
    name=$(basename "$path")
    target="$DST/$name"

    # Совпадает целиком — не трогаем и не шумим.
    if [ -d "$target" ] && diff -rq --exclude=__pycache__ --exclude=.DS_Store "$path" "$target" >/dev/null 2>&1; then
        same=$((same + 1))
        continue
    fi

    if [ -n "$DRY" ]; then
        if [ -d "$target" ]; then echo "обновил бы: $name"; changed=$((changed + 1))
        else echo "добавил бы: $name"; added=$((added + 1)); fi
        continue
    fi

    # Разовая страховка: прежнее состояние целиком, чтобы любую правку можно было вернуть.
    if [ -d "$target" ] && [ ! -d "$BACKUP/$name" ]; then
        mkdir -p "$BACKUP"
        cp -R "$target" "$BACKUP/$name"
    fi

    rsync -a --delete --exclude='__pycache__' --exclude='.DS_Store' "$path" "$target/"
    if [ -d "$BACKUP/$name" ]; then echo "обновлён: $name"; changed=$((changed + 1))
    else echo "добавлен: $name"; added=$((added + 1)); fi
done

echo "итого: обновлено=$changed добавлено=$added без изменений=$same"
[ -d "$BACKUP" ] && echo "прежнее состояние: $BACKUP"
exit 0
