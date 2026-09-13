"""CoreDiff (Gao et al., arXiv:2304.01814) bridge for the PWM-LDCT v0.5 harness.

The official repo trains with 3-channel context (prev, cur, next) low-dose slices and
a T=10 DDIM diffusion schedule.  This module exposes a torch.nn.Module with two entry
points:

  * ``forward(x, y, n_iter)``   training: official two-stage interpolated denoising,
                                returns (recon, recon_sub1) used with 0.5/0.5 MSE loss.
  * ``sample(x, n_iter)``       inference: official DDIM sampling, returns [B,1,H,W].

Checkpoint format matches the harness: ``{"model": "corediff", "state_dict": ...}``.
"""
from __future__ import annotations

import os
import sys

import torch
import torch.nn as nn

_VENDOR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "vendor", "CoreDiff"))
if _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)

try:  # noqa: E402
    from models.corediff.corediff_wrapper import Network
    from models.corediff.diffusion_modules import Diffusion
except ModuleNotFoundError as _exc:  # pragma: no cover - depends on the fetch
    # CoreDiff is fetched, not vendored: upstream carries no licence, so this
    # project does not redistribute it. Say that plainly instead of surfacing a
    # bare ModuleNotFoundError that looks like a broken install.
    raise ModuleNotFoundError(
        "CoreDiff is not present. It is fetched rather than vendored, because "
        "upstream (https://github.com/qgao21/CoreDiff) carries no licence and "
        "this project does not redistribute it.\n"
        "    run: %s\n"
        "See %s for why, and record the commit you fetch alongside any results.\n"
        "Every other baseline (RED-CNN, LEARN, CTformer, the blur trap) is "
        "unaffected."
        % (os.path.join(_VENDOR, "fetch.sh"), os.path.join(_VENDOR, "README.md"))
    ) from _exc


class CoreDiffWrapper(nn.Module):
    def __init__(self, img_size: int = 512, in_channels: int = 3, out_channels: int = 1,
                 T: int = 10, sampling_routine: str = "ddim",
                 start_adjust_iter: int = 1, context: bool = True):
        super().__init__()
        self.context = context
        self.T = T
        self.sampling_routine = sampling_routine
        self.start_adjust_iter = start_adjust_iter
        denoise_fn = Network(in_channels=in_channels, out_channels=out_channels, context=context)
        self.model = Diffusion(denoise_fn=denoise_fn, image_size=img_size,
                               channels=out_channels, timesteps=T, context=context)

    def forward(self, x, y=None, n_iter: int = 1):
        # x: (B, 3, H, W) low-dose context; y: (B, 1, H, W) full-dose
        x_recon, _x_mix, x_recon_sub1, _x_mix_sub1 = self.model(
            x, y, n_iter,
            only_adjust_two_step=False,
            start_adjust_iter=self.start_adjust_iter,
        )
        return x_recon, x_recon_sub1

    @torch.no_grad()
    def sample(self, x, n_iter: int = 1):
        gen, _direct, _imstep = self.model.sample(
            batch_size=x.shape[0], img=x, t=self.T,
            sampling_routine=self.sampling_routine, n_iter=n_iter,
            start_adjust_iter=self.start_adjust_iter,
        )
        return gen
