# Canonical Concern Ledger

Use one ledger for all agents. No agent drafts from raw reviews after the ledger is frozen.

## Atomic decomposition

Split every review into claims that can be answered independently. Preserve the exact reviewer quote and location. A sentence such as “the novelty is unclear and the baseline is weak” becomes two concerns. Merge duplicates only through `duplicates`; never delete them.

```markdown
| ID | Reviewer | Exact concern | Type | Severity | Decision criterion | Paper ground truth | Evidence need | Evidence | Strategy | Action | Owner | Status | Dependencies | Duplicates |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R2-C03 | R2 | “…” | correctness/theory/novelty/experiments/baseline/statistics/scope/clarity/reproducibility/ethics/presentation | decision_critical/major/moderate/minor | What would change the reviewer's or AC's assessment? | section, theorem, table, code | already_supported/needs_derivation/needs_experiment/needs_citation/concede_and_repair/clarify_scope/insufficient | E-level + artifact | shared stance enum | smallest sufficient move | agent | open/partly_resolved/resolved/blocked | IDs | IDs |
```

For each row, attach a private evidence packet:

- `paper_anchor`: page/section/equation/table plus the exact submitted claim.
- `reviewer_model`: strongest charitable interpretation, not the easiest wording to defeat.
- `answer_core`: one-sentence direct answer, before context or thanks.
- `support`: theorem derivation, prior-art source, config, log, or computed number.
- `revision_delta`: exact old claim and exact proposed replacement, if any.
- `residual_risk`: what remains unresolved after the response.

## Priority

Order work by expected decision impact, not review order:

$$P(c)=\Pr(\text{answer changes assessment})\times \text{severity}\times \text{answerability}.$$

Use qualitative high/medium/low values. Fatal validity, novelty, missing decisive baseline, and central empirical-support concerns normally come first. Stylistic requests come last unless they reveal a genuine misunderstanding of the contribution.

## Strategy labels

- `correct_misunderstanding`: submitted evidence resolves a factual premise; quote and locate it, then improve exposition.
- `clarify`: make an existing distinction or scope boundary explicit.
- `defend`: rebut an inapplicable premise with verified evidence.
- `concede_local`: fix a real issue without changing the method or central claim.
- `narrow_claim`: state the weaker claim supported by the evidence.
- `promise_revision`: commit to a concrete presentation or local manuscript change.
- `run_experiment`: run one feasible discriminating test through the launch gate.
- `cannot_resolve`: give the strongest existing evidence and record the residual risk.

Track method identity separately as `same-method`, `local-fix`, or `core-revision`; never encode `core-revision` as a rhetorical stance.

## Freeze and coverage rules

1. Concern Mapper freezes IDs before drafting. Later concerns append new IDs.
2. Paper Grounder verifies every `paper_anchor`; “we already show” without a location fails.
3. Theory/Experiment leads may update evidence and strategy, never the reviewer's wording.
4. Composer answers every non-duplicate row exactly once. Cross-references must name the primary ID.
5. Verifier reports: total atomic concerns, answered, partial, unsupported, and omitted. `omitted > 0` blocks delivery.
6. Conflicting reviewer requests remain separate rows linked by `dependencies`; the response explains the tradeoff to the AC.
