# Conditional monotonicity in $r$ (`open_questions.md` §5)

**Status:** v0.1 — conjecture + counterexample sketch recorded 2026-06-03 (D9 + 14).
The empirical validation against Phase 1 pilot data is gated on D9 + 90.
**Cross-references:** [`open_questions.md`](../open_questions.md) §5; manuscript [`paper_draft/manuscript.tex`](../../paper_draft/manuscript.tex) §framework + Discussion; [`dose-equivalence-framework.md`](../dose-equivalence-framework.md) §8 (which lists this as the *key open property*).

---

## 1. The question

Intuitively, more signal should be at least as informative as less, so a method that is signal-equivalent at a low ratio $r_0$ "should" also be equivalent at any higher ratio $r \in [r_0, 1]$. Concretely:

> **Naive monotonicity (false in general).** If $M \equiv_{(r_0, T, \varepsilon, \alpha, \Pi)} \mathcal{M}_{\textrm{ref}}$ for some $r_0 \in (0, 1]$, then $M \equiv_{(r, T, \varepsilon, \alpha, \Pi)} \mathcal{M}_{\textrm{ref}}$ for all $r \in [r_0, 1]$.

The naive form is **false**. A reconstruction method optimised (trained, tuned, or hand-engineered) for one specific signal ratio $r_0$ can degrade at other ratios because the underlying noise statistics, regularisation strengths, and learned priors are calibrated to $r_0$'s operating regime. A learned denoiser trained on $25\%$-dose CT may produce *worse* outputs on full-dose input than full-dose FBP, simply because it was never trained on that regime and aggressively denoises away features it has learned to interpret as noise.

So the question is whether a *conditional* form holds under a training discipline that the literature already recognises (e.g.\ training on a distribution over $r$ that covers the range).

---

## 2. The class $\mathcal{M}_{[r_{\min}, 1]}$

Let $r_{\min} \in (0, 1]$. A reconstruction method $M$ is in the class $\mathcal{M}_{[r_{\min}, 1]}$ if it is trained or calibrated under a sampling distribution over signal ratios whose support covers $[r_{\min}, 1]$, i.e.\ during training/calibration each acquisition $s$ is drawn as $s \sim T_R(\mathcal{S}_{\textrm{ref}}(X))$ where $R$ has a density on $[r_{\min}, 1]$ that is bounded away from zero.

The class captures the **"single-network, $r$-conditioned"** design pattern that the low-dose CT / accelerated MRI / low-activity PET communities have converged on over the last several years. Concrete members include:

* **CT** — *Variable-dose RED-CNN / DnCNN* trained with random Poisson-thinning at $r \sim \mathrm{Uniform}(r_{\min}, 1)$ per training example.
* **MRI** — *Variable-density-mask end-to-end variational networks* trained at acceleration $R \sim \mathrm{Uniform}(1, 1/r_{\min})$.
* **PET** — *Activity-aware UNet denoisers* trained with random list-mode thinning at $r \sim \mathrm{Uniform}(r_{\min}, 1)$.

The class explicitly excludes methods trained at a single $r$ (e.g.\ "the $25\%$ model"), under-relaxed iterative reconstruction with one fixed regularisation strength, and any method whose training prior collapses to a single operating point.

---

## 3. The conjecture

> **Conjecture (conditional monotonicity).** Let $M \in \mathcal{M}_{[r_{\min}, 1]}$. If $M \equiv_{(r_0, T, \varepsilon, \alpha, \Pi)} \mathcal{M}_{\textrm{ref}}$ for some $r_0 \in [r_{\min}, 1]$, then for all $r \in [r_0, 1]$,
> $$ M \equiv_{(r, T, \varepsilon, \alpha, \Pi)} \mathcal{M}_{\textrm{ref}}. $$

In words: if a method trained-over-the-range achieves equivalence at the *low* end of its training range, it achieves equivalence everywhere up to full signal. The conjecture is a statement about the well-posedness of the *training discipline*, not a statement about reconstruction methods in general.

We deliberately do not extend the conjecture to $r < r_{\min}$ (outside the training support). A method's behaviour outside its training distribution is genuinely an extrapolation question and is not what the framework is designed to certify.

---

## 4. Heuristic argument

The intuition is that for $r > r_0$ the candidate's input acquisition $T_r(\mathcal{S}_{\textrm{ref}}(\Pi))$ is *closer in distribution* to the full-signal acquisition than the input at $r_0$ was. If the metric $P(T(\cdot), g(\cdot))$ is a measurable functional that *does not deteriorate sharply when the input becomes cleaner* — a property that holds for AUC, Dice, MAE, and contrast-recovery under standard regularity — then:

