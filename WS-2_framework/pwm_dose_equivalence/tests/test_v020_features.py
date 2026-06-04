"""Tests for the v0.2.0 features.

* ``bca_ci`` — bias-corrected accelerated bootstrap exposed as an opt-in
  estimator.
* Small-$n$ anti-conservativeness warning fires for non-AUC metrics at
  $n < 30$ (per ``theory/proofs/estimator.md`` §4c / V3-11).
* ``bound_M`` argument exposed in the public API and propagated to the
  Bernstein sample-size formula.
"""

from __future__ import annotations

import numpy as np
import pytest

from pwm_dose_equivalence import (
    Task,
    bca_ci,
    signal_equivalence_credential,
)


# --------------------------------------------------------------------------
# BCa
# --------------------------------------------------------------------------

def test_bca_ci_returns_four_tuple():
    rng = np.random.default_rng(0)
    deltas = rng.normal(0.0, 0.05, size=200)
    mean, lo, hi, boots = bca_ci(
        deltas, alpha=0.05, n_bootstrap=1000, rng=np.random.default_rng(1),
    )
    assert lo < mean < hi
    assert len(boots) == 1000


def test_bca_ci_covers_zero_under_null():
    """At the truly-equivalent null, the BCa CI covers 0 in ≈ 95% of trials."""
    base_rng = np.random.default_rng(11)
    covered = 0
    n_trials = 150
    for _ in range(n_trials):
        deltas = base_rng.normal(0.0, 0.05, size=200)
        _, lo, hi, _ = bca_ci(
            deltas, alpha=0.05, n_bootstrap=1000,
            rng=np.random.default_rng(base_rng.integers(0, 2**32)),
        )
        if lo <= 0 <= hi:
            covered += 1
    coverage = covered / n_trials
    # MC SE ~0.018 at T=150; allow [0.87, 1.0]
    assert 0.87 <= coverage <= 1.0


def test_bca_ci_falls_back_when_degenerate():
    """When every bootstrap mean equals theta_hat, BCa falls back to percentile."""
    deltas = np.full(50, 0.5)
    mean, lo, hi, _ = bca_ci(
        deltas, alpha=0.05, n_bootstrap=500,
        rng=np.random.default_rng(0),
    )
    # All bootstrap means are 0.5; CI collapses
    assert mean == 0.5
    assert lo == 0.5 and hi == 0.5


def test_bca_ci_rejects_empty():
    with pytest.raises(ValueError):
        bca_ci(
            np.array([]), alpha=0.05, n_bootstrap=100,
            rng=np.random.default_rng(0),
        )


# --------------------------------------------------------------------------
# API integration: estimator="bca"
# --------------------------------------------------------------------------

def test_api_bca_with_equivalent_methods_passes():
    rng = np.random.default_rng(0)
    n = 200
    a = rng.normal(0.80, 0.05, size=n)
    b = rng.normal(0.80, 0.05, size=n)
    cred = signal_equivalence_credential(
        paired_a=a, paired_b=b,
        signal_ratio=0.25, modality="CT",
        task=Task("liver_dice", metric="dice"),
        subpopulation="test_v1",
        epsilon=0.05, alpha=0.05,
        n_bootstrap=1000, seed=1,
        estimator="bca",
    )
    assert cred.credential.verdict.value == "PASS"
    assert cred.credential.estimator == "bca"


def test_api_bca_with_auc_mode_raises():
    """estimator='bca' requires per-patient (paired_a, paired_b) — not AUC."""
    rng = np.random.default_rng(0)
    a_pos = rng.normal(1.5, 1.0, size=100)
    a_neg = rng.normal(0.0, 1.0, size=100)
    b_pos = rng.normal(1.5, 1.0, size=100)
    b_neg = rng.normal(0.0, 1.0, size=100)
    with pytest.raises(ValueError, match="bca"):
        signal_equivalence_credential(
            a_pos=a_pos, a_neg=a_neg, b_pos=b_pos, b_neg=b_neg,
            signal_ratio=0.25, modality="CT",
            task=Task("auc", metric="auc"),
            subpopulation="test_v1",
            epsilon=0.05, alpha=0.05, seed=2,
            estimator="bca",
        )


# --------------------------------------------------------------------------
# Small-n anti-conservativeness warning
# --------------------------------------------------------------------------

