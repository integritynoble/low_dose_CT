"""End-to-end integration tests.

Where the per-module unit tests exercise individual functions
(``estimator.py`` / ``sample_size.py`` / ``operators.py`` / ``credential.py``
/ ``framework_hash.py``) in isolation, these tests exercise the full
credential-issuance pipeline through the public ``signal_equivalence_credential``
API across all three modalities and verify the cross-cutting invariants
the manuscript advertises:

* The same single API call signature produces credentials of identical
  shape across CT / MRI / PET (the modality-general claim).
* The credential JSON round-trips losslessly.
* The framework hash is stable and content-addressed.
* Seeded credentials are reproducible bit-for-bit.
* The synthetic cross-modality consistency demo (3 PASS + 3 FAIL) can be
  reproduced inside a test using the public API end-to-end.
"""

from __future__ import annotations

import json

import numpy as np

from pwm_dose_equivalence import (
    SignalEquivalenceCredential,
    Task,
    Tr_ct,
    Tr_mri,
    Tr_pet,
    Verdict,
    framework_hash,
    signal_equivalence_credential,
)

# --------------------------------------------------------------------------
# End-to-end per-modality credential issuance
# --------------------------------------------------------------------------

def _simulate_paired_dice(rng, n_patients, sigma_delta, delta_true=0.0):
    """Per-patient Dice-difference draws from Normal(delta_true, sigma_Δ²)."""
    deltas = rng.normal(delta_true, sigma_delta, size=n_patients)
    # Anchor scores around realistic clinical Dice ≈ 0.82 ± noise
    b = rng.normal(0.82, 0.04, size=n_patients)
    a = b + deltas
    return a, b


def _simulate_paired_auc(rng, n_per_class, auc_b=0.92, delta_auc=0.0):
    """Paired binormal AUC scores for two methods (Method A optionally shifted)."""
    from scipy import stats
    mu_b = float(np.sqrt(2) * stats.norm.ppf(auc_b))
    mu_a = float(np.sqrt(2) * stats.norm.ppf(auc_b + delta_auc))
    rho = 0.5
    cov = np.array([[1.0, rho], [rho, 1.0]])
    pos = rng.multivariate_normal([mu_a, mu_b], cov, size=n_per_class)
    neg = rng.multivariate_normal([0.0, 0.0], cov, size=n_per_class)
    return pos[:, 0], neg[:, 0], pos[:, 1], neg[:, 1]


def test_end_to_end_ct_auc_credential_passes_when_equivalent():
    """CT lung-nodule AUC at the v0.3 AUC default ε = 0.05, n = 500 (per §4a)."""
    rng = np.random.default_rng(7)
    a_pos, a_neg, b_pos, b_neg = _simulate_paired_auc(
        rng, n_per_class=250, auc_b=0.92, delta_auc=0.0,
    )
    cred = signal_equivalence_credential(
        a_pos=a_pos, a_neg=a_neg, b_pos=b_pos, b_neg=b_neg,
        signal_ratio=0.25, modality="CT",
        task=Task(
            "lung_nodule_5mm", metric="auc",
            ground_truth_protocol="pwm-ldct/annotation-qa/v0.5#sha256:test",
        ),
        subpopulation="adult_chest_pwm_l3_test_v1",
        epsilon=0.05, alpha=0.05, seed=7,
    )
    assert cred.credential.verdict == Verdict.PASS
    assert cred.credential.modality == "CT"
    assert cred.credential.estimator == "delong"  # auto-selected for AUC


def test_end_to_end_mri_dice_credential_passes_when_equivalent():
    """MRI knee-meniscus Dice at the v0.3 non-AUC default ε = 0.02, n = 200."""
    rng = np.random.default_rng(8)
    a, b = _simulate_paired_dice(rng, n_patients=200, sigma_delta=0.05)
    cred = signal_equivalence_credential(
        paired_a=a, paired_b=b,
        signal_ratio=0.25, modality="MRI",
        task=Task("meniscus_dice", metric="dice"),
        subpopulation="fastmri_knee_vd_cartesian_R4_v1",
        epsilon=0.02, alpha=0.05,
        n_bootstrap=2000, seed=8,
        sigma_delta_hint=0.05,
    )
    assert cred.credential.verdict == Verdict.PASS
    assert cred.credential.modality == "MRI"
    assert cred.credential.estimator == "percentile"


