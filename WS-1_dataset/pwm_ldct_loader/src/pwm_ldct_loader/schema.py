"""Schema constants and conventions.

Mirrors ``WS-1_dataset/schema/dataset_schema.md`` (the single source of truth). If that
spec changes, update these constants in lockstep and bump ``SCHEMA_VERSION``.
"""
from __future__ import annotations

import numpy as np

SCHEMA_VERSION = "0.5.0"

SOURCES = ("lidc", "aapm", "mayo")
ANATOMIES = ("chest", "abdomen")
DOSE_RATIOS = (0.10, 0.25, 0.50)   # simulated low-dose ratios
REAL_DOSE_RATIO = 0.25             # AAPM/Mayo real paired low-dose
PIXEL_DTYPE = np.float32           # all image/sinogram data are HU / line-integral float32

# --- HDF5 dataset paths (dataset_schema.md §3) -----------------------------------------
H5_FULL = "recon/full_dose"
H5_LD_REAL = "recon/low_dose_real"
H5_SINO_FULL = "sinogram/full_dose"
H5_SINO_LD_REAL = "sinogram/low_dose_real"


def h5_ld_sim(ratio: float) -> str:
    """HDF5 path for the simulated low-dose volume at the given ratio, e.g. 0.25 -> ``recon/low_dose_sim/r025``."""
    return f"recon/low_dose_sim/r{int(round(ratio * 100)):03d}"


# --- Split fractions (dataset_schema.md §7) --------------------------------------------
SPLIT_FRACTIONS = {"train": 0.60, "val": 0.20, "test": 0.20}

# --- Loader sample contract (dataset_schema.md §4) -------------------------------------
SAMPLE_KEYS = (
    "full_dose", "low_dose", "low_dose_kind", "dose_ratio", "sinogram",
    "source", "patient_id", "series_id", "slice_index", "annotations", "metadata",
)

# --- metadata.json required fields (dataset_schema.md §5) ------------------------------
META_REQUIRED = (
    "scan_uid", "patient_id", "series_id", "source", "anatomy", "schema_version", "acquisition",
)
ACQ_REQUIRED = (
    "manufacturer", "slice_thickness_mm", "pixel_spacing_mm", "recon_kernel",
    "image_orientation_patient", "patient_position",
)

THIN_SLICE_MAX_MM = 1.5  # "thin" series selection threshold (dataset_schema.md §4.1)
