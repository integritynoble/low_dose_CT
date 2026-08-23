"""CLI: ``python -m pwm_ldct_baselines {train,eval,dose-curve,vendor-loocv}`` (manuscript Usage Notes)."""
from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

from .dose_curve import build_curve
from .eval import FIXED_SEED_SET, evaluate_seed_set, evaluate_to_json
from .models import available_models
from .observers import TaskSpec
from .train import train


def _sources(v):
    return v.split(",") if v else None


def _add_task_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--task-contrast-hu", type=float, default=TaskSpec.peak_contrast_hu,
                   help="declared lesion peak contrast in HU (task specification, Rung 1.1)")
    p.add_argument("--task-sigma-px", type=float, default=TaskSpec.signal_sigma_px,
                   help="declared lesion Gaussian sigma in pixels")
    p.add_argument("--task-label", default=TaskSpec.label,
                   help="human-readable task label written into results JSON")


def _build_task(args) -> TaskSpec:
    return TaskSpec(peak_contrast_hu=args.task_contrast_hu,
                    signal_sigma_px=args.task_sigma_px,
                    label=args.task_label)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pwm_ldct_baselines",
                                description="Train / evaluate reconstruction baselines on PWM-LDCT v0.5.")
    sub = p.add_subparsers(dest="cmd", required=True)

    tr = sub.add_parser("train", help="train a baseline (low-dose -> full-dose)")
    tr.add_argument("--dataset", required=True, help="harmonized PWM-LDCT v0.5 tree")
    tr.add_argument("--out", required=True, help="output checkpoint path (.pt)")
    tr.add_argument("--model", default="red_cnn", help=f"one of {available_models()}")
    tr.add_argument("--split", default="train")
    tr.add_argument("--epochs", type=int, default=1)
    tr.add_argument("--lr", type=float, default=1e-4)
    tr.add_argument("--batch-size", type=int, default=1)
    tr.add_argument("--max-steps", type=int, default=None)
    tr.add_argument("--sources", default=None, help="comma list, e.g. mayo,aapm")
    tr.add_argument("--seed", type=int, default=42)
    tr.add_argument("--device", default=None)

    ev = sub.add_parser("eval", help="evaluate a checkpoint -> results.json (PSNR/SSIM/LPIPS + detectability per dose)")
    ev.add_argument("--dataset", required=True)
    ev.add_argument("--checkpoint", required=True,
                    help="checkpoint .pt path, or the literal 'blur' for the standing Gaussian-blur trap")
    ev.add_argument("--split", default="test")
    ev.add_argument("--out", required=True, help="results.json path")
    ev.add_argument("--sources", default=None)
    ev.add_argument("--seed", type=int, default=42)
    ev.add_argument("--seeds", default=None,
                    help="comma list of seeds for the fixed-seed-set evaluation (§7.3); when set, "
                         "`--out` is the aggregate JSON path and mean+interval are reported")
    ev.add_argument("--device", default=None)
    ev.add_argument("--no-detectability", action="store_true",
                    help="skip the task-based detectability pass (fidelity only)")
    ev.add_argument("--det-trials", type=int, default=None,
                    help="override observer trial count (default: TaskSpec.n_trials=64)")
    _add_task_args(ev)

    dc = sub.add_parser("dose-curve", help="build the dose-detectability curve from *_results_det.json (Rung 4)")
    dc.add_argument("--results-dir", default=None,
                    help="directory with *_results_det.json (default: baselines/results)")
    dc.add_argument("--out-png", default=None,
                    help="output curve PNG path (default: output/dose_detectability_curve.png)")
    dc.add_argument("--out-json", default=None,
                    help="output statistics JSON path (default: output/dose_detectability_stats.json)")

    vl = sub.add_parser("vendor-loocv",
                        help="leave-one-vendor-out fidelity+detectability spread report (Rung 6)")
    vl.add_argument("--results-glob", default=None,
                    help="glob pattern for per-fold results JSON files")
    vl.add_argument("--out", required=True, help="output JSON report path")
    vl.add_argument("--demo", action="store_true",
                    help="emit a synthetic demo report (no real per-vendor folds yet)")

    dp = sub.add_parser("dicom-pairing",
                        help="DICOM geometric pairing check by ImagePositionPatient (Rung 2)")
    dp.add_argument("--fd-dir", required=True, help="full-dose DICOM series directory")
    dp.add_argument("--ld-dir", required=True, help="low-dose DICOM series directory")
    dp.add_argument("--out", required=True, help="output JSON report path")
    dp.add_argument("--tol-mm", type=float, default=None,
                    help="along-axis tolerance in mm (default: 0.5)")
    dp.add_argument("--min-correlation", type=float, default=None,
                    help="target Pearson correlation threshold (default: 0.99)")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "train":
        train(args.dataset, args.out, model_name=args.model, split=args.split, epochs=args.epochs,
              lr=args.lr, batch_size=args.batch_size, max_steps=args.max_steps,
              sources=_sources(args.sources), seed=args.seed, device=args.device)
    elif args.cmd == "dose-curve":
        _pkg = os.path.dirname(os.path.abspath(__file__))
        results_dir = args.results_dir or os.path.join(_pkg, "..", "..", "results")
        out_png = args.out_png or os.path.join(_pkg, "..", "..", "..", "output", "dose_detectability_curve.png")
        out_json = args.out_json or os.path.join(_pkg, "..", "..", "..", "output", "dose_detectability_stats.json")
        build_curve(results_dir, out_png, out_json)
    elif args.cmd == "vendor-loocv":
        from .vendor_loocv import main as _vl_main
        return _vl_main(sys.argv[2:])  # skip program name and subcommand
    elif args.cmd == "dicom-pairing":
        from .dicom_pairing import main as _dp_main
        return _dp_main(sys.argv[2:])  # skip program name and subcommand
    else:
        task = _build_task(args) if not args.no_detectability else None
        kw = dict(split=args.split, sources=_sources(args.sources), device=args.device,
                  task=task, detectability=not args.no_detectability,
                  det_n_trials=args.det_trials)
        if args.seeds:
            seeds = tuple(int(s) for s in args.seeds.split(",") if s.strip())
            evaluate_seed_set(args.dataset, args.checkpoint, args.out, seeds=seeds, **kw)
        else:
            evaluate_to_json(args.dataset, args.checkpoint, args.out, seed=args.seed, **kw)
    return 0