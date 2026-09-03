"""Evaluate a trained baseline on a split: PSNR/SSIM/(LPIPS) + task-based detectability per dose level -> results.json.

Reports simulated dose levels (r in {0.10, 0.25, 0.50}) and the real low-dose subset separately
(manuscript Technical Validation, Table tab:baselines_v05). Role is evidence the unified loader +
checkpoint reproduce numbers bit-identically on equivalent hardware -- not a method ranking.

Detectability (Rung 1 / §4): per dose level the same slices are scored with a declared task
specification and a stated observer (CNR + channelized Hotelling observer AUC, see observers.py).
The observer parameters and the task are fixed and written into the results JSON, so both numbers
appear together (a fidelity gain with flat detectability is a failure, not a mixed result).
"""
from __future__ import annotations

import json
from typing import Optional, Sequence

import torch
from torch.utils.data import DataLoader

from pwm_ldct_loader import seed_everything
from pwm_ldct_loader.schema import H5_LD_REAL

from . import metrics as M
from .data import PairedSlices
from .models import get_model
from .observers import TaskSpec, evaluate_detectability, run_model

DOSE_RATIOS = (0.10, 0.25, 0.50)
DEFAULT_TASK = TaskSpec()


def _device(name):
    return name or ("cuda" if torch.cuda.is_available() else "cpu")


def _eval_loader(model, ds, dev, only_real=False, task: Optional[TaskSpec] = None,
                 det_n_trials: Optional[int] = None, max_slices: Optional[int] = None,
                 only_real_scan_cap: Optional[int] = 2048) -> dict:
    """Fidelity (+ optional detectability) per slice.

    Returns the existing PSNR/SSIM/LPIPS keys and, when ``task`` is given,
    a ``detectability`` sub-dict with CNR / CHO AUC / NPWE aggregated over the
    evaluated slices (insertion protocol, see observers.model_detectability).

    ``max_slices`` caps the number of evaluated slices (deterministic prefix)
    so the observer protocol stays cheap while remaining identical across
    models and dose levels; the fidelity stats come from the same slices.
    """
    loader = DataLoader(ds, batch_size=1, shuffle=False, num_workers=0)
    ps, ss, lp, n = 0.0, 0.0, 0.0, 0
    lp_n = 0
    pvals: list = []   # per-slice PSNR (same order as lows / fulls)
    svals: list = []   # per-slice SSIM
    lvals: list = []   # per-slice LPIPS (None when the package is unavailable)
    lows: list = []
    fulls: list = []
    scanned = 0
    with torch.no_grad():
        for low, full, _ratio, _src, kind in loader:
            scanned += 1
            if only_real and kind[0] != "real":
                # real low-dose is absent in some trees (e.g. LIDC-only v0.5):
                # cap the scan so an empty real subset does not walk the whole split.
                if only_real_scan_cap is not None and scanned >= only_real_scan_cap:
                    break
                continue
            if max_slices is not None and n >= max_slices:
                break
            low, full = low.to(dev), full.to(dev)
            out = run_model(model, low).clamp(0, 1)
            _ps = M.psnr(out, full)
            _ss = M.ssim(out, full)
            ps += _ps
            ss += _ss
            pvals.append(float(_ps))
            svals.append(float(_ss))
            lv = M.lpips(out, full)
            lvals.append(float(lv) if lv is not None else None)
            if lv is not None:
                lp += lv
                lp_n += 1
            if task is not None:
                lows.append(low[0, 0].cpu().numpy())
                fulls.append(full[0, 0].cpu().numpy())
            n += 1
    if n == 0:
        res = {"psnr": None, "ssim": None, "lpips": None, "n": 0}
        if task is not None:
            res["detectability"] = None
        return res
    res = {"psnr": ps / n, "ssim": ss / n,
           "lpips": (lp / lp_n) if lp_n else None, "n": n}
    if task is not None and lows:
        det = evaluate_detectability(model, lows, fulls, task=task, device=dev,
                                     n_trials=det_n_trials)
        res["detectability"] = {
            "task": task.label,
            "signal_sigma_px": task.signal_sigma_px,
            "peak_contrast_hu": task.peak_contrast_hu,
            "location_known": task.location_known,
            "observer": {
                "cnr": {"rose_criterion": 3.0},
                "cho": {"channels": "DOG", "n_channels": 4},
                "npwe": {"eye_filter": "rho*exp(-rho/0.2)"},
            },
            "cnr_mean": det["cnr_mean"],
            "cnr_median": det["cnr_median"],
            "cnr_std": det["cnr_std"],
            "cho_auc_mean": det["cho_auc_mean"],
            "cho_auc_median": det["cho_auc_median"],
            "npwe_mean": det["npwe_mean"],
            "n_slices": det["n_slices"],
            "roi_pos": det["roi_pos"],
            # Per-slice detail (added for sample-level bootstrap; aggregates above unchanged):
            # cnr / cho_auc / npwe are per-slice observer results, psnr / ssim / lpips are
            # per-slice fidelity metrics over the same slices in the same order.
            "per_slice": {
                "psnr": pvals,
                "ssim": svals,
                "lpips": lvals,
                "cnr": det["cnr_values"],
                "cho_auc": det["cho_auc_values"],
                "npwe": det["npwe_values"],
            },
        }
    return res