def test_small_n_warning_fires_at_n_below_threshold(recwarn):
    """At n < 30 the library warns about percentile-bootstrap anti-conservativeness."""
    rng = np.random.default_rng(0)
    a = rng.normal(0.80, 0.05, size=20)
    b = rng.normal(0.80, 0.05, size=20)
    signal_equivalence_credential(
        paired_a=a, paired_b=b,
        signal_ratio=0.25, modality="CT",
        task=Task("dice", metric="dice"),
        subpopulation="test_v1",
        epsilon=0.05, alpha=0.05,
        n_bootstrap=500, seed=3,
    )
    assert any(
        "small-n threshold" in str(w.message)
        for w in recwarn.list
    )


def test_small_n_warning_silent_at_n_above_threshold(recwarn):
    """At n >= 30 the small-n warning does not fire."""
    rng = np.random.default_rng(0)
    a = rng.normal(0.80, 0.05, size=50)
    b = rng.normal(0.80, 0.05, size=50)
    signal_equivalence_credential(
        paired_a=a, paired_b=b,
        signal_ratio=0.25, modality="CT",
        task=Task("dice", metric="dice"),
        subpopulation="test_v1",
        epsilon=0.05, alpha=0.05,
        n_bootstrap=500, seed=4,
    )
    assert not any(
        "small-n threshold" in str(w.message)
        for w in recwarn.list
    )


def test_small_n_warning_also_for_bca(recwarn):
    """The same warning fires for BCa at n < 30 because BCa is still a bootstrap."""
    rng = np.random.default_rng(0)
    a = rng.normal(0.80, 0.05, size=15)
    b = rng.normal(0.80, 0.05, size=15)
    signal_equivalence_credential(
        paired_a=a, paired_b=b,
        signal_ratio=0.25, modality="CT",
        task=Task("dice", metric="dice"),
        subpopulation="test_v1",
        epsilon=0.05, alpha=0.05,
        n_bootstrap=500, seed=5,
        estimator="bca",
    )
    assert any(
        "small-n threshold" in str(w.message)
        for w in recwarn.list
    )


# --------------------------------------------------------------------------
# bound_M unbounded-metric extension
# --------------------------------------------------------------------------

def test_bound_M_default_is_one():
    """When bound_M is not specified, the Bernstein bound uses M = 1."""
    rng = np.random.default_rng(0)
    a = rng.normal(0.80, 0.05, size=100)
    b = rng.normal(0.80, 0.05, size=100)
    cred = signal_equivalence_credential(
        paired_a=a, paired_b=b,
        signal_ratio=0.25, modality="CT",
        task=Task("dice", metric="dice"),
        subpopulation="test_v1",
        epsilon=0.05, alpha=0.05,
        n_bootstrap=500, seed=6,
        sigma_delta_hint=0.05,
    )
    sc = cred.credential.sample_size_check
    assert sc["bound_M"] == 1.0


def test_bound_M_passes_through_to_bernstein():
    """A larger bound_M produces a strictly larger Bernstein n requirement."""
    rng = np.random.default_rng(0)
    n = 200
    a = rng.normal(0.80, 0.05, size=n)
    b = rng.normal(0.80, 0.05, size=n)
    cred_m1 = signal_equivalence_credential(
        paired_a=a.copy(), paired_b=b.copy(),
        signal_ratio=0.25, modality="CT",
        task=Task("dice", metric="dice"),
        subpopulation="test_v1",
        epsilon=0.05, alpha=0.05,
        n_bootstrap=500, seed=7,
        sigma_delta_hint=0.05,
        bound_M=1.0,
    )
    cred_m100 = signal_equivalence_credential(
        paired_a=a.copy(), paired_b=b.copy(),
        signal_ratio=0.25, modality="CT",
        task=Task("dice", metric="dice"),
        subpopulation="test_v1",
        epsilon=0.05, alpha=0.05,
        n_bootstrap=500, seed=7,
        sigma_delta_hint=0.05,
        bound_M=100.0,
    )
    sc1 = cred_m1.credential.sample_size_check
    sc100 = cred_m100.credential.sample_size_check
    assert sc100["bound_M"] == 100.0
    # Larger M → larger Bernstein requirement
    assert sc100["n_required_bernstein"] > sc1["n_required_bernstein"]
    # CLT requirement does not depend on M
    assert sc1["n_required_clt"] == sc100["n_required_clt"]
