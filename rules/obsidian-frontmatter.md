# Obsidian frontmatter (applies to ALL agents, ALL sessions)

## HARD RULE: reserved property keys are ALWAYS English

Obsidian recognises a fixed set of built-in property names. It matches them **literally and only in English**. A translated key is silently treated as an ordinary custom property, so the feature it was supposed to drive just does not work — no tag indexing, no alias resolution, nothing in the tag pane or in search by `tag:`.

Never write `теги:`. Always write `tags:`.

The reserved keys, all lowercase, all English:

- `tags` — the tag list. This is the one that actually breaks things when translated.
- `aliases` — alternative note names for linking and search.
- `cssclasses` — CSS classes applied to the note.
- `publish`, `permalink`, `description`, `image` — Obsidian Publish.

Tag **values** are also written in English kebab-case (`matrix-optimization`, not `Матричная оптимизация`), because a tag is an identifier that gets typed into search and reused across notes.

```yaml
---
tags: [wsd-muon, muon, forgetting, iclr2027]
---
```

## Custom keys

Anything outside that reserved set is a free-form property, and the vault's own naming wins. This vault has long used Russian custom keys (`тип`, `тема`, `обновлено`), and `general/Knowledge/obsidian-conventions.md` documents them, so keep them as they are unless the owner says otherwise. Russian is fine there precisely because nothing built-in depends on those names.

## How to apply

Before writing any `.md` into the vault, check the frontmatter block: every reserved key in English, tag values in English kebab-case, custom keys matching the surrounding notes. When editing an existing note that has `теги:`, rename it to `tags:` in passing — that is a fix, not scope creep.
