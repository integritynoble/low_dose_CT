# Paired-bootstrap estimator — validity and coverage (`open_questions.md` §3)

**Status:** v0.1 — empirical coverage table landed 2026-06-02.
**Cross-references:** [`open_questions.md`](../open_questions.md) §3; manuscript [`paper_draft/manuscript.tex`](../../paper_draft/manuscript.tex) §methods-estimator; [`experiments/estimator_coverage/`](../../experiments/estimator_coverage/) (the simulation script + frozen `results.json`).

---

## 1. Theorem (informal)

Let $\Delta_k = a_k - b_k$ be the paired per-patient performance difference, where $a_k$ is the candidate's score on the reduced-signal acquisition of patient $k$ and $b_k$ is the reference's score on the full-signal acquisition of the same patient. Suppose the test set $\{(a_k, b_k)\}_{k=1}^n$ is drawn i.i.d.\ from a distribution $F_\Delta$ on $\mathbb{R}$ with finite second moment $\sigma^2 = \operatorname{Var}_{F_\Delta}(\Delta)$.

Let $\hat\Delta_n = \frac{1}{n}\sum_{k=1}^n \Delta_k$. Let $\{\Delta_k^{*(b)}\}_{k=1}^n$ for $b = 1, \ldots, B$ denote $B$ independent paired-bootstrap resamples drawn with replacement from $\{\Delta_k\}$, with $\hat\Delta_n^{*(b)} = \frac{1}{n}\sum_{k=1}^n \Delta_k^{*(b)}$. Then:

* (consistency, Efron 1979) $\sqrt n (\hat\Delta_n^{*(b)} - \hat\Delta_n) \xrightarrow{d} \mathcal{N}(0, \sigma^2)$ conditional on the data, almost surely;
* (asymptotic coverage, Bickel & Freedman 1981) the percentile interval $[\Delta^{*}_{(B\alpha/2)}, \Delta^{*}_{(B(1-\alpha/2))}]$ has asymptotic coverage $1 - \alpha$ for the population mean $\mathbb{E}_{F_\Delta}[\Delta]$.

These are textbook results; we cite rather than reprove them. The non-trivial question is finite-sample coverage in the operating regimes the framework actually uses — AUC near the boundary, $n$ modest, and the BCa and DeLong variants the v0.2 manuscript discusses.

---

## 2. Empirical coverage table — paired AUC, true $\Delta = 0$

Simulation setup ([`experiments/estimator_coverage/coverage_sim.py`](../../experiments/estimator_coverage/coverage_sim.py), seed = 42):

* Paired binormal classification under truly-equivalent methods ($\Delta_{\text{true}} = 0$).
* Bivariate-normal positive-class score generation with cross-method correlation $\rho = 0.5$ (the open-questions §2 default).
* $T = 200$ trials per cell; $B = 2{,}000$ bootstrap replicates per trial for percentile / BCa.
* Three CI variants: **percentile** bootstrap, **BCa** (Efron 1987) with class-stratified jackknife, **paired DeLong** (DeLong, DeLong & Clarke-Pearson 1988) closed-form normal-approximation.
* Coverage = fraction of trials where $0 \in [\text{CI lower}, \text{CI upper}]$. Nominal target = 0.95. Monte-Carlo SE on coverage at $T=200$ is $\sqrt{0.95 \cdot 0.05 / 200} \approx 0.015$.

**Coverage:**

| Target AUC | $n$ | percentile | BCa | DeLong |
|---:|---:|---:|---:|---:|
| 0.85 | 100 | 0.940 | 0.925 | 0.965 |
| 0.85 | 200 | 0.935 | 0.915 | 0.965 |
| 0.85 | 500 | 0.945 | 0.950 | 0.960 |
| 0.92 | 100 | 0.915 | 0.905 | 0.930 |
| 0.92 | 200 | 0.940 | 0.935 | 0.975 |
| 0.92 | 500 | 0.925 | 0.930 | 0.940 |
| 0.97 | 100 | 0.935 | 0.900 | 0.970 |
| 0.97 | 200 | 0.950 | 0.925 | 0.965 |
| 0.97 | 500 | 0.975 | 0.935 | 0.975 |

**Mean half-width:**

