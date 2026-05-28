"""CLI: ``python -m pwm_ldct_prep {prep,finalize,validate}``.

Each Dockerfile bakes its source via the ``PWM_LDCT_SOURCE`` env var (the default for --source).
Typical flow: run ``prep`` once per source into a shared --output tree, then ``finalize`` once to
write splits + manifest, then ``validate``.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
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
from .writers import (append_audit, write_annotations, write_manifest, write_metadata,
                      write_series_hdf5, write_splits)


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def cmd_prep(args) -> int:
    adapter = get_adapter(args.source)
    if getattr(args, "with_sinograms", False):
        adapter.with_sinograms = True
    if getattr(args, "id_map", None):
        with open(args.id_map) as f:
            adapter.id_map = json.load(f)
    sim_model = lowdose_sim.model_name()
    n_done = 0
    for ps in adapter.iter_patients(args.input, subset=args.subset):
        fd = ps.fd
        n_slices = int(fd.volume_hu.shape[0])
        meta = build_metadata(fd, sim_model=sim_model, seed=args.seed, n_slices=n_slices)
        # split on the cross-source canonical patient key so a patient appearing in >1 source
        # (e.g. AAPM 2016 ⊂ Mayo LDCT-PD) lands in a single split (no train/test leakage)
        split = assign_split(fd.canonical_key or fd.patient_id, args.seed)
        sims = {}
        if not args.no_sim:
            sims = lowdose_sim.simulate_multi(fd.volume_hu, DOSE_RATIOS, args.seed)
        meta_sha = write_metadata(args.output, meta)
        write_series_hdf5(args.output, fd, sims, split, meta_sha, real_ld=ps.ld)
        write_annotations(args.output, fd.patient_id, fd.series_id, args.source, ps.annotations)
        append_audit(args.output, audit_row(
            scan_uid=meta["scan_uid"], source=args.source,
            stage1={"note": "extraction is whitelist-based; see dicom_cleaning_spec.md"},
            ocr_hits=[], tool_versions={"pydicom": pydicom.__version__}, timestamp_utc=_now(),
        ))
        n_done += 1
        n_nod = len(ps.annotations["majority"]) if ps.annotations else 0
        print(f"[{args.source}] {fd.series_id}  split={split}  slices={n_slices}"
              f"  real_ld={ps.ld is not None}  sims={len(sims)}  nodules={n_nod}")
    print(f"prep done: {n_done} patient(s) from {args.input} -> {args.output}")
    return 0


def cmd_stage(args) -> int:
    from .stage import stage_aapm
    patients = [p.strip() for p in args.patients.split(",")] if args.patients else None
    domains = [d.strip() for d in args.domains.split(",") if d.strip()]
    stage_aapm(args.work_dir, gcs_prefix=args.gcs_prefix, patients=patients, domains=domains)
    print(f"staged AAPM tree at {args.work_dir} — now run: "
          f"prep --source aapm --input {args.work_dir} --output <tree> [--with-sinograms]")
    return 0


def cmd_finalize(args) -> int:
    splits = write_splits(args.output)
    manifest = write_manifest(args.output)
    print(f"splits: " + ", ".join(f"{k}={len(v)}" for k, v in splits.items()))
    print(f"manifest written: {manifest}")
    return 0


def cmd_recon_sanity(args) -> int:
    from pwm_ldct_loader import LowDoseCTDataset

    from . import recon_sanity as rs
    checked = 0
    for split in ("train", "val", "test"):
        ds = LowDoseCTDataset(root=args.output, split=split, backend="numpy")
        seen = set()
        for i in range(len(ds)):
            sid = ds[i]["series_id"]
            if sid in seen:
                continue
            seen.add(sid)
            proj = ds.get_series_projections(sid)
            if not proj:
                continue
            m = rs.check_series_projection_recon(proj["full_dose"], ds.get_series_recon(sid),
                                                 proj.get("geometry", {}))
            print(f"{sid}: status={m.get('status')} pearson_r={m.get('pearson_r', float('nan')):.3f} "
                  f"rmse={m.get('rmse', float('nan')):.1f} frac_within_tol={m.get('frac_within_tol', float('nan')):.3f}")
            checked += 1
            if args.max_series and checked >= args.max_series:
                print(f"recon-sanity: checked {checked} series (approximate/uncalibrated)")
                return 0
    if checked == 0:
        print("recon-sanity: no series with projections (run prep --with-sinograms first)")
    else:
        print(f"recon-sanity: checked {checked} series (approximate/uncalibrated)")
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
    pr.add_argument("--with-sinograms", action="store_true",
                    help="ingest DICOM-CT-PD projection data (AAPM/Mayo); large output")
    pr.add_argument("--id-map", default=None,
                    help="JSON {native_id: assigned_id} crosswalk for stable IDs across chunked runs")
    pr.set_defaults(func=cmd_prep)

    st = sub.add_parser("stage", help="download+extract AAPM 2016 zips from GCS into a local DICOM tree (the 'unzip step')")
    st.add_argument("--work-dir", required=True, help="local tree to extract into (feeds prep --input)")
    st.add_argument("--gcs-prefix", default="gs://low-dose-ct/aapm_2016_grand_challenge",
                    help="GCS prefix holding the AAPM zips")
    st.add_argument("--patients", default=None, help="comma-separated L### subset (default: all)")
    st.add_argument("--domains", default="image,projection", help="comma-separated: image,projection")
    st.set_defaults(func=cmd_stage)

    fi = sub.add_parser("finalize", help="write splits + manifest over the combined output tree")
    fi.add_argument("--output", required=True)
    fi.set_defaults(func=cmd_finalize)

    va = sub.add_parser("validate", help="run pwm_ldct_loader.validate on the output tree")
    va.add_argument("--output", required=True)
    va.set_defaults(func=cmd_validate)

    rs = sub.add_parser("recon-sanity",
                        help="approximate projection->recon agreement check (uncalibrated; see recon_sanity.py)")
    rs.add_argument("--output", required=True)
    rs.add_argument("--max-series", type=int, default=None, help="limit to first N series")
    rs.set_defaults(func=cmd_recon_sanity)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if getattr(args, "cmd", None) == "prep" and not args.source:
        print("error: --source is required (or set PWM_LDCT_SOURCE)", file=sys.stderr)
        return 2
    return args.func(args)
