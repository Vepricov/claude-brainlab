# Review Response Strategy Library

This document provides systematic response strategies for different types of review comments, helping write professional and effective rebuttals.

## Four Core Strategies

### 1. Accept

**Applicable scenarios**:
- The reviewer correctly identified a problem or deficiency
- The revision cost is low and can improve paper quality
- Typos and formatting issues
- Reasonable improvement suggestions

**Response template**:
```
We thank the reviewer for this valuable suggestion. We have [specific revision action].
```

**Example**:

**Review comment**:
> "The related work section is too brief and misses several important recent papers."

**Response**:
> "We thank the reviewer for pointing this out. We have significantly expanded the related work section and added discussions of the suggested papers [X, Y, Z]. The revised section now provides a more comprehensive overview of the field."

---

### 2. Defend

**Applicable scenarios**:
- There is sufficient justification for the current approach
- The reviewer's suggestion does not apply to this research
- Need to explain the rationale behind design choices

**Key principles**:
- Maintain politeness and respect
- Provide sufficient reasons and evidence
- Avoid phrasing like "The reviewer is wrong"

**Response template**:
```
We appreciate the reviewer's concern. However, we respectfully note that [our approach] is motivated by [reason]. This choice is motivated by [specific rationale].
```

**Example**:

**Review comment**:
> "The authors should use method X instead of method Y."

**Response**:
> "We appreciate the reviewer's suggestion. However, we respectfully note that method Y is more suitable for our specific setting because [reason 1] and [reason 2]. While method X has advantages in [scenario A], our preliminary experiments showed that method Y achieves better performance in our task due to [specific reason]. We have added this discussion to Section 3.2."

---

### 3. Clarify

**Applicable scenarios**:
- The reviewer misunderstood the paper content
- The paper already contains the relevant content but the reviewer missed it
- Need to point to existing explanations or experiments in the paper

**Key principles**:
- Politely point to existing content in the paper
- Provide specific location references (section, page, figure, table)
- Avoid making the reviewer feel embarrassed
- Consider improving the wording to make it clearer

**Response template**:
```
We thank the reviewer for raising this point. We would like to respectfully clarify that [existing content]. This is discussed in [specific location]. To make this clearer, we have [improvements].
```

**Example**:

**Review comment**:
> "The authors did not compare their method with baseline X."

**Response**:
> "We thank the reviewer for this comment. We would like to respectfully clarify that we did include comparisons with baseline X in our experiments. These results are presented in Table 2 (page 6) and discussed in Section 4.2. To make this comparison more prominent, we have added a dedicated paragraph highlighting the key differences and added baseline X to Figure 3 for visual comparison."

**Notes**:
- Even if the reviewer misunderstood, maintain politeness and respect
- If possible, acknowledge that the paper's wording could be clearer, and make improvements
- Provide specific citation locations to make it easy for the reviewer to find

---

### 4. Experiment

**Applicable scenarios**:
- Reviewer requests key additional experiments or comparisons
- The experimental request is reasonable and feasible
- Additional experiments can significantly strengthen the paper's persuasiveness
- Experimental requests in Major Issues

**Key principles**:
- Clearly commit to conducting additional experiments
- Explain the experimental design and expected timeline
- If already completed, present results directly
- If time is tight, state preliminary results or plan

**Response template**:
```
We thank the reviewer for this valuable suggestion. We agree that [importance of experiment]. We have conducted additional experiments on [experiment content]. The results show that [main findings]. These new results have been added to [location].
```

**Example 1 (completed experiments)**:

**Review comment**:
> "The authors should compare their method with the recent state-of-the-art method Z."

**Response**:
> "We thank the reviewer for this excellent suggestion. We agree that comparing with method Z is important for a comprehensive evaluation. We have conducted additional experiments comparing our method with Z on all three datasets. The results show that our method achieves comparable or better performance (Dataset A: +2.3%, Dataset B: +1.1%, Dataset C: -0.5%). These new results have been added to Table 3 and discussed in Section 4.3. We also provide detailed analysis of the performance differences in the revised manuscript."

**Example 2 (committing to experiments)**:

**Review comment**:
> "The authors should conduct ablation studies to verify the contribution of each component."

**Response**:
> "We thank the reviewer for this important suggestion. We agree that ablation studies are crucial for understanding the contribution of each component. We are currently conducting comprehensive ablation experiments and will include the results in the revised manuscript. Based on our preliminary analysis, we expect to show that [expected findings]. We will complete these experiments within the rebuttal period and update the manuscript accordingly."

