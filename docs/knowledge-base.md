# Feeding the shared knowledge base

The lab runs a shared knowledge service (Lab Knowledge MCP, 52 tools) that holds two corpora side by
side: the lab's own records — hypotheses, experiments, evidence, derivations, decisions — and the
library of read papers with the claims those papers make. Search answers over both.

A record exists so that someone who was not there can cite it, which is also the one bar that keeps
the base useful: reads are lab-wide, so a record written in a project's private vocabulary is private
memory in a shared place. Each project therefore keeps a registry of its internal names — build
nicknames, run ids, local protocol names — and defining a name is retroactive: every earlier record
that used it becomes readable without being rewritten. The write path names what is still undefined
instead of refusing, because a record carrying a measurement must not be lost because its vocabulary
was late.

The service is the master. A personal Obsidian vault and a Zotero library are one way to feed it, not
a requirement. Most members have neither, and a paper contributed with nothing but an arXiv id is a
first-class paper.

## Four ways in, pick the one that matches your setup

### 1. You have an arXiv id and nothing else

```
upsert_paper(title="…", arxiv_id="2606.19348", themes=["muon-sign-methods"])
```

That is the whole contribution. Sections are optional, a reading note is not needed, and any member
may write. Add `abstract`, `summary_ru`, `url`, `code_url` if you have them; add `sections` (a list of
`{section, ordinal, content}`) if you wrote a real analysis.

Themes come from `list_themes`. Pass them explicitly here: without a library folder there is nothing
to derive a theme from, and a paper without a theme is missing from every theme view. An unknown
theme slug is refused with a message telling you how to create one — nothing is invented silently.

### 2. You keep reading notes in Obsidian and papers in Zotero

Run `/paper-ingest` for a new paper (it writes the note, the Zotero item and the library mirror), then
push the library:

```bash
python3 scripts/library_sync/parse_library.py --vault "$OBSIDIAN_VAULT" --zotero ~/Zotero/zotero.sqlite --out library.json
python3 scripts/library_sync/push_library.py --manifest library.json
```

Parsing and pushing are separate on purpose: notes and Zotero live on your machine, the database does
not. The parse step reports by name what it skipped and what arrived without any sections, so a run
that loses papers cannot look like a clean one.

Themes are derived from the library folder. One paper hard-linked into several folders belongs to all
their themes.

### 3. You want to record what the lab learned, not what it read

| Tool | Records |
|---|---|
| `create_hypothesis`, `update_hypothesis` | a claim, its falsifier, its status |
| `record_experiment`, `update_experiment_status` | a planned or finished run |
| `record_evidence` | what a run showed, tied to its source |
| `record_derivation`, `update_derivation_status` | a proof of a claim: assumptions, argument, result, completeness |
| `propose_decision`, `update_decision` | a decision and the evidence it rests on |
| `record_paper_claim`, `link_paper` | what an outside paper claims, and how one of our records stands to it |
| `publish_source_note` | the artifact a claim points at |
| `set_record_papers` | which papers a record is about, and its theme |

A claim is closed by our own evidence or our own derivation, and by nothing else. A theoretical
result has no protocol, no seeds and no hardware, so recording it as an experiment used to make a
purely theoretical project read as an experimental one; `record_derivation` is that shape, and a hole
in a proof is named through `status='gap'` rather than left silent.

A hypothesis also says what would close it: `kind='empirical'` waits for a run, `kind='theoretical'`
waits for a proof. Of 670 hypotheses in the base, 141 are theorems, and `list_hypotheses(kind=…)`
separates the two, so a theory project is no longer read as a stalled experimental one. The
falsifier has to be reachable: "worse in every setting" never arrives and therefore closes nothing.

An outside paper carries claims of its own, each on a sentence quoted from the text stored for that
paper. The quote is checked against that text and a quote absent from it is refused, so
"this paper contradicts us" points at a sentence a reader can check instead of at twenty pages. Such
a claim never concludes a claim of ours: it can be prior art, a baseline, the reason we asked, or a
contradiction.

A quote check is not a quality check, and this cost us a third of the library before we noticed.
A table row, an entry from a notation list and half a formula are all present in the paper, so they
pass verification and then sit there as claims nobody can use. `record_paper_claim` therefore also
looks at the shape of the statement and refuses a fragment: shorter than 80 characters, cut
mid-sentence, a row of pipe-separated numbers, an item from a numbered list, a formula with no text
around it, or an empirical claim with no magnitude — where a figure or theorem number counts as a
pointer, not a measurement. The refusal names the defect, so rewriting is cheaper than arguing.

