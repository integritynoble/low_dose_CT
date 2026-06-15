"""Synthetic end-to-end demo shared by ``pwm-recon smoke`` and the RunBundle self-test.

Builds a tiny deep ensemble + two synthetic scans, emits a corpus (reference method + an
FBP baseline), runs the full deposit pipeline, and computes a small validation block. It
proves the whole Phase-3 pipeline executes with **no GPU and no Phase-3 data** -- it is NOT
scientific data (pixels are phantoms, credential scores are synthetic).
"""
from __future__ import annotations

from pathlib import Path
from typing import List

import numpy as np
import torch

from . import emit_corpus as ec
from .config import EnsembleConfig, ReconConfig
from .data import SyntheticPairs, denormalize
from .detector import DeterministicStubDetector
from .ensemble import ensemble_infer, train_ensemble
from .metrics import psnr, spearman, ssim

VENDORS = ("Siemens", "GE")


def _demo_config(size: int, members: int) -> EnsembleConfig:
    base = ReconConfig(n_views=24, n_dets=size, slice_size=size, iterations=2,
                       unet_channels=(8, 16), batch_size=2, doses=(0.10, 0.25, 0.50),
                       dose_mix_weights=(0.4, 0.4, 0.2))
    seeds = tuple(42 + i for i in range(members))
    return EnsembleConfig(members=members, seeds=seeds, base=base)


def _scans(ds: SyntheticPairs) -> List[ec.ScanInput]:
    rng = np.random.default_rng(0)
    scans = []
    for vi, vendor in enumerate(VENDORS):
        ref = denormalize(ds.full[vi]).astype("f4")[None]
        low = {r: denormalize(np.clip(ds.full[vi] + rng.normal(0, 0.05 / r, ds.full[vi].shape),
                                      0, 1)).astype("f4")[None] for r in (0.10, 0.25, 0.50)}
        scans.append(ec.ScanInput(scan_id=f"scan_{vendor.lower()}_chest", vendor=vendor,
                                  patient_id=f"p{vi + 1:03d}", full_dose=ref, low_dose=low))
    return scans


def _auc(rng, lift):
    from emit_credentials import AucScores  # sibling tool, path-loaded by emit_corpus.run

    n = 60
    return AucScores(a_pos=rng.normal(0.55 + lift, 0.18, n), a_neg=rng.normal(0.45 - lift, 0.18, n),
                     b_pos=rng.normal(0.65, 0.18, n), b_neg=rng.normal(0.35, 0.18, n))


def _scores_fn():
    rng = np.random.default_rng(7)
    return lambda vendor, anatomy, r: _auc(rng, 0.10)        # reference method


def _baseline_scores_fn():
    rng = np.random.default_rng(11)
    return lambda method, vendor, anatomy, r: _auc(rng, 0.05)  # baseline


@torch.no_grad()
def _validation(models, ds: SyntheticPairs) -> dict:
    """Reconstruct the synthetic pairs and report fidelity + UQ tracking (structure, not science)."""
    low = torch.from_numpy(np.stack(ds.low)).unsqueeze(1)
    full = torch.from_numpy(np.stack(ds.full)).unsqueeze(1)
    res = ensemble_infer(models, models[0].physics.forward(low))
    err = (res.mean - full).abs()
    return {"psnr_db": round(psnr(res.mean, full), 3),
            "ssim": round(ssim(res.mean, full), 4),
            "uq_spearman": round(spearman(res.sigma, err), 4)}


def run_demo(out_dir: Path | str, *, size: int = 32, steps: int = 4, members: int = 2) -> dict:
    """Train -> emit (with FBP baseline) -> deposit-verify -> validate. Returns a report dict."""
    cfg = _demo_config(size, members)
    ds = SyntheticPairs(n=6, size=size, seed=0)
    models = train_ensemble(cfg, ds, max_steps=steps, estimate_step=False)
    report = ec.run(out_dir, _scans(ds), models, DeterministicStubDetector(), _scores_fn(),
                    cfg=cfg, baselines=[ec.FBPBaseline(models[0].physics)],
                    baseline_scores_fn=_baseline_scores_fn())
    report["validation"] = _validation(models, ds)
    report["mode"] = "self-test (synthetic; not scientific data)"
    return report


def demo_ok(report: dict) -> bool:
    return bool(report["credentials_ok"] and report["manifest_ok"]
               and report["error_maps_ok"] and not report["schema_errors"])
