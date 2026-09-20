"""Trap-rank gate tests (Rung 5/6: the permanent blur trap must rank last on BandER).

The trap's CNR *outscores* real methods (1.08-2.23x) and CHO-AUC saturates at 1.000
on real anatomy; BandER is what separates it (measured 8.9-19.0x, blur last 4/4 in
every vendor group). This gate refuses a board where the trap is not last -- or
cannot prove it is last -- on the discriminating metric.

Main-baseline API (adapted from the heyang `by=` / `min_separation=` signature):

* :func:`assert_trap_ranks_last(entries, *, min_ratio=None)` -- the publishing
  gate. Raises ValueError on any trap-rank violation; ``min_ratio`` is the
  required **separation ratio** (Rung 5/6 uses 3x), checked separately from
  "ranks last".
* :func:`save` -- runs the full gate chain (§2-C: paired gate, task identity,
  trap-rank, required strata). It refuses to write a board that fails any of
  them and keeps a failed diagnostic record at ``<path>.failed.json``; a board
  that passes is written with a receipt and a ``publication`` field defaulting
  to ``pending``. A NO_CLAIM board (nothing to rank) is writable but makes no
  publishable claim.
* per-group checking (Rung 5/6: never average across groups) is
  :func:`trap_rank_by_group` / :func:`assert_trap_separates_in_every_group`,
  not a `by=` argument on the global gate.
"""
from __future__ import annotations

import json

import pytest

from scoring import (BLUR_ENTRY_ID, TRAP_RANK_FAIL, TRAP_RANK_INDETERMINATE,
                     TRAP_RANK_PASS, assert_trap_ranks_last,
                     assert_trap_separates_in_every_group, blur_entry, load,
                     new_leaderboard, save, sort_entries, trap_rank_by_group,
                     trap_rank_report)


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
    """Seed placeholders (no real groups) have nothing to rank: must pass."""
    assert_trap_ranks_last(new_leaderboard()["entries"])


def test_gate_passes_when_trap_last_with_separation():
    """Blur 0.43 vs vendor 4.0 mirrors the measured AAPM separation (>3x)."""
    board = _trap_bander(new_leaderboard(), 0.43)
    _add_vendor(board, "A", 4.0)
    assert_trap_ranks_last(board["entries"])  # ratio ~9.3x -> pass
    assert trap_rank_report(board["entries"])["min_ratio_observed"] == pytest.approx(4.0 / 0.43)


def test_gate_passes_multiple_clean_vendor_groups():
    board = _trap_bander(new_leaderboard(), 0.43)
    _add_vendor(board, "A", 4.0)
    _add_vendor(board, "B", 6.7)
    assert_trap_ranks_last(board["entries"])


def test_gate_refuses_when_trap_not_last():
    """A vendor below the trap means the blur does not rank last."""
    board = _trap_bander(new_leaderboard(), 0.43)
    _add_vendor(board, "A", 0.20)
    with pytest.raises(ValueError, match="trap is not last"):
        assert_trap_ranks_last(board["entries"])


def test_gate_refuses_below_declared_min_ratio():
    """Ratio 2.3x clears 'trap last' but not the declared >=3x separation
    (Rung 5/6). The rank and the separation ratio are checked separately."""
    board = _trap_bander(new_leaderboard(), 0.43)
    _add_vendor(board, "A", 1.0)
    assert_trap_ranks_last(board["entries"])              # ranks last: passes
    with pytest.raises(ValueError, match="below the required 3x"):
        assert_trap_ranks_last(board["entries"], min_ratio=3.0)


def test_gate_refuses_tighter_custom_min_ratio():
    """A stricter publishing requirement than the 3x default."""
    board = _trap_bander(new_leaderboard(), 0.43)
    _add_vendor(board, "A", 4.0)  # 9.3x passes the 3x default, fails a stricter 10x
    with pytest.raises(ValueError, match="below the required 10x"):
        assert_trap_ranks_last(board["entries"], min_ratio=10.0)
    assert_trap_ranks_last(board["entries"])  # default (no min_ratio) still passes


def test_gate_refuses_when_trap_unmeasured():
    """A board whose trap has lost its discriminating number cannot prove
    trap-last: INDETERMINATE, and the gate refuses it. The seed carries its
    measured numbers now, so the state is reconstructed by stripping the value.

    Note: this must never read as a sound board, or the way to beat the gate is
    to stop measuring the trap.
    """
    board = new_leaderboard()
    blur_entry(board["entries"])["metrics"].pop("bander_roi", None)
    _add_vendor(board, "A", 5.0)
    report = trap_rank_report(board["entries"])
    assert report["verdict"] == TRAP_RANK_INDETERMINATE
    with pytest.raises(ValueError, match="reports no bander_roi"):
        assert_trap_ranks_last(board["entries"])


def test_gate_member_without_metric_is_excluded_not_failed():
    """A member reporting no numeric discriminating value is excluded from the
    comparison rather than failing it: there is nothing to rank it against."""
    board = _trap_bander(new_leaderboard(), 0.43)
    _add_vendor(board, "A", None)
    assert trap_rank_report(board["entries"])["n_compared"] == 0
    assert_trap_ranks_last(board["entries"])                    # no raise
    assert_trap_ranks_last(board["entries"], min_ratio=3.0)     # no ratio -> no fail


