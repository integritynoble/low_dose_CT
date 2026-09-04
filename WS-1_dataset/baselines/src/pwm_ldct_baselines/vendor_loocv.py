"""Leave-one-vendor-out spread report (Rung 6 / companion charter 3.3, 5).

Standing measurement: for the four vendors (GE / Siemens / Philips / Toshiba) the
evaluation reports BOTH fidelity (PSNR) and task-based detectability (CNR) per fold
(leave-one-vendor-out), and the *spread* across folds (mean / std / min / max) is the
cross-vendor generalization statement — never a vendor-averaged single number that
hides the spread.

This module is the runnable entrypoint for that measurement:

- ``vendor_loocv_folds(vendors)`` — fold plan (pure);
- ``compute_spread(values)`` — mean/std/min/max (pure);
- ``spread_report(fold_results)`` — aggregate per-dose fidelity + detectability
  spread from per-fold results (pure, unit-tested with synthetic data);
- CLI ``python -m pwm_ldct_baselines vendor-loocv`` — consume per-fold results JSON
  (``--results-glob``) or emit a synthetic demo (``--demo``) to show the report shape.

For v0.5 (LIDC-only, all vendors at full dose) no vendor-level low-dose folds exist
yet; the v1.0 roadmap adds real paired low-dose data per vendor. The tool is
therefore registered as a standing measurement and can be run as soon as per-fold
evaluation outputs exist.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from typing import Dict, List, Optional, Sequence

VENDORS = ("GE", "Siemens", "Philips", "Toshiba")
DOSE_ORDER = ("sim_r010", "sim_r025", "sim_r050")


def vendor_loocv_folds(vendors: Sequence[str] = VENDORS) -> List[Dict[str, object]]:
    """Fold plan: each vendor held out once, the rest used for training."""
    vs = list(vendors)
    return [{"held_out_vendor": v,
             "train_vendors": [w for w in vs if w != v]}
            for v in vs]


def compute_spread(values: Sequence[Optional[float]]) -> Dict[str, object]:
    """Mean / std / min / max over a fold series (std of a single value = 0.0)."""
    vals = [v for v in values if v is not None]
    n = len(vals)
    if n == 0:
        return {"n": 0, "mean": None, "std": None, "min": None, "max": None}
    mean = sum(vals) / n
    if n == 1:
        std = 0.0
    else:
        var = sum((v - mean) ** 2 for v in vals) / (n - 1)
        std = var ** 0.5
    return {"n": n, "mean": mean, "std": std, "min": min(vals), "max": max(vals)}


def spread_report(fold_results: Dict[str, Dict[str, object]],
                  doses: Sequence[str] = DOSE_ORDER) -> Dict[str, object]:
    """Aggregate per-dose fidelity+detectability spread across leave-one-vendor-out folds.

    Parameters
    ----------
    fold_results : {fold_label: {"vendor": str, "per_dose": {dose: {"psnr": float,
        "cnr": float}}}} — one dict per leave-one-out fold.

    Returns a report with per-dose spread for PSNR and CNR, plus the fold labels.
    """
    per_dose_psnr: Dict[str, List[Optional[float]]] = {d: [] for d in doses}
    per_dose_cnr: Dict[str, List[Optional[float]]] = {d: [] for d in doses}
    fold_vendors: List[str] = []
    for label, res in sorted(fold_results.items()):
        fold_vendors.append(str(res.get("vendor", label)))
        for d in doses:
            pd = res.get("per_dose", {}).get(d, {}) or {}
            per_dose_psnr[d].append(pd.get("psnr"))
            per_dose_cnr[d].append(pd.get("cnr"))
    return {
        "measurement": "leave-one-vendor-out",
        "folds": [{"label": k, "vendor": str(v.get("vendor", k))}
                  for k, v in sorted(fold_results.items())],
        "per_dose": {
            d: {"psnr_spread": compute_spread(per_dose_psnr[d]),
                "cnr_spread": compute_spread(per_dose_cnr[d])}
            for d in doses
        },
        "report_rule": "fidelity and detectability are reported together per fold; "
                       "the spread (mean/std/min/max across folds) is the cross-vendor "
                       "generalization statement (never a vendor-averaged single number).",
    }


def _demo_fold(vendor: str, seed: int) -> Dict[str, object]:
    import random
    rng = random.Random(seed)
    return {
        "vendor": vendor,
        "per_dose": {
            d: {"psnr": round(rng.uniform(47.0, 52.0), 2),
                "cnr": round(rng.uniform(1.5, 4.5), 2)}
            for d in DOSE_ORDER
        },
    }


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="vendor-loocv",
        description="Leave-one-vendor-out fidelity+detectability spread report (Rung 6).")
    p.add_argument("--results-glob", default=None,
                   help="glob pattern for per-fold results JSON files "
                        "({vendor}_{dose}_results_det.json style, each with per_dose psnr/cnr)")
    p.add_argument("--out", required=True, help="output JSON report path")
    p.add_argument("--demo", action="store_true",
                   help="emit a synthetic demo report (no real per-vendor folds yet)")
    args = p.parse_args(argv)

    if args.demo:
        folds = {v: _demo_fold(v, i) for i, v in enumerate(VENDORS)}
    elif args.results_glob:
        folds: Dict[str, Dict[str, object]] = {}
        for path in sorted(glob.glob(args.results_glob)):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            label = os.path.basename(path).replace("_results_det.json", "")
            folds[label] = {
                "vendor": data.get("vendor", label),
                "per_dose": {d: {"psnr": data.get("per_dose", {}).get(d, {}).get("psnr"),
                                 "cnr": data.get("per_dose", {}).get(d, {}).get("detectability", {}).get("cnr_mean")}
                             for d in DOSE_ORDER},
            }
    else:
        p.error("provide --results-glob or --demo")
        return 2

    report = spread_report(folds)
    report["vendors"] = list(VENDORS)
    report["note"] = ("v0.5 is LIDC-only with simulated dose (all vendors at full dose); "
                      "per-vendor low-dose folds arrive with the v1.0 real paired data. "
                      "This tool is the standing measurement entrypoint.")
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
