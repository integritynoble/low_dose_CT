"""Trap-rank gate tests (Rung 5/6: the permanent blur trap must rank last on BandER).

The trap's CNR *outscores* real methods (1.08-2.23x) and CHO-AUC saturates at 1.000
on real anatomy; BandER is what separates it (measured 8.9-19.0x, blur last 4/4 in
every vendor group). This gate refuses a board where the trap is not last -- or
cannot prove it is last -- on the discriminating metric within every vendor/dose
group.
"""
from __future__ import annotations

import pytest

from scoring import (BLUR_ENTRY_ID, assert_trap_ranks_last, blur_entry,
                     load, new_leaderboard, save)


def _trap_bander(board, value):
    """Give the seed blur a measured ROI BandER so it can be ranked against."""
    blur_entry(board["entries"])["metrics"]["bander_roi"] = value
    return board


def _add_vendor(board, vid, bander, dose="1.0mGy"):
    """Append a measured vendor submission carrying the discriminating index."""
    board["entries"].append({
        "id": f"sub-{vid}",
        "method": f"vendor-{vid}",
        "kind": "submission",
        "permanent": False,
        "trap": False,
        "placeholder": False,
        "vendor": vid,
        "dose": dose,
        "metrics": {"psnr_db": 39.0, "ssim": 0.93, "bander_roi": bander,
                    "cnr_mean": 5.0, "cho_auc_mean": 0.99, "npwe_mean": 1.0,
                    "task": "SKE-Gaussian20HU-s2px"},
        "submitted_at": "2026-09-06T00:00:00+00:00",
        "notes": "synthetic test submission",
    })
    return board


def test_gate_passes_seed_board_without_groups():
    """Seed placeholders (no vendor groups) have nothing to rank: must pass."""
    assert_trap_ranks_last(new_leaderboard()["entries"])


def test_gate_passes_when_trap_last_with_separation():
    """Blur 0.43 vs vendor 4.0 mirrors the measured AAPM separation (>3x)."""
    board = _trap_bander(new_leaderboard(), 0.43)
    _add_vendor(board, "A", 4.0)
    assert_trap_ranks_last(board["entries"])  # ratio ~9.3x -> pass


def test_gate_passes_multiple_clean_vendor_groups():
    board = _trap_bander(new_leaderboard(), 0.43)
    _add_vendor(board, "A", 4.0)
    _add_vendor(board, "B", 6.7)
    assert_trap_ranks_last(board["entries"])


def test_gate_refuses_when_trap_not_last():
    """A vendor below the trap means the blur does not rank last."""
    board = _trap_bander(new_leaderboard(), 0.43)
    _add_vendor(board, "A", 0.20)
    with pytest.raises(ValueError, match="does not rank last"):
        assert_trap_ranks_last(board["entries"])


def test_gate_refuses_below_declared_minimum_separation():
    """Ratio 2.3x clears 'trap last' but not the declared >=3x separation."""
    board = _trap_bander(new_leaderboard(), 0.43)
    _add_vendor(board, "A", 1.0)
    with pytest.raises(ValueError, match="below the declared >= 3x separation"):
        assert_trap_ranks_last(board["entries"])


def test_gate_refuses_group_present_but_trap_unmeasured():
    """A vendor group with an unrefreshed trap cannot prove trap-last: refused."""
    board = new_leaderboard()  # seed blur has no bander_roi yet
    _add_vendor(board, "A", 5.0)
    with pytest.raises(ValueError, match="trap has no numeric bander_roi"):
        assert_trap_ranks_last(board["entries"])


def test_gate_refuses_member_without_metric():
    board = _trap_bander(new_leaderboard(), 0.43)
    _add_vendor(board, "A", None)
    with pytest.raises(ValueError, match="no numeric bander_roi"):
        assert_trap_ranks_last(board["entries"])


def test_gate_names_offending_group():
    board = _trap_bander(new_leaderboard(), 0.43)
    _add_vendor(board, "A", 5.0)      # clean
    _add_vendor(board, "B", 0.10)     # trap wins on BandER here
    with pytest.raises(ValueError, match="sub-B.*group 'B'"):
        assert_trap_ranks_last(board["entries"])


def test_gate_can_group_by_dose():
    board = _trap_bander(new_leaderboard(), 0.43)
    _add_vendor(board, "A", 5.0, dose="0.5mGy")
    _add_vendor(board, "B", 0.20, dose="0.25mGy")  # fine per-vendor, bad per-dose
    with pytest.raises(ValueError, match="group '0.25mGy'"):
        assert_trap_ranks_last(board["entries"], by="dose")


def test_gate_honours_custom_min_separation():
    board = _trap_bander(new_leaderboard(), 0.43)
    _add_vendor(board, "A", 4.0)  # 9.3x passes the 3x default, fails a stricter 10x
    with pytest.raises(ValueError, match="below the declared >= 10x separation"):
        assert_trap_ranks_last(board["entries"], min_separation=10.0)
    assert_trap_ranks_last(board["entries"])  # default 3x still passes


def test_save_refuses_board_without_trap_last(tmp_path):
    board = _trap_bander(new_leaderboard(), 0.43)
    _add_vendor(board, "A", 0.20)  # below the trap
    with pytest.raises(ValueError, match="does not rank last"):
        save(board, tmp_path / "board.json")


def test_save_persists_clean_vendor_board(tmp_path):
    board = _trap_bander(new_leaderboard(), 0.43)
    _add_vendor(board, "A", 4.0)
    p = tmp_path / "board.json"
    save(board, p)
    loaded = load(p)
    assert any(e["id"] == BLUR_ENTRY_ID for e in loaded["entries"])
    assert any(e["id"] == "sub-A" for e in loaded["entries"])
