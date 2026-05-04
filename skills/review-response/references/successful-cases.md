# Successful Rebuttal Case Library

This document collects real successful rebuttal cases to provide practical patterns for reference.

## Case Sources

- ICLR 2024 Spotlight papers
- NeurIPS 2023 accepted papers
- ICML 2023 accepted papers

---

## Case 1: Responding to Clarity Issues

### Review Comment
> "The algorithm description in Section 3.2 is unclear. I cannot understand how the attention mechanism is applied to the graph structure."

### Successful Response
```markdown
We apologize for the confusion. We have completely rewritten Section 3.2 to clarify the attention mechanism:

**Original text** (unclear):
"We apply attention to nodes based on their features."

**Revised text** (clear):
"For each node v, we compute attention weights α_ij for all neighbors j ∈ N(v) using:
α_ij = softmax(LeakyReLU(a^T [W h_i || W h_j]))
where W is a learnable weight matrix and a is an attention vector."

We also added:
- Algorithm 1 with detailed pseudocode (page 5)
- Figure 3 showing a concrete example with 4 nodes (page 6)
- Appendix B with step-by-step walkthrough

These additions make the mechanism explicit and reproducible.
```

### Success Factors
- Acknowledge the problem
- Compare original and revised text
- Provide multiple forms of explanation (formula, algorithm, figure, example)
- State specific locations

---

## Case 2: Responding to Missing Experiments

### Review Comment
> "The paper lacks comparison with the recent state-of-the-art method GraphTransformer (Dwivedi et al., 2022). This comparison is essential for evaluating the proposed method."

### Successful Response
```markdown
We thank the reviewer for this excellent suggestion. We have added comprehensive comparisons with GraphTransformer on all three datasets:

**New Results** (Table 3, page 7):
- ZINC: Our method 0.087 ± 0.004 vs GraphTransformer 0.094 ± 0.006 (8% improvement)
- MNIST: Our method 97.3% ± 0.2% vs GraphTransformer 96.5% ± 0.3% (0.8% improvement)
- PROTEINS: Our method 76.2% ± 1.1% vs GraphTransformer 75.1% ± 1.3% (1.1% improvement)

**Analysis** (Section 4.3, pages 7-8):
We also added ablation studies showing that our improvement comes from:
1. The simplicial-aware features (contributes 60% of improvement)
2. The efficient aggregation scheme (contributes 40% of improvement)

This demonstrates that our method's advantage is not just from better optimization, but from fundamental architectural improvements.
```

### Success Factors
- Thank the reviewer for the suggestion
- Provide specific numerical results
- State result locations
- Add analysis explaining the source of improvements
- Emphasize the fundamental advantages of the method

---

## Case 3: Responding to Statistical Significance Questions

### Review Comment
> "The improvements shown in Table 2 are marginal (0.5-1%). Are these differences statistically significant?"

### Successful Response
```markdown
We agree that statistical testing is important. We have added comprehensive statistical analysis:

**Statistical Tests** (Table 2, updated):
- All comparisons now include 95% confidence intervals
- Paired t-tests show p < 0.01 for all improvements
- Results averaged over 10 runs (increased from 3)

**Practical Significance** (Section 4.2, page 7):
While the improvements are 0.5-1%, we note that:
1. In this domain, even 0.5% improvement is considered significant (see [Citation])
2. Our method achieves this with 3x faster training time
3. The improvement is consistent across all 5 datasets

**Updated Table 2**:
| Method | Accuracy | 95% CI | p-value |
|--------|----------|--------|---------|
| Baseline | 85.2% | [84.8, 85.6] | - |
| Ours | 86.1% | [85.7, 86.5] | <0.01 |

We believe both statistical and practical significance support our claims.
```

### Success Factors
- Acknowledge the importance of statistical testing
- Provide multiple statistical metrics
- Distinguish statistical significance from practical significance
- Provide domain context for support
- Update table to show complete information

---

## Case 4: Responding to Insufficient Baselines

### Review Comment
> "Why didn't you compare with Method X and Method Y? These are important baselines in this area."

### Successful Response
```markdown
We thank the reviewer for raising this point. We have:

**Added Method X** (Table 3, page 7):
- Method X: 82.3% ± 1.2%
- Ours: 86.1% ± 0.8% (3.8% improvement)

**Excluded Method Y** with justification:
Method Y is designed for static graphs, while our work focuses on dynamic graphs. As noted in [Method Y paper, Section 5], "our method is not applicable to temporal settings." Direct comparison would be inappropriate because:
1. Method Y requires graph structure to be fixed
2. Our datasets have time-varying edges
3. Adapting Method Y would require substantial modifications that deviate from the original method

We have added this clarification to Section 4.1 (page 6).
```

### Success Factors
- Added the comparable baseline
- Explained exclusion reason (citing original paper)
- Provided specific technical reasons
- Stated where the change was made

---

## Case 5: Responding to Overclaiming

### Review Comment
> "The claim 'our method achieves state-of-the-art on all tasks' is too strong. Your method performs worse than Baseline X on Task 3."

