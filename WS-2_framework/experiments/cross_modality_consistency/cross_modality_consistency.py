"""cross_modality_consistency.py — synthetic validation of the signal-equivalence
credential across three signal-reduction operators.

Demonstrates that the SAME paired-bootstrap code path
(``signal_equivalence_credential``) — modality-agnostic by construction —
returns the expected verdict when applied to:

* CT  (Poisson-thinning of photon counts)
* MRI (variable-density Cartesian k-space subsampling)
* PET (Poisson-thinning of list-mode counts)

For each modality two candidates are evaluated:

* "equivalent" — a candidate method whose score equals the reference method's
  score up to acquisition noise. The expected verdict is ``PASS``.
* "biased"     — a candidate method with a known additive bias > epsilon.
  The expected verdict is ``FAIL``.

Run::

    python3 cross_modality_consistency.py

Writes ``results.json`` alongside this file and prints a 6-row table to stdout.
The numbers reported in the WS-2 manuscript draft (Results section,
"Cross-modality consistency") are produced by this script at seed=42 and are
bit-for-bit reproducible.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable

import numpy as np

# --------------------------------------------------------------------------
# Modality-specific signal-reduction operators T_r
# --------------------------------------------------------------------------

def Tr_ct(s_ref: np.ndarray, r: float, rng: np.random.Generator) -> np.ndarray:
    """Poisson-thinning of full-signal photon counts at rate r (CT)."""
    return rng.binomial(s_ref.astype(np.int64), r)


def Tr_pet(s_ref: np.ndarray, r: float, rng: np.random.Generator) -> np.ndarray:
    """Poisson-thinning of list-mode counts at rate r (PET)."""
    return rng.binomial(s_ref.astype(np.int64), r)


def Tr_mri(s_ref: np.ndarray, r: float, rng: np.random.Generator) -> np.ndarray:
    """Variable-density Cartesian k-space mask retaining fraction r (MRI).

    Unsampled entries are NaN so the candidate method can ignore them without
    coupling the mask to a value-comparison heuristic.
    """
    n = s_ref.shape[-1]
    n_keep = max(1, int(np.ceil(r * n)))
    mask = np.zeros(n, dtype=bool)
    n_center = max(1, n_keep // 4)
    c0 = n // 2 - n_center // 2
    mask[c0 : c0 + n_center] = True
    edges = np.flatnonzero(~mask)
    n_extra = n_keep - n_center
    if n_extra > 0:
        extra = rng.choice(edges, size=n_extra, replace=False)
        mask[extra] = True
    out = np.full_like(s_ref, np.nan, dtype=np.float64)
    out[mask] = s_ref[mask]
    return out


# --------------------------------------------------------------------------
# Per-patient simulation
# --------------------------------------------------------------------------

BASE_COUNT_CT = 1000     # mean photon count per measurement at full dose
BASE_COUNT_PET = 800     # mean list-mode count per bin at full activity
N_MEAS = 64              # measurements per patient
MRI_SCALE = 0.10         # noise scale for MRI k-space measurements


def simulate_modality(
    modality: str,
    Tr_op: Callable,
    n_patients: int,
    r: float,
    candidate_bias: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Returns (a_k, b_k) per patient.

    a_k = candidate method's task score on T_r(S_ref(x_k))
    b_k = reference method's task score on S_ref(x_k)

    ``candidate_bias`` is added to a_k to create a known additive bias in
    the candidate's expected score — used for the FAIL-direction test.
    """
    a = np.empty(n_patients)
    b = np.empty(n_patients)
    for k in range(n_patients):
        x_k = rng.normal(0.0, 1.0)

        if modality == "CT":
            mean_ref = BASE_COUNT_CT * np.exp(0.1 * x_k)
            s_ref = rng.poisson(mean_ref, size=N_MEAS)
            s_red = Tr_op(s_ref, r, rng)
            b[k] = np.log(s_ref.mean() / BASE_COUNT_CT) / 0.1
            a[k] = (
                np.log(s_red.mean() / (BASE_COUNT_CT * r) + 1e-9) / 0.1
                + candidate_bias
            )

        elif modality == "PET":
            mean_ref = BASE_COUNT_PET * np.exp(0.1 * x_k)
            s_ref = rng.poisson(mean_ref, size=N_MEAS)
            s_red = Tr_op(s_ref, r, rng)
            b[k] = np.log(s_ref.mean() / BASE_COUNT_PET) / 0.1
            a[k] = (
                np.log(s_red.mean() / (BASE_COUNT_PET * r) + 1e-9) / 0.1
                + candidate_bias
            )

        elif modality == "MRI":
            s_ref = rng.normal(x_k, MRI_SCALE, size=N_MEAS)
            s_red = Tr_op(s_ref, r, rng)
            b[k] = s_ref.mean()
            a[k] = float(np.nanmean(s_red)) + candidate_bias

        else:
            raise ValueError(f"Unknown modality: {modality}")
    return a, b


