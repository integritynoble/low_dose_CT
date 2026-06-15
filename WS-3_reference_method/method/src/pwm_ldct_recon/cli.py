"""Command-line entry: ``pwm-recon {info,smoke,train-ensemble,emit}``.

``info``           print the resolved Table-S1 config + model parameter count.
``smoke``          synthetic end-to-end (train tiny ensemble -> emit -> deposit-verify); no data.
``train-ensemble`` train M members on the WS-1 tree and save an ensemble checkpoint (data-gated).
``emit``           reconstruct a held-out split with a saved ensemble -> corpus (data-gated).

``smoke`` is the one-command reproduction that runs anywhere (CPU, no Phase-3 data); the other
two are the real Phase-3 commands and need the harmonized WS-1 HDF5 tree + the pinned detector.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import EnsembleConfig, ReconConfig


def _count_params(model) -> int:
    return sum(p.numel() for p in model.parameters())


def cmd_info(args: argparse.Namespace) -> int:
    from .train import build_model

    cfg = ReconConfig()
    model = build_model(cfg, estimate_step=False)
    info = {
        "version": __import__("pwm_ldct_recon").__version__,
        "iterations": cfg.iterations,
        "unet_channels": list(cfg.unet_channels),
        "denoiser_params": _count_params(model.denoiser),
        "total_params_per_member": _count_params(model),
        "ensemble_members": EnsembleConfig().members,
        "doses": list(cfg.doses),
    }
    print(json.dumps(info, indent=2))
    return 0


def cmd_smoke(args: argparse.Namespace) -> int:
    from .demo import demo_ok, run_demo

    report = run_demo(args.out, size=args.size, steps=args.steps)
    print(json.dumps(report, indent=2))
    return 0 if demo_ok(report) else 1


def cmd_train_ensemble(args: argparse.Namespace) -> int:
    from .data import PairedSlices
    from .ensemble import save_ensemble, train_ensemble

    cfg = EnsembleConfig()
    ds = PairedSlices(root=args.data_root, split="train", dose_ratio=args.dose)
    models = train_ensemble(cfg, ds, max_steps=args.max_steps)
    save_ensemble(models, args.out)
    print(json.dumps({"saved": args.out, "members": len(models)}, indent=2))
    return 0


def cmd_emit(args: argparse.Namespace) -> int:
    raise SystemExit(
        "emit: wire the held-out WS-1 split + pinned detector + cohort scores here at "
        "Phase-3 freeze time (see emit_corpus.run); `smoke` exercises the same path end-to-end."
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="pwm-recon", description="WS-3 reference recon method.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("info", help="print config + parameter counts").set_defaults(fn=cmd_info)

    s = sub.add_parser("smoke", help="synthetic end-to-end (no data)")
    s.add_argument("out", type=Path)
    s.add_argument("--size", type=int, default=32)
    s.add_argument("--steps", type=int, default=4)
    s.set_defaults(fn=cmd_smoke)

    t = sub.add_parser("train-ensemble", help="train M members on the WS-1 tree")
    t.add_argument("--data-root", required=True)
    t.add_argument("--out", required=True)
    t.add_argument("--dose", type=float, default=0.25)
    t.add_argument("--max-steps", type=int, default=None)
    t.set_defaults(fn=cmd_train_ensemble)

    e = sub.add_parser("emit", help="emit the corpus from a saved ensemble")
    e.set_defaults(fn=cmd_emit)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
