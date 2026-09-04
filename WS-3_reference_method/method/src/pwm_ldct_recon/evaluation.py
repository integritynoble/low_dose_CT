"""Paired fidelity + detectability evaluation for WS-3 (low-dose-ct.md §4 / Rung 1 / Rung 1.3).

The WS-3 reference method (and every comparison baseline) is evaluated on **two
coordinated quantities** that must be published together: a fidelity number (PSNR / SSIM)
and a task detectability number (CNR / CHO-AUC / NPWE via the observers in
:mod:`pwm_ldct_recon.observers`). The low-dose-ct.md §4 core rule is "both numbers or
neither": a result that reports PSNR without detectability (or vice versa) is not
publishable. That rule is enforced here both at evaluation time (the block is built as a
pair) and at the gate (:func:`validate_paired_report`, wired into the RunBundle entrypoint
and the results schema).

This module also owns the **permanent Gaussian blur trap** (Rung 1.3 / §4): the fixed
sigma=1.0 px / 5x5 blur is a standing member of the comparison suite. Reference methods
are allowed to fail; the blur stays. Its numbers are reported in the same paired schema,
so the trap is visible as "PSNR high, CNR < 3" rather than being hidden.

Reproducible configuration. The task/observer parameters are declared once here and
written into every evaluation block (``task`` / ``signal`` / ``observer`` fields), so an
independent verifier can reconstruct the exact detection task from the output alone.
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional, Sequence

import numpy as np
import torch

from .ensemble import EnsembleResult, ensemble_infer
from .metrics import psnr, ssim
from .models import GaussianBlur, UnrolledRecon, blur_recon_fn
from .observers import ReconFn, TaskSpec, evaluate_detectability

# --------------------------------------------------------------------------- #
# Declared, reproducible task + observer configuration (Rung 1.1 / Rung 1.2)
# --------------------------------------------------------------------------- #
# Values mirror WS-1's observer task exactly (WS-1 observers.py), so WS-1 and WS-3
# detectability numbers are measured on the same declared task.
ROSE_CRITERION = 3.0
CHO_N_CHANNELS = 4
NPWE_EYE_FILTER = "rho*exp(-rho/0.2)"

PAIRED_TASK = TaskSpec(
    signal_sigma_px=2.0,
    peak_contrast_hu=20.0,
    roi_size_px=32,
    location_known=True,
    noise_roi_hu_band=(10.0, 120.0),
    n_trials=64,
    label="SKE-Gaussian20HU-s2px",
)


def task_config() -> Dict:
    """Serialisable task specification (written into every evaluation block)."""
    t = PAIRED_TASK
    return {
        "label": t.label,
        "signal": {
            "sigma_px": t.signal_sigma_px,
            "peak_contrast_hu": t.peak_contrast_hu,
            "location_known": t.location_known,
        },
        "observer": {
            "cnr": {"rose_criterion": ROSE_CRITERION},
            "cho": {"channels": "dog", "n_channels": CHO_N_CHANNELS},
            "npwe": {"eye_filter": NPWE_EYE_FILTER},
        },
        "noise_roi_hu_band": list(t.noise_roi_hu_band),
    }


def _detectability_block(det: dict, task: TaskSpec) -> Dict:
    """Wrap an observer batch result + the declared task config into a schema block."""
    block = task_config()
    block.update({
        "task": task.label,          # schema-required task label (both numbers or neither)
        "cnr_mean": det["cnr_mean"],
        "cnr_median": det["cnr_median"],
        "cnr_std": det["cnr_std"],
        "cho_auc_mean": det["cho_auc_mean"],
        "cho_auc_median": det["cho_auc_median"],
        "npwe_mean": det["npwe_mean"],
        "n_slices": det["n_slices"],
        "roi_pos": list(det["roi_pos"]),
        "task_label": det["task_label"],
    })
    return block


# --------------------------------------------------------------------------- #
# Recon callables (one per method under test)
# --------------------------------------------------------------------------- #

def recon_fn_from_ensemble(models: Sequence[UnrolledRecon]) -> ReconFn:
    """WS-3 reference method as a recon callable: low slice -> ensemble-mean slice.

    The unrolled net reconstructs from the *simulated measurement* ``y = R(low)`` (the
    same path used by training and the corpus run; provenance ``simulated`` unless the
    corpus path supplies real projections). The callable interface matches
    :data:`pwm_ldct_recon.observers.ReconFn` so the insertion protocol is shared.
    """
    if not models:
        raise ValueError("empty ensemble")
    physics = models[0].physics

    def fn(low_norm_slice: np.ndarray) -> np.ndarray:
        x = torch.from_numpy(np.asarray(low_norm_slice, dtype=np.float32))[None, None]
        with torch.no_grad():
            y = physics.forward(x)
            res = ensemble_infer(models, y)
        return res.mean.clamp(0, 1)[0, 0].cpu().numpy()

    return fn


def recon_fn_from_model(model: torch.nn.Module) -> ReconFn:
    """Wrap any torch module taking [1,1,H,W] in [0,1] as a numpy recon callable."""
    def fn(low_norm_slice: np.ndarray) -> np.ndarray:
        x = torch.from_numpy(np.asarray(low_norm_slice, dtype=np.float32))[None, None]
        with torch.no_grad():
            out = model(x)
            if isinstance(out, (tuple, list)):
                out = out[0]
            return out.clamp(0, 1)[0, 0].cpu().numpy()

    return fn


def blur_method(sigma: float = 1.0, kernel_size: int = 5) -> Dict:
    """The permanent Gaussian-blur trap as a named method descriptor.

    Returns ``{"name": "blur", "recon_fn": ..., "config": {...}}``. The blur is a
    standing member of the suite (Rung 1.3): it always runs, it is never removed.
    """
    return {
        "name": "blur",
        "recon_fn": blur_recon_fn(sigma=sigma, kernel_size=kernel_size),
        "config": {"sigma_px": sigma, "kernel_size": kernel_size,
                   "module": "pwm_ldct_recon.models.GaussianBlur"},
    }


# --------------------------------------------------------------------------- #
# Paired evaluation
# --------------------------------------------------------------------------- #

def evaluate_method(name: str, recon_fn: ReconFn,
                    low_slices: Sequence[np.ndarray], full_slices: Sequence[np.ndarray],
                    task: Optional[TaskSpec] = None,
                    n_trials: Optional[int] = None,
                    max_slices: Optional[int] = None) -> Dict:
    """Fidelity + detectability for one method, as one paired block (§4).

    Fidelity (PSNR/SSIM) is computed on the method's reconstructions of the low-dose
    slices vs the full-dose references; detectability runs the insertion protocol
    (:func:`pwm_ldct_recon.observers.evaluate_detectability`) on the same slices. The two
    numbers are returned together: a caller that drops one of them breaks the pair.
    """
    if task is None:
        task = PAIRED_TASK
    lows = [np.asarray(s, dtype=np.float32) for s in low_slices]
    fulls = [np.asarray(s, dtype=np.float32) for s in full_slices]
    if max_slices is not None:
        lows, fulls = lows[:max_slices], fulls[:max_slices]

    recon = [np.asarray(recon_fn(s), dtype=np.float32).clip(0, 1) for s in lows]
    # metrics.psnr/ssim expect 4D [B,1,H,W]
    psnr_vals = [psnr(torch.from_numpy(r)[None, None], torch.from_numpy(f)[None, None])
                 for r, f in zip(recon, fulls)]
    ssim_vals = [ssim(torch.from_numpy(r)[None, None], torch.from_numpy(f)[None, None])
                 for r, f in zip(recon, fulls)]
    det = evaluate_detectability(recon_fn, lows, fulls, task=task, n_trials=n_trials)

    return {
        "name": name,
        "psnr_db": float(np.mean(psnr_vals)),
        "ssim": float(np.mean(ssim_vals)),
        "detectability": _detectability_block(det, task),
    }


# --------------------------------------------------------------------------- #
# Validation block + paired gate (both numbers or neither, §4)
# --------------------------------------------------------------------------- #

def validate_paired_report(validation: dict) -> List[str]:
    """Enforce the §4 paired rule on a validation block.

    Returns a list of violations (empty = gate passes). Checks:
      1. The block carries both top-level ``psnr_db`` and ``detectability``.
      2. Every entry in ``paired_methods`` carries both ``psnr_db`` and
         ``detectability`` (or, if a method is explicitly incomplete, it is rejected --
         publishing one without the other is not allowed).
      3. ``paired_methods_ok`` is consistent with the actual pair check.
    """
    errors: List[str] = []
    if not isinstance(validation, dict):
        return ["validation is not an object"]

    top = validation.get("psnr_db") is not None
    top_det = validation.get("detectability") is not None
    if top != top_det:
        errors.append("top-level psnr_db and detectability must be present together "
                      "(both numbers or neither)")

    methods = validation.get("paired_methods")
    if not isinstance(methods, dict) or not methods:
        errors.append("paired_methods must be a non-empty object of per-method blocks")
        return errors
    for name, m in methods.items():
        if not isinstance(m, dict):
            errors.append(f"paired_methods.{name} is not an object")
            continue
        has_f = m.get("psnr_db") is not None
        has_d = m.get("detectability") is not None
        if has_f != has_d:
            errors.append(f"paired_methods.{name}: psnr_db and detectability must be "
                          "present together (both numbers or neither)")
        if not has_d and "ssim" in m and m.get("ssim") is not None:
            errors.append(f"paired_methods.{name}: ssim without detectability is a "
                          "fidelity-only report; not publishable")

    ok = validation.get("paired_methods_ok")
    if not isinstance(ok, bool):
        errors.append("paired_methods_ok must be a boolean")
    elif ok and errors:
        errors.append("paired_methods_ok is true but paired checks failed")
    elif not ok and not errors:
        # A method block can set paired_methods_ok=false deliberately; the gate accepts
        # either an explicit false (block is then not publishable) or a passing pair.
        pass
    return errors


def evaluate_validation_block(models: Sequence[UnrolledRecon],
                              low_slices: Sequence[np.ndarray],
                              full_slices: Sequence[np.ndarray],
                              *,
                              task: Optional[TaskSpec] = None,
                              n_trials: Optional[int] = None,
                              max_slices: Optional[int] = None,
                              uq_spearman: Optional[float] = None,
                              include_blur: bool = True,
                              recon_fn: Optional[ReconFn] = None) -> Dict:
    """Assemble the full validation block: reference + blur, all paired (§4 / Rung 1.3).

    ``low_slices`` / ``full_slices`` are [0,1] slices (the same arrays the fidelity and
    UQ blocks use). Returns the schema-compatible ``validation`` object; its
    ``paired_methods_ok`` reflects the paired gate result.

    ``recon_fn`` may override the reference callable (tests / lightweight callers that
    do not have a trained ensemble); when omitted the reference is built from ``models``.
    """
    if task is None:
        task = PAIRED_TASK
    ref_fn = recon_fn if recon_fn is not None else recon_fn_from_ensemble(models)
    ref = evaluate_method("reference", ref_fn, low_slices, full_slices,
                          task=task, n_trials=n_trials, max_slices=max_slices)

    methods: Dict = {"reference": ref}
    if include_blur:
        bm = blur_method()
        methods["blur"] = evaluate_method(bm["name"], bm["recon_fn"], low_slices,
                                          full_slices, task=task, n_trials=n_trials,
                                          max_slices=max_slices)

    validation: Dict = {
        "psnr_db": ref["psnr_db"],
        "ssim": ref["ssim"],
        "detectability": ref["detectability"],
        "paired_methods": methods,
        "paired_methods_ok": False,  # set below from the real gate
    }
    if uq_spearman is not None:
        validation["uq_spearman"] = float(uq_spearman)

    validation["paired_methods_ok"] = not validate_paired_report(validation)
    return validation
