"""dice_sim.py — combined coverage + power simulation for Dice-type metrics.

Extends the AUC coverage (`coverage_sim.py`) and power (`power_sim.py`)
simulations to a Dice-bounded paired-difference setting, closing the
*AUC-only* caveat in ``theory/proofs/estimator.md`` §5.1.

Generative model (matches the (S1) general-metric framework):
    Δ_k = a_k - b_k ~ Normal(Δ_true, σ_Δ²)

For Dice segmentation tasks the per-patient difference SD is empirically
σ_Δ ∈ [0.05, 0.10] at typical Dice means around 0.85; values outside that
range are unusual for clinically-meaningful segmentation tasks.

Cells:
    Δ_true      ∈ {0.00, 0.02, 0.05}     (under, at, past ε = 0.02 boundary)
    σ_Δ         ∈ {0.05, 0.10}
    n           ∈ {100, 200, 500}

Estimator: percentile bootstrap only (no Dice equivalent of DeLong's
closed-form AUC variance).

Output: ``dice_results.json`` (seed = 42) + stdout summary.

Note: ε = 0.02 is the v0.3 manuscript's *non-AUC* default (per V3-1);
AUC tasks use ε = 0.05.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np

CONFIG = {
    "delta_true_values": [0.00, 0.02, 0.05],
    "sigma_delta_values": [0.05, 0.10],
    "n_values": [100, 200, 500],
    "n_trials": 200,
    "n_bootstrap": 2000,
    "alpha": 0.05,
    "epsilon": 0.02,     # non-AUC default per manuscript v0.3 V3-1
    "seed": 42,
}


def percentile_ci(
    deltas: np.ndarray, alpha: float, n_bootstrap: int,
    rng: np.random.Generator,
):
    """Paired-bootstrap percentile CI for the mean of ``deltas``."""
    n = len(deltas)
    boots = np.empty(n_bootstrap)
    for b in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        boots[b] = deltas[idx].mean()
    lo = float(np.percentile(boots, 100 * alpha / 2))
    hi = float(np.percentile(boots, 100 * (1 - alpha / 2)))
    return float(deltas.mean()), lo, hi


def verdict_from_ci(lo, hi, epsilon):
    if -epsilon < lo and hi < epsilon:
        return "PASS"
    if hi <= -epsilon or lo >= epsilon:
        return "FAIL"
    return "INDETERMINATE"


@dataclass
class DiceCell:
    delta_true: float
    sigma_delta: float
    n: int
    n_trials: int
    epsilon: float
    # Coverage at Δ_true (should be ~1 - alpha across cells)
    coverage: float
    mean_half_width: float
    # Verdict distribution (power proxies)
    p_pass: float
    p_fail: float
    p_indeterminate: float
    mean_delta_observed: float


def run_cell(delta_true, sigma_delta, n, cfg, rng) -> DiceCell:
    n_trials = cfg["n_trials"]
    n_bootstrap = cfg["n_bootstrap"]
    alpha = cfg["alpha"]
    epsilon = cfg["epsilon"]

    covered = 0
    pass_n = 0
    fail_n = 0
    indet_n = 0
    half_widths = []
    deltas_obs = []
    for _ in range(n_trials):
        # Per-patient differences (S1 setting, bounded Dice via normal model)
        deltas = rng.normal(delta_true, sigma_delta, size=n)
        delta_hat, lo, hi = percentile_ci(deltas, alpha, n_bootstrap, rng)
        if lo <= delta_true <= hi:
            covered += 1
        v = verdict_from_ci(lo, hi, epsilon)
        if v == "PASS":
            pass_n += 1
        elif v == "FAIL":
            fail_n += 1
        else:
            indet_n += 1
        half_widths.append((hi - lo) / 2)
        deltas_obs.append(delta_hat)

    return DiceCell(
        delta_true=delta_true,
        sigma_delta=sigma_delta,
        n=n,
        n_trials=n_trials,
        epsilon=epsilon,
        coverage=covered / n_trials,
        mean_half_width=float(np.mean(half_widths)),
        p_pass=pass_n / n_trials,
        p_fail=fail_n / n_trials,
        p_indeterminate=indet_n / n_trials,
        mean_delta_observed=float(np.mean(deltas_obs)),
    )


def main():
    cfg = CONFIG
    master_rng = np.random.default_rng(cfg["seed"])
    cells = []
    n_cells = (len(cfg["delta_true_values"]) *
               len(cfg["sigma_delta_values"]) *
               len(cfg["n_values"]))
    print(f"Dice sim: {n_cells} cells; T = {cfg['n_trials']} × B = "
          f"{cfg['n_bootstrap']}; ε = {cfg['epsilon']}, α = {cfg['alpha']}\n")

    t0 = time.time()
    for d in cfg["delta_true_values"]:
        for s in cfg["sigma_delta_values"]:
            for n in cfg["n_values"]:
                sub_rng = np.random.default_rng(master_rng.integers(0, 2**32))
                t_cell = time.time()
                r = run_cell(d, s, n, cfg, sub_rng)
                cells.append(r)
                print(f"  Δ={d:.2f}  σ_Δ={s:.2f}  n={n:>3}  "
                      f"cov={r.coverage:.3f}  hw={r.mean_half_width:.4f}  "
                      f"P(PASS)={r.p_pass:.3f}  P(FAIL)={r.p_fail:.3f}  "
                      f"P(INDET)={r.p_indeterminate:.3f}  "
                      f"({time.time()-t_cell:.1f}s)")

    print(f"\nTotal: {time.time()-t0:.1f}s")

    out_path = Path(__file__).resolve().parent / "dice_results.json"
    with open(out_path, "w") as f:
        json.dump(
            {"config": cfg, "results": [asdict(c) for c in cells]},
            f, indent=2,
        )
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
