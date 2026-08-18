# A setup that works

This is the configuration the repository is developed against, described so it can be copied rather
than guessed at. Host names, tokens and member names are deliberately absent: they belong to the lab's
private configuration.

## The machine

macOS with Claude Code as the interactive agent, Homebrew tools (note that `gh` and friends live in
`/opt/homebrew/bin`, which is not always on `PATH`). Obsidian holds the personal research vault, Zotero
holds PDFs and BibTeX, and the reading queue is a kanban of Markdown cards inside the vault.

Install this repository with `install/setup.sh`; it renders `settings.json.template` from your `.env`
and skips the Lab Knowledge server entirely when `LAB_MCP_URL` and `LAB_MCP_TOKEN` are absent, so the
toolkit is usable without lab access.

## The knowledge service

The service is a FastMCP application over streamable HTTP with a bearer token in front of Postgres. It
runs on a lab host as a user service, and a local port is forwarded over SSH, so `LAB_MCP_URL` points at
`127.0.0.1`. Semantic search is enabled on the host with embeddings on CPU; the reranker stays off.

Two operational habits matter more than they look:

- After a full library sync, run the warm-up rather than letting the first search compute thousands of
  vectors at once. A run that replaces sections drops their vectors, and an unwarmed corpus made the
  service take 1200% CPU and stop answering.
- Keep scratch space on `$HOME` on shared servers, not in `/tmp`: the root filesystem is small and
  shared with everyone.

## What runs unattended

- A stop hook interrupts the end of a turn every ten exchanges and asks the agent to save the session
  into three places: the memory MCP, Obsidian, and the shared base. The earlier design had the hook
  parse the session for markup and write the records itself, which cost nothing per turn and fired
  almost never: the markup was documented in the hook and nowhere else. Interrupting and demanding
  costs a turn and works.
- A pre-tool hook blocks any `\cite{}` key that is missing from `references.bib`.
- Long jobs live in `tmux` on GPU servers; the loop that watches them appends timestamped progress to
  an experiment note and refreshes a plot, so a dead run is visible without watching it.
- Paper batches run in a queue with a circuit breaker: after three consecutive startup failures it
  stops instead of burning through the list, and it treats "the record exists" as done only when the
  record actually has content.

## The literature loop

`paper-search` proposes papers the library does not already have. `want-2-read` walks the reading
queue, runs `paper-ingest` per paper, and — this step is mandatory — pushes the result into the shared
corpus. `paper-ingest` writes the Zotero item, the vault note with an eight-section analysis, the
AlphaXiv mirror, and audits its own BibTeX at the end.

The library is mirrored to an AlphaXiv account, so filing a paper locally and filing it there stay in
step. The same paper in two folders is one canonical note plus a hard link, never two copies.

## Rules learned the hard way

- A paper needs a natural key (arXiv, DOI or Zotero) or the next sync files a duplicate beside it.
- An empty field must never overwrite a stored one: the moment more than one person writes, a short
  card would otherwise erase somebody's analysis.
- Anything that must be verifiable later — citation keys, subject tags, record codes — is computed, not
  generated.
- Reports must name what they skipped. "Sent 476, 0 failures" while eleven papers never entered the
  manifest is the same class of bug as a silent exception.
- Tests that describe a design which no longer exists are deleted, not skipped: a red suite nobody
  trusts is worse than a smaller green one.
