# LinkedIn example — SoftSignum / SoftMuon

Worked example (English, professional prose, de-emojified Telegram substance). Replace coauthor handles and links before posting.

---

Our paper "Softsign: Smooth Sign in Your Optimizer for Better Parameter Heterogeneity Handling" was accepted at ICML 2026.

Sign-based and LMO-based optimizers like Muon, Signum and Lion are everywhere in LLM pretraining: fast, memory-light, strong. But they keep only the direction of the gradient and drop its magnitude, so near a minimum the coordinates that have already converged still get a full-size update and start to oscillate. The end of training is exactly where this hurts.

Our fix is one line. We replace the hard sign with a temperature-controlled tanh, tanh(τ·m). High temperature recovers sign (Signum), low temperature becomes plain momentum SGD, and a quantile-based schedule moves each coordinate from one regime to the other on its own clock. The same idea extends to matrices through the singular values, giving SoftMuon, a drop-in smooth version of Muon. It all falls out of a single geometry-relaxation framework with a convergence proof in the stochastic non-convex setting.

It is close to free to adopt: one extra hyperparameter, robust across a wide range, and you can warm-start from an existing Signum or Muon checkpoint. On LLM pretraining SoftMuon reaches the best eval perplexity (16.216 vs 16.362 for Muon at 720M), and the gains hold on GNN benchmarks and imbalanced-data tasks.

Paper: arxiv.org/abs/2605.31371
Code: github.com/brain-lab-research/softsign
Work with [coauthors].

#MachineLearning #DeepLearning #LLM #Optimization #ICML2026

---

## Notes
- First two lines carry the click (acceptance + the flaw). Everything after "see more" is the payoff.
- Connected prose, short paragraphs, one exact number, calm closing. No em dashes, no hype.
- Attach one figure (the LLM results plot or the tanh concept figure) with a one-line caption.