# --------------------------------------------------------------------------
# The single, modality-agnostic credential code path
# --------------------------------------------------------------------------

@dataclass
class Credential:
    modality: str
    candidate: str
    r: float
    epsilon: float
    alpha: float
    n_test: int
    n_bootstrap: int
    delta_mean: float
    delta_ci_low: float
    delta_ci_high: float
    verdict: str


def signal_equivalence_credential(
    *,
    paired_a: np.ndarray,
    paired_b: np.ndarray,
    epsilon: float,
    alpha: float,
    n_bootstrap: int,
    rng: np.random.Generator,
) -> tuple[float, float, float, str]:
    """Paired-bootstrap credential. Identical code path for CT, MRI, PET.

    Returns (delta_mean, ci_lower, ci_upper, verdict).
    """
    deltas = paired_a - paired_b
    n = len(deltas)
    boot_means = np.empty(n_bootstrap)
    for b_idx in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        boot_means[b_idx] = deltas[idx].mean()
    lo = float(np.percentile(boot_means, 100 * alpha / 2))
    hi = float(np.percentile(boot_means, 100 * (1 - alpha / 2)))
    if -epsilon < lo and hi < epsilon:
        verdict = "PASS"
    elif hi <= -epsilon or lo >= epsilon:
        verdict = "FAIL"
    else:
        verdict = "INDETERMINATE"
    return float(deltas.mean()), lo, hi, verdict


# --------------------------------------------------------------------------
# Experiment driver
# --------------------------------------------------------------------------

CONFIG = {
    "n_patients": 200,
    "r": 0.25,
    "epsilon": 0.05,
    "alpha": 0.05,
    "n_bootstrap": 10_000,
    "seed": 42,
    "bias": 0.10,
}

MODALITIES: list[tuple[str, Callable]] = [
    ("CT", Tr_ct),
    ("MRI", Tr_mri),
    ("PET", Tr_pet),
]


def run() -> list[Credential]:
    cfg = CONFIG
    master_rng = np.random.default_rng(cfg["seed"])
    creds: list[Credential] = []

    for modality, Tr_op in MODALITIES:
        for label, bias in [("equivalent", 0.0), ("biased", cfg["bias"])]:
            sub_seed = int(master_rng.integers(0, 2**32))
            sub_rng = np.random.default_rng(sub_seed)
            a, b = simulate_modality(
                modality, Tr_op, cfg["n_patients"], cfg["r"], bias, sub_rng,
            )
            delta_mean, lo, hi, verdict = signal_equivalence_credential(
                paired_a=a, paired_b=b,
                epsilon=cfg["epsilon"], alpha=cfg["alpha"],
                n_bootstrap=cfg["n_bootstrap"], rng=sub_rng,
            )
            creds.append(Credential(
                modality=modality, candidate=label,
                r=cfg["r"], epsilon=cfg["epsilon"], alpha=cfg["alpha"],
                n_test=cfg["n_patients"], n_bootstrap=cfg["n_bootstrap"],
                delta_mean=delta_mean,
                delta_ci_low=lo, delta_ci_high=hi,
                verdict=verdict,
            ))
    return creds


def print_table(creds: list[Credential]) -> None:
    header = f"{'Modality':<10}{'Candidate':<14}{'delta_mean':>12}{'CI low':>12}{'CI high':>12}  Verdict"
    print(header)
    print("-" * len(header))
    for c in creds:
        print(
            f"{c.modality:<10}{c.candidate:<14}"
            f"{c.delta_mean:>12.4f}{c.delta_ci_low:>12.4f}{c.delta_ci_high:>12.4f}  {c.verdict}"
        )


def main() -> None:
    creds = run()
    print_table(creds)
    out_path = Path(__file__).resolve().parent / "results.json"
    with open(out_path, "w") as f:
        json.dump(
            {"config": CONFIG, "credentials": [asdict(c) for c in creds]},
            f,
            indent=2,
        )
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
