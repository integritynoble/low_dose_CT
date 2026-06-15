"""Reconstruction-quality metrics (PSNR / SSIM) on [0,1] single-channel images.

Mirrors the WS-1 baseline harness (``pwm_ldct_baselines.metrics``) so WS-3 fidelity
numbers (manuscript tab:reconstruction_quality) are comparable across the two repos.
"""
from __future__ import annotations

import math

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
    return (g.t() @ g).unsqueeze(0).unsqueeze(0)


def ssim(pred: torch.Tensor, target: torch.Tensor, data_range: float = 1.0,
         win_size: int = 11, sigma: float = 1.5) -> float:
    if pred.dim() == 3:
        pred, target = pred.unsqueeze(0), target.unsqueeze(0)
    w = _gaussian_window(win_size, sigma, pred.device)
    c1, c2 = (0.01 * data_range) ** 2, (0.03 * data_range) ** 2
    mu_p, mu_t = F.conv2d(pred, w), F.conv2d(target, w)
    mu_p2, mu_t2, mu_pt = mu_p ** 2, mu_t ** 2, mu_p * mu_t
    sig_p = F.conv2d(pred * pred, w) - mu_p2
    sig_t = F.conv2d(target * target, w) - mu_t2
    sig_pt = F.conv2d(pred * target, w) - mu_pt
    s = ((2 * mu_pt + c1) * (2 * sig_pt + c2)) / ((mu_p2 + mu_t2 + c1) * (sig_p + sig_t + c2))
    return float(s.mean().item())


def spearman(a: torch.Tensor, b: torch.Tensor) -> float:
    """Spearman rank correlation (manuscript UQ validation: per-pixel sigma vs error)."""
    a, b = a.flatten().float(), b.flatten().float()
    ra = a.argsort().argsort().float()
    rb = b.argsort().argsort().float()
    ra = ra - ra.mean()
    rb = rb - rb.mean()
    denom = (ra.norm() * rb.norm()).clamp_min(1e-12)
    return float((ra @ rb / denom).item())