**Notes**:
- Only commit to feasible experiments; don't over-commit
- If an experiment is not feasible, explain why (time, resource, technical constraints)
- Provide a timeline so the reviewer knows the progress
- If already completed, present results immediately to strengthen persuasiveness

---

## Success Patterns (Based on ICLR Spotlight Papers)

Key patterns extracted from successful ICLR 2024 spotlight paper rebuttals:

### Pattern 1: Acknowledge Strengths, Address Criticism Directly

**Observation**:
- Reviewers typically acknowledge a paper's strengths first (novelty, impact, practical applicability)
- Even spotlight papers receive constructive criticism
- About 20% of papers see score changes after rebuttal

**Application strategy**:
```
We thank the reviewer for recognizing [acknowledged strength]. Regarding [concern], we have [specific action taken].
```

**Example**:
> "We thank the reviewer for recognizing the novelty of our game-theoretic formulation. Regarding the brevity of Section 2.2, we have expanded it with 2-3 additional paragraphs providing more intuition for readers without a game theory background."

---

### Pattern 2: Provide Clarity and Intuitive Understanding

**Observation**:
- High-quality papers can still have clarity issues
- Reviewers need to provide intuition for readers from different backgrounds
- Suggestion: expand sections, move technical details to appendix

**Application strategy**:
```
We apologize for the confusion. We have [clarification action]. To make this clearer, we have [additional improvements].
```

**Example**:
> "We apologize for the confusion in Section 3.2. We have completely rewritten this section with detailed mathematical formulation and added Algorithm 1 with pseudocode. We have also moved some technical details to Appendix B to improve readability."

---

### Pattern 3: Thoroughly Justify Experimental Setup

**Observation**:
- Reviewers expect the experimental setup to be well-justified
- Need to consider and discuss alternative metrics
- Comprehensive experiments are a common feature of spotlight papers

**Application strategy**:
```
We chose [experimental setup] because [justification]. We have also considered [alternative approach], but [reason for current choice]. We have added [additional experiments] to strengthen our evaluation.
```

**Example**:
> "We chose dataset W because it better represents our target scenario [justification]. We have also considered dataset Z, but it focuses on static graphs while our work targets dynamic graphs. We have added ablation studies showing that our improvement comes from fundamental architectural innovations."

---

### Pattern 4: Proactively Discuss Ethical Considerations

**Observation**:
- For research involving privacy, security, and other sensitive topics, ethical considerations are crucial
- Reviewers pay special attention to ethical implications
- Spotlight papers typically have thorough ethical discussions

**Application strategy**:
```
We appreciate the concern about ethical implications. We have [ethical consideration actions]. We have also added [ethical safeguards/discussions].
```

**Example**:
> "We appreciate the concern about privacy implications. We have added a comprehensive ethics section discussing potential risks and mitigation strategies. We have also included anonymization experiments and detailed our data handling procedures in Appendix C."

---

### Pattern 5: Emphasize Practical Application Value

**Observation**:
- Reviewers value practical applicability and scalability
- "Easily applicable" and "scalable" are important advantages
- Spotlight papers typically demonstrate practical benefits

**Application strategy**:
```
Our method is [practical benefit]. It is easily applicable because [reason] and scales to [scale] without [limitation].
```

**Example**:
> "Our method is practical and easily applicable to large language models without extensive tuning. It scales efficiently to models with up to 540B parameters, as demonstrated by our experiments. The consistent performance improvements across different model sizes highlight its practical value."

---

## Combining Strategies

In actual rebuttals, multiple strategies are typically combined:

### Combination Example 1: Accept + Clarify

**Review comment**:
> "The paper lacks discussion of limitation X, and the authors did not mention related work Y."

**Response**:
> "We thank the reviewer for these valuable comments. Regarding limitation X, we agree this is an important point and have added a dedicated discussion in Section 5.3 (**Accept**). Regarding related work Y, we would like to respectfully clarify that we did discuss this work in Section 2.2 (page 3, paragraph 2). To make this more prominent, we have expanded the discussion and added it to the comparison table (**Clarify**)."

### Combination Example 2: Defend + Experiment

**Review comment**:
> "The authors should use dataset Z instead of dataset W, and should add experiments on task T."

**Response**:
> "We appreciate the reviewer's suggestions. Regarding dataset Z, we respectfully note that dataset W is more suitable for our research question because [reason]. Dataset Z focuses on [scenario A], while our work targets [scenario B] (**Defend**). However, we agree that experiments on task T would strengthen our evaluation. We have conducted additional experiments on task T, and the results show [findings]. These new results have been added to Section 4.4 (**Experiment**)."

---

## Usage Guide

### Strategy Selection Process

