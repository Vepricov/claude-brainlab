# Write your work into the base with git

The base is a git repository per work. You do not fill a form and hope: you clone it, edit
the markdown, push a branch and open a pull request. A human reads the diff and merges.

## Your credentials

The machine's key is on this machine, at `~/.config/brainlab/git-token`, with the base
address in `git-url` and the login in `git-login`. Read them and use them; do not ask, and
never use a person's token. The key is a group key at developer level: it pushes branches
and opens merge requests, and it cannot merge anywhere.

```
TOKEN=$(cat ~/.config/brainlab/git-token)
URL=$(cat ~/.config/brainlab/git-url)
git clone ${URL/https:\/\//https://oauth2:$TOKEN@}/brainlab/<направление>/<тема>/<работа>.git
```

**The base is GitLab since 01-10-2026, reachable over the network.** The old path through
`127.0.0.1:3080` and Gitea is dead; if you find it anywhere, that is leftover, not a
fallback. The certificate is self-signed, so certificate checking is turned off
deliberately — the address comes from a file on disk, not from the network.

The work lives inside the group of its theme, and the theme inside a direction:
`brainlab/preconditioning-curvature/dykaf` style paths vary, so take the full path from the
project list rather than assembling it from the slug. `list_projects` gives the work and
its theme.

## Where things live

```
README.md                          what the paper is about; generated, do not hand-edit
claims/H-DYC-007/README.md         the claim, as a person reads it
claims/H-DYC-007/series/S-DYC-022.md   a group of runs answering one question
claims/H-DYC-007/runs/E-DYC-126.md     one run: settings, how it was checked, numbers
claims/H-DYC-007/theory/D-DYC-002.md   a theorem with its proof
claims/H-DYC-007/figures/F-DYC-001.svg pictures, SVG text only
```

**Everything under `claims/` belongs to you and to the reviewer.** The service creates a
file once and never rewrites it, so your edit survives. Outside `claims/` the tree is
generated: the work README and the index are rebuilt, and editing them is pointless.

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
git push -o merge_request.create origin claim/H-DYC-007
```

4. **The pull request opens from that push.** Its title is the first line of the commit
   message and its body is the rest — measured 03-10-2026, no API call needed. Pushing again
   into the same branch adds to the open request; `-o merge_request.create` on a branch that
   already has one is simply ignored. `Closes #12` in the commit message closes that task on
   merge.

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
  `~/.claude/skills/lab-knowledge/references/canon.md`; this is how it is done.
- **No water.** Tables for numbers, one bold sentence per finding, prose only where it
  explains. A paragraph that says nothing is worse than no paragraph.
- **Every number next to the code of the run it came from**, and every run file says where
  it came from: our log with its address, our run with a thin protocol, or a number taken
  from the paper. Never dress up a foreign number as our measurement.
- **Russian prose.** Metric names, flags, method and library names stay English.
- **Formulas**: `$…$` inline, and a display formula in a ```math fence — GitLab reads `$$…$$`
  only on one line.

## What not to do

- Do not edit `main` — it is protected and you cannot push there anyway.
- Do not invent a public code for a new record. Leave the code out of the filename and say
  in the pull request that it needs one; codes are handed out by the service.
- Do not cite public codes as stable addresses in messages: they are renumbered when a work
  is tidied. **The stable address is the path of the file in the repository** — quote that.
  A record that has not been merged yet has no UUID at all, so there is nothing else to quote.
