---
name: lab-knowledge
description: "Searches the laboratory's git knowledge base and writes into it through a pull request on a claim. Use when the user asks what the lab knows about something, or when work produces something the lab should keep — a finished run, a series of runs with a verdict, a derivation, a new claim, or a correction to one. Also use before writing anything into a work repository, the handbook or the journal, because it carries the canon of rules that the proposal gates enforce."
---

# Lab Knowledge

Read the base from the local clone of the work (`grep`, `git log`, `git show`); there is no reading server any more, it was removed on 05-10-2026 because nobody used it. Personal Obsidian notes, agent history
and the laboratory's shared records have different owners and purposes.

## Find what the laboratory knows

**Search the clone, with `grep` and `git log`.** There is no search service: the one that
existed lived on Postgres embeddings and was deleted on 07-10-2026 together with its base.
A work is a git repository, so `grep -rn "<term>" <work>/claims/` and `git log -S"<number>"`
answer faster than any index, and they never return a stale snapshot. Papers of the library
are files too: `<theme>/literature/` holds one page per paper, named by its citation key.

For the laboratory's own knowledge, **read the clone**: `grep` and `git log` over
`<work>/claims/`, which is checked out locally. That is faster than any search call and it is
the same bytes the reviewer sees. There is no typed index and no read API: the directory
listing of `claims/` is the index, and the first line of each `README.md` is the claim.

A closed task is not a confirmed claim. Verify changeable facts against their current source
before reporting them as current. A read-only question must not cause writes.

Return the supporting public codes, shared links, and any uncertainty. Do not publish local
paths, private transcripts, or credentials as provenance.

## Start with the manuscript and the code, not with the claims

A work that has a paper and a training repository brings them **into the work itself**, as
submodules, before a single claim is written:

```bash
git submodule add https://git.overleaf.com/<id> paper/<work>
git submodule add <git url of the training code> code/<name>
git commit -F -        # say what was connected and where it came from
```

The repository then stores a pointer, `lab pull` brings the text, and both are named in the
README in backticks. They are not gitignored and not pasted as a link in prose: a reader, a
gate and an agent all need to open them, not to be told they exist.

**Why this comes first.** Claims, runs and series are then derived from material that is in
hand. Every number copied out of the paper carries the address it came from — the table or
figure label, not the word «рукопись» — and that address can be opened and checked on the
spot. Measured 13-10-2026 on `spectral-wd`: with the manuscript pulled, four of its numbers
turned out not to be in the paper's tables at all, one was attributed to a 124M model where
the paper's caption says 257M, and the claim «the manuscript has no experiments» proved
false — it had been written from an older version someone had sent. None of that is visible
while `paper/` is an empty folder.

**Before writing anything, check they are actually there**, because an unpulled submodule
looks exactly like an absent one:

```bash
git submodule update --init --recursive
find paper -name '*.tex' | head        # empty output means not pulled, not «no manuscript»
```

If the work has no paper or no code yet, say so in the README in one line and name who has
them. That is a debt with an owner, not a silence.

## What you are writing into: a git repository

The shared knowledge of the laboratory is a git repository, one per work, and nothing else.
Every claim is a folder, every run is a file inside it:

```
<work>/claims/H-DYC-035/README.md          the claim itself, as a person reads it
<work>/claims/H-DYC-035/series/S-DYC-021.md a group of runs answering one question
<work>/claims/H-DYC-035/runs/E-DYC-072.md   one run: commit, config, command, logs, numbers
<work>/claims/H-DYC-035/theory/D-DYC-002.md a theorem with its proof
<work>/claims/H-DYC-035/figures/            pictures, as SVG text
```

You do not write into any other place. The calls below are how you put files into that
repository; they are not a second store standing beside it.

**Work out where you are before writing anything.** Three questions, answered by reading:

0. **Which work?** The session-start hook has already worked it out and printed it: the
   work's slug, the path to its clone, its claims, what is open and what is assigned to you.
   It reads a `.lab-work` file in the project folder, here or higher up the tree. Nothing is
   typed into a message to declare this: the `ЛАБ-РАБОТА:` line is gone, together with the
   markup hook that used to parse it (disabled, then removed 03-10-2026). Working somewhere
   else? Put a `.lab-work` file there, or say the slug in plain words.
   `dykaf`, `rl-muon`, `warmup` are works and have repositories.
   `lab-general` or `preconditioning-curvature` are shelves above them: no repository, no
   pull request, and a record sent there reaches no file and no review — eleven thousand
   records sit in one such shelf unseen. A submission into a shelf is refused. If you cannot
   name the work, say so and stop; do not park it somewhere general.
1. **Which claim** does this work test? A work carries a handful of them; yours is one.
   New runs at a new scale are almost never a new claim — they are corpus under one that
   already exists. Read `<work>/claims/` in the clone: the directory listing IS the list of
   claims, and each `README.md` starts with the claim's own sentence.
2. **Which series** inside it? A claim's runs are grouped into series, one per question the
   runs answer together. The claim page names them with what each was checking.
3. **Is there an open pull request** for that claim already? There is one per claim, on the
   branch `claim/<CODE>`, and it lives as long as the claim is being checked. Proposing
   into the same claim again adds a commit to that same request rather than opening a
   second one — so a long check accumulates where its reviewer reads it.

**You write by editing files, not by filling a form.** Clone the work's repository, check
out the branch `claim/<CODE>`, edit the markdown, push, open or extend the pull request. A
person reads the diff and merges. Everything under `claims/` belongs to you and the reviewer:
the service creates a file once and never rewrites it. The mechanics, with commands, are in
[writing in git](references/writing-in-git.md); how each kind of page is written and read is
[claim-page.md](references/claim-page.md).

Inside your branch you are free: add a run file, rewrite a paragraph, drop in a figure, fix a
number, start a series. What is asked is style, not caution — no water, numbers in tables,
every number next to the code of the run it came from, and the provenance of every run said
out loud.

**There is no service to write through: the base is git and nothing else.** The MCP service
and its Postgres were deleted on 07-10-2026. Every write is a file in a clone, a branch, a
commit and a merge request.

**Who merges, and on whose word.** Push to `main` is closed for everyone, so a record enters
only by merge. A human merges — or an agent by that human's word, said in the same session.
An agent that merges writes into the proposal, before merging, whose word it acts on and
when, quoting the person. Permission covers what was agreed and nothing else: "merge these
two" is not "merge whatever you like from now on". An agent never merges another person's
work, a proposal with a red verdict, one with open remarks, or its own proposal that the
person does not know about. (Owner, 16-10-2026.)

**Take a free code from the clone, not from the base.** The old rule said the opposite —
check codes against the database, never the files — and it was right while the base was
Postgres and the files lagged behind it. **That rule is now cancelled:** the files are the
base. Checked 01-10-2026 by comparing the two: they agreed code for code.

Take the **maximum**, not the count: the holes in the numbering are real, so counting rows
gives the wrong answer.

```bash
find . -name '*-WSD-*' | grep -o '[HDSEF]-WSD-[0-9]*' | sort -u
```