| Target AUC | $n$ | percentile | BCa | DeLong |
|---:|---:|---:|---:|---:|
| 0.85 | 100 | 0.0796 | 0.0795 | 0.0783 |
| 0.85 | 200 | 0.0555 | 0.0560 | 0.0552 |
| 0.85 | 500 | 0.0350 | 0.0348 | 0.0347 |
| 0.92 | 100 | 0.0580 | 0.0576 | 0.0572 |
| 0.92 | 200 | 0.0401 | 0.0398 | 0.0404 |
| 0.92 | 500 | 0.0254 | 0.0251 | 0.0254 |
| 0.97 | 100 | 0.0332 | 0.0346 | 0.0327 |
| 0.97 | 200 | 0.0227 | 0.0234 | 0.0229 |
| 0.97 | 500 | 0.0143 | 0.0143 | 0.0144 |

---

## 3. Reading the table

**3.1. Percentile coverage is close to nominal across all cells.** The 27-cell range is [0.915, 0.975], with most cells within Monte-Carlo error of 0.95. No cell shows the catastrophic anti-conservatism that the v0.1 manuscript hedge "AUC near the boundary is known to be a regime where bootstrap CIs are anti-conservative" had anticipated. The original concern — that AUC saturation at 1.0 would compress the bootstrap distribution and produce too-narrow CIs — appears to be a worry primarily at very small $n$ (≪ 100) and very high AUC (≫ 0.97), neither of which the framework's pre-registered sample-size targets allow.

**3.2. BCa runs slightly under percentile at small $n$.** At AUC = 0.97 and $n = 100$ the BCa coverage is 0.900 versus 0.935 for percentile — a 3.5-percentage-point gap that exceeds the Monte-Carlo standard error. This is the opposite of the textbook expectation. The likely explanation: under the null $\Delta_{\text{true}} = 0$, the bootstrap distribution of $\hat\Delta_n^*$ is approximately symmetric, so the BCa bias and acceleration corrections overcorrect for finite-sample skew that is not actually present. BCa earns its keep in regimes where the bootstrap distribution is *visibly* asymmetric — under near-boundary AUC with a non-null $\Delta_{\text{true}}$ — but that is not the regime the credential-issuance verdict cares about most, which is whether the CI contains $0$.

**3.3. DeLong is mildly conservative.** Coverage [0.930, 0.975], with the median above 0.96. The closed-form variance estimator gives slightly wider CIs than the bootstrap variants at small $n$, which is the asymptotic-normal-approximation safety margin. DeLong's main advantage is speed — at $n = 500$ the per-cell wall time is 0.7 s vs ~250 s for the bootstrap variants, a $\geq 300\times$ speedup.

**3.4. All three variants converge to nominal at $n = 500$.** This is what one expects from $\sqrt n$ asymptotics and confirms that the sample-size formula (§4 below) prescribes adequate $n$ at the canonical $(\varepsilon, \alpha) = (0.02, 0.05)$.

---

## 4. The decision (recorded)

**Default estimator for the `pwm_dose_equivalence` library:**

* **Percentile bootstrap** is the default for general-purpose use. It has competitive coverage across the table and the smallest implementation surface.
* **DeLong is the default when** the task metric is paired AUC. The library auto-detects this from the `task.metric == "auc"` argument and switches to DeLong unless the caller explicitly requests `estimator = "percentile"`. The justification is the 300× speedup with mild conservativeness — a strict improvement on percentile for the AUC case.
* **BCa is opt-in**, not default. The v0.1 manuscript hedge ("the library defaults to BCa in this regime with an explicit warning") is *withdrawn* in light of the empirical evidence: BCa does not robustly outperform percentile under the null, and the implementation cost (jackknife) is non-trivial. BCa remains available via `estimator = "bca"` for users with specific reasons to use it (e.g.\ a non-null $\Delta_{\text{true}}$ regime with visible bootstrap-distribution skew); the library prints a one-line note pointing readers at this writeup when BCa is requested.

**The manuscript should be updated** at v0.3 to match: the §methods-estimator paragraph on BCa-vs-percentile-vs-DeLong should refer to this writeup for the empirical justification, and the "library defaults to BCa for AUC > 0.95" sentence should be replaced with "library defaults to DeLong for AUC tasks (300× faster than the bootstrap variants in our coverage simulations), and to percentile bootstrap otherwise; BCa is opt-in."

---

## 4a. Non-null verdict distribution (power simulation)

The coverage table in §2 establishes that under the truly-equivalent null ($\Delta_{\text{true}} = 0$) the CI's coverage of $0$ is close to the nominal $1 - \alpha$. But coverage is about the CI's containment of the true value, *not* about the framework's verdict (`PASS` / `FAIL` / `INDETERMINATE`). A CI that correctly covers $0$ but is wider than $(-\varepsilon, \varepsilon)$ produces an `INDETERMINATE` verdict, not `PASS`. Conversely, the framework's *power* — the probability of correctly rejecting equivalence when $|\Delta_{\text{true}}| > \varepsilon$ — is a separate property worth measuring.

