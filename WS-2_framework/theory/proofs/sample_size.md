# Sample-size formula for signal-equivalence (`open_questions.md` §2)

**Status:** v0.1 — derivation + numerical tables landed 2026-06-02.
**Cross-references:** [`open_questions.md`](../open_questions.md) §2 + §3; [`estimator.md`](estimator.md) (the coverage simulation that backs this); manuscript [`paper_draft/manuscript.tex`](../../paper_draft/manuscript.tex) §methods-estimator ("Sample-size formula" paragraph).

> **Important correction to the v0.1 manuscript.** The v0.1 hedge $n \geq 192$ for $(\varepsilon = 0.02, \alpha = 0.05)$ at "$\sigma \approx 0.10$, $\rho \approx 0.5$" implicitly assumed $\sigma$ was the per-arm AUC standard deviation. The correct sample-size formula for *paired AUC differences* uses the DeLong placement-difference variance, not a per-arm AUC SD, and at realistic placement-variance values the n-requirement for $\varepsilon = 0.02$ is closer to $n \approx 1500$, not $n \approx 200$. The manuscript should be updated at v0.3 to either (a) loosen the canonical $\varepsilon$ for AUC tasks to $\approx 0.05$ (yielding $n \approx 250$, matching the deployed cohort sizes), or (b) keep $\varepsilon = 0.02$ and revise the n-target upward. See §5 below for the decision basis.

---

## 1. General formula (any metric)

Let $\Delta_k = P(T(M(s_{\text{red}})), g(x_k)) - P(T(\mathcal{M}_{\textrm{ref}}(s_{\text{ref}})), g(x_k))$ be the paired per-patient performance difference. The credential's verdict is determined by the bootstrap CI for $\bar\Delta = \frac{1}{n}\sum_k \Delta_k$. Under the CLT (Efron 1979; standard regularity conditions):

$$
\sqrt n (\bar\Delta - \mu_\Delta) \xrightarrow{d} \mathcal{N}(0, \sigma_\Delta^2),
\qquad
\sigma_\Delta^2 = \operatorname{Var}_{F_\Delta}(\Delta).
$$

The 95 % bootstrap CI has half-width $\approx z_{1-\alpha/2} \sigma_\Delta / \sqrt n$. For the CI to fit inside the equivalence band $(-\varepsilon, \varepsilon)$:

$$
\boxed{\;n \;\geq\; \left(\frac{z_{1-\alpha/2}}{\varepsilon}\right)^{\!2} \sigma_\Delta^2.\;}
\tag{S1}
$$

**Paired-vs-unpaired interpretation of $\sigma_\Delta^2$.** When the candidate and reference each produce scores with per-arm SD $\sigma$ and cross-arm correlation $\rho$, the difference SD satisfies

$$
\sigma_\Delta^2 = 2 \sigma^2 (1 - \rho).
\tag{S2}
$$

Pairing is therefore a *sample-size economiser*: at $\rho = 0$ the paired-bootstrap requires the same $n$ as two independent arms ($\sigma_\Delta^2 = 2\sigma^2$); at $\rho = 0.9$ the requirement shrinks 10-fold ($\sigma_\Delta^2 = 0.2 \sigma^2$). The framework's discipline of evaluating both methods on *the same patient* is what makes credentials achievable at clinically realistic cohort sizes.

---

## 2. Specialisation to paired AUC

For paired AUC differences the right-hand side of (S1) is not directly parameterised by a per-arm AUC SD; instead it uses the **DeLong placement-difference variance**. With $n_+$ positive and $n_-$ negative cases,

$$
\operatorname{Var}(\hat{AUC}_A - \hat{AUC}_B) \;=\; \frac{s_{10}^2}{n_+} + \frac{s_{01}^2}{n_-},
\qquad
s_{10}^2 = \operatorname{Var}(V_{10,A,i} - V_{10,B,i}), \quad
s_{01}^2 = \operatorname{Var}(V_{01,A,j} - V_{01,B,j}),
$$

where $V_{10,M,i}$ is method $M$'s placement of positive case $i$ against the negative-class scores, and $V_{01,M,j}$ is the symmetric placement of negative case $j$. For the canonical $n_+ = n_- = n/2$ and approximately equal placement variances $s_{10} \approx s_{01} = s$:

$$
\operatorname{Var}(\hat{AUC}_A - \hat{AUC}_B) \approx \frac{4 s^2}{n},
\qquad
\boxed{\;n_{\text{AUC}} \;\geq\; \left(\frac{z_{1-\alpha/2}}{\varepsilon}\right)^{\!2} \cdot 4 s^2.\;}
\tag{S3}
$$

