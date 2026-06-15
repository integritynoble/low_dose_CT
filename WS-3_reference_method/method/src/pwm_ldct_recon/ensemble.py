"""Deep ensemble: M independently-seeded members -> recon mean + per-pixel uncertainty.

UQ method (manuscript Architecture / Table S1): deep ensembles, M=5. The released
``recon_mean`` is the member mean; ``uncertainty_sigma`` is the per-pixel standard deviation
across members (ensemble disagreement) -- the corpus's distinctive paired (uncertainty, error)
signal. Single-model baselines carry no sigma (manuscript D4).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import torch
from torch.utils.data import Dataset

from .config import EnsembleConfig
from .models import UnrolledRecon
from .train import build_model, train_member


@dataclass
class EnsembleResult:
    mean: torch.Tensor   # [B,1,H,W]
    sigma: torch.Tensor  # [B,1,H,W] per-pixel std across members
    members: torch.Tensor  # [M,B,1,H,W] stacked per-member reconstructions


def train_ensemble(cfg: EnsembleConfig, dataset: Dataset, *, device: str = "cpu",
                   max_steps: Optional[int] = None, estimate_step: bool = True
                   ) -> List[UnrolledRecon]:
    """Train all M members (one per seed). Each is fully independent (weights + data order)."""
    models = []
    for i in range(cfg.members):
        res = train_member(cfg.member_config(i), dataset, device=device,
                           max_steps=max_steps, estimate_step=estimate_step)
        models.append(res.model)
    return models


@torch.no_grad()
def ensemble_infer(models: List[UnrolledRecon], y: torch.Tensor) -> EnsembleResult:
    """Reconstruct ``y`` with every member; return mean, per-pixel std, and the stack."""
    if not models:
        raise ValueError("empty ensemble")
    for m in models:
        m.eval()
    preds = torch.stack([m(y) for m in models], dim=0)  # [M,B,1,H,W]
    mean = preds.mean(dim=0)
    # population std (unbiased=False): with M=1 this is 0 rather than NaN.
    sigma = preds.std(dim=0, unbiased=False)
    return EnsembleResult(mean=mean, sigma=sigma, members=preds)


def save_ensemble(models: List[UnrolledRecon], path: str) -> None:
    torch.save([m.state_dict() for m in models], path)


def load_ensemble(cfg: EnsembleConfig, path: str, *, device: str = "cpu",
                  estimate_step: bool = False) -> List[UnrolledRecon]:
    states = torch.load(path, map_location=device)
    models = []
    for i, sd in enumerate(states):
        m = build_model(cfg.member_config(i), device=device, estimate_step=estimate_step)
        m.load_state_dict(sd)
        m.eval()
        models.append(m)
    return models