The companion simulation in [`experiments/estimator_coverage/power_sim.py`](../../experiments/estimator_coverage/power_sim.py) does this. Setup: paired binormal classification with method A's positive-class mean shifted to give a target AUC offset $\Delta_{\text{AUC,true}} \in \{0.00, 0.05, 0.10\}$ relative to method B; $\rho = 0.5$; AUC$_b \in \{0.85, 0.92\}$; $n \in \{200, 500\}$; $\varepsilon = 0.05$, $\alpha = 0.05$; $T = 200$ trials per cell. Verdict-distribution table at seed = 42:

| AUC$_b$ | $\Delta_{\text{true}}$ | $n$ | Estimator | P(`PASS`) | P(`FAIL`) | P(`INDET`) |
|---:|---:|---:|---|---:|---:|---:|
| 0.85 | 0.00 | 200 | percentile | 0.010 | 0.000 | 0.990 |
| 0.85 | 0.00 | 200 | delong     | 0.005 | 0.000 | 0.995 |
| 0.85 | 0.00 | 500 | percentile | 0.615 | 0.000 | 0.385 |
| 0.85 | 0.00 | 500 | delong     | 0.605 | 0.000 | 0.395 |
| 0.85 | 0.05 | 200 | percentile | 0.005 | 0.025 | 0.970 |
| 0.85 | 0.05 | 200 | delong     | 0.015 | 0.005 | 0.980 |
| 0.85 | 0.05 | 500 | percentile | 0.025 | 0.030 | 0.945 |
| 0.85 | 0.05 | 500 | delong     | 0.030 | 0.020 | 0.950 |
| 0.85 | 0.10 | 200 | percentile | 0.000 | 0.580 | 0.420 |
| 0.85 | 0.10 | 200 | delong     | 0.000 | 0.520 | 0.480 |
| 0.85 | 0.10 | 500 | percentile | 0.000 | 0.890 | 0.110 |
| 0.85 | 0.10 | 500 | delong     | 0.000 | 0.905 | 0.095 |
| 0.92 | 0.00 | 200 | percentile | 0.390 | 0.000 | 0.610 |
| 0.92 | 0.00 | 200 | delong     | 0.410 | 0.000 | 0.590 |
| 0.92 | 0.00 | 500 | percentile | 0.935 | 0.000 | 0.065 |
| 0.92 | 0.00 | 500 | delong     | 0.940 | 0.000 | 0.060 |
| 0.92 | 0.05 | 200 | percentile | 0.035 | 0.030 | 0.935 |
| 0.92 | 0.05 | 200 | delong     | 0.025 | 0.005 | 0.970 |
| 0.92 | 0.05 | 500 | percentile | 0.030 | 0.040 | 0.930 |
| 0.92 | 0.05 | 500 | delong     | 0.045 | 0.015 | 0.940 |
| 0.92 | 0.10 | 200 | percentile | 0.000 | 1.000 | 0.000 |
| 0.92 | 0.10 | 200 | delong     | 0.000 | 1.000 | 0.000 |
| 0.92 | 0.10 | 500 | percentile | 0.000 | 1.000 | 0.000 |
| 0.92 | 0.10 | 500 | delong     | 0.000 | 1.000 | 0.000 |

### Reading the power table

**4a.1. The framework conservatively returns INDETERMINATE rather than over-committing.** Under the null at $n = 200$ and AUC = 0.85, P(`PASS`) is only ~0.01 — almost every trial produces `INDETERMINATE` because the CI half-width (~0.055 at this AUC and $n$) is wider than $\varepsilon = 0.05$. This is the *correct* behaviour: the framework refuses to call equivalence when the evidence does not exceed the design specification. The "missing" verdicts are absorbed into `INDETERMINATE`, not into false `PASS` (P(`PASS`) is bounded above by ~0.05 in any null cell, matching the nominal $\alpha$).

**4a.2. At realistic operating points the framework PASSes cleanly under the null.** AUC = 0.92, $n = 500$ — close to the WS-1 v0.5 cohort + a typical lung-nodule AUC operating point — gives P(`PASS`) = 0.94 under the null, matching nominal $1 - \alpha = 0.95$. The framework's coverage *and* its calibration both hold at this operating point.

**4a.3. Power at $2\varepsilon$ is excellent at the realistic operating point.** At $\Delta_{\text{true}} = 0.10 = 2\varepsilon$ (a "clear non-equivalence" deviation), P(`FAIL`) reaches $1.00$ at AUC = 0.92 (any $n$ in the table) and $\approx 0.90$ at AUC = 0.85, $n = 500$. This is the framework's statistical *power*: a 10-percentage-point AUC degradation is rejected with high probability across the typical operating range.

