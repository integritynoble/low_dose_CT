"""Task-based detectability observers (low-dose-ct.md Rung 1 / Rung 1.2 / §4 / §5).

This module is a **port** of the WS-1 implementation
``WS-1_dataset/baselines/src/pwm_ldct_baselines/observers.py`` (implemented against
PWM-LDCT v0.5 for the Rung-1 baseline harness). Task parameters, channel sets and
noise-ROI protocol are kept **identical** so the two repos measure the same task and
produce cross-reproducible detectability numbers (a WS-3 result can be compared against
the WS-1 baseline numbers on the same task specification).

The only deliberate interface change: instead of a ``torch.nn.Module`` taking a normalised
tensor, the per-slice reconstruction is expressed as a **recon callable**
``recon_fn(low_norm_slice) -> recon_norm_slice`` (numpy ``[H, W]`` in [0, 1] both ways).
WS-3's reference method is an unrolled iterative net that reconstructs from a *sinogram*
(``y = R(low)``), and its comparison baselines (FBP, Gaussian blur) are numpy/torch
callables of different signatures; the callable abstraction lets all of them share one
insertion protocol.

Task specification (declared, per Rung 1.1):
  - SKE/BKS: signal-known-exactly, background-known-statistically
  - signal: 2D Gaussian, sigma_signal = 2.0 px (~1.4 mm at 0.7 mm/px)
  - peak contrast: 20 HU (subtle lesion)
  - location: known (centred in the extracted patch)
  - background: homogeneous soft-tissue ROI, no anatomy

Protocol (insertion study): a synthetic Gaussian lesion is inserted into the low-dose
INPUT slice (the lesion is part of the anatomy, so it is present in both the low-dose
acquisition and the full-dose reference). The method reconstructs both the lesion-present
and lesion-absent inputs; detectability is measured on the method OUTPUTS. A method that
merely smooths (e.g. Gaussian blur) destroys the inserted signal, so its CNR falls below
the Rose criterion (3.0) even when PSNR rises -- the blur trap (Rung 1.3 / §4).

The noise ROI is selected to be a tissue-only patch (HU band + low gradient), never placed
over anatomy (Rung 3). Observer parameters are stated and fixed (Rung 1.2).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Optional, Sequence, Tuple

import numpy as np
from scipy import linalg, ndimage, signal

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
HU_MIN = -1024.0
HU_MAX = 3072.0
HU_RANGE = HU_MAX - HU_MIN  # 4096

# A per-slice reconstruction callable: low-dose slice in [0, 1] -> recon slice in [0, 1].
ReconFn = Callable[[np.ndarray], np.ndarray]


def hu_to_norm(hu: np.ndarray) -> np.ndarray:
    """Normalise HU to [0, 1] (matching pwm_ldct_recon.data.normalize)."""
    return np.clip((hu - HU_MIN) / HU_RANGE, 0.0, 1.0).astype(np.float32)


def norm_to_hu(x: np.ndarray) -> np.ndarray:
    """De-normalise [0,1] back to HU."""
    return x * HU_RANGE + HU_MIN


# ---------------------------------------------------------------------------
# Task specification
# ---------------------------------------------------------------------------

@dataclass
class TaskSpec:
    """Declared task for detectability assessment (Rung 1.1).

    All fields are fixed and published with the benchmark. Defaults mirror the WS-1
    observer task exactly (see WS-1 observers.py) so cross-repo numbers are comparable.
    """
    signal_sigma_px: float = 2.0          # Gaussian sigma in pixels
    peak_contrast_hu: float = 20.0        # peak contrast above background
    roi_size_px: int = 32                 # square patch size for observer
    location_known: bool = True           # SKE (signal-known-exactly)
    noise_roi_hu_band: Tuple[float, float] = (10.0, 120.0)  # soft-tissue HU band
    n_trials: int = 64                    # signal-present / absent trials for CHO
    label: str = "SKE-Gaussian20HU-s2px"

    @property
    def peak_contrast_norm(self) -> float:
        return hu_to_norm(np.array(self.peak_contrast_hu)).item()


# ---------------------------------------------------------------------------
# Gaussian lesion insertion
# ---------------------------------------------------------------------------

def gaussian_lesion(shape: Tuple[int, int], center: Tuple[int, int],
                    sigma_px: float, contrast_hu: float) -> np.ndarray:
    """2D Gaussian lesion in HU space (peak = contrast_hu, positive = brighter)."""
    ys, xs = np.ogrid[:shape[0], :shape[1]]
    cy, cx = center
    d2 = (ys - cy) ** 2 + (xs - cx) ** 2
    g = np.exp(-d2 / (2.0 * sigma_px ** 2))
    return g * contrast_hu


def insert_lesion_into_norm(img_norm: np.ndarray, center: Tuple[int, int],
                            task: TaskSpec) -> np.ndarray:
    """Insert a Gaussian lesion into a normalized [0,1] image (HU-space addition)."""
    img_hu = norm_to_hu(img_norm)
    h, w = img_hu.shape
    lesion = gaussian_lesion((h, w), center, task.signal_sigma_px, task.peak_contrast_hu)
    return hu_to_norm(img_hu + lesion)


# ---------------------------------------------------------------------------
# Tissue ROI selection
# ---------------------------------------------------------------------------

def _local_gradient(img: np.ndarray) -> np.ndarray:
    """Gradient magnitude (Sobel) of an image."""
    gx = ndimage.sobel(img, axis=1)
    gy = ndimage.sobel(img, axis=0)
    return np.hypot(gx, gy)


def find_tissue_roi(img_norm: np.ndarray, patch_size: int,
                    task: Optional[TaskSpec] = None,
                    n_attempts: int = 50) -> Tuple[int, int]:
    """Find a homogeneous tissue-only region of size ``patch_size``.

    Scores random candidate patches by closeness to soft-tissue HU, low internal
    gradient, and low std. Returns (row, col) of the top-left corner. If the image is
    smaller than ``patch_size`` the patch is clamped to the image extent (smoke tests
    run on tiny synthetic slices; the protocol still executes).
    """
    if task is None:
        task = TaskSpec()
    h, w = img_norm.shape
    if h <= patch_size or w <= patch_size:
        return (max(0, (h - patch_size) // 2), max(0, (w - patch_size) // 2))

    img_hu = norm_to_hu(img_norm)
    grad = _local_gradient(img_hu)
    lo_hu, hi_hu = task.noise_roi_hu_band

    rng = np.random.default_rng(42)
    best_score = -float("inf")
    best_pos = (h // 2 - patch_size // 2, w // 2 - patch_size // 2)

    for _ in range(n_attempts):
        y0 = rng.integers(0, h - patch_size)
        x0 = rng.integers(0, w - patch_size)
        patch_hu = img_hu[y0:y0 + patch_size, x0:x0 + patch_size]
        patch_grad = grad[y0:y0 + patch_size, x0:x0 + patch_size]

        mean_hu = float(np.mean(patch_hu))
        mean_grad = float(np.mean(patch_grad))
        std_hu = float(np.std(patch_hu))

        hu_center = (lo_hu + hi_hu) / 2.0
        hu_width = (hi_hu - lo_hu) / 2.0
        hu_score = math.exp(-0.5 * ((mean_hu - hu_center) / hu_width) ** 2)
        grad_score = math.exp(-mean_grad / 20.0)
        std_score = math.exp(-std_hu / 50.0)

        score = hu_score * 0.4 + grad_score * 0.4 + std_score * 0.2
        if score > best_score:
            best_score = score
            best_pos = (y0, x0)

    return best_pos


# ---------------------------------------------------------------------------
# CNR
# ---------------------------------------------------------------------------

def compute_cnr(present_patch: np.ndarray, absent_patch: np.ndarray) -> float:
    """CNR = (mu_present - mu_absent) / sigma_absent (Rose criterion: >= 3).

    Returns NaN (not inf) when the noise region has zero variance -- the ratio is
    undefined there (tiny synthetic smoke slices can be locally noise-free; real
    reconstructions are not). NaN is serialised as ``null`` by the RunBundle gate.
    """
    mu_p = float(np.mean(present_patch))
    mu_a = float(np.mean(absent_patch))
    sigma_a = float(np.std(absent_patch))
    if sigma_a <= 0:
        return float("nan")
    return float((mu_p - mu_a) / sigma_a)


# ---------------------------------------------------------------------------
# CHO – Channelized Hotelling Observer
# ---------------------------------------------------------------------------

def _dog_channels(patch_size: int, n_channels: int = 4,
                  sigma0: float = 0.5, factor: float = 2.0) -> np.ndarray:
    """Difference-of-Gaussians channels: G(s0 f^i) - G(s0 f^{i+1})."""
    coords = np.arange(patch_size) - patch_size // 2
    xx, yy = np.meshgrid(coords, coords)
    r2 = xx ** 2 + yy ** 2
    channels = []
    for i in range(n_channels):
        s1 = sigma0 * (factor ** i)
        s2 = sigma0 * (factor ** (i + 1))
        g1 = np.exp(-r2 / (2.0 * s1 ** 2))
        g1 = g1 / g1.sum()
        g2 = np.exp(-r2 / (2.0 * s2 ** 2))
        g2 = g2 / g2.sum()
        channels.append(g1 - g2)
    return np.stack(channels, axis=0)


def _channel_response(patch_hu: np.ndarray, channels: np.ndarray) -> np.ndarray:
    """Channel response at the patch centre (lesion location)."""
    responses = []
    for ch in channels:
        r = signal.convolve2d(patch_hu, ch, mode="valid")
        responses.append(r[r.shape[0] // 2, r.shape[1] // 2])
    return np.array(responses, dtype=np.float64)


def compute_cho_auc(present_patches: Sequence[np.ndarray],
                    absent_patches: Sequence[np.ndarray],
                    n_channels: int = 4) -> float:
    """Channelized Hotelling Observer AUC (Mann-Whitney).

    DOG channels, regularized pooled-covariance Hotelling template.
    """
    if len(present_patches) < 2 or len(absent_patches) < 2:
        return 0.5

    patch_size = present_patches[0].shape[0]
    channels = _dog_channels(patch_size, n_channels=n_channels)

    v_present = np.array([_channel_response(p, channels) for p in present_patches])
    v_absent = np.array([_channel_response(p, channels) for p in absent_patches])

    mu_p = np.mean(v_present, axis=0)
    mu_a = np.mean(v_absent, axis=0)
    n_p, n_a = len(v_present), len(v_absent)

    cov_p = np.cov(v_present, rowvar=False) if n_p > 1 else np.eye(n_channels) * 1e-6
    cov_a = np.cov(v_absent, rowvar=False) if n_a > 1 else np.eye(n_channels) * 1e-6
    S = ((n_p - 1) * cov_p + (n_a - 1) * cov_a) / (n_p + n_a - 2)
    S += np.eye(n_channels) * 1e-4

    diff = mu_p - mu_a
    try:
        w = linalg.solve(S, diff, assume_a="pos")
    except linalg.LinAlgError:
        w = linalg.pinv(S) @ diff

    t_p = v_present @ w
    t_a = v_absent @ w
    return _mann_whitney_auc(t_p, t_a)


def _mann_whitney_auc(scores_present: np.ndarray, scores_absent: np.ndarray) -> float:
    n_p, n_a = len(scores_present), len(scores_absent)
    if n_p == 0 or n_a == 0:
        return 0.5
    count = 0.0
    for sp in scores_present:
        count += float(np.sum(sp > scores_absent) + 0.5 * np.sum(sp == scores_absent))
    return count / (n_p * n_a)


# ---------------------------------------------------------------------------
# NPWE – Non-Prewhitening Observer with Eye Filter
# ---------------------------------------------------------------------------

def _eye_filter(patch_size: int, rho0: float = 0.2) -> np.ndarray:
    coords = np.arange(patch_size) - patch_size // 2
    xx, yy = np.meshgrid(coords, coords)
    rho = np.sqrt(xx ** 2 + yy ** 2) / (patch_size // 2)
    filt = rho * np.exp(-rho / rho0)
    filt[rho == 0] = 0
    return filt


def compute_npwe_score(present_patch: np.ndarray, absent_patch: np.ndarray,
                       task: TaskSpec) -> float:
    """NPWE matched-filter response with an eye filter."""
    delta = present_patch - absent_patch
    center = (present_patch.shape[0] // 2, present_patch.shape[1] // 2)
    sig = gaussian_lesion(present_patch.shape, center, task.signal_sigma_px, task.peak_contrast_hu)
    filt = _eye_filter(present_patch.shape[0])
    filt_f = np.fft.fft2(filt)
    delta_filt = np.fft.ifft2(np.fft.fft2(delta) * filt_f).real
    sig_filt = np.fft.ifft2(np.fft.fft2(sig) * filt_f).real
    return float(np.sum(delta_filt * sig_filt))


# ---------------------------------------------------------------------------
# Per-slice method detectability
# ---------------------------------------------------------------------------

def method_detectability(recon_fn: ReconFn, low_norm: np.ndarray,
                         full_norm: np.ndarray, task: TaskSpec,
                         roi_pos: Optional[Tuple[int, int]] = None,
                         n_trials: Optional[int] = None) -> dict:
    """Run the insertion protocol for one slice through a reconstruction callable.

    Parameters
    ----------
    recon_fn : ReconFn
        ``low_norm_slice [H, W] in [0,1] -> recon_slice [H, W] in [0,1]``. For the WS-3
        reference this is an ensemble forward through the sinogram (see evaluation.py);
        for comparison methods (FBP, Gaussian blur) it is the method itself.
    low_norm : np.ndarray [H, W] in [0, 1]
        Low-dose input slice.
    full_norm : np.ndarray [H, W] in [0, 1]
        Full-dose reference slice (used to pick the tissue ROI).
    task : TaskSpec
    roi_pos : tuple or None
        Pre-computed ROI top-left corner.
    n_trials : int or None
        Override task.n_trials (for fast smoke runs).

    Returns
    -------
    dict: cnr, cho_auc, npwe_score, roi_pos, lesion_center, task_label
    """
    trials = n_trials if n_trials is not None else task.n_trials
    h, w = low_norm.shape
    patch = min(task.roi_size_px, h, w)          # clamp for tiny smoke slices
    if roi_pos is None:
        roi_pos = find_tissue_roi(full_norm, patch, task)
    y0, x0 = roi_pos
    cy, cx = y0 + patch // 2, x0 + patch // 2

    # Lesion-present input: insert lesion at ROI centre of the LOW-DOSE image.
    low_present = insert_lesion_into_norm(low_norm, (cy, cx), task)

    out_present = np.asarray(recon_fn(low_present), dtype=np.float64).clip(0, 1)
    out_absent = np.asarray(recon_fn(low_norm), dtype=np.float64).clip(0, 1)

    # ROI patches from the outputs (HU)
    p_present = norm_to_hu(out_present[y0:y0 + patch, x0:x0 + patch])
    p_absent = norm_to_hu(out_absent[y0:y0 + patch, x0:x0 + patch])

    # Signal region: central disk of the lesion (radius = 2*sigma).
    r = int(math.ceil(task.signal_sigma_px * 2))
    c = patch // 2
    sig_slice = (slice(c - r, c + r + 1), slice(c - r, c + r + 1))
    cnr = compute_cnr(p_present[sig_slice], p_absent[sig_slice])

    # CHO trial patches: jittered lesion positions, present vs absent.
    present_patches, absent_patches = [], []
    rng = np.random.default_rng(42)
    for _ in range(trials):
        jy = int(rng.integers(-2, 3))
        jx = int(rng.integers(-2, 3))
        jc = (cy + jy, cx + jx)
        low_jitter = insert_lesion_into_norm(low_norm, jc, task)
        out_jitter = np.asarray(recon_fn(low_jitter), dtype=np.float64).clip(0, 1)
        q = norm_to_hu(out_jitter[y0:y0 + patch, x0:x0 + patch])
        present_patches.append(q)
        absent_patches.append(p_absent.copy())

    cho_auc = compute_cho_auc(present_patches, absent_patches)
    npwe_score = compute_npwe_score(p_present, p_absent, task)

    return {
        "cnr": cnr,
        "cho_auc": cho_auc,
        "npwe_score": npwe_score,
        "roi_pos": (int(y0), int(x0)),
        "lesion_center": (int(cy), int(cx)),
        "task_label": task.label,
    }


def evaluate_detectability(recon_fn: ReconFn,
                           low_norm_batch: Sequence[np.ndarray],
                           full_norm_batch: Sequence[np.ndarray],
                           task: Optional[TaskSpec] = None,
                           n_trials: Optional[int] = None,
                           max_slices: Optional[int] = None) -> dict:
    """Batch detectability over multiple slices through one reconstruction callable.

    The tissue ROI is chosen once from the first reference slice and reused (same
    anatomical location across the cohort's slices, avoiding anatomy).
    """
    if task is None:
        task = TaskSpec()
    if max_slices is not None:
        low_norm_batch = low_norm_batch[:max_slices]
        full_norm_batch = full_norm_batch[:max_slices]

    patch = min(task.roi_size_px, *np.asarray(full_norm_batch[0]).shape)
    roi_pos = find_tissue_roi(full_norm_batch[0], patch, task)
    cnrs, aucs, npwes = [], [], []
    for low, full in zip(low_norm_batch, full_norm_batch):
        det = method_detectability(recon_fn, low, full, task, roi_pos=roi_pos,
                                   n_trials=n_trials)
        cnrs.append(det["cnr"])
        aucs.append(det["cho_auc"])
        npwes.append(det["npwe_score"])

    return {
        "cnr_mean": float(np.mean(cnrs)),
        "cnr_median": float(np.median(cnrs)),
        "cnr_std": float(np.std(cnrs)),
        "cnr_values": [float(v) for v in cnrs],
        "cho_auc_mean": float(np.mean(aucs)),
        "cho_auc_median": float(np.median(aucs)),
        "npwe_mean": float(np.mean(npwes)),
        "n_slices": len(cnrs),
        "task_label": task.label,
        "roi_pos": (int(roi_pos[0]), int(roi_pos[1])),
    }
