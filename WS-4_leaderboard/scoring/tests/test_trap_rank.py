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
                     TRAP_RANK_NO_CLAIM, TRAP_RANK_PASS, add_submission,
                     assert_trap_ranks_last, check_trap_rank, load,
                     new_leaderboard, save, sort_entries, trap_rank_report)
from scoring.task_spec import TASK_LABEL
from scoring.verify import provenance_sha256


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
    """A fresh board carries no real entries; that is not a failure, but it is
    also not a PASS -- an empty coverage must never read as a certified board
    (§2-B: zero comparisons are a no-claim, not a pass)."""
    board = new_leaderboard()
    report = board["trap_rank"]
    assert report["verdict"] == TRAP_RANK_NO_CLAIM
    assert report["n_compared"] == 0
    assert "nothing to rank" in report["note"]
    assert_trap_ranks_last(board["entries"])       # must not raise


def test_placeholder_entries_never_count_as_comparisons():
    entries = healthy_board()[:1] + [entry("seed", bander_roi=0.001, placeholder=True)]
    report = trap_rank_report(entries)
    assert report["n_compared"] == 0               # the 0.001 seed is not a finding
    assert report["verdict"] == TRAP_RANK_NO_CLAIM


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
    manifest = {"corpus": "LIDC lowdose_sim", "r": 0.25, "seed": 42, "n_patients": 2}
    weights = {"arch": "conv", "params": 1000}
    result = {"validation": {"paired_methods": {"oversmoother": {
        "psnr_db": 41.6, "ssim": 0.965,
        "detectability": {"bander_roi": 0.10, "cnr_mean": 14.0,
                          "task": "SKE-Gaussian20HU-s2px"}}}},
        "claim": {"task_id": TASK_LABEL,
                  "protocol_id": "detectability-freq-v1",
                  "data_manifest_sha256": provenance_sha256(manifest),
                  "model_sha256": provenance_sha256(weights),
                  "evaluator_version": "pwm_ldct_recon-2026-09-14"},
        "evidence": {"data_manifest": manifest, "model_weights": weights}}
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
    # no real entries yet: the fresh verdict is a no-claim, never a PASS
    assert load(path)["trap_rank"]["verdict"] == TRAP_RANK_NO_CLAIM


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


# ------------------------------------------------- per-group (Rung 5/6)

from scoring import (assert_trap_separates_in_every_group,  # noqa: E402
                     trap_rank_by_group)
from scoring.leaderboard import VENDOR_TRAP_MEASUREMENTS  # noqa: E402
from scoring.leaderboard import TRAP_RANK_MISSING_STRATUM  # noqa: E402

#: the weakest real model in each vendor group, from
#: aapm_lidc_cross_vendor_spread.json's `separation.min_model_roi_ber`
MIN_MODEL = {"GE": 0.4377207350211846, "Philips": 3.192782063728278,
             "Siemens": 1.157229319065808, "Toshiba": 1.1227839915166196,
             "AAPM-Siemens-real": 3.853913}


def multi_vendor_board():
    """A seeded board plus the weakest real model in each vendor group."""
    board = new_leaderboard()
    for vendor, value in MIN_MODEL.items():
        board["entries"].append({
            "id": "sub-%s" % vendor, "method": "weakest-model", "trap": False,
            "placeholder": False, "vendor": vendor, "dose": "0.25",
            "metrics": {"psnr_db": 40.0, "ssim": 0.95, "bander_roi": value},
        })
    return board


def test_every_vendor_group_carries_its_own_trap():
    groups = trap_rank_by_group(new_leaderboard()["entries"], by="vendor")
    assert set(groups["groups"]) == set(VENDOR_TRAP_MEASUREMENTS)
    assert groups["n_groups"] == 5
    # seeded groups with no real members are a no-claim, not a PASS (§2-B)
    assert groups["verdict"] == TRAP_RANK_NO_CLAIM


def test_multi_vendor_board_separates_in_all_five_groups():
    board = multi_vendor_board()
    report = trap_rank_by_group(board["entries"], by="vendor", min_ratio=3.0)
    assert report["verdict"] == TRAP_RANK_PASS
    assert report["violations"] == []
    for vendor in VENDOR_TRAP_MEASUREMENTS:
        block = report["groups"][vendor]
        assert block["n_compared"] == 1
        assert block["min_ratio_observed"] >= 3.0, vendor
    assert_trap_separates_in_every_group(board["entries"], min_ratio=3.0)


