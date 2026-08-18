# Human rebuttal pattern cards

These cards are retrieval aids, not authority. Select by concern type and load **at most one primary card plus one secondary card**. Never load all cases by default. Re-derive every factual or mathematical answer from the current submission, reviews, configs, and logs. Do not copy wording from the examples.

## Card 1: Refusal Axes, local score gains defeated by core-method drift

**Source anchors:** Refusal Axes OpenReview export, pp. 1–2 (program decision and author AC summary), pp. 3–9 (reviewer threads); submitted paper, pipeline and graph-construction sections.

**Trigger.** Reviewers asked for external steering baselines, judge robustness, utility checks, defensive evidence, and justification of GRPO. The original pipeline used Wikidata for the paper's defining knowledge-retrieval stage.

**Move.** The response supplied comparisons with Heretic, RDO, and SOM, added MMLU and a second judge, showed a defensive use case, and explained why low-dimensional black-box optimizers did not match the actual optimization problem. Two reviewers raised their scores by two points, and another remained strongly positive.

**Evidence.** The added measurements directly targeted requested decision tests. The AC summary reported post-rebuttal scores of 5, 4, 6, and 2.

**Concession boundary.** The new results used WordNet after the authors found the submitted Wikidata graph semantically noisy. That was not a small implementation correction. It replaced the first stage and central methodological contribution.

**Outcome.** Reject. The program decision held that results from the unreviewed WordNet variant could not validate the submitted Wikidata pipeline. Inconsistent judge naming and swapped baseline references compounded the provenance problem.

**Failure lesson.** A rebuttal can win individual concerns yet lose the paper globally. Before running anything, classify each change as clarification, peripheral fix, or core-method replacement. If it is core, preserve an original-method comparison or concede that the evidence belongs to a resubmission.

## Card 2: PPBC federated learning, scientific concerns closed by targeted breadth

**Source anchors:** PPBC OpenReview export, pp. 1–2 (decision and AC discussion), pp. 3–16 (reviews, rebuttals, and follow-ups); paper Sections 3–4 and Appendix B.

**Trigger.** Reviewers viewed the theory as substantial but found the evaluation narrow, the surrogate construction unclear, and inactive-client comparisons incomplete. They also questioned assumptions, communication cost, weighting and sampling behavior, and novelty relative to error-feedback methods.

**Move.** The response added FedDyn, FedNova, MOON, and the inactive-client baseline F3AST in the difficult non-IID setup, exposed PPBC+ results, varied local epochs, and answered algorithmic questions with explicit reductions. For theory and novelty concerns, it showed which standard cases are recovered and why compressed-communication arguments do not transfer mechanically.

**Evidence.** Reviewer follow-ups say the questions were resolved, one reviewer explicitly raised the score after the missing comparison was added, and all reviewers ultimately recommended acceptance on scientific grounds. The program decision highlights the combination of extensive theory, new experiments, and detailed clarification.

**Concession boundary.** The authors accepted presentation and evaluation gaps and committed to moving essential evidence into the main paper. They did not concede that PPBC was merely FedAvg or error feedback.

**Outcome.** Scientific rebuttal success. The recorded rejection was attributed to an external sanctions decision, not unresolved technical review.

**Failure lesson.** Escalation to the AC should summarize concern-by-concern closure and remaining questions calmly. A frustrated early message was followed by an apology and a concrete status table. Use process escalation only after substantive responses exist.

## Card 3: Warm-up, causal controls and scale change the discussion

**Source anchors:** Warm-up OpenReview discussion export, pp. 2–4 (causality, scale, statistics, RAdam), pp. 5–7 (scale, sensitivity, Scion), pp. 8–11 (assumption and theory follow-up); paper Sections 3–6 and experimental appendices.

**Trigger.** Reviewers argued that warm-up-trajectory curvature was circular, that 124M/210M models did not support the scale motivation, that target loss replaced the warm-up knob, and that RAdam and Scion were missing. Theory follow-up requested a satisfying objective and comparison with fixed-step GD.

**Move.** The rebuttal isolated causality with no-warm-up, no-decay, varying-learning-rate, and deterministic full-batch controls. It surfaced and verified already-prepared 583M and 720M evidence, then added bounded second-seed, task-sensitivity, RAdam, and Scion checks. It separated estimable target loss from searched duration, connected Adam variance to geometry without claiming equivalence, and added a mathematical example while narrowing the stochastic theorem.

**Evidence.** Reviewers credited the larger scales, sensitivity analysis, Scion comparison, and causal checks. Multiple scores increased. The response reported narrow margins and the run-to-run floor rather than calling a single curve significant.

**Concession boundary.** The authors accepted that the original causal evidence and breadth were insufficient and sharpened the scope. They defended the central mechanism only where new controls or derivations supported it.

**Outcome.** Strong score-moving rebuttal evidence, with some theory skepticism remaining in one thread. No final acceptance should be inferred from the discussion export alone.

**Failure lesson.** Inventory completed and running evidence before experiment triage. Then choose missing work by reviewer decision test: causal control before decorative benchmarks, central scale evidence before repeated small-scale runs, a direct or contextual competing-mechanism baseline when appropriate, and a constructive witness or reduction before rhetorical theory defense.
