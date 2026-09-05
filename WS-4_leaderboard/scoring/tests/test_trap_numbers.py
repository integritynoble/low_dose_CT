"""The permanent trap's numbers must stay tied to the run they came from.

``seed_blur_entry`` carries literals so the scoring package stays importable
without WS-1 present. Literals drift. These tests re-read the source file named
in ``TRAP_SOURCE``, verify its hash, and fail if any metric has moved, so a
re-run of WS-1 cannot silently change what the board treats as its trap. They
skip when WS-1 is not checked out beside WS-4.

The second test is the one that matters scientifically: with the measured
numbers, the trap must win fidelity and lose detectability. If that ever stops
being true, the trap has stopped being a trap and the board's whole Rung 1
claim needs revisiting.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scoring import TASK_SPEC, new_leaderboard, trap_rank_report
from scoring.leaderboard import TRAP_SOURCE, seed_blur_entry

REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE = REPO_ROOT / TRAP_SOURCE["file"]

#: metric on the entry -> path into the source document
FIELD_PATHS = {
    "psnr_db": ("fidelity", "psnr"),
    "ssim": ("fidelity", "ssim"),
    "cnr_mean": ("detectability", "cnr_mean"),
    "cho_auc_mean": ("detectability", "cho_auc_mean"),
    "npwe_mean": ("detectability", "npwe_mean"),
    "bander_roi": ("freq_roi", "roi_band_energy_ratio"),
    "bander_full": ("freq_roi", "band_energy_ratio_full"),
    "roi_tm_auc": ("freq_roi", "roi_tm_auc"),
}

needs_ws1 = pytest.mark.skipif(not SOURCE.exists(),
                               reason="WS-1_dataset/output not present beside WS-4")


@needs_ws1
def test_trap_metrics_still_match_their_source_run():
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == TRAP_SOURCE["sha256"], (
        "the source run has changed on disk; re-read it and refresh the trap "
        "deliberately rather than updating this hash")
    doc = json.loads(raw)
    assert doc["schema"] == TRAP_SOURCE["schema"]
    assert doc["updated_at"] == TRAP_SOURCE["generated_at"]
    assert doc["split_assignment"]["test"] == TRAP_SOURCE["patients"]
    assert doc["task"]["task"] == TASK_SPEC["label"]        # same task, or not comparable
    assert doc["task"]["noise_roi_hu_band"] == TASK_SPEC["noise_roi_hu_band"]

    blur = doc["by_split"]["blur"]
    metrics = seed_blur_entry()["metrics"]
    for field, (section, name) in FIELD_PATHS.items():
        assert metrics[field] == blur[section][name]["mean"], field
    assert blur["freq_roi"]["n_roi"]["mean"] == 48.0


@needs_ws1
def test_the_trap_wins_fidelity_and_loses_detectability_on_this_run():
    """The structural claim Rungs 1, 3, 5 and 6 rest on, checked against the data."""
    doc = json.loads(SOURCE.read_bytes())
    by = doc["by_split"]
    models = doc["models"]
    assert set(models) == {"red_cnn", "ctformer", "learn", "blur"}

    def best(section, name):
        return max(models, key=lambda m: by[m][section][name]["mean"])

    # highest on all three of the indices a reader reaches for first
    assert best("fidelity", "ssim") == "blur"
    assert best("fidelity", "psnr") == "blur"
    assert best("detectability", "cnr_mean") == "blur"

    # and last on the discriminating one, by the margin Rung 5/6 requires
    band = {m: by[m]["freq_roi"]["roi_band_energy_ratio"]["mean"] for m in models}
    assert min(band, key=band.get) == "blur"
    ratios = [v / band["blur"] for m, v in band.items() if m != "blur"]
    assert min(ratios) >= 3.0, "trap separation fell below the Rung 5/6 3x criterion"
    assert min(ratios) == pytest.approx(8.93, abs=0.05)


def test_refreshed_board_is_checkable_where_the_placeholder_board_was_not():
    """The reason the refresh was needed, as a test.

    A real submission beside a placeholder trap read INDETERMINATE: no
    ``bander_roi`` on the trap, nothing to rank against. With the measured
    numbers the same board resolves, and passes the 3x separation criterion.
    """
    board = new_leaderboard()
    board["entries"].append({
        "id": "real_model", "method": "red_cnn", "trap": False, "placeholder": False,
        "vendor": "Siemens", "dose": "0.25",  # a submission does carry its context
        "metrics": {"psnr_db": 39.9, "ssim": 0.92, "bander_roi": 3.876178},
    })
    report = trap_rank_report(board["entries"], min_ratio=3.0)
    assert report["verdict"] == "PASS"
    assert report["trap_value"] == pytest.approx(0.4315421991344855)
    assert report["min_ratio_observed"] == pytest.approx(8.98, abs=0.05)


def test_the_trap_is_no_longer_marked_placeholder_and_carries_its_provenance():
    entry = seed_blur_entry()
    assert entry["placeholder"] is False
    assert entry["source"]["file"] == TRAP_SOURCE["file"]
    assert entry["source"]["sha256"] == TRAP_SOURCE["sha256"]
    # Context lives in `source`, not in vendor/dose: those are compute_spread's
    # grouping keys and the trap is the control for a group, not a member of it.
    assert entry["vendor"] is None and entry["dose"] is None
    assert "Siemens" not in json.dumps(entry["metrics"])
    assert "AAPM" in entry["source"]["corpus"]


# ------------------------------------------------- per-vendor traps

from scoring.leaderboard import (VENDOR_TRAP_MEASUREMENTS, VENDOR_TRAP_SOURCE,  # noqa: E402
                                 seed_vendor_trap_entries, trap_rank_by_group)

VENDOR_SOURCE = REPO_ROOT / VENDOR_TRAP_SOURCE["file"]
VENDOR_FIELDS = {"psnr_db": "psnr", "ssim": "ssim", "cnr_mean": "cnr_mean",
                 "cho_auc_mean": "cho_auc_mean", "bander_roi": "roi_band_energy_ratio",
                 "bander_full": "band_energy_ratio_full", "roi_tm_auc": "roi_tm_auc"}
needs_vendor_file = pytest.mark.skipif(not VENDOR_SOURCE.exists(),
                                       reason="WS-1_dataset/output not present beside WS-4")


@needs_vendor_file
def test_vendor_trap_metrics_still_match_their_source_run():
    raw = VENDOR_SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == VENDOR_TRAP_SOURCE["sha256"], (
        "the cross-vendor run has changed on disk; re-read it and refresh the "
        "per-vendor traps deliberately rather than updating this hash")
    doc = json.loads(raw)
    assert doc["schema"] == VENDOR_TRAP_SOURCE["schema"]
    assert doc["updated_at"] == VENDOR_TRAP_SOURCE["generated_at"]
    assert doc["task"]["task"] == TASK_SPEC["label"]
    assert set(doc["agg_by_vendor"]) == set(VENDOR_TRAP_MEASUREMENTS)
    for vendor, block in VENDOR_TRAP_MEASUREMENTS.items():
        blur = doc["agg_by_vendor"][vendor]["blur"]
        for field, name in VENDOR_FIELDS.items():
            assert block["metrics"][field] == blur[name]["mean"], (vendor, field)
        assert block["n_patients"] == blur["n_patients"]
        assert block["separation_ratio"] == doc["separation"][vendor]["ratio_min_model_over_blur"]


@needs_vendor_file
def test_the_board_recomputes_the_separation_the_source_reports():
    """The gate must not trust the file's own ratio; it recomputes and must agree."""
    doc = json.loads(VENDOR_SOURCE.read_bytes())
    entries = seed_vendor_trap_entries()
    for vendor in VENDOR_TRAP_MEASUREMENTS:
        agg = doc["agg_by_vendor"][vendor]
        for model in doc["models"]:
            if model == "blur":
                continue
            entries.append({"id": "%s-%s" % (vendor, model), "method": model, "trap": False,
                            "placeholder": False, "vendor": vendor,
                            "metrics": {"bander_roi": agg[model]["roi_band_energy_ratio"]["mean"]}})
    report = trap_rank_by_group(entries, by="vendor", min_ratio=3.0)
    assert report["verdict"] == "PASS"
    assert doc["gate"]["verdict"] == "PASS"
    for vendor in VENDOR_TRAP_MEASUREMENTS:
        block = report["groups"][vendor]
        assert block["n_compared"] == 3
        assert block["min_ratio_observed"] == pytest.approx(
            doc["separation"][vendor]["ratio_min_model_over_blur"], rel=1e-9), vendor
    assert min(b["min_ratio_observed"] for b in report["groups"].values()) == pytest.approx(8.93, abs=0.01)
    assert max(b["min_ratio_observed"] for b in report["groups"].values()) == pytest.approx(18.96, abs=0.01)


def test_the_aapm_vendor_trap_is_the_same_measurement_as_the_canonical_trap():
    """Two files, one run: the AAPM-real group must agree with seed_blur_entry exactly."""
    canonical = seed_blur_entry()["metrics"]
    aapm = VENDOR_TRAP_MEASUREMENTS["AAPM-Siemens-real"]["metrics"]
    for field in ("psnr_db", "ssim", "cnr_mean", "cho_auc_mean", "bander_roi", "bander_full", "roi_tm_auc"):
        assert aapm[field] == canonical[field], field
