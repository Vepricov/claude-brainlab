# Twitter/X thread playbook

Language: **English**. Voice and anti-AI rules live in `voice-and-anti-ai.md` (read that first). Gold example: `examples/twitter-softsign-thread.md`. Figure extraction: `images.md`.

## Thread structure (8–12 tweets)

A reliable skeleton. Adapt order to the paper, but keep the shape.

1. **Hook.** Stand-alone tweet. Open inside a live debate the audience already cares about ("Muon and sign optimizers are everywhere, but..."). State the problem the paper fixes in one human sentence. End with a reason to keep reading. Add the 🧵 emoji. No title-dump. **The image on tweet 1 is ALWAYS the arXiv screenshot** (see the rule below).
2. **Why it breaks.** The root cause in plain words. What is the field doing and why does it fail in the case you fix?
3. **Why the obvious fix is wrong.** Pre-empt the "couldn't you just...?" reply. Shows you thought about it.
4. **The fix in one line + concept figure.** The single equation or idea, stated so a non-specialist gets it. Attach the concept figure here.
5. **The mechanism.** How the method actually works (the schedule, the adaptive part). One idea per tweet.
6. **Theory / why it's principled.** Briefly. "Not a heuristic, it's the closed-form solution of X, and we prove convergence." Don't dump the proof.
7. **Results + results figure.** Lead with the headline number, exact. Attach the money plot. Say where the gain comes from.
8. **Breadth.** Other domains/benchmarks it wins on. Shows it generalizes.
9. **Cost to adopt.** The "is it free?" tweet. Hyperparameter robustness, drop-in, checkpoint reuse. This is what makes people actually try it.
10. **Links + credits + question.** Paper, code, coauthor tags. End with a genuine question to drive replies (the X algorithm rewards reply count heavily).

Not every paper needs all ten, and a theory-heavy paper needs more. Cut, never pad.

## Three rules learned the hard way (Andrey insisted on each)

- **Tweet 1 ALWAYS carries the arXiv screenshot.** The opening tweet's image is the paper's arXiv page, every time, no exceptions. Preferred: a screenshot of the arXiv abstract page. If arXiv is not yet public, render the arXiv PDF title page instead (PyMuPDF: open the arXiv PDF, render page 0 down to the "Introduction" heading, trim margins — clean and reliable; Chrome `--screenshot` is flaky and macOS has no `timeout`). NEVER use an OpenReview author-console screenshot (it leaks the submission status). A concept/results figure does not go on tweet 1; it moves to the tweet where it is actually discussed. See `images.md` for both recipes.
- **Fill each tweet near the limit.** Target 255–279 chars. Thin 180–220-char tweets read as lazy and boring. Dense, specific, near the cap reads as a researcher who has a lot to say. Always verify with a char-count script (emoji = 2 on X, a raw URL = ~23).
- **Give theory its own tweets.** If the paper proves something, dedicate 2–3 tweets: (1) the framework/setup, (2) the main result stated in plain words, (3) *why* the theory explains the empirical win. "We also prove convergence" in a half-sentence is not acceptable.

## Tagging (a separate closing post, not sprinkled through the thread)

Keep @mentions OUT of the main numbered thread. Put them in a **dedicated closing post**, the way Pethick does. ONE exception in the main thread: if the paper was accepted somewhere, tweet 1 may lead with the venue tag (e.g. "accepted at @icmlconf 2026!"), because that is the actual news. Confirm the venue handle (ICML = @icmlconf, NeurIPS = @NeurIPSConf, ICLR = @iclr_conf).

**The closing post is a per-role CREDITS post for the coauthors** (Andrey's preference, 2026-06-26). Not a generic "respect to related work" shout-out. It names each coauthor and what they owned, the way ML researchers do it (CRediT-style: theory / experiments / code / writing / supervision). This is grounded in how real paper-announcement threads close (Kamoun Lab's thread guide, Taylor & Francis researcher-Twitter guide), and in published contribution statements ("X led the theory, the experiments and code were led by Y, Z drove the writing").