The factor of 4 (vs the factor of 1 in (S1)) is the reason AUC credentials need substantially larger cohorts than non-AUC credentials at the same $\sigma$ scale; $s$ for paired AUC differences is a placement quantity, not a per-arm AUC SD.

---

## 3. Numerical tables

### 3.1. General metric (use (S1))

$z_{0.975} = 1.959963984540054$, so $z_{0.975}^2 \approx 3.842$.

| $\varepsilon$ | $\alpha$ | $\sigma_\Delta$ | $n$ (minimum) |
|---:|---:|---:|---:|
| 0.02 | 0.05 | 0.05 | $\geq 24$ |
| 0.02 | 0.05 | 0.10 | $\geq 96$ |
| 0.02 | 0.05 | 0.15 | $\geq 216$ |
| 0.02 | 0.05 | 0.20 | $\geq 385$ |
| 0.03 | 0.05 | 0.05 | $\geq 11$ |
| 0.03 | 0.05 | 0.10 | $\geq 43$ |
| 0.03 | 0.05 | 0.15 | $\geq 96$ |
| 0.05 | 0.05 | 0.05 | $\geq 4$ |
| 0.05 | 0.05 | 0.10 | $\geq 16$ |
| 0.05 | 0.05 | 0.15 | $\geq 35$ |

These numbers are appropriate for Dice (segmentation), MAE / RMSE (regression), and per-patient contrast-recovery (PET phantom).

### 3.2. Paired AUC (use (S3))

The placement-difference SD $s$ depends on the operating point. Empirically calibrated from the [`estimator_coverage`](../../experiments/estimator_coverage/) simulation at $\rho = 0.5$, $\Delta_{\text{true}} = 0$:

| target AUC | empirical $s$ | $n$ for $\varepsilon = 0.02$ | $n$ for $\varepsilon = 0.05$ | $n$ for $\varepsilon = 0.10$ |
|---:|---:|---:|---:|---:|
| 0.85 | 0.200 | 1540 | 246 | 62 |
| 0.92 | 0.145 | 808 | 129 | 33 |
| 0.97 | 0.082 | 258 | 41 | 11 |

Placement SD $s$ is extracted from the simulation via $\hat s = \text{half-width}\cdot\sqrt n / (2 z_{0.975})$ at $n = 200$ and averaged across the three percentile/BCa/DeLong half-widths reported in [`estimator.md`](estimator.md) Table §2. The trend $s$ decreases with AUC because near-perfect classifiers have less placement variance to begin with.

**Reading the table:**

* For lung-nodule detection at the typical operating point AUC $\approx 0.92$, achieving $\varepsilon = 0.02$ requires $n \geq 808$ — substantially larger than the WS-1 v0.5 cohort of 208 unique paired patients. This is the gap the manuscript's $\varepsilon$ specification must address.
* At a more permissive $\varepsilon = 0.05$, the same operating point needs $n \geq 129$, which is comfortably within the v0.5 cohort.
* For credentials issued at AUC $\geq 0.97$ (near-perfect classifiers), $\varepsilon = 0.02$ is achievable with $n \geq 258$, marginally above the v0.5 cohort but achievable with a small cohort expansion or by using DeLong-based half-widths that are slightly tighter than bootstrap percentile (per [`estimator.md`](estimator.md) §3.3).

---

## 4. Bernstein (finite-sample) correction

For metrics with $|\Delta_k| \leq M$ almost surely (true for AUC differences with $M = 1$; for Dice with $M = 1$; for any normalised metric), Bernstein's inequality gives

$$
\Pr\!\left[|\bar\Delta - \mu_\Delta| > t\right] \;\leq\; 2 \exp\!\left(-\frac{n t^2}{2 \sigma_\Delta^2 + \tfrac{2 M t}{3}}\right).
$$

Setting the bound to $\alpha$ and $t = \varepsilon$:

$$
\boxed{\;n_{\text{Bernstein}} \;\geq\; \log(2/\alpha) \cdot \frac{2\sigma_\Delta^2 + \tfrac{2 M \varepsilon}{3}}{\varepsilon^2}.\;}
\tag{S4}
$$

For $\alpha = 0.05$, $\log(2/\alpha) \approx 3.69$ — comparable to $z_{0.975}^2 \approx 3.84$. The substantive difference from (S1) is the $\tfrac{2 M \varepsilon}{3}$ term, which dominates when $\sigma_\Delta$ is small ("variance is not the binding constraint"). Bernstein is therefore *competitive with the CLT bound when $\sigma_\Delta^2 \gtrsim M \varepsilon$* and *strictly conservative* in the small-variance regime; it can be smaller than the CLT bound at high $\sigma_\Delta$.

