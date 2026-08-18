# Venue Rule Resolver

Conference rules change. **Reverify the live official page at the start of every rebuttal**, record the check date, and let the live rule override this snapshot. Never infer one venue's revision/link/character policy from another.

## Required resolver output

```markdown
Venue/cycle:
Official sources and checked-at date:
Initial response deadline and discussion deadline:
Per-review/global character or word limit:
Paper/supplement revision allowed? What remains the decision basis?
New results allowed?
Links/files allowed?
Public, reviewer-only, and AC-confidential channels:
Anonymity constraints:
Unresolved ambiguity requiring chair confirmation:
```

## Official snapshot, checked 13-08-2026

### NeurIPS 2026 Main Track

Sources: [Main Track Handbook](https://neurips.cc/Conferences/2026/MainTrackHandbook) and [Reviewer Guidelines](https://neurips.cc/Conferences/2026/ReviewerGuidelines).

- Initial per-review rebuttal limit: 10,000 characters; rolling author/reviewer/AC discussion follows.
- No revised paper or supplement during response. New results may appear in text, but the original submission remains the basis for recommendations.
- No links in the response. Exception: if code is requested, an anonymized link may be sent to the AC in an Official Comment with correct readers.
- Preserve double blindness. Respond per review and verify OpenReview readers.
- Reviewer guidelines ask for actionable, opinion-changing questions and caution against large-compute requests; use that framing when explaining a minimal discriminating test.

### ICML 2026

Sources: [Peer Review FAQ and Rebuttal Instructions](https://icml.cc/Conferences/2026/PeerReviewFAQ) and [Dates](https://icml.cc/Conferences/2026/Dates).

- One response per official review, 5,000 characters each; all reviewers can see them. Cross-reference duplicate answers.
- Snapshot deadlines: initial response 30-03-2026 AoE, acknowledgement 03-04-2026, author-reviewer discussion through 07-04-2026 AoE. Recheck for the actual cycle.
- Reviewers may ask follow-ups; one final response per follow-up note, 5,000 characters.
- AC-confidential comments are for procedural/logistical matters, not extra or late rebuttal, except the FAQ's narrow late-review procedure.
- The FAQ page is the operational authority for revision, link, and channel details not restated here; resolve them live rather than assume.

### ICLR 2026

Source: [Author Guide](https://iclr.cc/Conferences/2026/AuthorGuide).

- Public discussion ran 11-11-2025 through 03-12-2025. Authors could respond and upload revised paper/supplement until the end.
- Rebuttal revision main-text limit: 10 pages. Changes to title, abstract, content, and supplement were allowed, but must be clearly communicated; reviewers/ACs may ignore changes that materially differ from the submission.
- Multiple revisions/comments were technically allowed, but reviewers need not inspect every version. Consolidate and provide an exact change summary.
- The author set could not change during rebuttal; preserve anonymity and select OpenReview readers deliberately for private messages.

### ACL Rolling Review

Source: [ARR Authors Guidelines](https://aclrollingreview.org/authors), especially “Step 2: Respond to reviews.”

- Timing varies by cycle. Author response is optional and immediately visible, with possible back-and-forth.
- ARR is a reviewing platform, not the venue decision itself. The response should mainly correct factual misunderstandings and clarify assessment-relevant points; major clarity or scientific changes may be better handled by revise-and-resubmit.
- Keep threads short. ARR says ACs are asked to consider at most two author responses per review thread, and directly asking reviewers to raise scores is inappropriate.
- Reviewers need not respond. Use the review-issue process for genuine guideline violations, not scientific disagreement.
- Confirm the target conference's separate commitment and decision rules after the ARR meta-review.

## Fail-closed rule

If an official page is missing, contradictory, or silent on a material action, do not upload, link, revise, or use a private channel based on memory. Record the ambiguity and ask the chair/support address before acting.
