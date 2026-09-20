"""Tests for WS-4 P1-3 (held-out isolation) / P1-4 (spread) / P2-5 (observer
sensitivity) / P3-6 (Rung registry)."""
from __future__ import annotations

import json

import pytest

from scoring import (BLUR_ENTRY_ID, OWN_PRINCIPAL, SubmissionEnvelope,
                     add_submission, assert_no_write_path, authorize_write,
                     compute_spread, make_heldout_set, new_leaderboard,
                     publish_observer_channels, rank_shift_report,
                     referee_append, render_markdown, report_observer_sensitivity,
                     update_status, validate_registry)
from scoring.heldout import (HELDOUT_FILE_NAME, LEADERBOARD_FILE_NAME,
                             check_submission_cannot_write_back)
from scoring.task_spec import TASK_LABEL
from scoring.verify import provenance_sha256


def claim_block():
    """§2-D: a self-consistent claim + evidence block bound to the WS-4 task."""
    manifest = {"corpus": "LIDC lowdose_sim", "r": 0.25, "seed": 42, "n_patients": 2}
    weights = {"arch": "conv", "params": 1000}
    return {
        "claim": {
            "task_id": TASK_LABEL,
            "protocol_id": "detectability-freq-v1",
            "data_manifest_sha256": provenance_sha256(manifest),
            "model_sha256": provenance_sha256(weights),
            "evaluator_version": "pwm_ldct_recon-2026-09-14",
        },
        "evidence": {"data_manifest": manifest, "model_weights": weights},
    }


# --------------------------------------------------------------------------- #
# P1-3 held-out isolation
# --------------------------------------------------------------------------- #

def test_heldout_set_is_frozen_and_readonly():
    hs = make_heldout_set(id="ho-1", records=[("case", "a"), ("case", "b")])
    assert len(hs) == 2
    assert list(hs) == [("case", "a"), ("case", "b")]
    assert hs.authorized_by == OWN_PRINCIPAL
    with pytest.raises(Exception):
        hs.records = ()  # frozen dataclass rejects attribute assignment


def test_heldout_set_exposes_no_write_surface():
    hs = make_heldout_set(id="ho-1", records=[1, 2, 3])
    assert assert_no_write_path(hs) == []


def test_referee_append_requires_own():
    hs = make_heldout_set(id="ho-1", records=[1])
    with pytest.raises(PermissionError):
        referee_append(hs, [2], authorized_by="some-method-name")
    grown = referee_append(hs, [2], authorized_by=OWN_PRINCIPAL)
    assert len(grown) == 2
    assert len(hs) == 1  # original untouched


def test_submission_envelope_cannot_write_back():
    ok = SubmissionEnvelope(method_name="MyMethod",
                            result={"validation": {"paired_methods": {}}})
    assert check_submission_cannot_write_back(ok) == []


def test_submission_with_write_surface_rejected():
    """A non-container object carrying a callable write method is rejected."""
    class Attacker:
        def write(self):  # noqa: D401 - simulated smuggled write handle
            pass

    bad = SubmissionEnvelope(
        method_name="attacker",
        result={"validation": {"paired_methods": {}}, "hidden": Attacker()})
    violations = check_submission_cannot_write_back(bad)
    assert any("write surface" in v for v in violations)


def test_submission_referencing_referee_files_rejected():
    bad = SubmissionEnvelope(
        method_name="attacker",
        result={"save_to": f"../scoring/data/{LEADERBOARD_FILE_NAME}"})
    violations = check_submission_cannot_write_back(bad)
    assert any("referee-owned files" in v for v in violations)


def test_submission_referencing_heldout_rejected():
    bad = SubmissionEnvelope(
        method_name="attacker",
        result={"read": f"../scoring/data/{HELDOUT_FILE_NAME}"})
    violations = check_submission_cannot_write_back(bad)
    assert any("referee-owned files" in v for v in violations)


def test_authorize_write_only_own():
    assert authorize_write(OWN_PRINCIPAL) is True
    assert authorize_write("any-submitter") is False


def test_cli_submit_runs_write_back_gate():
    """The CLI rejects a submission that smuggles a referee path."""
    import subprocess, sys
    from pathlib import Path
    env_root = str(Path(__file__).resolve().parents[2])
    sub = Path(__file__).resolve().parent / "tmp_smuggled_submission.json"
    sub.write_text(json.dumps({
        "validation": {"paired_methods": {
            "algo": {"psnr_db": 18.0, "ssim": 0.91,
                     "detectability": {"cnr_mean": 6.0, "cho_auc_mean": 0.99,
                                       "task": "SKE-Gaussian20HU-s2px"}}}},
        "save_to": f"../data/{LEADERBOARD_FILE_NAME}"}), encoding="utf-8")
    try:
        r = subprocess.run(
            [sys.executable, "-m", "scoring.cli", "submit",
             "--result", str(sub), "--method", "Attacker",
             "--out", str(sub.with_name("tmp_board.json"))],
            cwd=env_root, capture_output=True, text=True)
        assert r.returncode == 1
        assert "REJECT" in r.stdout
    finally:
        sub.unlink(missing_ok=True)


# --------------------------------------------------------------------------- #
# P1-4 spread
# --------------------------------------------------------------------------- #

