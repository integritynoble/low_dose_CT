"""S1-S4 verification pipeline tests (Phase 1 task 1.2).

Coverage: S1 structure validation, S2 identity/claim/write-path gates, S3
published-vs-live numeric verification (runs locally), S4 publish-eligibility
pre-check. The S3 *sandbox execution* itself is a container/data-machine
runtime dependency (``[UNRESOLVED]`` in ``scoring/spec.md``); the pipeline
reports it as SKIPPED and this suite asserts exactly that.
"""
from __future__ import annotations

import json

import pytest

from scoring import (Verdict, check_claim_and_provenance,
                     check_publish_eligibility, check_runbundle_structure,
                     new_leaderboard, verify_published_vs_live,
                     verify_runbundle)
from scoring import gates as G
from scoring.task_spec import TASK_LABEL
from scoring.verify import PROTOCOL_ID, provenance_sha256


def _valid_result() -> dict:
    manifest = {"patients": ["aapm-0003", "aapm-0005"], "dose_grid": ["r025"]}
    weights = {"checkpoint": "model.pt", "framework": "torch", "sha": "abc123"}
    claim = {
        "task_id": TASK_LABEL,
        "protocol_id": PROTOCOL_ID,
        "data_manifest_sha256": provenance_sha256(manifest),
        "model_sha256": provenance_sha256(weights),
        "evaluator_version": "ws4-eval/v1",
    }
    return {
        "validation": {
            "paired_methods": {
                "my-method": {
                    "name": "my-method",
                    "psnr_db": 32.1,
                    "ssim": 0.91,
                    "detectability": {
                        "task": TASK_LABEL,
                        "bander_roi": 0.72,
                        "cnr_mean": 1.2,
                        "cho_auc_mean": 0.85,
                        "npwe_mean": 5.0,
                        "bander_full": 0.70,
                        "roi_tm_auc": 0.80,
                    },
                }
            }
        },
        "claim": claim,
        "evidence": {"data_manifest": manifest, "model_weights": weights},
    }


def _write_bundle(tmp_path, *, result=None, method_json=None,
                  files=("method.json", "eval.py", "results.json")):
    bundle = tmp_path / "runbundle"
    bundle.mkdir()
    if "method.json" in files:
        meta = method_json if method_json is not None else {
            "name": "my-method", "version": "1.0.0",
            "paper": "arxiv:2401.00000", "license": "CC-BY-4.0"}
        (bundle / "method.json").write_text(json.dumps(meta), encoding="utf-8")
    if "eval.py" in files:
        (bundle / "eval.py").write_text(
            "def main():\n    print('eval')\n", encoding="utf-8")
    if "results.json" in files:
        (bundle / "results.json").write_text(
            json.dumps(result if result is not None else _valid_result()),
            encoding="utf-8")
    return bundle


# --------------------------------------------------------------------------- S1

def test_s1_accepts_a_minimal_valid_runbundle(tmp_path):
    bundle = _write_bundle(tmp_path)
    assert check_runbundle_structure(bundle) == []


def test_s1_rejects_missing_required_files(tmp_path):
    bundle = _write_bundle(tmp_path, files=("method.json",))
    v = check_runbundle_structure(bundle)
    assert any("eval.py" in x for x in v)
    assert any("results.json" in x for x in v)


def test_s1_rejects_non_directory(tmp_path):
    assert check_runbundle_structure(tmp_path / "nope") != []


def test_s1_rejects_method_json_without_name(tmp_path):
    bundle = _write_bundle(tmp_path, method_json={"version": "1.0.0"})
    v = check_runbundle_structure(bundle)
    assert any("method.json.name" in x for x in v)


def test_s1_rejects_unknown_metric_fields(tmp_path):
    result = _valid_result()
    result["validation"]["paired_methods"]["my-method"]["psnr_extra"] = 1.0
    bundle = _write_bundle(tmp_path, result=result)
    v = check_runbundle_structure(bundle)
    assert any("psnr_extra" in x for x in v)


def test_s1_rejects_unknown_top_level_fields(tmp_path):
    result = _valid_result()
    result["totally_unknown"] = 1
    bundle = _write_bundle(tmp_path, result=result)
    v = check_runbundle_structure(bundle)
    assert any("totally_unknown" in x for x in v)


# --------------------------------------------------------------------------- S2

def test_s2_accepts_a_claim_bound_result():
    out = check_claim_and_provenance(_valid_result(), run_ws1_gates=False)
    assert not out["paired+task"]
    assert not out["claim"]
    assert not out["no_write_path"]