(substitute the work's own letters for `WSD`), then take the largest number per prefix. This
also finds figure codes, which a search for `*.md` misses.

**A public code is still a label, not an address.** `H-DYC-035` became `H-DYC-007` within a
quarter of an hour when a work was renumbered. The address of a record is **the path of its
file in the repository** — that is what does not move. A code written inside the text of a
page needs fixing after a renumbering; a path does not.

## When to write, without being asked

Recording is part of doing the work, not a ceremony after it. These moments are the trigger;
each becomes a file in the claim's pull request.

| what just happened | the file you add | do not wait for |
|---|---|---|
| a run finished, succeeded or failed | `claims/<CODE>/runs/<E-code>.md` with its real status | a second edit to move the status: give the state it is in |
| numbers came out of a run | the same run file: a table, each number next to the run code it came from | the claim to be concluded first |
| a claim got stated that someone could test | `claims/<H-code>/README.md` with its falsification criterion | certainty; a draft assertion is a legitimate state |
| a proof or a bound was worked out | `claims/<CODE>/theory/<D-code>.md` | the gaps to close: name them in «Чего не хватает» instead |
| a group of runs answers one question | `claims/<CODE>/series/<S-code>.md`, and list the runs in its «Запуски» table | all the runs to finish |
| a choice was made and will be lived with | a paragraph in the claim README, or in the series if it is about one group of runs | consensus; a decision written down is a decision |
| a figure | `claims/<CODE>/figures/<F-code>.svg`, referenced from the page that uses it | the figure to be final |

**A derivation is read by whoever did not write it, so it has to read from zero.** Four canon
rules govern that, and none of them is caught by a gate: `theorem-reads-from-zero` (no letter
used before it is introduced, no letter standing for two different objects, the assumptions one
by one and each with a line saying why it is needed and what changes if it fails, the set a
maximum is taken over named explicitly, and a paragraph right after the proof translating the
answer into a quantity the reader cares about rather than leaving it as a ratio of symbols),
`theorem-has-no-run-numbers` (the statement is dimensionless and measured numbers enter it by
substitution, so a threshold on a hyperparameter becomes a condition on a dimensionless
combination), `derivation-names-where-it-works` (a derivation whose place of use cannot be named
leaves the corpus, and what stays gets a paragraph on what it means and what it is for), and
`one-file-per-storyline` (the theory folder is split by storyline, not by lemma). The check is
one and it is done before pushing: read the section without remembering the rest of the file,
and if a letter appears that was not introduced above it, the section is not ready.

Then push, and the pull request opens from the push itself:

```bash
git commit -F -                      # first line is the title, the rest is the body
git push -o merge_request.create \
         -o merge_request.assign=veprikov   # and lands on whoever merges it
lab checks                           # what the checks said
```

**A proposal is not done while a remark is unresolved.** Two sources, and a green verdict is
silent about the second: the service says what is mechanically broken, a person in the
discussion says what to rewrite. `lab checks` prints both, with unresolved threads listed
separately and with their file and line. Fix in the same branch and push to the same branch —
the proposal updates itself, do not open a second one. The session hook prints how many
remarks are waiting, so acting on them does not depend on remembering to look.

**Assign it to whoever will merge it.** GitLab assigns a merge request to its author, and the
author is the agent's account; the person then sees zero in «Merge requests → Assigned» and
never finds your proposal. The hourly pass fixes a forgotten one, but set it yourself.

**The body of the proposal is taken from the commit message** — measured 03-10-2026: title
from the first line, body from the rest, `Closes #12` works from there too. There is no `lab
pr` any more and no wrapper for this: it is plain git with one option.

One pull request per claim, on branch `claim/<CODE>`; a new edit adds a commit to it rather
than opening a second.

**Before every push**: `git fetch`, merge `main` into your branch, and read
`git diff --stat main..HEAD` with your own eyes. A branch cut from a stale `main` shows other
people's files as deletions in the pull request, and the base check does not catch it — it
measures deletions against the `main` of the moment it ran. Merge, do not rebase: a rebase
breaks the push and invites `--force-with-lease`, which has already wiped a branch once here.

### Define the name before you use it, but know where that definition can go

Before writing a page that contains an internal name, define that name. An internal name is
anything a reader outside the project cannot resolve: a run name (`exact-old124`), a method
name (`KronZO`), a metric (`pooled M2`), an in-house abbreviation. A month later the page is
read by someone who was not on the call, and «DyKAF обгоняет SOAP на 210M» without a
definition of DyKAF is a line nobody can act on.

**But the repository has no place for a definition.** The tree is only
`<work>/claims/<CODE>/{runs,series,theory,figures}` and `literature/`. There is no `terms/`,
no `resources/`, no journal in a work. A term goes to the theme's glossary (`literature/glossary/`,
and the same pages are published as that project's wiki); the way of working goes to
`brainlab/journal`; an instruction others need goes to `brainlab/handbook`.

So do this instead, and do not invent a folder for it:

| what | where it actually goes |
|---|---|
| jargon of this work | defined in place, in the page that first uses it — one sentence, not a glossary file |
| a machine, a dataset, a volume | the owner's own notes; a resource card has no file in the repository |
| something operational that was learned | the owner's own notes, and said out loud in the answer |
| a paper | `literature/<citation_key>.md`, which the ingest pipeline writes |

Do not open a `terms/` directory in a theme repository to hold these. Two descriptions of one
machine diverge: on nodes `ali117196` and `ali117197` they already did, and the divergence cost
five failed runs.

## Choose the needed writing guidance

- **The rules themselves live in one place, and this skill does not restate them:**
  `brainlab/handbook/canon.md` in GitLab. Named rules, each with the line that says what
  enforces it. Everything in this skill is how to do the work; the canon is what the work
  must satisfy, and a disagreement between the two is settled by the canon. It is edited in
  the handbook by a proposal, never in a copy: a second copy of the canon is a check failure
  (`canon_check.py`).
- **Before writing a claim, a series or a run page**, read
  [how a claim page is written and read](references/claim-page.md). It carries the chain the
  laboratory runs on: what the code writes and what you write, how a group of runs becomes a
  series with one question and a verdict, when a figure belongs in the conclusion, how the
  series changes the claim's state, and what the body of the proposal must say.
- **Before stating something as a claim**, read
  [what a claim is](references/what-is-a-claim.md) — the difference between a claim and a
  note, and why a claim without a falsification criterion is not one.
- **When the criterion has to be written down**, read
  [acceptance as conditions](references/acceptance.md).
- Before publishing scientific records or literature, read
  [record types, destinations, and approval](references/record-contract.md).
- To create or update a project's scientific chain, read
  [publication workflow](references/publishing.md).
- To ingest, quote, or connect an external paper, read
  [library workflow](references/library.md).

Load only the guidance needed for the operation. Use the live tool schema for required
fields, supported types, relations, and lifecycle values; a remembered signature is not a
contract. An unavailable integration limits that destination, not unrelated read-only work.

For meeting extraction, `call-notes` supplies the meeting-specific workflow. Brain Call has
its own pipeline; it does not require running `call-notes` afterwards.

## Tasks live in GitLab

Tasks of a work are its own issues; tasks that are not about science live in the group
`ops`. `lab tasks` lists them, `lab take <number>` takes one, and `Closes #<number>` in a
commit message closes it on merge. A task names the claim it affects in its body; open
questions are not filed as tasks at all — they live on the page of their claim.

## The judge reads the work before the person does

Two gates run on every proposal — the base check (mechanics) and the prose judge — and
neither of them reads the work as a whole. For that there is a judge: an agent that reads
the fourteen rules the owner judges by and the work laid out the way a person sees it. Those
fourteen rules are the single list — `scripts/claims/sudya-task.md` in `brainlab/tools` — and
they are not restated anywhere else: a second copy of a rule list diverges from the first
within a week, and then nobody knows which one is being judged by.

```bash
python3 scripts/claims/sudya.py <clone> <where to put it>   # lays the work out
# then an agent reads scripts/claims/sudya-task.md and that folder, and returns
# JSON: rabota, verdikt, zamechaniya[{pravilo, gde, chto, kak_pochinit, kem}], chto_horosho
```

The loop is judge → the work's own agent fixes by reading and rewriting → judge again, until
the verdict is clean. Measured 13-10-2026: two to three rounds per work, and the second round
finds smaller things than the first. The judge is worth running even when the gates are green,
because it catches what mechanics cannot: a claim that restates a definition, a page that
cannot be read on its own, a state that disagrees with its own text, a number presented as
the manuscript's when it is our own recount.

**A pass over the tree only counts and shows; the text is edited by whoever read it.** A
regular expression finds a class of defect well and ruins pages reliably: it cannot see that
the machine is named three words later, that backticks hold a command, or that a filename
contains a space. On 13-10-2026 one such pass broke twelve places out of a hundred and twenty
edited lines, every one of them in text that had been correct.

## The canon of rules

`brainlab/handbook/canon.md` in GitLab — the named rules of the base, each with the line that
says what enforces it. That file is the one place the rules live, and nothing here restates
them. `canon_sync.py` puts a readable copy on the machine next to this skill. Read the canon
before writing into a work, the handbook or the journal.
