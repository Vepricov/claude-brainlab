# Hard-Case Playbook

Lead with the answer, then evidence, revision, and residual limitation. Never bury a real defect under tone.

## Theorem or proof bug

1. Re-derive the exact theorem and identify whether the fault is statement, assumption, constant, proof step, or algorithm-to-theorem bridge.
2. Classify: local correction, material weakening, or invalid central result.
3. Give the corrected statement and which downstream claims survive. Do not claim a repaired proof without line-by-line verification.
4. If central, concede and narrow. An experiment cannot rescue mathematical incorrectness.

## Novelty attack

Build a claim-by-claim comparison to the closest prior work: object, setting, assumptions, mechanism, guarantee, and evidence. Acknowledge overlap exactly. Defend the smallest genuine delta and why it matters. For a new assumption or theoretical regime, construct a simple witness where every new term is active, disable the terms one by one, and compare the resulting method to the canonical fixed-step or prior rule under known constants. Add missing citations only after verification. If the main method is known, reposition around a supported analysis, setting, or result rather than asserting broad novelty.

## Quantifier or definition trap

Before defending a formal statement, swap universally quantified variables, substitute the optimum, initialization, zero/noise-free limits, and boundary points, and check whether the claim collapses or becomes stronger than intended. Align population and samplewise assumptions, norm/dual-norm definitions, sign and nonnegativity constraints, and theorem constants with practical fitted coefficients. A rhetorical explanation cannot repair a globally inconsistent definition; correct or narrow it explicitly.

## Missing baseline

First test comparability. If valid and decision-critical, run the matched baseline using the experiment gate. Report tuning budgets and all mismatches. If invalid, demonstrate the incompatibility from the baseline's own formulation or official implementation, then offer the nearest valid control. “No time” alone is not a scientific answer.

If the reviewer names a different optimizer family to test a competing mechanism, classify it as an `adjacent_contextual_comparator`, not automatically as a core revision. It can answer whether that explanation suffices in a matched task, but it cannot replace the nearest direct baseline or validate the submitted mechanism by itself.

For a defensive or reversed-objective claim, prefer the closest baseline with a transformation already defined by its paper or implementation, such as a documented sign reversal. Match the defensive objective and evaluation setting. Do not extrapolate defense rankings from attack results, and do not invent adaptations for methods whose objective must be redesigned.

## Weak statistics or marginal gains

Expose per-seed results and paired differences. Add frozen seeds only if feasible. Separate statistical uncertainty from practical value and compute cost. If the interval contains effects that contradict the claim, narrow it. Never turn one seed, overlapping intervals, or a post-hoc test into “significant” or “robust.”

## Circular evidence or mechanism claim

State the alternative causal explanation explicitly. Reuse of the proposed method's own trajectory, reward judge, selected checkpoint, or tuned configuration cannot independently validate the mechanism that produced it. Freeze all downstream choices and intervene on only the disputed factor. Add a negative control and measure the claimed mediator as well as the endpoint. If no intervention separates the explanations, downgrade the claim from causal/mechanistic to descriptive association.

## Impossible requested experiment

Name the concrete barrier: unavailable data/license, incompatible setting, compute beyond the period, absent implementation, or test that cannot identify the concern. Quantify it when possible. Provide the closest discriminating alternative and existing evidence. State what remains unanswered. Do not fabricate a timeline or expected outcome.

## Contradictory reviewers

Keep both concerns in the ledger. Identify the shared evaluation criterion, then explain why one scoped response satisfies both or why the requests trade off. Prefer a sensitivity analysis or explicit scope boundary over two inconsistent promises. Write the synthesis so the AC can adjudicate it without reconstructing the conflict.

## Nonresponsive reviewer

Post one concise, complete response with the decisive evidence. Do not repeatedly ping or ask for a score. Use the venue's AC/confidential channel only for procedural issues and only as permitted. Address the response to the record and AC: exact concern, resolution, evidence location, residual limitation.

## Core-method revision

Examples: swapping the knowledge source, objective, architecture, theorem setting, principal dataset, or evaluation definition. Label it explicitly as a new variant, never as clarification of the submitted method. Do not use its results to claim the original concern is resolved. Defend the submitted method with submitted/local evidence, narrow the contribution, or reserve the revision for resubmission. Check venue policy before uploading any revision.

Require a field-by-field method-identity diff before accepting any new result. A changed knowledge source in the primary submitted-method arm is presumptively a core revision even when the surrounding graph or optimizer formulation is unchanged. This does not prohibit a labeled source-swap comparator against an unchanged submitted arm; it prohibits using the changed arm as the paper's replacement result.

## Follow-up consistency drift

Every follow-up can introduce new scientific claims and new errors. Re-run citation-to-method mapping, entity/model names, table values, units, percentages, and method identity across all reviewer threads. Add newly raised concerns to the canonical ledger. Never summarize a concern as fully resolved when the reviewer marks it partial or when decisive evidence belongs to a core revision.

## Review based on a factual misunderstanding

Assume the paper failed to communicate. Quote the submitted definition/result and give a page/section/table anchor. Explain the implication in one sentence and state the clarity edit. Avoid “the reviewer missed” or an answer that merely repeats the original wording.

## Novel requested claim or scope expansion

The rebuttal need not prove a stronger paper than submitted. State that the request is outside the defined setting, explain why, and test only if it directly changes assessment of an existing central claim. Do not absorb speculative scope into the contribution list.

## Reviewer misconduct or process issue

Separate scientific disagreement from guideline violations. Preserve exact evidence, remain factual, and use only the official private reporting route. Never threaten, deanonymize, speculate about identity, or turn the public response into a procedural complaint.
