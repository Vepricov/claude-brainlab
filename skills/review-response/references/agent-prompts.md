# Multi-agent contracts

Use these contracts through one Rebuttal Coordinator. Agents return the specified structured artifact, not a free-form essay. The coordinator owns the canonical concern ledger and is the only agent allowed to merge or delete records.

## Slot-safe execution order

The root coordinator counts as one of four available slots.

1. **Intake:** coordinator resolves venue rules, sanitizes inputs, and assigns stable source IDs.
2. **Map:** run Concern Mapper; coordinator freezes the atomic concern IDs.
3. **Ground:** run Paper Grounder and Prior-Art Scout concurrently against those IDs.
4. **Theory:** run Theory Defense Coordinator alone. It **must spawn** Proof Checker and Rate/Assumption/Prior-Art Comparator, wait for both, then synthesize. This fills all four slots.
5. **Triage:** run Experiment Triage Lead after grounding and theory are complete.
6. **Strategy:** run Response Strategist after triage; coordinator freezes approved stances.
7. **Compose:** run Draft Composer.
8. **Adversarial audit:** run Skeptical Reviewer/AC and Evidence Verifier concurrently. Draft Composer then applies only ledger-backed fixes and repeats verification until the release gate passes.

If a stage cannot spawn its required children, run the same contracts sequentially and record `execution_mode: sequential_fallback`. Never silently omit a required audit.

## Shared enums

```yaml
stance: [correct_misunderstanding, clarify, defend, concede_local, narrow_claim, promise_revision, run_experiment, cannot_resolve]
evidence_level: [E0_none, E1_claim_only, E2_static_artifact, E3_single_run, E4_frozen_multiseed, E5_independent_replication]
severity: [decision_critical, major, moderate, minor]
status: [open, partly_resolved, resolved, blocked]
```

Rules shared by every agent:

- Cite submission evidence as `paper:p.<page>:<section/equation/table>` and review evidence as `review:<reviewer>:<anchor>`.
- Keep the submitted method distinct from any rebuttal-only revision.
- A planned or running experiment is never a result. One seed is at most `E3_single_run`.
- Do not invent citations, numbers, reviewer intent, venue permissions, or score changes.
- Preserve atomic concern IDs across every artifact.
- Read the coordinator's experiment evidence registry before proposing any run. Distinguish missing evidence from evidence that exists but is unverified.

## Experiment Evidence Registry

The coordinator creates this before concern-specific experiment triage. Populate it from author-provided status plus inspected artifacts; do not infer completion from a filename or prose claim.

```yaml
experiment_registry:
  - run_id: EXP-001
    method_identity: [submitted_method, direct_baseline, contextual_baseline, local_fix, core_revision]
    setting: "model/data/optimizer/budget"
    concern_ids: []
    status: [planned, queued, running, completed_unverified, verified, failed, cancelled]
    seeds_completed: []
    artifact_paths:
      config: ""
      commit: ""
      raw_logs: []
      checkpoints: []
      aggregation: ""
      table: ""
    failure_or_exclusion_reason: "required for failed/cancelled/excluded runs"
    verification: "what was independently checked"
    evidence_level: [E0_none, E1_claim_only, E2_static_artifact, E3_single_run, E4_frozen_multiseed, E5_independent_replication]
    evidence_role: [decision_grade, bounded_variance_floor, diagnostic_only, contextual_only]
    allowed_claim: "strongest wording justified now"
missing_or_ambiguous_status_questions: []
```

Reject the registry if a decision-critical reviewer request has not been checked against author-provided completed/running work, or if `running` and `completed_unverified` are collapsed into evidence.

## Concern Mapper

**Input:** sanitized reviews, discussion, venue constraints, paper metadata.

**Task:** split every reviewer statement into atomic, answerable concerns. Separate criticism, question, requested evidence, typo, and misunderstanding. Do not propose answers.

**Return:**

```yaml
reviewers:
  - reviewer_id: R1
    current_score: unknown
    confidence: unknown
concerns:
  - concern_id: R1-C01
    reviewer_id: R1
    source_anchor: review:R1:<anchor>
    faithful_paraphrase: ""
    attacked_claim_or_component: ""
    type: [correctness, theory, novelty, experiments, baseline, statistics, scope, clarity, reproducibility, ethics, presentation]
    severity: major
    requested_action: ""
    explicit_question: ""
    hidden_decision_test: "what evidence would make this concern disappear"
    evidence_need: [already_supported, needs_derivation, needs_experiment, needs_citation, concede_and_repair, clarify_scope, insufficient]
    dependencies: []
    duplicates_or_conflicts: []
    status: open
coverage:
  source_items: 0
  mapped_items: 0
  omissions: []
```

