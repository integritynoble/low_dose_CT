"""LEARN baseline (PyTorch faithful re-implementation).

LEARN: Learned Experts' Assessment-based Reconstruction Network
(H. Chen, Y. Zhang, Y. Chen, J. Zhang, W. Zhang, H. Sun, Y. Lv, P. Liao,
 J. Zhou, G. Wang, "LEARN: Learned Experts' Assessment-based Reconstruction
 Network for Sparse-data CT", IEEE TMI 37(6):1333-1347, 2018).

The official release (github.com/FrankZhangYK/LEARN) is MATLAB + MatConvNet;
this module is a PyTorch re-implementation of its unrolled-iterative
architecture adapted to the PWM-LDCT v0.5 image-domain protocol
(low-dose -> full-dose denoising, mapping [B,1,H,W] -> [B,1,H,W]):

    u_0 = x                        (input: low-dose image)
    u_k = u_{k-1} - eta_k * (u_{k-1} - x) + R_k(u_{k-1}),   k = 1..K

where the first term is the data-consistency / expert-update step with
learnable per-step step-size eta_k, and R_k is a per-step CNN (the learned
"expert assessment" regularizer). K unrolled stages, each with its own CNN
and step-size, matching the paper's alternating update structure.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class _Regularizer(nn.Module):
    """Small CNN regularizer R_k: 3 conv layers, residual (matches LEARN's per-stage CNN)."""

    def __init__(self, nf: int = 64):
        super().__init__()
        self.body = nn.Sequential(
            nn.Conv2d(1, nf, 3, padding=1, bias=True),
            nn.ReLU(inplace=True),
            nn.Conv2d(nf, nf, 3, padding=1, bias=True),
            nn.ReLU(inplace=True),
            nn.Conv2d(nf, 1, 3, padding=1, bias=True),
        )
        # LEARN initializes the regularizer to (approximately) identity at start
        # so early training begins close to the data-consistency baseline.
        for m in self.body.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode="fan_in", nonlinearity="relu")
        with torch.no_grad():
            self.body[-1].weight.zero_()
            self.body[-1].bias.zero_()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.body(x)


class LEARN(nn.Module):
    """K-stage unrolled iterative reconstruction network (image-domain)."""

    def __init__(self, K: int = 5, nf: int = 64):
        super().__init__()
        self.K = K
        self.regularizers = nn.ModuleList([_Regularizer(nf=nf) for _ in range(K)])
        self.etas = nn.ParameterList([nn.Parameter(torch.tensor(0.1)) for _ in range(K)])

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        u = x
        for k in range(self.K):
            # data-consistency / expert update: pull back toward the measurement
            u = u - self.etas[k] * (u - x)
            # learned regularizer (CNN residual update)
            u = u + self.regularizers[k](u)
        return u


def learn_K5() -> LEARN:
    return LEARN(K=5, nf=64)
