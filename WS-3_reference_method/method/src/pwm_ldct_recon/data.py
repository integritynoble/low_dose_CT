"""Training/eval data: (low, full) HU->[0,1] slice pairs over the WS-1 loader.

``PairedSlices`` wraps ``pwm_ldct_loader.LowDoseCTDataset`` exactly as the WS-1 baseline
harness does (same HU window, same normalisation), so the two repos train on an identical
data contract. ``SyntheticPairs`` is an in-memory stand-in with no HDF5 dependency, used by
the CPU test suite and as a smoke-test fixture for the pipeline.

Measurement model. The unrolled net reconstructs from a *sinogram*; the per-slice loader
sample exposes images, not projections (projections are series-level). The training loop
therefore forms the measurement as ``y = RadonTransform.forward(low_dose)`` -- the low-dose
image's forward projection -- which is the scaffold's stand-in until real low-dose sinograms
are wired via ``LowDoseCTDataset.get_series_projections``.
"""
from __future__ import annotations

from typing import Optional, Sequence

import numpy as np
import torch
from torch.utils.data import Dataset

HU_MIN, HU_MAX = -1024.0, 3072.0


def normalize(a: np.ndarray) -> np.ndarray:
    return np.clip((a - HU_MIN) / (HU_MAX - HU_MIN), 0.0, 1.0).astype(np.float32)


def denormalize(a: np.ndarray | torch.Tensor):
    return a * (HU_MAX - HU_MIN) + HU_MIN


class PairedSlices(Dataset):
    """(low, full) ``[1,H,W]`` tensors in [0,1] over the harmonized WS-1 tree."""

    def __init__(self, root: str, split: str, dose_ratio: float = 0.25,
                 prefer_real_ld: bool = True, sources: Optional[Sequence[str]] = None,
                 seed: int = 42):
        from pwm_ldct_loader import LowDoseCTDataset

        self.ds = LowDoseCTDataset(root=root, split=split, dose_ratio=dose_ratio,
                                   prefer_real_ld=prefer_real_ld, sources=sources,
                                   seed=seed, backend="numpy")

    def __len__(self) -> int:
        return len(self.ds)

    def __getitem__(self, i: int):
        s = self.ds[i]
        low = torch.from_numpy(normalize(s["low_dose"])).unsqueeze(0)
        full = torch.from_numpy(normalize(s["full_dose"])).unsqueeze(0)
        return low, full, float(s["dose_ratio"]), s["source"], (s["low_dose_kind"] or "")


class SyntheticPairs(Dataset):
    """In-memory phantom pairs (no HDF5): smooth full-dose image + noisier low-dose.

    Deterministic given ``seed``. Pixel values already in [0,1]. For tests and pipeline
    smoke-runs only -- NOT scientific data.
    """

    def __init__(self, n: int = 8, size: int = 32, dose_ratio: float = 0.25, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.size = size
        self.dose_ratio = float(dose_ratio)
        yy, xx = np.mgrid[0:size, 0:size].astype(np.float32) / size
        self.full, self.low = [], []
        for _ in range(n):
            cx, cy, r = rng.uniform(0.3, 0.7, 3)
            disk = ((xx - cx) ** 2 + (yy - cy) ** 2 < (0.15 + 0.1 * r) ** 2).astype(np.float32)
            base = 0.3 + 0.4 * disk + 0.05 * np.sin(8 * xx)
            base = np.clip(base, 0.0, 1.0).astype(np.float32)
            noise = rng.normal(0.0, 0.05 / max(self.dose_ratio, 1e-3), (size, size)).astype(np.float32)
            self.full.append(base)
            self.low.append(np.clip(base + noise, 0.0, 1.0).astype(np.float32))

    def __len__(self) -> int:
        return len(self.full)

    def __getitem__(self, i: int):
        low = torch.from_numpy(self.low[i]).unsqueeze(0)
        full = torch.from_numpy(self.full[i]).unsqueeze(0)
        return low, full, self.dose_ratio, "synthetic", "simulated"