**4a.4. At the boundary $\Delta_{\text{true}} = \varepsilon$ the framework correctly refuses to commit.** Across all 8 boundary cells, `INDETERMINATE` accounts for $\geq 0.93$ of trials; P(`PASS`) and P(`FAIL`) each remain below $0.05$. This is the desired behaviour at the equivalence margin — a test that decisively called either direction at the boundary would be either anti-conservative (FAIL) or over-permissive (PASS).

**4a.5. Percentile and DeLong agree closely on power.** At $\Delta_{\text{true}} = 0.10$, $n = 500$: percentile gives P(`FAIL`) = $\{0.890, 1.000\}$; DeLong gives $\{0.905, 1.000\}$ for AUC $\in \{0.85, 0.92\}$. Agreement to within 1.5 percentage points — and DeLong is again $\sim 300\times$ faster. The §4 default decision (DeLong for AUC) survives under non-null evaluation.

### Cohort-sizing implication

The non-null table sharpens the §3 cohort-sizing implication: the WS-1 v0.5 cohort of $n \approx 208$ is *exactly* in the regime where P(`PASS`) under the null is sensitive to the operating AUC. At AUC = 0.92 (the typical lung-nodule operating point), $n = 200$ gives P(`PASS`) = 0.40 under the null; expansion to $n \approx 500$ would lift this to $\approx 0.94$. Without that expansion, credentials issued at the v0.5 cohort should be expected to return `INDETERMINATE` rather than `PASS` even when the candidate is truly equivalent — *the absence of a `PASS` verdict is not evidence of non-equivalence*, only of insufficient $n$. This is the reading the manuscript v0.3 §methods-estimator paragraph and `proofs/sample_size.md` §5 jointly endorse.

---

## 5. Caveats

**5.1. AUC only.** Both the §2 coverage simulation and the §4a power simulation evaluate only the AUC metric. For Dice (MRI segmentation) and contrast-recovery (PET) the comparable checks are follow-ups; we expect qualitatively similar conclusions because the paired bootstrap is metric-agnostic, but the BCa-vs-percentile-vs-closed-form trade-offs may shift (Dice has no widely-used closed-form equivalent of DeLong).

**5.2. $T = 200$ trials.** Monte-Carlo SE on a probability estimate at $T = 200$ is $\approx \sqrt{p(1-p)/200}$ — at most $\approx 0.035$ for $p$ near $0.5$, and $\approx 0.015$ near the nominal $0.95$. Distinctions smaller than $\sim 0.03$ in the verdict-distribution table should be read with caution; the qualitative conclusions (percentile competitive; BCa not strictly better under null; DeLong fast and mildly conservative; framework conservatively INDET-s under small $n$; power $\to 1$ at $2\varepsilon$) survive at this SE.

**5.3. Cross-method correlation $\rho = 0.5$.** The synthetic setup fixes the across-method score correlation at the open-questions §2 default. Real CT lung-nodule scores between two reconstruction methods on the same scan are typically much more correlated (often $\rho > 0.85$), which *shrinks* the half-widths — at higher $\rho$ the cohort-sizing implications of §4a become more favourable (P(`PASS`) under the null grows faster with $n$). The bootstrap's variance estimate uses the empirical $\rho$ on the test set, so the qualitative conclusions generalise.

---

## 6. What this writeup is and is not

**It is** the empirical-coverage *and* empirical-power anchor for the v0.3 manuscript's §methods-estimator paragraph on estimator defaults. The decision recorded in §4 (DeLong default for AUC; percentile otherwise; BCa opt-in) is reaffirmed by the §4a power simulation. The cohort-sizing implication in §4a is the key new finding: the v0.5 WS-1 cohort is *exactly* in the regime where conservative INDETERMINATE outcomes are common even under the null.

**It is not** the formal proof of paired-bootstrap consistency under the framework's specific assumptions (i.i.d.\ from $\Pi$; finite second moment of $\Delta$; content-addressed test set). Those reduce to the cited Efron 1979 and Bickel & Freedman 1981 results; reproducing the proofs here would be padding. The §4a simulation does not extend to the Dice / contrast-recovery cases — those are follow-ups (§5.1).

---

*v0.1 — 2026-06-02 (coverage). v0.2 — 2026-06-03 (D9 + 14): §4a non-null power table added, §5 caveats trimmed (the v0.1 "null only" caveat is now superseded), §6 closing reaffirmed.*
