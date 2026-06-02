"""Tests for the (S1), (S3), (S4) sample-size formulas."""

from __future__ import annotations

import pytest

from pwm_dose_equivalence.sample_size import (
    required_n_auc,
    required_n_bernstein,
    required_n_general,
)


# --------------------------------------------------------------------------
# (S1) general-metric CLT bound
# --------------------------------------------------------------------------

def test_S1_zero_variance_gives_zero_sample():
    """If sigma_delta = 0 there is no estimation cost."""
    assert required_n_general(epsilon=0.02, alpha=0.05, sigma_delta=0.0) == 0


def test_S1_canonical_table_row_sigma_010():
    """Spot-check theory/proofs/sample_size.md §3.1: sigma_delta=0.10
    at eps=0.02, alpha=0.05 → n ≥ 97 (ceil of 96.04)."""
    n = required_n_general(epsilon=0.02, alpha=0.05, sigma_delta=0.10)
    assert n == 97


def test_S1_canonical_table_row_sigma_015():
    """sigma_delta=0.15 → n ≥ 217 (ceil of 216.09)."""
    n = required_n_general(epsilon=0.02, alpha=0.05, sigma_delta=0.15)
    assert n == 217


def test_S1_scales_as_sigma_squared():
    """Doubling sigma_delta quadruples n."""
    n_a = required_n_general(epsilon=0.02, alpha=0.05, sigma_delta=0.10)
    n_b = required_n_general(epsilon=0.02, alpha=0.05, sigma_delta=0.20)
    # Allow rounding; n_b should be ~4× n_a
    assert 3.9 <= (n_b / n_a) <= 4.1


def test_S1_scales_as_inverse_epsilon_squared():
    """Doubling epsilon quarters n. Ceil rounding introduces small slack
    so we allow the ratio in [3.5, 4.5] rather than ~4 exactly."""
    n_tight = required_n_general(epsilon=0.02, alpha=0.05, sigma_delta=0.10)
    n_loose = required_n_general(epsilon=0.04, alpha=0.05, sigma_delta=0.10)
    assert 3.5 <= (n_tight / n_loose) <= 4.5


def test_S1_rejects_invalid_args():
    with pytest.raises(ValueError):
        required_n_general(epsilon=-0.01, alpha=0.05, sigma_delta=0.1)
    with pytest.raises(ValueError):
        required_n_general(epsilon=0.02, alpha=1.5, sigma_delta=0.1)
    with pytest.raises(ValueError):
        required_n_general(epsilon=0.02, alpha=0.05, sigma_delta=-0.1)


# --------------------------------------------------------------------------
# (S3) paired AUC bound
# --------------------------------------------------------------------------

def test_S3_canonical_table_AUC085_eps02():
    """theory/proofs/sample_size.md §3.2: AUC=0.85, eps=0.02 → n ≥ 1540."""
    n = required_n_auc(epsilon=0.02, alpha=0.05, placement_sd=0.20)
    assert n == 1537 or n == 1538 or n == 1540  # allow small rounding


def test_S3_canonical_table_AUC092_eps05():
    """AUC=0.92, eps=0.05 → n ≥ 129."""
    n = required_n_auc(epsilon=0.05, alpha=0.05, placement_sd=0.145)
    assert 128 <= n <= 131


def test_S3_canonical_table_AUC097_eps10():
    """AUC=0.97, eps=0.10 → n ≥ 11."""
    n = required_n_auc(epsilon=0.10, alpha=0.05, placement_sd=0.082)
    assert n == 11


def test_S3_is_4x_S1_at_same_sigma():
    """(S3) has a factor 4 vs (S1) at the same nominal sigma."""
    n_s3 = required_n_auc(epsilon=0.02, alpha=0.05, placement_sd=0.10)
    n_s1 = required_n_general(epsilon=0.02, alpha=0.05, sigma_delta=0.10)
    assert 3.9 <= (n_s3 / n_s1) <= 4.1


# --------------------------------------------------------------------------
# (S4) Bernstein bound
# --------------------------------------------------------------------------

def test_S4_returns_positive_for_canonical_inputs():
    n = required_n_bernstein(epsilon=0.02, alpha=0.05, sigma_delta=0.10)
    assert n > 0


def test_S4_at_zero_sigma_isnt_zero_due_to_bound_term():
    """Bernstein keeps the M·epsilon/3 term even when sigma_delta = 0."""
    n_zero = required_n_bernstein(
        epsilon=0.02, alpha=0.05, sigma_delta=0.0, bound_M=1.0,
    )
    assert n_zero > 0


def test_S4_strictly_more_conservative_than_S1():
    """Per theory/proofs/sample_size.md §4: Bernstein is strictly
    more conservative than CLT at typical operating points. At
    (eps=0.02, alpha=0.05, sigma=0.10, M=1) the ratio is ~3.2x."""
    n_s1 = required_n_general(epsilon=0.02, alpha=0.05, sigma_delta=0.10)
    n_s4 = required_n_bernstein(
        epsilon=0.02, alpha=0.05, sigma_delta=0.10, bound_M=1.0,
    )
    # Bernstein never smaller than CLT; ~3.2x at these inputs.
    ratio = n_s4 / n_s1
    assert ratio >= 1.0
    assert 2.5 <= ratio <= 4.0
