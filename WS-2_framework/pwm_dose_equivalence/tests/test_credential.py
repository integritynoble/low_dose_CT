"""Tests for the Credential / SignalEquivalenceCredential dataclasses."""

from __future__ import annotations

import json

from pwm_dose_equivalence.credential import (
    Credential,
    SignalEquivalenceCredential,
    Task,
    Verdict,
)


def _make_credential():
    return SignalEquivalenceCredential(
        schema_version="pwm-signal-equivalence/v0.2",
        framework_hash="sha256:" + "0" * 64,
        credential=Credential(
            method="M",
            reference_method="M_ref",
            signal_ratio=0.25,
            modality="CT",
            task=Task(
                name="lung_nodule_5mm", metric="auc",
                target=0.95,
                ground_truth_protocol=(
                    "pwm-ldct/annotation-qa/v0.5#sha256:abc"
                ),
            ),
            subpopulation="adult_chest_pwm_l3_test_v1",
            epsilon=0.02,
            alpha=0.05,
            estimator="delong",
            n_test=200,
            n_bootstrap=0,
            seed=42,
            delta_mean=0.001,
            delta_ci_low=-0.015,
            delta_ci_high=0.017,
            verdict=Verdict.PASS,
            sample_size_check={
                "rule": "S3-auc-clt",
                "n_required": 130,
                "n_actual": 200,
                "ok": True,
            },
        ),
    )


def test_to_dict_serialises_verdict_to_string():
    c = _make_credential()
    d = c.to_dict()
    assert d["credential"]["verdict"] == "PASS"


def test_to_json_is_valid_json():
    c = _make_credential()
    s = c.to_json()
    json.loads(s)  # must not raise


def test_round_trip_via_json():
    c = _make_credential()
    s = c.to_json()
    c2 = SignalEquivalenceCredential.from_json(s)
    assert c2.schema_version == c.schema_version
    assert c2.framework_hash == c.framework_hash
    assert c2.credential.verdict == Verdict.PASS
    assert c2.credential.task.name == c.credential.task.name
    assert c2.credential.task.ground_truth_protocol == (
        c.credential.task.ground_truth_protocol
    )


def test_task_defaults_to_auc():
    t = Task("default_task")
    assert t.metric == "auc"
    assert t.target is None
    assert t.ground_truth_protocol is None


def test_from_dict_round_trip():
    c = _make_credential()
    d = c.to_dict()
    c2 = SignalEquivalenceCredential.from_dict(d)
    assert c2.to_dict() == d
