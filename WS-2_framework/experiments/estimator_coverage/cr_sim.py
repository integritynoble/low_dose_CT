"""cr_sim.py — combined coverage + power simulation for PET phantom
contrast-recovery (CR) metrics.

Mirrors `dice_sim.py` but tuned for the NEMA NU-2 IQ-phantom CR setting:

* Smaller per-trial σ_Δ values (0.02, 0.05) reflecting physical-phantom
  statistics — CR differences between two reconstruction methods on the
  same phantom acquisition are tighter than between-patient Dice differences
  because the phantom does not move and the metric is a deterministic
  geometric ratio.

* Smaller n values (6, 12, 30, 60) reflecting per-credential phantom-
  acquisition cohort sizes — a single NEMA NU-2 IQ phantom acquisition has
  6 spheres, so n = 6 is "one acquisition", n = 12 is "two acquisitions",
  n = 30 is "five acquisitions" (a realistic worked-example cohort), and
  n = 60 is "ten acquisitions" (the upper end of a single-site phantom
  validation study).

* ε = 0.02 (non-AUC default per manuscript v0.3 V3-1).

Together with `coverage_sim.py` (AUC) and `dice_sim.py` (Dice), this
closes the per-modality coverage trio (CT lung-nodule AUC; MRI knee-
meniscus Dice; PET phantom CR) and the §5.1 "AUC + Dice; CR pending"
caveat in ``theory/proofs/estimator.md``.

Generative model: per-sphere differences Δ_k ~ Normal(Δ_true, σ_Δ²) —
the (S1) general-metric setting from ``theory/proofs/sample_size.md``.

Cells:
    Δ_true      ∈ {0.00, 0.02, 0.05}     (under, at, past ε = 0.02 boundary)
    σ_Δ         ∈ {0.02, 0.05}
    n           ∈ {6, 12, 30, 60}

Estimator: percentile bootstrap only (no CR analog of DeLong).

Output: ``cr_results.json`` (seed = 42) + stdout summary.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np

CONFIG = {
    "delta_true_values": [0.00, 0.02, 0.05],
    "sigma_delta_values": [0.02, 0.05],
    "n_values": [6, 12, 30, 60],
    "n_trials": 200,
    "n_bootstrap": 2000,
    "alpha": 0.05,
    "epsilon": 0.02,
    "seed": 42,
}


def percentile_ci(deltas, alpha, n_bootstrap, rng):
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
class CRCell:
    delta_true: float
    sigma_delta: float
    n: int
    n_trials: int
    epsilon: float
    coverage: float
    mean_half_width: float
    p_pass: float
    p_fail: float
    p_indeterminate: float
    mean_delta_observed: float


def run_cell(delta_true, sigma_delta, n, cfg, rng) -> CRCell:
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

    return CRCell(
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
    print(f"CR sim: {n_cells} cells; T = {cfg['n_trials']} × B = "
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

    out_path = Path(__file__).resolve().parent / "cr_results.json"
    with open(out_path, "w") as f:
        json.dump(
            {"config": cfg, "results": [asdict(c) for c in cells]},
            f, indent=2,
        )
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
