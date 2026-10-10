# AlphaXiv Library Sync (applies to ALL agents, ALL sessions)

> Зеркал теперь два. AlphaXiv это витрина для чтения с телефона, а **общая база лаборатории в
> git** это то, что читают остальные участники: репозиторий на тему, страница на статью,
> рисунки рядом. Правила git-стороны лежат отдельно, в `~/.claude/rules/lab-git-literature.md`,
> и шаг туда обязателен в `paper-ingest` и `want-2-read` так же, как шаг на AlphaXiv.

The user's **local Obsidian `Literature/` is the master** paper library. The **AlphaXiv account**
(Codex MCP server `alphaxiv`, folder view = `alphaxiv.org/bookmarks`) is a **mirror** of it. Any
skill that changes the local library MUST propagate the change to AlphaXiv in the same run, so the
two never drift.

## Откуда берётся сам сервер

С 29-09-2026 AlphaXiv подключён **напрямую**, своим сервером
`https://api.alphaxiv.org/mcp/v1`, а не коннектором через claude.ai. Причина простая: коннектор
регулярно отваливался с `404 Server not found`, потому что жил в реестре claude.ai и зависел от
чужого обновления токена. Прямое подключение авторизуется само (OAuth 2.1 с обновлением) и
переживает перезапуск.

```bash
claude mcp add --transport http --scope user alphaxiv https://api.alphaxiv.org/mcp/v1
# затем /mcp в Claude Code — вход в браузере, один раз
```

Если OAuth всё же начнёт слетать, у alphaXiv есть постоянный ключ: Settings → API Keys на
alphaxiv.org, и тогда в `~/.claude.json` серверу дописывается
`"headers": {"Authorization": "Bearer <ключ>"}`. Это же единственный путь для неинтерактивных
прогонов — на сервере, в кроне, у Гермеса.

Имена инструментов при этом стали `mcp__alphaxiv__*` вместо прежних
`mcp__claude_ai_alphaXiv__*`. Набор тот же: `list_library`, `save_papers_to_folder`,
`move_papers_between_folders`, `remove_papers_from_folder`, `create_folder`, — поэтому все
правила ниже действуют без изменений.

## Когда локальный вход слетел: ходить с сервера

Сервер AlphaXiv в Claude Code на маке живёт на OAuth и после перезапуска отвечает
`Needs authentication`, а починить это можно только руками через `/mcp` в браузере. На
do-vpn тот же сервер подключён к Гермесу, его токен обновляется сам, поэтому правки
библиотеки надёжнее делать оттуда:

```bash
ssh do-vpn 'python3 /root/paper-agent/ax_call.py list_library "{}"'
ssh do-vpn 'python3 /root/paper-agent/ax_call.py save_papers_to_folder \
    "{\"folder_id\": \"<id>\", \"paper_ids_or_urls\": [\"2609.12345\"]}"'
```

Три грабли, на которых это ломалось:

- **Cloudflare отвергает запрос без внятного User-Agent**: `python-urllib` получает
  `1010 Access denied by browser signature`, а не отказ авторизации, и это сбивает с толку.
- **Адрес обновления токена лежит в метаданных провайдера**, `token_endpoint` =
  `https://api.alphaxiv.org/auth/oauth2/token`. Корень `/auth/` отвечает 404.
- **`move_papers_between_folders` не идемпотентен**: если статья уже есть в папке-цели,
  вызов молча оставляет её и в папке-источнике. Проверять надо составом папок, а не кодом
  ответа; лишнее членство снимается `remove_papers_from_folder`.

## Authoritative map
`~/.claude/alphaxiv-library-map.json` — соответствие темы её `folder_id` на AlphaXiv, плюс
`want_to_read_folder_id` и `personal_folder_id`. **Читать перед любой синхронизацией.** Если папку
пересоздали и id устарел, обновить через `list_library` и переписать файл.

**Устройство AlphaXiv с 29-09-2026.** В корне ровно две папки владельца: `personal` и
`Want to read`. Плюс служебные `My publications` и `Private Papers` — их не трогать никогда. Все
темы лежат внутри `personal`, и **имена совпадают буквально** со слагами тем в git и с папками
`Literature/<тема>` в хранилище. Поэтому перевода имён нет: `folders[<слаг темы>]` и всё.
Прежняя двухуровневая таксономия (`Applied`, `LLM`, `Optimization`, `PEFT`, `RL`, `Reference`)
удалена, 588 статей разложены по 25 темам. Копия карты живёт на do-vpn в
`/root/paper-agent/alphaxiv-library-map.json` — обновлять обе.

## The one place local and AlphaXiv may differ
Only the **reading queue**: the local Operon Reading board (`Operon/Reading/*.md`, visually ordered
_Trash → Жду публикацию → Инбокс → Очередь → Читаю → Прочитано) ⇄ AlphaXiv default **"Want to read"**
folder (`0196244b-7b41-79ff-9c0a-e01fe749c0c5`). Papers sit there until processed; once a paper is
filed into a topic folder locally, it must also be filed (and removed from "Want to read") on AlphaXiv.