def test_the_global_check_would_wrongly_fail_a_low_band_energy_vendor():
    """Why the per-group check is not merely a stronger global check.

    The trap's own band energy spans an order of magnitude between vendors,
    0.0452 on GE to 0.4315 on AAPM. Judging a GE submission against the AAPM
    trap is the cross-group comparison Rung 6 forbids, and it gives the wrong
    answer: a GE entry at 0.40 sits 8.8x above the GE trap, a clean separation,
    while falling below the global trap and reading FAIL.
    """
    board = new_leaderboard()
    board["entries"].append({
        "id": "sub-ge", "method": "a-real-ge-model", "trap": False, "placeholder": False,
        "vendor": "GE", "dose": "0.25",
        "metrics": {"psnr_db": 40.0, "ssim": 0.95, "bander_roi": 0.40},
    })
    assert trap_rank_report(board["entries"])["verdict"] == TRAP_RANK_FAIL   # spurious
    per_group = trap_rank_by_group(board["entries"], by="vendor", min_ratio=3.0)
    # §2-B: a single covered vendor cannot certify the per-vendor claim (the
    # other REQUIRED_VENDOR_GROUPS strata are missing), so the overall verdict
    # is MISSING_STRATUM -- but the GE group itself separates cleanly, which is
    # exactly the point this test exists to pin.
    assert per_group["verdict"] == TRAP_RANK_MISSING_STRATUM
    assert per_group["groups"]["GE"]["verdict"] == TRAP_RANK_PASS
    assert per_group["groups"]["GE"]["min_ratio_observed"] > 8.0


def test_an_entry_below_its_own_group_trap_fails_and_names_the_group():
    board = new_leaderboard()
    board["entries"].append({
        "id": "sub-ge-oversmooth", "method": "oversmoother", "trap": False,
        "placeholder": False, "vendor": "GE", "dose": "0.25",
        "metrics": {"psnr_db": 44.0, "ssim": 0.99, "bander_roi": 0.03},
    })
    report = trap_rank_by_group(board["entries"], by="vendor")
    assert report["verdict"] == TRAP_RANK_FAIL
    assert report["groups"]["GE"]["verdict"] == TRAP_RANK_FAIL
    assert any("vendor=GE" in v and "sub-ge-oversmooth" in v for v in report["violations"])
    with pytest.raises(ValueError, match="trap-rank gate \\(vendor\\)"):
        assert_trap_separates_in_every_group(board["entries"])


def test_a_group_with_no_trap_is_indeterminate_not_pass():
    """A vendor nobody has measured the trap on cannot be certified."""
    board = new_leaderboard()
    board["entries"].append({
        "id": "sub-canon", "method": "m", "trap": False, "placeholder": False,
        "vendor": "Canon", "dose": "0.25",
        "metrics": {"psnr_db": 40.0, "ssim": 0.95, "bander_roi": 2.0},
    })
    report = trap_rank_by_group(board["entries"], by="vendor")
    assert report["verdict"] == TRAP_RANK_INDETERMINATE
    assert report["groups"]["Canon"]["verdict"] == TRAP_RANK_INDETERMINATE
    assert "no trap measured in this group" in report["violations"][0]


def test_a_failing_group_outranks_an_indeterminate_one():
    board = new_leaderboard()
    board["entries"] += [
        {"id": "sub-canon", "method": "m", "trap": False, "placeholder": False,
         "vendor": "Canon", "metrics": {"bander_roi": 2.0}},
        {"id": "sub-ge-bad", "method": "m", "trap": False, "placeholder": False,
         "vendor": "GE", "metrics": {"bander_roi": 0.01}},
    ]
    assert trap_rank_by_group(board["entries"], by="vendor")["verdict"] == TRAP_RANK_FAIL


def test_traps_are_kept_out_of_the_spread_they_would_otherwise_set():
    """Vendored traps carry a grouping key; the span must still be the submissions'."""
    from scoring import compute_spread
    board = multi_vendor_board()
    spread = compute_spread(board["entries"], by="vendor")
    for vendor in MIN_MODEL:
        assert spread[vendor]["n_entries"] == 1          # the submission, not the trap
        assert spread[vendor]["bander_roi_span"] == 0.0  # one value, no span
