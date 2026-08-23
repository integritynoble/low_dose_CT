"""Shared helpers for the PWM-LDCT 1.0 table-extraction scripts.

These scripts regenerate the manuscript's Data-Records tables (demographics,
acquisition, inter-rater) *from the deposited artifacts* -- ``metadata/{series_id}.json``
(schema/dataset_schema.md §5) and ``annotations/lidc_majority_vote/{patient_id}.json``
(§6). Every table cell the manuscript prints is emitted by one of these scripts, so
no number is asserted by hand. Stdlib only (no numpy) so the scripts run anywhere.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
from collections import Counter
from statistics import median
from typing import Any, Dict, Iterable, List, Optional, Tuple

SOURCES = ("lidc", "aapm", "mayo")


def normalize_source(source: Any) -> str:
    """Bucket a series' raw ``source`` field onto a canonical source key.

    LIDC-derived entries may carry an annotation suffix, e.g. ``"lidc
    (simulated_from lidc-0237)"`` for the placeholder-fill supplements; anything
    whose key starts with ``"lidc"`` is bucketed under ``"lidc"`` so the full
    1,010-patient cohort is counted. AAPM/Mayo keys are returned unchanged, so
    future v1.0 builds need no script changes.
    """
    src = str(source or "").strip()
    if src.startswith("lidc"):
        return "lidc"
    return src


# --------------------------------------------------------------------------- IO
def load_series_metadata(metadata_dir: str) -> List[Dict[str, Any]]:
    """Load every ``metadata/{series_id}.json`` under *metadata_dir* (sorted)."""
    out: List[Dict[str, Any]] = []
    for path in sorted(glob.glob(os.path.join(metadata_dir, "*.json"))):
        with open(path, "r", encoding="utf-8") as fh:
            out.append(json.load(fh))
    return out


def load_json_dir(directory: str) -> List[Tuple[str, Any]]:
    """Load every ``*.json`` under *directory* as ``(basename, obj)``, sorted."""
    out: List[Tuple[str, Any]] = []
    for path in sorted(glob.glob(os.path.join(directory, "*.json"))):
        with open(path, "r", encoding="utf-8") as fh:
            out.append((os.path.basename(path), json.load(fh)))
    return out


def inputs_fingerprint(paths: Iterable[str]) -> Dict[str, Any]:
    """A committed-artifact provenance record: file count + combined SHA-256.

    The combined hash is ``sha256`` over the sorted list of per-file ``sha256``
    digests, so it is stable regardless of filesystem ordering and lets a reader
    confirm the table was generated from a specific set of deposited files.
    """
    digests = []
    for path in sorted(paths):
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        digests.append(h.hexdigest())
    combined = hashlib.sha256("\n".join(sorted(digests)).encode("utf-8")).hexdigest()
    return {"n_files": len(digests), "combined_sha256": combined}


# ----------------------------------------------------------------------- stats
def _sorted_non_null(values: Iterable[Any]) -> List[float]:
    return sorted(float(v) for v in values if v is not None)


def _quantile(sorted_vals: List[float], q: float) -> Optional[float]:
    """Linear-interpolation quantile (same convention as numpy 'linear')."""
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = q * (len(sorted_vals) - 1)
    lo = int(pos)
    frac = pos - lo
    if lo + 1 < len(sorted_vals):
        return sorted_vals[lo] + frac * (sorted_vals[lo + 1] - sorted_vals[lo])
    return sorted_vals[lo]


def summarize_numeric(values: Iterable[Any]) -> Dict[str, Optional[float]]:
    """median / IQR / range / n over the non-null values."""
    xs = _sorted_non_null(values)
    if not xs:
        return {"n": 0, "median": None, "q1": None, "q3": None, "min": None, "max": None}
    return {
        "n": len(xs),
        "median": median(xs),
        "q1": _quantile(xs, 0.25),
        "q3": _quantile(xs, 0.75),
        "min": xs[0],
        "max": xs[-1],
    }


def count_categories(values: Iterable[Any]) -> Counter:
    return Counter(v for v in values if v is not None)


# ---------------------------------------------------------------- LaTeX output
def latex_escape(s: str) -> str:
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"),
                 ("_", r"\_"), ("#", r"\#"), ("$", r"\$")):
        s = s.replace(a, b)
    return s


def fmt_median_iqr(summary: Dict[str, Optional[float]], nd: int = 0) -> str:
    if summary["n"] == 0 or summary["median"] is None:
        return "N/A"
    m, q1, q3 = summary["median"], summary["q1"], summary["q3"]
    return f"{m:.{nd}f} ({q1:.{nd}f}--{q3:.{nd}f})"


def fmt_range(summary: Dict[str, Optional[float]], nd: int = 0) -> str:
    if summary["n"] == 0 or summary["min"] is None:
        return "N/A"
    return f"{summary['min']:.{nd}f}--{summary['max']:.{nd}f}"


def write_outputs(stem: str, table: Dict[str, Any], latex: str, out_dir: str) -> None:
    """Write ``tables/{stem}.json`` (numbers) and ``tables/{stem}.tex`` (rows)."""
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, f"{stem}.json"), "w", encoding="utf-8") as fh:
        json.dump(table, fh, indent=2, sort_keys=True)
    with open(os.path.join(out_dir, f"{stem}.tex"), "w", encoding="utf-8") as fh:
        fh.write(latex)