## Hard rules
1. **Ingest / file a paper into a topic folder** (`paper-ingest`, `want-2-read`, `paper-search` acceptance, manual add): after the local note lands in `Literature/<тема>/`, call `save_papers_to_folder(folder_id=<mapped id>, [arxiv_id])`. If the paper was in "Want to read", use `move_papers_between_folders(from=want_to_read_folder_id, to=<topic folder_id>, [arxiv_id])` instead (adds to topic + removes from Want to read atomically).
2. **New reading-queue item** the user drops only on AlphaXiv "Want to read": treat it as a card in the «Очередь» column — `/want-2-read` reads BOTH sources.
3. **Move / reclassify a paper between local folders** → mirror with `move_papers_between_folders`.
4. **Delete a paper from the local library** → `remove_papers_from_folder` on the matching AlphaXiv folder.
5. **New local folder** → first propose the folder and wait for explicit user confirmation. Only
   after confirmation call `create_folder(name=<слаг темы>, parent_folder_id=<personal_folder_id>)`
   and add its id to `folders` в обеих копиях карты. Статья, для которой темы ещё нет, уезжает в
   `personal/_inbox` — ровно как в `Literature/_inbox` локально, и это не требует подтверждения.
6. **arXiv-only via MCP**: the MCP can only add arXiv papers (`save_papers_to_folder` fetches from arXiv; there is NO upload/private-paper tool). For a paper without an arXiv id (e.g. ICML-poster-only), file it locally, skip the MCP sync, and tell the user they can upload the PDF manually as a **Private Paper** on the alphaxiv.org site if they want it there.
7. Never touch AlphaXiv system folders (`My publications`, `Private Papers`). "Want to read" is managed only via the queue flow above.
8. If the AlphaXiv MCP is not connected/authenticated, do the local work, then tell the user the AlphaXiv sync was skipped and needs `/mcp` auth — do not silently drop it.
9. **Rejected queue item**: `Reading._Trash` is the local master decision. Remove that arXiv ID from AlphaXiv "Want to read" with `remove_papers_from_folder`, but do not remove it from existing thematic folders. Archived rejected cards remain part of dedup.
10. **Waiting for publication**: `Reading.Жду публикацию` has no AlphaXiv mirror until a real arXiv ID exists. Recheck official sources; never invent or substitute an ID. A card whose only public source is OpenReview, a DOI, or a venue page is still marked `[found]` and is still fully ingestable into Zotero and Obsidian — it simply never reaches AlphaXiv (rule 6), and its callout must say so.
11. **Canonical Reading card**: file tasks use `Operon/Reading/operon-<operonId>.md`, never the paper
    title as basename. A completed report remains in `Reading.Очередь` and is marked by H1
    `# [[Literature/path/note|Human title]]` plus the exact canonical link in `## Заметка`. YAML
    `taskTitle` equals the H1 content without `# ` so Operon never displays the technical basename.
12. **All Reading task representations count**: every queue scan must collect YAML file tasks and
    inline tasks with `{{status:: Reading.*}}`. Normalize inline tasks without losing owner text.
13. **Availability transition**: every `paper-search` and `want-2-read` run starts by checking
    `Reading.Жду публикацию`, and both run the identical `[found]` protocol. When a canonical public
    source appears, the card keeps `status: Reading.Жду публикацию`, gains a `[found] ` prefix on its
    H1 and `taskTitle`, gets the canonical URL in `## arXiv`, and its stale "not found anywhere"
    agent report is replaced by a success callout. **Neither skill moves the card to `Очередь`** —
    that is the owner's drag, exactly as for `Инбокс`. Ingest happens only after the owner has moved
    it. A `[found]` card is, however, **ingestable where it stands**: `want-2-read` takes it into the
    same batch as `Очередь`, builds the full Zotero + Obsidian record, strips the `[found] ` prefix,
    and — on a genuinely successful ingest — **moves the card to `Очередь`**, because the column
    means "no public version yet" and that is no longer true. That promotion is the only status
    change either skill may make, it never applies to `Инбокс`, and it must be reported in chat.
    A failed or metadata-only attempt leaves the card where it was. A title-only card is never
    ingested; nothing changes for it beyond `paperLastChecked`. Every such edit is reported in chat
    line by line.
14. **Trash is not instant**: `Reading._Trash` stays visible on the board for 14 days
    (`operon_daily_archive.py --cancelled-grace-days`), unlike `Прочитано`, which archives the next
    day. Recently rejected papers therefore remain reviewable and an accidental drag is reversible
    on the board. `archiveHold: true` pins any card indefinitely. Archived or not, a rejected
    title/arXiv ID stays part of dedup.

Full folder mapping + the 2026-07-12 full-rebuild rationale: MemPalace `literature/decisions` drawer + Obsidian `general/Knowledge/alphaxiv-mcp-sync.md`.