def test_gate_names_offending_group():
    """Per-group gate (Rung 5/6): a vendor group whose member scores below its
    own group's trap is refused and the offending group is named."""
    board = new_leaderboard()   # seeds include a GE trap at bander_roi=0.0452
    board["entries"].append({
        "id": "sub-ge", "method": "oversmoother", "trap": False,
        "placeholder": False, "vendor": "GE", "dose": "0.25",
        "metrics": {"psnr_db": 44.0, "ssim": 0.99, "bander_roi": 0.03},
    })
    with pytest.raises(ValueError, match=r"vendor=GE: entry 'sub-ge'"):
        assert_trap_separates_in_every_group(board["entries"], by="vendor")


def test_gate_by_dose_requires_a_trap_in_every_group():
    """Per-dose grouping: a dose group holding real entries but no trap
    measurement is INDETERMINATE, and the gate refuses to certify it."""
    board = _trap_bander(new_leaderboard(), 0.43)
    _add_vendor(board, "A", 5.0, dose="0.5mGy")
    report = trap_rank_by_group(board["entries"], by="dose")
    assert report["verdict"] == TRAP_RANK_INDETERMINATE
    assert report["groups"]["0.5mGy"]["verdict"] == TRAP_RANK_INDETERMINATE
    with pytest.raises(ValueError, match="no trap measured in this group"):
        assert_trap_separates_in_every_group(board["entries"], by="dose")


def test_gate_handles_zero_and_negative_trap_values():
    """Extreme input: a trap at 0 (or below) has no defined separation ratio --
    rank is still checked, and anything at or below the trap still fails."""
    def board_with(trap_value, member_value):
        return [
            {"id": BLUR_ENTRY_ID, "method": "gaussian-blur", "permanent": True,
             "trap": True, "placeholder": False,
             "metrics": {"bander_roi": trap_value}},
            {"id": "m", "method": "m", "trap": False, "placeholder": False,
             "metrics": {"bander_roi": member_value}},
        ]

    report = trap_rank_report(board_with(0.0, 0.5))
    assert report["verdict"] == TRAP_RANK_PASS                 # 0.5 > 0: rank is fine
    assert report["min_ratio_observed"] is None                # ratio undefined
    assert_trap_ranks_last(board_with(0.0, 0.5))

    with pytest.raises(ValueError, match="at or below"):
        assert_trap_ranks_last(board_with(0.0, -0.1))          # <= trap: not last


def test_gate_sorts_board_detectability_descending():
    """The board's ranking leads with the discriminating index, descending; an
    entry without the index sorts below every entry that has it."""
    board = _trap_bander(new_leaderboard(), 0.4315421991344855)
    _add_vendor(board, "A", 4.0)
    _add_vendor(board, "B", 6.7)
    board["entries"].append({
        "id": "no-bander", "method": "m", "trap": False, "placeholder": False,
        "metrics": {"cnr_mean": 99.0, "psnr_db": 99.0},
    })
    ranked = sort_entries(board["entries"])
    ranked_ids = [e["id"] for e in ranked]
    assert ranked_ids.index("sub-B") < ranked_ids.index("sub-A")
    assert ranked_ids.index("sub-A") < ranked_ids.index(BLUR_ENTRY_ID)
    assert ranked_ids.index(BLUR_ENTRY_ID) < ranked_ids.index("no-bander")
    assert ranked_ids[-1] == "seed-ws3-reference"  # placeholders sort at the very bottom


def test_save_persists_clean_vendor_board(tmp_path):
    """§2-C: save() runs the full gate chain, including the required-strata
    check (§2-B). A board covering every REQUIRED_VENDOR_GROUPS stratum with the
    trap last in each group is writable."""
    board = _trap_bander(new_leaderboard(), 0.43)
    # weakest real model in each REQUIRED vendor group (aapm_lidc_cross_vendor_spread)
    for vid, bander in (("GE", 0.4377), ("Philips", 3.1928),
                        ("Siemens", 1.1572), ("Toshiba", 1.1228)):
        _add_vendor(board, vid, bander)
    p = tmp_path / "board.json"
    save(board, p)
    loaded = load(p)
    assert any(e["id"] == BLUR_ENTRY_ID for e in loaded["entries"])
    for vid in ("GE", "Philips", "Siemens", "Toshiba"):
        assert any(e["id"] == f"sub-{vid}" for e in loaded["entries"]), vid
    assert loaded["receipt"]["gate"]["strata"] == TRAP_RANK_PASS
    assert loaded["publication"]["status"] == "pending"


def test_save_refuses_failed_board_and_keeps_diagnostics(tmp_path):
    """§2-C: save() refuses to write a board whose trap is not last, instead of
    recording the FAIL and writing it anyway, and keeps a failed diagnostic
    record at ``<path>.failed.json`` so the failure is evidence rather than a
    silently discarded board."""
    board = _trap_bander(new_leaderboard(), 0.43)
    _add_vendor(board, "A", 0.20)  # below the trap
    p = tmp_path / "board.json"
    with pytest.raises(ValueError, match="board not publishable"):
        save(board, p)
    failed = tmp_path / "board.json.failed.json"
    assert failed.is_file(), "failed diagnostic record was not written"
    diag = json.loads(failed.read_text(encoding="utf-8"))
    assert any("not last" in v for v in diag["gate_violations"])
    assert not p.exists(), "a board that fails the gate was written anyway"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-v"]))