def evaluate(root: str, ckpt: str, split: str = "test", seed: int = 42,
             sources: Optional[Sequence[str]] = None, device: Optional[str] = None,
             task: Optional[TaskSpec] = None,
             detectability: bool = True,
             det_n_trials: Optional[int] = None,
             max_slices: Optional[int] = None) -> dict:
    seed_everything(seed)
    dev = _device(device)

    # Blur trap: no checkpoint needed (fixed kernel); pass checkpoint="blur".
    blur_requested = str(ckpt).lower() in ("blur", "blur.pt") or str(ckpt).lower().endswith("blur.pt")
    if blur_requested:
        model = get_model("blur").to(dev)
        model.eval()
        model_name = "blur"
    else:
        state = torch.load(ckpt, map_location=dev)
        model = get_model(state["model"]).to(dev)
        model.load_state_dict(state["state_dict"])
        model.eval()
        model_name = state["model"]

    use_task = task if (detectability and task is not None) else None
    results = {"model": model_name, "split": split, "seed": seed, "per_dose": {},
               "task": (task.label if task is not None else None)}
    for r in DOSE_RATIOS:
        ds = PairedSlices(root, split, dose_ratio=r, prefer_real_ld=False, sources=sources, seed=seed)
        results["per_dose"][f"sim_r{int(r * 100):03d}"] = _eval_loader(model, ds, dev, task=use_task,
                                                                        det_n_trials=det_n_trials,
                                                                        max_slices=max_slices)
    ds_real = PairedSlices(root, split, prefer_real_ld=True, sources=sources, seed=seed)
    # Probe whether the tree actually contains real low-dose pairs (LIDC-only v0.5
    # does not). Empty real subset is reported as n=0 without walking the whole split.
    real_available = False
    import glob as _glob
    import os as _os
    for _f in _glob.glob(_os.path.join(root, "hdf5", split, "*", "*", "*.h5"))[:64]:
        try:
            import h5py as _h5
            with _h5.File(_f, "r") as _fh:
                if H5_LD_REAL in _fh:
                    real_available = True
                    break
        except Exception:
            continue
    results["per_dose"]["real"] = (
        _eval_loader(model, ds_real, dev, only_real=True, task=use_task,
                     det_n_trials=det_n_trials, max_slices=max_slices)
        if real_available else {"psnr": None, "ssim": None, "lpips": None, "n": 0,
                                "detectability": None, "real_available": False})
    return results


def evaluate_to_json(root, ckpt, out_path, **kw) -> dict:
    res = evaluate(root, ckpt, **kw)
    with open(out_path, "w") as f:
        json.dump(res, f, indent=2)
    print(f"wrote {out_path}", flush=True)
    return res


# Fixed seed set (§7.3 of the companion charter / RUN_PLAN): every reported evaluation
# must run over ALL seeds below and report the mean and the interval (min/max) of the
# per-seed results — a single-seed number is never the reported evaluation.
FIXED_SEED_SET = (42, 2023, 7, 12345, 999)


def evaluate_seed_set(root, ckpt, out_path, seeds=FIXED_SEED_SET, **kw) -> dict:
    """Run the evaluation over the fixed seed set and aggregate mean + interval.

    Writes a JSON with per-seed results plus an ``aggregate`` section: for every dose
    level and every metric (psnr / ssim / lpips / cnr_mean / cho_auc_mean) the mean,
    min and max across seeds are reported. The single-seed numbers are preserved so
    the full set can be inspected (fixed seed set rule, §7.3).
    """
    per_seed = {}
    for seed in seeds:
        res = evaluate(root, ckpt, seed=seed, **kw)
        per_seed[str(seed)] = res

    doses = list(res["per_dose"].keys())
    metrics = ("psnr", "ssim", "lpips", "cnr_mean", "cho_auc_mean")
    aggregate = {}
    for dose in doses:
        agg = {}
        for m in metrics:
            vals = []
            for seed in seeds:
                d = per_seed[str(seed)]["per_dose"].get(dose, {})
                v = (d.get("detectability") or {}).get(m) if m in ("cnr_mean", "cho_auc_mean") else d.get(m)
                if v is not None:
                    vals.append(float(v))
            if vals:
                n = len(vals)
                mean = sum(vals) / n
                agg[m] = {
                    "mean": mean,
                    "min": min(vals),
                    "max": max(vals),
                    "interval": [min(vals), max(vals)],
                    "n_seeds": n,
                }
        aggregate[dose] = agg

    report = {
        "model": res["model"],
        "split": res["split"],
        "fixed_seed_set": list(seeds),
        "rule": "all seeds reported; mean and interval (min/max) are the evaluation statement",
        "per_seed": per_seed,
        "aggregate": aggregate,
    }
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"wrote {out_path}", flush=True)
    return report