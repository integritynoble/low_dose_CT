"""Train one ensemble member: seeded unrolled reconstruction (Table S1 optimisation).

AdamW + cosine schedule with 5% linear warmup, L1 reconstruction loss on HU-normalised
images, measurement formed as ``y = R(low_dose)`` (see data.py measurement-model note).
One call trains one independently-seeded member; the ensemble (ensemble.py) calls it M times.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

from .config import ReconConfig
from .physics import RadonTransform
from .models import UNetDenoiser, UnrolledRecon


def seed_everything(seed: int) -> None:
    """Seed all RNG streams and pin the determinism knobs from Supplementary Table S2.

    Mirrors the reproducibility contract stated in the manuscript (Table S2) and the
    WS-3 per-baseline checklist: seeded ``random`` / NumPy / torch (CPU+CUDA) plus
    ``cudnn.deterministic=True`` / ``cudnn.benchmark=False``. The CuDNN flags are
    inert on CPU-only builds, so this is CI-safe.

    Note: ``torch.use_deterministic_algorithms(True)`` is intentionally NOT set
    globally -- it routes the differentiable ``grid_sample`` in the Radon warm-start
    through ``grid_sampler_2d_backward``, which lacks the derivative that path needs
    and aborts training. Determinism here rests on full seeding plus the CuDNN flags;
    Table S2 records this exception.
    """
    import random

    import numpy as np

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():  # pragma: no cover - no GPU in CI
        torch.cuda.manual_seed_all(seed)

    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def _lr_factor(step: int, total: int, warmup_frac: float) -> float:
    """Cosine schedule with linear warmup (Table S1)."""
    warmup = max(1, int(total * warmup_frac))
    if step < warmup:
        return step / warmup
    prog = (step - warmup) / max(1, total - warmup)
    return 0.5 * (1.0 + math.cos(math.pi * min(prog, 1.0)))


@dataclass
class TrainResult:
    model: UnrolledRecon
    final_loss: float
    steps: int


def build_model(cfg: ReconConfig, device: str = "cpu", estimate_step: bool = True) -> UnrolledRecon:
    physics = RadonTransform(n_views=cfg.n_views, n_dets=cfg.n_dets,
                             img_size=cfg.slice_size, filter_name=cfg.fbp_filter)
    model = UnrolledRecon(physics, UNetDenoiser(channels=cfg.unet_channels), cfg,
                          estimate_step=estimate_step)
    return model.to(device)


def train_member(cfg: ReconConfig, dataset: Dataset, *, device: str = "cpu",
                 max_steps: Optional[int] = None, model: Optional[UnrolledRecon] = None,
                 estimate_step: bool = True, log_every: int = 0) -> TrainResult:
    """Train (or continue) one member; returns the model + final loss."""
    seed_everything(cfg.seed)
    if model is None:
        model = build_model(cfg, device=device, estimate_step=estimate_step)
    model.train()
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.peak_lr, weight_decay=cfg.weight_decay)

    loader = DataLoader(dataset, batch_size=cfg.batch_size, shuffle=True, drop_last=False,
                        generator=torch.Generator().manual_seed(cfg.seed))
    steps_per_epoch = max(1, len(loader))
    total = max_steps if max_steps is not None else cfg.epochs * steps_per_epoch

    step, last = 0, float("nan")
    done = False
    while not done:
        for low, full, *_ in loader:
            low, full = low.to(device), full.to(device)
            y = model.physics.forward(low)            # measurement surrogate
            recon = model(y)
            loss = F.l1_loss(recon, full) if cfg.recon_loss == "l1" else F.mse_loss(recon, full)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            # step+1 so the first update gets a non-zero warmup LR (not 0/warmup).
            for g in opt.param_groups:
                g["lr"] = cfg.peak_lr * _lr_factor(step + 1, total, cfg.warmup_frac)
            opt.step()
            last = float(loss.detach())
            step += 1
            if log_every and step % log_every == 0:
                print(f"[seed {cfg.seed}] step {step}/{total} loss {last:.4f}")
            if step >= total:
                done = True
                break
    return TrainResult(model=model, final_loss=last, steps=step)