def test_s2_rejects_a_result_without_claim():
    result = _valid_result()
    del result["claim"]
    out = check_claim_and_provenance(result, run_ws1_gates=False)
    assert any("claim" in v.lower() for v in out["claim"])


def test_s2_rejects_a_wrong_task_label():
    result = _valid_result()
    result["validation"]["paired_methods"]["my-method"]["detectability"]["task"] = "other-task"
    out = check_claim_and_provenance(result, run_ws1_gates=False)
    assert any("not the WS-4 task" in v for v in out["paired+task"])


def test_s2_rejects_a_write_back_path():
    result = _valid_result()
    result["smuggled"] = "../data/leaderboard.json"
    out = check_claim_and_provenance(result, run_ws1_gates=False)
    assert any("referee-owned" in v for v in out["no_write_path"])


needs_ws1 = pytest.mark.skipif(not G.PAIRING_VALIDATION.exists(),
                               reason="WS-1_dataset/output not present beside WS-4")


@needs_ws1
def test_s2_rung_evidence_gates_pass_on_real_artifacts():
    out = check_claim_and_provenance(_valid_result(), run_ws1_gates=True)
    for label in ("rung_2", "rung_3", "rung_4"):
        assert not out.get(label), (label, out.get(label))


# --------------------------------------------------------------------------- S3

def test_s3_accepts_identical_published_and_live():
    result = _valid_result()
    assert verify_published_vs_live(result, json.loads(json.dumps(result))) == []


def test_s3_rejects_numeric_drift_beyond_r6_tolerance():
    published = _valid_result()
    live = json.loads(json.dumps(published))
    live["validation"]["paired_methods"]["my-method"]["psnr_db"] += 0.0000011
    v = verify_published_vs_live(published, live)
    assert any("numeric drift" in x for x in v)


def test_s3_rejects_structure_difference():
    published = _valid_result()
    live = json.loads(json.dumps(published))
    del live["claim"]
    v = verify_published_vs_live(published, live)
    assert any("extra field" in x for x in v)


# --------------------------------------------------------------------------- S4

def test_s4_rejects_a_board_without_publishable_claims():
    """The seed board carries no per-vendor submission claim yet, so the S4
    pre-check must reject publication (the real gate stays leaderboard.save())."""
    board = new_leaderboard()
    violations = check_publish_eligibility(board["entries"])
    assert any("vendor stratum" in v for v in violations)


def test_s4_rejects_an_empty_board():
    assert check_publish_eligibility([]) != []


# --------------------------------------------------------------------------- pipeline

def test_verify_runbundle_end_to_end_marks_s3_and_s4_skipped(tmp_path):
    """S1+S2 run locally; S3 needs the sandbox runtime, S4 needs the board."""
    bundle = _write_bundle(tmp_path)
    verdict = verify_runbundle(bundle, run_ws1_gates=False)
    assert isinstance(verdict, Verdict)
    assert not verdict.violations["S1"]
    assert not verdict.violations["S2"]
    assert "S3" in verdict.skipped
    assert "S4" in verdict.skipped
    assert not verdict.ok
    assert "INCOMPLETE" in verdict.summary()
    assert "ALL PASS" not in verdict.summary()


def test_verify_runbundle_reports_s1_rejections_first(tmp_path):
    bundle = _write_bundle(tmp_path, files=("method.json",))
    verdict = verify_runbundle(bundle, run_ws1_gates=False)
    assert verdict.violations["S1"]
    assert "S2" in verdict.skipped
    assert not verdict.ok


def test_verify_runbundle_s3_with_live_document(tmp_path):
    bundle = _write_bundle(tmp_path)
    live = json.loads(json.dumps(_valid_result()))
    verdict = verify_runbundle(bundle, live_result=live, run_ws1_gates=False)
    assert not verdict.violations.get("S3")
    assert "S3" not in verdict.skipped


@pytest.mark.parametrize("published,live", [(True, 1), (False, 0), (1, True)])
def test_s3_rejects_boolean_numeric_type_substitution(published, live):
    assert verify_published_vs_live({"value": published}, {"value": live})


def test_verdict_cannot_certify_skipped_rung_checks():
    verdict = Verdict(runbundle="example", skipped=["S2 rung gates disabled"])
    assert not verdict.ok
    assert "INCOMPLETE" in verdict.summary()
