---
name: writing-anti-ai
description: This skill should be used when the user asks to "remove AI writing patterns", "humanize this text", "make this sound more natural", "remove AI-generated traces", "fix robotic writing", or needs to eliminate AI writing patterns from prose. Based on Wikipedia's "Signs of AI writing" guide, detects and fixes inflated symbolism, promotional language, superficial -ing analyses, vague attributions, AI vocabulary, negative parallelisms, and excessive conjunctive phrases.
version: 1.0.0
author: gaoruizhang
license: MIT
tags: [Writing, AI, Anti-AI, Humanizer]
---

# Writing Anti-AI

Remove AI-generated writing patterns from text to make it sound natural and human-written.

## Overview

This skill identifies and eliminates predictable AI writing patterns from prose, based on [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), maintained by WikiProject AI Cleanup.

**Core insight**: LLMs use statistical algorithms to predict what should come next. The result tends toward the most statistically likely outcome that applies to the widest variety of cases—creating detectable patterns.

## When to Use This Skill

**Trigger phrases:**
- "Humanize this text"
- "Remove AI writing patterns"
- "Make this sound more natural"
- "This sounds robotic/AI-generated"
- "Fix the AI patterns"

**Use cases:**
- Editing AI-generated content to sound human
- Reviewing text for AI patterns before publication
- Polishing academic or professional writing
- Removing "slop" from prose

## Core Rules

### 0. Hard Bans for Academic Paper Text (LaTeX)
These three rules are absolute — no exceptions:

- **No em dashes**: Never use `---`, `--`, or `—` in any form. Replace with a comma, period, or rewrite the sentence.
- **No emphasis markup**: Never use `\emph{}`, `\textbf{}`, or `\textit{}` in new text. State the point directly without typographic emphasis.
- **No semicolons**: Never use `;` to join clauses. Split into two sentences with a period instead.

### 1. Cut Filler Phrases
Remove throat-clearing openers and emphasis crutches.

**Examples**:
- "In order to achieve this goal" → "To achieve this"
- "Due to the fact that" → "Because"
- "It is important to note that" → (delete)

### 2. Break Formulaic Structures
Avoid binary contrasts, dramatic fragmentation, rhetorical setups.

**Patterns to avoid**:
- Negative parallelisms: "It's not just X, it's Y"
- Rule of three: "A, B, and C" (prefer two or four items)
- Em-dash reveals: "X—Y" (just use commas — or better, rewrite)

### 3. Vary Rhythm
Mix sentence lengths. End paragraphs differently.

**Check**:
- Three consecutive sentences same length? Break one.
- Paragraph ends with punchy one-liner? Vary it.

### 4. Trust Readers
State facts directly. Skip softening, justification, hand-holding.

**Bad**: "It could potentially be argued that the policy might have some effect."
**Good**: "The policy may affect outcomes."

### 5. Cut Quotables
If it sounds like a pull-quote, rewrite it.

**Bad**: "This represents a major step in the right direction."
**Good**: "The company plans to open two more locations."

## Common AI Patterns

### Content Patterns

| Pattern | Description |
|---------|-------------|
| **Undue emphasis** | "stands as a testament", "crucial role" |
| **Promotional language** | "vibrant", "rich heritage", "breathtaking" |
| **Vague attributions** | "Experts believe", "Observers note" |
| **Superficial -ing analyses** | "highlighting the importance", "ensuring that" |
| **Formulaic "challenges" sections** | "Despite X, faces challenges" |

### Language Patterns

| Pattern | Description |
|---------|-------------|
| **AI vocabulary** | Additionally, crucial, delve, enhance, landscape |
| **Copula avoidance** | "serves as", "stands for", "represents" |
| **Em dash overuse** | Using — more than humans |
| **Rule of three** | Forcing ideas into groups of three |
| **Elegant variation** | Excessive synonym substitution |

For comprehensive pattern lists, see:
- **`references/patterns-english.md`** - Complete English pattern reference
- **`references/patterns-chinese.md`** - Complete Chinese pattern reference

## Personality and Soul

Avoiding AI patterns is only half the job. Sterile, voiceless writing is just as obvious.

### Signs of soulless writing:
- Every sentence is the same length and structure
- No opinions, just neutral reporting
- No acknowledgment of uncertainty or mixed feelings
- No first-person perspective when appropriate
- No humor, no edge, no personality

### How to add voice:

**Have opinions.** Don't just report facts—react to them.

> "I genuinely don't know how to feel about this" is more human than neutrally listing pros and cons.

**Vary your rhythm.** Short punchy sentences. Then longer ones that take their time.

**Acknowledge complexity.** Real humans have mixed feelings.

> "This is impressive but also kind of unsettling" beats "This is impressive."

**Use "I" when it fits.** First person isn't unprofessional—it's honest.

> "I keep coming back to..." signals a real person thinking.

## Workflow

1. **Identify patterns** - Scan for AI patterns listed above
2. **Rewrite sections** - Replace AI-isms with natural alternatives
3. **Preserve meaning** - Keep core message intact
4. **Maintain voice** - Match intended tone (formal, casual, technical)
5. **Add soul** - Inject personality and opinions

## Quick Scoring

Rate the text 1-10 on each dimension (max 50):

| Dimension | Question | Score |
|-----------|----------|-------|
| **Directness** | Direct statements or announcements? | /10 |
| **Rhythm** | Varied or metronomic? | /10 |
| **Trust** | Respects reader intelligence? | /10 |
| **Authenticity** | Sounds human? | /10 |
| **Density** | Anything cuttable? | /10 |

**Standard**:
- 45-50: Excellent, AI patterns removed
- 35-44: Good, room for improvement
- Below 35: Needs revision

## Examples

See **`examples/`** for before/after transformations:
- **`examples/english.md`** - English text examples

## Quick Reference

### Common Fixes:
| Before | After |
|--------|-------|
| "serves as a testament to" | "shows" |
| "Moreover, it provides" | "It adds" |
| "It's not just X, it's Y" | "X does Y" |
| "Industry experts believe" | "According to [specific source]" |

## Additional Resources

### Reference Files
- **`references/patterns-english.md`** - Complete English pattern reference
- **`references/phrases-to-cut.md`** - Filler phrases to remove
- **`references/wikipedia-source.md`** - Original Wikipedia source material

### Example Files
- **`examples/english.md`** - English before/after examples

## Best Practices

✅ **DO**:
- Combine pattern detection with soul injection
- Use progressive disclosure (core rules here, details in references/)
- Vary sentence structure and rhythm
- Add specific details instead of vague claims
- Use simple constructions (is/are/have) where appropriate

❌ **DON'T**:
- Just remove patterns without adding voice
- Leave stereotypic structures intact
- Over-correct and lose the original meaning
- Ignore language-specific patterns
- Make all sentences the same length

## License

MIT

## Attribution

Based on [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia/Signs_of_AI_writing), maintained by WikiProject AI Cleanup. Merges content from `humanizer`, `humanizer-zh`, and `stop-slop` skills.
