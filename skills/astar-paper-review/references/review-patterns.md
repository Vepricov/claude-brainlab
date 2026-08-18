# Review patterns and calibration cards

Use these cards as diagnostic habits. Load only cards whose trigger matches the current paper. Never reuse their conclusions without deriving them from the current paper and citing its exact locations.

## Comparative theory audit

Normalize every compared result across:

`problem and objective | oracle | geometry | convexity or stationarity regime | smoothness | stochasticity and heterogeneity | momentum | step size | initialization | batch | output rule | expectation or high probability | convergence criterion | leading rate | logs and constants | dimension | calls per iteration | total query, gradient, communication, memory cost`

Always test reductions and limiting cases:

- disable the new mechanism;
- set momentum to zero;
- take deterministic or zero-noise limits;
- take homogeneous, full-batch, convex, strongly convex, or PL special cases where meaningful;
- compare against the relevant lower bound;
- separate an improved numerator from stronger assumptions or a more expensive oracle.

Call results `not directly comparable` when no valid criterion or oracle conversion is available.

### Theory card: SoftSignum

**Source artifacts:** `9246_Softsignum_Smooth_Your_Si.pdf`, Theorem 3.4, Corollary 3.5, Appendix A, Algorithms 3–4; `SoftSignum_ Smooth Your Signum For Better Heterogeneity Handling.docx`, sections `Вопросы к теории`, `Вопросы к экспериментам`, and `Общие вопросы`.

**Trigger:** A generalized optimizer theorem is presented as a guarantee for a scheduled practical optimizer.

**Checks:** Derive the exact update from the regularizer. Match it to the algorithm. Normalize the stationarity measure against momentum SGD, SGD, and momentum Signum.

**Observed pattern:** The theorem controls an average of $V^*(-\delta\nabla f(\theta_k))$. The Euclidean choice gives the usual squared-gradient criterion, while the SoftSignum choice gives a different quantity involving $\log\cosh$. Equal right-hand Big-O expressions do not establish faster convergence under different left-hand criteria. The fixed-regularizer update also does not automatically cover a temperature schedule, weight decay, or an approximation used only in the implementation.

**General lesson:** Compare criteria through an explicit $\varepsilon$ conversion and prove that the analyzed update is the implemented update. A special case that recovers an SGD rate is not yet a comparison with the claimed practical method.

### Theory card: LDSD

**Source artifacts:** `4052_Zero_Order_Optimization_f.pdf`, Corollary 3.4, Theorem 3.5, Lemmas 3.6–3.7, Algorithm 2, Table 2; `Review LDSD.pdf`, weaknesses 1–10 and questions 1–4.

**Trigger:** A method claims a dimension-free zero-order rate comparable to first-order SGD.

**Checks:** Verify that initialization assumptions define a non-empty regime. Separate exact directional derivatives from finite-difference and finite-sample estimators. Compare total query complexity rather than iterations alone. Trace dimension through smoothing, sampling, and policy-estimation accuracy.

**Observed pattern:** A standard-looking rate can rest on incompatible initialization inequalities, while a second result controls a weighted gradient criterion that is not normalized like SGD stationarity. The idealized analysis can also use exact directional derivatives and an exact reward gradient while the practical algorithm uses finite differences and REINFORCE estimates. Dimension may re-enter through feasible parameters and estimator variance even when absent from the displayed RHS.

**General lesson:** First check that theorem conditions are non-empty. Then align the convergence criterion, oracle, smoothing bias, estimator accuracy, and total calls before saying `dimension-free` or `same as SGD`.

## Empirical evidence ladder

- **E0: unsupported suspicion.** A visual or numerical anomaly without internal or artifact evidence. Use `unclear`, `cannot assess`, or `raises a question`.
- **E1: paper-internal evidence.** A contradiction, omission, arithmetic issue, or unsupported inference visible in the paper or supplement.
- **E2: static artifact evidence.** Code, configs, logs, checkpoints, or aggregation scripts confirm a mismatch without executing the pipeline.
- **E3: executable smoke evidence.** A minimal faithful path runs successfully, and metric and logging wiring have been checked. A failed setup is reported separately as `execution blocked` and does not raise the evidence level.
- **E4: partial reproduction.** At least one representative claim is rerun under the paper's stated seed protocol or a predefined multi-seed paired protocol. A faithful one-seed headline run remains E3 with qualifier `headline cell checked`.
- **E5: independent reproduction.** The main conclusions reproduce across relevant tasks, baselines, budgets, and uncertainty protocol.

