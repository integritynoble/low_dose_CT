"""Tests for the P1/P2 additions:

- P1-5 DICOM geometry pairing (Rung 2): pure geometry functions, no pydicom needed.
- P1-3 dose-detectability curve + knee naming (Rung 4).
- P1-4 TaskSpec serialization / published task spec consistency.
"""
import json
import os

import numpy as np
import pytest

from pwm_ldct_baselines.dicom_pairing import (
    along_axis_positions, pair_by_geometry, validate,
)
from pwm_ldct_baselines.dose_curve import (
    build_stats, max_gain_interval, rose_crossing_ratio,
)
from pwm_ldct_baselines.eval import FIXED_SEED_SET, evaluate_seed_set
from pwm_ldct_baselines.observers import TaskSpec
from pwm_ldct_baselines.vendor_loocv import (
    compute_spread, spread_report, vendor_loocv_folds,
)


# ---------------------------------------------------------------------------
# P1-5 DICOM geometry pairing
# ---------------------------------------------------------------------------

def _axial_meta(z_mm, uid):
    """A single axial slice at along-axis position z_mm."""
    return {"sop_uid": uid, "instance_number": int(z_mm * 1000),
            "position_xyz": [0.0, 0.0, float(z_mm)],
            "orientation_xyz": [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]}


def test_along_axis_positions_axial():
    metas = [_axial_meta(10.0, "fd-001"), _axial_meta(20.5, "fd-002")]
    out = along_axis_positions(metas)
    assert out[0][1] == 10.0
    assert out[1][1] == 20.5
    # sop uid preserved
    assert out[0][0] == "fd-001"


def test_pairing_ignores_file_name_order():
    # fd series ordered [z=3, z=1, z=2], ld series ordered [z=2, z=3, z=1]
    # pairing must be by geometry, so each position lands on its own match.
    fd = [_axial_meta(1.0, "fd-a"), _axial_meta(2.0, "fd-b"), _axial_meta(3.0, "fd-c")]
    ld = [_axial_meta(2.0, "ld-b"), _axial_meta(3.0, "ld-c"), _axial_meta(1.0, "ld-a")]
    res = pair_by_geometry(fd, ld, tol_mm=0.1)
    assert res["n_paired"] == 3
    for pair in res["pairs"]:
        # each pair must join the *same* position (geometry match, not order)
        assert float(pair["abs_delta_mm"]) < 1e-9
    # correlation must be 1.0 for exact geometry match
    assert res["geometry_correlation"] == pytest.approx(1.0)


def test_pairing_correlation_and_validate():
    base = np.linspace(0.0, 99.0, 50)
    fd = [_axial_meta(float(z), f"fd-{i:03d}") for i, z in enumerate(base)]
    ld = [_axial_meta(float(z) + 0.1, f"ld-{i:03d}") for i, z in enumerate(base)]
    res = pair_by_geometry(fd, ld, tol_mm=0.5)
    assert res["n_paired"] == 50
    # slight systematic offset keeps correlation ~1 but deltas within tol
    assert res["geometry_correlation"] > 0.99
    assert validate(res)["passed"] is True


def test_pairing_rejects_beyond_tolerance():
    fd = [_axial_meta(1.0, "fd-a"), _axial_meta(2.0, "fd-b")]
    ld = [_axial_meta(5.0, "ld-x"), _axial_meta(20.0, "ld-y")]  # far apart
    res = pair_by_geometry(fd, ld, tol_mm=1.0)
    assert res["n_paired"] == 0
    assert validate(res)["passed"] is False
    assert res["n_unpaired_fd"] == 2


def test_pairing_detects_misregistration_as_low_correlation():
    # same set but one series reordered by a permutation that breaks geometry:
    # simulate a real misregistration by shifting every other slice far apart
    base = np.arange(0, 40, 2.0)
    fd = [_axial_meta(float(z), f"fd-{i:03d}") for i, z in enumerate(base)]
    ld = [_axial_meta(float(z) + (8.0 if i % 2 else 0.0), f"ld-{i:03d}")
          for i, z in enumerate(base)]
    res = pair_by_geometry(fd, ld, tol_mm=0.5)
    # alternating 8mm offsets push half the slices out of tolerance -> not all paired
    assert res["n_paired"] < len(fd)


