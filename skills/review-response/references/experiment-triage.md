# Experiment Triage and Evidence Levels

Run experiments to answer a decision-critical uncertainty, not to create a larger results dump.

## Existing evidence registry first

Before designing anything, inventory all completed, running, queued, planned, failed, and cancelled experiments from configs, logs, checkpoints, job metadata, draft tables, and author notes. Ask the authors directly about evidence relevant to every decision-critical concern. For each match record status, method identity, setting, seeds, concrete artifact paths, failure/exclusion reason when applicable, and whether the result has been independently recomputed. The first triage decision is therefore one of: verify existing evidence, monitor without claiming, re-analyze, launch new work, or narrow the claim. Never infer “too expensive to run” when the relevant run is already complete or underway.

## Evidence levels

| Level | Meaning | Allowed language |
|---|---|---|
| E0 | Proposed or expected; no artifact | “we propose/will test”; never imply a result |
| E1 | Static claim or number in paper/review, not independently traced | “the submission reports” |
| E2 | Config/table/log inspected and arithmetic checked | “artifact inspection confirms”; no robustness claim |
| E3 | Reproducible smoke or single completed run | “in this run”; no significance/generalization claim |
| E4 | Predefined paired multi-seed protocol completed, with uncertainty | “across $n$ paired seeds…” with effect and interval |
| E5 | Independent replication or broad, preregistered-style validation across relevant settings | strong general claim only within tested scope |

One seed remains E3 even if it matches the desired result. A mean without seeds, pairing, dispersion, or raw outputs is at most E2.

## Revision classification gate

Before launching anything, classify the proposed answer:

- `same-method`: evaluates the submitted algorithm, assumptions, objective, and claims unchanged.
- `local-fix`: corrects an implementation bug, typo, missing control, or narrow analysis without changing the paper's identity. Disclose the delta and rerun affected comparisons.
- `core-revision`: changes the central method, representation, objective, theorem assumptions, dataset contract, or main evaluation protocol. Do not use new performance to defend the original submission. Escalate to the coordinator and venue rules; usually concede, narrow, or reserve for a resubmission.

If classification is disputed, treat it as `core-revision` until resolved.

Before admitting any rebuttal-only result, diff the **primary submitted-method arm** against the frozen submission: knowledge/data source, representation, objective/reward, trainable parameterization, algorithm/update, dataset/split contract, and evaluator roles. Record every changed field. A changed knowledge source or other defining pipeline input in that primary arm is automatically quarantined as `core-revision` until the coordinator proves otherwise. Quarantined primary-arm results may describe a new variant, but cannot resolve a concern about the submitted method. A deliberately changed, clearly labeled comparator or swap-only ablation is allowed when the submitted arm remains unchanged; it tests component necessity and must not be presented as the submitted method.

Classification applies to the submitted method, not to every comparator. A separately labeled baseline from another optimizer family is an `adjacent_contextual_comparator` when it tests a competing explanation without replacing the submitted method. Its result may support or weaken that explanation, but cannot establish direct superiority of the submitted method.

## Minimum discriminating test

For each request, write before running:

```markdown
Concern:
Competing explanations H1/H2:
Smallest test whose outcomes separate them:
Frozen method/config/checkpoint/data split:
Comparator and tuning budget:
Primary metric and direction:
Seeds/pairing and uncertainty estimator:
Decision table for positive, null, and negative outcomes:
Compute/time owner:
Artifact paths:
```

Prefer verified existing evidence and re-analysis first. Rank remaining tests by decision relevance, isolation, feasibility, and reviewer specificity, not by a universal experiment-type hierarchy. A test is not discriminating if both plausible explanations predict the same outcome. When scale is part of the paper's central motivation and explicitly named by a reviewer, one credible additional scale can outrank repeated small-scale evidence. State whether the evidence is decision-grade or only a bounded variance-floor check.

## What to run

- **Missing baseline:** reproduce the closest valid baseline under matched data, preprocessing, budget, stopping, and tuning. If impossible, use its official artifact and disclose mismatches.
- **Competing explanation:** a contextual baseline may change optimizer family if that family uniquely instantiates the reviewer's hypothesis. Label it contextual, match the surrounding task/budget as far as possible, and do not present it as a direct method comparison.
- **Component necessity:** remove or replace exactly one component while keeping all other choices fixed. If two or more components differ, reject the result for causal attribution and redesign a swap-only control.
- **Causal/mechanistic claim:** intervene on the claimed mechanism and include a negative control; correlation along one training trajectory is insufficient.
- **Robustness/statistics:** paired seeds with identical splits/initializations where possible. Report per-seed values, mean/median as appropriate, effect size, and a justified interval.
- **Scale/generalization:** choose the smallest additional scale/domain that tests the stated extrapolation boundary, not an unrelated benchmark.
- **Theory counterexample:** first run a symbolic/numerical sanity check, then repair or narrow the theorem; experiments cannot prove a false theorem.
- **Theory applicability/novelty:** attempt a constructive witness with every claimed new term active. Disable each term, derive the limiting behavior, and compare with a fixed-step or canonical method using known constants. This is often more decision-changing than another benchmark.

## Seed and uncertainty gate

Freeze the seed count before looking at outcomes. Default to at least three paired seeds for expensive ML rebuttal runs, but choose more when variance is high or the claimed effect is small. Never add seeds until significance appears. Use paired differences when runs share seeds/splits. Report all completed and failed runs, the stopping rule, and uncertainty compatible with the sample size. Do not call $p>0.05$ “equivalent”; use an equivalence/non-inferiority margin only if justified in advance.

## Launch gate

Launch only when all are true:

- concern and decision criterion are explicit;
- the primary submitted-method arm is `same-method` or an approved `local-fix`; labeled comparator or swap-only ablation arms may differ when their role, exact delta, and inability to substitute for the submitted arm are recorded;
- comparator, metric, seeds, stop rule, and analysis are frozen;
- code/config/data provenance is known;
- compute fits the rebuttal window with time for verification;
- every outcome has an honest response path.

Otherwise answer from existing evidence, narrow the claim, or mark blocked.

## Judge-role matrix

For every LLM-as-judge result, record separately: optimization reward judge, checkpoint/model-selection judge, final scoring judge, and human adjudicator. A post-hoc rescore only tests scoring sensitivity. It must not be described as re-optimization under an alternative reward. If the same judge occupies several roles, state the dependence and cap evaluator-independence claims accordingly.

## Feasibility evidence

An infeasibility or scalability answer needs the attempted command/config, parameter count derived from the implemented tensor shapes, hardware, wall time and memory trace, stopping/failure state, and a frozen comparison budget. Profiling can establish that a requested comparator is impractical in the tested setup. It cannot establish that the submitted optimizer is superior.

## Bounded variance-floor evidence

One or two additional runs can sometimes show that a reported gap is larger than the observed run-to-run variation. This is useful rebuttal evidence only as a `bounded_variance_floor`: report every run, the exact spread, and the narrow setting. Do not call it robust, significant, or a confidence interval, and do not let it replace a frozen paired multi-seed evaluation when the central claim depends on a small margin.

## Negative or null results

Never hide them or replace the question. Verify implementation and protocol once without outcome-driven retuning. Then:

1. state the result and evidence level;
2. say which claim it weakens or falsifies;
3. narrow/remove that claim or present the boundary discovered;
4. retain unaffected contributions precisely;
5. include the result if venue policy permits, or disclose it in the response.

A clean negative result that resolves a concern is more credible than an unexplained positive number. Do not promise unfinished runs as evidence.
