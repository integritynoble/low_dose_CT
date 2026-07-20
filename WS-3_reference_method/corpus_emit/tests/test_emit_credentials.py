"""Tests for the WS-3 credential-emission step.

Run from the corpus_emit/ directory with the WS-2 library importable:

    PYTHONPATH=. pytest -q
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from emit_credentials import (
    AucScores,
    CredentialEmitError,
    PairedScores,
    StratumSpec,
    build_credential,
    dose_tag,
    emit_stratum_credential,
    rebuild_index,
    verify_corpus_credentials,
)
from pwm_dose_equivalence import CREDENTIAL_JSON_SCHEMA, audit_credential


# --------------------------------------------------------------------------- #
# Fixtures: synthetic score generators (stand in for frozen-detector outputs)
# --------------------------------------------------------------------------- #
def _equivalent_auc(n: int, seed: int) -> AucScores:
    """Candidate and reference draw from the same separable distributions."""
    rng = np.random.default_rng(seed)
    return AucScores(
        a_pos=rng.normal(0.65, 0.18, n),
        a_neg=rng.normal(0.35, 0.18, n),
        b_pos=rng.normal(0.65, 0.18, n),
        b_neg=rng.normal(0.35, 0.18, n),
    )


def _equivalent_dice(n: int, seed: int) -> PairedScores:
    rng = np.random.default_rng(seed)
    base = rng.uniform(0.80, 0.92, n)
    return PairedScores(paired_a=base + rng.normal(0, 0.01, n),
                        paired_b=base + rng.normal(0, 0.01, n))


def _auc_spec(**kw) -> StratumSpec:
    defaults = dict(
        task_name="lung_nodule_5mm", metric="auc", signal_ratio=0.25,
        subpopulation="adult_chest_pwm_l3_test_v1", epsilon=0.05,
        method="pwm_ref_v1", reference_method="full_dose_fbp", anatomy="chest",
    )
    defaults.update(kw)
    return StratumSpec(**defaults)


# --------------------------------------------------------------------------- #
# dose_tag
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("r,tag", [(0.10, "r010"), (0.25, "r025"), (0.50, "r050"), (1.0, "r100")])
def test_dose_tag(r, tag):
    assert dose_tag(r) == tag


@pytest.mark.parametrize("bad", [0.0, -0.1, 1.5])
def test_dose_tag_rejects_out_of_range(bad):
    with pytest.raises(ValueError):
        dose_tag(bad)


# --------------------------------------------------------------------------- #
# build_credential — shape + schema conformance + dispatch
# --------------------------------------------------------------------------- #
def test_build_auc_credential_conforms_to_schema():
    cred = build_credential(_auc_spec(), _equivalent_auc(300, seed=1))
    payload = cred.to_dict()
    # validate against the WS-2 published wire schema
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.validate(payload, CREDENTIAL_JSON_SCHEMA)
    assert payload["credential"]["task"]["metric"] == "auc"
    assert payload["credential"]["estimator"] == "delong"
    assert payload["credential"]["n_test"] == 600


def test_build_dice_credential_uses_percentile():
    spec = _auc_spec(task_name="liver_lesion", metric="dice",
                     subpopulation="adult_abdomen_pwm_l3_test_v1",
                     epsilon=0.03, anatomy="abdomen")
    cred = build_credential(spec, _equivalent_dice(200, seed=2))
    payload = cred.to_dict()
    assert payload["credential"]["task"]["metric"] == "dice"
    assert payload["credential"]["estimator"] == "percentile"


def test_build_rejects_mismatched_score_type():
    with pytest.raises(TypeError):
        build_credential(_auc_spec(), _equivalent_dice(50, seed=3))
    dice_spec = _auc_spec(metric="dice")
    with pytest.raises(TypeError):
        build_credential(dice_spec, _equivalent_auc(50, seed=3))


def test_built_credential_passes_audit():
    cred = build_credential(_auc_spec(), _equivalent_auc(300, seed=4))
    assert audit_credential(cred.to_dict()).ok


# --------------------------------------------------------------------------- #
# emit_stratum_credential — file landing + layout
# --------------------------------------------------------------------------- #
def test_emit_writes_to_expected_path(tmp_path: Path):
    out = emit_stratum_credential(tmp_path, _auc_spec(vendor="Siemens"),
                                  _equivalent_auc(300, seed=5))
    assert out == tmp_path / "credentials" / "lung_nodule_5mm" / "r025" / "pwm_ref_v1__Siemens.json"
    assert out.exists()
    payload = json.loads(out.read_text())
    assert payload["credential"]["verdict"] in {"PASS", "FAIL", "INDETERMINATE"}
    assert payload["framework_hash"].startswith("sha256:")


def test_emit_pooled_vendor_slug(tmp_path: Path):
    out = emit_stratum_credential(tmp_path, _auc_spec(vendor=None),
                                  _equivalent_auc(300, seed=6))
    assert out.name == "pwm_ref_v1__pooled.json"


def test_emit_blocks_on_failed_audit(tmp_path: Path, monkeypatch):
    # Force a credential whose stored verdict is inconsistent with its CI.
    import emit_credentials as ec

    good = build_credential(_auc_spec(), _equivalent_auc(300, seed=7))

    class _Tampered:
        def to_dict(self):
            d = good.to_dict()
            v = d["credential"]["verdict"]
            d["credential"]["verdict"] = "FAIL" if v != "FAIL" else "PASS"
            return d

    monkeypatch.setattr(ec, "build_credential", lambda *a, **k: _Tampered())
    with pytest.raises(CredentialEmitError):
        ec.emit_stratum_credential(tmp_path, _auc_spec(), _equivalent_auc(10, seed=7))


# --------------------------------------------------------------------------- #
# rebuild_index + verify_corpus_credentials
# --------------------------------------------------------------------------- #
def _populate(tmp_path: Path) -> None:
    emit_stratum_credential(tmp_path, _auc_spec(vendor="Siemens", signal_ratio=0.25),
                            _equivalent_auc(300, seed=10))
    emit_stratum_credential(tmp_path, _auc_spec(vendor="GE", signal_ratio=0.10, epsilon=0.05),
                            _equivalent_auc(300, seed=11))
    emit_stratum_credential(
        tmp_path,
        _auc_spec(task_name="liver_lesion", metric="dice",
                  subpopulation="adult_abdomen_pwm_l3_test_v1",
                  epsilon=0.03, vendor="Siemens", anatomy="abdomen"),
        _equivalent_dice(200, seed=12),
    )


def test_rebuild_index_one_line_per_credential(tmp_path: Path):
    _populate(tmp_path)
    index = rebuild_index(tmp_path)
    lines = [json.loads(ln) for ln in index.read_text().splitlines()]
    assert len(lines) == 3
    # required query fields present
    for row in lines:
        assert {"path", "task", "metric", "signal_ratio", "verdict",
                "delta_ci_low", "delta_ci_high", "framework_hash", "audit_ok"} <= row.keys()
        assert row["audit_ok"] is True
    # stable sort by path
    assert [r["path"] for r in lines] == sorted(r["path"] for r in lines)


def test_index_excludes_itself_on_rebuild(tmp_path: Path):
    _populate(tmp_path)
    rebuild_index(tmp_path)
    index = rebuild_index(tmp_path)  # second pass must not ingest the jsonl
    lines = index.read_text().splitlines()
    assert len(lines) == 3


def test_verify_corpus_all_ok(tmp_path: Path):
    _populate(tmp_path)
    report = verify_corpus_credentials(tmp_path)
    assert report["n_credentials"] == 3
    assert report["ok"] is True
    assert report["failures"] == []


def test_verify_corpus_flags_tampered_file(tmp_path: Path):
    _populate(tmp_path)
    # hand-tamper one credential on disk
    victim = next((tmp_path / "credentials").rglob("*.json"))
    payload = json.loads(victim.read_text())
    payload["credential"]["delta_ci_low"] = 99.0  # CI no longer brackets delta_mean
    victim.write_text(json.dumps(payload))
    report = verify_corpus_credentials(tmp_path)
    assert report["ok"] is False
    assert any(victim.name in f["path"] for f in report["failures"])
