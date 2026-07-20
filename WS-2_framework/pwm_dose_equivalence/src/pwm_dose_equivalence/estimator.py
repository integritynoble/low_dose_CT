"""Paired-bootstrap and closed-form DeLong CI estimators.

Default selection per ``theory/proofs/estimator.md`` (2026-06-02 decision):

* ``percentile`` — paired bootstrap on case identifiers; coverage close to
  nominal across all tested AUC × n cells.
* ``delong`` — auto-selected for ``Task.metric == "auc"``; ~300× faster than
  bootstrap with mild conservativeness.
* ``bca`` (v0.2.0) — bias-corrected accelerated bootstrap (Efron 1987);
  opt-in only. Does not robustly outperform percentile under the null per
  the 27-cell coverage simulation in ``experiments/estimator_coverage/``;
  most useful in regimes with visible bootstrap-distribution skew.
"""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
import numpy.typing as npt
from scipy import stats

# --------------------------------------------------------------------------
# Generic paired-bootstrap (any metric where Δ_k is a per-patient scalar)
# --------------------------------------------------------------------------

def percentile_ci(
    deltas: npt.NDArray[Any],
    *,
    alpha: float,
    n_bootstrap: int,
    rng: np.random.Generator,
) -> tuple[float, float, float, npt.NDArray[Any]]:
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
# BCa (bias-corrected accelerated) bootstrap (v0.2.0)
# --------------------------------------------------------------------------

def bca_ci(
    deltas: npt.NDArray[Any],
    *,
    alpha: float,
    n_bootstrap: int,
    rng: np.random.Generator,
) -> tuple[float, float, float, npt.NDArray[Any]]:
    """Bias-corrected accelerated (BCa) bootstrap CI for ``E[delta]``.

    Efron 1987. Adjusts the percentile-bootstrap CI endpoints via:

    * the bias-correction constant ``z0 = Phi^{-1}(p_below)`` where
      ``p_below`` is the fraction of bootstrap means below the observed
      sample mean;
    * the acceleration constant ``a`` computed from the third moment of
      the jackknife distribution of ``mean(deltas)``.

    Returns ``(observed_mean, ci_lower, ci_upper, bootstrap_means)``. Falls
    back to the percentile CI when the BCa formula is degenerate (``z0``
    undefined; ``a`` denominator zero).
    """
    n = len(deltas)
    if n == 0:
        raise ValueError("empty deltas array")
    theta_hat = float(deltas.mean())
    boots = np.empty(n_bootstrap)
    for b in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        boots[b] = deltas[idx].mean()

    # Bias correction z0
    p_below = float((boots < theta_hat).mean())
    if p_below <= 0.0 or p_below >= 1.0:
        # degenerate; fall back to percentile
        lo = float(np.percentile(boots, 100 * alpha / 2))
        hi = float(np.percentile(boots, 100 * (1 - alpha / 2)))
        return theta_hat, lo, hi, boots
    z0 = float(stats.norm.ppf(p_below))

    # Jackknife (vectorised leave-one-out sample-mean)
    total = deltas.sum()
    jk = (total - deltas) / (n - 1)
    jk_bar = jk.mean()
    num = float(((jk_bar - jk) ** 3).sum())
    den = 6.0 * float(((jk_bar - jk) ** 2).sum()) ** 1.5
    a_accel = num / den if den > 0 else 0.0

    # BCa endpoints
    za_lo = float(stats.norm.ppf(alpha / 2))
    za_hi = float(stats.norm.ppf(1 - alpha / 2))
    alpha_lo_adj = float(
        stats.norm.cdf(z0 + (z0 + za_lo) / (1 - a_accel * (z0 + za_lo)))
    )
    alpha_hi_adj = float(
        stats.norm.cdf(z0 + (z0 + za_hi) / (1 - a_accel * (z0 + za_hi)))
    )
    # Clip to (0, 1) to keep np.percentile safe
    alpha_lo_adj = float(np.clip(alpha_lo_adj, 1e-4, 1 - 1e-4))
    alpha_hi_adj = float(np.clip(alpha_hi_adj, 1e-4, 1 - 1e-4))
    lo = float(np.percentile(boots, 100 * alpha_lo_adj))
    hi = float(np.percentile(boots, 100 * alpha_hi_adj))
    return theta_hat, lo, hi, boots


# --------------------------------------------------------------------------
# Closed-form paired DeLong CI (AUC only)
# --------------------------------------------------------------------------

def _auc_components(
    scores_pos: npt.NDArray[Any], scores_neg: npt.NDArray[Any],
) -> tuple[npt.NDArray[Any], npt.NDArray[Any]]:
    """DeLong placement components (V10 per positive case, V01 per negative)."""
    s_pos = scores_pos[:, None]
    s_neg = scores_neg[None, :]
    indicator = (s_pos > s_neg).astype(np.float64) + 0.5 * (s_pos == s_neg)
    V10 = indicator.mean(axis=1)
    V01 = indicator.mean(axis=0)
    return V10, V01


def _nonnegative_variance(v: float) -> float:
    """Clip a variance estimate to 0 if floating-point pathology makes it negative.

    DeLong's variance is the sum of two non-negative sample-variance terms divided
    by positive sample sizes, so in exact arithmetic it is always non-negative.
    Floating-point pathology (e.g.\\ catastrophic cancellation on very small
    differences) could in principle yield a tiny negative value; we clip it to 0
    so the downstream ``sqrt`` does not raise.
    """
    return v if v >= 0.0 else 0.0


def delong_ci(
    *,
    a_pos: npt.NDArray[Any],
    a_neg: npt.NDArray[Any],
    b_pos: npt.NDArray[Any],
    b_neg: npt.NDArray[Any],
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
    var = _nonnegative_variance(s10 / n_pos + s01 / n_neg)
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
