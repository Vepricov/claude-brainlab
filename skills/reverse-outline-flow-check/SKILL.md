---
name: reverse-outline-flow-check
description: Diagnose and rewrite section flow using reverse outlining, one-paragraph-one-message structure, and explicit sentence-to-sentence relations. Use when a paper section feels unclear, disconnected, or hard to follow even though the content is roughly correct.
argument-hint: [section-or-draft]
---

# Reverse Outline Flow Check

Use this skill when the main problem is local writing flow rather than missing experiments or missing citations.

## When to Use

- A user asks whether a section "flows" or "makes sense"
- Paragraphs feel individually acceptable but weak as a sequence
- Topic sentences, evidence, and thesis claims do not align cleanly
- The draft reads like accumulated edits instead of a coherent argument

## Workflow

### Step 1: Read as an External Reader
- Ignore what the author intended and focus on what the text actually communicates.
- For each paragraph, identify the one message a reader would take away.
- If a paragraph appears to carry multiple messages, mark it for splitting or rewriting.

### Step 2: Build the Reverse Outline
- Write down the section thesis or local goal.
- List the topic sentence of each paragraph.
- Under each paragraph, list the evidence, explanation, or example it actually contains.
- Check whether `section goal -> paragraph topic sentence -> supporting content` forms a clean chain.

See `references/reverse-outline-template.md` for the minimal template.

### Step 3: Audit Sentence-Level Flow
- Check whether each sentence relates to the previous one through cause, contrast, consequence, refinement, or example.
- Add explicit transitions only where the relation is unclear; do not pad with generic connectors.
- Rewrite the first sentence of each paragraph so it states the paragraph's role clearly.

See `references/paragraph-relations.md` for the allowed relation types.

### Step 4: Repair the Section
- Remove or merge paragraphs that cannot be mapped back to the section goal.
- Split paragraphs that contain more than one core message.
- If needed, add temporary subsection headers during revision, then remove them if the final flow is clear without them.

### Step 5: Return a Structured Rewrite
Return:

1. A compact reverse outline
2. A paragraph-by-paragraph rewrite plan
3. Revised prose or topic-sentence rewrites
4. Remaining flow risks that still need author judgment

## Rules

- One paragraph should carry one message.
- The first sentence should make the paragraph role obvious.
- Keep explicit transitions only when they clarify a real logical relation.
- Delete or rewrite paragraphs that cannot be justified in the reverse outline.

## References

- `references/reverse-outline-template.md`: minimal reverse-outline structure
- `references/paragraph-relations.md`: sentence and paragraph relation types

## Related Skills

- Upstream: [ml-paper-writing](../ml-paper-writing/), [paper-writing-section](https://github.com/Research-Equality/RE-paper-writing/tree/4aa7e40c5e1b9780fbc5d1519df63eb3ba37ff4f/skills/paper-writing-section)
- Downstream: [long-form-manuscript-polish](https://github.com/Research-Equality/RE-paper-writing/tree/4aa7e40c5e1b9780fbc5d1519df63eb3ba37ff4f/skills/long-form-manuscript-polish), [paper-revision](https://github.com/Research-Equality/RE-paper-writing/tree/4aa7e40c5e1b9780fbc5d1519df63eb3ba37ff4f/skills/paper-revision)
- See also: [claim-evidence-map](https://github.com/Research-Equality/RE-paper-writing/tree/4aa7e40c5e1b9780fbc5d1519df63eb3ba37ff4f/skills/claim-evidence-map), [self-review](https://github.com/Research-Equality/RE-paper-writing/tree/4aa7e40c5e1b9780fbc5d1519df63eb3ba37ff4f/skills/self-review)