# ---------------------------------------------------------------------------
# P1-3 dose-detectability knee
# ---------------------------------------------------------------------------

def _det_json(tmp_path, name, cnrs, psnrs):
    p = tmp_path / f"{name}_results_det.json"
    data = {"model": name, "task": "SKE-Gaussian20HU-s2px", "per_dose": {}}
    for key, c, ps in zip(("sim_r010", "sim_r025", "sim_r050"), cnrs, psnrs):
        data["per_dose"][key] = {"psnr": ps,
                                 "detectability": {"cnr_mean": c, "cnr_median": c,
                                                   "cnr_std": 0.1, "cho_auc_mean": 1.0}}
    p.write_text(json.dumps(data))
    return p


def test_rose_crossing_ratio_interpolation():
    # CNR 1.5 -> 4.5 across [0.10, 0.50]: crosses 3.0 exactly at midpoint (0.30)
    r = rose_crossing_ratio([0.10, 0.25, 0.50], [1.5, 3.0, 4.5])
    assert r == pytest.approx(0.25)  # crossing exactly at the r025 point
    r2 = rose_crossing_ratio([0.10, 0.25, 0.50], [1.0, 2.0, 5.0])
    # interpolate between (0.25, 2.0) and (0.50, 5.0): (3-2)/(5-2)=1/3 -> 0.25+0.25/3
    assert r2 == pytest.approx(0.25 + 0.25 / 3.0)


def test_knee_not_reached():
    r = rose_crossing_ratio([0.10, 0.25, 0.50], [0.2, 0.2, 0.2])
    assert r is None


def test_max_gain_interval():
    mg = max_gain_interval([0.10, 0.25, 0.50], [1.0, 2.0, 5.0])
    assert mg is not None
    assert mg[2] == (0.25, 0.50)  # largest gain on the second interval


def test_build_stats_and_knee_label(tmp_path):
    _det_json(tmp_path, "red_cnn", [1.56, 2.68, 3.69], [47.66, 50.64, 52.27])
    _det_json(tmp_path, "ctformer", [0.21, 0.22, 0.22], [42.28, 43.06, 43.34])
    stats = build_stats(str(tmp_path))
    assert stats["rose_criterion"] == 3.0
    assert stats["n_models"] == 2
    assert stats["per_model"]["red_cnn"]["knee"]["label"].startswith("rose-crossing@")
    assert stats["per_model"]["ctformer"]["knee"]["label"] == "not_reached"
    # knee of red_cnn lies between r025 and r050
    knee = stats["per_model"]["red_cnn"]["knee"]["rose_crossing_ratio"]
    assert 0.25 < knee < 0.50


# ---------------------------------------------------------------------------
# P1-4 TaskSpec serialization / published spec consistency
# ---------------------------------------------------------------------------

def test_taskspec_roundtrip():
    t = TaskSpec()
    d = t.to_dict()
    assert d["signal_sigma_px"] == 2.0
    assert d["peak_contrast_hu"] == 20.0
    assert d["location_known"] is True
    assert d["noise_roi_hu_band"] == [10.0, 120.0]
    t2 = TaskSpec.from_dict(d)
    assert t2 == t


def test_published_task_spec_matches_observers():
    here = os.path.dirname(__file__)
    spec_path = os.path.join(here, "..", "task_spec.json")
    if not os.path.exists(spec_path):  # repo may not be checked out in tests
        pytest.skip("baselines/task_spec.json not present")
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)
    t = TaskSpec()
    assert spec["signal"]["sigma_px"] == t.signal_sigma_px
    assert spec["signal"]["peak_contrast_hu"] == t.peak_contrast_hu
    assert spec["location"]["known"] == t.location_known
    assert spec["background"]["noise_roi_hu_band"] == list(t.noise_roi_hu_band)
    assert spec["observer"]["cnr"]["rose_criterion"] == 3.0
    assert spec["signal"]["sigma_mm"] == pytest.approx(t.signal_sigma_px * 0.7)


