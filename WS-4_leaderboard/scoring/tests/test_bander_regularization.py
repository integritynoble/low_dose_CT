"""Regression tests for BandER robust regularisation (2026-08-22) plus
R4/R5/R6 key-function edge cases.

Background (see WS-4 RUNG_REGISTRY / scoring README caveats):
  ROI BandER = num / max(denom, eps), where denom is the FD high-frequency
  energy inside a tissue ROI. GE/Toshiba simulated-dose ROIs can be nearly
  flat in the FD band (denom down to 0), so the old fixed floor
  ``max(denom, 1e-9)`` inflated values by 5-13 orders of magnitude. The
  regularised path replaces the fixed floor with a band-energy-proportional
  floor ``eps_floor = 1e-4 * denom_full`` (denom_full = full-image FD energy),
  pulling near-zero denominators back to a finite, physically meaningful
  scale while leaving normal ROIs untouched and preserving rank statistics.

This module covers:
  - adaptive-epsilon floor behaviour: finite output, no magnitude blow-up
    (returns to ~1e-1..1e1), zero perturbation on normal inputs;
  - rank preservation: a strictly-lowest blur slice group keeps rank 4/4
    under per-slice ordering and slice-level bootstrap;
  - source-contract check: the four temp run scripts still carry the
    regularised floor (skipped when the scripts are absent);
  - R4 dose-curve knee extraction (linear_cross) edge cases: single dose
    point (k=1), threshold never reached, None filtering;
  - R5/R6 spread (compute_spread) edge cases: single vendor, single dose,
    k=1 groups (no std key), empty groups;
  - observer bootstrap rank edge case: k=1 (single slice) with blur strictly
    lowest stays rank 4/4 across draws.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

from scoring import compute_spread, new_leaderboard

# --------------------------------------------------------------------------- #
# BandER regularised ROI helper (mirrors temp/run_lidc_r6.py,
# run_aapm_r3.py, run_aapm_r4.py, run_observer_real.py)
# --------------------------------------------------------------------------- #

_EPS_SCALE = 1e-4


def _bander_roi(o_hf_patch, hf_fd_patch, denom_full, eps_scale=_EPS_SCALE):
    """ROI BandER with the band-energy-proportional floor introduced 2026-08-22.

    Formula (identical in all four temp run scripts):
        eps_floor = eps_scale * denom_full          # denom_full = (hf_fd**2).sum()
        denom     = (hf_fd_patch**2).sum()
        ber       = (o_hf_patch**2).sum() / max(denom, eps_floor)
    """
    eps_floor = eps_scale * denom_full
    denom = float((hf_fd_patch ** 2).sum())
    return float((o_hf_patch ** 2).sum()) / max(denom, eps_floor)


def _old_fixed_floor(o_hf_patch, hf_fd_patch):
    """Pre-regularisation path: fixed floor max(denom, 1e-9)."""
    denom = float((hf_fd_patch ** 2).sum())
    return float((o_hf_patch ** 2).sum()) / max(denom, 1e-9)


def _patches(num, denom, patch=32):
    """Build o_hf_patch / hf_fd_patch with exact squared-energy num / denom.

    Deterministic construction so tests do not depend on random draw scale.
    """
    o = np.full((patch, patch), np.sqrt(max(num, 0.0) / (patch * patch)))
    h = np.full((patch, patch), np.sqrt(max(denom, 0.0) / (patch * patch)))
    return o, h


# --------------------------------------------------------------------------- #
# 1. Adaptive-epsilon floor: near-zero denominators (GE/Toshiba scenario)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("denom_patch", [0.0, 1e-13, 1e-11, 1e-9])
@pytest.mark.parametrize("num", [1e-4, 1e-3])
def test_near_zero_denominator_finite_and_bounded(num, denom_patch):
    """Flat FD ROI (denom ~ 0) must yield finite, bounded ROI BandER."""
    o_hf_patch, hf_fd_patch = _patches(num, denom_patch)
    denom_full = 1.0  # full-image FD energy, normalised scale

    ber = _bander_roi(o_hf_patch, hf_fd_patch, denom_full)

    assert math.isfinite(ber)
    # regularisation must pull values back to the ~1e-1..1e1 band of other
    # vendors, not to 1e5..1e13
    assert 1e-1 <= ber <= 1e2


def test_regularisation_removes_orders_of_magnitude_inflation():
    """New floor must shrink the old fixed-floor blow-up by >=5 orders."""
    num, denom_patch, denom_full = 1e-4, 0.0, 10.0
    o_hf_patch, hf_fd_patch = _patches(num, denom_patch)

    ber_old = _old_fixed_floor(o_hf_patch, hf_fd_patch)      # num / 1e-9 = 1e5
    ber_new = _bander_roi(o_hf_patch, hf_fd_patch, denom_full)

    assert math.isfinite(ber_old) and math.isfinite(ber_new)
    # old path inflated to ~1e5; new path must be at least 5 orders smaller
    assert ber_new < ber_old * 1e-5
    assert 1e-1 <= ber_new <= 1e2


def test_normal_input_identical_to_old_path_zero_perturbation():
    """When denom >> eps_floor the regularised value equals num/denom exactly."""
    o_hf_patch, hf_fd_patch = _patches(num=0.5, denom=10.0)
    denom_full = 1000.0                                # eps_floor = 0.1 << denom
    denom = float((hf_fd_patch ** 2).sum())
    assert denom > 10 * (1e-4 * denom_full)            # sanity: not clamped

    ber_new = _bander_roi(o_hf_patch, hf_fd_patch, denom_full)
    ber_old = _old_fixed_floor(o_hf_patch, hf_fd_patch)

    assert ber_new == pytest.approx(ber_old, rel=1e-12)
    assert ber_new == pytest.approx(float((o_hf_patch ** 2).sum()) / denom, rel=1e-12)


def test_near_zero_vendor_comparable_to_normal_vendor():
    """Near-zero-denominator vendor must be within ~1e2 of a normal vendor,
    not 5-13 orders above it."""
    num = 1e-3
    # normal vendor: ROI keeps FD energy comparable to output energy
    normal_ber = _bander_roi(*_patches(num, denom=1e-3), denom_full=1.0)
    # GE/Toshiba-style: flat ROI, denom == 0 -> eps_floor = 1e-4 kicks in
    flat_ber = _bander_roi(*_patches(num, denom=0.0), denom_full=1.0)

    assert 1e-1 <= normal_ber <= 1e2
    assert 1e-1 <= flat_ber <= 1e2
    assert flat_ber / normal_ber < 1e2


# --------------------------------------------------------------------------- #
# 2. Rank preservation (blur strictly lowest -> rank 4/4)
# --------------------------------------------------------------------------- #

def _bootstrap_blur_rank(per_slice, n_draws=200, seed=42):
    """Simplified observer bootstrap (mirrors run_observer_real.py main()):
    each draw resamples per-slice ROI BandER with replacement, ranks models
    by mean, returns the rank assigned to the blur method (1 = best)."""
    rng = np.random.default_rng(seed)
    models = list(per_slice)
    ranks = []
    for _ in range(n_draws):
        means = {}
        for m in models:
            x = np.asarray(per_slice[m], dtype=float)
            idx = rng.integers(0, len(x), size=len(x))
            means[m] = x[idx].mean()
        order = sorted(means, key=means.get, reverse=True)
        ranks.append(order.index("blur") + 1)
    return ranks


def test_regularisation_preserves_rank_4_of_4():
    """A strictly-lowest blur slice group keeps rank 4/4 per slice and under
    slice-level bootstrap. All models share the same per-slice ROI FD energy
    (same input volume); only the output energy (num) differs."""
    rng = np.random.default_rng(5)
    models = ["red_cnn", "ctformer", "learn", "blur"]
    num_scale = {"red_cnn": 1e-2, "ctformer": 1e-2, "learn": 1e-2,
                 "blur": 1e-4}                          # blur strictly lowest
    n_slices = 48
    # per-slice ROI denominators shared by all models; mix of near-zero
    # (GE/Toshiba style) and normal values
    denoms = rng.choice([0.0, 1e-13, 1e-3, 1e-1], size=n_slices)

    per_slice = {}
    for m in models:
        ber = []
        for d in denoms:
            o_patch, hf_patch = _patches(num_scale[m], d)
            ber.append(_bander_roi(o_patch, hf_patch, 1.0))
        per_slice[m] = np.asarray(ber)

    # per-slice ordering: blur strictly lowest on every slice
    for i in range(n_slices):
        vals = {m: per_slice[m][i] for m in models}
        assert vals["blur"] < min(v for mm, v in vals.items() if mm != "blur")

    # bootstrap ranking: blur last (rank 4/4) in every draw
    ranks = _bootstrap_blur_rank(per_slice, n_draws=200)
    assert all(r == 4 for r in ranks)


def test_bootstrap_k1_single_slice_blur_last():
    """k=1 (single slice per model): no resampling variance; blur must rank
    4/4 in every draw."""
    per_slice = {
        "red_cnn": np.asarray([2.0]),
        "ctformer": np.asarray([1.5]),
        "learn": np.asarray([1.2]),
        "blur": np.asarray([0.1]),
    }
    ranks = _bootstrap_blur_rank(per_slice, n_draws=50)
    assert all(r == 4 for r in ranks)


def test_bootstrap_detects_rank_break_when_blur_not_lowest():
    """Negative control: if blur is not strictly lowest, the bootstrap helper
    must be able to detect it (guard against a vacuous rank test)."""
    per_slice = {
        "red_cnn": np.asarray([2.0]),
        "ctformer": np.asarray([1.5]),
        "learn": np.asarray([0.1]),
        "blur": np.asarray([1.2]),      # not lowest
    }
    ranks = _bootstrap_blur_rank(per_slice, n_draws=50)
    assert any(r < 4 for r in ranks)


# --------------------------------------------------------------------------- #
# 3. Source contract: temp run scripts still carry the regularised floor
# --------------------------------------------------------------------------- #

_TEMP_DIR = Path.home() / (
    "AppData/Roaming/Tencent/Marvis/User/"
    "oAN1i2UYfvOcqvWo-7R7BX4MGNvY/workspace/"
    "conv_1a0188c6c5a_fce73b28b42c/temp"
)
_RUN_SCRIPTS = ["run_lidc_r6.py", "run_aapm_r3.py", "run_aapm_r4.py",
                "run_observer_real.py"]
_FLOOR_FRAGMENTS = ["eps_floor = 1e-4 * denom_full",
                    "max(denom, eps_floor)"]


@pytest.mark.skipif(not _TEMP_DIR.exists(),
                    reason="session temp run scripts not present")
@pytest.mark.parametrize("script", _RUN_SCRIPTS)
def test_run_script_keeps_regularised_floor(script):
    """Guard against drift: every BandER producer must still use the adaptive
    floor, not the old fixed 1e-9."""
    src = (_TEMP_DIR / script).read_text(encoding="utf-8")
    for frag in _FLOOR_FRAGMENTS:
        assert frag in src, f"{script} missing regularised floor fragment {frag!r}"


# --------------------------------------------------------------------------- #
# 4. R4 dose-curve knee extraction (linear_cross) edge cases
# --------------------------------------------------------------------------- #

sys.path.insert(0, str(_TEMP_DIR))
try:
    from run_aapm_r4 import linear_cross  # noqa: E402
    _HAS_LINEAR_CROSS = True
except Exception:  # pragma: no cover - import failure path
    linear_cross = None
    _HAS_LINEAR_CROSS = False

_NEEDS_R4 = pytest.mark.skipif(not _HAS_LINEAR_CROSS,
                               reason="run_aapm_r4 (temp) not importable")


@_NEEDS_R4
def test_knee_linear_interpolation():
    assert linear_cross([0.10, 0.25, 0.50], [0.20, 0.60, 0.90], 0.50) == \
        pytest.approx(0.2125, rel=1e-9)


@_NEEDS_R4
def test_knee_single_point_reached():
    """k=1: a single dose point already at/above threshold -> that ratio."""
    assert linear_cross([0.25], [0.70], 0.50) == pytest.approx(0.25)


@_NEEDS_R4
def test_knee_single_point_not_reached():
    """k=1: a single dose point below threshold -> None (knee not reached)."""
    assert linear_cross([0.10], [0.30], 0.50) is None


@_NEEDS_R4
def test_knee_never_reached():
    assert linear_cross([0.10, 0.25, 0.50], [0.20, 0.30, 0.45], 0.50) is None


@_NEEDS_R4
def test_knee_skips_none_values():
    vals = [None, 0.30, 0.60]
    # crossing between r=0.25 (v=0.30) and r=0.50 (v=0.60):
    # 0.25 + (0.5-0.3)/(0.6-0.3) * (0.50-0.25) = 0.4167
    assert linear_cross([0.10, 0.25, 0.50], vals, 0.50) == pytest.approx(0.4167, rel=1e-3)


@_NEEDS_R4
def test_knee_flat_plateau_no_division_by_zero():
    """Equal consecutive values crossing the threshold must not divide by 0."""
    assert linear_cross([0.10, 0.25], [0.50, 0.50], 0.50) == pytest.approx(0.10)


# --------------------------------------------------------------------------- #
# 5. R5/R6 spread (compute_spread) edge cases
# --------------------------------------------------------------------------- #

def _entry(method, vendor, dose, bander, cnr=5.0):
    """Minimal on-board entry carrying frequency-domain detectability
    (same shape run_r5_spread.py builds from WS-1 JSONs)."""
    return {
        "id": f"sub-{method}",
        "method": method,
        "kind": "submission",
        "permanent": False,
        "trap": False,
        "placeholder": False,
        "vendor": vendor,
        "dose": dose,
        "metrics": {"psnr_db": 16.0, "ssim": 0.8, "cnr_mean": cnr,
                    "bander_roi": bander,
                    "task": "SKE-Gaussian20HU-s2px"},
        "submitted_at": "t",
        "notes": "",
    }


def test_spread_single_vendor_k1_no_std():
    """Single vendor, single entry (k=1): span present (=0), no std key."""
    entries = [_entry("M1", "GE", "0.25", 1.2)]
    spread = compute_spread(entries, by="vendor")
    assert set(spread) == {"GE"}
    assert spread["GE"]["n_entries"] == 1
    assert spread["GE"]["bander_roi_span"] == 0.0
    assert "bander_roi_std" not in spread["GE"]
    assert "psnr_db_std" not in spread["GE"]


def test_spread_single_dose_group():
    """Single dose group: compute_spread by=dose works and keeps the group."""
    entries = [_entry("M1", "Siemens", "0.25", 0.8)]
    spread = compute_spread(entries, by="dose")
    assert set(spread) == {"0.25"}
    assert spread["0.25"]["n_entries"] == 1
    assert spread["0.25"]["bander_roi_span"] == 0.0


def test_spread_empty_board_returns_empty():
    """No vendor/dose-tagged entries -> no groups (seed entries are context-free)."""
    spread = compute_spread(new_leaderboard()["entries"], by="vendor")
    assert spread == {}