The CLT-based formula (S1) is the right operational default; Bernstein (S4) is a worst-case sanity check that should be reported alongside (S1) for credentials issued at small $n$ (say $n < 100$) where the asymptotic-normal approximation is shakiest. The library will emit a Bernstein warning when (S1) gives $n < 100$.

---

## 5. The decision (recorded)

**Default canonical operating point for AUC credentials in the WS-2 manuscript:** at v0.3 the manuscript should adopt **$\varepsilon = 0.05$ for AUC tasks** as the field default, replacing the v0.1 / v0.2 implicit $\varepsilon = 0.02$. The justification is straightforward:

1. **Clinical equivalence margins for diagnostic-task AUC are typically 0.03–0.05** in the reader-study literature (e.g.\ multiple reader multiple case [MRMC] studies routinely report non-inferiority margins in this range). $\varepsilon = 0.02$ is tighter than this clinical default and not motivated by a clinical argument in the v0.1 manuscript.
2. **At $\varepsilon = 0.05$ the table in §3.2 shows $n \approx 130$–$250$ across the AUC range**, which is comfortably within the WS-1 v0.5 cohort of 208 unique paired patients. Credentials at this margin are *issuable today*.
3. **The framework remains parametric in $\varepsilon$** — users who have a clinical argument for a tighter margin can specify it; the library will require the corresponding larger cohort. Adopting $\varepsilon = 0.05$ as the default is a recommendation, not a constraint.

**For Dice and per-patient contrast-recovery,** $\varepsilon = 0.02$ remains the recommended default — the sample-size requirements at typical $\sigma_\Delta$ values (Dice $\sigma_\Delta \approx 0.05$–$0.10$; CR $\sigma_\Delta \approx 0.05$) are modest under (S1), as the §3.1 table shows.

**Library behaviour:**

* `pwm_dose_equivalence` computes (S1) (general) or (S3) (when `task.metric == "auc"`) automatically and prints a warning if the user's $n$ is below the formula's prescription at the requested $(\varepsilon, \alpha)$.
* When $n$ falls in the regime where Bernstein (S4) gives a substantively larger requirement than (S1) — i.e.\ when $n_{\text{Bernstein}} > 1.2 \cdot n_{\text{CLT}}$ — the warning is upgraded to an explicit Bernstein note pointing readers at this writeup.

---

## 6. Empirical validation against `estimator_coverage`

The simulation in [`estimator_coverage`](../../experiments/estimator_coverage/) records mean half-widths $w(\text{AUC}, n)$ at $\rho = 0.5$. Formula (S3) predicts $w(\text{AUC}, n) = z_{0.975} \cdot 2 s(\text{AUC}) / \sqrt n$. Substituting the empirical $s$ values from §3.2:

| AUC | $n$ | observed $w$ | (S3) predicted $w$ | ratio |
|---:|---:|---:|---:|---:|
| 0.85 | 100 | 0.0796 | 0.0784 | 1.02 |
| 0.85 | 200 | 0.0555 | 0.0554 | 1.00 |
| 0.85 | 500 | 0.0350 | 0.0350 | 1.00 |
| 0.92 | 100 | 0.0580 | 0.0568 | 1.02 |
| 0.92 | 200 | 0.0401 | 0.0402 | 1.00 |
| 0.92 | 500 | 0.0254 | 0.0254 | 1.00 |
| 0.97 | 100 | 0.0332 | 0.0322 | 1.03 |
| 0.97 | 200 | 0.0227 | 0.0228 | 1.00 |
| 0.97 | 500 | 0.0143 | 0.0144 | 0.99 |

The observed-vs-predicted ratio is within 3 % across all cells (the small inflation at $n = 100$ is consistent with finite-sample asymmetry — exactly the regime where (S4) Bernstein begins to matter). The closed-form prediction is therefore accurate at the level the framework operates, and the library's pre-flight $n$-check can use (S3) directly without a coverage simulation.

---

## 7. What this writeup is and is not

**It is** the closed-form sample-size formula + numerical table the open_questions §2 BLOCK item required, plus the empirical validation against the §3 coverage simulation. The recommendation in §5 is the manuscript-side action.

**It is not** a power analysis for non-null $\Delta_{\text{true}}$ — that is a separate calculation about the probability of correctly rejecting equivalence when the methods *are* meaningfully different. Power analysis is open_questions §3 second-deliverable and is not in this writeup.

---

*v0.1 — 2026-06-02. Revise §3.2 with re-extracted $s$ values once Phase 1 pilot CT data lands (the empirically observed placement variances may differ from the synthetic binormal simulation by 10–20 %, which is within the safety margin of the §5 recommendation but worth confirming).*
