"""metadata.json loading and validation (dataset_schema.md §5)."""
from __future__ import annotations

import json
from typing import List

from .schema import ACQ_REQUIRED, ANATOMIES, META_REQUIRED, SCHEMA_VERSION, SOURCES


def load_metadata(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def validate_metadata(meta: dict) -> List[str]:
    """Return a list of human-readable schema violations; empty list means valid."""
    errs: List[str] = []
    for k in META_REQUIRED:
        if k not in meta:
            errs.append(f"missing top-level field: {k}")
    if meta.get("schema_version") != SCHEMA_VERSION:
        errs.append(f"schema_version {meta.get('schema_version')!r} != {SCHEMA_VERSION!r}")
    if meta.get("source") not in SOURCES:
        errs.append(f"source {meta.get('source')!r} not in {SOURCES}")
    if meta.get("anatomy") not in ANATOMIES:
        errs.append(f"anatomy {meta.get('anatomy')!r} not in {ANATOMIES}")

    acq = meta.get("acquisition", {})
    if not isinstance(acq, dict):
        errs.append("acquisition must be an object")
        return errs
    for k in ACQ_REQUIRED:
        if k not in acq:
            errs.append(f"missing acquisition field: {k}")
    ps = acq.get("pixel_spacing_mm")
    if not (isinstance(ps, (list, tuple)) and len(ps) == 2):
        errs.append("acquisition.pixel_spacing_mm must be [row, col]")
    iop = acq.get("image_orientation_patient")
    if not (isinstance(iop, (list, tuple)) and len(iop) == 6):
        errs.append("acquisition.image_orientation_patient must be 6 floats")
    return errs