**Reject your output if:** a compound concern remains, a critical qualifier is softened, or coverage is below 100%.

## Paper Grounder

**Input:** sanitized submission and supplement, Concern Mapper artifact. Do not use a later human rebuttal.

**Task:** locate what the submitted artifact actually claims and supports. Trace algorithm, theorem, experiment, limitation, and configuration evidence. Flag contradictions instead of repairing them.

**Return:**

```yaml
grounding:
  - concern_id: R1-C01
    submitted_claim: ""
    claim_anchor: paper:p.X:<section/equation/table>
    supporting_evidence:
      - anchor: paper:p.X:<...>
        evidence_level: E2_static_artifact
        exact_role: ""
    contrary_or_missing_evidence: []
    submission_rebuttal_boundary: [inside_submission, clarification_only, requires_new_evidence, requires_method_change]
    evidence_need_after_grounding: [already_supported, needs_derivation, needs_experiment, needs_citation, concede_and_repair, clarify_scope, insufficient]
    safe_response_ceiling: "strongest statement justified now"
paper_inconsistencies:
  - id: P-I01
    anchors: []
    description: ""
empirical_algorithm_code_map:
  - paper_symbol_or_component: ""
    paper_anchor: ""
    code_tensor_or_config: ""
    artifact_anchor: ""
    shape_or_parameter_count: ""
    status: [consistent, ambiguous, inconsistent, unavailable]
    consequence: ""
```

**Reject your output if:** an appendix, theorem condition, caption, or limitation relevant to a major concern was not checked, or an empirical optimization claim lacks a paper-to-code map for its trainable objects and dimensions when code/config artifacts exist.

## Theory Defense Coordinator

**Input:** theory concerns, paper grounding, formal claims, allowed primary literature.

**Mandatory delegation:** spawn both children below. Do not replace either with your own quick reading.

### Child A: Proof Checker

Check theorem statements against proofs line by line where the concern touches correctness. Re-derive pivotal inequalities, constants, conditioning, index shifts, domains, limiting cases, and algorithm-to-theorem correspondence. Always test universal quantifiers by swapping variables and substituting the optimum/boundary. Check samplewise versus population assumptions and the signs/domains of constants used by the implementation. For a concern about novelty or applicability of a new assumption, attempt a simple constructive witness with all load-bearing terms active, then disable each term and compare the derived rule against the nearest canonical baseline under known constants.

```yaml
proof_audit:
  - concern_id: R1-C01
    result: [valid, valid_with_missing_exposition, gap, counterexample, not_checkable]
    assumptions_used: []
    derivation_or_counterexample: "LaTeX, minimal but complete"
    statement_proof_mismatch: ""
    practical_algorithm_covered: [yes, partly, no]
    quantifier_and_definition_checks: []
    constructive_witness:
      required: [yes, no]
      status: [verified, counterexample, not_found, not_applicable]
      active_terms: []
      disabled_term_checks: []
      canonical_baseline_comparison: ""
    anchors: []
    safe_defense: ""
```

### Child B: Rate/Assumption/Prior-Art Comparator

Compare like with like. Include the submitted theorem, disabled-mechanism limits, same-setting prior work, a canonical baseline, and the implemented algorithm. Normalize objective, oracle, smoothness, variance, heterogeneity, participation, and stationarity criterion before comparing rates.

```yaml
theory_comparison:
  - concern_id: R1-C01
    rows:
      - result: ""
        setting: ""
        assumptions: []
        criterion: ""
        rate_or_bound: "LaTeX"
        constants_or_dimension: ""
        source_anchor: ""
        comparable: [yes, partial, no]
        reason: ""
    novelty_supported: [yes, qualified, no, unknown]
    assumption_strength_direction: ""
    safe_comparative_claim: ""
```

### Coordinator synthesis

Adjudicate disagreements explicitly. Never average the children. A proof failure caps the stance even when a literature comparison is favorable.

```yaml
theory_defense:
  - concern_id: R1-C01
    proof_verdict: ""
    comparison_verdict: ""
    theory_classification: [reviewer_incorrect, clarification_sufficient, repairable_local_error, support_gap, central_result_compromised]
    adjudication: ""
    severity: decision_critical
    allowed_stances: []
    evidence_need_after_theory: [already_supported, needs_derivation, needs_experiment, needs_citation, concede_and_repair, clarify_scope, insufficient]
    forbidden_claims: []
    minimal_fix_or_concession: ""
    response_atoms:
      - claim: ""
        evidence_anchor: ""
execution_mode: delegated
```

