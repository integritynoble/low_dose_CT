"""§2 (HEYANG_NEXT 2026-09-15) invalid-evidence-acceptance gate fixtures & tests.

Covers, per gate:

* A task identity: ``check_paired_submission`` refuses a missing / unrelated /
  non-string ``task`` field; the valid fixture carries ``TASK_LABEL``.
* B mandatory strata: ``trap_rank_by_group`` refuses to certify the per-vendor
  claim unless every ``REQUIRED_VENDOR_GROUPS`` stratum is covered; an empty
  required coverage is NO_CLAIM, never PASS.
* C direct save / publication separation: ``save()`` runs the full gate chain
  and refuses to write a board that fails it (failed diagnostic at
  ``<path>.failed.json``, target byte-for-byte untouched); a written board
  carries a receipt and a ``publication`` field defaulting to ``pending``.
* D claim-bound provenance: ``check_claim_bound_provenance`` requires a claim
  whose task/protocol and evidence hashes match; patient-level bootstrap
  requires ``patient_id`` evidence.
* E registry silent-swallow: ``load_registry`` / ``update_status`` /
  ``save_registry`` raise on an invalid registry instead of treating a
  well-formed file as evidence that the checks ran.

The CLI end-to-end block pins RC=0 for the valid submission and RC=1 for every
invalid submission, with the leaderboard byte-for-byte unchanged on rejection.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scoring import (TRAP_RANK_MISSING_STRATUM, TRAP_RANK_NO_CLAIM,
                     TRAP_RANK_PASS, add_submission, assert_trap_separates_in_every_group,
                     check_paired_submission, load, new_leaderboard, save,
                     trap_rank_by_group)
from scoring.leaderboard import TRAP_RANK_FAIL
from scoring.rung_registry import (STATUS_VALUES, load_registry, save_registry,
                                   update_status, validate_registry)
from scoring.task_spec import REQUIRED_VENDOR_GROUPS, TASK_LABEL
from scoring.verify import check_claim_bound_provenance

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "s2_gates"
WS4 = Path(__file__).resolve().parents[2]


def load_fixture(name: str):
    with open(FIXTURES / (name + ".json"), encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# A. task identity
# ---------------------------------------------------------------------------

def test_task_identity_valid_fixture():
    assert check_paired_submission(load_fixture("task_identity_valid")) == []


@pytest.mark.parametrize("name,needle", [
    ("task_identity_missing", "does not declare the WS-4 task"),
    ("task_identity_unrelated_label", "not the WS-4 task"),
    ("task_identity_non_string", "must be a string"),
])
def test_task_identity_invalid_fixtures(name, needle):
    errors = check_paired_submission(load_fixture(name))
    assert any(needle in e for e in errors)


def test_task_identity_refused_at_submission_without_mutating_board():
    board = new_leaderboard()
    before = copy.deepcopy(board)
    with pytest.raises(ValueError, match="not the WS-4 task"):
        add_submission(board, load_fixture("task_identity_unrelated_label"),
                       method="bad")
    assert board == before


# ---------------------------------------------------------------------------
# B. mandatory strata
# ---------------------------------------------------------------------------

def test_strata_valid_covers_all_required_vendors():
    board = load_fixture("strata_valid")
    groups = trap_rank_by_group(board["entries"], by="vendor")
    assert set(groups["groups"]) >= set(REQUIRED_VENDOR_GROUPS)
    assert groups["verdict"] == TRAP_RANK_PASS
    assert_trap_separates_in_every_group(board["entries"], by="vendor")


def test_strata_missing_vendor_is_not_passed_and_not_publishable(tmp_path):
    board = load_fixture("strata_missing_vendor")
    groups = trap_rank_by_group(board["entries"], by="vendor")
    assert groups["verdict"] == TRAP_RANK_MISSING_STRATUM
    assert any("missing required vendor stratum" in v for v in groups["violations"])
    # Publishing gate refuses, and the saved artifact must not claim PASS: a
    # missing stratum is recorded on the board (strata != PASS, publication
    # pending) rather than silently certified or silently refused away.
    with pytest.raises(ValueError, match="missing required vendor stratum"):
        assert_trap_separates_in_every_group(board["entries"], by="vendor")
    p = tmp_path / "board.json"
    save(copy.deepcopy(board), p)
    loaded = load(p)
    assert loaded["receipt"]["gate"]["strata"] == TRAP_RANK_MISSING_STRATUM
    assert loaded["receipt"]["gate"]["strata"] != TRAP_RANK_PASS
    assert loaded["publication"]["status"] == "pending"


def test_strata_empty_coverage_is_no_claim_never_pass():
    board = load_fixture("strata_empty")
    groups = trap_rank_by_group(board["entries"], by="vendor")
    assert groups["verdict"] == TRAP_RANK_NO_CLAIM
    assert groups["verdict"] != TRAP_RANK_PASS


# ---------------------------------------------------------------------------
# C. direct save / publication separation
# ---------------------------------------------------------------------------

def test_direct_save_runs_full_gate_chain_and_attaches_receipt(tmp_path):
    board = load_fixture("direct_save_valid")
    p = tmp_path / "board.json"
    save(board, p)
    loaded = load(p)
    receipt = loaded["receipt"]
    assert receipt["gate"] == {
        "check_submission_result": "ok",
        "task_identity": "ok",
        "trap_rank": TRAP_RANK_PASS,
        "strata": TRAP_RANK_PASS,
    }
    assert receipt["input_sha256"]  # bound to the input board
    assert loaded["publication"]["status"] == "pending"
    assert loaded["publication"]["published_at"] is None
    assert not (p.with_name(p.name + ".failed.json")).exists()


def test_direct_save_refuses_invalid_board_and_keeps_target_bytes(tmp_path):
    """§2-C byte-for-byte guard: a refused save must not touch an existing
    leaderboard file; the failure is recorded beside it, not over it."""
    board = load_fixture("direct_save_valid")
    p = tmp_path / "board.json"
    save(copy.deepcopy(board), p)
    before = p.read_bytes()
    broken = copy.deepcopy(board)
    broken["entries"].append(load_fixture("strata_valid")["entries"][0])  # valid shape
    # make the trap not last in its group: append a real GE submission below GE's trap
    weakest = {"id": "sub-GE-low", "method": "GE-low", "kind": "submission",
               "permanent": False, "trap": False, "placeholder": False,
               "vendor": "GE", "dose": "0.25",
               "metrics": {"psnr_db": 41.0, "ssim": 0.96, "cnr_mean": 14.0,
                           "cho_auc_mean": 1.0, "npwe_mean": 220804.56,
                           "bander_roi": 0.02, "task": TASK_LABEL},
               "submitted_at": "2026-09-15T00:00:00+00:00", "notes": "fixture"}
    broken["entries"].append(weakest)
    with pytest.raises(ValueError, match="board not publishable"):
        save(broken, p)
    assert p.read_bytes() == before, "refused save overwrote the existing board"
    failed = p.with_name(p.name + ".failed.json")
    assert failed.is_file()
    diag = json.loads(failed.read_text(encoding="utf-8"))
    assert diag["saved_path"] == str(p)
    assert diag["input_sha256"]
    assert any("not last" in v for v in diag["gate_violations"])


# ---------------------------------------------------------------------------
# D. claim-bound provenance
# ---------------------------------------------------------------------------

def test_provenance_valid_fixture():
    assert check_claim_bound_provenance(load_fixture("provenance_valid")) == []


@pytest.mark.parametrize("name,needle", [
    ("provenance_hash_mismatch", "does not match the evidence"),
    ("provenance_other_task", "claimed for a different task"),
    ("provenance_patient_bootstrap_no_patient_id", "carries no patient_id"),
])
def test_provenance_invalid_fixtures(name, needle):
    errors = check_claim_bound_provenance(load_fixture(name))
    assert any(needle in e for e in errors)


def test_provenance_patient_bootstrap_with_patient_id_accepted():
    assert check_claim_bound_provenance(
        load_fixture("provenance_patient_bootstrap_with_patient_id")) == []


def test_provenance_hash_mismatch_refused_at_submission():
    board = new_leaderboard()
    before = copy.deepcopy(board)
    with pytest.raises(ValueError, match="claim provenance"):
        add_submission(board, load_fixture("provenance_hash_mismatch"), method="bad")
    assert board == before


# ---------------------------------------------------------------------------
# E. registry silent-swallow
# ---------------------------------------------------------------------------

def test_registry_valid_roundtrip(tmp_path):
    reg = load_fixture("registry_valid")
    assert validate_registry(reg) == []
    assert load_registry(FIXTURES / "registry_valid.json") == reg
    updated = update_status(reg, 2, "blocked", reason="fixture")
    assert updated["rungs"][1]["status"] == "blocked"
    p = tmp_path / "registry.json"
    save_registry(reg, p)
    assert load_registry(p) == reg


@pytest.mark.parametrize("name,needle", [
    ("registry_missing_rung", "missing rung"),
    ("registry_bad_status", "bad status"),
    ("registry_missing_gate", "missing gate"),
])
def test_registry_invalid_fixtures_raise_on_load(tmp_path, name, needle):
    path = FIXTURES / (name + ".json")
    with pytest.raises(ValueError, match=needle):
        load_registry(path)
    with pytest.raises(ValueError, match=needle):
        save_registry(load_fixture(name), tmp_path / "never.json")
    assert not (tmp_path / "never.json").exists()


def test_registry_silent_swallow_is_closed_for_update():
    reg = load_fixture("registry_bad_status")
    with pytest.raises(ValueError, match="invalid rung registry"):
        update_status(reg, 1, "done")


# ---------------------------------------------------------------------------
# CLI end-to-end: valid RC=0, each invalid RC=1, board bytes unchanged
# ---------------------------------------------------------------------------

def _run_cli_submit(result_path, board_path, cwd):
    env = dict(os.environ, PYTHONPATH=str(WS4), PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(
        [sys.executable, "-m", "scoring.cli", "submit", "--result", str(result_path),
         "--method", "fixture", "--out", str(board_path)],
        cwd=cwd, env=env, capture_output=True, text=True)


def test_cli_end_to_end_valid_fixture(tmp_path):
    result_path = tmp_path / "result.json"
    result_path.write_text(json.dumps(load_fixture("provenance_valid")), encoding="utf-8")
    board_path = tmp_path / "board.json"
    result = _run_cli_submit(result_path, board_path, tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    board = json.loads(board_path.read_text(encoding="utf-8"))
    assert any(e["method"] == "fixture" for e in board["entries"])
    assert board["publication"]["status"] == "pending"
    assert board["receipt"]["gate"]["task_identity"] == "ok"


@pytest.mark.parametrize("name", [
    "task_identity_missing",
    "task_identity_unrelated_label",
    "task_identity_non_string",
    "provenance_hash_mismatch",
    "provenance_other_task",
    "provenance_patient_bootstrap_no_patient_id",
])
def test_cli_end_to_end_invalid_fixtures(tmp_path, name):
    """Each invalid fixture must be refused with RC=1 and leave an existing
    leaderboard byte-for-byte unchanged (a rejection is not a write)."""
    board_path = tmp_path / "board.json"
    save(load_fixture("strata_valid"), board_path)
    before = board_path.read_bytes()
    result_path = tmp_path / "result.json"
    result_path.write_text(json.dumps(load_fixture(name)), encoding="utf-8")
    result = _run_cli_submit(result_path, board_path, tmp_path)
    assert result.returncode == 1, (name, result.stdout, result.stderr)
    assert board_path.read_bytes() == before, name


def test_cli_invalid_fixture_on_fresh_board_writes_nothing(tmp_path):
    board_path = tmp_path / "board.json"
    result_path = tmp_path / "result.json"
    result_path.write_text(json.dumps(load_fixture("provenance_hash_mismatch")),
                           encoding="utf-8")
    result = _run_cli_submit(result_path, board_path, tmp_path)
    assert result.returncode == 1
    assert not board_path.exists(), "a refused submission created a leaderboard file"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-v"]))
