"""DICOM geometry-based pairing validation (Rung 2 / companion charter 1.4).

For the v1.0 real paired data (AAPM 2016 + Mayo LDCT-PD) the low-dose and full-dose
series must be paired by **scan geometry**, not by file-name or InstanceNumber order.
This module is a standalone, independently recomputed validator:

1. reads ImagePositionPatient (0020,0032) from every slice of the two series,
2. projects each position onto the series normal (derived from
   ImageOrientationPatient 0020,0037) to get the along-axis coordinate,
3. pairs slices whose along-axis coordinates agree within ``tol_mm``,
4. independently recomputes the correlation of the paired geometry
   (target Pearson r > 0.99; any pair whose delta exceeds ``tol_mm`` fails),
5. never sorts by file name / InstanceNumber.

It is a ready-to-run tool; it is not required to run on the AAPM/Mayo trees today
(v1.0 roadmap). The pure geometry functions are tested with synthetic metadata so the
validator is exercised without real DICOM files.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from typing import Dict, List, Optional, Sequence, Tuple

# target: correlation of paired slice positions (companion charter 1.4 ">0.99")
DEFAULT_MIN_CORRELATION = 0.99
DEFAULT_TOL_MM = 0.5

SliceMeta = Dict[str, object]  # {"sop_uid", "instance_number", "position_xyz": [x,y,z], "orientation_xyz": [rx,ry,rz,cx,cy,cz]}


# ---------------------------------------------------------------------------
# pure geometry functions (no pydicom dependency)
# ---------------------------------------------------------------------------

def _cross(a: Sequence[float], b: Sequence[float]) -> List[float]:
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return float(sum(x * y for x, y in zip(a, b)))


def _norm(a: Sequence[float]) -> float:
    return math.sqrt(_dot(a, a))


def along_axis_positions(metas: Sequence[SliceMeta], ) -> List[Tuple[str, float]]:
    """Project each slice position onto the series normal (from orientation).

    For an axial series the normal is (0,0,±1) so the along-axis coordinate is the
    Z of ImagePositionPatient; for oblique series it is the projected distance.
    Returns [(sop_uid, along_axis_mm)].
    """
    out: List[Tuple[str, float]] = []
    for m in metas:
        pos = [float(v) for v in m["position_xyz"]]
        orient = [float(v) for v in m["orientation_xyz"]]
        row, col = orient[:3], orient[3:]
        normal = _cross(row, col)
        n = _norm(normal)
        if n < 1e-9:
            raise ValueError("degenerate ImageOrientationPatient (zero normal)")
        normal = [v / n for v in normal]
        out.append((str(m["sop_uid"]), _dot(pos, normal)))
    return out


def pair_by_geometry(fd_metas: Sequence[SliceMeta],
                     ld_metas: Sequence[SliceMeta],
                     tol_mm: float = DEFAULT_TOL_MM) -> Dict[str, object]:
    """Pair full-dose and low-dose slices by along-axis geometry.

    The key is the geometry value, never the file name or InstanceNumber order.
    Returns a dict with 'pairs' (list of {fd_sop_uid, ld_sop_uid, pos_mm, abs_delta_mm}),
    'n_fd', 'n_ld', 'n_paired', 'n_unpaired_fd', 'n_unpaired_ld',
    'geometry_correlation' (Pearson r over paired positions) and 'violations'.
    """
    fd_pos = along_axis_positions(fd_metas)
    ld_pos = along_axis_positions(ld_metas)
    fd_pos = sorted(fd_pos, key=lambda t: t[1])
    ld_pos = sorted(ld_pos, key=lambda t: t[1])

    pairs: List[Dict[str, object]] = []
    used_ld = set()
    for fd_uid, p in fd_pos:
        # nearest low-dose slice in geometry space
        best = None
        best_d = float("inf")
        for i, (ld_uid, q) in enumerate(ld_pos):
            if i in used_ld:
                continue
            d = abs(p - q)
            if d < best_d:
                best_d = d
                best = (i, ld_uid, q)
        if best is None:
            continue
        i, ld_uid, q = best
        if best_d > tol_mm:
            continue  # no geometry match within tolerance -> unpaired
        used_ld.add(i)
        pairs.append({"fd_sop_uid": fd_uid, "ld_sop_uid": ld_uid,
                      "pos_mm": p, "abs_delta_mm": best_d})
    pairs.sort(key=lambda d: float(d["pos_mm"]))

    # correlation over paired geometry (independent recomputation)
    corr = None
    if len(pairs) >= 2:
        xs = [float(d["pos_mm"]) for d in pairs]
        ys = [_geometry_value_for(ld_pos, d) for d in pairs]
        corr = _pearson(xs, ys)
    else:
        corr = None

    violations = [d for d in pairs if float(d["abs_delta_mm"]) > tol_mm]
    n_ld_total = len(ld_pos)
    return {
        "pairs": pairs,
        "n_fd": len(fd_pos),
        "n_ld": n_ld_total,
        "n_paired": len(pairs),
        "n_unpaired_fd": len(fd_pos) - len(pairs),
        "n_unpaired_ld": n_ld_total - len(pairs),
        "geometry_correlation": corr,
        "tol_mm": tol_mm,
        "violations": violations,
    }


def _geometry_value_for(ld_pos: Sequence[Tuple[str, float]], d: Dict[str, object]) -> float:
    for uid, pos in ld_pos:
        if uid == d["ld_sop_uid"]:
            return pos
    return float(d["pos_mm"])


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float:
    n = len(xs)
    if n < 2:
        return None  # type: ignore[return-value]
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None  # constant series: correlation undefined
    return sxy / math.sqrt(sxx * syy)


def validate(pairs_result: Dict[str, object],
             min_correlation: float = DEFAULT_MIN_CORRELATION) -> Dict[str, object]:
    """Evaluate the pairing against the charter target (>0.99 correlation, no violations)."""
    corr = pairs_result.get("geometry_correlation")
    violations = pairs_result.get("violations", [])
    ok = (corr is not None and corr > min_correlation and len(violations) == 0)
    return {
        "passed": bool(ok),
        "min_correlation_target": min_correlation,
        "geometry_correlation": corr,
        "n_violations": len(violations),
        "reason": ("OK" if ok else
                   ("correlation below target" if (corr is None or corr <= min_correlation)
                    else "delta violations found")),
    }


# ---------------------------------------------------------------------------
# DICOM reading (pydicom)
# ---------------------------------------------------------------------------

def read_series_positions(dicom_dir: str) -> List[SliceMeta]:
    """Read ImagePositionPatient / ImageOrientationPatient / SOPInstanceUID from a DICOM dir."""
    try:
        import pydicom
    except ImportError as e:  # pragma: no cover
        raise RuntimeError("pydicom is required to read DICOM series; "
                           "install it (`pip install pydicom`) or pass synthetic metadata "
                           "to the pure functions.") from e
    metas: List[SliceMeta] = []
    for fn in sorted(os.listdir(dicom_dir)):
        path = os.path.join(dicom_dir, fn)
        if not os.path.isfile(path):
            continue
        try:
            ds = pydicom.dcmread(path, stop_before_pixels=True)
        except Exception:
            continue
        if "ImagePositionPatient" not in ds or "ImageOrientationPatient" not in ds:
            continue
        metas.append({
            "sop_uid": str(ds.get("SOPInstanceUID", fn)),
            "instance_number": int(ds.get("InstanceNumber", 0) or 0),
            "position_xyz": [float(v) for v in ds.ImagePositionPatient],
            "orientation_xyz": [float(v) for v in ds.ImageOrientationPatient],
        })
    if not metas:
        raise RuntimeError(f"no DICOM slices with geometry found under {dicom_dir}")
    return metas


def run_pairing_check(fd_dir: str, ld_dir: str, out_json: str,
                      tol_mm: float = DEFAULT_TOL_MM,
                      min_correlation: float = DEFAULT_MIN_CORRELATION) -> Dict[str, object]:
    """End-to-end: read two DICOM dirs, pair by geometry, validate, write JSON."""
    fd_metas = read_series_positions(fd_dir)
    ld_metas = read_series_positions(ld_dir)
    res = pair_by_geometry(fd_metas, ld_metas, tol_mm=tol_mm)
    verdict = validate(res, min_correlation=min_correlation)
    report = {"input": {"fd_dir": fd_dir, "ld_dir": ld_dir},
              "pairing": res, "validation": verdict}
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"wrote {out_json}")
    print(f"paired={res['n_paired']}/{res['n_fd']}  corr={res['geometry_correlation']}  "
          f"passed={verdict['passed']}  reason={verdict['reason']}")
    return report


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="dicom-pairing",
        description="Validate low-dose/full-dose DICOM pairing by ImagePositionPatient geometry "
                    "(never by file-name order). Ready for v1.0 real paired data.")
    p.add_argument("--fd-dir", required=True, help="full-dose DICOM series directory")
    p.add_argument("--ld-dir", required=True, help="low-dose DICOM series directory")
    p.add_argument("--out", required=True, help="output JSON report path")
    p.add_argument("--tol-mm", type=float, default=DEFAULT_TOL_MM)
    p.add_argument("--min-correlation", type=float, default=DEFAULT_MIN_CORRELATION)
    args = p.parse_args(argv)
    run_pairing_check(args.fd_dir, args.ld_dir, args.out,
                      tol_mm=args.tol_mm, min_correlation=args.min_correlation)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
