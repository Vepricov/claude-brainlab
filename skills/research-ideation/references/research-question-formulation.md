# Research Question Formulation

A systematic approach to transforming research interests into concrete, actionable research questions.

## 1. SMART Principles

Good research questions should satisfy the SMART principles:

### 1.1 Specific

**Poorly formulated question**:
- "How can we improve model performance?" (too broad)

**Well formulated question**:
- "How can we improve Transformer performance on long-document understanding tasks by improving the attention mechanism?"

**Key elements**:
- Clear research subject (Transformer)
- Specific improvement direction (attention mechanism)
- Clear task scenario (long-document understanding)
- Defined goal (improve performance)

### 1.2 Measurable

Research questions should have clear evaluation criteria:

**Examples**:
- "improve performance" → "improve F1 score on the SQuAD dataset"
- "improve interpretability" → "improve faithfulness score on human evaluation"

**Evaluation dimensions**:
- Quantitative metrics: accuracy, F1, BLEU, perplexity
- Qualitative metrics: human evaluation, case analysis
- Efficiency metrics: training time, inference speed, memory usage

### 1.3 Achievable

Consider resource and capability constraints:

**Resource assessment**:
- Computational resources: Number and type of GPUs
- Data resources: Availability and quality of datasets
- Time resources: Research cycle (3 months, 6 months, 1 year)
- Human resources: Team size and expertise

**Feasibility check**:
- Is there similar work to build on?
- Is the required technology already mature?
- Is the dataset publicly available?
- Is the computational cost within budget?

### 1.4 Relevant

Research questions should have value to academia or industry:

**Academic value**:
- Fills research gaps
- Challenges existing assumptions
- Provides new theoretical perspectives
- Advances methodological progress

**Practical value**:
- Solves real application problems
- Improves system performance
- Reduces cost or resource consumption
- Improves user experience

### 1.5 Time-bound

Set a reasonable research time frame:

**Short-term goals** (1-3 months):
- Literature review and problem definition
- Preliminary experiments and proof of concept

**Medium-term goals** (3-6 months):
- Method development and optimization
- Comprehensive experiments and analysis

**Long-term goals** (6-12 months):
- Paper writing and submission
- Code open-sourcing and community promotion

## 2. Research Question Types

### 2.1 Exploratory Questions

**Characteristics**: Explore unknown territory, discover new phenomena

**Examples**:
- "What patterns does the Transformer attention mechanism exhibit when processing long text?"
- "What internal representations do large language models use in reasoning tasks?"

**Applicable scenarios**:
- Emerging research fields
- Phenomena lacking a theoretical foundation
- Complex systems requiring deep understanding

### 2.2 Confirmatory Questions

**Characteristics**: Verify hypotheses or theories

**Examples**:
- "Does increasing model depth improve long-document understanding performance?"
- "Does pre-training help with low-resource language tasks?"

**Applicable scenarios**:
- Clear hypothesis that needs verification
- Challenging existing theory or viewpoint
- Reproducing and extending existing work

### 2.3 Applied Questions

**Characteristics**: Solve real application problems

**Examples**:
- "How can we reduce model size by 50% while maintaining performance?"
- "How can we make a dialogue system better understand user intent?"

**Applicable scenarios**:
- Clear application requirements
- Need to optimize under constraints
- Industrial collaboration projects

## 3. Research Question Evaluation Criteria

### 3.1 Significance

**Evaluation dimensions**:
- **Academic impact**: Does it advance the field?
- **Practical value**: Does it solve important problems?
- **Audience size**: How many people care about this problem?

**Scoring criteria** (1-5):
- 5: Breakthrough problem affecting the entire field
- 4: Important problem, multiple research groups interested
- 3: Valuable problem, some researchers interested
- 2: Marginal problem, few interested
- 1: Trivial problem, almost no one interested

### 3.2 Novelty

**Evaluation dimensions**:
- **Problem novelty**: Is this a new problem?
- **Method novelty**: Is there a new method?
- **Perspective novelty**: Is there a new perspective?

**Scoring criteria** (1-5):
- 5: Entirely new problem or breakthrough method
- 4: New problem or significantly improved method
- 3: New perspective or method combination
- 2: Incremental improvement
- 1: Repeating existing work

### 3.3 Feasibility

**Evaluation dimensions**:
- **Technical feasibility**: Can existing technology achieve it?
- **Resource feasibility**: Are resources sufficient?
- **Time feasibility**: Is the timeline reasonable?

**Scoring criteria** (1-5):
- 5: Fully feasible, sufficient resources
- 4: Basically feasible, resources adequate
- 3: Has challenges, requires effort
- 2: Significant difficulties, needs breakthrough
- 1: Nearly infeasible

### 3.4 Overall Evaluation

**Decision matrix**:

| Significance | Novelty | Feasibility | Recommendation |
|--------|--------|--------|------|
| High | High | High | Prioritize |
| High | High | Medium | Worth attempting |
| High | Medium | High | Safe choice |
| Medium | High | High | Consider |
| Low | * | * | Reconsider |
