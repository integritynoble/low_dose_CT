"""Parallel-beam Radon transform: differentiable forward + backprojection + FBP warm start.

The WS-3 plan reuses ``pwm_core.contrib.modalities.ct_radon`` as the single forward-model
source of truth (manuscript Table S1, ``\\todo`` version pin). That package is not vendored
into this repo, so this module is a **self-contained, drop-in-compatible** parallel-beam
implementation with the same role: a differentiable ``forward`` so the unrolled loop's
data-consistency term can be back-propagated, plus a filtered-backprojection warm start.

Swap-in contract: a replacement need only provide ``forward(image) -> sinogram`` (differentiable)
and ``fbp(sinogram) -> image``; the unrolled model computes the data-term gradient by autograd
through ``forward``, so the adjoint is always exactly consistent with whatever ``forward`` is.

Conventions: images are ``[B, 1, H, W]``, sinograms ``[B, 1, n_views, n_dets]``, angles span
``[0, pi)``. Rotation uses ``grid_sample`` (bilinear), so everything is GPU-ready and autograd-safe.
"""
from __future__ import annotations

import math
from typing import Optional, cast

import torch
import torch.nn.functional as F


class RadonTransform(torch.nn.Module):
    """Parallel-beam Radon operator over a fixed angle set.

    Args:
        n_views: number of projection angles uniformly spanning ``[0, pi)``.
        n_dets: detector bins; defaults to the image width (single-pixel detector pitch).
        img_size: reconstruction grid side length (square).
        filter_name: FBP filter, ``"ramp"`` (Ram-Lak) or ``"hann"`` (manuscript S1 \\todo{filter}).
    """

    def __init__(self, n_views: int = 720, n_dets: Optional[int] = None,
                 img_size: int = 512, filter_name: str = "ramp"):
        super().__init__()
        self.n_views = int(n_views)
        self.img_size = int(img_size)
        self.n_dets = int(n_dets) if n_dets is not None else self.img_size
        self.filter_name = filter_name
        angles = torch.linspace(0.0, math.pi, self.n_views + 1)[:-1]  # [0, pi)
        self.register_buffer("angles", angles)
        self.register_buffer("_fbp_filter", self._make_filter(self.n_dets, filter_name))

    # register_buffer is typed as Tensor|Module; these cast back to Tensor for the type checker.
    @property
    def _ang(self) -> torch.Tensor:
        return cast(torch.Tensor, self.angles)

    @property
    def _filt(self) -> torch.Tensor:
        return cast(torch.Tensor, self._fbp_filter)

    # ------------------------------------------------------------------ #
    # rotation primitive (shared by forward + backprojection)
    # ------------------------------------------------------------------ #
    def _rotate(self, x: torch.Tensor, angle: torch.Tensor) -> torch.Tensor:
        """Rotate ``[N,1,H,W]`` by ``angle`` radians (CCW) about the centre, bilinear."""
        n = x.shape[0]
        cos, sin = torch.cos(angle), torch.sin(angle)
        # affine_grid expects the inverse (output->input) map; rotation is orthogonal.
        theta = torch.zeros(n, 2, 3, dtype=x.dtype, device=x.device)
        theta[:, 0, 0], theta[:, 0, 1] = cos, -sin
        theta[:, 1, 0], theta[:, 1, 1] = sin, cos
        grid = F.affine_grid(theta, list(x.shape), align_corners=False)
        return F.grid_sample(x, grid, align_corners=False, padding_mode="zeros")

    # ------------------------------------------------------------------ #
    # forward / backprojection
    # ------------------------------------------------------------------ #
    def forward(self, image: torch.Tensor) -> torch.Tensor:
        """Radon transform ``image [B,1,H,W] -> sinogram [B,1,n_views,n_dets]`` (differentiable)."""
        if image.dim() != 4 or image.shape[1] != 1:
            raise ValueError(f"expected [B,1,H,W]; got {tuple(image.shape)}")
        b = image.shape[0]
        proj = []
        for a in self._ang:
            rot = self._rotate(image, a.expand(b))
            line = rot.sum(dim=-2)                      # integrate along rows -> [B,1,W]
            proj.append(line)
        sino = torch.stack(proj, dim=2)                  # [B,1,n_views,W]
        if sino.shape[-1] != self.n_dets:
            sino = F.interpolate(sino, size=(self.n_views, self.n_dets),
                                 mode="bilinear", align_corners=False)
        return sino

    def backproject(self, sino: torch.Tensor) -> torch.Tensor:
        """Unfiltered backprojection ``sinogram -> image`` (the smearing adjoint of forward)."""
        if sino.dim() != 4 or sino.shape[2] != self.n_views:
            raise ValueError(f"expected [B,1,n_views,n_dets]; got {tuple(sino.shape)}")
        b = sino.shape[0]
        if sino.shape[-1] != self.img_size:
            sino = F.interpolate(sino, size=(self.n_views, self.img_size),
                                 mode="bilinear", align_corners=False)
        acc = torch.zeros(b, 1, self.img_size, self.img_size,
                          dtype=sino.dtype, device=sino.device)
        for i, a in enumerate(self._ang):
            line = sino[:, :, i, :]                       # [B,1,W]
            smear = line.unsqueeze(-2).expand(b, 1, self.img_size, self.img_size)
            acc = acc + self._rotate(smear, -a.expand(b))
        return acc * (math.pi / self.n_views)

    # ------------------------------------------------------------------ #
    # FBP warm start
    # ------------------------------------------------------------------ #
    @staticmethod
    def _make_filter(n_dets: int, name: str) -> torch.Tensor:
        """1-D frequency-domain ramp (optionally Hann-apodised) of length ``n_dets``."""
        freqs = torch.fft.fftfreq(n_dets).abs() * 2.0     # ramp in [0,1]
        if name == "hann":
            freqs = freqs * (0.5 + 0.5 * torch.cos(math.pi * freqs))
        elif name not in ("ramp", "ram-lak", "ramlak"):
            raise ValueError(f"unknown FBP filter {name!r}")
        return freqs

    def fbp(self, sino: torch.Tensor) -> torch.Tensor:
        """Filtered backprojection warm start (manuscript S1 'TV-FBP' before the TV stage)."""
        f = self._filt.to(sino.device, sino.dtype)
        spec = torch.fft.fft(sino, dim=-1)
        filtered = torch.fft.ifft(spec * f, dim=-1).real
        return self.backproject(filtered)

    # ------------------------------------------------------------------ #
    # operator-norm estimate (for the data-consistency step-size init)
    # ------------------------------------------------------------------ #
    @torch.no_grad()
    def opnorm_sq(self, n_iter: int = 8) -> float:
        """Power-iteration estimate of ``||R||_2^2`` (Table S1 tau init = 0.5/||R||_2^2)."""
        x = torch.randn(1, 1, self.img_size, self.img_size,
                        device=self._ang.device)
        x = x / x.norm()
        val = 1.0
        for _ in range(n_iter):
            y = self.backproject(self.forward(x))
            val = float(y.norm())
            x = y / (y.norm() + 1e-12)
        return val
