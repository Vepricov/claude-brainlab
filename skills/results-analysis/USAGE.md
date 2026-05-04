# Results Analysis Usage

This skill generates a **strict analysis bundle**, not a paper Results section draft.

## Default Outputs

```text
analysis-output/
├── analysis-report.md
├── stats-appendix.md
├── figure-catalog.md
└── figures/
```

## Typical Invocation Path

```text
/analyze-results (Command)
    |
    v
results-analysis (Skill)
    |
    v
results-report (Skill, optional follow-up)
```

## Applicable Scenarios

- Multi-model comparison requiring rigorous statistics
- Results aggregation across multiple seeds / subjects / folds
- Need real research-quality figures, not just figure specs
- Need to provide a credible analysis base for subsequent `results-report`

## Recommended Workflow

### 1. Prepare Input

Prepare at least one of the following:
- Seed-level `csv/json`
- Logs or directories for each experiment
- Corresponding results for baseline and ablation
- Training curves / evaluation curves / confusion or breakdown data

### 2. Run `/analyze-results`

```bash
/analyze-results path/to/results full
```

### 3. Expected Output

#### `analysis-report.md`
- Questions answered in this analysis round
- Key findings
- Which comparisons hold / do not hold
- Main caveats
- Which findings merit a full experiment report

#### `stats-appendix.md`
- `mean ± std`
- `95% CI`
- significance tests
- effect sizes
- multiple-comparison correction
- assumptions / fallback tests
- blockers

#### `figure-catalog.md`
- Filename of each figure
- Figure purpose
- Data source
- Information the caption must include
- Post-figure interpretation checklist

#### `figures/`
- Real research-quality figures, preferably in reusable formats like PDF/PNG

## Minimum Quality Requirements

### Statistics
- Cannot only report best score
- Cannot only report p-value
- Cannot confuse std and sem
- Must state correction when making multiple comparisons
- Must switch or explain non-parametric test when assumptions are not met

### Figures
- Draw real figures when data is available
- Every main figure must have error bars or uncertainty information (if applicable)
- Figures must have a clear purpose; cannot just be "pretty"
- Must explain what was observed and what it means after each figure

### Interpretation
- Write observation first, then interpretation, then implication
- If causal/mechanistic claims cannot be supported, must use conservative phrasing

## Relationship with `results-report`

- `results-analysis`: Responsible for rigorous statistics, figures, evidence verification
- `results-report`: Responsible for complete experiment summary report, narrative, retrospective, and decisions

Recommended order:

```text
experiment artifacts
    |
    v
results-analysis
    |
    v
strict analysis bundle
    |
    v
results-report
```

## Edge Cases

### Incomplete Input
If seed-level data, logs, or comparable baselines are missing:
- List missing items explicitly
- Reduce analysis intensity
- Do not generate conclusions beyond the evidence boundary

### Cannot Generate Figures
If the data structure does not support direct plotting:
- Explain the reason first
- Indicate which fields are still needed
- Do not use "visualization specs" as a substitute for real figures as a completed state

## Reference Reading

- `references/statistical-reporting.md`
- `references/figure-interpretation.md`
- `references/analysis-depth.md`
- `references/common-pitfalls.md`
