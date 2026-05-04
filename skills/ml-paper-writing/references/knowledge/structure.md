# Paper Structure Patterns

This file contains actionable patterns for organizing ML conference papers, extracted from successful publications.

---

## Introduction Patterns

### Pattern: Contribution Statement Structure
**Source:** "Attention Is All You Need", NeurIPS (2017)
**Context:** Introducing the main contribution

**Pattern:**
1. Start with broader context or problem
2. Narrow down to specific limitation
3. Present your approach as solution
4. State clear contribution upfront

**Example Template:**
```markdown
[Context/Problem]: Existing approaches struggle with [limitation] due to [reason].

[Our Approach]: We propose [method name], which [key innovation].

[Contribution]: This achieves [result] and enables [capability].
```

**Application:** Use this pattern when introducing your main contribution in the first or second paragraph of the introduction.

---

### Pattern: Bulleted Contribution List
**Source:** "BERT: Pre-training of Deep Bidirectional Transformers", NAACL (2019)
**Context:** Summarizing contributions for clarity

**Pattern:**
- Place near end of Introduction (after Related Work)
- Use 2-4 bullets
- Each bullet: 1-2 lines max (in two-column format)
- Start with strong verbs ("We propose", "We demonstrate", "We show")

**Example Template:**
```markdown
Our contributions are three-fold:
- We propose [method], which achieves [result].
- We demonstrate that [technique] improves [metric].
- We show that [approach] enables [new capability].
```

**Application:** Use this when you need to clearly delineate multiple contributions for reviewers.

---

### Pattern: Related Work Organization
**Source:** "Attention Is All You Need", NeurIPS (2017)
**Context:** Structuring literature review

**Pattern:**
- Organize methodologically, not chronologically
- Group papers by approach/assumption
- Contrast your approach with each group
- Use "One line of work uses X whereas we use Y because..."

**Example Template:**
```markdown
[Approach Category]: Several approaches use [assumption A] [refs].
[Contrast]: We adopt [assumption B] because it allows [benefit].

[Alternative Category]: Other methods focus on [aspect C] [refs].
[Positioning]: We build on this by adding [our innovation].
```

**Application:** Use this to position your work relative to existing literature without paper-by-paper reviews.

---

## Methods Section Patterns

### Pattern: Algorithm Presentation
**Source:** "Adam: A Method for Stochastic Optimization", ICLR (2015)
**Context:** Describing algorithms clearly

**Pattern:**
1. High-level overview first
2. Mathematical formulation
3. Algorithm pseudocode (if complex)
4. Implementation details

**Example Template:**
```markdown
[Overview]: We formulate [problem] as optimization. Let [objective] be our goal.

[Method]: Our approach optimizes [objective] using [technique].
Specifically, we [algorithm description].

[Algorithm]: The full procedure is shown in Algorithm 1.

[Implementation]: In practice, we [practical details].
```

**Application:** Use this when presenting novel algorithms or optimization methods.

---

### Pattern: Component Breakdown
**Source:** "BERT: Pre-training of Deep Bidirectional Transformers", NAACL (2019)
**Context:** Describing multi-component systems

**Pattern:**
- Present model architecture first
- Break down into key components
- Explain each component's role
- Show how components interact

**Example Template:**
```markdown
[Architecture]: Our model consists of [N components]: [list].

[Component 1]: The [component] module [function].
[Component 2]: The [component] layer [operation].

[Integration]: These components are stacked sequentially, with [connection pattern].
```

**Application:** Use this when describing complex architectures with multiple interacting parts.

---

## Results Section Patterns

### Pattern: Quantitative Opening
**Source:** "BERT: Pre-training of Deep Bidirectional Transformers", NAACL (2019)
**Context:** Presenting main findings

**Pattern:**
- Start with strongest quantitative result
- Use exact numbers and metrics
- Include comparison to baselines
- State statistical significance

**Example Template:**
```markdown
[Main Result]: Our method achieves [score] on [dataset], improving
over the previous best of [baseline] by [margin] (p<0.001).

[Comparison]: Compared to baselines:
- [Method A]: [score]
- [Method B]: [score]
- Ours: [score]

[Significance]: Results are averaged over N runs; standard deviations shown in parentheses.
```

**Application:** Use this to open your Results section with your strongest finding.

---

### Pattern: Table Integration
**Source:** "Attention Is All All You Need", NeurIPS (2017)
**Context:** Presenting results in tables

**Pattern:**
- Bold best results in each column
- Include direction indicators (↑↓)
- Provide table caption that stands alone
- Reference table in text before presenting

**Example Template:**
```markdown
Table 1 shows our method's performance. Our model (bold) outperforms
all baselines across datasets.

[Table content]

As shown in Table 1, we achieve state-of-the-art on [datasets].
```

**Application:** Use this when presenting comparative results in table format.

---

## Discussion Section Patterns

### Pattern: Limitations First
**Source:** "Attention Is All You Need", NeurIPS (2017)
**Context:** Acknowledging limitations proactively

**Pattern:**
- State limitations clearly in first paragraph
- Explain why limitations don't undermine core claims
- Distinguish between limitations and future work

**Example Template:**
```markdown
[Limitation Statement]: Our approach has [limitation]. Specifically,
[constraint].

[Mitigation]: Despite this, our core findings about [main contribution] remain
valid because [reason].

[Future Work]: Addressing this limitation is an important direction for
future research.
```

**Application:** Use this to acknowledge limitations honestly while maintaining paper strength.

---

### Pattern: Broader Impact Framing
**Source:** "Language Models are Few-Shot Learners", GPT-3 Paper (2020)
**Context:** Discussing wider implications

**Pattern:**
- Start with direct implications
- Expand to related domains
- Consider societal impact (if appropriate)
- End with forward-looking statement

**Example Template:**
```markdown
[Direct Impact]: Our findings suggest that [implication for domain].

[Broader Implications]: Beyond [specific domain], this approach could
enable [application in other areas].

[Future Outlook]: As [trend] continues, methods like ours will become
increasingly important for [reason].
```

**Application:** Use this when writing the final paragraphs of Discussion or Conclusion.

---

## Transition Patterns

### Pattern: Section Transitions
**Source:** "Attention Is All You Need", NeurIPS (2017)
**Context:** Moving between sections

**Pattern:**
- Introduction → Methods: "We now describe our approach."
- Methods → Results: "We evaluate our method on [tasks]."
- Results → Discussion: "These results suggest that [insight]."

**Example Template:**
```markdown
[Transition to Methods]: Having established [motivation], we present
our method.

[Transition to Results]: To validate our approach, we conduct experiments
on [datasets].

[Transition to Discussion]: The experimental results reveal several insights
about [phenomenon], which we discuss next.
```

**Application:** Use these to create smooth transitions between major sections.

---

## Notes

- **Consistency**: Maintain consistent terminology throughout the paper
- **Flow**: Each section should logically lead to the next
- **Clarity**: Make structure explicit with signposting
- **Audience**: Write for tired reviewers - make their job easy

```
We introduce [method name], a [key feature] framework for [task].
We show that [method] achieves [result] on [dataset].
```

```
[Problem] is difficult for [task]. We present [solution]
that addresses this by [key mechanism].
```

```
Deeper neural networks are more difficult to train. We present a
residual learning framework to ease the training of networks that
are substantially deeper than those used previously.
```

```markdown
```

- "This represents a [X]% improvement over baseline"
