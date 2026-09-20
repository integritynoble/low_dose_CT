"""Torch Dataset over pwm_ldct_loader: yields (low_dose, full_dose) pairs normalized HU -> [0,1]."""
from __future__ import annotations

from typing import Optional, Sequence

import numpy as np
import torch
from torch.utils.data import Dataset

from pwm_ldct_loader import LowDoseCTDataset

HU_MIN, HU_MAX = -1024.0, 3072.0


def normalize(a: np.ndarray) -> np.ndarray:
    return np.clip((a - HU_MIN) / (HU_MAX - HU_MIN), 0.0, 1.0).astype(np.float32)


def denormalize(a: np.ndarray) -> np.ndarray:
    return a * (HU_MAX - HU_MIN) + HU_MIN


class PairedSlices(Dataset):
    """(low, full) single-channel [1,H,W] tensors in [0,1], plus dose_ratio / source / kind / patient_id.

    ``__getitem__`` returns a 6-tuple ``(low, full, dose_ratio, source, kind,
    patient_id)``.  The trailing ``patient_id`` (a str, unique per subject in the
    harmonized tree) is threaded through from ``pwm_ldct_loader.LowDoseCTDataset``
    so downstream per-slice outputs (eval.py per_slice blocks, patient-level
    bootstrap) can group slices by patient.  Existing consumers that unpack
    ``for low, full, *_ in loader`` keep working unchanged.
    """

    def __init__(self, root: str, split: str, dose_ratio: float = 0.25, prefer_real_ld: bool = True,
                 sources: Optional[Sequence[str]] = None, seed: int = 42):
        self.ds = LowDoseCTDataset(root=root, split=split, dose_ratio=dose_ratio,
                                   prefer_real_ld=prefer_real_ld, sources=sources, seed=seed,
                                   backend="numpy", return_sinogram=False)

    def __len__(self) -> int:
        return len(self.ds)

    def __getitem__(self, i: int):
        s = self.ds[i]
        low = torch.from_numpy(normalize(s["low_dose"])).unsqueeze(0)
        full = torch.from_numpy(normalize(s["full_dose"])).unsqueeze(0)
        return (low, full, float(s["dose_ratio"]), s["source"],
                (s["low_dose_kind"] or ""), s["patient_id"])
