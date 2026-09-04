"""Reconstruction-quality metrics: PSNR, SSIM (Gaussian-windowed), optional LPIPS.

All operate on single-channel images in [0, 1] (the harness normalizes HU -> [0,1]); pass
``data_range=1.0``. LPIPS is computed only if the ``lpips`` package is importable, else None.
"""
from __future__ import annotations

import math
from typing import Optional

import torch
import torch.nn.functional as F


def psnr(pred: torch.Tensor, target: torch.Tensor, data_range: float = 1.0) -> float:
    mse = F.mse_loss(pred, target).item()
    if mse <= 0:
        return float("inf")
    return 20.0 * math.log10(data_range) - 10.0 * math.log10(mse)


def _gaussian_window(size: int, sigma: float, device) -> torch.Tensor:
    coords = torch.arange(size, dtype=torch.float32, device=device) - size // 2
    g = torch.exp(-(coords ** 2) / (2 * sigma ** 2))
    g = (g / g.sum()).unsqueeze(0)
    w = (g.t() @ g).unsqueeze(0).unsqueeze(0)  # [1,1,size,size]
    return w


def ssim(pred: torch.Tensor, target: torch.Tensor, data_range: float = 1.0,
         win_size: int = 11, sigma: float = 1.5) -> float:
    """Mean SSIM over a [B,1,H,W] (or [1,H,W]) pair."""
    if pred.dim() == 3:
        pred, target = pred.unsqueeze(0), target.unsqueeze(0)
    w = _gaussian_window(win_size, sigma, pred.device)
    c1, c2 = (0.01 * data_range) ** 2, (0.03 * data_range) ** 2
    mu_p = F.conv2d(pred, w)
    mu_t = F.conv2d(target, w)
    mu_p2, mu_t2, mu_pt = mu_p ** 2, mu_t ** 2, mu_p * mu_t
    sig_p = F.conv2d(pred * pred, w) - mu_p2
    sig_t = F.conv2d(target * target, w) - mu_t2
    sig_pt = F.conv2d(pred * target, w) - mu_pt
    s = ((2 * mu_pt + c1) * (2 * sig_pt + c2)) / ((mu_p2 + mu_t2 + c1) * (sig_p + sig_t + c2))
    return float(s.mean().item())


_LPIPS = None


def lpips(pred: torch.Tensor, target: torch.Tensor) -> Optional[float]:
    """Optional LPIPS (AlexNet). Returns None if the ``lpips`` package is unavailable."""
    global _LPIPS
    try:
        import lpips as _lp
    except Exception:
        return None
    if _LPIPS is None:
        _LPIPS = _lp.LPIPS(net="alex", verbose=False)
    if _LPIPS is not None and pred.is_cuda and next(_LPIPS.parameters()).device != pred.device:
        _LPIPS = _LPIPS.to(pred.device)
    if pred.dim() == 3:
        pred, target = pred.unsqueeze(0), target.unsqueeze(0)
    # LPIPS expects 3-channel in [-1, 1]
    p = (pred.clamp(0, 1) * 2 - 1).repeat(1, 3, 1, 1)
    t = (target.clamp(0, 1) * 2 - 1).repeat(1, 3, 1, 1)
    with torch.no_grad():
        return float(_LPIPS(p, t).mean().item())
