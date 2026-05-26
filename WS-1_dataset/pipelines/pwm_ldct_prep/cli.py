"""CLI: ``python -m pwm_ldct_prep {prep,finalize,validate}``.

Each Dockerfile bakes its source via the ``PWM_LDCT_SOURCE`` env var (the default for --source).
Typical flow: run ``prep`` once per source into a shared --output tree, then ``finalize`` once to
write splits + manifest, then ``validate``.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import sys
from typing import List, Optional

import pydicom

from pwm_ldct_loader.schema import DOSE_RATIOS
from pwm_ldct_loader.splits import assign_split

from . import lowdose_sim
from .adapters import get_adapter
from .deident import audit_row
from .harmonize import build_metadata
from .writers import (append_audit, write_manifest, write_metadata, write_series_hdf5,
                      write_splits)


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def cmd_prep(args) -> int:
    adapter = get_adapter(args.source)
    sim_model = lowdose_sim.model_name()
    n_done = 0
    for ps in adapter.iter_patients(args.input, subset=args.subset):
        fd = ps.fd
        n_slices = int(fd.volume_hu.shape[0])
        meta = build_metadata(fd, sim_model=sim_model, seed=args.seed, n_slices=n_slices)
        split = assign_split(fd.patient_id, args.seed)
        sims = {}
        if not args.no_sim:
            sims = {r: lowdose_sim.simulate(fd.volume_hu, r, args.seed, args.source) for r in DOSE_RATIOS}
        meta_sha = write_metadata(args.output, meta)
        write_series_hdf5(args.output, fd, sims, split, meta_sha, real_ld=ps.ld)
        append_audit(args.output, audit_row(
            scan_uid=meta["scan_uid"], source=args.source,
            stage1={"note": "extraction is whitelist-based; see dicom_cleaning_spec.md"},
            ocr_hits=[], tool_versions={"pydicom": pydicom.__version__}, timestamp_utc=_now(),
        ))
        n_done += 1
        print(f"[{args.source}] {fd.series_id}  split={split}  slices={n_slices}"
              f"  real_ld={ps.ld is not None}  sims={len(sims)}")
    print(f"prep done: {n_done} patient(s) from {args.input} -> {args.output}")
    return 0


def cmd_finalize(args) -> int:
    splits = write_splits(args.output)
    manifest = write_manifest(args.output)
    print(f"splits: " + ", ".join(f"{k}={len(v)}" for k, v in splits.items()))
    print(f"manifest written: {manifest}")
    return 0


def cmd_validate(args) -> int:
    from pwm_ldct_loader import validate
    rep = validate(args.output)
    print(f"series={rep.n_series} patients={rep.n_patients} ok={rep.ok}")
    for w in rep.warnings:
        print(f"  warning: {w}")
    for e in rep.errors:
        print(f"  ERROR: {e}")
    return 0 if rep.ok else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pwm_ldct_prep",
                                description="Build the harmonized PWM-LDCT v0.5 tree from raw DICOM.")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("prep", help="harmonize one source's raw DICOM into the output tree")
    pr.add_argument("--source", default=os.environ.get("PWM_LDCT_SOURCE"),
                    choices=["lidc", "aapm", "mayo"], help="source dataset (or PWM_LDCT_SOURCE env)")
    pr.add_argument("--input", required=True, help="raw DICOM root for this source")
    pr.add_argument("--output", required=True, help="shared harmonized output tree")
    pr.add_argument("--seed", type=int, default=42)
    pr.add_argument("--subset", type=int, default=None, help="limit to first N patients")
    pr.add_argument("--no-sim", action="store_true", help="skip low-dose simulation")
    pr.set_defaults(func=cmd_prep)

    fi = sub.add_parser("finalize", help="write splits + manifest over the combined output tree")
    fi.add_argument("--output", required=True)
    fi.set_defaults(func=cmd_finalize)

    va = sub.add_parser("validate", help="run pwm_ldct_loader.validate on the output tree")
    va.add_argument("--output", required=True)
    va.set_defaults(func=cmd_validate)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if getattr(args, "cmd", None) == "prep" and not args.source:
        print("error: --source is required (or set PWM_LDCT_SOURCE)", file=sys.stderr)
        return 2
    return args.func(args)
