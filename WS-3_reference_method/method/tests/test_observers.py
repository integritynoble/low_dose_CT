"""Tests for the WS-3 port of the task-based detectability observers.

The observer protocol is ported from WS-1
(``WS-1_dataset/baselines/src/pwm_ldct_baselines/observers.py``) with identical task
parameters; these tests verify the protocol on tiny synthetic slices (structure, not
science) plus the two behavioural invariants that matter for the benchmark:

1. the Gaussian blur trap destroys the inserted lesion -> CNR < Rose criterion (3.0);
2. the blur looks *better* than the unprocessed low-dose input on PSNR yet still
   fails detectability -- the low-dose-ct.md §4 trap (high fidelity, low task AUC).
"""
import numpy as np
import pytest

from pwm_ldct_recon.evaluation import (
    ROSE_CRITERION,
    PAIRED_TASK,
    blur_method,
    evaluate_method,
    evaluate_validation_block,
    recon_fn_from_model,
    validate_paired_report,
)
from pwm_ldct_recon.models import GaussianBlur, blur_recon_fn
from pwm_ldct_recon.observers import (
    TaskSpec,
    evaluate_detectability,
    find_tissue_roi,
    hu_to_norm,
    insert_lesion_into_norm,
    norm_to_hu,
)


def _synthetic_slices(n: int = 6, size: int = 48):
    """Low-dose (noisy tissue) and full-dose (clean tissue) slices in [0, 1]."""
    rng = np.random.default_rng(0)
    base = hu_to_norm(np.full((size, size), 55.0, dtype=np.float32))
    lows, fulls = [], []
    for i in range(n):
        low = np.clip(base + rng.normal(0, 0.03, (size, size)), 0, 1).astype(np.float32)
        full = base.copy()
        lows.append(low)
        fulls.append(full)
    return lows, fulls


def test_find_tissue_roi_inside_image():
    lows, fulls = _synthetic_slices(n=1, size=48)
    y0, x0 = find_tissue_roi(fulls[0], 32)
    assert 0 <= y0 <= 48 - 32
    assert 0 <= x0 <= 48 - 32


def test_insert_lesion_changes_roi_centre():
    img = hu_to_norm(np.full((64, 64), 55.0, dtype=np.float32))
    task = TaskSpec()
    y0, x0 = 16, 16
    cy, cx = y0 + task.roi_size_px // 2, x0 + task.roi_size_px // 2
    mod = insert_lesion_into_norm(img, (cy, cx), task)
    assert np.max(mod) > np.max(img)  # brighter peak at the lesion centre
    # far away from the lesion nothing changes
    assert float(np.max(np.abs(mod[:10, :10] - img[:10, :10]))) < 1e-6


def test_gaussian_blur_trap_fails_rose_criterion():
    """The blur trap: fixed sigma=1.0 / 5x5 destroys detectability (CNR < Rose 3)."""
    lows, fulls = _synthetic_slices(n=4, size=48)
    det = evaluate_detectability(blur_recon_fn(), lows, fulls, n_trials=4)
    assert det["cnr_mean"] < ROSE_CRITERION


def test_blur_trap_high_psnr_low_detectability():
    """The trap's two faces: blur beats identity on PSNR yet stays below Rose on CNR.

    This is exactly the low-dose-ct.md §4 trap: a method that merely smooths looks
    better on fidelity but does not support the detection task.
    """
    lows, fulls = _synthetic_slices(n=4, size=48)
    identity = evaluate_method("identity", lambda x: np.asarray(x, dtype=np.float32),
                               lows, fulls, n_trials=4)
    blur = evaluate_method("blur", blur_recon_fn(), lows, fulls, n_trials=4)
    assert blur["psnr_db"] > identity["psnr_db"]
    assert blur["detectability"]["cnr_mean"] < ROSE_CRITERION


def test_blur_reduces_lesion_peak_contrast():
    """Mechanism: the blur attenuates the inserted lesion's peak contrast."""
    img = hu_to_norm(np.full((64, 64), 55.0, dtype=np.float32))
    task = TaskSpec()
    center = (32, 32)
    low_present = insert_lesion_into_norm(img, center, task)
    bl_out = np.asarray(blur_recon_fn()(low_present), dtype=np.float32)
    center_slice = (slice(center[0] - 2, center[0] + 3),
                    slice(center[1] - 2, center[1] + 3))

    def peak_contrast(x):
        return float(norm_to_hu(x)[center_slice].mean()) - 55.0

    id_peak = peak_contrast(low_present)
    bl_peak = peak_contrast(bl_out)
    assert id_peak > 0 and bl_peak > 0
    assert bl_peak < id_peak  # blur attenuates the signal


def test_blur_method_config_matches_ws1_parameters():
    bm = blur_method()
    assert bm["name"] == "blur"
    assert bm["config"] == {"sigma_px": 1.0, "kernel_size": 5,
                            "module": "pwm_ldct_recon.models.GaussianBlur"}
    m = GaussianBlur()
    assert m.sigma == 1.0
    assert m.kernel.shape[-1] == 5


def test_evaluate_method_pairs_fidelity_and_detectability():
    lows, fulls = _synthetic_slices(n=4, size=48)
    block = evaluate_method("identity", lambda x: np.asarray(x, dtype=np.float32),
                            lows, fulls, n_trials=4, max_slices=3)
    assert block["name"] == "identity"
    assert block["psnr_db"] is not None
    assert block["ssim"] is not None
    det = block["detectability"]
    assert det["task"] == "SKE-Gaussian20HU-s2px"
    assert det["signal"]["sigma_px"] == 2.0
    assert det["signal"]["peak_contrast_hu"] == 20.0
    assert det["observer"]["cnr"]["rose_criterion"] == 3.0
    assert det["observer"]["cho"]["n_channels"] == 4
    assert det["cnr_mean"] is not None and det["cho_auc_mean"] is not None


def test_validate_paired_report_rejects_unpaired_blocks():
    lows, fulls = _synthetic_slices(n=2, size=48)
    ok_block = evaluate_validation_block(
        [], lows, fulls, n_trials=2, max_slices=1,
        uq_spearman=0.5, include_blur=True,
        recon_fn=lambda x: np.asarray(x, dtype=np.float32))
    assert validate_paired_report(ok_block) == []

    broken = {
        "psnr_db": 30.0,
        "detectability": ok_block["paired_methods"]["blur"]["detectability"],
        "paired_methods": {
            "reference": {"psnr_db": 30.0, "ssim": 0.9},  # no detectability
            "blur": {"psnr_db": 33.0, "ssim": 0.95,
                     "detectability": ok_block["paired_methods"]["blur"]["detectability"]},
        },
        "paired_methods_ok": True,
    }
    errs = validate_paired_report(broken)
    assert any("paired_methods.reference" in e for e in errs)
    assert any("paired_methods_ok" in e for e in errs)

    # top-level pair missing detectability -> rejected
    top_broken = {"psnr_db": 30.0,
                  "paired_methods": ok_block["paired_methods"],
                  "paired_methods_ok": True}
    errs2 = validate_paired_report(top_broken)
    assert any("top-level" in e for e in errs2)


def test_recon_fn_from_model_wraps_torch_module():
    model = GaussianBlur()
    fn = recon_fn_from_model(model)
    out = fn(np.full((16, 16), 0.5, dtype=np.float32))
    assert out.shape == (16, 16)
    assert out.dtype == np.float32
    # uniform input unchanged away from the padded border (5x5 kernel)
    assert np.allclose(out[3:-3, 3:-3], 0.5, atol=1e-2)