```
Review comment -> Classify (Major/Minor/Typo/Misunderstanding) -> Choose strategy
|
+- Major Issues -> Experiment (conduct additional experiments) or Defend (sufficient reasons)
+- Minor Issues -> Accept (accept improvements) or Clarify (provide clarification)
+- Typos/Formatting -> Accept (accept directly)
+- Misunderstandings -> Clarify (politely clarify)
```

### Strategy Priority

1. **Prioritize Accept**: If the comment is reasonable and revision cost is low
2. **Cautious Defend**: Only use when there are sufficient reasons
3. **Polite Clarify**: Even when the reviewer misunderstands, maintain respect
4. **Honest Experiment**: Only commit to feasible experiments

### Tone Principles

**Always maintain**:
- Thank the reviewer for their comments
- Respectful and polite attitude
- Specific citations and evidence
- Constructive responses

**Avoid**:
- "The reviewer is wrong"
- "This is obvious"
- Defensive or aggressive tone
- Vague or evasive answers

---

## Conference-Specific Strategies

Different top conferences have different emphases for rebuttals; understanding these differences helps you respond more effectively.

### NeurIPS

**Conference characteristics**:
- Emphasizes conceptual novelty and theoretical contribution
- Values broader impact and social implications
- Requires reproducibility checklist

**Rebuttal focus**:
1. **Highlight conceptual innovation** - Emphasize the conceptual novelty of your method
2. **Demonstrate broader impact** - Explain the societal significance and potential impact of the research
3. **Ensure reproducibility** - Commit to open-sourcing code and data

**Example opening**:
```markdown
We thank the reviewers for their constructive feedback. Our key contributions advance the field by [conceptual innovation]. We have strengthened the paper with [new experiments] and clarified [methodology]. All code and data will be released upon acceptance to ensure reproducibility.
```

**Response strategy**:
- When reviewers question novelty, emphasize conceptual breakthrough rather than just performance improvement
- Proactively discuss broader impact, even if reviewers don't explicitly require it
- Provide detailed experimental setup and hyperparameters to ensure reproducibility

---

### ICML

**Conference characteristics**:
- Emphasizes methodological rigor and theoretical foundation
- Values mathematical proofs and theoretical analysis
- Requires broader impact statement

**Rebuttal focus**:
1. **Demonstrate theoretical rigor** - Provide mathematical proofs and theoretical analysis
2. **Emphasize methodological contributions** - Explain the theoretical advantages of the method
3. **Add theoretical analysis** - Include theorems, lemmas, or theoretical guarantees

**Example opening**:
```markdown
We appreciate the reviewers' thorough evaluation. We have added theoretical analysis (Theorem 2, Appendix C) proving [property]. Our method's soundness is further validated by [experiments]. We have also expanded the broader impact statement to address [concern].
```

**Response strategy**:
- When reviewers question the method, provide theoretical proofs rather than just experimental results
- Emphasize the theoretical complexity and convergence guarantees of the algorithm
- Connect experimental results with theoretical predictions

---

### ICLR

**Conference characteristics**:
- Emphasizes experimental thoroughness and comprehensive evaluation
- Values honest discussion of limitations
- Requires LLM usage disclosure (if applicable)

**Rebuttal focus**:
1. **Add experiments** - Conduct the comparative experiments and ablation studies requested by reviewers
2. **Expand limitations discussion** - Honestly acknowledge the method's limitations
3. **Disclose LLM usage** - If LLMs were used, explicitly state how

**Example opening**:
```markdown
We thank the reviewers for their detailed comments. We have conducted additional experiments (Tables 4-6) addressing all concerns. We have also expanded the Limitations section (Section 5.2) and added LLM usage disclosure (Appendix D). These revisions significantly strengthen the empirical validation.
```

**Response strategy**:
- When reviewers request more experiments, prioritize adding them over defending
- Proactively expand the limitations discussion to demonstrate clear understanding of the method's boundaries
- If LLMs were used for writing assistance or experiments, disclose honestly and specify the exact use

**ICLR 2026-specific strategies**:

**1. Evidence-backed clarifications are most effective**
- Research shows clarifications supported by evidence correlate most strongly with score increases
- Avoid vague or evasive responses, which maintain or decrease scores
- Explicitly cite specific sections or line numbers from the original paper

**Example**:
```markdown
Thank you for this concern. We respectfully clarify that we did include this comparison in Section 4.2 (page 6, lines 234-245). To make this more prominent, we have added a dedicated paragraph and included the baseline in Figure 3 for visual comparison.
```

**2. Strategy for borderline papers**
- Rebuttal has the most impact on borderline papers (score range 5-6)
- If the paper is borderline, even small improvements may affect the final decision
- Focus on aspects that can be quickly improved

