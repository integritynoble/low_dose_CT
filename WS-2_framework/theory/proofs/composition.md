# Composition law for signal-equivalence — negative-result note (`open_questions.md` §4)

**Status:** v0.1 — negative-result position recorded 2026-06-02 alongside the v0.2 manuscript.
**Cross-references:** [`open_questions.md`](../open_questions.md) §4; manuscript [`paper_draft/manuscript.tex`](../../paper_draft/manuscript.tex) Discussion §"Point-evaluated by design" (B3); [`dose-equivalence-framework.md`](../dose-equivalence-framework.md) §8.

---

## 1. The question

The framework defines signal-equivalence at level $(r, T, \varepsilon, \alpha)$ over subpopulation $\Pi$. The natural composition question:

> **Q.** Suppose $M \equiv_{(r, T, \varepsilon, \alpha, \Pi)} \mathcal{M}_{\textrm{ref}}$ and $\mathcal{M}_{\textrm{ref}} \equiv_{(r', T, \varepsilon', \alpha', \Pi)} \mathcal{M}_{\textrm{ref}}'$ (same task, same subpopulation). Does it follow that $M \equiv_{(r'', T, \varepsilon'', \alpha'', \Pi)} \mathcal{M}_{\textrm{ref}}'$ for some derivable $(r'', \varepsilon'', \alpha'')$?

The intuitive guess is $r'' = r \cdot r'$ (composing the signal-reduction operators), $\varepsilon'' = \varepsilon + \varepsilon'$ (triangle inequality on the means), $\alpha'' = \alpha + \alpha'$ (union bound on the events). This writeup argues the guess is wrong, and that no clean composition law exists.

---

## 2. Why $r'' = r \cdot r'$ is the *wrong* signal ratio

The signal ratio $r$ characterises the *acquisition operator* $T_r$, not the *method's tolerance for reduction*. When we write $M \equiv_{(r, ...)} \mathcal{M}_{\textrm{ref}}$, the statement is:

> "$M$ on $T_r(\mathcal{S}_{\textrm{ref}}(\Pi))$ produces task performance within $\varepsilon$ of $\mathcal{M}_{\textrm{ref}}$ on $\mathcal{S}_{\textrm{ref}}(\Pi)$."

A second credential $\mathcal{M}_{\textrm{ref}} \equiv_{(r', ...)} \mathcal{M}_{\textrm{ref}}'$ does *not* tell us how $M$ behaves on $T_{r r'}(\mathcal{S}_{\textrm{ref}}(\Pi))$. The first credential's evidence is gathered on reduced-signal data at ratio $r$; the second credential's evidence is gathered on reduced-signal data at ratio $r'$ — *for a different method*. Neither dataset tells us about $M$'s behaviour at $r \cdot r'$. Indeed, $M$ may not even have been *trained* on data at $r \cdot r'$, and methods trained at one $r$ frequently degrade at nearby $r'$ (see [`monotonicity.md`](monotonicity.md) — pending — for the conditional-monotonicity discussion).

**Conclusion:** $r$ cannot be composed across credentials because the evidence sets for the two component credentials do not overlap in their reduced-signal regime.

---

## 3. Why $\varepsilon'' = \varepsilon + \varepsilon'$ is *almost right but unsound*

For *independent* error contributions on the population means, a triangle-inequality argument would give

$$
\left| \mathbb{E}\!\left[P_M\right] - \mathbb{E}\!\left[P_{\mathcal{M}_{\textrm{ref}}'}\right] \right| \;\leq\; \left| \mathbb{E}\!\left[P_M\right] - \mathbb{E}\!\left[P_{\mathcal{M}_{\textrm{ref}}}\right] \right| + \left| \mathbb{E}\!\left[P_{\mathcal{M}_{\textrm{ref}}}\right] - \mathbb{E}\!\left[P_{\mathcal{M}_{\textrm{ref}}'}\right] \right| \;<\; \varepsilon + \varepsilon'.
$$

The inequality is mathematically sound *if the two component credentials are evaluated against the same reference acquisition $\mathcal{S}_{\textrm{ref}}$ on the same subpopulation $\Pi$*. But two practical obstructions break the chain:

1. **The reference for credential 1 ($\mathcal{M}_{\textrm{ref}}$) is the candidate for credential 2.** Credential 2's metric averages over $\mathcal{S}_{\textrm{ref}}(\Pi)$ — the *full-signal* acquisition — and the reference there is $\mathcal{M}_{\textrm{ref}}'$. Credential 1's metric averages over $T_r(\mathcal{S}_{\textrm{ref}}(\Pi))$ — the *reduced-signal* acquisition. The two expectation operators are taken over different random variables. The triangle inequality on means *as I wrote it above* silently equated $\mathbb{E}_{T_r}\!\left[P_{\mathcal{M}_{\textrm{ref}}}\right]$ with $\mathbb{E}\!\left[P_{\mathcal{M}_{\textrm{ref}}}\right]$, which is precisely the non-trivial population claim each credential makes — *not* a derivable consequence.

2. **The $\varepsilon$ values inherit the noise of the bootstrap, not the population truth.** The $\varepsilon$ in a credential is a margin specified *a priori* by the user; the verdict says the CI is contained in $(-\varepsilon, \varepsilon)$. Adding $\varepsilon$ and $\varepsilon'$ does not give a margin that the composed CI is guaranteed to fit inside. Two CIs near the boundary of their respective margins can yield a composed difference that is outside $\varepsilon + \varepsilon'$ — the bound is on the *worst case the user agreed to accept*, not on the actual mean differences.

**Conclusion:** the $\varepsilon$-budget composition is intuitive but is not a derivable theorem. Asserting it would propagate user-specified slack as if it were a measured quantity.

---

## 4. Why $\alpha'' = \alpha + \alpha'$ is sound but useless

The union bound on independent verdicts does give $\Pr[\text{both pass}] \geq 1 - \alpha - \alpha'$. So if both component credentials issue at the canonical $\alpha = 0.05$, a composed claim at $\alpha = 0.10$ is statistically sound. But this is the only piece of the composition that does compose, and it composes at the cost of doubling the type-I error budget — which immediately makes the composed credential less informative than either component, not more.

A practitioner wanting a $\Pr \geq 1 - 0.05$ composed claim would need to design each component at $\alpha = 0.025$ via Bonferroni — which requires re-issuing both component credentials at the tighter significance level. This is not a *composition of existing credentials*; it is *re-evaluation under a different design*.

**Conclusion:** $\alpha$ composes only via the union bound, and the union bound is a deflationary operation. It cannot be the basis of a useful composition law.

---

## 5. The framework's position

**The framework intentionally does not admit a composition law.** This is recorded in the manuscript Discussion §"Point-evaluated by design" (B3):

> Signal-equivalence is a *point-evaluated* framework: each credential is a separately verifiable claim at a specific $(r, T, \varepsilon, \alpha, \Pi)$, and algebraic combinations of credentials are deliberately not derivable from one another.

A user who wants to claim equivalence between $M$ and $\mathcal{M}_{\textrm{ref}}'$ at some $(r'', T, \varepsilon'', \alpha'', \Pi)$ must **issue a new credential by running the paired-bootstrap on a new test set at the new operating point**. The framework's content-addressed schema makes this cheap to do — issuing a credential is a function call — and the no-composition discipline is precisely what allows each credential to be independently verifiable without provenance entanglement.

---

## 6. The publishable position

This is a **negative result with a positive framing**: the framework's design choice not to admit composition is what makes each credential individually trustworthy. A reader of a published credential does not have to audit a chain of prior credentials to verify the present one; they re-run the bootstrap on the present test set under the present framework hash and check the verdict.

The alternative — a transitive framework — would have produced credentials whose meaning depends on the meaning of credentials they cite, which in turn depends on the meaning of credentials *those* cite, etc. The auditing burden grows with the depth of the chain, and a single mid-chain re-interpretation can invalidate a downstream claim that the downstream author had no way to verify. The medical-imaging-methods community has experience with this failure mode in benchmark drift~([Wang, Ye & De Man 2020](https://doi.org/10.1038/s42256-020-00273-z)) and we explicitly avoid recreating it.

---

## 7. What this writeup does *not* do

* It does not prove that *no* derivable composition rule exists in some weaker form. A future research programme might find that, conditional on additional assumptions (e.g.\ all methods drawn from a fixed training distribution, all credentials issued by the same library version, the reductions $r, r'$ both within a calibrated monotonicity range), some restricted composition rule holds. The current position is that such a rule is *not assumed* by the framework.
* It does not preclude users from *reporting* multiple credentials side by side and inviting the reader to draw their own conclusions. What it precludes is automatic algebraic derivation by the framework.

---

*v0.1 — 2026-06-02. The "design choice, not omission" framing is load-bearing for the v0.2 manuscript; future revisions of this note should retain it even if a restricted composition rule is eventually proven.*
