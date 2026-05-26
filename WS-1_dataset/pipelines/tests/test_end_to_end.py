"""End-to-end: synthetic CT DICOM -> prep -> finalize -> validate() passes -> loadable.

Exercises the reconstructed-image path (LIDC-style: image-only, simulated low-dose) without any
real data, proving the pipeline emits a schema-conformant tree.
"""
import os

import numpy as np
import pydicom
import pytest
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import CTImageStorage, ExplicitVRLittleEndian, generate_uid

from pwm_ldct_loader import LowDoseCTDataset, validate
from pwm_ldct_loader.splits import assign_split
from pwm_ldct_prep.cli import main as prep_main

ROWS = COLS = 16


def _write_slice(path, patient_id, study_uid, series_uid, z, rows=ROWS, cols=COLS):
    fm = FileMetaDataset()
    fm.MediaStorageSOPClassUID = CTImageStorage
    fm.MediaStorageSOPInstanceUID = generate_uid()
    fm.TransferSyntaxUID = ExplicitVRLittleEndian
    ds = Dataset()
    ds.file_meta = fm
    ds.SOPClassUID = CTImageStorage
    ds.SOPInstanceUID = fm.MediaStorageSOPInstanceUID
    ds.PatientID = patient_id
    ds.PatientName = "ANON^TEST"          # PHI: must not survive into outputs
    ds.PatientSex = "M"
    ds.PatientAge = "060Y"
    ds.Modality = "CT"
    ds.StudyInstanceUID = study_uid
    ds.SeriesInstanceUID = series_uid
    ds.SeriesDescription = "Standard Full Dose"
    ds.BodyPartExamined = "CHEST"
    ds.Manufacturer = "SIEMENS"
    ds.ManufacturerModelName = "SOMATOM"
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
    ds.Rows = rows
    ds.Columns = cols
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 1
    ds.RescaleIntercept = -1024
    ds.RescaleSlope = 1
    rng = np.random.default_rng(z)
    ds.PixelData = rng.integers(0, 2000, size=(rows, cols), dtype=np.int16).tobytes()
    ds.save_as(path, enforce_file_format=True)


@pytest.fixture()
def raw_lidc(tmp_path):
    root = tmp_path / "lidc_raw"
    for pnum in (1, 2):
        pid = f"LIDC-IDRI-{pnum:04d}"
        study, series = generate_uid(), generate_uid()
        d = root / pid
        d.mkdir(parents=True)
        for z in range(3):
            _write_slice(str(d / f"{z}.dcm"), pid, study, series, z)
    return str(root)


def test_prep_finalize_validate(raw_lidc, tmp_path):
    out = str(tmp_path / "pwm_ldct_v0_5")
    assert prep_main(["prep", "--source", "lidc", "--input", raw_lidc, "--output", out, "--seed", "42"]) == 0
    assert prep_main(["finalize", "--output", out]) == 0

    report = validate(out)
    assert report.ok, report.errors
    assert report.n_series == 2
    assert report.n_patients == 2


def test_no_phi_in_outputs(raw_lidc, tmp_path):
    out = str(tmp_path / "pwm_ldct_v0_5")
    prep_main(["prep", "--source", "lidc", "--input", raw_lidc, "--output", out, "--seed", "42"])
    prep_main(["finalize", "--output", out])
    # PatientName and native PatientID must not appear anywhere in the deposited tree
    leaked = []
    for base, _, files in os.walk(out):
        for fn in files:
            blob = open(os.path.join(base, fn), "rb").read()
            if b"ANON^TEST" in blob or b"LIDC-IDRI-0001" in blob:
                leaked.append(fn)
    assert leaked == [], f"PHI leaked into: {leaked}"


def test_loadable_and_contract(raw_lidc, tmp_path):
    out = str(tmp_path / "pwm_ldct_v0_5")
    prep_main(["prep", "--source", "lidc", "--input", raw_lidc, "--output", out, "--seed", "42"])
    prep_main(["finalize", "--output", out])

    total = 0
    for split in ("train", "val", "test"):
        ds = LowDoseCTDataset(root=out, split=split, backend="numpy")
        for i in range(len(ds)):
            s = ds[i]
            assert s["full_dose"].shape == (ROWS, COLS)
            assert s["source"] == "lidc"
            assert s["low_dose_kind"] == "sim"      # LIDC has no real low-dose
            assert s["sinogram"] is None            # LIDC is image-only
            total += 1
    assert total == 2 * 3  # 2 patients x 3 slices


def test_split_placement_matches_assign(raw_lidc, tmp_path):
    out = str(tmp_path / "pwm_ldct_v0_5")
    prep_main(["prep", "--source", "lidc", "--input", raw_lidc, "--output", out, "--seed", "42"])
    for pnum in (1, 2):
        pid = f"lidc-{pnum:04d}"
        split = assign_split(pid, 42)
        assert os.path.isdir(os.path.join(out, "hdf5", split, "lidc", pid))
