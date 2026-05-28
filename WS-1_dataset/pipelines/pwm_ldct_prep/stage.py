"""Staging ("unzip step"): materialize AAPM 2016 zips into a local DICOM tree for the adapter.

The AAPM/Box distribution (``gs://low-dose-ct/aapm_2016_grand_challenge/``) ships Siemens
``.IMA`` files in per-(recon | patient) zips whose DICOM headers carry ``PatientID='Anonymous'``
and **no** ``SeriesDescription`` — the patient (``L###``), dose (full/quarter), domain
(image/projection) and recon (thickness/kernel) live *only* in the path. This module pulls the
zips from GCS (or a local mirror) and extracts them preserving the source-relative path, so the
AAPM adapter (:mod:`adapters.aapm_2016`) can recover those facts by path.

No DICOM is redistributed by the project; this runs locally against the user's own GCS copy.
Extraction uses the stdlib :mod:`zipfile` (no ``unzip`` binary); GCS access uses ``gsutil``.
"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
import zipfile
from typing import Dict, Iterable, List, Optional

DEFAULT_GCS_PREFIX = "gs://low-dose-ct/aapm_2016_grand_challenge"
_PID_RE = re.compile(r"[LC]\d{2,}")


def classify_aapm_path(relpath: str) -> Dict[str, Optional[str]]:
    """Recover (patient, role, domain, recon) from an AAPM source/staged path.

    role: ``fd`` (full / FD) | ``ld`` (quarter / QD / low) | None
    domain: ``image`` | ``projection``  (projection iff path names projection / DICOM-CT-PD)
    recon: ``{thickness}_{kernel}`` for images (e.g. ``1mm_b30``), ``""`` for projections.
    """
    low = relpath.lower()
    toks = set(re.split(r"[^a-z0-9]+", low))
    m = _PID_RE.search(relpath)
    patient = m.group(0) if m else None
    domain = "projection" if ("projection" in low or "dicom-ct-pd" in low) else "image"
    if {"qd", "quarter", "low"} & toks:
        role = "ld"
    elif {"fd", "full"} & toks:
        role = "fd"
    else:
        role = None
    thickness = "1mm" if "1mm" in toks else ("3mm" if "3mm" in toks else "")
    if {"b30", "b30f"} & toks:
        kernel = "b30"
    elif {"d45", "sharp"} & toks:
        kernel = "d45"
    else:
        kernel = ""
    recon = "_".join(t for t in (thickness, kernel) if t) if domain == "image" else ""
    return {"patient": patient, "role": role, "domain": domain, "recon": recon,
            "thickness": thickness, "kernel": kernel}


def _domain_of(zip_uri: str) -> str:
    low = zip_uri.lower()
    return "projection" if ("projection" in low or "dicom-ct-pd" in low) else "image"


def extract_zip(local_zip: str, dest_dir: str, patients: Optional[Iterable[str]] = None) -> int:
    """Extract ``local_zip`` into ``dest_dir`` (stdlib zipfile). Returns #files written.

    If ``patients`` is given, only members whose path contains one of those ``L###`` IDs are
    extracted (so a multi-patient image zip can be subset). Members with no ``L###`` token in
    their path (rare; e.g. a stray top-level file) are always extracted.
    """
    want = set(patients) if patients else None
    os.makedirs(dest_dir, exist_ok=True)
    n = 0
    with zipfile.ZipFile(local_zip) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            if want is not None:
                pid = _PID_RE.search(info.filename)
                if pid is not None and pid.group(0) not in want:
                    continue
            zf.extract(info, dest_dir)
            n += 1
    return n


def list_gcs_zips(gcs_prefix: str) -> List[str]:
    r = subprocess.run(["gsutil", "ls", "-r", gcs_prefix.rstrip("/") + "/**"],
                       capture_output=True, text=True, check=True)
    return [ln.strip() for ln in r.stdout.splitlines() if ln.strip().lower().endswith(".zip")]


def stage_aapm(work_dir: str, gcs_prefix: str = DEFAULT_GCS_PREFIX,
               patients: Optional[Iterable[str]] = None,
               domains: Iterable[str] = ("image", "projection"),
               tmp_dir: Optional[str] = None) -> str:
    """Download the needed AAPM zips from ``gcs_prefix`` and extract into ``work_dir``.

    Each zip ``<prefix>/REL.zip`` extracts under ``work_dir/REL/`` (path preserved), then the
    local zip is deleted (no disk bloat beyond one zip at a time). ``patients`` (``L###`` list)
    and ``domains`` restrict the pull; projection zips are per-patient so they are filtered by
    URI, image zips are multi-patient so they are subset on extraction.
    """
    os.makedirs(work_dir, exist_ok=True)
    want = set(patients) if patients else None
    domains = set(domains)
    base = gcs_prefix.rstrip("/")
    tmp_dir = tmp_dir or tempfile.gettempdir()
    staged: List[str] = []
    for uri in list_gcs_zips(gcs_prefix):
        if _domain_of(uri) not in domains:
            continue
        if want is not None and _domain_of(uri) == "projection":
            pid = _PID_RE.search(uri)
            if pid is not None and pid.group(0) not in want:
                continue
        rel = uri[len(base) + 1:]                       # e.g. "Training_Image_Data/1mm B30/FD_1mm.zip"
        dest = os.path.join(work_dir, rel[:-4])         # strip ".zip"
        local_zip = os.path.join(tmp_dir, os.path.basename(uri))
        subprocess.run(["gsutil", "-q", "cp", uri, local_zip], check=True)
        try:
            n = extract_zip(local_zip, dest, patients=want)
            print(f"  staged {n:5d} files  {rel}", flush=True)
            staged.append(rel)
        finally:
            if os.path.exists(local_zip):
                os.remove(local_zip)
    print(f"stage_aapm: {len(staged)} zip(s) -> {work_dir}", flush=True)
    return work_dir