# ---------------------------------------------------------------------------
# P2-6 leave-one-vendor-out spread
# ---------------------------------------------------------------------------

def test_loocv_fold_plan():
    folds = vendor_loocv_folds(("GE", "Siemens", "Philips", "Toshiba"))
    assert len(folds) == 4
    assert {f["held_out_vendor"] for f in folds} == {"GE", "Siemens", "Philips", "Toshiba"}
    for f in folds:
        assert f["held_out_vendor"] not in f["train_vendors"]
        assert len(f["train_vendors"]) == 3


def test_compute_spread():
    s = compute_spread([1.0, 2.0, 3.0])
    assert s["mean"] == pytest.approx(2.0)
    assert s["min"] == pytest.approx(1.0)
    assert s["max"] == pytest.approx(3.0)
    assert s["n"] == 3
    s1 = compute_spread([4.0])
    assert s1["std"] == 0.0
    s0 = compute_spread([None, None])
    assert s0["n"] == 0


def test_spread_report_keeps_fold_spread():
    folds = {
        "GE_fold": {"vendor": "GE",
                    "per_dose": {"sim_r010": {"psnr": 50.0, "cnr": 2.0},
                                 "sim_r025": {"psnr": 51.0, "cnr": 3.0},
                                 "sim_r050": {"psnr": 52.0, "cnr": 4.0}}},
        "Siemens_fold": {"vendor": "Siemens",
                         "per_dose": {"sim_r010": {"psnr": 46.0, "cnr": 1.0},
                                      "sim_r025": {"psnr": 47.0, "cnr": 2.0},
                                      "sim_r050": {"psnr": 48.0, "cnr": 3.0}}},
    }
    rep = spread_report(folds)
    # r010 PSNR spread across folds: [50, 46] -> mean 48, min 46, max 50
    r010 = rep["per_dose"]["sim_r010"]
    assert r010["psnr_spread"]["mean"] == pytest.approx(48.0)
    assert r010["psnr_spread"]["min"] == pytest.approx(46.0)
    assert r010["psnr_spread"]["max"] == pytest.approx(50.0)
    assert r010["cnr_spread"]["mean"] == pytest.approx(1.5)
    # report carries both indices per dose (never vendor-averaged away)
    assert set(rep["per_dose"]["sim_r050"].keys()) == {"psnr_spread", "cnr_spread"}


# ---------------------------------------------------------------------------
# P2-7 fixed seed set (§7.3)
# ---------------------------------------------------------------------------

def _fake_eval(root, ckpt, seed=None, **kw):
    """Deterministic per-seed fake: PSNR = 40 + seed/1000, CNR = 2.0 + seed/10000."""
    return {
        "model": "red_cnn",
        "split": "test",
        "per_dose": {
            "sim_r010": {"psnr": 40.0 + seed / 1000.0,
                         "detectability": {"cnr_mean": 2.0 + seed / 10000.0}},
            "sim_r025": {"psnr": 45.0 + seed / 1000.0,
                         "detectability": {"cnr_mean": 3.0 + seed / 10000.0}},
        },
    }


def test_evaluate_seed_set_aggregates_mean_and_interval(tmp_path, monkeypatch):
    monkeypatch.setattr("pwm_ldct_baselines.eval.evaluate", _fake_eval)
    out = tmp_path / "agg.json"
    report = evaluate_seed_set("root", "ckpt", str(out), seeds=(42, 58))
    assert report["fixed_seed_set"] == [42, 58]
    assert set(report["per_seed"].keys()) == {"42", "58"}
    r010 = report["aggregate"]["sim_r010"]
    assert r010["psnr"]["mean"] == pytest.approx(40.05)
    assert r010["psnr"]["min"] == pytest.approx(40.042)
    assert r010["psnr"]["max"] == pytest.approx(40.058)
    assert r010["cnr_mean"]["interval"] == pytest.approx([2.0042, 2.0058])
    assert os.path.exists(out)


def test_fixed_seed_set_has_multiple_seeds():
    assert len(FIXED_SEED_SET) >= 4
    assert 42 in FIXED_SEED_SET