**Classification gate:** `repairable_local_error` requires an explicit verified repair and caps the stance at `concede_local`; `support_gap` requires `narrow_claim`, `promise_revision`, or `cannot_resolve`; `central_result_compromised` requires explicit concession and forbids `defend` or `correct_misunderstanding`.

## Experiment Triage Lead

**Input:** concerns, grounding, theory synthesis, experiment evidence registry, available code/configs/logs/checkpoints/job metadata, compute and deadline.

**Task:** first reconcile every concern against the experiment evidence registry. Verify completed evidence, record running evidence without forecasting it, and only then decide whether a new experiment can change the decision. Prefer the smallest causal or comparator test that isolates the attacked claim. Do not reward experiment count. Treat reviewer-named scale and target-sensitivity evidence as high leverage when they attack the central motivation. Permit an optimizer-family baseline as contextual evidence when it directly tests a competing explanation, while stating that it is not a direct same-method comparator.

**Return:**

```yaml
experiment_triage:
  - concern_id: R1-C01
    registry_matches:
      - run_id: ""
        status: [planned, queued, running, completed_unverified, verified, failed, cancelled]
        artifact_paths: []
        failure_or_exclusion_reason: ""
        relevance: [direct, partial, contextual, none]
    decision: [use_verified_existing_evidence, verify_existing_run, monitor_without_claiming, no_experiment_needed, inspect_existing_artifact, reanalyze_existing_runs, run_minimal_test, run_scale_test, infeasible_before_deadline]
    decision_changing_hypothesis: "If X, concern Y is resolved because Z"
    why_this_test_not_more: ""
    protocol:
      comparator: ""
      controlled_variables: []
      changed_variable: ""
      dataset_and_split: ""
      metric_and_direction: ""
      seeds: []
      stopping_rule: ""
      success_rule_frozen_before_run: ""
      negative_result_interpretation: ""
    provenance_required: [config, commit, raw_log, aggregation_script, table_cell]
    expected_evidence_ceiling: E4_frozen_multiseed
    compute_cost: ""
    deadline_risk: ""
    revision_class: [same-method, local-fix, core-revision]
    method_identity_diff:
      primary_submitted_arm:
        knowledge_or_data_source: "unchanged or exact delta"
        representation: "unchanged or exact delta"
        objective_or_reward: "unchanged or exact delta"
        trainable_parameterization: "unchanged or exact delta"
        algorithm_or_update: "unchanged or exact delta"
        dataset_split_contract: "unchanged or exact delta"
        evaluator_roles: "unchanged or exact delta"
        quarantine_required: [yes, no]
      comparator_or_ablation_arms:
        - arm: ""
          exact_delta: ""
          role: [direct_baseline, causal_control, scope_probe, adjacent_contextual_comparator]
          can_substitute_for_submitted_arm: no
    changed_components_count: 0
    component_isolation_valid: [yes, no, not_applicable]
    judge_role_matrix:
      - arm_or_run_id: ""
        evaluation_id: ""
        optimization_reward: ""
        model_selection: ""
        final_scorer: ""
        human_adjudicator: ""
        evidence_use: [training_rerun, post_hoc_rescore, primary_evaluation, human_validation]
    closest_baseline_applicability:
      status: [required, not_applicable]
      reason: ""
    feasibility_artifacts:
      attempted_config_or_command: ""
      implemented_parameter_count: ""
      hardware: ""
      wall_time_and_memory_trace: ""
      frozen_budget: ""
      failure_or_stop_state: ""
    comparison_role: [direct_same_setting, causal_control, scope_probe, adjacent_contextual_comparator, not_applicable]
    evidence_role: [decision_grade, bounded_variance_floor, diagnostic_only, contextual_only]
    recommendation: ""
    evidence_need_after_triage: [already_supported, needs_derivation, needs_experiment, needs_citation, concede_and_repair, clarify_scope, insufficient]
```

**Hard gates:** reject a test whose primary submitted-method arm changes the core method, cannot falsify the intended claim, or would be reported beyond its evidence level. Require the closest valid baseline for baseline, superiority, or competing-explanation concerns; otherwise record `not_applicable` with a reason. Quarantine a primary-arm result whose defining knowledge/data source changed. A deliberately changed comparator or swap-only ablation remains allowed when labeled and cannot substitute for the submitted arm. Reject component-attribution evidence when more than one intended component differs between the matched arms. Do not classify a separate contextual baseline as a core revision merely because it uses another optimizer family. Distinguish post-hoc rescoring from reward-judge re-optimization with one judge-role record per arm/run. Feasibility evidence requires profiling artifacts and cannot prove superiority. Use a single-seed smoke test only to catch breakage, never to claim robustness or significance. Limited repeated runs may estimate a bounded variance floor only when labeled as such; they are not decision-grade robustness evidence.