Evidence level and severity are independent. A central E1 contradiction may be major. An E4 mismatch may still have a benign environment explanation.

## Empirical pattern cards

### Scheduler or configuration contradiction

**Trigger:** A figure names a scheduler or configuration that conflicts with the appendix, while architecture or chosen hyperparameters are missing.

**Review move:** Request the exact architecture, per-method config, scheduler trace, selected hyperparameters, and generating command. Ask for the matched control needed to attribute the effect. Treat this as a provenance break, not proof that the number is false.

### Extra hyperparameters and reused tuning

**Trigger:** The proposed method adds hyperparameters but gets the same nominal trial count as simpler baselines, or a limiting-case baseline reuses parameters selected for the full method.

**Review move:** Request search spaces, priors, trial histories, chosen configurations, and tuning compute. Ask for both a controlled shared-config comparison and an independently tuned best-performance comparison.

### Small near-ceiling gain without uncertainty

**Trigger:** Absolute scores are plausible and near a ceiling, while claimed gains are smaller than likely seed or split variation and no raw outcomes or intervals are reported.

**Review move:** Request paired per-seed values, split identities, mean differences with 95% intervals, and a robustness check. Do not state cherry-picking as fact without selection evidence.

### Test-driven ablation defaults

**Trigger:** Test-set ablations select defaults later evaluated on the same condition.

**Review move:** Ask whether defaults were selected on validation data. If not, require frozen defaults evaluated on untouched seeds, splits, or tasks.

### Budget fairness for zeroth-order methods

**Trigger:** Methods use different numbers of forward queries per iteration.

**Review move:** Audit exact oracle accounting. Report performance against oracle calls and wall time, then add memory and tuning cost. Preserve both equal-iteration and equal-oracle views when they answer different questions.

### Theory-to-experiment diagnostic mismatch

**Trigger:** A lemma predicts monotonic or bounded behavior while the diagnostic curve visibly violates it.

**Review move:** Check that the plot measures the theorem's quantity and that assumptions hold. Request raw values, plotting code, uncertainty, and an explanation distinguishing estimator noise, smoothing, regime mismatch, and genuine violation.

## Lessons preserved from the laboratory examples

The SoftSignum review demonstrates:

- compare a new optimizer with the natural methods named in its motivation and related work;
- audit weak baselines through their actual chosen hyperparameters and schedules;
- treat extra method-specific hyperparameters as additional researcher degrees of freedom;
- require sensitivity analysis and simple schedule alternatives;
- check whether a theoretical framework covers the scheduled, regularized algorithm actually run.

The LDSD review demonstrates:

- test initialization assumptions for internal consistency;
- distinguish weighted or non-standard convergence criteria from standard SGD stationarity;
- audit finite-difference scale and exact-versus-estimated oracle gaps;
- compare ZO methods on total oracle calls, then wall time and memory;
- treat sub-percent gains without seeds or intervals as unsupported rather than impossible;
- inspect large per-method step-size discrepancies and theory-diagnostic conflicts as attribution failures.

## External patterns incorporated

- Official NeurIPS theory guidance: correctness first, assumptions judged relative to novelty and literature norms, and no automatic demand for empirical SOTA in a theory contribution: <https://nips.cc/Conferences/2026/ReviewerGuidelines>
- Official NeurIPS review form: narrative evidence, contribution-type calibration, actionable questions, and explicit criteria that could change the score: <https://neurips.cc/Conferences/2026/MainTrackHandbook>
- ICML reviewer calibration and evidence expectations: <https://icml.cc/Conferences/2026/ReviewerInstructions>
- ICLR expectations for full-paper reading, reproducibility, related work, and reasoned updates: <https://iclr.cc/Conferences/2026/ReviewerGuide>
- ARR guidance on under-tuned baselines, p-hacking, missing uncertainty, and reproducibility reporting: <https://aclrollingreview.org/reviewerguidelines>
- ARR Responsible NLP checklist for splits, compute, infrastructure, hyperparameter search, and selected values: <https://aclrollingreview.org/responsibleNLPresearch/>
- ByteDance DeerFlow contributed the useful `What / Where / Why it matters` issue structure and claim-to-evidence framing. Do not copy its forced item counts or author-identity searches: <https://github.com/bytedance/deer-flow/blob/main/skills/public/academic-paper-review/SKILL.md>
- AI Research Feedback contributed independent advocate-versus-skeptic synthesis and paper-code alignment. This skill uses the disagreement-synthesis idea only when it adds information: <https://github.com/claesbackman/AI-research-feedback>
