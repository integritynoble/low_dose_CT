"""End-to-end tests of ``signal_equivalence_credential``."""

from __future__ import annotations

import json

import numpy as np
import pytest

from pwm_dose_equivalence import (
    SignalEquivalenceCredential,
    Task,
    signal_equivalence_credential,
)


def test_general_metric_equivalent_methods_pass():
    """Two methods with the same Dice distribution → PASS at eps=0.05."""
    rng = np.random.default_rng(0)
    n = 200
    # Both methods unbiased estimators of the latent Dice; small noise
    a = rng.normal(0.80, 0.05, size=n)
    b = rng.normal(0.80, 0.05, size=n)
    cred = signal_equivalence_credential(
        paired_a=a, paired_b=b,
        signal_ratio=0.25, modality="CT",
        task=Task("liver_dice", metric="dice"),
        subpopulation="test_v1",
        epsilon=0.05, alpha=0.05,
        n_bootstrap=2000, seed=1,
    )
    assert cred.credential.verdict.value == "PASS"
    assert cred.credential.estimator == "percentile"
    assert cred.framework_hash.startswith("sha256:")


def test_general_metric_biased_method_fails():
    rng = np.random.default_rng(0)
    n = 200
    a = rng.normal(0.85, 0.05, size=n)  # candidate is 0.05 higher on average
    b = rng.normal(0.70, 0.05, size=n)
    cred = signal_equivalence_credential(
        paired_a=a, paired_b=b,
        signal_ratio=0.25, modality="CT",
        task=Task("liver_dice", metric="dice"),
        subpopulation="test_v1",
        epsilon=0.05, alpha=0.05,
        n_bootstrap=2000, seed=1,
    )
    assert cred.credential.verdict.value == "FAIL"


def test_auc_mode_auto_selects_delong():
    rng = np.random.default_rng(0)
    a_pos = rng.normal(1.5, 1.0, size=100)
    a_neg = rng.normal(0.0, 1.0, size=100)
    b_pos = rng.normal(1.5, 1.0, size=100)
    b_neg = rng.normal(0.0, 1.0, size=100)
    cred = signal_equivalence_credential(
        a_pos=a_pos, a_neg=a_neg, b_pos=b_pos, b_neg=b_neg,
        signal_ratio=0.25, modality="CT",
        task=Task("lung_nodule_5mm", metric="auc"),
        subpopulation="test_v1",
        epsilon=0.10, alpha=0.05, seed=2,
    )
    assert cred.credential.estimator == "delong"
    assert cred.credential.n_bootstrap == 0  # DeLong is closed-form
    assert cred.credential.verdict.value in {"PASS", "INDETERMINATE"}


def test_json_round_trip():
    rng = np.random.default_rng(0)
    a = rng.normal(0.80, 0.05, size=100)
    b = rng.normal(0.80, 0.05, size=100)
    cred = signal_equivalence_credential(
        paired_a=a, paired_b=b,
        signal_ratio=0.25, modality="CT",
        task=Task("liver_dice", metric="dice"),
        subpopulation="test_v1",
        epsilon=0.05, alpha=0.05,
        n_bootstrap=1000, seed=3,
    )
    s = cred.to_json()
    # Should be valid JSON
    d = json.loads(s)
    assert d["schema_version"] == "pwm-signal-equivalence/v0.2"
    # And should round-trip
    cred2 = SignalEquivalenceCredential.from_json(s)
    assert cred2.credential.verdict == cred.credential.verdict
    assert cred2.credential.delta_mean == cred.credential.delta_mean
    assert cred2.framework_hash == cred.framework_hash


def test_rejects_mixed_modes():
    """Cannot pass both paired_a/paired_b and a_pos/a_neg/..."""
    rng = np.random.default_rng(0)
    with pytest.raises(ValueError):
        signal_equivalence_credential(
            paired_a=rng.normal(size=10), paired_b=rng.normal(size=10),
            a_pos=rng.normal(size=5),
            signal_ratio=0.25, modality="CT",
            task=Task("auc", metric="auc"),
            subpopulation="test_v1",
            epsilon=0.05,
        )


def test_rejects_missing_inputs():
    with pytest.raises(ValueError):
        signal_equivalence_credential(
            signal_ratio=0.25, modality="CT",
            task=Task("auc", metric="auc"),
            subpopulation="test_v1",
            epsilon=0.05,
        )


def test_sample_size_warning_when_n_too_small(recwarn):
    rng = np.random.default_rng(0)
    a = rng.normal(0.0, 0.30, size=30)  # very small n
    b = rng.normal(0.0, 0.30, size=30)
    signal_equivalence_credential(
        paired_a=a, paired_b=b,
        signal_ratio=0.25, modality="CT",
        task=Task("dice", metric="dice"),
        subpopulation="test_v1",
        epsilon=0.02, alpha=0.05,
        n_bootstrap=1000, seed=5,
        sigma_delta_hint=0.30,
    )
    assert any("Sample size" in str(w.message) for w in recwarn.list)


def test_credential_contains_framework_hash_and_schema():
    rng = np.random.default_rng(0)
    a = rng.normal(0.80, 0.05, size=100)
    b = rng.normal(0.80, 0.05, size=100)
    cred = signal_equivalence_credential(
        paired_a=a, paired_b=b,
        signal_ratio=0.25, modality="CT",
        task=Task("dice", metric="dice"),
        subpopulation="test_v1",
        epsilon=0.05, alpha=0.05,
        n_bootstrap=1000, seed=6,
    )
    d = cred.to_dict()
    assert d["schema_version"] == "pwm-signal-equivalence/v0.2"
    assert d["framework_hash"].startswith("sha256:")
    assert "credential" in d


