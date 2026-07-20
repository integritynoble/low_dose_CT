"""Tests for credential_schema.py + audit.py (L0.2.1)."""

from __future__ import annotations

import copy
import json

import numpy as np
import pytest

from pwm_dose_equivalence import (
    Task,
    framework_hash,
    signal_equivalence_credential,
)
from pwm_dose_equivalence.audit import (
    CredentialAudit,
    audit_credential,
)
from pwm_dose_equivalence.credential_schema import CREDENTIAL_JSON_SCHEMA


def _make_valid_credential_dict() -> dict:
    """Issue a real credential through the production API and return the dict."""
    rng = np.random.default_rng(0)
    deltas = rng.normal(0.0, 0.01, size=200)
    cred = signal_equivalence_credential(
        paired_a=np.zeros(200),
        paired_b=-deltas,
        signal_ratio=0.25,
        modality="CT",
        task=Task("liver_dice", metric="dice"),
        subpopulation="adult_abdomen_pwm_l3_test_v1",
        epsilon=0.05,
        alpha=0.05,
        n_bootstrap=500,
        seed=42,
        sigma_delta_hint=0.05,
    )
    return cred.to_dict()


# -- schema introspection ---------------------------------------------------

def test_schema_is_drafted_correctly():
    assert CREDENTIAL_JSON_SCHEMA["$schema"].startswith("http://json-schema.org/draft-07")
    assert set(CREDENTIAL_JSON_SCHEMA["required"]) == {
        "schema_version", "framework_hash", "credential",
    }
    cred_props = CREDENTIAL_JSON_SCHEMA["properties"]["credential"]["properties"]
    expected_credential_fields = {
        "method", "reference_method", "signal_ratio", "modality", "task",
        "subpopulation", "epsilon", "alpha", "estimator", "n_test",
        "n_bootstrap", "seed", "delta_mean", "delta_ci_low", "delta_ci_high",
        "verdict", "sample_size_check",
    }
    assert set(cred_props) == expected_credential_fields


def test_schema_is_serialisable():
    s = json.dumps(CREDENTIAL_JSON_SCHEMA)
    assert isinstance(s, str)
    roundtrip = json.loads(s)
    assert roundtrip == CREDENTIAL_JSON_SCHEMA


# -- happy path -------------------------------------------------------------

def test_valid_credential_audits_clean():
    d = _make_valid_credential_dict()
    report = audit_credential(d)
    assert report.ok is True
    assert report.schema_valid is True
    assert report.framework_hash_known is True
    assert report.verdict_self_consistent is True
    assert report.issues == []


def test_audit_accepts_json_string():
    d = _make_valid_credential_dict()
    s = json.dumps(d)
    report = audit_credential(s)
    assert report.ok is True
    assert isinstance(report, CredentialAudit)


# -- top-level error handling ----------------------------------------------

def test_invalid_json_string():
    report = audit_credential("not json")
    assert report.ok is False
    assert report.schema_valid is False
    assert any("not valid JSON" in i for i in report.issues)


def test_non_object_top_level():
    report = audit_credential([1, 2, 3])  # type: ignore[arg-type]
    assert report.ok is False
    assert report.schema_valid is False
    assert any("expected object" in i for i in report.issues)


# -- schema validity -------------------------------------------------------

def test_missing_required_top_level_field():
    d = _make_valid_credential_dict()
    del d["framework_hash"]
    report = audit_credential(d)
    assert report.schema_valid is False
    assert any("framework_hash" in i for i in report.issues)


def test_missing_required_inner_field():
    d = _make_valid_credential_dict()
    del d["credential"]["verdict"]
    report = audit_credential(d)
    assert report.schema_valid is False
    assert any("verdict" in i for i in report.issues)


def test_unexpected_top_level_field():
    d = _make_valid_credential_dict()
    d["extra_field"] = "tamper"
    report = audit_credential(d)
    assert report.schema_valid is False
    assert any("unexpected field" in i for i in report.issues)


def test_bad_framework_hash_format():
    d = _make_valid_credential_dict()
    d["framework_hash"] = "md5:abc123"
    report = audit_credential(d)
    assert report.schema_valid is False
    assert any("pattern" in i for i in report.issues)


