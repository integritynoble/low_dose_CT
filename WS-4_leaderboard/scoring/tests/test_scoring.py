"""Tests for the WS-4 scoring service (paired gate + permanent blur trap)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scoring import (BLUR_ENTRY_ID, add_submission, blur_entry, check_paired_submission,
                     check_submission_result, load, new_leaderboard, save,
                     sort_entries)


def paired_metrics(psnr=15.0, ssim=0.8, cnr=4.2, auc=0.93, npwe=123.0, task="SKE-Gaussian20HU-s2px"):
    return {"psnr_db": psnr, "ssim": ssim, "cnr_mean": cnr,
            "cho_auc_mean": auc, "npwe_mean": npwe, "task": task}


def test_seed_entries_include_permanent_blur_trap():
    board = new_leaderboard()
    ids = {e["id"] for e in board["entries"]}
    assert BLUR_ENTRY_ID in ids
    assert "seed-ws3-reference" in ids
    blur = blur_entry(board["entries"])
    assert blur["permanent"] is True
    assert blur["trap"] is True
    assert blur["config"] == {"sigma_px": 1.0, "kernel_size": 5, "module": "pwm_ldct_recon.models.GaussianBlur (WS-3)"}


def test_seed_blur_is_detectability_low_psnr_high():
    blur = blur_entry(new_leaderboard()["entries"])
    assert blur["metrics"]["psnr_db"] > 15
    assert blur["metrics"]["cnr_mean"] < 3.0  # below Rose criterion


def test_task_spec_matches_ws3():
    board = new_leaderboard()
    t = board["task"]
    assert t["label"] == "SKE-Gaussian20HU-s2px"
    assert t["signal"]["sigma_px"] == 2.0
    assert t["signal"]["peak_contrast_hu"] == 20.0
    assert t["signal"]["location_known"] is True
    assert t["observer"]["cho"]["channels"] == "dog"
    assert t["observer"]["cho"]["n_channels"] == 4
    assert t["observer"]["cnr"]["rose_criterion"] == 3.0
    assert t["observer"]["npwe"]["eye_filter"] == "rho*exp(-rho/0.2)"


def test_paired_gate_accepts_paired_metrics():
    assert check_paired_submission(paired_metrics()) == []


def test_paired_gate_rejects_fidelity_without_detectability():
    errs = check_paired_submission({"psnr_db": 15.0, "ssim": 0.8})
    assert any("both numbers or neither" in e for e in errs)


def test_paired_gate_rejects_detectability_without_fidelity():
    errs = check_paired_submission({"cnr_mean": 4.2, "cho_auc_mean": 0.93})
    assert any("both numbers or neither" in e for e in errs)


def test_paired_gate_rejects_empty():
    assert check_paired_submission({}) != []


def test_ws3_runbundle_format_accepted(tmp_path):
    """A WS-3 RunBundle results.json (validation.paired_methods) passes the gate."""
    result = {
        "ok": True,
        "validation": {
            "psnr_db": 8.5, "ssim": 1e-4,
            "paired_methods": {
                "reference": {"name": "reference", "psnr_db": 8.5, "ssim": 1e-4,
                              "detectability": paired_metrics(cnr=None, auc=0.5)},
                "blur": {"name": "blur", "psnr_db": 20.8, "ssim": 0.66,
                         "detectability": paired_metrics(cnr=0.011, auc=1.0)},
            },
            "paired_methods_ok": True,
        },
    }
    violations = check_submission_result(result)
    assert violations == {"reference": [], "blur": []}


def test_submit_accepts_paired_and_keeps_trap(tmp_path):
    board = new_leaderboard()
    result = {"validation": {"paired_methods": {
        "mymethod": {"psnr_db": 17.0, "ssim": 0.9,
                     "detectability": paired_metrics(cnr=5.1, auc=0.97)}}}}
    created = add_submission(board, result, method="MyMethod")
    assert len(created) == 1
    assert blur_entry(board["entries"]) is not None  # trap still present
    assert len(board["entries"]) == 3


def test_submit_rejects_unpaired(tmp_path):
    board = new_leaderboard()
    result = {"validation": {"paired_methods": {
        "bad": {"psnr_db": 17.0, "ssim": 0.9, "detectability": None}}}}
    with pytest.raises(ValueError, match="not publishable"):
        add_submission(board, result, method="BadMethod")


def test_save_rejects_missing_trap(tmp_path):
    board = new_leaderboard()
    board["entries"] = [e for e in board["entries"] if e["id"] != BLUR_ENTRY_ID]
    with pytest.raises(ValueError, match="permanent Gaussian blur trap missing"):
        save(board, tmp_path / "board.json")


def test_sort_is_detectability_first():
    board = new_leaderboard()
    entries = board["entries"]
    # blur CNR 0.011 vs reference CNR None: blur should rank above reference
    ranked = sort_entries(entries)
    assert ranked[0]["id"] == BLUR_ENTRY_ID


def test_roundtrip_load_save(tmp_path):
    p = tmp_path / "board.json"
    board = new_leaderboard()
    save(board, p)
    loaded = load(p)
    assert loaded["schema_version"] == board["schema_version"]
    assert blur_entry(loaded["entries"]) is not None


def test_cli_end_to_end(tmp_path):
    """init -> submit -> list through the public entrypoint."""
    import subprocess, sys
    board = tmp_path / "board.json"
    sub = tmp_path / "submission.json"
    sub.write_text(json.dumps({
        "validation": {"paired_methods": {
            "algo": {"psnr_db": 18.0, "ssim": 0.91,
                     "detectability": paired_metrics(cnr=6.0, auc=0.99)}}}}),
        encoding="utf-8")
    env_root = str(Path(__file__).resolve().parents[2])
    base = [sys.executable, "-m", "scoring.cli"]

    def run(*args):
        r = subprocess.run(base + list(args), cwd=env_root, capture_output=True, text=True)
        return r

    r = run("init", "--out", str(board))
    assert r.returncode == 0, r.stderr
    r = run("submit", "--result", str(sub), "--method", "MyAlgo", "--out", str(board))
    assert r.returncode == 0, r.stderr
    assert "accepted" in r.stdout
    r = run("list", "--leaderboard", str(board))
    assert r.returncode == 0, r.stderr
    assert "[TRAP]" in r.stdout
    assert "MyAlgo" in r.stdout
