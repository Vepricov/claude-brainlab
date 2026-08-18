# Mechanical Quality Gates

The Evidence & Consistency Verifier runs these gates on the final text and ledger. Any hard failure returns the draft to its owner.

## G0: Venue compliance

- [ ] Official rules were checked live and date-stamped.
- [ ] Deadlines, readers, anonymity, revision, new-result, link/file, and length rules are satisfied.
- [ ] Final rendered character/word/page count is measured, not estimated.

## G1: Coverage

- [ ] Every review was decomposed into atomic IDs.
- [ ] Every non-duplicate ID has exactly one answer or an explicit unresolved statement.
- [ ] Cross-references point to an existing primary answer.
- [ ] Fatal/major concerns appear before cosmetic points.

Hard metrics: `omitted = 0`, `duplicate_answers = 0`, `orphan_answers = 0`.

## G2: Grounding and provenance

- [ ] Each “paper already…” claim has an exact page/section/equation/table anchor.
- [ ] Every new number has method, comparator, dataset/split, metric, seed count, uncertainty, and artifact provenance.
- [ ] Evidence level E0–E5 is internally recorded and wording does not exceed it.
- [ ] Citations and descriptions of prior work were checked against primary sources.
- [ ] No expected, running, cherry-picked, or failed experiment is presented as completed evidence.
- [ ] Every decision-critical empirical concern was checked against the experiment evidence registry before any new run was proposed.

Hard metrics: `unsupported_claims = 0`, `untraceable_numbers = 0`, `fabricated_or_unverified_citations = 0`.

## G3: Scientific consistency

- [ ] Definitions, notation, assumptions, theorem constants, datasets, metrics, and claims agree with the submitted paper or disclosed local fix.
- [ ] New edits do not contradict another reviewer response.
- [ ] Every experiment is classified `same-method`, `local-fix`, or `core-revision`.
- [ ] Core revisions are not used to defend the original submission.
- [ ] Every new table has a method-identity diff against the frozen submission; a changed primary-arm knowledge/data source is quarantined as `core-revision`, while labeled comparator/ablation arms cannot substitute for it.
- [ ] A component claim is supported by a swap-only control; evidence changing multiple components is not used for causal attribution.
- [ ] Negative/null results and material limitations are disclosed; claims are narrowed where required.
- [ ] Formal claims passed variable-swap, optimum/boundary, sample-versus-population, sign/domain, and theorem-to-implementation checks.
- [ ] Applicability/novelty defenses record a constructive witness or explicitly state that none was found, plus disabled-term behavior where relevant.
- [ ] Empirical trainable symbols, tensor shapes, parameter counts, and configs map consistently from paper to code and every reviewer response.

## G4: Experiment integrity

- [ ] Comparator, tuning budget, metric, seeds, stop rule, and analysis were frozen before results.
- [ ] Per-seed/raw outputs and configs exist at recorded paths.
- [ ] Single-seed evidence is not called robust, significant, or general.
- [ ] Failed runs and exclusions have reasons; no outcome-dependent seed stopping.
- [ ] Reported deltas and aggregate statistics were independently recomputed.
- [ ] Existing/running experiments have explicit statuses and artifact paths; running work is never forecast as evidence.
- [ ] Contextual competing-explanation baselines are not presented as direct same-method comparisons.
- [ ] Bounded variance-floor evidence is labeled narrowly and is not called robust, significant, or decision-grade multi-seed evidence.
- [ ] Judge roles are explicit: optimization reward, model selection, final scorer, and human adjudicator; rescore and re-optimization are not conflated.
- [ ] Feasibility claims have profiling artifacts and a frozen budget and are not phrased as method superiority.

## G5: Response effectiveness

For each major concern, the first two sentences contain: direct answer, decisive evidence, and action/boundary. The paragraph also states the paper change and residual limitation when relevant. The strongest charitable version of the concern is answered. No paragraph relies on gratitude, confidence, or future work as evidence.

## G6: Style and budget

- [ ] No repeated thanks, generic praise, score request, reviewer blame, or promotional language.
- [ ] No “clearly/obviously/significantly/robustly” without evidence.
- [ ] Acronyms and cross-references are resolvable locally.
- [ ] Tables remain legible in the venue renderer.
- [ ] Removing any sentence would not delete required evidence; if it would change nothing, remove it.

## G7: Skeptical reviewer and AC pass

Run a blind challenge against the final draft:

1. Reviewer: “What exact part of my concern remains unresolved?”
2. Reviewer: “Does this evidence test my alternative explanation?”
3. AC: “Did the authors change the paper's identity?”
4. AC: “Which claims survive if the new result is ignored?”
5. Verifier: “Can every number and citation be reproduced from the packet?”

Record `pass`, `partial`, or `fail` for each major ID with one-line justification. Delivery requires no `fail`; every `partial` must be visible in the final response as a limitation.

After every follow-up, rerun cross-thread citation, method-name, table-value, and claim consistency checks. Append new reviewer concerns to the ledger instead of treating the original map as closed.
