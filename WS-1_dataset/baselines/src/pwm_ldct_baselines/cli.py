"""CLI: ``python -m pwm_ldct_baselines {train,eval}`` (manuscript Usage Notes)."""
from __future__ import annotations

import argparse
from typing import List, Optional

from .eval import evaluate_to_json
from .models import available_models
from .train import train


def _sources(v):
    return v.split(",") if v else None


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

    ev = sub.add_parser("eval", help="evaluate a checkpoint -> results.json (PSNR/SSIM/LPIPS per dose)")
    ev.add_argument("--dataset", required=True)
    ev.add_argument("--checkpoint", required=True)
    ev.add_argument("--split", default="test")
    ev.add_argument("--out", required=True, help="results.json path")
    ev.add_argument("--sources", default=None)
    ev.add_argument("--seed", type=int, default=42)
    ev.add_argument("--device", default=None)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "train":
        train(args.dataset, args.out, model_name=args.model, split=args.split, epochs=args.epochs,
              lr=args.lr, batch_size=args.batch_size, max_steps=args.max_steps,
              sources=_sources(args.sources), seed=args.seed, device=args.device)
    else:
        evaluate_to_json(args.dataset, args.checkpoint, args.out, split=args.split,
                         sources=_sources(args.sources), seed=args.seed, device=args.device)
    return 0