def test_end_to_end_pet_cr_credential_with_recommended_cohort_passes():
    """PET phantom CR at ε = 0.02, n = 30 (5 NEMA acquisitions × 6 spheres)
    — the recommended cohort from `proofs/estimator.md` §4c."""
    rng = np.random.default_rng(9)
    a, b = _simulate_paired_dice(rng, n_patients=30, sigma_delta=0.02)
    cred = signal_equivalence_credential(
        paired_a=a, paired_b=b,
        signal_ratio=0.25, modality="PET",
        task=Task("contrast_recovery", metric="contrast_recovery"),
        subpopulation="nema_nu2_iq_phantom_18FDG_v1",
        epsilon=0.02, alpha=0.05,
        n_bootstrap=2000, seed=9,
        sigma_delta_hint=0.02,
    )
    assert cred.credential.verdict == Verdict.PASS
    assert cred.credential.modality == "PET"


# --------------------------------------------------------------------------
# Cross-modality consistency: reproduce the experiments/ demo via the API
# --------------------------------------------------------------------------

def test_cross_modality_consistency_via_public_api():
    """The same API call signature produces credentials of identical shape
    across CT / MRI / PET for equivalent methods at n = 200, ε = 0.05.

    Mirrors `experiments/cross_modality_consistency/` but exercises the
    public ``signal_equivalence_credential`` rather than the prototype.
    """
    rng = np.random.default_rng(42)
    creds = []
    for modality in ("CT", "MRI", "PET"):
        a, b = _simulate_paired_dice(rng, n_patients=200, sigma_delta=0.05)
        cred = signal_equivalence_credential(
            paired_a=a, paired_b=b,
            signal_ratio=0.25, modality=modality,
            task=Task("dice", metric="dice"),
            subpopulation=f"{modality.lower()}_test_v1",
            epsilon=0.05, alpha=0.05,
            n_bootstrap=1000, seed=42,
        )
        creds.append(cred)
    # All three PASS — modality-general property
    assert all(c.credential.verdict == Verdict.PASS for c in creds)
    # Identical schema shape (same keys in serialised form)
    serialised = [c.to_dict() for c in creds]
    key_sets = [set(d["credential"].keys()) for d in serialised]
    assert key_sets[0] == key_sets[1] == key_sets[2]
    # All three carry the same framework hash (same library version)
    assert (creds[0].framework_hash
            == creds[1].framework_hash
            == creds[2].framework_hash)


# --------------------------------------------------------------------------
# JSON round-trip + framework-hash audit
# --------------------------------------------------------------------------

def test_credential_round_trip_preserves_framework_hash():
    rng = np.random.default_rng(10)
    a, b = _simulate_paired_dice(rng, n_patients=100, sigma_delta=0.05)
    cred = signal_equivalence_credential(
        paired_a=a, paired_b=b,
        signal_ratio=0.25, modality="CT",
        task=Task("dice", metric="dice"),
        subpopulation="test_v1",
        epsilon=0.05, alpha=0.05,
        n_bootstrap=1000, seed=10,
    )
    s = cred.to_json()
    cred2 = SignalEquivalenceCredential.from_json(s)
    assert cred2.framework_hash == cred.framework_hash
    # Re-compute hash from the canonical spec; must match
    assert cred2.framework_hash == framework_hash()


def test_published_credential_is_valid_json():
    rng = np.random.default_rng(11)
    a, b = _simulate_paired_dice(rng, n_patients=100, sigma_delta=0.05)
    cred = signal_equivalence_credential(
        paired_a=a, paired_b=b,
        signal_ratio=0.25, modality="CT",
        task=Task("dice", metric="dice"),
        subpopulation="test_v1",
        epsilon=0.05, alpha=0.05,
        n_bootstrap=1000, seed=11,
    )
    s = cred.to_json()
    parsed = json.loads(s)
    assert parsed["schema_version"] == "pwm-signal-equivalence/v0.2"
    assert parsed["framework_hash"].startswith("sha256:")
    assert "credential" in parsed


