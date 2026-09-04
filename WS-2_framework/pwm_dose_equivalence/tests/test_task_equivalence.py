"""Tests of the task-equivalence (observer detectability) extension.

P1-1: the 5-tuple signal credential is upgraded to a *task* credential by
requiring the observer-model detectability dimension — at equivalent dose the
population-mean detectability of the candidate on reduced-signal scans must be
within epsilon of the reference on full-signal scans. The observer
specification is the shared WS-1 / WS-3 SKE-Gaussian task (20 HU, sigma=2 px,
location known, tissue ROI HU band).
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from pwm_dose_equivalence.task_equivalence import (
    TASK_EQUIVALENCE_JSON_SCHEMA,
    ObserverSpec,
    TaskEquivalenceCredential,
    task_equivalence_credential,
)

#: Shared observer specification (WS-1 task_spec.json v0.5 / WS-3 observers.py).
SKE_OBSERVER = ObserverSpec(observer="cho")


def _paired_detectability(rng: np.random.Generator, n: int = 64,
                          full_mean: float = 0.90,
                          reduced_offset: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    """Per-slice CHO AUC measurements: full-dose reference vs reduced-signal."""
    full = rng.normal(full_mean, 0.02, size=n)
    reduced = rng.normal(full_mean + reduced_offset, 0.02, size=n)
    return reduced, full


def test_equivalent_detectability_passes():
    """Reduced-signal detectability equal to full-signal reference → PASS."""
    rng = np.random.default_rng(0)
    red, full = _paired_detectability(rng, reduced_offset=0.0)
    cred = task_equivalence_credential(
        detectability_reduced=red,
        detectability_full=full,
        observer_spec=SKE_OBSERVER,
        signal_ratio=0.25,
        modality="CT",
        subpopulation="ws1_test_v0.5",
        epsilon=0.05,
        alpha=0.05,
        n_bootstrap=2000,
        seed=1,
    )
    assert cred.credential.verdict.value == "PASS"
    assert cred.credential.task.name == "SKE-Gaussian20HU-s2px"
    assert cred.credential.task.metric == "auc"
    assert cred.observer_spec == SKE_OBSERVER


def test_detectability_loss_fails():
    """A method whose reduced-signal detectability drops by > epsilon → FAIL."""
    rng = np.random.default_rng(0)
    red, full = _paired_detectability(rng, full_mean=0.90, reduced_offset=-0.25)
    cred = task_equivalence_credential(
        detectability_reduced=red,
        detectability_full=full,
        observer_spec=SKE_OBSERVER,
        signal_ratio=0.25,
        modality="CT",
        subpopulation="ws1_test_v0.5",
        epsilon=0.05,
        alpha=0.05,
        n_bootstrap=2000,
        seed=1,
    )
    assert cred.credential.verdict.value == "FAIL"
    # The detectability summary records the cohort-level numbers verbatim
    assert cred.detectability_summary["detectability_diff_mean"] < -0.2


def test_pet_contrast_recovery_observer():
    """PET phantom endpoint uses NEMA contrast recovery, not CT detectability."""
    rng = np.random.default_rng(0)
    red = rng.normal(0.85, 0.03, size=12)
    full = rng.normal(0.85, 0.03, size=12)
    spec = ObserverSpec(observer="contrast_recovery",
                        label="NEMA-CRC-4to1-SBR")
    cred = task_equivalence_credential(
        detectability_reduced=red,
        detectability_full=full,
        observer_spec=spec,
        signal_ratio=0.25,
        modality="PET",
        subpopulation="pwm_pet_iq_1.0",
        epsilon=0.05,
        alpha=0.05,
        n_bootstrap=2000,
        seed=1,
    )
    assert cred.credential.task.metric == "contrast_recovery"
    assert cred.credential.verdict.value == "PASS"


def test_json_round_trip_keeps_observer_spec():
    rng = np.random.default_rng(0)
    red, full = _paired_detectability(rng, reduced_offset=0.0)
    cred = task_equivalence_credential(
        detectability_reduced=red,
        detectability_full=full,
        observer_spec=SKE_OBSERVER,
        signal_ratio=0.25,
        modality="CT",
        subpopulation="ws1_test_v0.5",
        epsilon=0.05,
        alpha=0.05,
        n_bootstrap=2000,
        seed=1,
    )
    parsed = TaskEquivalenceCredential.from_json(cred.to_json())
    assert parsed.observer_spec == cred.observer_spec
    assert parsed.detectability_summary == cred.detectability_summary
    assert parsed.credential.verdict == cred.credential.verdict
    assert parsed.framework_hash == cred.framework_hash


def test_schema_validates_credential():
    """The task-equivalence JSON schema accepts a serialised credential."""
    import jsonschema

    rng = np.random.default_rng(0)
    red, full = _paired_detectability(rng, reduced_offset=0.0)
    cred = task_equivalence_credential(
        detectability_reduced=red,
        detectability_full=full,
        observer_spec=SKE_OBSERVER,
        signal_ratio=0.25,
        modality="CT",
        subpopulation="ws1_test_v0.5",
        epsilon=0.05,
        alpha=0.05,
        n_bootstrap=2000,
        seed=1,
    )
    jsonschema.validate(instance=json.loads(cred.to_json()),
                        schema=TASK_EQUIVALENCE_JSON_SCHEMA)


def test_observer_metric_mapping():
    assert ObserverSpec(observer="cho").task_metric == "auc"
    assert ObserverSpec(observer="cnr").task_metric == "mae"
    assert ObserverSpec(observer="npwe").task_metric == "mae"
    assert ObserverSpec(observer="contrast_recovery").task_metric == "contrast_recovery"


def test_mismatched_lengths_raise():
    rng = np.random.default_rng(0)
    red = rng.normal(0.9, 0.02, size=32)
    full = rng.normal(0.9, 0.02, size=64)
    with pytest.raises(ValueError):
        task_equivalence_credential(
            detectability_reduced=red,
            detectability_full=full,
            observer_spec=SKE_OBSERVER,
            signal_ratio=0.25,
            modality="CT",
            subpopulation="ws1_test_v0.5",
            epsilon=0.05,
            alpha=0.05,
        )
