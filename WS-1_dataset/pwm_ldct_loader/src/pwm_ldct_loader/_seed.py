"""Deterministic seeding (dataset_schema.md §4.1; manuscript Usage Notes).

Pins Python, NumPy, and — if installed — PyTorch / CUDA RNGs, and selects deterministic
CuDNN. torch is optional; absence is not an error.
"""
from __future__ import annotations

import os
import random

import numpy as np


def seed_everything(seed: int = 42) -> int:
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
    except ImportError:
        return seed
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    try:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    except Exception:  # pragma: no cover - platform dependent
        pass
    return seed
