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
    sinogram: Optional[np.ndarray] = None      # [V, C, R] full-dose projections, or None
    geometry: Optional[Dict] = None
    ld_sinogram: Optional[np.ndarray] = None   # [V, C, R] low-dose projections when no LD recon (e.g. GE)
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


# --- DICOM-CT-PD projection reading (shared GE/Siemens; dicom_to_hdf5_mapping.md §3-§4) ----------
import struct

_PRIV_GROUPS = (0x7029, 0x7031, 0x7033, 0x7037, 0x7039, 0x7041)


def _decode_priv(raw):
    """Best-effort decode of a UN-VR private value: ascii string, u16, f32, or f32 list."""
    b = bytes(raw)
    stripped = b.rstrip(b"\x00 ")
    if len(stripped) >= 3 and all(32 <= c < 127 for c in stripped):
        try:
            return stripped.decode("ascii")
        except UnicodeDecodeError:
            pass
    if len(b) == 2:
        return struct.unpack("<H", b)[0]
    if len(b) == 4:
        return round(struct.unpack("<f", b)[0], 6)
    if len(b) % 4 == 0 and len(b) > 0:
        return [round(x, 4) for x in struct.unpack("<%df" % (len(b) // 4), b)]
    return b.hex()


def extract_ct_pd_geometry(hdr, n_views: int) -> Dict:
    """Decode DICOM-CT-PD acquisition geometry from a projection view header (GE & Siemens share tags)."""
    priv: Dict = {}
    for elem in hdr:
        if elem.tag.group in _PRIV_GROUPS and elem.tag.element != 0x0010:
            priv[f"{elem.tag.group:04x},{elem.tag.element:04x}"] = _decode_priv(elem.value)

    def gp(tag):
        return priv.get(tag)

    n_chan = gp("7029,1011") or int(getattr(hdr, "Rows", 0)) or None
    n_rows = gp("7029,1010") or int(getattr(hdr, "Columns", 0)) or None
    chan_pos = gp("7033,1065")
    chan_pos = chan_pos if isinstance(chan_pos, list) else None
    mfr = str(getattr(hdr, "Manufacturer", "")).strip().upper()
    return {
        "vendor": mfr.split()[0] if mfr else "",
        "detector_shape": gp("7029,100b"),
        "scan_type": gp("7037,1009"),
        "beam_geometry": gp("7037,100a"),
        "n_views": int(n_views),
        "n_det_channels": int(n_chan) if n_chan else None,
        "n_det_rows": int(n_rows) if n_rows else None,
        "views_per_rotation": gp("7033,1013"),
        "detector_channel_positions": chan_pos,
        "source_to_isocenter_mm": gp("7031,1003"),   # inferred; confirm vs data dictionary
        "source_to_detector_mm": gp("7031,1031"),    # inferred; confirm vs data dictionary
        "pitch": _num(getattr(hdr, "SpiralPitchFactor", None)),
        "kvp": _num(getattr(hdr, "KVP", None)),
        "data_collection_diameter_mm": _num(getattr(hdr, "DataCollectionDiameter", None)),
        # keep only scalars + short arrays verbatim (drop the long per-channel array, kept above)
        "raw_private_geometry": {k: v for k, v in priv.items()
                                 if not (isinstance(v, list) and len(v) > 16)},
        "calibration_status": ("private tags decoded; exact source/detector-distance and "
                               "channel-angle semantics require the DICOM-CT-PD data dictionary"),
    }


def read_projection_series(files: List[str]):
    """Read a DICOM-CT-PD projection series into native ``[V, C, R]`` line integrals + geometry.

    One DICOM object per view (SOP class Raw Data Storage); views ordered by InstanceNumber.
    """
    hdrs = []
    for p in files:
        ds = pydicom.dcmread(p, force=True)
        if not hasattr(ds, "PixelData"):
            continue
        hdrs.append((int(getattr(ds, "InstanceNumber", 0)), ds))
    if not hdrs:
        raise ValueError("no projection views with PixelData")
    hdrs.sort(key=lambda t: t[0])
    views = []
    for _, ds in hdrs:
        arr = ds.pixel_array.astype(np.float32)
        views.append(arr * float(getattr(ds, "RescaleSlope", 1.0)) + float(getattr(ds, "RescaleIntercept", 0.0)))
    sino = np.stack(views, axis=0).astype(np.float32)  # [V, C, R]
    geom = extract_ct_pd_geometry(hdrs[0][1], n_views=len(views))
    return sino, geom


class SourceAdapter(ABC):
    source: str = ""
    default_anatomy: str = "chest"

    @abstractmethod
    def iter_patients(self, input_dir: str, subset: Optional[int] = None) -> Iterator[PatientScans]:
        ...

    def reindex(self, native_id: str, registry: Dict[str, str]) -> str:
        """Assign a stable source-prefixed patient_id (the unpublished crosswalk, §4).

        If ``self.id_map`` is set (a precomputed native->assigned crosswalk) it takes precedence,
        so chunked/per-patient prep runs produce consistent IDs; otherwise IDs are assigned by
        insertion order within the run.
        """
        idmap = getattr(self, "id_map", None)
        if idmap and native_id in idmap:
            return idmap[native_id]
        if native_id not in registry:
            registry[native_id] = f"{self.source}-{len(registry) + 1:04d}"
        return registry[native_id]
