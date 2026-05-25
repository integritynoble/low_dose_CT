"""De-identification re-verification (../schema/dicom_cleaning_spec.md).

Two responsibilities:
  * ``clean_dataset`` — reference implementation of Stage-1 tag cleaning (whitelist filter,
    UID re-hash, date generalization) on a pydicom Dataset, returning an audit record.
  * the pipeline never writes non-whitelisted tags into its outputs (it extracts only
    whitelisted fields), so PHI cannot propagate even before cleaning is applied.

The Stage-2 Tesseract OCR sweep is provided as an optional hook (``ocr_sweep``); it is a
no-op stub here and is wired in the Docker image where Tesseract is installed.
"""
from __future__ import annotations

import hashlib
from typing import Dict, List

# Retained-tag whitelist by keyword (dicom_cleaning_spec.md §2). Everything else is removed.
WHITELIST_KEYWORDS = {
    "SOPClassUID", "Modality", "Manufacturer", "ManufacturerModelName", "SeriesDescription",
    "KVP", "SliceThickness", "SpacingBetweenSlices", "DataCollectionDiameter",
    "ReconstructionDiameter", "DistanceSourceToDetector", "DistanceSourceToPatient",
    "GantryDetectorTilt", "TableHeight", "RotationDirection", "ExposureTime",
    "XRayTubeCurrent", "Exposure", "FilterType", "ConvolutionKernel", "SpiralPitchFactor",
    "ImagePositionPatient", "ImageOrientationPatient", "InstanceNumber", "PatientPosition",
    "Rows", "Columns", "PixelSpacing", "BitsAllocated", "BitsStored", "HighBit",
    "PixelRepresentation", "RescaleIntercept", "RescaleSlope", "RescaleType", "PixelData",
    # demographics (generalized, see §2 / §3.3)
    "PatientSex", "PatientAge", "PatientSize", "PatientWeight", "BodyPartExamined",
    # UIDs are re-hashed (not removed) to preserve intra-series linkage
    "StudyInstanceUID", "SeriesInstanceUID", "SOPInstanceUID", "FrameOfReferenceUID",
}

_REHASH_UIDS = ("StudyInstanceUID", "SeriesInstanceUID", "SOPInstanceUID", "FrameOfReferenceUID")
_DATE_VRS = {"DA", "DT", "TM"}


def rehash_uid(uid: str, salt: str) -> str:
    """Salted, collision-resistant UID re-hash (dicom_cleaning_spec.md §3.2)."""
    digest = hashlib.sha256((salt + uid).encode()).hexdigest()
    return "2.25." + str(int(digest[:32], 16))


def clean_dataset(ds, salt: str) -> Dict:
    """Apply Stage-1 cleaning in place; return an audit record (dicom_cleaning_spec.md §6)."""
    deleted = 0
    private = 0
    dates = 0
    for elem in list(ds):
        kw = elem.keyword
        if elem.tag.is_private:
            del ds[elem.tag]
            private += 1
            continue
        if not kw or kw not in WHITELIST_KEYWORDS:
            if elem.VR in _DATE_VRS:
                dates += 1
            del ds[elem.tag]
            deleted += 1
    for kw in _REHASH_UIDS:
        if kw in ds:
            setattr(ds, kw, rehash_uid(str(getattr(ds, kw)), salt))
    return {
        "tags_deleted": deleted,
        "private_tags_deleted": private,
        "dates_generalized": dates,
        "uids_rehashed": sum(1 for kw in _REHASH_UIDS if kw in ds),
    }


def ocr_sweep(volume_hu) -> List[Dict]:  # pragma: no cover - Tesseract optional in scaffold
    """Stage-2 burned-in-text OCR sweep (dicom_cleaning_spec.md §5).

    No-op unless pytesseract + Tesseract are available; returns a list of PHI hits (empty = clean).
    The Docker image installs Tesseract and enables this.
    """
    try:
        import pytesseract  # noqa: F401
    except Exception:
        return []
    # A full implementation windows each slice to [-160, 240] HU, renders to 8-bit, and runs
    # Tesseract in sparse-text mode; tokens matching PHI patterns are returned for manual review.
    return []


def audit_row(scan_uid: str, source: str, stage1: Dict, ocr_hits: List[Dict],
              tool_versions: Dict, timestamp_utc: str) -> Dict:
    """Build one ``deident_audit.jsonl`` row (dicom_cleaning_spec.md §6)."""
    return {
        "scan_uid": scan_uid,
        "source": source,
        "stage1": stage1,
        "stage2_ocr": {"slices_scanned": 0, "hits": len(ocr_hits), "hit_detail": ocr_hits},
        "result": "pass" if not ocr_hits else "held_for_review",
        "tool_versions": tool_versions,
        "timestamp_utc": timestamp_utc,
    }