# --------------------------------------------------------------------------
# Reproducibility
# --------------------------------------------------------------------------

def test_seeded_credential_is_bit_reproducible():
    """Identical inputs + identical seed → identical credential JSON."""
    rng_a = np.random.default_rng(12)
    a1, b1 = _simulate_paired_dice(rng_a, n_patients=100, sigma_delta=0.05)
    rng_b = np.random.default_rng(12)
    a2, b2 = _simulate_paired_dice(rng_b, n_patients=100, sigma_delta=0.05)

    common_args = dict(
        paired_a=a1, paired_b=b1,
        signal_ratio=0.25, modality="CT",
        task=Task("dice", metric="dice"),
        subpopulation="test_v1",
        epsilon=0.05, alpha=0.05,
        n_bootstrap=1000, seed=999,
    )
    cred1 = signal_equivalence_credential(**common_args)
    cred2 = signal_equivalence_credential(
        **{**common_args, "paired_a": a2, "paired_b": b2}
    )
    # The deltas + seed are identical, so the credentials must match
    assert cred1.to_json() == cred2.to_json()


# --------------------------------------------------------------------------
# T_r operators composed with the API
# --------------------------------------------------------------------------

def test_tr_operators_produce_consistent_credential_shape():
    """Each T_r operator is part of the public surface and produces
    arrays of the expected shape for the downstream estimator."""
    rng = np.random.default_rng(13)
    n = 64
    counts = np.full(n, 100, dtype=np.int64)
    s_red_ct = Tr_ct(counts, r=0.5, rng=rng)
    s_red_pet = Tr_pet(counts, r=0.5, rng=rng)
    floats = rng.normal(0, 1, size=n)
    s_red_mri = Tr_mri(floats, r=0.5, rng=rng)

    assert s_red_ct.shape == counts.shape
    assert s_red_pet.shape == counts.shape
    assert s_red_mri.shape == floats.shape
    # CT / PET sub-thinned values are non-negative integers
    assert (s_red_ct >= 0).all()
    assert (s_red_pet >= 0).all()
    # MRI mask zeroes out roughly half the entries (NaN sentinel)
    assert np.isnan(s_red_mri).any()


# --------------------------------------------------------------------------
# Verdict transitions across margin / cohort regimes
# --------------------------------------------------------------------------

def test_biased_candidate_fails_at_n500():
    """At Δ_true > ε and n = 500 the framework correctly FAILS the
    equivalence claim (the V3-9 power finding at non-AUC margin)."""
    rng = np.random.default_rng(14)
    a, b = _simulate_paired_dice(
        rng, n_patients=500, sigma_delta=0.05, delta_true=0.08,
    )
    cred = signal_equivalence_credential(
        paired_a=a, paired_b=b,
        signal_ratio=0.25, modality="CT",
        task=Task("dice", metric="dice"),
        subpopulation="test_v1",
        epsilon=0.02, alpha=0.05,
        n_bootstrap=2000, seed=14,
    )
    assert cred.credential.verdict == Verdict.FAIL


def test_boundary_delta_yields_indeterminate_distribution():
    """At Δ_true ≈ ε and modest n the framework returns INDETERMINATE in
    the majority of trials (boundary behaviour from §4b / §4c)."""
    indet_n = 0
    n_trials = 20
    base_rng = np.random.default_rng(15)
    for _ in range(n_trials):
        a, b = _simulate_paired_dice(
            base_rng, n_patients=100, sigma_delta=0.05, delta_true=0.02,
        )
        cred = signal_equivalence_credential(
            paired_a=a, paired_b=b,
            signal_ratio=0.25, modality="CT",
            task=Task("dice", metric="dice"),
            subpopulation="test_v1",
            epsilon=0.02, alpha=0.05,
            n_bootstrap=1000,
            seed=int(base_rng.integers(0, 2**32)),
        )
        if cred.credential.verdict == Verdict.INDETERMINATE:
            indet_n += 1
    # At ε boundary, INDETERMINATE should dominate (per §4b 94% empirical)
    assert indet_n >= 16  # ≥ 80% INDETERMINATE
