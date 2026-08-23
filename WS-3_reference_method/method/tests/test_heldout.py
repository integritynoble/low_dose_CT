"""Tests for the held-out split isolation gate (low-dose-ct.md §6 / §7.2, P1-4).

The gate must reject any eval entrypoint that imports the training data path, and --
in emit mode -- any validation block that does not declare held-out-split provenance.
"""

from __future__ import annotations

import pytest

from pwm_ldct_recon.heldout import (
    HELDOUT_PROVENANCE,
    HeldOutSet,
    assert_no_write_path,
    check_eval_train_imports,
    check_heldout_isolation,
    heldout_isolation_gate,
    make_heldout_set,
)


# ---------------------------------------------------------------------------
# HeldOutSet: read-only by construction
# ---------------------------------------------------------------------------

def test_heldout_set_has_no_write_methods():
    ds = make_heldout_set(records=[{"slice": 0}, {"slice": 1}])
    assert isinstance(ds, HeldOutSet)
    assert assert_no_write_path(ds) == []
    assert ds.provenance == HELDOUT_PROVENANCE
    assert ds.authorized_by == "OWN"


def test_heldout_set_reproducible_and_readonly():
    a = make_heldout_set(records=[1, 2, 3])
    b = make_heldout_set(records=[1, 2, 3])
    assert len(a) == len(b) == 3
    assert tuple(a) == tuple(b)
    assert not hasattr(a, "write")
    assert not hasattr(a, "append")


def test_assert_no_write_path_detects_write_surface():
    class Mutable:
        def save(self):  # noqa: D401
            return None

    found = assert_no_write_path(Mutable())
    assert "save" in found


# ---------------------------------------------------------------------------
# Static import scan: eval entrypoints must not import training data
# ---------------------------------------------------------------------------

def test_check_eval_train_imports_ok():
    # The real evaluation.py / runbundle/run.py must not import the training path.
    problems = check_eval_train_imports()
    assert problems == [], problems


# ---------------------------------------------------------------------------
# Provenance gate: emit mode requires held-out-split provenance
# ---------------------------------------------------------------------------

def test_check_heldout_isolation_accepts_heldout_provenance():
    validation = {
        "data_provenance": HELDOUT_PROVENANCE,
        "psnr_db": 30.0,
        "detectability": {"cnr_mean": 4.0, "cho_auc_mean": 0.9},
    }
    assert check_heldout_isolation(validation) == []


def test_check_heldout_isolation_rejects_train_provenance():
    validation = {"data_provenance": "training-split", "psnr_db": 30.0}
    problems = check_heldout_isolation(validation)
    assert any("training-split" in p for p in problems)


def test_check_heldout_isolation_rejects_missing_provenance():
    validation = {"psnr_db": 30.0}
    problems = check_heldout_isolation(validation)
    assert any("data provenance" in p for p in problems)


def test_heldout_isolation_gate_self_test_mode():
    validation = {"psnr_db": 30.0, "detectability": {"cnr_mean": 4.0}}
    problems = heldout_isolation_gate(validation, mode="self-test")
    assert problems == []


def test_heldout_isolation_gate_emit_mode_missing_provenance():
    validation = {"psnr_db": 30.0, "detectability": {"cnr_mean": 4.0}}
    problems = heldout_isolation_gate(validation, mode="emit")
    assert any("data provenance" in p for p in problems)


def test_heldout_isolation_gate_emit_mode_ok():
    validation = {
        "data_provenance": HELDOUT_PROVENANCE,
        "psnr_db": 30.0,
        "detectability": {"cnr_mean": 4.0},
    }
    problems = heldout_isolation_gate(validation, mode="emit")
    assert problems == []
