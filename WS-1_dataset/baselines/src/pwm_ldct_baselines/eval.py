"""Evaluate a trained baseline on a split: PSNR/SSIM/(LPIPS) per dose level -> results.json.

Reports simulated dose levels (r in {0.10, 0.25, 0.50}) and the real low-dose subset separately
(manuscript Technical Validation, Table tab:baselines_v05). Role is evidence the unified loader +
checkpoint reproduce numbers bit-identically on equivalent hardware -- not a method ranking.
"""
from __future__ import annotations

import json
from typing import Optional, Sequence

import torch
from torch.utils.data import DataLoader

from pwm_ldct_loader import seed_everything

from . import metrics as M
from .data import PairedSlices
from .models import get_model

DOSE_RATIOS = (0.10, 0.25, 0.50)


def _device(name):
    return name or ("cuda" if torch.cuda.is_available() else "cpu")


def _eval_loader(model, ds, dev, only_real=False) -> dict:
    loader = DataLoader(ds, batch_size=1, shuffle=False, num_workers=0)
    ps, ss, lp, n = 0.0, 0.0, 0.0, 0
    lp_n = 0
    with torch.no_grad():
        for low, full, _ratio, _src, kind in loader:
            if only_real and kind[0] != "real":
                continue
            low, full = low.to(dev), full.to(dev)
            out = model(low).clamp(0, 1)
            ps += M.psnr(out, full)
            ss += M.ssim(out, full)
            lv = M.lpips(out, full)
            if lv is not None:
                lp += lv
                lp_n += 1
            n += 1
    if n == 0:
        return {"psnr": None, "ssim": None, "lpips": None, "n": 0}
    return {"psnr": ps / n, "ssim": ss / n,
            "lpips": (lp / lp_n) if lp_n else None, "n": n}


def evaluate(root: str, ckpt: str, split: str = "test", seed: int = 42,
             sources: Optional[Sequence[str]] = None, device: Optional[str] = None) -> dict:
    seed_everything(seed)
    dev = _device(device)
    state = torch.load(ckpt, map_location=dev)
    model = get_model(state["model"]).to(dev)
    model.load_state_dict(state["state_dict"])
    model.eval()

    results = {"model": state["model"], "split": split, "seed": seed, "per_dose": {}}
    for r in DOSE_RATIOS:
        ds = PairedSlices(root, split, dose_ratio=r, prefer_real_ld=False, sources=sources, seed=seed)
        results["per_dose"][f"sim_r{int(r * 100):03d}"] = _eval_loader(model, ds, dev)
    ds_real = PairedSlices(root, split, prefer_real_ld=True, sources=sources, seed=seed)
    results["per_dose"]["real"] = _eval_loader(model, ds_real, dev, only_real=True)
    return results


def evaluate_to_json(root, ckpt, out_path, **kw) -> dict:
    res = evaluate(root, ckpt, **kw)
    with open(out_path, "w") as f:
        json.dump(res, f, indent=2)
    print(f"wrote {out_path}", flush=True)
    return res
