# External papers and their claims

Apply [the shared record contract](record-contract.md), especially its distinction between
a paraphrased `statement` and a literal source `quote`.

The library corpus is independent of project membership. Read the existing page before
writing: `<theme>/literature/<citation-key>.md` in the clone, found with `grep` over the
theme's `literature/`. A paper may link to several laboratory projects without becoming
several independent papers.

For the owner's library, follow the current Obsidian and Zotero taxonomy and the configured
library sync. Other members contribute by proposal into the theme's `literature/` without
owning that vault. Do not require a private filesystem note from every contributor.

An upsert's behavior depends on the current schema. Read the stored paper first and preserve
metadata and sections that the update does not intend to replace. Use additive section writes
for additional verified source passages when supported. Do not invent titles, strip tags, or
replace a full reading note with a short metadata card.

Record claims that are useful to cite or assess, with their assumptions and source location.
Split independently supported assertions. Choose their number and kind from the paper.
Statements may be paraphrased or translated. Quotations are optional; a source reference and
locator keep the assertion traceable without copying prose. Do not pad claims to a character
minimum. If the current server refuses a claim without a quote, preserve the prepared payload
as pending and report the mismatch. Do not fabricate a quote or silently mark the paper fully
published. A reading note and a verified original passage are different source types.

Use `link_paper` with the appropriate relation and, when relevant, a specific paper claim.
A whole-paper relation may be enough for a baseline. Do not manufacture a connection because
another project shares a keyword. Preserve returned identifiers and verify the resulting link.

## Куда положить статью — решение, а не формальность

Владелец 26-09-2026, открыв тему с 86 статьями: «мне не нравится, что у меня есть папки, в
которых очень много статей. Это обычно означает, что она стала мусорной… в
optimization-basics почему-то есть про LMO методы. Такого мусора быть не должно».

Тема — это вопрос, на который статьи отвечают, а не корзина по смежности. Выбор темы при
записи статьи важнее, чем кажется: по теме ищут, по теме читают, и тема, в которую клали
всё подряд, перестаёт отвечать на что-либо.

**Границы, при которых тема остаётся темой:**

| условие | почему |
|---|---|
| Тема отвечает на ОДИН вопрос | если ответ приходится давать через «и» — это мешок, его придётся делить |
| Размер задаёт предмет, а не счётчик | сорок статей про ZO это тема; сто «про оптимизацию вообще» — мешок при любом счёте |
| Тема названа предметом, а не свойством | «адаптивные методы и их сходимость», а не «теория», «важное», «новое», «прочее» |
| Статья попадает ровно в одну тему | статья в трёх темах — признак того, что тема выбрана по ключевому слову |

**Перед записью статьи:** посмотри существующие темы (`list_themes`) и выбери ту, чей
вопрос статья действительно отвечает. Подходящей нет — предложи новую владельцу и скажи,
чем она отличается от соседних. Не клади «пока сюда, потом разберём»: разбирать это потом
придётся целым проходом, и `scripts/claims/shelf.sh` именно для этого и написан.

**Если тема, куда ты кладёшь, уже у границы** — скажи об этом вслух в ответе. Лучше
остановиться на двадцать шестой статье, чем на восемьдесят шестой.
