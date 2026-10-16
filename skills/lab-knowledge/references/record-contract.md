# Shared research records and destinations

Apply this contract when a workflow publishes research, literature, or meeting outcomes.
Client-specific paths, credentials, and permissions remain in the local installation.
There is no service and no payload: every record is a file in a git clone. This document
describes what belongs where, not an API.

## Everything an agent writes goes through git

The base is a git repository per work, and writing into it is ordinary git: a branch
`claim/<CODE>`, files, `git commit -F -`, and `git push -o merge_request.create` which opens
the proposal in the same push. One proposal per claim. There is no wrapper command for this
and no service to call. The full mechanics are in [publishing.md](publishing.md).

Two things follow, and both bite in practice:

- **A record exists when it is merged into `main`.** A checkpoint, a local file and a
  proposal with open remarks are not records. Merging is done by a human, or by an agent on
  that human's word said in the same session, and the agent leaves that word in the proposal.
- **Public codes are labels, not addresses.** They are renumbered when a work is tidied:
  `H-DYC-035` became `H-DYC-007` in a quarter of an hour on 23-09-2026. Quote UUIDs.

## Resolve the destination

Reuse an existing project and its stable identifiers. Search by subject and known aliases
when the identity is unclear. A missing local binding does not mean the project is absent.
Report conflicting bindings before creating a replacement.

Tasks live in GitLab: a work's own issues for its science, the group `ops` for everything
else. Customer stages, acceptance and administrative obligations go to `ops/management`.
Preserve existing IDs, history, access and links.

Resolve Obsidian paths from the client's project mapping and current vault conventions.
Research-paper projects can have a theme between `Papers` and the slug. Literature notes
use the live `Literature` taxonomy, not a remembered conference folder or a hard-coded path.
Do not change the library's taxonomy as a side effect of ingesting one paper.

## Classify by meaning

| Information | Canonical destination |
|---|---|
| Private transcript, draft, unfinished interpretation | Mapped Obsidian project |
| Personal reminder | Personal Operon task |
| Shared action, executor, deadline | the work's own issues, or the group `ops` |
| Personal Hermes task | Hermes board is authoritative; a private Obsidian view keeps its original task ID and source timestamp |
| Falsifiable scientific assertion | `claims/<CODE>/README.md` in the work, with its falsification criterion |
| A finished run: hyperparameters, metrics, environment, commit, hardware | `claims/<CODE>/runs/<E-code>.md`, written by the recorder `lab_run.py`, not by hand |
| A group of runs that answers one question | `claims/<CODE>/series/<S-code>.md`, with the runs listed in its table |
| Assumptions, argument, and mathematical result | `claims/<CODE>/theory/<D-code>.md` |
| Reviewed rule or choice | Not a record of its own. What was decided about the method goes into the claim's `decided`; a rule of one series' protocol goes into that series |
| External paper and what it asserts | Library paper, paper claims, and typed links |
| A changed way of working: a rule, a place, a tool, something switched off | `brainlab/journal` |
| An instruction other people need | `brainlab/handbook` |

Do not copy a personal Hermes queue into the laboratory's issues or personal Operon tasks. A shared
task may be linked to a Hermes task only through its confirmed project and original task ID.
Reading assigned work does not authorize moving every task on that board. Move an explicitly
delegated shared task only after checking its completion criteria and current status, then
read it back. Local Canvas movement does not update either source board. Keep one authority
for each task's status; a linked personal execution task is not a second shared board.

One record expresses one independently assessable assertion or action. Split a combined
claim when its parts have different evidence or conditions; do not impose a target number
of claims, characters, tasks, or proofs. Keep assumptions and scope with the claim.

A completed task does not establish a scientific result. An experiment request is not a
measurement, and a theorem is not a training run. Preserve the actual status, configuration,
metrics, units, seeds when applicable, artifacts, and limits of each result. Use structured
metrics when the live evidence schema supports or requires them.

Do not invent a hypothesis to accommodate an operational note. An administrative decision
does not need a fabricated experiment. Do not force a proof into empirical evidence when
the caller lacks a derivation adapter; report that missing capability.

## Literature and quotations

The `statement` is a faithful, self-contained formulation of the paper's claim. It may be
paraphrased or translated with its assumptions preserved. It is not required to be a literal
sentence from the paper.

A quotation is optional. The claim needs a source and location, not a copied sentence.
If a quote is deliberately included, label its actual origin and do not call a translated
reading note the author's words. Do not impose minimum lengths or quotas by claim kind.
If an older server still requires `quote`, retain the prepared claim as pending and report
that contract mismatch. Do not invent a quotation, pad the statement, or edit source text
to satisfy that requirement. Existing quoted material need not be deleted.

An outside paper supports a literature relation; it is not evidence that our own experiment
ran. Use an appropriate typed link such as `prior_art`, `baseline`, `inspired`, `supports`,
`contradicts`, or `reproduces` only when the relation is established.

Search before inserting papers or claims. Preserve existing metadata, sections, and links;
do not replace a full reading note with a short card. Follow the current tool's merge rules
and the library sync's ownership rather than assuming every upsert is harmless.

## Publication and read-back

Use the owner's explicit authorization for the object or bounded batch. Show the destination,
content, source, and visibility when approval is still needed; do not ask again for the same
already approved operation. A watcher's authority is limited to its assigned project and
publication scope. A private note, a search hit, or `visibility: lab` alone is not permission
to publish.

Publish each approved object once using the destination's supported deduplication and
idempotency mechanism. Preserve returned IDs and verify the stored content. Report partial
success per destination. Do not retry with broader credentials, fabricate missing fields,
or turn a failed write into a completed checkbox.
