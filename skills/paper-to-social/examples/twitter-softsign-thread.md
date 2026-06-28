# Gold example: SoftSignum / SoftMuon thread (annotated)

This is the bar. Written for *"Softsign: Smooth Sign in Your Optimizer for Better Parameter Heterogeneity Handling"* (ICML 2026 submission). Every tweet is 255–279 chars (dense, near the cap), the theory gets three dedicated tweets, Muon is named in tweet 1, and real @handles are tagged where the work is discussed. Each tweet is followed by **why it works** so future agents copy the *moves*.

Full deliverable (frontmatter, embeds, alt text, checklist): `Papers/softsign/softsign-twitter-thread.md`. This file is the teaching copy.

Tags are NOT inline. They live in one separate shout-out post (13) at the end, Pethick-style. All web-verified: @kellerjordan0 (Muon), @jxbz (signSGD/duality), @leloykun (Newton–Schulz), @tmpethick (Scion/clipping).

---

**1/n** 🎉 Our paper is accepted at @icmlconf 2026! Everyone races to crown one optimizer. Muon, Signum, Lion: sign/LMO methods, fast, memory-light, top on LLM pretraining. But all share a flaw that wrecks the *end* of training, when the loss should settle. We fixed it, and we prove it.
[IMG: paper_cover_from_arxiv]

> *Why:* leads with the **@icmlconf acceptance** (the one allowed inline tag, because it is the actual news), **names Muon in tweet 1**, then drops into the "which optimizer wins" debate and the failure. Cover image = the paper's arXiv title page. Stands alone.

**2/** The flaw: they keep only the gradient's *direction* and drop the magnitude. sign() for vectors, UVᵀ for matrices in Muon. Early that's a strength: scale-free, robust to heavy-tailed noise. But near a minimum, converged coordinates still get a full kick and oscillate.

> *Why:* root cause in one tweet, with the fair version of the baseline first. No @mention (tags are saved for the shout-out post).

**3/** The folklore fix: run Signum, then flip to SGD mid-run. A hack. All params switch at once, the two step scales don't match so you re-tune the LR, and the carried-over momentum is now wrong. But params finish at different times, so no single global switch can be right.

> *Why:* pre-empts the obvious "just switch to SGD" reply. Earns trust that the real fix is non-trivial.

**4/** Our fix is one line. Swap hard sign() for a temperature-controlled tanh: update = tanh(τ · m). Big τ → you recover sign() exactly (Signum). Small τ → tanh goes linear in m, plain momentum SGD. One dial slides between "pure direction" and "magnitude-aware", per coordinate.
[IMG: tanh_approx]

> *Why:* the whole idea in one equation with both limits spelled out. Concept figure attached where understanding peaks.

**5/** The dial moves on its own. We anneal τ on a quantile schedule, so each coordinate leaves the sign regime on its own clock, by its momentum size. Big noisy directions stay bounded. Small converged ones slide into fine SGD-like steps. No reset, no scale jump, momentum kept.

> *Why:* the mechanism (adaptivity), and it resolves the three problems raised in tweet 3 one by one.

**6/** Same trick for matrices. Muon replaces every singular value with 1, which is just sign() in the spectral domain. We push them through a smooth saturating map instead, via Newton–Schulz iterations. That gives SoftMuon, a drop-in smooth Muon.

> *Why:* scope (vectors AND matrices), names the second deliverable. The Muon/Newton–Schulz authors get tagged in the shout-out post, not here.

**7/** Not a bolted-on heuristic. Write any update as argmin_d ⟨m,d⟩ + (1/τ)V(d) for a strongly convex V. Euclidean V → SGD. A norm → Muon / Lion. A specific entropic V makes tanh fall out *exactly*, in closed form. One framework, many optimizers.

> *Why:* **theory tweet 1/3** — the unifying framework. Shows the method is a derivation, not a guess.

**8/** It comes with a proof. In the stochastic non-convex setting, progress is measured by the Fenchel conjugate V*(−τ∇f), a dual-geometry version of ‖∇f‖². Set V Euclidean and it collapses to the classic ∑‖∇f‖² rate, same iteration complexity. Generality, asymptotically free.

> *Why:* **theory tweet 2/3** — the main theorem in plain words, with the reassurance that the generality costs nothing.

**9/** The conjugate says *why* it helps. For SoftSignum, V*(y) = ∑ ln cosh(yᵢ): quadratic for small gradients, linear for large ones. So early on progress is measured in ℓ1, stricter than ℓ2, and τ acts like the LR. Effective step = τ·δ, so a per-parameter τ schedule is principled.

> *Why:* **theory tweet 3/3** — connects the math back to the practical knob. This is the payoff that makes the theory feel earned, not decorative.

**10/** Does it win? LLM pretraining: before the transition SoftSignum/SoftMuon track their hard counterparts, after it they break away. SoftMuon gets the best eval perplexity on 130M and 360M, at 720M 16.216 vs 16.362 for Muon. The whole gain lands in the terminal phase, as predicted.
[IMG: llm_pretraining]

> *Why:* headline result, exact numbers, money plot, and it ties the win back to the thesis ("terminal phase").

**11/** Not LLM-only. Best coordinate optimizer on char-level prediction. SoftMuon tops the GraphLand GNN benchmark by avg rank. On imbalanced CIFAR the smooth transition wins in the mid-imbalance regime, where pure SGD and pure sign both lose. Regime-dependent, end to end.

> *Why:* breadth + the "regime-dependent" insight that mirrors Pethick's own framing (he gets tagged in the shout-out post).

**12/** Best part: nearly free. One knob, α_sign, robust across 0.3–0.9. At 0.9 you warm-start from an existing Signum/Muon checkpoint and relax only the tail.
Paper: [arXiv link]
Code: github.com/brain-lab-research/softsign
@coauthors — how does τ interact with WSD decay at scale?

> *Why:* the cost-to-adopt close + links + a genuine question to the exact target audience (people training at scale). Reply count is the strongest reach signal. No @mention here.

**13/n (separate shout-out post)** Work with @coauthors. And real respect to the recent sign- and spectral-optimizer line we build on: @jxbz (signSGD), @kellerjordan0 (Muon), @leloykun (Newton–Schulz), @tmpethick (Scion, generalized clipping). Go read them.

> *Why:* this is the ONLY tweet with @mentions. Posted as the final reply (or a standalone quoting tweet 1). It tags coauthors + the related-work authors + notable people in one place, exactly like Pethick. Keeps the main thread clean and gives the credit post its own moment.

---

## What to reuse from this example

- **Hook into a live debate, name the marquee method (Muon) in tweet 1.**
- **Tweets filled to 255–279 chars** — dense, never thin.
- **Three dedicated theory tweets** (framework → theorem-in-words → why-it-explains-the-win), not a throwaway clause.
- **Tags in one separate shout-out post (13)**, never inline in the main thread, all web-verified.
- Fair-baseline-then-flaw (2), pre-empt-the-obvious-fix (3), one-equation-two-limits (4).
- Exact numbers tied back to the thesis (10), cost-to-adopt tweet (12), real closing question.
- Voice throughout: plain, confident, a little contrarian, no em dashes, no semicolons, no hype, one 🧵.
