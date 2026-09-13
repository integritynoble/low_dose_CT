#!/usr/bin/env python3
"""Anti-gaming control set for ROI BandER (issue #24, BANDER-1).

Every control is a pure, deterministic function of the FULL-DOSE image and
returns an image in HU. Randomised controls take an explicit seed and use a
local Generator, so no global RNG state is touched and repeated calls with the
same seed are bit-identical.

Nothing here changes a scoring rule, gate, tolerance or registry status. This
module only manufactures inputs so that BandER can be measured on them.

BandER is reproduced from the committed protocol
(WS-1_dataset/R6_recalc/freq_detectability_recalc.py):

    h(img) = img - gaussian_filter(img, sigma=1.0)
    ROI BandER = ||h(out)_roi||^2 / max(||h(fd)_roi||^2, eps_floor)
    eps_floor  = 1e-4 * ||h(fd)||^2 over the full slice

so 1.0 is the ideal: the output carries the same fine-structure energy as the
reference.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage

HF_SIGMA = 1.0
EPS_REL = 1e-4


# ---------------------------------------------------------------- BandER ----
def highfreq_hu(img_hu: np.ndarray) -> np.ndarray:
    """The committed 1-px high-pass band: h = img - G(sigma=1.0)(img)."""
    return img_hu - ndimage.gaussian_filter(img_hu, HF_SIGMA)


def band_energy_ratio(out_hu, fd_hu, mask=None) -> float:
    """ROI BandER of `out_hu` against full-dose `fd_hu`, committed definition."""
    ho, hf = highfreq_hu(out_hu), highfreq_hu(fd_hu)
    floor = EPS_REL * float(np.sum(hf * hf))          # from the FULL slice
    if mask is not None:
        ho, hf = ho[mask], hf[mask]
    return float(np.sum(ho * ho) / max(float(np.sum(hf * hf)), floor))


# --------------------------------------------------------------- controls ---
def ctrl_blur(fd_hu, sigma: float = 1.0):
    """The existing trap: isotropic Gaussian smoothing. Destroys fine structure."""
    return ndimage.gaussian_filter(np.asarray(fd_hu, float), sigma)


def ctrl_noise(fd_hu, sigma_hu: float, seed: int = 0):
    """Pure additive white Gaussian noise. Adds band energy, adds no information."""
    fd = np.asarray(fd_hu, float)
    rng = np.random.default_rng(seed)
    return fd + rng.normal(0.0, sigma_hu, size=fd.shape)


def ctrl_oversharpen(fd_hu, amount: float = 1.0, sigma: float = 1.0):
    """Unsharp mask: out = fd + amount * h(fd). Amplifies the band it is scored on."""
    fd = np.asarray(fd_hu, float)
    return fd + amount * (fd - ndimage.gaussian_filter(fd, sigma))


def ctrl_ringing(fd_hu, keep: float = 0.25):
    """Truncated-frequency reconstruction: keep the central `keep` fraction of
    each FFT axis and zero the rest, producing Gibbs ringing at edges."""
    fd = np.asarray(fd_hu, float)
    F = np.fft.fftshift(np.fft.fft2(fd))
    ny, nx = fd.shape
    m = np.zeros_like(F, dtype=bool)
    hy, hx = int(ny * keep / 2), int(nx * keep / 2)
    m[ny // 2 - hy: ny // 2 + hy + 1, nx // 2 - hx: nx // 2 + hx + 1] = True
    return np.real(np.fft.ifft2(np.fft.ifftshift(F * m)))


def ctrl_lesion_erase(fd_hu, center, radius: int, sigma: float = 3.0):
    """Smooth ONLY inside a disc, leaving the rest of the slice untouched.

    This is the control the whole matrix exists for: it destroys exactly the
    diagnostic content BandER is meant to stand for, while altering a vanishing
    fraction of a whole-ROI energy ratio.
    """
    fd = np.asarray(fd_hu, float)
    yy, xx = np.ogrid[:fd.shape[0], :fd.shape[1]]
    disc = (yy - center[0]) ** 2 + (xx - center[1]) ** 2 <= radius ** 2
    out = fd.copy()
    out[disc] = ndimage.gaussian_filter(fd, sigma)[disc]
    return out


# -------------------------------------------------------------- phantom -----
def synthetic_patch(n: int = 256, seed: int = 12345):
    """A deterministic HU-scale test slice: soft-tissue background, texture,
    vessel-like edges, and one low-contrast lesion at a known location."""
    rng = np.random.default_rng(seed)
    img = np.full((n, n), 40.0)
    yy, xx = np.ogrid[:n, :n]
    img += 6.0 * np.sin(2 * np.pi * xx / 23.0) * np.cos(2 * np.pi * yy / 19.0)
    img[(yy - n // 3) ** 2 + (xx - n // 3) ** 2 <= 30 ** 2] = 95.0     # organ
    img[:, n // 2 - 1: n // 2 + 1] = 300.0                              # sharp edge
    les_c, les_r = (2 * n // 3, 2 * n // 3), 10
    img[(yy - les_c[0]) ** 2 + (xx - les_c[1]) ** 2 <= les_r ** 2] += 20.0
    img += rng.normal(0.0, 3.0, size=img.shape)                         # FD noise
    return img, les_c, les_r