**3. Submission timing strategy**
- Submitting mid-way through the rebuttal period may be more effective
- Avoid submitting too early or at the last minute
- Mid-period submission can increase reviewer engagement and score changes

**4. Systematic response structure**
Each response should follow a three-step structure:
1. **Summarize the reviewer's concern** - Show that you understood their feedback
2. **State your response** - Clearly articulate your position
3. **Provide concrete evidence** - Give experiments, explanations, or revision plans

**Example**:
```markdown
**Reviewer's Concern**: The baseline comparison is insufficient.

**Our Response**: We appreciate this feedback. We understand the reviewer's concern about baseline coverage.

**Evidence**: We have added comparisons with three additional baselines (X, Y, Z) in Table 4 (Appendix). Results show our method achieves +2.3% improvement over the strongest baseline Z. We will integrate this into the main paper.
```

**5. Leveraging page limit extensions**
- ICLR 2026 expands camera-ready from 9 pages to 10 pages
- Use the extra page to integrate new results or discussions from the rebuttal
- Commit in the rebuttal to adding new content to the final version

**6. Reproducibility statement**
- Strongly recommended to include a reproducibility statement at the end of the main text (before references)
- Discuss efforts made to ensure reproducibility
- Cite relevant sections in the paper, appendix, or supplementary material

**7. ICLR 2026 scoring system**
- Uses discrete scores: {0, 2, 4, 6, 8, 10}
- 0=Strong Reject, 2=Reject, 4=Weak Reject, 6=Weak Accept, 8=Accept, 10=Strong Accept
- Understanding the scoring system helps judge which range the paper is in

---

### CVPR

**Conference characteristics**:
- Top computer vision conference, highly competitive
- Strict one-page rebuttal limit
- External links and large-scale new experiments prohibited
- Values visual quality and experimental completeness

**Rebuttal focus**:
1. **Identify "Champion" reviewers** - Find reviewers who support your paper and provide strong arguments for them
2. **Reiterate core contributions** - Subtly remind reviewers of the paper's important contributions when addressing criticism
3. **Demonstrate responsiveness** - Clearly state how you will incorporate suggestions in the final version

**Example opening**:
```markdown
We thank all reviewers for their valuable feedback. We are particularly grateful to R2 for recognizing our novel approach to [X]. Regarding the concerns raised, we provide clarifications below and will incorporate all valid suggestions in the camera-ready version.
```

**Response strategy**:
- Identify reviewers with positive attitudes and provide them arguments to defend in discussion
- While addressing issues, subtly reinforce the core advantages of the paper
- Provide clear, persuasive clarifications for misunderstandings of key concepts
- Demonstrate serious consideration of reviewer suggestions with a list of specific improvement plans

**Special restrictions**:
- Must use the official template with strict one-page limit
- No external links (code, video, supplementary materials)
- Can include tables and comparison charts based on existing results
- Reviewers should not request large-scale new experiments

---

### ACL

**Conference characteristics**:
- Top natural language processing conference
- Best paper standards: fascinating, controversial, surprising, impressive, field-changing
- Values linguistic significance and practical application of methods
- Requires Limitations and Ethics Statement

**Rebuttal focus**:
1. **Small table strategy** - If reviewers request additional results, include a small table in the rebuttal
2. **Enhance understanding** - Goal is to enhance reviewers' understanding of the paper, not a large-scale rewrite
3. **Highlight impact** - Emphasize potential impact of research on the NLP field

**Example opening**:
```markdown
We thank the reviewers for their insightful comments. We have prepared additional analysis to address the raised concerns. Below we provide clarifications and include a small table (Table R1) demonstrating the requested comparison. These results will be integrated into the revised manuscript.
```

**Response strategy**:
- If reviewers request additional data, include a small table in the rebuttal to demonstrate
- Emphasize the linguistic significance and contribution to the NLP community
- Proactively discuss ethical implications, especially for research involving bias and fairness
- Demonstrate consideration for different language and cultural backgrounds

**Best Paper considerations**:
- Is the paper "fascinating" - Does it pose exciting new questions or perspectives?
- Is it "controversial" - Does it challenge existing assumptions?
- Is it "surprising" - Are there counter-intuitive but persuasive findings?
- Is it "impressive" - Technical depth or experimental scale?
- Is it "field-changing" - Potential long-term impact?

---

## Reference Resources

For more detailed successful cases and templates, see:
- `successful-cases.md` - Real successful rebuttal case library
- `rebuttal-templates.md` - Complete rebuttal templates
- `tone-guidelines.md` - Tone and expression guidelines
