"""Rung 2, 3 and 4 gates: each accepts the field's own artifact and refuses a broken one.

The rung-7 audit of 2026-09-05 found these three rungs marked done with no
executable gate. A gate that only ever refuses would pass a rejection-only
suite and fail the project, so every gate here is asserted in both
directions, and the accept case is the real WS-1 artifact, not a fixture.
"""
from __future__ import annotations

import copy

import pytest

from scoring import gates as G

needs_ws1 = pytest.mark.skipif(not G.PAIRING_VALIDATION.exists(),
                               reason="WS-1_dataset/output not present beside WS-4")


# ------------------------------------------------------------- both directions, real artifact

@needs_ws1
@pytest.mark.parametrize("name", sorted(G.PROBES))
def test_each_gate_accepts_its_artifact_and_refuses_its_own_broken_probe(name):
    out = G.exercise(name)
    assert out["accepts"], (name, out["accept_violations"])
    assert out["rejects"], name
    assert out["ok"]


# ------------------------------------------------------------- Rung 2

@needs_ws1
def test_pairing_gate_checks_rows_not_just_the_summary():
    d = copy.deepcopy(G._load(G.PAIRING_VALIDATION))
    d["per_patient"][0]["n_unpaired_fd"] = 3           # summary still says all passed
    v = G.check_pairing_validation(d)
    assert any("n_unpaired_fd" in x for x in v)
    assert any("disagrees" in x for x in v) or v       # a lying summary is itself a violation


def test_pairing_gate_refuses_the_wrong_cohort_size():
    d = {"overall": {"n_passed": 1, "n_failed": 0, "all_passed": True, "min_correlation_target": 0.99},
         "per_patient": [{"patient": "L1", "passed": True, "geometry_correlation": 1.0, "n_unpaired_fd": 0,
                          "n_unpaired_ld": 0, "n_violations": 0, "n_fd": 5, "n_ld": 5, "n_paired": 5}]}
    v = G.check_pairing_validation(d)
    assert any("1 patients validated; the rung claims 10" in x for x in v)


def test_pairing_gate_refuses_a_lowered_target():
    d = {"overall": {"n_passed": 0, "n_failed": 0, "all_passed": True, "min_correlation_target": 0.5},
         "per_patient": []}
    v = G.check_pairing_validation(d)
    assert any("below the registry's 0.99" in x for x in v)


# ------------------------------------------------------------- Rung 3

@needs_ws1
def test_roi_gate_refuses_a_run_on_a_different_task():
    d = copy.deepcopy(G._load(G.R3_ROI_DETECTABILITY))
    d["task"]["noise_roi_hu_band"] = [0.0, 500.0]
    v = G.check_roi_protocol(d)
    assert any("HU band" in x for x in v)


@needs_ws1
def test_roi_gate_refuses_weak_separation_even_when_the_trap_is_last():
    d = copy.deepcopy(G._load(G.R3_ROI_DETECTABILITY))
    weakest = min(d["by_split"][m]["freq_roi"]["roi_band_energy_ratio"]["mean"] for m in d["models"] if m != "blur")
    d["by_split"]["blur"]["freq_roi"]["roi_band_energy_ratio"]["mean"] = weakest / 2.0   # last, but only 2x
    v = G.check_roi_protocol(d)
    assert any("below the 3x" in x for x in v)


@needs_ws1
def test_roi_gate_refuses_a_missing_roi_count():
    d = copy.deepcopy(G._load(G.R3_ROI_DETECTABILITY))
    pid = next(iter(d["per_patient"]))
    d["per_patient"][pid]["models"]["blur"]["freq_roi"]["n_roi"] = 12
    v = G.check_roi_protocol(d)
    assert any("12 ROIs, protocol says 48" in x for x in v)


# ------------------------------------------------------------- Rung 4

@needs_ws1
def test_dose_gate_refuses_a_two_point_curve():
    d = copy.deepcopy(G._load(G.DOSE_DETECTABILITY))
    d["dose_points"] = d["dose_points"][:2]
    v = G.check_dose_curve(d)
    assert any("at least 3" in x for x in v)


@needs_ws1
def test_dose_gate_refuses_a_model_missing_a_dose_point():
    d = copy.deepcopy(G._load(G.DOSE_DETECTABILITY))
    key = d["dose_points"][1]["key"]
    del d["by_model"]["ctformer"]["doses"][key]
    v = G.check_dose_curve(d)
    assert any("ctformer has no measurement" in x for x in v)


@needs_ws1
def test_dose_gate_refuses_a_knee_outside_the_measured_range():
    d = copy.deepcopy(G._load(G.DOSE_DETECTABILITY))
    d["by_model"]["red_cnn"]["knee"]["bander_roi_knee_tau50"] = 0.9
    v = G.check_dose_curve(d)
    assert any("not a dose ratio inside the measured range" in x for x in v)


@needs_ws1
def test_the_registry_numbers_hold_on_the_real_artifacts():
    """The claims the reasons state, read off the files the gates read."""
    p = G._load(G.PAIRING_VALIDATION)
    assert p["overall"]["n_patients"] == 10 and p["overall"]["all_passed"]
    assert all(r["geometry_correlation"] == 1.0 and r["n_violations"] == 0 for r in p["per_patient"])
    r3 = G._load(G.R3_ROI_DETECTABILITY)
    band = {m: r3["by_split"][m]["freq_roi"]["roi_band_energy_ratio"]["mean"] for m in r3["models"]}
    assert min(band, key=band.get) == "blur"
    assert min(v / band["blur"] for m, v in band.items() if m != "blur") >= 3.0
    dose = G._load(G.DOSE_DETECTABILITY)
    assert len(dose["dose_points"]) == 3
    assert dose["by_model"]["blur"]["knee"]["bander_roi_knee_tau50"] is None