# --------------------------------------------------------------------------
# Validation branches
# --------------------------------------------------------------------------

def test_forced_delong_with_general_inputs_raises():
    """estimator='delong' without AUC-style inputs is a user error."""
    rng = np.random.default_rng(0)
    a = rng.normal(0.0, 1.0, size=50)
    b = rng.normal(0.0, 1.0, size=50)
    with pytest.raises(ValueError, match="delong"):
        signal_equivalence_credential(
            paired_a=a, paired_b=b,
            signal_ratio=0.25, modality="CT",
            task=Task("dice", metric="dice"),
            subpopulation="test_v1",
            epsilon=0.05,
            estimator="delong",
        )


def test_forced_percentile_with_auc_inputs_raises():
    """estimator='percentile' with AUC-style inputs is a user error."""
    rng = np.random.default_rng(0)
    a_pos = rng.normal(1.0, 1.0, size=50)
    a_neg = rng.normal(0.0, 1.0, size=50)
    b_pos = rng.normal(1.0, 1.0, size=50)
    b_neg = rng.normal(0.0, 1.0, size=50)
    with pytest.raises(ValueError, match="percentile"):
        signal_equivalence_credential(
            a_pos=a_pos, a_neg=a_neg, b_pos=b_pos, b_neg=b_neg,
            signal_ratio=0.25, modality="CT",
            task=Task("auc", metric="auc"),
            subpopulation="test_v1",
            epsilon=0.05,
            estimator="percentile",
        )


def test_unknown_estimator_raises():
    """An invalid estimator string should fail fast."""
    rng = np.random.default_rng(0)
    a = rng.normal(0.0, 1.0, size=50)
    b = rng.normal(0.0, 1.0, size=50)
    with pytest.raises(ValueError, match="Unknown estimator"):
        signal_equivalence_credential(
            paired_a=a, paired_b=b,
            signal_ratio=0.25, modality="CT",
            task=Task("dice", metric="dice"),
            subpopulation="test_v1",
            epsilon=0.05,
            estimator="jackknife",  # genuinely not a supported estimator
        )


def test_shape_mismatch_raises():
    """paired_a and paired_b must have the same shape."""
    rng = np.random.default_rng(0)
    a = rng.normal(0.0, 1.0, size=50)
    b = rng.normal(0.0, 1.0, size=40)  # different length
    with pytest.raises(ValueError, match="shape"):
        signal_equivalence_credential(
            paired_a=a, paired_b=b,
            signal_ratio=0.25, modality="CT",
            task=Task("dice", metric="dice"),
            subpopulation="test_v1",
            epsilon=0.05,
        )


def test_delong_mode_emits_sample_size_warning_when_n_small(recwarn):
    """At n_test below the (S3) prescription, DeLong-mode also warns."""
    rng = np.random.default_rng(0)
    # 30 + 30 = 60 cases; placement_sd_hint=0.20 → (S3) requires
    # n ≥ (1.96/0.05)² × 4 × 0.04 = ~246 — far above 60.
    a_pos = rng.normal(1.0, 1.0, size=30)
    a_neg = rng.normal(0.0, 1.0, size=30)
    b_pos = rng.normal(1.0, 1.0, size=30)
    b_neg = rng.normal(0.0, 1.0, size=30)
    cred = signal_equivalence_credential(
        a_pos=a_pos, a_neg=a_neg, b_pos=b_pos, b_neg=b_neg,
        signal_ratio=0.25, modality="CT",
        task=Task("auc", metric="auc"),
        subpopulation="test_v1",
        epsilon=0.05, alpha=0.05, seed=7,
        placement_sd_hint=0.20,
    )
    assert any("S3 prescription" in str(w.message) for w in recwarn.list)
    assert cred.credential.sample_size_check["rule"] == "S3-auc-clt"
    assert cred.credential.sample_size_check["ok"] is False


def test_delong_mode_records_sample_check_when_n_sufficient():
    """When n is sufficient, the sample_size_check field still gets populated
    but ``ok`` is True and no warning fires."""
    rng = np.random.default_rng(0)
    # 200 + 200 = 400 cases at placement_sd_hint=0.05 → S3 needs
    # (1.96/0.05)² × 4 × 0.0025 = ~16 ≪ 400.
    a_pos = rng.normal(1.5, 1.0, size=200)
    a_neg = rng.normal(0.0, 1.0, size=200)
    b_pos = rng.normal(1.5, 1.0, size=200)
    b_neg = rng.normal(0.0, 1.0, size=200)
    cred = signal_equivalence_credential(
        a_pos=a_pos, a_neg=a_neg, b_pos=b_pos, b_neg=b_neg,
        signal_ratio=0.25, modality="CT",
        task=Task("auc", metric="auc"),
        subpopulation="test_v1",
        epsilon=0.05, alpha=0.05, seed=8,
        placement_sd_hint=0.05,
    )
    assert cred.credential.sample_size_check["rule"] == "S3-auc-clt"
    assert cred.credential.sample_size_check["ok"] is True
