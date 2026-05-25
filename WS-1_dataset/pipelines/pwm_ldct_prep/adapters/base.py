"""Source-adapter base: DICOM discovery, CT-volume reading, and the harmonized records.

Adapters turn a source's raw DICOM tree into ``PatientScans`` (a full-dose recon series plus an
optional real low-dose recon series and optional projections). The reconstructed-image path is
fully implemented here; projection (DICOM-CT-PD) reading is a documented hook (``read_projections``)
that adapters with sinograms override — see SiemensPairedAdapter.
"""
from __future__ import annotations

import glob
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional, Tuple

import numpy as np
import pydicom

CT_IMAGE_STORAGE = "1.2.840.10008.5.1.4.1.1.2"


@dataclass
class Series:
    patient_id: str            # harmonized, source-prefixed (e.g. "mayo-0001")
    series_id: str             # "{patient_id}_{anatomy}_{role}"
    source: str
    anatomy: str               # "chest" | "abdomen"
    role: str                  # "fd" | "ld"
    volume_hu: np.ndarray      # [Z, H, W] float32, HU
    acquisition: Dict
    slice_positions: List[List[float]]
    demographics: Dict = field(default_factory=dict)
    sinogram: Optional[np.ndarray] = None      # [Z, V, D] or None
    geometry: Optional[Dict] = None
    src_uids: Dict = field(default_factory=dict)  # rehashed study/series UIDs


@dataclass
class PatientScans:
    patient_id: str
    fd: Series                 # full-dose recon (always present)
    ld: Optional[Series] = None  # real low-dose recon (aapm/mayo); None for lidc
    annotations: Optional[Dict] = None  # source-native annotations (e.g. LIDC nodules), if any


def group_dicom(input_dir: str) -> Dict[str, Dict]:
    """Group all *.dcm under input_dir by SeriesInstanceUID; read one header per series.

    Returns {series_uid: {"files": [paths], "header": Dataset(stop_before_pixels)}}.
    """
    groups: Dict[str, Dict] = {}
    for path in glob.iglob(os.path.join(input_dir, "**", "*.dcm"), recursive=True):
        try:
            hdr = pydicom.dcmread(path, stop_before_pixels=True, force=True)
            suid = str(hdr.SeriesInstanceUID)
        except Exception:
            continue
        g = groups.setdefault(suid, {"files": [], "header": hdr})
        g["files"].append(path)
    return groups


def read_ct_volume(files: List[str]) -> Tuple[np.ndarray, Dict, List[List[float]], "pydicom.Dataset"]:
    """Read a CT image series into an HU volume [Z, H, W], sorted cranio-caudally."""
    slices = []
    for p in files:
        ds = pydicom.dcmread(p, force=True)
        if not hasattr(ds, "PixelData") or not hasattr(ds, "ImagePositionPatient"):
            continue
        slices.append(ds)
    if not slices:
        raise ValueError("no readable CT slices with PixelData + ImagePositionPatient")
    slices.sort(key=lambda s: (float(s.ImagePositionPatient[2]), int(getattr(s, "InstanceNumber", 0))))
    vol = []
    for s in slices:
        arr = s.pixel_array.astype(np.float32)
        vol.append(arr * float(getattr(s, "RescaleSlope", 1.0)) + float(getattr(s, "RescaleIntercept", 0.0)))
    volume = np.stack(vol, axis=0).astype(np.float32)
    ref = slices[0]
    acq = {
        "manufacturer": str(getattr(ref, "Manufacturer", "")),
        "model": str(getattr(ref, "ManufacturerModelName", "")),
        "kvp": _num(getattr(ref, "KVP", None)),
        "exposure_mas": _num(getattr(ref, "Exposure", None)),
        "pitch": _num(getattr(ref, "SpiralPitchFactor", None)),
        "slice_thickness_mm": _num(getattr(ref, "SliceThickness", 0.0)) or 0.0,
        "pixel_spacing_mm": [float(x) for x in getattr(ref, "PixelSpacing", [1.0, 1.0])],
        "recon_kernel": str(_first(getattr(ref, "ConvolutionKernel", ""))),
        "image_orientation_patient": [float(x) for x in getattr(ref, "ImageOrientationPatient",
                                                                  [1, 0, 0, 0, 1, 0])],
        "patient_position": str(getattr(ref, "PatientPosition", "")),
    }
    positions = [[float(x) for x in s.ImagePositionPatient] for s in slices]
    return volume, acq, positions, ref


def demographics_from(hdr) -> Dict:
    age = getattr(hdr, "PatientAge", None)
    age_years = None
    if age and str(age).endswith("Y"):
        try:
            age_years = int(str(age)[:-1])
            if age_years > 89:
                age_years = None  # Safe Harbor age cap
        except ValueError:
            pass
    return {
        "age_years": age_years,
        "sex": str(getattr(hdr, "PatientSex", "")) or None,
        "bmi": None,
        "scan_year": None,
        "indication": None,
    }


def _num(v):
    try:
        return float(v) if v is not None and v != "" else None
    except (TypeError, ValueError):
        return None


def _first(v):
    if isinstance(v, (list, tuple, pydicom.multival.MultiValue)):
        return v[0] if len(v) else ""
    return v


class SourceAdapter(ABC):
    source: str = ""
    default_anatomy: str = "chest"

    @abstractmethod
    def iter_patients(self, input_dir: str, subset: Optional[int] = None) -> Iterator[PatientScans]:
        ...

    def reindex(self, native_id: str, registry: Dict[str, str]) -> str:
        """Assign a stable source-prefixed patient_id (the unpublished crosswalk, §4)."""
        if native_id not in registry:
            registry[native_id] = f"{self.source}-{len(registry) + 1:04d}"
        return registry[native_id]
