"""Tests for the modality-specific T_r operators."""

from __future__ import annotations

import numpy as np
import pytest

from pwm_dose_equivalence.operators import Tr_ct, Tr_mri, Tr_pet

# --------------------------------------------------------------------------
# CT — Poisson-thinning
# --------------------------------------------------------------------------

def test_Tr_ct_preserves_expected_count_ratio():
    """E[T_r(s)] / E[s] ≈ r at large counts."""
    rng = np.random.default_rng(0)
    s_ref = np.full(10_000, 100, dtype=np.int64)
    s_red = Tr_ct(s_ref, r=0.25, rng=rng)
    ratio = s_red.mean() / s_ref.mean()
    assert 0.24 <= ratio <= 0.26


def test_Tr_ct_at_r_eq_1_preserves_total_in_expectation():
    rng = np.random.default_rng(0)
    s_ref = np.full(1000, 50, dtype=np.int64)
    s_red = Tr_ct(s_ref, r=1.0, rng=rng)
    assert (s_red == s_ref).all()


def test_Tr_ct_rejects_invalid_r():
    rng = np.random.default_rng(0)
    s = np.full(10, 10, dtype=np.int64)
    with pytest.raises(ValueError):
        Tr_ct(s, r=0.0, rng=rng)
    with pytest.raises(ValueError):
        Tr_ct(s, r=1.5, rng=rng)


# --------------------------------------------------------------------------
# PET — same Poisson-thinning
# --------------------------------------------------------------------------

def test_Tr_pet_matches_Tr_ct_at_same_seed():
    """PET activity reduction uses the same Poisson-thinning kernel."""
    s = np.full(1000, 50, dtype=np.int64)
    rng1 = np.random.default_rng(42)
    rng2 = np.random.default_rng(42)
    assert (Tr_ct(s, r=0.5, rng=rng1) == Tr_pet(s, r=0.5, rng=rng2)).all()


def test_Tr_pet_rejects_invalid_r():
    rng = np.random.default_rng(0)
    s = np.full(10, 10, dtype=np.int64)
    with pytest.raises(ValueError):
        Tr_pet(s, r=0.0, rng=rng)
    with pytest.raises(ValueError):
        Tr_pet(s, r=1.5, rng=rng)


# --------------------------------------------------------------------------
# MRI — Cartesian mask
# --------------------------------------------------------------------------

def test_Tr_mri_keeps_correct_fraction():
    rng = np.random.default_rng(0)
    s_ref = np.arange(128).astype(np.float64)
    s_red = Tr_mri(s_ref, r=0.25, rng=rng)
    n_keep = int(np.sum(~np.isnan(s_red)))
    assert n_keep == 32  # ceil(0.25 * 128)


def test_Tr_mri_central_region_always_sampled():
    rng = np.random.default_rng(0)
    n = 128
    s_ref = np.arange(n).astype(np.float64)
    s_red = Tr_mri(s_ref, r=0.25, rng=rng, central_fraction=0.5)
    n_keep = int(np.ceil(0.25 * n))
    n_center = max(1, int(n_keep * 0.5))
    c0 = n // 2 - n_center // 2
    # Central region values must be present (not NaN)
    assert not np.isnan(s_red[c0:c0 + n_center]).any()


def test_Tr_mri_unsampled_positions_are_nan():
    """The mask leaves NaN, not zero, so a downstream method can ignore
    masked entries without coupling to a value comparison."""
    rng = np.random.default_rng(0)
    s_ref = np.zeros(64, dtype=np.float64)  # all zeros!
    s_red = Tr_mri(s_ref, r=0.25, rng=rng)
    # If we used 0 as the sentinel, every entry would look unmasked.
    # Confirm at least some entries are NaN (the masked-out ones).
    assert np.isnan(s_red).any()


def test_Tr_mri_rejects_invalid_args():
    rng = np.random.default_rng(0)
    s = np.zeros(64, dtype=np.float64)
    with pytest.raises(ValueError):
        Tr_mri(s, r=0.0, rng=rng)
    with pytest.raises(ValueError):
        Tr_mri(s, r=0.5, rng=rng, central_fraction=0.0)
