"""validate(root) — conformance check (dataset_schema.md §8).

Checks: (a) every metadata record validates against §5; (b) HDF5 root attributes match
metadata; (c) manifest.sha256 verifies; (d) the de-identification audit reports zero
unresolved PHI hits. Optional artifacts (manifest, audit) absent => warning, not error.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import List

import h5py

from .metadata import load_metadata, validate_metadata
from .schema import H5_FULL
from .splits import read_splits


@dataclass
class ValidationReport:
    ok: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    n_series: int = 0
    n_patients: int = 0

    def __bool__(self) -> bool:
        return self.ok


def _sha256(path: str, buf: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(buf), b""):
            h.update(chunk)
    return h.hexdigest()


def validate(root: str) -> ValidationReport:
    errors: List[str] = []
    warnings: List[str] = []

    splits = read_splits(root)
    patients = sorted({p for v in splits.values() for p in v})
    if not patients:
        warnings.append("no splits/*.txt found or all empty")

    metas = sorted(glob.glob(os.path.join(root, "metadata", "*.json")))
    if not metas:
        errors.append("no metadata/*.json found")

    n_series = 0
    for mp in metas:
        meta = load_metadata(mp)
        for e in validate_metadata(meta):
            errors.append(f"{os.path.basename(mp)}: {e}")
        sid = meta.get("series_id")
        for h5p in glob.glob(os.path.join(root, "hdf5", "*", "*", "*", f"{sid}.h5")):
            with h5py.File(h5p, "r") as f:
                for attr in ("scan_uid", "series_id", "source"):
                    if f.attrs.get(attr) != meta.get(attr):
                        errors.append(f"{os.path.basename(h5p)}: HDF5 attr {attr!r} != metadata")
                if H5_FULL not in f:
                    errors.append(f"{os.path.basename(h5p)}: missing dataset {H5_FULL}")
        n_series += 1

    manifest = os.path.join(root, "manifest.sha256")
    if os.path.exists(manifest):
        with open(manifest) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                digest, rel = line.split(None, 1)
                fp = os.path.join(root, rel)
                if not os.path.exists(fp):
                    errors.append(f"manifest: missing file {rel}")
                elif _sha256(fp) != digest:
                    errors.append(f"manifest: hash mismatch {rel}")
    else:
        warnings.append("manifest.sha256 not present")

    audit = os.path.join(root, "deident_audit.jsonl")
    if os.path.exists(audit):
        with open(audit) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                if row.get("result") != "pass":
                    errors.append(f"deident: scan {row.get('scan_uid')} result != pass")
    else:
        warnings.append("deident_audit.jsonl not present")

    return ValidationReport(
        ok=(len(errors) == 0),
        errors=errors,
        warnings=warnings,
        n_series=n_series,
        n_patients=len(patients),
    )
