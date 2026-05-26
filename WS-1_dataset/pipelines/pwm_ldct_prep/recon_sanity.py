"""Reconstruction-sanity harness (manuscript Technical Validation -> Reconstruction sanity).

Provides the reconstruction machinery (parallel-beam Radon + filtered back-projection), the
agreement metric, and a self-consistency round-trip. numpy-only (no scipy/skimage).

SCOPE / honesty: a faithful FBP round-trip on the *real helical* DICOM-CT-PD projections requires
the calibrated fan + helical geometry (rebinning, view weighting, table feed) — the part flagged
``calibration_status`` in the geometry, pending the official data dictionary. The series-level
check here uses a crude parallel rebinning of the central detector row and is therefore
**approximate and uncalibrated**; it returns a status flag saying so and must not be read as a
pass/fail validation on real data. The genuinely-validated piece is ``self_consistency`` (our
Radon -> our FBP recovers a phantom), which exercises the machinery + metric.
"""
from __future__ import annotations

from typing import Dict, Sequence

import numpy as np


# --- parallel-beam Radon + FBP (numpy) --------------------------------------------------
def _bilinear(img: np.ndarray, ys: np.ndarray, xs: np.ndarray) -> np.ndarray:
    h, w = img.shape
    x0 = np.floor(xs).astype(int)
    y0 = np.floor(ys).astype(int)
    wx, wy = xs - x0, ys - y0

    def gather(yy, xx):
        m = (yy >= 0) & (yy < h) & (xx >= 0) & (xx < w)
        out = img[np.clip(yy, 0, h - 1), np.clip(xx, 0, w - 1)].astype(np.float64)
        out[~m] = 0.0
        return out

    return (gather(y0, x0) * (1 - wx) * (1 - wy) + gather(y0, x0 + 1) * wx * (1 - wy)
            + gather(y0 + 1, x0) * (1 - wx) * wy + gather(y0 + 1, x0 + 1) * wx * wy)


def _rotate(img: np.ndarray, angle_deg: float) -> np.ndarray:
    h, w = img.shape
    cy, cx = (h - 1) / 2.0, (w - 1) / 2.0
    th = np.deg2rad(angle_deg)
    cos, sin = np.cos(th), np.sin(th)
    ys, xs = np.mgrid[0:h, 0:w]
    xr, yr = xs - cx, ys - cy
    return _bilinear(img, -sin * xr + cos * yr + cy, cos * xr + sin * yr + cx)


def parallel_radon(image: np.ndarray, angles_deg: Sequence[float]) -> np.ndarray:
    """Parallel-beam forward projection -> sinogram [n_angles, n_det=width]."""
    return np.stack([_rotate(image, a).sum(axis=0) for a in angles_deg], axis=0)


def fbp(sinogram: np.ndarray, angles_deg: Sequence[float], out_size: int = None) -> np.ndarray:
    """Filtered back-projection (Ram-Lak) of a parallel-beam sinogram [n_angles, n_det]."""
    n_ang, n_det = sinogram.shape
    ramp = np.abs(np.fft.fftfreq(n_det)) * 2.0
    filtered = np.real(np.fft.ifft(np.fft.fft(sinogram, axis=1) * ramp[None, :], axis=1))
    size = out_size or n_det
    cy = cx = (size - 1) / 2.0
    ys, xs = np.mgrid[0:size, 0:size]
    xr, yr = xs - cx, ys - cy
    recon = np.zeros((size, size), dtype=np.float64)
    for i, a in enumerate(angles_deg):
        th = np.deg2rad(a)
        t = xr * np.cos(th) + yr * np.sin(th) + (n_det - 1) / 2.0
        t0 = np.clip(np.floor(t).astype(int), 0, n_det - 1)
        t1 = np.clip(t0 + 1, 0, n_det - 1)
        frac = t - np.floor(t)
        recon += filtered[i][t0] * (1 - frac) + filtered[i][t1] * frac
    return recon * (np.pi / (2 * max(1, n_ang)))


# --- metric + self-consistency ----------------------------------------------------------
def agreement(a: np.ndarray, b: np.ndarray, tol: float = 5.0) -> Dict:
    """Per-voxel agreement between two images (same shape). ``tol`` in image units (HU)."""
    a = np.asarray(a, np.float64)
    b = np.asarray(b, np.float64)
    diff = np.abs(a - b)
    af, bf = a.ravel(), b.ravel()
    if af.std() > 0 and bf.std() > 0:
        pearson = float(np.corrcoef(af, bf)[0, 1])
    else:
        pearson = 1.0 if np.allclose(af, bf) else 0.0
    return {
        "max_abs": float(diff.max()),
        "rmse": float(np.sqrt(np.mean(diff ** 2))),
        "frac_within_tol": float(np.mean(diff <= tol)),
        "pearson_r": pearson,
    }


def self_consistency(image: np.ndarray, n_angles: int = 180) -> Dict:
    """Our Radon -> our FBP on ``image``; returns agreement (structural recovery via pearson_r)."""
    angles = np.linspace(0.0, 180.0, n_angles, endpoint=False)
    recon = fbp(parallel_radon(image, angles), angles, out_size=image.shape[0])
    return agreement(image, recon)


def check_series_projection_recon(projections: np.ndarray, recon_volume: np.ndarray,
                                  geometry: Dict) -> Dict:
    """Best-effort, UNCALIBRATED projection->recon check for a series (see module docstring).

    Crude parallel rebinning of the central detector row; not a calibrated fan/helical recon.
    Returns the agreement metric on a central slice plus an explicit ``status``.
    """
    if projections is None or projections.ndim != 3:
        return {"status": "no_projections"}
    n_views, n_chan, n_rows = projections.shape
    sino = projections[:, :, n_rows // 2]                  # [n_views, n_chan]
    angles = np.linspace(0.0, 360.0, n_views, endpoint=False)
    est = fbp(sino, angles, out_size=recon_volume.shape[1])
    ref = recon_volume[recon_volume.shape[0] // 2]
    metric = agreement(est, ref, tol=50.0)
    metric["status"] = "approximate_uncalibrated_parallel_rebin"
    metric["note"] = ("not a calibrated fan/helical reconstruction; full reconstruction-sanity "
                      "requires the DICOM-CT-PD data dictionary geometry")
    return metric
