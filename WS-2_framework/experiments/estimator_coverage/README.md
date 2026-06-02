# Estimator coverage simulation

Empirical finite-sample coverage of the paired-bootstrap signal-equivalence estimator under three CI variants. Backs the `theory/proofs/estimator.md` decision on which estimator the `pwm_dose_equivalence` library defaults to.

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
python3 coverage_sim.py
```

Requires `numpy` and `scipy`. ~35 minutes wall time at the default config (T = 200, B = 2000). Writes `results.json` alongside the script; bit-for-bit reproducible from `seed = 42`.

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

1. **Percentile coverage is close to nominal across all cells** (range 0.915–0.975). No catastrophic anti-conservatism, even at the AUC ≈ 0.97 regime the v0.1 manuscript hedge had flagged.
2. **BCa does not robustly outperform percentile under the null.** At AUC = 0.97 / $n = 100$, BCa under-covers (0.900) vs percentile (0.935). The bias/acceleration corrections overcorrect when the bootstrap distribution is approximately symmetric.
3. **DeLong is mildly conservative and ~300× faster** at $n = 500$ (0.7 s vs ≥ 200 s for the bootstrap variants).

The library's recorded default:
* `percentile` for general use
* `delong` auto-selected when `task.metric == "auc"`
* `bca` opt-in only

---

## What this experiment is and is not

**It is** the empirical anchor for the `pwm_dose_equivalence` library's estimator-default decision.

**It is not** a substitute for the non-null power simulation (`open_questions §3` second deliverable, pending) or for the Dice / contrast-recovery coverage check (also pending).

---

## Cross-references

- [`../../theory/proofs/estimator.md`](../../theory/proofs/estimator.md) — formal writeup citing this table.
- [`../../theory/open_questions.md`](../../theory/open_questions.md) §3 — the question this simulation answers (in part).
- [`../cross_modality_consistency/`](../cross_modality_consistency/) — the *other* synthetic experiment, demonstrating the modality-general API; this one verifies the underlying estimator's coverage.