The library currently holds 509 papers decomposed into 7906 claims: 2733 empirical, 2535 about a
method, 2170 theoretical, 468 definitions. Every quote is verified against the stored text and
every empirical claim carries a value.

Records live inside a project and follow its access rules, so you need to be a member of that
project. Papers are shared: the library has no per-project walls.

### Who wrote it: the person answers, the agent acted

One token per person is not enough. Three agents sharing one token turn every record into
"a service account wrote this", and then nobody can tell which agent to stop when one of them starts
writing noise. So a token carries a label naming the agent or machine it belongs to, and the journal
records both: the person as the subject, the label as the actor. That is the split RFC 8693 draws
between subject and actor, without the token exchange a ten-person lab does not need.

```
issue_agent_token(label="rl-muon")        # a member issues their own; a lead may add email=…
list_agent_tokens()                       # labels and dates; the tokens themselves are not stored
revoke_agent_token(label="laptop")        # a stolen laptop costs one agent, not the person
```

The label is read from the database by the token, so it cannot be forged. A caller may additionally
send an `X-Lab-Actor` header saying what fired inside the agent — `codex_hook`, `board_sync`,
`digest` — and the journal shows it beside the label: `veprikov via rl-muon / codex_hook`. That
header is the caller's word rather than the database's, which is why it sits next to the label
instead of replacing it, and only characters safe to print survive.

`scripts/lab_connect.py --token <token>` does the client side: opens the tunnel, registers the
server in Claude Code and Codex with the right headers, labels the machine by its hostname, and
verifies that a call actually lands. Nothing to configure by hand.

### 4. What you learned is not a hypothesis, and the lab still wants it

Two record kinds exist for exactly this, because widening "hypothesis" would have cost the one
thing that makes a hypothesis worth citing — that it must be falsifiable.

```
upsert_resource(slug="cloud-ru-mlspace", title="Cloud.ru MLSpace", kind="cluster",
                role="…", capacity="…", quirks=["…"], themes=["…"])
record_journal(body="…", kind="measurement", theme="lab-agents", resources=["shkodnik-opt"])
```

**A resource** is a machine, cluster, quota, account, licence, dataset, budget or service the lab
has. It belongs to no project, like a paper, because one machine serves everybody. Its most useful
field is `quirks`: the gotchas that cost somebody a broken run — CUDA numbering that disagrees with
`nvidia-smi`, a host without systemd, a root filesystem too small for scratch. Access says how to
reach it and who grants it; a password there is refused, because this base is shared and a record
outlives the people in it.

**A journal entry** is an honest observation, incident, measurement, onboarding note or
organisational fact with no falsifier and no experiment behind it. Promoting one to a hypothesis
stays a separate, deliberate act. Tasks are not journal entries: they live on the project board.

Both are searched together with everything else, so "what cards does that server have and what is
wrong with its CUDA numbering" answers from the resource, and "why did the service stop answering"
answers from the journal.

### 5. Your knowledge is in a meeting, not in a file

The `call-notes` skill turns an approved meeting summary into records and lab tasks. Its runner lives
in the lab's private repository, because meeting content and member names are not public.

## Rules that hold for everybody

**A natural key is mandatory for papers** — arXiv id, DOI or Zotero key. Without one the next write
cannot recognise the paper and would file a duplicate beside it. Keys accumulate: a writer who knows
only the arXiv id never erases a stored Zotero key.

**Empty never erases.** Fields you leave out keep their stored values, and sections are replaced only
when you send some. Pushing a short card over somebody's full reading note takes nothing away.

**Every write names its author** in the audit log, so "who changed this paper" always has an answer.

**Subject tags are computed, not written.** A dictionary of terms is matched against the title,
abstract, summary and the section text; a shared tag is what links a hypothesis to a paper. Tags can
always be checked against the place in the text they came from, which is why they are trusted at all.
Adding a term is a code change, and a deliberate one.

## Reading

`search_lab` (scope `lab`, `library` or `all`), `list_themes` and `get_theme_context` for the map,
`get_paper` for one paper with its sections, `find_related_papers` and `related_by_terms` for the
bridge between the two corpora, `who_works_on_what` and `recent_changes` for people and movement.

Semantic search is optional and off unless the service enables it. After a large library sync, run the
warm-up (`scripts/warm_all.py` in the private repository) instead of letting the first query compute
thousands of vectors: a single query is capped at a small number of missing vectors precisely so that
a cold corpus degrades to word search instead of hanging.