* Under regularity on $M$ and $\mathcal{M}_{\textrm{ref}}$, the population-mean performance gap $\mu(r) = \mathbb{E}_\Pi[P_M(r) - P_{\mathcal{M}_{\textrm{ref}}}(1)]$ is continuous in $r$.
* $\mu(r_0)$ is inside $(-\varepsilon, \varepsilon)$ (the credential's verdict).
* If $\mu(r)$ does not exceed $\varepsilon$ at any $r \in [r_0, 1]$ — which is the conjecture's content — equivalence is preserved.

The proof is not a theorem because step three is exactly the property being conjectured; the chain of reasoning shows that the conjecture is consistent with the framework's regularity assumptions, not that it is forced by them.

---

## 5. Counterexample sketch (and what would refute the conjecture)

A counterexample to the conjecture would be a method $M \in \mathcal{M}_{[r_{\min}, 1]}$ with $M \equiv_{(r_0, \cdots)}$ but $M \not\equiv_{(r, \cdots)}$ for some $r \in (r_0, 1]$. Two candidate failure modes are worth checking against the Phase 1 pilot data once it lands:

**5.1. Catastrophic overfit to the low end.** If the training distribution $R$ has its mass concentrated near $r_{\min}$ (e.g.\ a Beta distribution with shape parameters $0.5, 2$), the method may be effectively optimised for $r_0$ and degrade at $r \gg r_0$. The conjecture as stated requires only that the training-distribution support cover $[r_{\min}, 1]$ — not that the density be uniform. To rule this counterexample out, the class should be tightened to require a density bounded away from zero on $[r_{\min}, 1]$ (which the §2 definition does require, but informally; a future revision should formalise the lower-bound constant).

**5.2. Equivariance-breaking architecture.** A method whose architecture treats full-signal and reduced-signal acquisitions through asymmetric paths (e.g.\ a learned gating layer that switches behaviour based on detected noise level) can produce performance discontinuities at the gating threshold. Such methods are inside $\mathcal{M}_{[r_{\min}, 1]}$ by training discipline but violate the implicit continuity assumption of §4. The conjecture would need to be conditioned on architectural regularity (no learned gating with discontinuous derivatives w.r.t.\ input SNR) to exclude this counterexample.

Both candidates are findable in the literature in principle; neither has been demonstrated as a *signal-equivalence* counterexample because the framework's discipline of explicit $r$-credentials is itself new. The Phase 1 pilot's three baselines (RED-CNN; a transformer reconstruction; a diffusion-based reconstruction) are testable instances; if any of them violates the conjecture, the §3 statement should be weakened to add the missing regularity assumption.

---

## 6. The empirical check (gated on Phase 1 pilot at D9 + 90)

When Phase 1 pilot CT data lands, the test is straightforward:

1. For each of the three baselines $M_i$, compute the 5-tuple credential at the pre-registered $r_0 = 0.25$ on the WS-1 v0.5 cohort.
2. For each baseline at which $r_0 = 0.25$ produced a `PASS` verdict, compute credentials at $r \in \{0.40, 0.55, 0.70, 0.85\}$ on the same cohort.
3. Plot the population-mean performance gap $\hat\mu(r)$ against $r$ for each baseline.
4. **Predicted by the conjecture:** $\hat\mu(r) \in (-\varepsilon, \varepsilon)$ for all $r \geq r_0$. **Predicted by the naive monotonicity:** $\hat\mu(r)$ is monotone non-increasing in $|r - 1|$.

If the conjecture holds across the three baselines, the manuscript can state it as "design recommendation supported by Phase 1 pilot data on 3 baselines." If any baseline violates the conjecture, the §3 statement should be weakened with the regularity assumption (architectural smoothness; density-bounded-away-from-zero training) that the failing case violates.

---

## 7. Manuscript implication

**Recommended v0.4 manuscript addition** (after Phase 1 pilot data lands at D9 + 90):

> *Design recommendation (conditional monotonicity).* When a method is trained or calibrated under a signal-ratio distribution whose support covers a range $[r_{\min}, 1]$, the framework's empirical evidence on this paper's three CT baselines suggests that equivalence at any $r_0 \in [r_{\min}, 1]$ predicts equivalence at all $r \in [r_0, 1]$. This is recommended as a design pattern; the framework continues to require a separately-issued credential at each operating point.

The recommendation is a *user-facing pattern*, not a relaxation of the credential discipline. Users are still asked to issue and publish credentials at the operating points they claim — the conjecture is a *cohort-sizing economy* (issue at the tightest $r$ first; if `PASS`, less aggressive points are likely to be `PASS` too), not a *credential composition* (which `proofs/composition.md` records as non-derivable in general).

---

## 8. What this writeup is and is not

**It is** the v0.1 theory-side anchor for the manuscript's pending design-recommendation paragraph on conditional monotonicity. The conjecture is precisely stated; the class $\mathcal{M}_{[r_{\min}, 1]}$ is precisely defined; two candidate counterexamples are flagged; the empirical check is scoped.

**It is not** a theorem. The conjecture's status is "consistent with the framework's regularity assumptions, falsifiable by a single counterexample on a method in the class." A theorem would require either (a) a tighter regularity condition on $M$ that rules out both counterexamples in §5, or (b) a measure-theoretic argument that bounds $\sup_{r \in [r_0, 1]} |\mu(r) - \mu(r_0)|$ from above by something computable from the credential's evidence — and that bound, if it exists, would itself be a publishable result.

---

*v0.1 — 2026-06-03. Revise after Phase 1 pilot data lands (D9 + 90): either upgrade to "design recommendation supported by 3 baselines" if no counterexample surfaces, or weaken the conjecture statement to add the regularity assumption(s) the failing case violates.*
