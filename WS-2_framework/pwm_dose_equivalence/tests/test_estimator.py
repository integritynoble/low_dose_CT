"""Tests for the percentile and DeLong CI estimators."""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from pwm_dose_equivalence.estimator import (
    delong_ci,
    percentile_ci,
    verdict_from_ci,
)


# --------------------------------------------------------------------------
# Percentile bootstrap
# --------------------------------------------------------------------------

def test_percentile_recovers_mean_at_large_n():
    """At n = 5000 the bootstrap CI is tight around the true mean."""
    rng = np.random.default_rng(0)
    deltas = rng.normal(loc=0.5, scale=0.1, size=5000)
    mean, lo, hi, _ = percentile_ci(
        deltas, alpha=0.05, n_bootstrap=1000,
        rng=np.random.default_rng(1),
    )
    assert lo < 0.5 < hi
    assert abs(mean - 0.5) < 0.01
    assert (hi - lo) < 0.01  # tight


def test_percentile_coverage_under_null():
    """Repeated trials at true mean = 0 cover 0 in ~95% of CIs."""
    covered = 0
    n_trials = 200
    base_rng = np.random.default_rng(7)
    for _ in range(n_trials):
        deltas = base_rng.normal(loc=0.0, scale=1.0, size=200)
        _, lo, hi, _ = percentile_ci(
            deltas, alpha=0.05, n_bootstrap=1000,
            rng=np.random.default_rng(base_rng.integers(0, 2**32)),
        )
        if lo <= 0 <= hi:
            covered += 1
    coverage = covered / n_trials
    # MC standard error at p=0.95, n=200 trials is ~0.015 so allow ±0.04
    assert 0.91 <= coverage <= 0.99, f"coverage {coverage} outside band"


def test_percentile_raises_on_empty():
    with pytest.raises(ValueError):
        percentile_ci(np.array([]), alpha=0.05, n_bootstrap=100,
                     rng=np.random.default_rng(0))


# --------------------------------------------------------------------------
# DeLong (paired AUC, closed-form)
# --------------------------------------------------------------------------

def _binormal_pair(rng, auc_target, n_per_class, rho=0.5):
    """Return paired scores for two methods at the same AUC, correlated rho."""
    mu = np.sqrt(2) * stats.norm.ppf(auc_target)
    cov = np.array([[1.0, rho], [rho, 1.0]])
    pos = rng.multivariate_normal([mu, mu], cov, size=n_per_class)
    neg = rng.multivariate_normal([0.0, 0.0], cov, size=n_per_class)
    return pos[:, 0], neg[:, 0], pos[:, 1], neg[:, 1]


def test_delong_under_null_contains_zero():
    """Two methods drawn from the same AUC distribution → CI contains 0
    in close to 95% of trials."""
    covered = 0
    n_trials = 200
    base_rng = np.random.default_rng(11)
    for _ in range(n_trials):
        a_pos, a_neg, b_pos, b_neg = _binormal_pair(
            base_rng, auc_target=0.85, n_per_class=100,
        )
        delta, lo, hi = delong_ci(
            a_pos=a_pos, a_neg=a_neg, b_pos=b_pos, b_neg=b_neg, alpha=0.05,
        )
        if lo <= 0 <= hi:
            covered += 1
    coverage = covered / n_trials
    assert 0.90 <= coverage <= 0.99, f"coverage {coverage} outside band"


def test_delong_returns_finite_for_perfect_classifier():
    """A perfectly separated classifier should still produce a finite CI."""
    a_pos = np.array([1.0, 1.5, 2.0])
    a_neg = np.array([-1.0, -0.5, 0.0])
    b_pos = np.array([1.0, 1.5, 2.0])  # identical to A
    b_neg = np.array([-1.0, -0.5, 0.0])
    delta, lo, hi = delong_ci(
        a_pos=a_pos, a_neg=a_neg, b_pos=b_pos, b_neg=b_neg, alpha=0.05,
    )
    assert delta == 0.0
    assert lo == 0.0 and hi == 0.0  # zero variance


# --------------------------------------------------------------------------
# Verdict
# --------------------------------------------------------------------------

def test_verdict_pass():
    assert verdict_from_ci(-0.01, 0.01, epsilon=0.02) == "PASS"


def test_verdict_fail_upper():
    assert verdict_from_ci(0.05, 0.10, epsilon=0.02) == "FAIL"


def test_verdict_fail_lower():
    assert verdict_from_ci(-0.10, -0.05, epsilon=0.02) == "FAIL"


def test_verdict_indeterminate_straddles_upper():
    assert verdict_from_ci(-0.01, 0.05, epsilon=0.02) == "INDETERMINATE"


def test_verdict_indeterminate_straddles_lower():
    assert verdict_from_ci(-0.05, 0.01, epsilon=0.02) == "INDETERMINATE"