def test_bad_verdict_enum():
    d = _make_valid_credential_dict()
    d["credential"]["verdict"] = "MAYBE"
    report = audit_credential(d)
    assert report.schema_valid is False
    assert any("enum" in i for i in report.issues)


def test_bad_estimator_enum():
    d = _make_valid_credential_dict()
    d["credential"]["estimator"] = "jackknife"
    report = audit_credential(d)
    assert report.schema_valid is False
    assert any("enum" in i for i in report.issues)


def test_signal_ratio_out_of_range():
    d = _make_valid_credential_dict()
    d["credential"]["signal_ratio"] = 1.5
    report = audit_credential(d)
    assert report.schema_valid is False
    assert any("maximum" in i for i in report.issues)


def test_signal_ratio_zero_rejected():
    d = _make_valid_credential_dict()
    d["credential"]["signal_ratio"] = 0.0
    report = audit_credential(d)
    assert report.schema_valid is False
    assert any("exclusiveMinimum" in i for i in report.issues)


def test_epsilon_negative_rejected():
    d = _make_valid_credential_dict()
    d["credential"]["epsilon"] = -0.05
    report = audit_credential(d)
    assert report.schema_valid is False


def test_alpha_at_one_rejected():
    d = _make_valid_credential_dict()
    d["credential"]["alpha"] = 1.0
    report = audit_credential(d)
    assert report.schema_valid is False
    assert any("exclusiveMaximum" in i for i in report.issues)


def test_n_test_zero_rejected():
    d = _make_valid_credential_dict()
    d["credential"]["n_test"] = 0
    report = audit_credential(d)
    assert report.schema_valid is False
    assert any("minimum" in i for i in report.issues)


def test_wrong_type_for_numeric_field():
    d = _make_valid_credential_dict()
    d["credential"]["delta_mean"] = "not a number"
    report = audit_credential(d)
    assert report.schema_valid is False


def test_bad_task_metric_enum():
    d = _make_valid_credential_dict()
    d["credential"]["task"]["metric"] = "f1"
    report = audit_credential(d)
    assert report.schema_valid is False


def test_arbitrary_modality_string_accepted():
    """Per R3-3 the API accepts arbitrary modality strings."""
    d = _make_valid_credential_dict()
    d["credential"]["modality"] = "Optical"
    report = audit_credential(d)
    assert report.schema_valid is True
    assert report.ok is True


# -- framework-hash recognition --------------------------------------------

def test_unknown_framework_hash_is_warning_not_issue():
    d = _make_valid_credential_dict()
    d["framework_hash"] = "sha256:" + "a" * 64
    report = audit_credential(d)
    assert report.schema_valid is True
    assert report.framework_hash_known is False
    assert any("does not match" in w for w in report.warnings)


def test_known_framework_hash_no_warning():
    d = _make_valid_credential_dict()
    assert d["framework_hash"] == framework_hash()
    report = audit_credential(d)
    assert report.framework_hash_known is True
    assert not any("does not match" in w for w in report.warnings)


# -- verdict self-consistency ---------------------------------------------

def test_tampered_verdict_is_caught():
    d = _make_valid_credential_dict()
    original = d["credential"]["verdict"]
    # Flip to a verdict the CI does not support
    if original == "PASS":
        d["credential"]["verdict"] = "FAIL"
    else:
        d["credential"]["verdict"] = "PASS"
    report = audit_credential(d)
    assert report.verdict_self_consistent is False
    assert report.ok is False
    assert any("verdict" in i for i in report.issues)


def test_pass_boundary_just_inside():
    """CI strictly inside (-epsilon, epsilon) -> PASS."""
    d = _make_valid_credential_dict()
    d["credential"]["delta_ci_low"] = -0.04
    d["credential"]["delta_ci_high"] = 0.04
    d["credential"]["delta_mean"] = 0.0
    d["credential"]["epsilon"] = 0.05
    d["credential"]["verdict"] = "PASS"
    report = audit_credential(d)
    assert report.verdict_self_consistent is True


def test_fail_boundary_just_outside():
    """CI entirely above +epsilon -> FAIL."""
    d = _make_valid_credential_dict()
    d["credential"]["delta_ci_low"] = 0.06
    d["credential"]["delta_ci_high"] = 0.08
    d["credential"]["delta_mean"] = 0.07
    d["credential"]["epsilon"] = 0.05
    d["credential"]["verdict"] = "FAIL"
    report = audit_credential(d)
    assert report.verdict_self_consistent is True


