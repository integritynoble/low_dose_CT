"""coverage_sim.py — empirical coverage of the paired-bootstrap signal-equivalence
estimator under three CI variants (percentile / BCa / DeLong) on synthetic
paired AUC tasks.

For each (target AUC, n) cell, we simulate T trials of paired binormal
classification data under the null *truly-equivalent* configuration
(``true Δ = 0`` because both methods share the same score distribution).
Empirical coverage is the fraction of trials in which the 95 % CI for the
AUC difference contains the true Δ. Expected coverage is 0.95.

Cells:
    AUC ∈ {0.85, 0.92, 0.97}
    n_per_class ∈ {50, 100, 250}  (total n ∈ {100, 200, 500})
    CI variants ∈ {percentile, BCa, DeLong}

Outputs:
    results.json  — frozen empirical coverage per cell (seed=42)
    stdout table  — human-readable summary
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
from scipy import stats

CONFIG = {
    "auc_targets": [0.85, 0.92, 0.97],
    "n_per_class_values": [50, 100, 250],
    "ci_variants": ["percentile", "bca", "delong"],
    "n_trials": 200,
    "n_bootstrap": 2000,
    "alpha": 0.05,
    "seed": 42,
}


# --------------------------------------------------------------------------
# AUC and DeLong utilities — vectorised numpy
# --------------------------------------------------------------------------

def auc(scores_pos: np.ndarray, scores_neg: np.ndarray) -> float:
    """Mann-Whitney-U based AUC. Vectorised; handles ties via 0.5 weight."""
    # For each negative, count positives above (1) or equal (0.5)
    # Use broadcasting; for our sizes (n_pos, n_neg <= 250) this is fine.
    s_pos = scores_pos[:, None]
    s_neg = scores_neg[None, :]
    return float(((s_pos > s_neg).sum() + 0.5 * (s_pos == s_neg).sum()) /
                 (len(scores_pos) * len(scores_neg)))


def auc_components(scores_pos: np.ndarray, scores_neg: np.ndarray):
    """Return (V10, V01) — DeLong placement components per case.

    V10[i] = P(score_pos[i] > random negative); shape (n_pos,)
    V01[j] = P(random positive > score_neg[j]); shape (n_neg,)
    """
    s_pos = scores_pos[:, None]
    s_neg = scores_neg[None, :]
    indicator = (s_pos > s_neg).astype(np.float64) + 0.5 * (s_pos == s_neg)
    V10 = indicator.mean(axis=1)
    V01 = indicator.mean(axis=0)
    return V10, V01


def delong_ci(
    a_pos: np.ndarray, a_neg: np.ndarray,
    b_pos: np.ndarray, b_neg: np.ndarray,
    alpha: float,
):
    """Paired DeLong 1988 / Sun & Xu 2014 closed-form CI for AUC_A − AUC_B."""
    V10_A, V01_A = auc_components(a_pos, a_neg)
    V10_B, V01_B = auc_components(b_pos, b_neg)
    auc_A = V10_A.mean()
    auc_B = V10_B.mean()
    delta = float(auc_A - auc_B)
    n_pos = len(a_pos)
    n_neg = len(a_neg)
    # paired covariance components
    s10 = np.cov(V10_A - V10_B, ddof=1)
    s01 = np.cov(V01_A - V01_B, ddof=1)
    var = float(s10) / n_pos + float(s01) / n_neg
    if var < 0:  # numerical guard
        var = 0.0
    half = stats.norm.isf(alpha / 2) * np.sqrt(var)
    return delta, delta - half, delta + half


# --------------------------------------------------------------------------
# Bootstrap helpers
# --------------------------------------------------------------------------

def paired_bootstrap_auc_diff(
    a_pos: np.ndarray, a_neg: np.ndarray,
    b_pos: np.ndarray, b_neg: np.ndarray,
    n_bootstrap: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Return n_bootstrap resamples of (AUC_A − AUC_B).

    Resampling is paired-on-case independently within positives and negatives
    (the standard for paired-on-patient AUC bootstrap with class-stratified
    sampling — Carpenter & Bithell 2000).
    """
    n_pos = len(a_pos)
    n_neg = len(a_neg)
    boots = np.empty(n_bootstrap)
    for b in range(n_bootstrap):
        ip = rng.integers(0, n_pos, n_pos)
        ineg = rng.integers(0, n_neg, n_neg)
        boots[b] = auc(a_pos[ip], a_neg[ineg]) - auc(b_pos[ip], b_neg[ineg])
    return boots


def percentile_ci(boots: np.ndarray, alpha: float):
    lo = float(np.percentile(boots, 100 * alpha / 2))
    hi = float(np.percentile(boots, 100 * (1 - alpha / 2)))
    return lo, hi


