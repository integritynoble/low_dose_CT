"""Paired-bootstrap and closed-form DeLong CI estimators.

Default selection per ``theory/proofs/estimator.md`` (2026-06-02 decision):

* ``percentile`` — paired bootstrap on case identifiers; coverage close to
  nominal across all tested AUC × n cells.
* ``delong`` — auto-selected for ``Task.metric == "auc"``; ~300× faster than
  bootstrap with mild conservativeness.

BCa is not yet exposed in v0.1 (opt-in deferred to v0.2.0 per the
estimator-coverage findings).
"""

from __future__ import annotations

from typing import Literal

import numpy as np
from scipy import stats


# --------------------------------------------------------------------------
# Generic paired-bootstrap (any metric where Δ_k is a per-patient scalar)
# --------------------------------------------------------------------------

def percentile_ci(
    deltas: np.ndarray,
    *,
    alpha: float,
    n_bootstrap: int,
    rng: np.random.Generator,
) -> tuple[float, float, float, np.ndarray]:
    """Paired bootstrap percentile CI for ``E[delta]``.

    ``deltas`` is the array of per-case differences ``a_k - b_k`` for the
    candidate-minus-reference scores. The bootstrap resamples cases
    (paired-on-patient) with replacement and reports the central ``1 - alpha``
    percentile interval of the bootstrap means.

    Returns ``(observed_mean, ci_lower, ci_upper, bootstrap_means)``.
    """
    n = len(deltas)
    if n == 0:
        raise ValueError("empty deltas array")
    boots = np.empty(n_bootstrap)
    for b in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        boots[b] = deltas[idx].mean()
    lo = float(np.percentile(boots, 100 * alpha / 2))
    hi = float(np.percentile(boots, 100 * (1 - alpha / 2)))
    return float(deltas.mean()), lo, hi, boots


# --------------------------------------------------------------------------
# Closed-form paired DeLong CI (AUC only)
# --------------------------------------------------------------------------

def _auc_components(
    scores_pos: np.ndarray, scores_neg: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """DeLong placement components (V10 per positive case, V01 per negative)."""
    s_pos = scores_pos[:, None]
    s_neg = scores_neg[None, :]
    indicator = (s_pos > s_neg).astype(np.float64) + 0.5 * (s_pos == s_neg)
    V10 = indicator.mean(axis=1)
    V01 = indicator.mean(axis=0)
    return V10, V01


def delong_ci(
    *,
    a_pos: np.ndarray,
    a_neg: np.ndarray,
    b_pos: np.ndarray,
    b_neg: np.ndarray,
    alpha: float,
) -> tuple[float, float, float]:
    """Paired DeLong 1988 / Sun & Xu 2014 CI for ``AUC_A - AUC_B``.

    ``a_pos / a_neg`` are the candidate method's scores on positive / negative
    cases; ``b_pos / b_neg`` are the reference method's scores on *the same
    cases* (paired-on-patient). Returns ``(delta, ci_lower, ci_upper)``.
    """
    V10_A, V01_A = _auc_components(a_pos, a_neg)
    V10_B, V01_B = _auc_components(b_pos, b_neg)
    auc_A = float(V10_A.mean())
    auc_B = float(V10_B.mean())
    delta = auc_A - auc_B
    n_pos = len(a_pos)
    n_neg = len(a_neg)
    s10 = float(np.var(V10_A - V10_B, ddof=1)) if n_pos > 1 else 0.0
    s01 = float(np.var(V01_A - V01_B, ddof=1)) if n_neg > 1 else 0.0
    var = s10 / n_pos + s01 / n_neg
    if var < 0:
        var = 0.0
    half = float(stats.norm.isf(alpha / 2)) * np.sqrt(var)
    return delta, delta - half, delta + half


# --------------------------------------------------------------------------
# Verdict from a CI
# --------------------------------------------------------------------------

Verdict = Literal["PASS", "FAIL", "INDETERMINATE"]


def verdict_from_ci(ci_low: float, ci_high: float, epsilon: float) -> Verdict:
    """Three-way verdict per the framework definition.

    ``PASS`` iff the CI is strictly inside ``(-epsilon, epsilon)``;
    ``FAIL`` iff the CI is disjoint from ``(-epsilon, epsilon)``;
    ``INDETERMINATE`` otherwise.
    """
    if -epsilon < ci_low and ci_high < epsilon:
        return "PASS"
    if ci_high <= -epsilon or ci_low >= epsilon:
        return "FAIL"
    return "INDETERMINATE"
