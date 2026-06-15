"""Unrolled iterative reconstruction (manuscript Architecture; Table S1).

K gradient-descent-network steps: each iteration takes one data-consistency gradient
step against the measurement, then applies the shared-weight residual denoiser. The
data-term gradient ``R^T(R x - y)`` is obtained by autograd through ``RadonTransform.forward``,
so the adjoint is exactly consistent with the forward operator and stays differentiable for
end-to-end unrolling (no hand-written, possibly-mismatched adjoint).

    x_0      = FBP(y)                                  # warm start (S1: TV-FBP)
    x_{k+1}  = f_theta( x_k - tau * R^T(R x_k - y) )   # K times, weights shared
"""
from __future__ import annotations

from typing import Optional

import torch
import torch.nn as nn

from ..config import ReconConfig
from ..physics import RadonTransform
from .unet import UNetDenoiser


class UnrolledRecon(nn.Module):
    def __init__(self, physics: RadonTransform, denoiser: Optional[UNetDenoiser] = None,
                 cfg: Optional[ReconConfig] = None, estimate_step: bool = True):
        super().__init__()
        self.cfg = cfg or ReconConfig()
        self.physics = physics
        self.denoiser = denoiser or UNetDenoiser(channels=self.cfg.unet_channels)
        self.iterations = self.cfg.iterations
        # learned scalar step size; init = dc_step_init / ||R||_2^2 (Table S1).
        scale = self.physics.opnorm_sq() if estimate_step else 1.0
        tau0 = self.cfg.dc_step_init / max(scale, 1e-8)
        self.log_tau = nn.Parameter(torch.log(torch.tensor(float(tau0))))

    @property
    def tau(self) -> torch.Tensor:
        return torch.exp(self.log_tau)  # keep the step size positive

    def _dc_grad(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """``R^T(R x - y)`` via autograd through forward. Differentiable when training."""
        with torch.enable_grad():
            need_leaf = not x.requires_grad
            xin = x.detach().requires_grad_(True) if need_leaf else x
            resid = self.physics.forward(xin) - y
            dc = 0.5 * (resid ** 2).sum()
            (grad,) = torch.autograd.grad(dc, xin, create_graph=self.training and not need_leaf)
        return grad

    def forward(self, y: torch.Tensor, x_init: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Reconstruct from measurement ``y [B,1,V,D]``; returns image ``[B,1,H,W]``."""
        x = self.physics.fbp(y) if x_init is None else x_init
        for _ in range(self.iterations):
            x = x - self.tau * self._dc_grad(x, y)
            x = self.denoiser(x)
        return x
