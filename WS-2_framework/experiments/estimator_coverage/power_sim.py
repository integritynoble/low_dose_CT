"""power_sim.py — statistical power of the paired-bootstrap signal-equivalence
estimator under controlled non-null shifts.

Companion to ``coverage_sim.py``. The coverage simulation verifies that, when
the two methods are truly equivalent (``Δ_true = 0``), the 95 % CI contains 0
in approximately 95 % of trials — the framework's *coverage* property. This
script verifies the complementary property — *power* — by shifting the
candidate method's positive-class score distribution to produce a known true
AUC difference ``Δ_true > 0`` and measuring how often the framework correctly
returns a ``FAIL`` verdict at the v0.3 canonical AUC default ``(ε = 0.05,
α = 0.05)``.

Expected behaviour:

* ``Δ_true = 0``:  P(PASS) ≈ 0.95, P(FAIL) ≈ 0, P(INDETERMINATE) ≈ 0.05.
* ``Δ_true = ε``:  the boundary case; verdict distribution depends on n and
  the CI variant. INDETERMINATE is the modal outcome.
* ``Δ_true > ε``:  P(FAIL) → 1 as n grows; this is the framework's power.

Cells:
    AUC_baseline  ∈ {0.85, 0.92}              (method B's population AUC)
    Δ_AUC_true    ∈ {0.00, 0.05, 0.10}        (population AUC offset of A vs B)
    n_per_class   ∈ {100, 250}                (total n ∈ {200, 500})
    CI variants   ∈ {percentile, delong}      (BCa skipped — opt-in per v0.3)

Output:
    power_results.json — frozen verdict-distribution per cell (seed = 42)
    stdout table       — human-readable summary
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
from scipy import stats

CONFIG = {
    "auc_baseline_values": [0.85, 0.92],
    "delta_auc_true_values": [0.00, 0.05, 0.10],
    "n_per_class_values": [100, 250],
    "ci_variants": ["percentile", "delong"],
    "n_trials": 200,
    "n_bootstrap": 2000,
    "alpha": 0.05,
    "epsilon": 0.05,
    "seed": 42,
}


# --------------------------------------------------------------------------
# Re-use the AUC + bootstrap + DeLong machinery from coverage_sim.py
# (duplicated here to keep this script standalone; the v0.2.0 library
# refactor will extract a shared module.)
# --------------------------------------------------------------------------

def auc(scores_pos: np.ndarray, scores_neg: np.ndarray) -> float:
    s_pos = scores_pos[:, None]
    s_neg = scores_neg[None, :]
    return float(((s_pos > s_neg).sum() + 0.5 * (s_pos == s_neg).sum()) /
                 (len(scores_pos) * len(scores_neg)))


def auc_components(scores_pos: np.ndarray, scores_neg: np.ndarray):
    s_pos = scores_pos[:, None]
    s_neg = scores_neg[None, :]
    indicator = (s_pos > s_neg).astype(np.float64) + 0.5 * (s_pos == s_neg)
    return indicator.mean(axis=1), indicator.mean(axis=0)


def delong_delta_ci(
    a_pos, a_neg, b_pos, b_neg, alpha,
):
    V10_A, V01_A = auc_components(a_pos, a_neg)
    V10_B, V01_B = auc_components(b_pos, b_neg)
    delta = float(V10_A.mean() - V10_B.mean())
    n_pos = len(a_pos)
    n_neg = len(a_neg)
    s10 = float(np.var(V10_A - V10_B, ddof=1)) if n_pos > 1 else 0.0
    s01 = float(np.var(V01_A - V01_B, ddof=1)) if n_neg > 1 else 0.0
    var = max(s10 / n_pos + s01 / n_neg, 0.0)
    half = stats.norm.isf(alpha / 2) * np.sqrt(var)
    return delta, delta - half, delta + half


def percentile_delta_ci(
    a_pos, a_neg, b_pos, b_neg, alpha, n_bootstrap, rng,
):
    n_pos = len(a_pos)
    n_neg = len(a_neg)
    delta_obs = auc(a_pos, a_neg) - auc(b_pos, b_neg)
    boots = np.empty(n_bootstrap)
    for b in range(n_bootstrap):
        ip = rng.integers(0, n_pos, n_pos)
        ineg = rng.integers(0, n_neg, n_neg)
        boots[b] = auc(a_pos[ip], a_neg[ineg]) - auc(b_pos[ip], b_neg[ineg])
    lo = float(np.percentile(boots, 100 * alpha / 2))
    hi = float(np.percentile(boots, 100 * (1 - alpha / 2)))
    return delta_obs, lo, hi


def verdict_from_ci(lo, hi, epsilon):
    if -epsilon < lo and hi < epsilon:
        return "PASS"
    if hi <= -epsilon or lo >= epsilon:
        return "FAIL"
    return "INDETERMINATE"


# --------------------------------------------------------------------------
# Data generation: paired binormal with controlled AUC offset
# --------------------------------------------------------------------------

def auc_to_mu(auc_target: float) -> float:
    return float(np.sqrt(2) * stats.norm.ppf(auc_target))


def simulate_non_null(
    auc_baseline: float,
    delta_auc_true: float,
    n_per_class: int,
    rng: np.random.Generator,
):
    """Paired binormal: method B has AUC = auc_baseline; method A has
    AUC = auc_baseline + delta_auc_true (achieved by shifting A's
    positive-class mean upward). Cross-method correlation rho = 0.5.

    True population Δ_AUC = delta_auc_true.
    """
    mu_b = auc_to_mu(auc_baseline)
    mu_a = auc_to_mu(auc_baseline + delta_auc_true)
    rho = 0.5
    cov = np.array([[1.0, rho], [rho, 1.0]])
    # Positive class: A and B see correlated noise but A's mean is mu_a, B's is mu_b
    pos = rng.multivariate_normal([mu_a, mu_b], cov, size=n_per_class)
    neg = rng.multivariate_normal([0.0, 0.0], cov, size=n_per_class)
    return pos[:, 0], neg[:, 0], pos[:, 1], neg[:, 1]


# --------------------------------------------------------------------------
# Per-cell trial loop
# --------------------------------------------------------------------------

@dataclass
class PowerCellResult:
    auc_baseline: float
    delta_auc_true: float
    n_per_class: int
    n_total: int
    ci_variant: str
    n_trials: int
    epsilon: float
    p_pass: float
    p_fail: float
    p_indeterminate: float
    mean_delta_observed: float
    mean_half_width: float


def run_cell(
    auc_baseline, delta_auc_true, n_per_class, ci_variant, cfg, rng,
) -> PowerCellResult:
    n_trials = cfg["n_trials"]
    alpha = cfg["alpha"]
    epsilon = cfg["epsilon"]

    pass_n = 0
    fail_n = 0
    indet_n = 0
    deltas_obs = []
    half_widths = []
    for _ in range(n_trials):
        a_pos, a_neg, b_pos, b_neg = simulate_non_null(
            auc_baseline, delta_auc_true, n_per_class, rng,
        )
        if ci_variant == "delong":
            delta, lo, hi = delong_delta_ci(a_pos, a_neg, b_pos, b_neg, alpha)
        elif ci_variant == "percentile":
            delta, lo, hi = percentile_delta_ci(
                a_pos, a_neg, b_pos, b_neg, alpha, cfg["n_bootstrap"], rng,
            )
        else:
            raise ValueError(ci_variant)
        v = verdict_from_ci(lo, hi, epsilon)
        if v == "PASS":
            pass_n += 1
        elif v == "FAIL":
            fail_n += 1
        else:
            indet_n += 1
        deltas_obs.append(delta)
        half_widths.append((hi - lo) / 2)

    return PowerCellResult(
        auc_baseline=auc_baseline,
        delta_auc_true=delta_auc_true,
        n_per_class=n_per_class,
        n_total=2 * n_per_class,
        ci_variant=ci_variant,
        n_trials=n_trials,
        epsilon=epsilon,
        p_pass=pass_n / n_trials,
        p_fail=fail_n / n_trials,
        p_indeterminate=indet_n / n_trials,
        mean_delta_observed=float(np.mean(deltas_obs)),
        mean_half_width=float(np.mean(half_widths)),
    )


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------

def main():
    cfg = CONFIG
    master_rng = np.random.default_rng(cfg["seed"])
    cells = []
    n_cells = (len(cfg["auc_baseline_values"]) *
               len(cfg["delta_auc_true_values"]) *
               len(cfg["n_per_class_values"]) *
               len(cfg["ci_variants"]))
    print(f"Cells: {n_cells}; T = {cfg['n_trials']} × B = {cfg['n_bootstrap']}; "
          f"ε = {cfg['epsilon']}, α = {cfg['alpha']}\n")

    t0 = time.time()
    for auc_b in cfg["auc_baseline_values"]:
        for d in cfg["delta_auc_true_values"]:
            for n_per in cfg["n_per_class_values"]:
                for ci in cfg["ci_variants"]:
                    sub_rng = np.random.default_rng(master_rng.integers(0, 2**32))
                    t_cell = time.time()
                    r = run_cell(auc_b, d, n_per, ci, cfg, sub_rng)
                    cells.append(r)
                    expected = "PASS" if d == 0 else (
                        "FAIL" if d > cfg["epsilon"] else "INDETERMINATE/boundary"
                    )
                    print(f"  AUC_b={auc_b:.2f}  Δ_true={d:.2f}  n={2*n_per:>3}  "
                          f"{ci:<10}  "
                          f"P(PASS)={r.p_pass:.3f}  "
                          f"P(FAIL)={r.p_fail:.3f}  "
                          f"P(INDET)={r.p_indeterminate:.3f}  "
                          f"(exp. {expected:<23} {time.time()-t_cell:.1f}s)")

    print(f"\nTotal: {time.time()-t0:.1f}s")

    out_path = Path(__file__).resolve().parent / "power_results.json"
    with open(out_path, "w") as f:
        json.dump(
            {"config": cfg, "results": [asdict(c) for c in cells]},
            f, indent=2,
        )
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