### Successful Response
```markdown
We accept that our original claim was too strong. We have revised throughout the paper:

**Abstract** (page 1):
- Original: "achieves state-of-the-art on all tasks"
- Revised: "achieves state-of-the-art on 4 out of 5 tasks and competitive performance on the remaining task"

**Introduction** (page 2):
- Added: "While our method excels on tasks requiring [property], it performs comparably to baselines on Task 3, which emphasizes [different property]."

**Limitations Section** (new Section 5.2, page 9):
We added a dedicated limitations section acknowledging:
1. Our method's relative weakness on Task 3
2. Potential reasons (Task 3 requires [property] which our architecture doesn't explicitly model)
3. Future directions to address this

We believe these revisions accurately reflect our contributions without overclaiming.
```

### Success Factors
- Acknowledge the problem
- Show specific changes (original vs. revised text)
- Add limiting statements
- Provide technical explanation
- Maintain honesty and accuracy

---

## Case 6: Responding to Writing Quality Issues

### Review Comment
> "The paper is hard to follow. Section 3 jumps between concepts without clear transitions. There are also several grammatical errors."

### Successful Response
```markdown
We apologize for the writing issues. We have made substantial revisions:

**Section 3 Restructuring** (pages 4-6):
- Added subsection headings for clarity:
  - 3.1 Problem Formulation
  - 3.2 Model Architecture
  - 3.3 Training Procedure
- Added transition sentences between subsections
- Moved technical details to appendix

**Grammar and Style**:
- Professional editing service reviewed the entire manuscript
- Fixed all grammatical errors
- Improved technical terminology consistency
- Added a notation table (Appendix A)

**Improved Flow**:
- Added signposting: "In this section, we...", "Next, we describe..."
- Clarified pronoun references
- Shortened overly long sentences

The revised manuscript is significantly more readable while maintaining technical precision.
```

### Success Factors
- Acknowledge the problem
- Provide specific improvements
- Show structural improvements
- Mention professional editing
- Emphasize readability improvement

---

## Summary of Universal Success Patterns

### Pattern 1: Thank + Action + Evidence

```markdown
We thank the reviewer for [specific point].
We have [specific action taken].
[Evidence: results/figures/citations]
```

### Pattern 2: Acknowledge + Revise + Explain

```markdown
We agree that [issue].
We have revised [specific location]:
- Original: [old text]
- Revised: [new text]
This addresses the concern by [explanation].
```

### Pattern 3: Explain + Evidence + Citation

```markdown
We respectfully note that [our position].
This is supported by:
1. [Evidence 1]
2. [Evidence 2]
3. [Citation]
```

### Pattern 4: Add + Location + Impact

```markdown
We have added [new content].
Location: [Section X, Table Y, Figure Z]
This strengthens our claims by [impact].
```

---

## Conference-Specific Strategies

### NeurIPS Rebuttal

**Focus**:
- Emphasize conceptual novelty
- Highlight broader impact
- Demonstrate reproducibility

**Example opening**:
```markdown
We thank the reviewers for their constructive feedback. Our key contributions advance the field by [conceptual innovation]. We have strengthened the paper with [new experiments] and clarified [methodology]. All code and data will be released upon acceptance.
```

### ICML Rebuttal

**Focus**:
- Emphasize theoretical rigor
- Provide mathematical proofs
- Demonstrate methodological contributions

**Example opening**:
```markdown
We appreciate the reviewers' thorough evaluation. We have added theoretical analysis (Theorem 2, Appendix C) proving [property]. Our method's soundness is further validated by [experiments]. We have also expanded the broader impact statement.
```

### ICLR Rebuttal

**Focus**:
- Emphasize experimental thoroughness
- Acknowledge limitations
- Disclose LLM usage

**Example opening**:
```markdown
We thank the reviewers for their detailed comments. We have conducted additional experiments (Tables 4-6) addressing all concerns. We have also expanded the Limitations section and added LLM usage disclosure. These revisions significantly strengthen the empirical validation.
```

---

## Error Patterns to Avoid

### Error 1: Defensive Tone

**Bad response**:
> "The reviewer clearly misunderstood our method. If they had read Section 3 carefully, they would see that..."

**Good response**:
> "We apologize for the confusion. We have clarified Section 3 to make this point more explicit..."

### Error 2: Vague Promises

**Bad response**:
> "We will add more experiments in the final version."

**Good response**:
> "We have added experiments comparing with Method X on datasets A, B, C (Table 4, page 8)."

### Error 3: Ignoring the Issue

**Bad response**:
> "This is beyond the scope of our paper."

**Good response**:
> "While [suggestion] is valuable, it is beyond our current scope due to [specific constraint]. However, we have added [alternative] which addresses the core concern."

### Error 4: Overly Technical

**Bad response**:
> "Our method uses a novel attention mechanism with learnable parameters θ = {W_q, W_k, W_v, W_o} where..."

**Good response**:
> "We have clarified the attention mechanism in Section 3.2 with pseudocode (Algorithm 1) and a concrete example (Figure 3)."

---

## Usage Recommendations

1. **Select similar cases** - Find cases that match your review comments
2. **Adapt to your situation** - Don't copy directly; adjust based on actual circumstances
3. **Stay honest** - Only commit to what you can deliver
4. **Provide evidence** - Every claim needs support
5. **State locations** - Clearly indicate where changes were made

---

## Ongoing Updates

This document will be continuously updated with more successful cases. Contributions of good rebuttal examples are welcome.
