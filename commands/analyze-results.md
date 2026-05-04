---
name: analyze-results
description: Run the full post-experiment workflow in one command: strict statistical analysis, real scientific figures, and a decision-oriented results report. Uses results-analysis + results-report as a two-stage workflow.
args:
  - name: data_path
    description: Path to experimental results (CSV, JSON, logs, or directory)
    required: false
  - name: analysis_type
    description: Type of analysis (full, comparison, ablation, visualization)
    required: false
    default: full
  - name: purpose
    description: Optional report purpose slug (e.g. transfer-summary, ablation-report)
    required: false
    default: auto
  - name: round
    description: Optional experiment round number for report naming
    required: false
  - name: experiment_line
    description: Optional experiment line slug for report naming
    required: false
tags: [Research, Analysis, Statistics, Visualization, Reporting]
---

# Analyze Results Command

### Phase 1: strict analysis bundle
- figure interpretation checklist

### Phase 2: complete results report

```bash
/analyze-results
```

```bash
/analyze-results path/to/experiment_dir
```

```bash
/analyze-results path/to/results comparison
```

```bash
/analyze-results path/to/results full transfer-summary 3 freezing
```

|------|------|
| `analysis_type` | `full` / `comparison` / `ablation` / `visualization` |

|------|------|--------------|--------------|

```text
analysis-output/
├── analysis-report.md
├── stats-appendix.md
├── figure-catalog.md
└── figures/
```

```text
Results/Reports/
└── YYYY-MM-DD--{experiment-line}--r{round}--{purpose}.md
```

```text
{Experiment Line} / Round {N} / {Purpose} / {YYYY-MM-DD}
```

- **Primary user entrypoint**: `/analyze-results`
- **Phase 1 skill**: `results-analysis`
- **Phase 2 skill**: `results-report`

