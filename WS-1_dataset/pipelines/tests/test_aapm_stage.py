"""AAPM 2016 staging + path-based adapter discovery.

The real AAPM/Box data is Siemens .IMA with PatientID='Anonymous' and no SeriesDescription;
dose/domain/patient/recon live only in the path. These tests build a tiny synthetic tree in that
exact layout and prove (a) classify_aapm_path decodes it, (b) extract_zip subsets by patient, and
(c) the adapter anchors on the FD recon, de-dups via the L### canonical key, prefers 1mm/B30, and
skips QD-only ("testing") patients.
"""
import os
import zipfile

import numpy as np
import pydicom
import pytest
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import CTImageStorage, ExplicitVRLittleEndian, generate_uid

from pwm_ldct_prep.adapters import get_adapter
from pwm_ldct_prep.adapters.base import canonical_patient_key
from pwm_ldct_prep.stage import classify_aapm_path, extract_zip

ROWS = COLS = 8


def _write_ima(path, z):
    """Write a minimal CT slice (PatientID intentionally 'Anonymous', no SeriesDescription)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fm = FileMetaDataset()
    fm.MediaStorageSOPClassUID = CTImageStorage
    fm.MediaStorageSOPInstanceUID = generate_uid()
    fm.TransferSyntaxUID = ExplicitVRLittleEndian
    ds = Dataset()
    ds.file_meta = fm
    ds.SOPClassUID = CTImageStorage
    ds.SOPInstanceUID = fm.MediaStorageSOPInstanceUID
    ds.PatientID = "Anonymous"            # exactly as in the real AAPM data
    ds.Modality = "CT"
    ds.StudyInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.BodyPartExamined = "ABDOMEN"
    ds.Manufacturer = "SIEMENS"
    ds.ManufacturerModelName = "SOMATOM Definition AS+"
    ds.KVP = 120
    ds.ConvolutionKernel = "B30f"
    ds.SliceThickness = 1.0
    ds.PixelSpacing = [0.7, 0.7]
    ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
    ds.ImagePositionPatient = [0.0, 0.0, float(z)]
    ds.PatientPosition = "HFS"
    ds.InstanceNumber = z + 1
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.Rows = ROWS
    ds.Columns = COLS
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 1
    ds.RescaleIntercept = -1024
    ds.RescaleSlope = 1
    ds.PixelData = np.full((ROWS, COLS), 1000 + z, dtype=np.int16).tobytes()
    ds.save_as(path, enforce_file_format=True)


def test_classify_real_paths():
    # full-dose 1mm B30 image slice
    c = classify_aapm_path("Training_Image_Data/1mm B30/FD_1mm/L067/full_1mm/L067_FD_1_1.CT.0001.IMA")
    assert (c["patient"], c["role"], c["domain"], c["recon"]) == ("L067", "fd", "image", "1mm_b30")
    # quarter-dose 3mm sharp image
    c = classify_aapm_path("Testing_Image_Data/3mm D45/QD_3mm_sharp/L554/quarter_3mm/L554_QD_3_1.IMA")
    assert (c["patient"], c["role"], c["domain"], c["kernel"]) == ("L554", "ld", "image", "d45")
    # full-dose projections (note: 'PD' must not be read as a dose token)
    c = classify_aapm_path("Training_Projection_Data/L096/DICOM-CT-PD_FD/proj.0001.dcm")
    assert (c["patient"], c["role"], c["domain"], c["recon"]) == ("L096", "fd", "projection", "")
    c = classify_aapm_path("Testing_Projection_Data/L008/DICOM-CT-PD_QD/proj.0001.dcm")
    assert (c["patient"], c["role"], c["domain"]) == ("L008", "ld", "projection")


def test_extract_zip_patient_subset(tmp_path):
    # a multi-patient image zip
    src = tmp_path / "src"
    for pid in ("L067", "L096"):
        for z in range(2):
            _write_ima(str(src / pid / "full_1mm" / f"{pid}_FD_1_1.{z}.IMA"), z)
    zpath = tmp_path / "FD_1mm.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        for root, _, files in os.walk(src):
            for f in files:
                full = os.path.join(root, f)
                zf.write(full, os.path.relpath(full, src))
    dest = tmp_path / "out"
    n = extract_zip(str(zpath), str(dest), patients=["L067"])
    assert n == 2  # only L067's two slices
    got = [p for _, _, fs in os.walk(dest) for p in fs]
    assert len(got) == 2 and all("L067" in p for p in got)


@pytest.fixture()
def staged_aapm(tmp_path):
    """Synthetic staged tree: L067 = paired FD+QD (training); L554 = QD-only (testing)."""
    root = tmp_path / "aapm_staged"
    # L067 — full + quarter, two recons (1mm B30 preferred, 3mm D45 alternate)
    for role, dosefolder in (("FD", "full"), ("QD", "quarter")):
        for kern, thick in (("1mm B30", "1mm"), ("3mm D45", "3mm")):
            base = root / f"Training_Image_Data/{kern}/{role}_{thick}/L067/{dosefolder}_{thick}"
            for z in range(3):
                _write_ima(str(base / f"L067_{role}_{thick}.{z}.IMA"), z)
    # L554 — quarter only (no FD anchor -> must be skipped)
    for z in range(3):
        _write_ima(str(root / "Testing_Image_Data/1mm B30/QD_1mm/L554/quarter_1mm" /
                       f"L554_QD_1.{z}.IMA"), z)
    return str(root)


def test_adapter_discovery(staged_aapm):
    adapter = get_adapter("aapm")
    patients = list(adapter.iter_patients(staged_aapm))
    # only L067 anchors (has FD image); L554 (QD-only) is skipped
    assert len(patients) == 1
    ps = patients[0]
    assert ps.fd is not None and ps.ld is not None
    assert ps.fd.source == "aapm" and ps.fd.role == "fd" and ps.ld.role == "ld"
    assert ps.fd.anatomy == "abdomen"
    assert ps.fd.volume_hu.shape[0] == 3  # preferred 1mm recon's 3 slices, not the 3mm one
    # canonical key derives from the path L### (not the 'Anonymous' tag)
    assert ps.fd.canonical_key == canonical_patient_key("L067")
    assert ps.fd.canonical_key == ps.ld.canonical_key
    # harmonized id is source-prefixed
    assert ps.patient_id.startswith("aapm-")
