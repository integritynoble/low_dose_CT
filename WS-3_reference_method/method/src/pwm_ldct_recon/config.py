"""Configuration dataclasses mirroring Supplementary Table S1 (hyperparameters).

These are the single source of truth for the values the manuscript reports: every
default here corresponds to a fixed cell of ``paper_draft/supplementary.tex`` Table S1.
The ``\\todo`` cells in that table (peak LR, weight decay, epochs, geometry) are the
fields a real Phase-3 run sets and then back-fills into the table; their defaults below
are reasonable starting points flagged with ``# S1 \\todo``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class ReconConfig:
    """One ensemble member: unrolled reconstruction + denoiser + optimisation (Table S1)."""

    # --- Unrolled reconstruction ---
    iterations: int = 10                         # S1: Iterations K
    dc_step_init: float = 0.5                     # S1: tau init = 0.5 / ||R||_2^2 (scaled in model)
    recon_loss: str = "l1"                        # S1: MAE (L1) on HU

    # --- Projection geometry (S1 \todo{geometry}) ---
    n_views: int = 720                            # S1 \todo: parallel-beam views over [0, pi)
    n_dets: int = 512                             # S1 \todo: detector bins (= slice width)
    fbp_filter: str = "ramp"                      # S1 \todo: Ram-Lak warm-start filter

    # --- Denoiser f_theta (weights shared across iterations) ---
    unet_channels: Sequence[int] = (32, 64, 128, 256)  # S1: channels per stage
    unet_norm: str = "group"                      # S1: GroupNorm
    unet_act: str = "gelu"                         # S1: GELU
    unet_upsample: str = "bilinear"               # S1: bilinear

    # --- Optimisation ---
    optimizer: str = "adamw"                       # S1: AdamW
    peak_lr: float = 2e-4                          # S1 \todo{lr}
    weight_decay: float = 1e-4                     # S1 \todo{wd}
    lr_schedule: str = "cosine"                    # S1: cosine, 5% linear warmup
    warmup_frac: float = 0.05
    epochs: int = 100                              # S1 \todo{epochs}
    batch_size: int = 4                            # S1: 4
    slice_size: int = 512                          # S1: full 512x512 axial slice

    # --- Training data ---
    # S1: dose levels and per-minibatch mix weights. r=1.00 is the reference
    # (not a trained/credentialed dose; see manuscript M4), so it is absent here.
    doses: Sequence[float] = (0.10, 0.25, 0.50)
    dose_mix_weights: Sequence[float] = (0.4, 0.4, 0.2)
    aug_flip_p: float = 0.5
    aug_rot_deg: float = 5.0
    aug_wl_shift_hu: float = 50.0

    seed: int = 42

    def __post_init__(self) -> None:
        if len(self.doses) != len(self.dose_mix_weights):
            raise ValueError("doses and dose_mix_weights must align (S1 dose-mix row).")
        if abs(sum(self.dose_mix_weights) - 1.0) > 1e-6:
            raise ValueError("dose_mix_weights must sum to 1.0.")


@dataclass(frozen=True)
class EnsembleConfig:
    """Deep ensemble (Table S1): M independently-seeded members for UQ via disagreement."""

    members: int = 5                               # S1: Members M = 5
    seeds: Sequence[int] = (42, 43, 44, 45, 46)    # S1: member seeds
    base: ReconConfig = field(default_factory=ReconConfig)

    def __post_init__(self) -> None:
        if len(self.seeds) != self.members:
            raise ValueError("Number of seeds must equal members (S1 ensemble row).")

    def member_config(self, i: int) -> ReconConfig:
        """The i-th member's config (same hyperparameters, member-specific seed)."""
        from dataclasses import replace

        return replace(self.base, seed=self.seeds[i])