def test_indeterminate_straddling_boundary():
    d = _make_valid_credential_dict()
    d["credential"]["delta_ci_low"] = -0.06
    d["credential"]["delta_ci_high"] = 0.02
    d["credential"]["delta_mean"] = -0.02
    d["credential"]["epsilon"] = 0.05
    d["credential"]["verdict"] = "INDETERMINATE"
    report = audit_credential(d)
    assert report.verdict_self_consistent is True


# -- sanity on the CI itself ----------------------------------------------

def test_inverted_ci_is_caught():
    d = _make_valid_credential_dict()
    d["credential"]["delta_ci_low"], d["credential"]["delta_ci_high"] = (
        d["credential"]["delta_ci_high"], d["credential"]["delta_ci_low"],
    )
    if d["credential"]["delta_ci_low"] == d["credential"]["delta_ci_high"]:
        d["credential"]["delta_ci_low"] = 0.5
        d["credential"]["delta_ci_high"] = -0.5
    report = audit_credential(d)
    assert report.ok is False
    assert any("delta_ci_low > delta_ci_high" in i for i in report.issues)


def test_delta_mean_outside_ci_is_caught():
    d = _make_valid_credential_dict()
    d["credential"]["delta_ci_low"] = 0.0
    d["credential"]["delta_ci_high"] = 0.01
    d["credential"]["delta_mean"] = 0.5  # way outside
    d["credential"]["epsilon"] = 0.05
    d["credential"]["verdict"] = "PASS"
    report = audit_credential(d)
    assert report.ok is False
    assert any("delta_mean falls outside" in i for i in report.issues)


# -- sample-size check coherence ------------------------------------------

def test_sample_size_check_ok_propagates():
    d = _make_valid_credential_dict()
    assert "ok" in d["credential"]["sample_size_check"]
    report = audit_credential(d)
    assert report.sample_size_check_ok is d["credential"]["sample_size_check"]["ok"]


def test_undersized_pass_warning():
    d = _make_valid_credential_dict()
    d["credential"]["sample_size_check"] = {
        "rule": "S1-clt",
        "sigma_delta_hint": 0.05,
        "n_required_clt": 9999,
        "n_actual": d["credential"]["n_test"],
        "ok": False,
    }
    d["credential"]["verdict"] = "PASS"
    # PASS verdict requires consistent CI; force one
    d["credential"]["delta_ci_low"] = -0.01
    d["credential"]["delta_ci_high"] = 0.01
    d["credential"]["delta_mean"] = 0.0
    d["credential"]["epsilon"] = 0.05
    report = audit_credential(d)
    assert report.sample_size_check_ok is False
    assert any("undersized" in w.lower() or "below the formula" in w.lower()
               for w in report.warnings)


def test_no_sample_size_check_gives_none():
    d = _make_valid_credential_dict()
    d["credential"]["sample_size_check"] = {}
    report = audit_credential(d)
    assert report.sample_size_check_ok is None


# -- estimator-specific soft signals --------------------------------------

def test_delong_with_nonzero_bootstrap_warns():
    d = _make_valid_credential_dict()
    d["credential"]["estimator"] = "delong"
    d["credential"]["n_bootstrap"] = 10_000
    report = audit_credential(d)
    assert any("closed-form" in w for w in report.warnings)


def test_bca_estimator_emits_opt_in_warning():
    d = _make_valid_credential_dict()
    d["credential"]["estimator"] = "bca"
    report = audit_credential(d)
    assert any("opt-in" in w for w in report.warnings)
    # BCa warning does not flip `ok` (it is a soft signal)
    assert report.ok is True


# -- internal schema-walker guardrail -------------------------------------

def test_check_type_rejects_unsupported_json_type():
    """The raise-ValueError fallback guards against schema-spec mistakes."""
    from pwm_dose_equivalence.audit import _check_type
    with pytest.raises(ValueError, match="unsupported JSON type"):
        _check_type([1, 2], "array")  # we deliberately do not support arrays


# -- robustness to deep copying -------------------------------------------

def test_audit_does_not_mutate_input():
    d = _make_valid_credential_dict()
    snapshot = copy.deepcopy(d)
    audit_credential(d)
    assert d == snapshot
