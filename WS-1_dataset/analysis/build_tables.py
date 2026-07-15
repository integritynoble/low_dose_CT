"""Regenerate every provisional manuscript table from a deposited release tree.

Runs the three extractors over ``{root}/metadata`` and
``{root}/annotations/lidc_majority_vote`` and writes ``{out}/{stem}.json`` (numbers),
``{out}/{stem}.tex`` (LaTeX rows to \\input into the manuscript), and
``{out}/provenance.json`` (input file count + combined SHA-256 of every file consumed).
The provenance record is what lets a caption honestly say "regenerated from a committed
artifact": the hash pins the exact inputs.

Usage:
    python build_tables.py --root /path/pwm_ldct_1_0 --out tables [--n-patients-total 1010]
"""
from __future__ import annotations

import argparse
import glob
import json
import os

from common import inputs_fingerprint, load_series_metadata, write_outputs
from extract_acquisition import compute_acquisition, to_latex as acq_latex
from extract_demographics import compute_demographics, to_latex as demo_latex
from extract_inter_rater import compute_inter_rater, to_latex as irr_latex


def build(root: str, out: str, n_patients_total=None) -> dict:
    metadata_dir = os.path.join(root, "metadata")
    mv_dir = os.path.join(root, "annotations", "lidc_majority_vote")

    series = load_series_metadata(metadata_dir)
    demo = compute_demographics(series)
    acq = compute_acquisition(series)
    write_outputs("demographics", demo, demo_latex(demo), out)
    write_outputs("acquisition", acq, acq_latex(acq), out)

    consumed = sorted(glob.glob(os.path.join(metadata_dir, "*.json")))
    result = {"demographics": demo, "acquisition": acq}

    if os.path.isdir(mv_dir):
        irr = compute_inter_rater(mv_dir, n_patients_total)
        write_outputs("inter_rater", irr, irr_latex(irr), out)
        consumed += sorted(glob.glob(os.path.join(mv_dir, "*.json")))
        result["inter_rater"] = irr

    prov = inputs_fingerprint(consumed)
    with open(os.path.join(out, "provenance.json"), "w", encoding="utf-8") as fh:
        json.dump(prov, fh, indent=2)
    result["provenance"] = prov
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="deposited release root (has metadata/ + annotations/)")
    ap.add_argument("--out", default="tables")
    ap.add_argument("--n-patients-total", type=int, default=None)
    args = ap.parse_args()
    res = build(args.root, args.out, args.n_patients_total)
    print(f"wrote tables to {args.out}/  (provenance: {res['provenance']['n_files']} files, "
          f"sha256 {res['provenance']['combined_sha256'][:12]}...)")


if __name__ == "__main__":
    main()
