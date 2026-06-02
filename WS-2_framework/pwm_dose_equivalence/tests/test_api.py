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
