# Put work into the laboratory's git base

Apply [the shared record contract](record-contract.md).

## You are writing into a repository, through a pull request

The shared knowledge of the laboratory is a git repository per work, inside the group of its
theme, inside the group of its direction. The same path is where its clone lies in the tree:

```
brainlab/matrix-optimization/preconditioning-curvature/dykaf      in GitLab
~/brainlab/matrix-optimization/preconditioning-curvature/dykaf    on the machine
  README.md                       what the paper is about, who leads it (Ведут, Команда)
  claims/H-DYC-007/README.md      the claim itself, as a person reads it
  claims/H-DYC-007/series/S-DYC-022.md   a group of runs answering one question
  claims/H-DYC-007/runs/E-DYC-126.md     one run: commit, config, command, logs, numbers
  claims/H-DYC-007/theory/D-DYC-002.md   a theorem with its proof
  claims/H-DYC-007/figures/F-DYC-004.svg a figure, shown inline where it explains a result
```

The work's own jargon is defined in place, in the page that first uses it. A term of the
theme goes to the theme's glossary, `<theme>/literature/glossary/`, not to a file in the work.

**An agent never writes into `main`.** Every write is a branch `claim/<CODE>` in the tree
clone (`lab here <work>` places it), a commit, and a plain `git push`: the clone is
configured so that the push opens — or extends — one merge request per claim and assigns it
to the lead from the README's `Ведут` line. A human merges it, and merging is what lands the
change. A push to `main` is refused for everyone.

**A green verdict is not a record: the merge is.** Push to `main` is closed for everyone,
so nothing enters except through a proposal. A human merges, or an agent on that human's word
said in the same session, and the agent writes that word into the proposal before merging.

## Work out where you are, by reading, before you write anything

1. **Which claim** does this test? Read `<work>/claims/` in the clone: that listing is the
   list of claims, and each `README.md` opens with the claim's own sentence. A work
   carries a handful of them — dykaf has seven. New runs at a new scale are almost never a
   new claim: they are corpus under one that already exists.
2. **Which series** inside it? A claim's runs are grouped into series, one per question the
   runs answer together, and the claim page names them with what each was checking.
   The series is a file, `claims/<CODE>/series/<S-code>.md`, and it lists its runs.
3. **Is there an open pull request** for that claim? There is one per claim and it lives as
   long as the claim is being checked. Proposing into the same claim again adds a commit to
   it rather than opening a second one.

## Codes come from the clone; the address is the file path

**Take a free code by reading the clone, not the base.** The old rule said the opposite, and
it was right while the base was Postgres and the files lagged. It is cancelled: the files are
the base. Verified 01-10-2026 by comparing both — they agreed code for code.

```bash
find . -name '*-WSD-*' | grep -o '[HDSEF]-WSD-[0-9]*' | sort -u
```

Substitute the work's own letters, then take the **largest** number per prefix. Take the
maximum, not the count: the holes are real (runs skip 017-020 and 028-032 in `wsd-muon`), so
counting rows gives the wrong answer. This also finds figure codes, which `*.md` misses.

A code remains a label for reading, not an address: `H-DYC-035` became `H-DYC-007` within a
quarter of an hour on 23-09-2026 when a work was renumbered. **The address of a record is the
path of its file in the repository** — that is what survives a renumbering. A code written
into the text of a page still needs fixing afterwards.

## What goes into one submission

The unit is a CLAIM WITH ITS SUPPORT, not one record. One submission carries the idea, what
confirms it, and every write that follows, so the reviewer judges a case and not a row.

- a run finished — add `claims/<CODE>/runs/<E-code>.md` with its real status;
- numbers came out — a table in that same run file, each number beside the code it came from;
- a proof was worked out — `claims/<CODE>/theory/<D-code>.md` with assumptions, statement,
  argument and a «Чего не хватает» section;
- an internal name appeared — define it in place, in the page that first uses it, and if it
  is a term of the theme, add it to `<theme>/literature/glossary/`. A work itself has no
  `terms/` directory; do not create one;
- a decision was made — it is not a record of its own. What was decided about the method
  is a paragraph in the claim's README; a rule of one series' protocol goes into that series.

Ask before writing only when the record belongs to somebody else's project, publishes what
the user called private, or changes a conclusion another person reached. Then show the
project, the object, the owner and the source.

## Vocabulary

Define project-specific run names, implementations, protocols, metrics and artifacts when
another researcher could not read the page without them, and define them **in place**, in the
page itself. A reference must open for whoever reads the base — the run in the tracker, the
log on the server, the path of the page. A path into a personal note store is refused.

## After the merge

Read back what landed, in the clone: `git pull` on `main` and open the files. A page is not
rendered from records any more — it is the file you wrote, so what is in the file is what is
in the knowledge, and a number left out of it is left out. An evidence link or a finished
task does not by itself conclude a claim; an unfinished check is not an `inconclusive`
result.
