# Which model does what, and what it costs

The work in this repository splits into four jobs with very different price and quality profiles.
Sending all of them to one model is how a literature pipeline becomes expensive without becoming
better.

## The four jobs

| Job | What it needs | What we run |
|---|---|---|
| Interactive agent: reads the repo, edits code, decides what to do next | judgement, long context, tool use | Claude Code (Opus for judgement, Sonnet for volume) |
| Writing a paper analysis: eight sections per paper, dozens of papers | throughput, decent reasoning, cheap | Haiku inside `paper-ingest`; a separate CLI lane for batches |
| Pulling hypotheses and decisions out of a text | precision and restraint, small output | the interactive agent, under human review |
| Retrieval: embeddings and reranking | nothing from a provider | local models, see below |

## Retrieval runs locally

Search does not call any provider. Embeddings are `intfloat/multilingual-e5-large` through
`fastembed`, enabled with `LAB_KNOWLEDGE_SEMANTIC_ENABLED=true`; the optional cross-encoder is
`jinaai/jina-reranker-v2-base-multilingual`, off by default. Both run on CPU on the service host, so
the cost of search is the host, not tokens.

## Cheap bulk reading

For "read forty papers and write a full analysis of each", a cheap model with an OpenAI-compatible API
is the right tool. As of 18-08-2026, DeepSeek publishes peak and off-peak rates per million tokens:

| Model | Input (cache miss) | Output | Cache hit |
|---|---|---|---|
| V4-Flash off-peak | $0.22 | $0.66 | $0.007 |
| V4-Flash peak | $0.44 | $1.32 | $0.014 |
| V4-Pro off-peak | $0.66 | $1.98 | $0.022 |
| V4-Pro peak | $1.32 | $3.96 | $0.044 |

Peak is 01:00–04:00 and 06:00–10:00 UTC, everything else is off-peak; these rates took effect on
16-08-2026, two days before this table, so check them before planning a large batch. A queue of paper
analyses is exactly the workload that should be started off-peak.

Sources: [DeepSeek pricing](https://deepseek.ai/pricing),
[price change 16-08-2026](https://www.techtimes.com/articles/324764/20260817/deepseek-v4-api-prices-quadruple-peak-what-developers-pay-starting-now.htm).

## Feeding the base: what a model has to be able to do

Writing to the shared knowledge base is not a writing task, it is a tool-use task, and that is the
only requirement worth checking before pointing a new model at it:

- **reliable tool calling over ~24 tools** with typed arguments. The write path is a chain —
  hypothesis, run, status, evidence — and every step takes ids returned by the previous one;
- **reading its own tool results.** The service answers with more than a receipt: a missing resource
  slug comes back as `unregistered_resources`, an undefined internal name as `unexplained_terms`, a
  fresh project as `next_steps`. A model that ignores the response body loses exactly the guidance
  that keeps records readable;
- **restraint.** A hypothesis needs a falsifier, evidence needs its experiment, and an invented
  record that someone later cites is worse than a missing one. This is a property of the prompt and
  the model both;
- **no long context needed.** One record is a few hundred tokens; the base is read through search,
  not by loading it.

What we have actually seen do the whole chain unattended: **Opus 5** inside Claude Code, and
**gpt-5.6-sol** through Codex inside the Hermes agents on the server — the second one recorded a
project, its hypotheses, four experiments and their evidence across a night, concluded a refuted
claim itself and reported the codes.

What is reasonable but only partly verified for this path: **DeepSeek V4** and other cheap OpenAI-compatible
models. They are already the right tool for bulk paper reading above, and the chain is mechanical
enough that they should manage it under review; nobody has run it end to end here, so do not
promise it. Small local models are not suitable: they lose the id chain, not the prose.

A cost note, because it decides how often an agent writes. One knowledge record costs a few hundred
output tokens and one or two calls. What is expensive is the surrounding turn: the agent re-reads
its context to decide there is something worth recording. That is why the autonomous agents are
asked once every five turns rather than every turn, and why findings are buffered in a file and
flushed together.

## Switching providers: ask for a role, not a model

Callers name the job, not the model. `config/llm-routes.toml` maps eight roles onto providers, and
`scripts/lab_llm/route.py` resolves one:

    python3 scripts/lab_llm/route.py ideas --json
    LAB_LLM_IDEAS=openrouter/some-model python3 scripts/lab_llm/route.py ideas

The lab's choice, and the reason for it: **thinking goes to DeepSeek, reading goes to Claude.**
Idea generation, arguing about a hypothesis and writing up something new run on `deepseek-v4-pro`,
which is the default provider for anything not stated otherwise. Literature review stays on Claude,
where long context and careful quoting matter and the volume is bounded. Bulk paper analysis and
call notes go to `deepseek-v4-flash`, where throughput is the whole point. Retrieval names no
provider at all.

An unknown role is refused rather than quietly substituted: a silent default is a bill for work
nobody ordered. `--check` prints which roles have no key, and a key is never printed, only its
presence.

What routing cannot do, and it is worth being blunt: a skill that executes inside Claude Code runs
on Claude by construction. What can be routed is everything that leaves in its own process —
the Hermes agents on the server (`model.provider` per profile), batch lanes, and any script that
calls an API itself. Everything else is a Claude Code session and the table does not change that.

The batch lane still shells out to a CLI, one process per paper, each with its own home directory,
and the queue watches for a verdict file and restarts a lane that dies. That is honest rather than
elegant, and it has one advantage: a lane that writes its result to a file can be reviewed and
re-run per paper, whatever produced it.

## What must never go to a model

Some values look like a language task and are not:

- **Citation keys** come from the BibTeX block fetched from an external API. A generated key silently
  breaks the bibliography, so a hook blocks any `\cite{}` whose key is missing from `references.bib`.
- **Subject tags** come from a term dictionary matched against the text, so every tag can be shown at
  the place it was found. An invented tag is worse than a missing one.
- **Themes** come from the library folder or are passed explicitly and checked against existing themes.
- **Record codes** are assigned by the service, in sequence, and never reused.

The rule behind all four: if a value must be verifiable later, compute it and let a human extend the
rules. Ask a model for judgement, not for identifiers.