def test_spread_by_vendor_and_dose():
    board = new_leaderboard()
    result = {"validation": {"paired_methods": {
        "m1": {"psnr_db": 16.0, "ssim": 0.8,
               "detectability": {"cnr_mean": 5.0, "cho_auc_mean": 0.9,
                                 "bander_roi": 0.63,
                                 "task": "SKE-Gaussian20HU-s2px"}}}}}
    result.update(claim_block())
    add_submission(board, result, method="M1", vendor="Siemens", dose="0.25")
    add_submission(board, result, method="M1", vendor="GE", dose="0.25")
    add_submission(board, result, method="M1", vendor="Siemens", dose="0.50")

    spread_v = compute_spread(board["entries"], by="vendor")
    assert set(spread_v) == {"Siemens", "GE"}
    assert spread_v["Siemens"]["n_entries"] == 2
    assert spread_v["Siemens"]["psnr_db_span"] == 0.0
    assert spread_v["Siemens"]["cnr_mean_span"] == 0.0
    assert "cnr_mean_std" in spread_v["Siemens"]
    # bander_roi must survive extract_paired_methods into the entry metrics and
    # reach the spread block. Before 2026-09-04 it was dropped during extraction,
    # so compute_spread's bander_roi branch and leaderboard.py's carry-through
    # were both unreachable.
    assert spread_v["Siemens"]["bander_roi_span"] == 0.0
    assert "bander_roi_std" in spread_v["Siemens"]

    spread_d = compute_spread(board["entries"], by="dose")
    assert set(spread_d) == {"0.25", "0.50"}


def test_seed_entries_have_no_vendor_dose():
    board = new_leaderboard()
    assert compute_spread(board["entries"], by="vendor") == {}


def test_submission_updates_board_spread_block():
    board = new_leaderboard()
    result = {"validation": {"paired_methods": {
        "m1": {"psnr_db": 16.0, "ssim": 0.8,
               "detectability": {"cnr_mean": 5.0, "cho_auc_mean": 0.9,
                                 "bander_roi": 0.63,
                                 "task": "SKE-Gaussian20HU-s2px"}}}}}
    result.update(claim_block())
    add_submission(board, result, method="M1", vendor="Siemens", dose="0.25")
    assert board["spread"]["Siemens"]["n_entries"] == 1


# --------------------------------------------------------------------------- #
# P2-5 observer sensitivity
# --------------------------------------------------------------------------- #

def test_observer_channels_published():
    channels = publish_observer_channels()
    assert channels["observers"][0]["name"] == "CNR+CHO(DOG-4)+NPWE"
    assert channels["observers"][1]["cho"]["n_channels"] == 6
    for obs in channels["observers"]:
        assert "internal_noise" in obs
        assert obs["internal_noise"]["sigma"] > 0


def test_rank_shift_report_structure():
    board = new_leaderboard()
    report = rank_shift_report(board["entries"], seed=7)
    assert report["synthetic"] is True
    assert report["spearman_rho"] == pytest.approx(1.0)  # monotone-ish transform keeps order
    ids = {e["id"] for e in report["entries"]}
    assert BLUR_ENTRY_ID in ids
    for e in report["entries"]:
        assert "rank_shift" in e and "trap_flip" in e


def test_observer_sensitivity_markdown():
    board = new_leaderboard()
    md = report_observer_sensitivity(board["entries"], seed=7, markdown=True)
    assert "## Observer sensitivity" in md
    assert "Spearman rho" in md
    assert "| id |" in md


# --------------------------------------------------------------------------- #
# P3-6 Rung registry
# --------------------------------------------------------------------------- #

def test_registry_has_rungs_1_to_6():
    reg = {
        "schema_version": "0.1.0",
        "updated_at": "t",
        "rungs": [
            {"rung": i, "title": f"R{i}", "status": "partial", "reason": "r",
             "gate": "g"}
            for i in range(1, 7)],
    }
    assert validate_registry(reg) == []


def test_registry_missing_rung_reported():
    reg = {"rungs": [{"rung": 1, "title": "x", "status": "done", "gate": "g"}]}
    errs = validate_registry(reg)
    assert any("missing rung 2" in e for e in errs)


def test_registry_bad_status_reported():
    reg = {"rungs": [
        {"rung": i, "title": f"R{i}", "status": "oops", "reason": "r", "gate": "g"}
        for i in range(1, 7)]}
    assert validate_registry(reg) != []


def test_update_status_validated():
    reg = {"rungs": [
        {"rung": i, "title": f"R{i}", "status": "partial", "reason": "r", "gate": "g"}
        for i in range(1, 7)]}
    update_status(reg, 2, "done", reason="independently recomputed")
    assert reg["rungs"][1]["status"] == "done"
    with pytest.raises(ValueError):
        update_status(reg, 1, "not-a-status")


def test_registry_markdown_renders_table():
    reg = {"schema_version": "0.1.0", "updated_at": "t", "rungs": [
        {"rung": 1, "title": "Detectability", "status": "partial",
         "supported_data": ["SKE"], "reason": "no run", "gate": "verify.py"}]}
    md = render_markdown(reg)
    assert "| Rung |" in md and "**partial**" in md and "`verify.py`" in md