def bca_ci(
    boots: np.ndarray, theta_hat: float,
    a_pos: np.ndarray, a_neg: np.ndarray,
    b_pos: np.ndarray, b_neg: np.ndarray,
    alpha: float,
):
    """BCa CI (Efron 1987). Uses bias-correction z0 and jackknife acceleration."""
    # Bias correction
    p_below = (boots < theta_hat).mean()
    if p_below <= 0 or p_below >= 1:
        # degenerate; fall back to percentile
        return percentile_ci(boots, alpha)
    z0 = stats.norm.ppf(p_below)

    # Jackknife (leave-one-out across cases; class-stratified)
    jk = []
    n_pos = len(a_pos)
    n_neg = len(a_neg)
    for i in range(n_pos):
        keep = np.r_[0:i, i + 1:n_pos]
        jk.append(auc(a_pos[keep], a_neg) - auc(b_pos[keep], b_neg))
    for j in range(n_neg):
        keep = np.r_[0:j, j + 1:n_neg]
        jk.append(auc(a_pos, a_neg[keep]) - auc(b_pos, b_neg[keep]))
    jk = np.array(jk)
    jk_bar = jk.mean()
    num = ((jk_bar - jk) ** 3).sum()
    den = 6 * (((jk_bar - jk) ** 2).sum()) ** 1.5
    a_accel = float(num / den) if den > 0 else 0.0

    za_lo = stats.norm.ppf(alpha / 2)
    za_hi = stats.norm.ppf(1 - alpha / 2)
    alpha_lo = stats.norm.cdf(z0 + (z0 + za_lo) / (1 - a_accel * (z0 + za_lo)))
    alpha_hi = stats.norm.cdf(z0 + (z0 + za_hi) / (1 - a_accel * (z0 + za_hi)))

    # Clip to (0, 1)
    alpha_lo = float(np.clip(alpha_lo, 1e-4, 1 - 1e-4))
    alpha_hi = float(np.clip(alpha_hi, 1e-4, 1 - 1e-4))

    lo = float(np.percentile(boots, 100 * alpha_lo))
    hi = float(np.percentile(boots, 100 * alpha_hi))
    return lo, hi


# --------------------------------------------------------------------------
# Data generation
# --------------------------------------------------------------------------

def auc_to_mu(auc_target: float) -> float:
    """Binormal: AUC = Φ(μ/√2), so μ = √2 · Φ⁻¹(AUC)."""
    return float(np.sqrt(2) * stats.norm.ppf(auc_target))


def simulate_paired(
    auc_target: float, n_per_class: int, rng: np.random.Generator,
):
    """Generate two methods' scores on the same paired cases, both with
    population AUC = auc_target and correlated noise (the methods are truly
    equivalent in distribution but observe shared cases). True Δ_AUC = 0.

    Positive-class scores: bivariate Normal(μ, μ); negative: bivariate Normal(0, 0)
    with correlation ρ = 0.5 across methods (the same ρ used in the WS-2
    open-questions §2 default).
    """
    mu = auc_to_mu(auc_target)
    rho = 0.5
    cov = np.array([[1.0, rho], [rho, 1.0]])
    pos = rng.multivariate_normal([mu, mu], cov, size=n_per_class)
    neg = rng.multivariate_normal([0.0, 0.0], cov, size=n_per_class)
    return pos[:, 0], pos[:, 1], neg[:, 0], neg[:, 1]


# --------------------------------------------------------------------------
# Per-cell trial
# --------------------------------------------------------------------------

@dataclass
class CellResult:
    auc_target: float
    n_per_class: int
    n_total: int
    ci_variant: str
    n_trials: int
    coverage: float
    mean_half_width: float


def run_cell(
    auc_target: float, n_per_class: int, ci_variant: str,
    cfg: dict, rng: np.random.Generator,
) -> CellResult:
    n_trials = cfg["n_trials"]
    n_bootstrap = cfg["n_bootstrap"]
    alpha = cfg["alpha"]
    true_delta = 0.0

    covered = 0
    half_widths = []
    for _t in range(n_trials):
        a_pos, b_pos, a_neg, b_neg = simulate_paired(auc_target, n_per_class, rng)
        if ci_variant == "delong":
            theta_hat, lo, hi = delong_ci(a_pos, a_neg, b_pos, b_neg, alpha)
        else:
            theta_hat = auc(a_pos, a_neg) - auc(b_pos, b_neg)
            boots = paired_bootstrap_auc_diff(
                a_pos, a_neg, b_pos, b_neg, n_bootstrap, rng,
            )
            if ci_variant == "percentile":
                lo, hi = percentile_ci(boots, alpha)
            elif ci_variant == "bca":
                lo, hi = bca_ci(boots, theta_hat,
                                a_pos, a_neg, b_pos, b_neg, alpha)
            else:
                raise ValueError(ci_variant)
        if lo <= true_delta <= hi:
            covered += 1
        half_widths.append((hi - lo) / 2)

    return CellResult(
        auc_target=auc_target,
        n_per_class=n_per_class,
        n_total=2 * n_per_class,
        ci_variant=ci_variant,
        n_trials=n_trials,
        coverage=covered / n_trials,
        mean_half_width=float(np.mean(half_widths)),
    )


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------

def main():
    cfg = CONFIG
    master_rng = np.random.default_rng(cfg["seed"])
    results = []
    print(f"Cells: {len(cfg['auc_targets'])}×{len(cfg['n_per_class_values'])}"
          f"×{len(cfg['ci_variants'])} = "
          f"{len(cfg['auc_targets']) * len(cfg['n_per_class_values']) * len(cfg['ci_variants'])}; "
          f"{cfg['n_trials']} trials × {cfg['n_bootstrap']} bootstrap each\n")

    t0 = time.time()
    for auc_t in cfg["auc_targets"]:
        for n_per in cfg["n_per_class_values"]:
            for ci in cfg["ci_variants"]:
                sub_rng = np.random.default_rng(master_rng.integers(0, 2**32))
                t_cell = time.time()
                r = run_cell(auc_t, n_per, ci, cfg, sub_rng)
                results.append(r)
                print(f"  AUC={auc_t:.2f}  n={2*n_per:>3}  {ci:<10}  "
                      f"coverage={r.coverage:.3f}  "
                      f"mean half-width={r.mean_half_width:.4f}  "
                      f"({time.time()-t_cell:.1f}s)")

    print(f"\nTotal: {time.time()-t0:.1f}s")

    out_path = Path(__file__).resolve().parent / "results.json"
    with open(out_path, "w") as f:
        json.dump(
            {"config": cfg, "results": [asdict(r) for r in results]},
            f, indent=2,
        )
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
