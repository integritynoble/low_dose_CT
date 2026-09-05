"""The trap-rank gate: the permanent blur trap must rank last on the discriminating index.

Rungs 1, 3, 5 and 6 all rest on the same structural fact: a Gaussian blur that
wins fidelity must lose detectability. Until 2026-09-05 nothing checked it. The
board was ranked by CNR, which Rung 1 records as non-discriminative on real
anatomy and which the trap actually *wins* on the simulated arm, so the trap
could sit at the top of the board with every gate green.

These tests exercise the gate in both directions. A gate that only ever refuses
would pass a rejection-only suite and fail the project, so the healthy board is
asserted to pass as explicitly as the broken one is asserted to fail. The last
test is the non-vacuity guard: it shows the pre-change ranking put the trap
first on the very numbers the new ranking puts it last on.

Numbers are the measured AAPM held-out values from RUNG_REGISTRY.md: Rung 1
(blur ROI BandER 0.247 vs RED-CNN 0.636 / LEARN 0.631 / CTformer 1.040) and
Rung 3 (blur 0.432 vs models 3.854-6.735, with blur taking the highest SSIM).
"""
from __future__ import annotations

import pytest

from scoring import (BLUR_ENTRY_ID, TRAP_RANK_FAIL, TRAP_RANK_INDETERMINATE,
                     TRAP_RANK_PASS, add_submission, assert_trap_ranks_last,
                     check_trap_rank, load, new_leaderboard, save, sort_entries,
                     trap_rank_report)


def entry(entry_id, *, bander_roi=None, cnr=None, ssim=None, psnr=None,
          trap=False, placeholder=False):
    metrics = {}
    if bander_roi is not None:
        metrics["bander_roi"] = bander_roi
    if cnr is not None:
        metrics["cnr_mean"] = cnr
    if ssim is not None:
        metrics["ssim"] = ssim
    if psnr is not None:
        metrics["psnr_db"] = psnr
    return {
        "id": BLUR_ENTRY_ID if trap else entry_id,
        "method": "gaussian-blur" if trap else entry_id,
        "permanent": trap,
        "trap": trap,
        "placeholder": placeholder,
        "metrics": metrics,
    }


def healthy_board():
    """Rung 1's measured board: the trap last on BandER, 2.6-4.2x behind."""
    return [
        entry("trap", bander_roi=0.247, cnr=13.04, ssim=0.929, psnr=39.46, trap=True),
        entry("red_cnn", bander_roi=0.636, cnr=5.19, ssim=0.913, psnr=40.98),
        entry("learn", bander_roi=0.631, cnr=4.80, ssim=0.910, psnr=39.49),
        entry("ctformer", bander_roi=1.040, cnr=2.57, ssim=0.905, psnr=39.60),
    ]


# --------------------------------------------------------------- accepts

def test_healthy_board_passes_and_reports_its_separation():
    report = trap_rank_report(healthy_board())
    assert report["verdict"] == TRAP_RANK_PASS
    assert report["violations"] == []
    assert report["index"] == "bander_roi"
    assert report["trap_value"] == pytest.approx(0.247)
    assert report["n_compared"] == 3
    # 0.631 / 0.247 = 2.55x, the narrowest gap on this board
    assert report["min_ratio_observed"] == pytest.approx(0.631 / 0.247)
    assert_trap_ranks_last(healthy_board())        # must not raise


def test_placeholder_only_board_is_sound_and_says_why():
    """A fresh board carries no real entries; that is not a failure."""
    board = new_leaderboard()
    report = board["trap_rank"]
    assert report["verdict"] == TRAP_RANK_PASS
    assert report["n_compared"] == 0
    assert "nothing to rank" in report["note"]
    assert_trap_ranks_last(board["entries"])       # must not raise


def test_placeholder_entries_never_count_as_comparisons():
    entries = healthy_board()[:1] + [entry("seed", bander_roi=0.001, placeholder=True)]
    report = trap_rank_report(entries)
    assert report["n_compared"] == 0               # the 0.001 seed is not a finding
    assert report["verdict"] == TRAP_RANK_PASS


# --------------------------------------------------------------- refuses

def test_entry_below_the_trap_fails_and_is_named():
    entries = healthy_board() + [entry("oversmoother", bander_roi=0.180, cnr=14.0)]
    report = trap_rank_report(entries)
    assert report["verdict"] == TRAP_RANK_FAIL
    assert len(report["violations"]) == 1
    assert "oversmoother" in report["violations"][0]
    assert "not last" in report["violations"][0]
    with pytest.raises(ValueError, match="trap-rank gate"):
        assert_trap_ranks_last(entries)


def test_tying_the_trap_is_not_separation():
    entries = healthy_board() + [entry("tie", bander_roi=0.247)]
    assert trap_rank_report(entries)["verdict"] == TRAP_RANK_FAIL


def test_a_trap_without_the_index_is_indeterminate_not_pass():
    """The evasion route: drop the trap's number and nothing can be compared.

    This must not read as a sound board, or the way to beat the gate is to stop
    measuring the trap.
    """
    entries = [entry("trap", cnr=13.04, ssim=0.929, trap=True),
               entry("red_cnn", bander_roi=0.636, cnr=5.19)]
    report = trap_rank_report(entries)
    assert report["verdict"] == TRAP_RANK_INDETERMINATE
    assert report["verdict"] != TRAP_RANK_PASS
    assert "reports no bander_roi" in report["violations"][0]
    with pytest.raises(ValueError, match="trap-rank gate"):
        assert_trap_ranks_last(entries)


