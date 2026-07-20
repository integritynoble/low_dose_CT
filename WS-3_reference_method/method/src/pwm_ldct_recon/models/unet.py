"""Compact U-Net denoiser f_theta (Supplementary Table S1).

4 encoder / 4 decoder stages, channels ``(32, 64, 128, 256)``, GroupNorm + GELU,
bilinear upsampling, single-channel in/out, ~4M parameters. Used as a *residual*
denoiser inside the unrolled loop with weights shared across all K iterations.
"""
from __future__ import annotations

from typing import Sequence

import torch
import torch.nn as nn
import torch.nn.functional as F


def _norm(c: int) -> nn.GroupNorm:
    # GroupNorm (S1) -- batch-size-independent, so the unrolled loop is stable at batch 4.
    return nn.GroupNorm(num_groups=min(8, c), num_channels=c)


class _Block(nn.Module):
    """Two 3x3 convs with GroupNorm + GELU (S1 activation/normalisation)."""

    def __init__(self, cin: int, cout: int):
        super().__init__()
        self.c1 = nn.Conv2d(cin, cout, 3, padding=1)
        self.n1 = _norm(cout)
        self.c2 = nn.Conv2d(cout, cout, 3, padding=1)
        self.n2 = _norm(cout)
        self.act = nn.GELU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.act(self.n1(self.c1(x)))
        return self.act(self.n2(self.c2(x)))


class UNetDenoiser(nn.Module):
    """Residual U-Net: returns ``x + f_theta(x)`` so a zero net is the identity (stable warm start)."""

    def __init__(self, channels: Sequence[int] = (32, 64, 128, 256), in_ch: int = 1):
        super().__init__()
        chs = list(channels)
        self.stem = nn.Conv2d(in_ch, chs[0], 3, padding=1)
        # encoder
        self.enc = nn.ModuleList()
        for i in range(len(chs) - 1):
            self.enc.append(_Block(chs[i], chs[i + 1]))
        self.bottleneck = _Block(chs[-1], chs[-1])
        # decoder (bilinear upsample + skip concat)
        self.dec = nn.ModuleList()
        for i in range(len(chs) - 1, 0, -1):
            self.dec.append(_Block(chs[i] + chs[i - 1], chs[i - 1]))
        self.head = nn.Conv2d(chs[0], in_ch, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.stem(x)
        skips = [h]                       # [h0, e0, e1, e2]
        for blk in self.enc:
            h = F.max_pool2d(h, 2)
            h = blk(h)
            skips.append(h)
        h = self.bottleneck(h)
        skips.pop()                       # drop e2: bottleneck-level, not a skip target
        for blk in self.dec:
            skip = skips.pop()            # e1, then e0, then h0
            h = F.interpolate(h, size=skip.shape[-2:], mode="bilinear", align_corners=False)
            h = blk(torch.cat([h, skip], dim=1))
        return x + self.head(h)
