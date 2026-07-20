"""Closed-form sample-size requirements.

Implements formulas (S1), (S3), (S4) from ``theory/proofs/sample_size.md``.
"""

from __future__ import annotations

import math

from scipy import stats


def required_n_general(*, epsilon: float, alpha: float, sigma_delta: float) -> int:
    """(S1) CLT-based sample size for a general metric.

    ``sigma_delta`` is the per-patient standard deviation of the difference
    ``Delta_k = a_k - b_k``. Returns the minimum n such that the bootstrap
    half-width fits inside the equivalence band at significance ``alpha``.
    """
    if sigma_delta < 0:
        raise ValueError("sigma_delta must be non-negative")
    if not (0 < alpha < 1):
        raise ValueError("alpha must be in (0, 1)")
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    z = float(stats.norm.isf(alpha / 2))
    return int(math.ceil((z / epsilon) ** 2 * sigma_delta ** 2))


def required_n_auc(
    *, epsilon: float, alpha: float, placement_sd: float,
) -> int:
    """(S3) Sample size for paired AUC.

    ``placement_sd`` is ``s`` in (S3) — the standard deviation of the DeLong
    placement-component difference ``V10_A - V10_B``, approximately equal for
    V10 and V01. Per ``theory/proofs/sample_size.md`` §3.2, empirical s values
    at rho = 0.5 are roughly:

    +-------+-------+
    | AUC   | s     |
    +=======+=======+
    | 0.85  | 0.20  |
    +-------+-------+
    | 0.92  | 0.15  |
    +-------+-------+
    | 0.97  | 0.08  |
    +-------+-------+
    """
    if placement_sd < 0:
        raise ValueError("placement_sd must be non-negative")
    if not (0 < alpha < 1):
        raise ValueError("alpha must be in (0, 1)")
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    z = float(stats.norm.isf(alpha / 2))
    return int(math.ceil((z / epsilon) ** 2 * 4 * placement_sd ** 2))


def required_n_bernstein(
    *, epsilon: float, alpha: float, sigma_delta: float, bound_M: float = 1.0,
) -> int:
    """(S4) Bernstein finite-sample bound for bounded ``|Delta_k| <= M``.

    Returns the minimum n such that

        Pr[|mean(Delta) - mu| > epsilon] <= alpha

    holds by Bernstein's inequality. Useful as a worst-case sanity check
    alongside the CLT bound, especially for small n.
    """
    if sigma_delta < 0 or bound_M < 0:
        raise ValueError("sigma_delta and bound_M must be non-negative")
    if not (0 < alpha < 1):
        raise ValueError("alpha must be in (0, 1)")
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    log_term = math.log(2 / alpha)
    numerator = 2 * sigma_delta ** 2 + (2 * bound_M * epsilon) / 3
    return int(math.ceil(log_term * numerator / epsilon ** 2))