- **Default closing post = team credits, by role.** Format: "Genuinely a team effort. Theory and proofs led by @A and @B, the experiments by @C and @D, with @E guiding the framing. Learned a ton from all of you." A per-line layout (`@A — theory and proofs`) is clearer but for 5+ authors it spills past 280, so trim to one role each or split into two tweets.
- **NEVER invent who did what.** Roles are personal content. If you don't know each coauthor's contribution and handle, ASK the user, then fill it. Leave clear `@[handle] — [role]` placeholders meanwhile.
- **Prior-work respect is now optional and secondary.** Tagging the authors of methods you build on (signSGD, Muon, etc.) is still good for reach, but it goes in an *optional extra* post after the credits, only if the user wants it. Do not lead with it.
- **Verify every handle by web search before using it.** A wrong @handle tags a stranger and looks careless. If you cannot confirm a handle, leave a `verify` note instead of guessing.

Example credits post (softsign, template until Andrey supplies roles): *"Genuinely a team effort. Theory and the convergence proofs led by @A and @B, the LLM and GNN experiments by @C and @D, SoftMuon and the matrix extension by @B, with @E guiding the framing. Learned a ton from all of you."*

Optional prior-work post (only if asked): *"Built on the sign- and spectral-optimizer line: @jxbz (signSGD), @kellerjordan0 (Muon), @leloykun (Newton–Schulz), @tmpethick (Scion, generalized clipping)."*

Handles confirmed for the optimizer subfield (reuse / extend for related papers):
- **@kellerjordan0** — Keller Jordan, Muon.
- **@jxbz** — Jeremy Bernstein, signSGD, modular duality / steepest-descent theory.
- **@leloykun** — Franz Louis Cesista, Newton–Schulz coefficients, spectral clipping.
- **@tmpethick** — Thomas Pethick, Scion / LMO, generalized clipping (the reference-thread author).
- (consider also coauthors and, when confirmed, the relevant lab leads.)

## X algorithm rules that actually matter (2026)

- The **first tweet decides reach**: X surfaces the rest of the thread only if the opener earns engagement on its own. Spend the most effort here.
- **First-hour engagement window** is critical. Post when the audience is active (weekday ~9am or ~6pm in the audience's main timezone, usually ET for ML). Reply to early comments fast.
- **Replies > likes** as a quality signal. End with a real question. Ask the audience something tied to the content.
- **"Edutain":** teach one useful thing per tweet, enjoyably. Do not use the paper title as the copy.
- **Images lift reach and dwell time.** Attach figures; always add alt text (accessibility + a small ranking signal).
- Tag coauthors and relevant orgs/people whose work you build on (they often reshare).

Sources consulted: ihpi.umich.edu guide to research threads; Taylor & Francis "Twitter for researchers"; sendcove X-algorithm-2026 explainer; xagently thread guide.

## The reference example: Thomas Pethick (@tmpethick) optimizer thread

The thread Andrey pointed to as the bar. Opening tweet (verbatim):

> "1/ Let me chip in on the recent 'which optimizer rules them all' discussion with a somewhat more moderate take, asking: What Schatten-p norm to use? Turns out the answer is regime dependent! Specifically, even when smooth in Schatten-∞, Muon is not necessarily the best choice."

Why it works, and what to copy:

- **Enters a live debate.** "the recent 'which optimizer rules them all' discussion" — the reader is already invested before the paper is mentioned.
- **A moderate, specific take, not a sales pitch.** "a somewhat more moderate take" signals a researcher, not a marketer. Lowers the reader's guard.
- **Poses a sharp question** ("What Schatten-p norm to use?") and answers with nuance ("regime dependent"). Nuance reads as credible.
- **A concrete, slightly contrarian claim** ("Muon is not necessarily the best choice") that makes you want the rest.
- **One clean chart** attached to the opener.
- **Conversational register**, first person, no hype adjectives, no em dashes.

This is the register to write in: smart, plain, specific, a little contrarian, figure-backed. (For the SoftSignum paper this resonates perfectly — same Muon/optimizer debate, and the paper's answer is also regime-dependent.)
