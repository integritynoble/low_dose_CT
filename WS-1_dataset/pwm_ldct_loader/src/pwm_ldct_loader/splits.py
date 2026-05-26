"""Deterministic patient-level split assignment (dataset_schema.md §7).

The deposited ``splits/*.txt`` files are authoritative (they include the post-pass that
guarantees every (source, anatomy) stratum is represented). ``assign_split`` reproduces the
base deterministic bucketing and is used as a fallback when no split files are present.
"""
from __future__ import annotations

import hashlib
import os
from typing import Dict, List


def _bucket(patient_id: str, seed: int) -> int:
    h = hashlib.sha256(f"{seed}:{patient_id}".encode()).hexdigest()
    return int(h, 16) % 100


def assign_split(patient_id: str, seed: int = 42) -> str:
    """Base deterministic split for a patient: <60 train, <80 val, else test."""
    b = _bucket(patient_id, seed)
    if b < 60:
        return "train"
    if b < 80:
        return "val"
    return "test"


def read_splits(root: str) -> Dict[str, List[str]]:
    """Read the authoritative ``splits/{train,val,test}.txt`` (one patient_id per line)."""
    out: Dict[str, List[str]] = {}
    sdir = os.path.join(root, "splits")
    for name in ("train", "val", "test"):
        p = os.path.join(sdir, f"{name}.txt")
        if os.path.exists(p):
            with open(p) as f:
                out[name] = [line.strip() for line in f if line.strip()]
        else:
            out[name] = []
    return out