def test_missing_trap_fails_the_rank_gate_too():
    entries = [e for e in healthy_board() if not e["trap"]]
    report = trap_rank_report(entries)
    assert report["verdict"] == TRAP_RANK_FAIL
    assert "missing" in report["violations"][0]


def test_min_ratio_is_separate_from_rank():
    """Rung 5/6 wants 3x separation; rank alone is a weaker claim than that."""
    entries = [entry("trap", bander_roi=0.30, trap=True), entry("m", bander_roi=0.60)]
    assert trap_rank_report(entries)["verdict"] == TRAP_RANK_PASS        # ranks last
    tight = trap_rank_report(entries, min_ratio=3.0)
    assert tight["verdict"] == TRAP_RANK_FAIL                            # but only 2x
    assert "2x" in tight["violations"][0] or "2.0" in tight["violations"][0]
    assert check_trap_rank(entries) == []
    assert check_trap_rank(entries, min_ratio=3.0) != []


# --------------------------------------------------------------- the board carries its verdict

def test_the_board_records_the_verdict_on_submission_rather_than_hiding_it():
    """A board that fails is written down failing; it is not discarded.

    The failure is evidence about the index or about the submission. Refusing to
    record it would let the leaderboard suppress a finding about itself.
    """
    board = new_leaderboard()          # the seed trap carries its measured numbers
    board["entries"].append(entry("real_model", bander_roi=3.854, cnr=5.19))
    result = {"validation": {"paired_methods": {"oversmoother": {
        "psnr_db": 41.6, "ssim": 0.965,
        "detectability": {"bander_roi": 0.10, "cnr_mean": 14.0,
                          "task": "SKE-Gaussian20HU-s2px"}}}}}
    # the paired gate admits it: it reports fidelity and the discriminating index
    created = add_submission(board, result, method="OverSmoother")
    assert len(created) == 1
    # ...and the board now carries a FAIL naming it, without raising
    assert board["trap_rank"]["verdict"] == TRAP_RANK_FAIL
    assert any("oversmoother" in v.lower() for v in board["trap_rank"]["violations"])


def test_an_unmeasured_trap_makes_a_real_board_indeterminate():
    """A board whose trap has lost its discriminating number cannot be checked.

    This was the state of every board before 2026-09-05, when the seed trap
    carried synthetic placeholders and no BandER: real submissions could
    accumulate beside a trap nobody had measured. The seed is measured now, so
    the case is reconstructed by stripping the value rather than by relying on
    the seed being unmeasured.
    """
    board = new_leaderboard()
    for e in board["entries"]:
        if e["id"] == BLUR_ENTRY_ID:
            e["metrics"].pop("bander_roi")
    board["entries"].append(entry("real_model", bander_roi=3.854, cnr=5.19))
    report = trap_rank_report(board["entries"])
    assert report["verdict"] == TRAP_RANK_INDETERMINATE
    assert "Refresh the trap" in report["violations"][0]


def test_the_seeded_board_is_now_checkable_out_of_the_box():
    """The refresh, from the gate's point of view: same board, real verdict."""
    board = new_leaderboard()
    board["entries"].append(entry("real_model", bander_roi=3.854, cnr=5.19))
    report = trap_rank_report(board["entries"], min_ratio=3.0)
    assert report["verdict"] == TRAP_RANK_PASS
    assert report["min_ratio_observed"] > 8.0


def test_saved_board_carries_a_fresh_verdict(tmp_path):
    board = new_leaderboard()
    board.pop("trap_rank")
    path = tmp_path / "board.json"
    save(board, path)
    assert load(path)["trap_rank"]["verdict"] == TRAP_RANK_PASS


# --------------------------------------------------------------- non-vacuity guard

def test_the_old_cnr_led_ranking_put_the_trap_first_on_these_numbers():
    """Proves the ranking fix is not vacuous.

    The pre-2026-09-05 key was (cnr, cho_auc, psnr) descending. On the measured
    Rung 1 board that ordering placed the blur trap at the top, because its CNR
    of 13.04 beats every learned baseline. The current key leads with BandER and
    places the same trap last.
    """
    entries = healthy_board()

    def old_key(e):
        m = e["metrics"]
        return (m.get("cnr_mean", float("-inf")),
                m.get("cho_auc_mean", float("-inf")),
                m.get("psnr_db", float("-inf")))

    old_ranked = sorted(entries, key=old_key, reverse=True)
    assert old_ranked[0]["id"] == BLUR_ENTRY_ID          # the cheat ranked first

    new_ranked = sort_entries(entries)
    assert new_ranked[-1]["id"] == BLUR_ENTRY_ID         # and now ranks last
    assert [e["id"] for e in new_ranked[:3]] == ["ctformer", "red_cnn", "learn"]


def test_an_entry_without_the_index_sorts_below_every_entry_that_has_it():
    entries = healthy_board() + [entry("no_bander", cnr=99.0, psnr=99.0)]
    assert sort_entries(entries)[-1]["id"] == "no_bander"
