---
name: kaggle-learner
description: This skill should be used when the user asks to "learn from Kaggle", "study Kaggle solutions", "analyze Kaggle competitions", or mentions Kaggle competition URLs. Provides access to extracted knowledge from winning Kaggle solutions across NLP, CV, time series, tabular, and multimodal domains.
version: 0.1.0
---

# Kaggle Learner

Extract and apply knowledge from Kaggle competition winning solutions. This skill provides access to a continuously updated knowledge base of techniques, code patterns, and best practices from top Kaggle competitors.

## Overview

Kaggle competitions are at the forefront of practical machine learning. Winning solutions often innovate with novel techniques, clever feature engineering, and optimized pipelines. This skill captures that knowledge and makes it accessible for your projects.

## When to Use

Use this skill when:
- Studying for a Kaggle competition
- Looking for proven techniques in a specific domain (NLP, CV, etc.)
- Need code templates for common ML tasks
- Want to learn from competition winners

## Knowledge Categories

| Category | Focus | Directory |
|----------|-------|-----------|
| **NLP** | Text classification, NER, translation, LLM applications | `references/knowledge/nlp/` |
| **CV** | Image classification, detection, segmentation, generation | `references/knowledge/cv/` |
| **Time Series** | Forecasting, anomaly detection, sequence modeling | `references/knowledge/time-series/` |
| **Tabular** | Feature engineering, traditional ML, structured data | `references/knowledge/tabular/` |
| **Multimodal** | Cross-modal tasks, vision-language models | `references/knowledge/multimodal/` |

**File structure**: one markdown file per competition, organized by domain directory.

Examples:
- `time-series/birdclef-plus-2025.md`
- `nlp/aimo-2-2025.md`

## Quick Reference

**To learn from a competition:**
1. Provide the Kaggle competition URL
2. The kaggle-miner agent will extract the winning solution
3. Knowledge is automatically added to the relevant category
4. **Front-runner Detailed Technical Analysis** is automatically included

**To browse existing knowledge:**
- Browse the relevant domain directory: `references/knowledge/[domain]/`
- Each competition has one file containing:
  - Competition Brief
  - **Front-runner Detailed Technical Analysis** ⭐
  - Code Templates
  - Best Practices

## Self-Evolving

This skill automatically updates its knowledge base when the kaggle-miner agent processes new competitions. The more you use it, the smarter it becomes.

## Knowledge Extraction Standard

Every time knowledge is extracted from a Kaggle competition, **must** include the following standard sections:

### Required Content Checklist

| Section | Description | Required |
|---------|-------------|----------|
| **Competition Brief** | Background, task description, data scale, evaluation metric | ✅ Required |
| **Original Summaries** | Brief overview of top solutions | ✅ Required |
| **Front-runner Detailed Technical Analysis** | Core techniques and implementation details for top 20 solutions | ✅ **Required** ⭐ |
| **Code Templates** | Reusable code templates | ✅ Required |
| **Best Practices** | Best practices and common pitfalls | ✅ Required |
| **Metadata** | Data source tags and date | ✅ Required |

### Front-runner Detailed Technical Analysis Format

Each front-runner solution should include:
- **Rank and team/author**
- **Core techniques list** (3-6 key technical points)
- **Implementation details** (specific parameters, configs, data)

Example format:
```markdown
**Rank Place - Core Technique Name (Author)**

Core techniques:
- **Technique 1**: brief description
- **Technique 2**: brief description

Implementation details:
- Specific parameters, models, configs
- Data and experimental results
```

**Recommended to cover Top 20 solutions to capture more innovative techniques from top competitors**

## Additional Resources

### Knowledge Directories
- **`references/knowledge/nlp/`** - NLP competition techniques
- **`references/knowledge/cv/`** - Computer vision techniques
- **`references/knowledge/time-series/`** - Time series methods
- **`references/knowledge/tabular/`** - Tabular data approaches
- **`references/knowledge/multimodal/`** - Multimodal solutions

### Competition Examples
- **BirdCLEF+ 2025** (`time-series/birdclef-plus-2025.md`) - Complete Top 14 front-runner detailed technical analysis
- **BirdCLEF 2024** (`time-series/birdclef-2024.md`) - Top 3 solutions detailed technical analysis
- **AIMO-2** (`nlp/aimo-2-2025.md`) - Top 12+ front-runner technical summary
