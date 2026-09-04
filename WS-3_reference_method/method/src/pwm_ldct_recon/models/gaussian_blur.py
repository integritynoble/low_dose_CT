"""Gaussian blur trap — standing reference that wins on PSNR and fails on detectability.

Port of ``WS-1_dataset/baselines/src/pwm_ldct_baselines/models/gaussian_blur.py`` with
identical parameters (sigma=1.0 px, kernel=5x5). The blur is the canonical trap from
low-dose-ct.md §4 / Rung 1.3: a fixed smoothing that scores higher PSNR than learned
denoisers yet fails the Rose criterion (CNR < 3), proving that fidelity alone is
insufficient for diagnostic assessment.

The blur is a **permanent fixture** in the WS-3 evaluation suite: reference methods are
allowed to fail, the blur stays (Rung 1.3). It is exposed both as a torch module
(``GaussianBlur``, for torch-context baselines) and as a numpy recon callable
(``blur_recon_fn``, for the detectability protocol in ``pwm_ldct_recon.evaluation``).
"""
from __future__ import annotations

from typing import Callable

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

BLUR_SIGMA_PX = 1.0
BLUR_KERNEL_SIZE = 5


def _gauss_kernel_1d(sigma: float, radius: int) -> torch.Tensor:
    """1D Gaussian kernel."""
    coords = torch.arange(2 * radius + 1, dtype=torch.float32) - radius
    kernel = torch.exp(-0.5 * (coords / sigma) ** 2)
    return kernel / kernel.sum()


def _gauss_kernel_2d(sigma: float, radius: int) -> torch.Tensor:
    """2D Gaussian kernel (separable)."""
    k1d = _gauss_kernel_1d(sigma, radius)
    k2d = k1d.unsqueeze(1) @ k1d.unsqueeze(0)  # outer product
    return k2d


class GaussianBlur(nn.Module):
    """Fixed Gaussian blur applied per-channel (1ch input).

    Parameters
    ----------
    sigma : float
        Gaussian sigma in pixels. Default 1.0 (the canonical trap value).
    kernel_size : int
        Kernel radius (full size = 2*radius+1). Default 5 (radius=2).

    The kernel is fixed at construction and not trainable.
    """

    def __init__(self, sigma: float = BLUR_SIGMA_PX, kernel_size: int = BLUR_KERNEL_SIZE):
        super().__init__()
        assert kernel_size % 2 == 1, "kernel_size must be odd"
        radius = kernel_size // 2
        k = _gauss_kernel_2d(sigma, radius)
        # Register as buffer: [1, 1, kernel_size, kernel_size]
        self.register_buffer("kernel", k.unsqueeze(0).unsqueeze(0))
        self.padding = radius
        self._sigma = sigma

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, 1, H, W] in [0, 1]
        return F.conv2d(x, self.kernel, padding=self.padding)

    @property
    def sigma(self) -> float:
        return self._sigma

    def extra_repr(self) -> str:
        return f"sigma={self._sigma}, kernel_size={self.kernel.shape[-1]}"


def blur_recon_fn(sigma: float = BLUR_SIGMA_PX,
                  kernel_size: int = BLUR_KERNEL_SIZE) -> Callable[[np.ndarray], np.ndarray]:
    """Numpy recon callable for the blur trap: [H, W] in [0,1] -> blurred [H, W] in [0,1].

    Matches the GaussianBlur module's fixed separable kernel exactly; used by the
    detectability protocol and the paired-evaluation block.
    """
    model = GaussianBlur(sigma=sigma, kernel_size=kernel_size)

    def fn(low_norm_slice: np.ndarray) -> np.ndarray:
        x = torch.from_numpy(np.asarray(low_norm_slice, dtype=np.float32))[None, None]
        with torch.no_grad():
            return model(x)[0, 0].clamp(0, 1).numpy()

    return fn
