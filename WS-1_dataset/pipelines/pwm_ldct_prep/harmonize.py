"""Harmonization: HU offset application and metadata.json assembly (../schema/dataset_schema.md §5).

HU offsets and MTF/electronic-noise calibration are per-source constants measured from each
source's CT-performance-phantom data; defaults are 0.0 / null and are the [CONFIRM] values in
the manuscript. Kernels are preserved (no re-reconstruction).
"""
from __future__ import annotations

import hashlib
from typing import Dict, List, Optional

import numpy as np

from pwm_ldct_loader.schema import DOSE_RATIOS, SCHEMA_VERSION

# Per-source HU offset (HU), [CONFIRM] at release; 0.0 = no correction.
HU_OFFSET = {"lidc": 0.0, "aapm": 0.0, "mayo": 0.0}


def scan_uid(series_id: str) -> str:
    return hashlib.sha256((series_id + SCHEMA_VERSION).encode()).hexdigest()[:16]


def apply_hu_offset(volume: np.ndarray, source: str) -> np.ndarray:
    off = HU_OFFSET.get(source, 0.0)
    return volume if off == 0.0 else (volume + off).astype(np.float32)


def build_metadata(series, sim_model: str, seed: int, n_slices: int) -> Dict:
    """Assemble a schema-§5 metadata object for a (full-dose) series."""
    acq = series.acquisition
    return {
        "scan_uid": scan_uid(series.series_id),
        "patient_id": series.patient_id,
        "series_id": series.series_id,
        "source": series.source,
        "anatomy": series.anatomy,
        "schema_version": SCHEMA_VERSION,
        "acquisition": {
            "manufacturer": acq.get("manufacturer", ""),
            "model": acq.get("model", ""),
            "kvp": acq.get("kvp"),
            "exposure_mas": acq.get("exposure_mas"),
            "pitch": acq.get("pitch"),
            "slice_thickness_mm": acq.get("slice_thickness_mm", 0.0),
            "pixel_spacing_mm": acq.get("pixel_spacing_mm", [1.0, 1.0]),
            "recon_kernel": acq.get("recon_kernel", ""),
            "image_orientation_patient": acq.get("image_orientation_patient", [1, 0, 0, 0, 1, 0]),
            "patient_position": acq.get("patient_position", ""),
        },
        "calibration": {
            "hu_offset": HU_OFFSET.get(series.source, 0.0),
            "mtf_50_lp_per_cm": None,
            "bowtie_profile": "uniform_fallback",
            "electronic_noise_sigma": None,
        },
        "lowdose_sim": {
            "model": sim_model,
            "ratios": list(DOSE_RATIOS),
            "I0_monochromatic_ref": None,
            "seed": seed,
        },
        "demographics": series.demographics,
        "provenance": {
            "source_sop_class_uid": "1.2.840.10008.5.1.4.1.1.2",
            "rehashed_study_uid": series.src_uids.get("study", ""),
            "rehashed_series_uid": series.src_uids.get("series", ""),
            "n_slices": n_slices,
            "deident_audit_id": scan_uid(series.series_id),
        },
    }
