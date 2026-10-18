# Write your work into the base with git

The base is a git repository per work. You do not fill a form and hope: you take its clone in
the tree, edit the markdown, push a branch, and the push opens a pull request. A human reads
the diff and merges.

## Your clone and your credentials

The work's clone lies in the tree, at the same path as in GitLab without the `brainlab/`
root. One command places it, or updates it if it is already there:

```bash
lab here <работа>      # → ~/brainlab/<направление>/<тема>/<работа>
```

Do not `git clone` by hand and never put the key into a URL: a key in `remote.origin.url`
lies in the open in `.git/config` and leaks into every log that prints the remote. `lab here`
hands the key to git through a credential helper (`~/.config/brainlab/git-credentials`),
finds the full path of the work by its slug, closes the local-only folders in
`.git/info/exclude` and sets the push options. The key itself is on this machine, at
`~/.config/brainlab/git-token`, with the base address in `git-url`; do not ask for it, and
never use a person's token. A second clone «somewhere for myself» is not made: `lab here
<работа> --рядом` (a clone in `<project folder>/lab-base`) is only for a machine without the
tree.

**The base is GitLab since 01-10-2026, reachable over the network.** The old path through
`127.0.0.1:3080` and Gitea is dead; if you find it anywhere, that is leftover, not a
fallback.

## Where things live

```
README.md                          what the paper is about, Ведут and Команда lines
claims/H-DYC-007/README.md         the claim, as a person reads it
claims/H-DYC-007/series/S-DYC-022.md   a group of runs answering one question
claims/H-DYC-007/runs/E-DYC-126.md     one run: settings, how it was checked, numbers
claims/H-DYC-007/theory/D-DYC-002.md   a theorem with its proof
claims/H-DYC-007/figures/F-DYC-001.svg pictures, SVG text only
```

**Everything under `claims/` belongs to you and to the reviewer**, and nothing rewrites it
behind you. The work README is written by people too and changes by proposal like anything
else; keep its `**Ведут**` and `**Команда**` lines intact — the push options take the
assignee of every proposal from `Ведут`. Next to these, the clone has folders that never
leave the machine: `notes/`, `daily/`, `runs/`, `paper/drafts/`, `code/local/`, `calls/raw/`.

## The loop

1. **Find the claim your work develops.** A work carries a handful of them. New runs at a
   new scale are almost never a new claim: they are corpus under one that exists. Read
   `claims/*/README.md` — that is the whole list.
2. **Find the series.** The claim page names its series with what each was checking. Your
   run belongs in one of them; its file goes in `runs/`, and the series file lists it.
3. **Branch `claim/<CODE>`.** One branch and one pull request per claim, living as long as
   the claim is being checked. If the branch is already there, add to it — do not open a
   second one.

```bash
git fetch origin && git checkout claim/H-DYC-007 || git checkout -b claim/H-DYC-007
# правь файлы, клади рисунки, дописывай таблицы
git merge --no-edit main && git diff --stat main..HEAD    # посмотреть ГЛАЗАМИ
git add -A && git commit -F -      # заголовок и тело предложения прямо здесь
git push                           # клон настроен: push сам открывает предложение
```

4. **The pull request opens from that push**, assigned to the lead named in the README's
   `Ведут` line. Its title is the first line of the commit message and its body is the rest —
   measured 03-10-2026, no API call needed. Pushing again into the same branch adds to the
   open request; the create option on a branch that already has one is simply ignored.
   `Closes #12` in the commit message closes that task on merge.

   The body must carry three things, and none of them can be skipped: **what changed and
   why**, **what disappeared and why**, **how it was checked**. The third exists because once,
   under a green verdict, seven measured numbers left the base silently. How to write them for
   a series or a claim: [claim-page.md](claim-page.md).

## You have full freedom inside the branch

Add a run file, rewrite a paragraph of the claim, drop in a figure, fix a number, start a
new series. A person reads the diff before anything lands. What is asked of you is not
caution but **style**: the page must read the way the others read.

- **The standard is [claim-page.md](claim-page.md), next to this file.** Read it before
  writing a page: section order, what belongs in each, how a title is built, how results and
  the conclusion differ. What the page must satisfy is the canon,
  `brainlab/handbook/canon.md`; this is how it is done.
- **No water.** Tables for numbers, one bold sentence per finding, prose only where it
  explains. A paragraph that says nothing is worse than no paragraph.
- **Every number next to the code of the run it came from**, and every run file says where
  it came from: our log with its address, our run with a thin protocol, or a number taken
  from the paper. Never dress up a foreign number as our measurement.
- **Russian prose.** Metric names, flags, method and library names stay English.
- **Formulas**: `$…$ inline, $$…$$` for a display formula, on as many lines as it
  needs. Checked on GitLab 17.11 and in Obsidian: both render this. A ```math fence
  renders in GitLab only, and in Obsidian it shows up as a code block — do not use it.

## What not to do

- Do not edit `main` — it is protected and you cannot push there anyway.
- Do not guess a public code for a new record. Take the next free one from the clone: the
  largest number per prefix, not the count (see [publishing](publishing.md)).
- Do not cite public codes as stable addresses in messages: they are renumbered when a work
  is tidied. **The stable address is the path of the file in the repository** — quote that.
