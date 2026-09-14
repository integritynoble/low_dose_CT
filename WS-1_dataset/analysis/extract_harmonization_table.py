"""Regenerate the manuscript harmonization-validation table (``tab:harmonization_v05``).

The table previously carried "intermediate provenance": it was produced by a temporary
script (``hv_fast.py``) that was never committed, so the five published numbers could not
be reproduced from the repository.  This module replaces it with a committed, seeded
implementation; every cell comes from the released metadata tree plus the released
full-dose HDF5 volumes, and the emitted caption records the sampling seed and the
file-set fingerprint.

Definitions (stated explicitly here because the original script documented none):

* **Sampling** -- vendor-stratified random sample of ``--per-vendor`` series per vendor
  (default 30, 120 total), drawn with ``random.Random(--seed)`` while iterating vendors
  and series ids in sorted order, so the sample is a deterministic function of the
  metadata tree.
* **HU histogram** -- full-dose volumes are read from ``recon/full_dose`` at up to
  ``--max-slices`` equally spaced slices per series, every voxel kept, histogrammed over
  the clinical window [-1100, 500] HU with ``--bins`` equal-width bins.
* **W1 (HU)** -- 1-Wasserstein distance between a vendor's histogram and the aggregate
  histogram pooled over the 120 sampled series (equally weighted per vendor), evaluated
  as the L1 area between the two CDFs over the window.
* **Spacing overlap (%)** -- distribution-overlap coefficient (histogram intersection)
  between a vendor's pixel-spacing distribution and the aggregate's.
* **Thickness overlap (%)** -- same coefficient restricted to the thin-slice subset
  (slice thickness <= 1.5 mm); vendors contributing no thin series report ``---``.
* **Worst vendor pair** -- maximum W1 over all vendor pairs; this is the number that
  sets the manuscript's threshold.

Usage:
    python extract_harmonization_table.py --data-root D:\\ZHY\\LIDC3DDataSet\\output_all \
        --out tables
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import random
from collections import OrderedDict, defaultdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from common import inputs_fingerprint, write_outputs

HU_WINDOW: Tuple[float, float] = (-1100.0, 500.0)
THIN_MM: float = 1.5

VENDOR_LABELS: Dict[str, str] = {
    "GE MEDICAL SYSTEMS": "GE Medical Systems",
    "SIEMENS": "Siemens",
    "TOSHIBA": "Toshiba",
    "Philips": "Philips",
}


def _series_index(data_root: str) -> Dict[str, List[Dict[str, Any]]]:
    meta_dir = os.path.join(data_root, "metadata")
    by_vendor: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for path in sorted(glob.glob(os.path.join(meta_dir, "*.json"))):
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
        acq = doc.get("acquisition") or {}
        vendor = acq.get("manufacturer") or "UNKNOWN"
        by_vendor[vendor].append({
            "meta_path": path,
            "series_id": doc.get("series_id") or doc.get("patient_id"),
            "patient_id": doc.get("patient_id"),
            "spacing": float((acq.get("pixel_spacing_mm") or [np.nan])[0]),
            "thickness": float(acq.get("slice_thickness_mm") or np.nan),
        })
    return by_vendor


def _h5_path(data_root: str, patient_id: str) -> Optional[str]:
    hits = glob.glob(os.path.join(data_root, "hdf5", "*", "lidc", patient_id,
                                  f"{patient_id}_chest_fd.h5"))
    return hits[0] if hits else None


def _histogram(h5_path: str, bins: int, max_slices: int) -> Tuple[np.ndarray, int]:
    import h5py

    lo, hi = HU_WINDOW
    edges = np.linspace(lo, hi, bins + 1)
    with h5py.File(h5_path, "r") as fh:
        ds = fh["recon/full_dose"]
        z = ds.shape[0]
        idx = np.unique(np.linspace(0, z - 1, min(z, max_slices)).round().astype(int))
        acc = np.zeros(bins, dtype=np.float64)
        for i in idx:
            sl = ds[int(i), :, :].astype(np.float32)
            acc += np.histogram(sl, bins=edges)[0]
    return acc, int(idx.size)


def _pooled(hist: np.ndarray) -> np.ndarray:
    total = hist.sum()
    return hist / total if total else hist


def _w1(p: np.ndarray, q: np.ndarray, edges: np.ndarray) -> float:
    """1-Wasserstein distance (HU) between two histograms on a common bin grid."""
    dx = float(edges[1] - edges[0])
    return float(np.abs(np.cumsum(p) - np.cumsum(q)).sum() * dx)


def _overlap_labels(xs: List[float], ys: List[float]) -> Tuple[float, List[float]]:
    """Distribution-overlap coefficient (%) between two categorical samples."""
    from collections import Counter
    a, b = Counter(xs), Counter(ys)
    keys = set(a) | set(b)
    na, nb = max(len(xs), 1), max(len(ys), 1)
    ov = sum(min(a[k] / na, b[k] / nb) for k in keys)
    return 100.0 * ov, sorted(keys)


def build(data_root: str, per_vendor: int, seed: int, bins: int,
          max_slices: int, aggregate_mode: str = "pooled",
          dump_hists: Optional[str] = None) -> Dict[str, Any]:
    lo, hi = HU_WINDOW
    edges = np.linspace(lo, hi, bins + 1)
    by_vendor = _series_index(data_root)
    vendors = sorted(v for v in by_vendor if v in VENDOR_LABELS)

    rng = random.Random(seed)
    sample: Dict[str, List[Dict[str, Any]]] = OrderedDict()
    for v in vendors:
        rows = sorted(by_vendor[v], key=lambda r: str(r["series_id"]))
        if len(rows) < per_vendor:
            raise SystemExit(f"{v}: only {len(rows)} series for per-vendor={per_vendor}")
        sample[v] = rng.sample(rows, per_vendor)

    hists: Dict[str, np.ndarray] = {}
    slices_used: Dict[str, int] = {}
    meta_paths: List[str] = []
    for v, rows in sample.items():
        acc = np.zeros(bins, dtype=np.float64)
        used = 0
        for r in rows:
            meta_paths.append(r["meta_path"])
            h5 = _h5_path(data_root, r["patient_id"])
            if h5 is None:
                raise SystemExit(f"no full-dose HDF5 for {r['patient_id']}")
            h, n = _histogram(h5, bins, max_slices)
            acc += h
            used = max(used, n)
        hists[v] = acc
        slices_used[v] = used

    pq = {v: _pooled(h) for v, h in hists.items()}
    if aggregate_mode == "leave-one-out":
        agg_hist = {v: np.sum([hists[u] for u in vendors if u != v], axis=0) for v in vendors}
    else:
        agg_hist = {v: np.sum(list(hists.values()), axis=0) for v in vendors}
    p_agg = {v: _pooled(h) for v, h in agg_hist.items()}
    if dump_hists:
        np.savez(dump_hists, edges=edges,
                 vendor_keys=np.array(vendors),
                 **{f"hist_{v}": hists[v] for v in vendors})

    rows_out: List[Dict[str, Any]] = []
    for v in vendors:
        all_spacing = [r["spacing"] for r in sample[v]]
        all_thick = [r["thickness"] for r in sample[v]]
        agg_spacing = [r["spacing"] for rows in sample.values() for r in rows]
        agg_thick = [r["thickness"] for rows in sample.values() for r in rows]
        sp_ov, _ = _overlap_labels(all_spacing, agg_spacing)
        thin = [t for t in all_thick if t == t and t <= THIN_MM]
        agg_thin = [t for t in agg_thick if t == t and t <= THIN_MM]
        if thin:
            th_ov, _ = _overlap_labels(thin, agg_thin)
        else:
            th_ov = None
        rows_out.append({
            "vendor": v,
            "label": VENDOR_LABELS[v],
            "n_series": len(sample[v]),
            "w1_hu": _w1(pq[v], p_agg[v], edges),
            "spacing_overlap_pct": sp_ov,
            "thickness_overlap_pct": th_ov,
            "max_slices_read": slices_used[v],
        })

    worst = (0.0, None, None)
    for i, a in enumerate(vendors):
        for b in vendors[i + 1:]:
            d = _w1(pq[a], pq[b], edges)
            if d > worst[0]:
                worst = (d, a, b)

    return {
        "window_hu": list(HU_WINDOW),
        "thin_mm": THIN_MM,
        "bins": bins,
        "max_slices_per_series": max_slices,
        "sample_seed": seed,
        "per_vendor": per_vendor,
        "aggregate_mode": aggregate_mode,
        "vendors": rows_out,
        "worst_pair": {
            "w1_hu": worst[0],
            "vendor_a": VENDOR_LABELS.get(worst[1] or "", worst[1]),
            "vendor_b": VENDOR_LABELS.get(worst[2] or "", worst[2]),
        },
        "provenance": inputs_fingerprint(sorted(meta_paths)),
        "n_metadata_files": len(meta_paths),
    }


def to_latex(t: Dict[str, Any]) -> str:
    lines = [
        "\\textbf{Vendor} & $n_{\\text{series}}$ & $W_1$ vs.\\ aggregate (HU) & "
        "Spacing overlap (\\%) & Thickness overlap (\\%) \\\\",
        "\\midrule",
    ]
    for r in t["vendors"]:
        th = "---" if r["thickness_overlap_pct"] is None else f"{r['thickness_overlap_pct']:.1f}"
        lines.append(f"{r['label']} & {r['n_series']} & {r['w1_hu']:.1f} & "
                     f"{r['spacing_overlap_pct']:.1f} & {th} \\\\")
    return ("% auto-generated by extract_harmonization_table.py -- do not hand-edit\n"
            + "\n".join(lines) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", required=True,
                    help="harmonized LIDC root holding metadata/ and hdf5/")
    ap.add_argument("--out", default="tables")
    ap.add_argument("--per-vendor", type=int, default=30)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--bins", type=int, default=160)
    ap.add_argument("--max-slices", type=int, default=26)
    ap.add_argument("--aggregate-mode", choices=["pooled", "leave-one-out"], default="pooled",
                    help="reference histogram: pooled over all sampled series, or the "
                         "other vendors' pooled histogram (leave-one-out)")
    ap.add_argument("--dump-hists", default=None,
                    help="optional .npz path to cache per-vendor HU histograms")
    args = ap.parse_args()

    t = build(args.data_root, args.per_vendor, args.seed, args.bins, args.max_slices,
              args.aggregate_mode, args.dump_hists)
    write_outputs("harmonization", t, to_latex(t), args.out)

    prov = t["provenance"]
    print(f"harmonization: {len(t['vendors'])} vendors x {t['per_vendor']} series "
          f"(seed {t['sample_seed']}); provenance {prov['n_files']} metadata files, "
          f"SHA {prov['combined_sha256'][:12]}...")
    for r in t["vendors"]:
        th = "---" if r["thickness_overlap_pct"] is None else f"{r['thickness_overlap_pct']:.1f}"
        print(f"  {r['label']:20s} W1={r['w1_hu']:7.1f} HU  spacing={r['spacing_overlap_pct']:5.1f}%"
              f"  thickness={th}")
    w = t["worst_pair"]
    print(f"  worst pair: {w['vendor_a']}--{w['vendor_b']} W1={w['w1_hu']:.1f} HU")


if __name__ == "__main__":
    main()