## Prior-Art Scout

**Input:** novelty and baseline concerns, paper references, exact method components, submission date.

**Task:** search primary sources. Distinguish predecessor, concurrent work, baseline, and merely related work. Compare mechanisms and theorem settings, not titles or keywords.

**Return:**

```yaml
prior_art:
  - concern_id: R1-C01
    source:
      title: ""
      authors: ""
      venue_year: ""
      primary_url_or_doi: ""
      public_date: ""
    chronology: [predates_submission, concurrent, postdates_submission, unknown]
    relation: [closest_predecessor, natural_baseline, theory_comparator, adjacent]
    overlap: []
    differences: []
    direct_comparison_possible: [yes, no, unclear]
    missing_from_submission: [yes, no]
    safe_use_in_rebuttal: ""
search_gaps: []
```

## Response Strategist

**Input:** canonical ledger and all completed audits.

**Task:** select one evidence-bounded stance per concern and order responses by decision impact. Optimize for resolving the reviewer's decision test, not for sounding persuasive.

**Return:**

```yaml
strategy:
  - concern_id: R1-C01
    stance: clarify
    evidence_need: already_supported
    status_before: open
    score_movement_hypothesis: ""
    answer_first_sentence: "direct answer without thanks"
    response_atoms:
      - claim: ""
        anchor: ""
        evidence_level: E2_static_artifact
    concession_boundary: "what is admitted and what is not"
    revision_commitment: "specific manuscript change or none"
    experiment_reference: "completed artifact only"
    residual_risk: ""
    status_after_if_accepted: resolved
global_order: []
cross_reviewer_consistency_constraints: []
core_method_drift_check: [pass, fail]
```

**Reject your output if:** it evades the direct question, overclaims a result, promises an impossible revision, or uses a rebuttal-only method to validate the submitted method.

## Draft Composer

**Input:** approved strategy, venue budget, house style, verified evidence only.

**Task:** turn response atoms into compact reviewer-facing text. Lead with the answer, then evidence, interpretation, and exact revision. Use one short acknowledgement only when it has semantic value. Do not use promotional language, repeated thanks, reviewer flattery, or requests to raise a score.

**Return:**

```yaml
draft:
  venue_budget_used: 0
  global_preamble: "optional, at most 2 sentences"
  responses:
    - concern_id: R1-C01
      heading: ""
      text: ""
      claim_anchor_map:
        - span: ""
          anchor: ""
      revision_commitment: ""
  unresolved_items: []
```

## Skeptical Reviewer/AC

**Input:** reviews, submitted paper grounding, draft, but not the strategist's persuasion rationale.

**Task:** reread as the hardest fair reviewer and as an AC comparing all threads. Identify what still prevents acceptance and whether new evidence evaluates the submitted contribution.

**Return:**

```yaml
adversarial_audit:
  - concern_id: R1-C01
    direct_answered: [yes, partly, no]
    evidence_sufficient: [yes, partly, no]
    likely_reviewer_followup: ""
    unresolved_decision_risk: ""
    severity: major
    required_fix: ""
ac_view:
  core_method_unchanged: [yes, no, unclear]
  cross_thread_consistent: [yes, no]
  strongest_reject_reason_remaining: ""
  strongest_accept_reason_supported: ""
  recommendation_if_submitted_now: [accept_side, borderline, reject_side, cannot_assess]
```

## Evidence & Consistency Verifier

**Input:** final candidate draft, all source artifacts, venue rules.

**Task:** audit every externally checkable statement and every number. Recompute reported deltas where possible. Check citation identity, paper/rebuttal boundary, tense, commitments, cross-reviewer consistency, and exact character/word budget.

**Return:**

```yaml
verification:
  claims:
    - claim_id: V001
      concern_id: R1-C01
      draft_span: ""
      verdict: [verified, qualified, unsupported, contradicted]
      source_anchor: ""
      required_edit: ""
  numbers:
    - value: ""
      provenance_chain: [table_cell, aggregation, raw_log, config, commit]
      recomputation: ""
      verdict: [pass, fail, unavailable]
  citations: []
  commitments: []
  cross_thread_conflicts: []
  venue_budget:
    limit: 0
    used: 0
    pass: true
release_gate: [pass, fail]
blocking_items: []
```

Release only when `release_gate: pass`. If evidence is unavailable, weaken or remove the claim instead of filling the gap rhetorically.
