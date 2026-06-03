# Estimator coverage + power simulations

Two empirical simulations of the paired-bootstrap signal-equivalence estimator. The **coverage** simulation (`coverage_sim.py`) verifies that the 95 % CI covers the true $\Delta$ at nominal rate under the truly-equivalent null. The **power** simulation (`power_sim.py`) verifies that the verdict distribution behaves correctly under non-null shifts ($\Delta_{\text{true}} \in \{0, \varepsilon, 2\varepsilon\}$). Together they back the `theory/proofs/estimator.md` decision on the library's estimator defaults and the cohort-sizing implications of `theory/proofs/sample_size.md` §5.

---

## What it does

For each (target AUC, $n$) cell, simulates $T = 200$ trials of paired binormal classification under the truly-equivalent null configuration (both methods share the same score distribution, so true $\Delta_{\text{AUC}} = 0$). For each trial, computes a 95% CI for $\Delta_{\text{AUC}}$ using each of three estimators:

| Estimator | Source | Cost |
|---|---|---|
| `percentile` | Efron 1979 paired bootstrap, percentile-based CI | $O(B \cdot n)$ |
| `bca` | Efron 1987 bias-corrected accelerated, with class-stratified jackknife | $O(B \cdot n + n^2)$ |
| `delong` | DeLong, DeLong & Clarke-Pearson 1988 closed-form normal approximation | $O(n^2)$ |

Coverage = fraction of trials in which the CI contains $0$. Expected coverage = 0.95.

**Cells:** AUC $\in \{0.85, 0.92, 0.97\}$ × $n \in \{100, 200, 500\}$ × 3 estimators = 27 cells.

---

## Run

```bash
python3 coverage_sim.py    # ~35 min; writes results.json
python3 power_sim.py       # ~25 min; writes power_results.json
```

Requires `numpy` and `scipy`. Both scripts are bit-for-bit reproducible from `seed = 42`.

---

## Result at seed = 42 (excerpt)

| Target AUC | $n$ | percentile | BCa | DeLong |
|---:|---:|---:|---:|---:|
| 0.85 | 100 | 0.940 | 0.925 | 0.965 |
| 0.85 | 500 | 0.945 | 0.950 | 0.960 |
| 0.92 | 100 | 0.915 | 0.905 | 0.930 |
| 0.92 | 500 | 0.925 | 0.930 | 0.940 |
| 0.97 | 100 | 0.935 | 0.900 | 0.970 |
| 0.97 | 500 | 0.975 | 0.935 | 0.975 |

Full 27-cell table and discussion in [`../../theory/proofs/estimator.md`](../../theory/proofs/estimator.md).

---

## Headline conclusions

**Coverage (under the null, $\Delta_{\text{true}} = 0$):**

1. **Percentile coverage is close to nominal across all cells** (range 0.915–0.975). No catastrophic anti-conservatism, even at the AUC ≈ 0.97 regime the v0.1 manuscript hedge had flagged.
2. **BCa does not robustly outperform percentile under the null.** At AUC = 0.97 / $n = 100$, BCa under-covers (0.900) vs percentile (0.935).
3. **DeLong is mildly conservative and ~300× faster** at $n = 500$ (0.7 s vs ≥ 200 s for the bootstrap variants).

**Power (under non-null shifts):**

4. **The framework conservatively returns INDETERMINATE rather than over-committing under small $n$.** Under the null at AUC = 0.85, $n = 200$: P(`PASS`) ≈ 0.01, P(`INDET`) ≈ 0.99. The CI is correctly centred but its half-width exceeds $\varepsilon$.
5. **At realistic operating points, P(`PASS`) under the null hits nominal.** AUC = 0.92, $n = 500$ gives P(`PASS`) ≈ 0.94.
6. **Power at $2\varepsilon$ is excellent.** P(`FAIL`) = 1.00 at AUC = 0.92 (any $n$); ≈ 0.90 at AUC = 0.85, $n = 500$.
7. **At the boundary $\Delta_{\text{true}} = \varepsilon$**, INDETERMINATE dominates (≥ 0.93) — the framework correctly refuses to commit.

**Combined library-default decision:**
* `percentile` for general use
* `delong` auto-selected when `task.metric == "auc"`
* `bca` opt-in only

**Combined cohort-sizing implication:** the WS-1 v0.5 cohort ($n \approx 208$) at the typical AUC ≈ 0.92 lung-nodule operating point is *exactly* in the regime where P(`PASS`) under the null is sensitive to $n$. Expansion to $n \approx 500$ would lift the typical null verdict from ~40 % PASS to ~94 % PASS. Below that, expect INDETERMINATE-but-truly-equivalent outcomes; absence of `PASS` is not evidence of non-equivalence.

---

## What these experiments are and are not

**They are** the empirical anchor for the `pwm_dose_equivalence` library's estimator-default decision and for the cohort-sizing guidance in `theory/proofs/sample_size.md` §5.

**They are not** a substitute for the Dice / contrast-recovery coverage and power checks (both pending; would extend the simulations to non-AUC metrics). The library's defaults are AUC-anchored; the percentile bootstrap is the conservative choice for any other metric until the equivalent simulation lands.

---

## Cross-references

- [`../../theory/proofs/estimator.md`](../../theory/proofs/estimator.md) — formal writeup citing this table.
- [`../../theory/open_questions.md`](../../theory/open_questions.md) §3 — the question this simulation answers (in part).
- [`../cross_modality_consistency/`](../cross_modality_consistency/) — the *other* synthetic experiment, demonstrating the modality-general API; this one verifies the underlying estimator's coverage.
