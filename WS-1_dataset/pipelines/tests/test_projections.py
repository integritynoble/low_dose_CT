"""End-to-end projection path: synthetic Mayo-style DICOM-CT-PD -> prep --with-sinograms ->
validate() -> series-level projections + geometry loadable.

Builds a Mayo patient with Full/Low Dose Images (recon) + Full/Low Dose Projections (DICOM-CT-PD
views carrying the shared GE/Siemens private geometry tags), then drives the real pipeline.
"""
import struct

import numpy as np
import pydicom
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import CTImageStorage, ExplicitVRLittleEndian, generate_uid

from pwm_ldct_loader import LowDoseCTDataset, validate
from pwm_ldct_prep.cli import main as prep_main

RAW_DATA_STORAGE = "1.2.840.10008.5.1.4.1.1.66"
NC, NR, NVIEWS = 5, 4, 3   # detector channels, rows; projection views


def _common(ds, patient, study, series, desc, manufacturer):
    fm = FileMetaDataset()
    fm.MediaStorageSOPInstanceUID = generate_uid()
    fm.TransferSyntaxUID = ExplicitVRLittleEndian
    ds.file_meta = fm
    ds.SOPInstanceUID = fm.MediaStorageSOPInstanceUID
    ds.PatientID = patient
    ds.PatientName = patient
    ds.PatientSex = "M"
    ds.Modality = "CT"
    ds.StudyInstanceUID = study
    ds.SeriesInstanceUID = series
    ds.SeriesDescription = desc
    ds.BodyPartExamined = "ABDOMEN"
    ds.Manufacturer = manufacturer
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated = 16
    ds.HighBit = 15


def _write_recon_slice(path, patient, study, series, desc, z, manufacturer):
    ds = Dataset()
    fm = FileMetaDataset()
    fm.MediaStorageSOPClassUID = CTImageStorage
    ds.file_meta = fm
    _common(ds, patient, study, series, desc, manufacturer)
    ds.file_meta.MediaStorageSOPClassUID = CTImageStorage
    ds.SOPClassUID = CTImageStorage
    ds.ManufacturerModelName = "SOMATOM"
    ds.KVP = 120
    ds.ConvolutionKernel = "B30f"
    ds.SliceThickness = 1.0
    ds.PixelSpacing = [0.7, 0.7]
    ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
    ds.ImagePositionPatient = [0.0, 0.0, float(z)]
    ds.PatientPosition = "FFS"
    ds.InstanceNumber = z + 1
    ds.Rows, ds.Columns = 8, 8
    ds.BitsStored = 16
    ds.PixelRepresentation = 1
    ds.RescaleIntercept = -1024
    ds.RescaleSlope = 1
    ds.PixelData = np.random.default_rng(z).integers(0, 2000, (8, 8), dtype=np.int16).tobytes()
    ds.save_as(path, enforce_file_format=True)


def _write_projection_view(path, patient, study, series, desc, view, manufacturer):
    ds = Dataset()
    fm = FileMetaDataset()
    fm.MediaStorageSOPClassUID = RAW_DATA_STORAGE
    ds.file_meta = fm
    _common(ds, patient, study, series, desc, manufacturer)
    ds.SOPClassUID = RAW_DATA_STORAGE
    ds.InstanceNumber = view + 1
    ds.KVP = 120
    ds.SpiralPitchFactor = 0.9
    ds.DataCollectionDiameter = 500
    ds.Rows, ds.Columns = NC, NR
    ds.BitsStored = 16
    ds.PixelRepresentation = 0
    ds.RescaleSlope = 0.001
    ds.RescaleIntercept = -0.1
    ds.PixelData = np.random.default_rng(100 + view).integers(0, 5000, (NC, NR), dtype=np.uint16).tobytes()
    # shared DICOM-CT-PD private geometry tags (UN VR, little-endian)
    ds.add_new(pydicom.tag.Tag(0x7029, 0x1011), "UN", struct.pack("<H", NC))   # channels
    ds.add_new(pydicom.tag.Tag(0x7029, 0x1010), "UN", struct.pack("<H", NR))   # rows
    ds.add_new(pydicom.tag.Tag(0x7029, 0x100B), "UN", b"CYLINDRICAL ")
    ds.add_new(pydicom.tag.Tag(0x7037, 0x1009), "UN", b"HELICAL ")
    ds.add_new(pydicom.tag.Tag(0x7037, 0x100A), "UN", b"FANBEAM ")
    ds.add_new(pydicom.tag.Tag(0x7033, 0x1013), "UN", struct.pack("<H", 12))   # views/rotation
    ds.add_new(pydicom.tag.Tag(0x7031, 0x1003), "UN", struct.pack("<f", 595.0))     # SID
    ds.add_new(pydicom.tag.Tag(0x7031, 0x1031), "UN", struct.pack("<f", 1085.6))    # SDD
    ds.add_new(pydicom.tag.Tag(0x7033, 0x1065), "UN", struct.pack("<%df" % NC, *range(NC)))
    ds.save_as(path, enforce_file_format=True)


def _build_mayo_patient(root, manufacturer="SIEMENS", pid="L999", with_ld_image=True):
    study = generate_uid()
    series = {k: generate_uid() for k in ("fdi", "ldi", "fdp", "ldp")}
    d = root / pid
    d.mkdir(parents=True)
    for z in range(2):
        _write_recon_slice(str(d / f"fdi_{z}.dcm"), pid, study, series["fdi"], "Full Dose Images", z, manufacturer)
        if with_ld_image:   # GE patients lack a reconstructed Low Dose Images series
            _write_recon_slice(str(d / f"ldi_{z}.dcm"), pid, study, series["ldi"], "Low Dose Images", z, manufacturer)
    for v in range(NVIEWS):
        _write_projection_view(str(d / f"fdp_{v}.dcm"), pid, study, series["fdp"], "Full Dose Projections", v, manufacturer)
        _write_projection_view(str(d / f"ldp_{v}.dcm"), pid, study, series["ldp"], "Low Dose Projections", v, manufacturer)


def test_projection_pipeline(tmp_path):
    raw = tmp_path / "mayo_raw"
    _build_mayo_patient(raw, manufacturer="SIEMENS")
    out = str(tmp_path / "pwm_ldct_v0_5")

    assert prep_main(["prep", "--source", "mayo", "--input", str(raw), "--output", out,
                      "--seed", "42", "--with-sinograms"]) == 0
    assert prep_main(["finalize", "--output", out]) == 0

    report = validate(out)
    assert report.ok, report.errors
    assert report.n_series == 1   # one fd series (ld real-LD folds into the fd HDF5)

    # locate the series across splits
    found = None
    for split in ("train", "val", "test"):
        d = LowDoseCTDataset(root=out, split=split, backend="numpy")
        for i in range(len(d)):
            s = d[i]
            assert s["source"] == "mayo"
            assert s["has_projections"]          # projections present for this series
            assert s["low_dose_kind"] == "real"  # real low-dose recon present
            found = (d, s["series_id"])
    assert found is not None
    d, sid = found
    proj = d.get_series_projections(sid)
    assert proj is not None
    assert proj["full_dose"].shape == (NVIEWS, NC, NR)        # native [V, C, R]
    assert proj["low_dose_real"].shape == (NVIEWS, NC, NR)
    g = proj["geometry"]
    assert g["vendor"] == "SIEMENS"
    assert g["n_det_channels"] == NC and g["n_det_rows"] == NR
    assert g["detector_shape"] == "CYLINDRICAL" and g["scan_type"] == "HELICAL"
    assert g["source_to_isocenter_mm"] == 595.0
    assert len(g["detector_channel_positions"]) == NC


def test_ge_no_ld_image_captures_ld_projection_and_id_map(tmp_path):
    """GE patients have no Low Dose Images recon; their LD projection must still be captured,
    and the --id-map crosswalk must drive the patient_id (chunk-safe)."""
    import json
    raw = tmp_path / "ge_raw"
    _build_mayo_patient(raw, manufacturer="GE", pid="C001", with_ld_image=False)
    out = str(tmp_path / "pwm_ldct_v0_5")
    id_map = tmp_path / "idmap.json"
    id_map.write_text(json.dumps({"C001": "mayo-0042"}))

    assert prep_main(["prep", "--source", "mayo", "--input", str(raw), "--output", out,
                      "--seed", "42", "--with-sinograms", "--id-map", str(id_map)]) == 0
    assert prep_main(["finalize", "--output", out]) == 0
    assert validate(out).ok

    found = None
    for split in ("train", "val", "test"):
        d = LowDoseCTDataset(root=out, split=split, backend="numpy")
        for i in range(len(d)):
            s = d[i]
            assert s["patient_id"] == "mayo-0042"      # id-map honored
            assert s["low_dose_kind"] == "sim"          # no LD recon image for GE -> simulated
            assert s["has_projections"]
            found = (d, s["series_id"])
    assert found is not None
    d, sid = found
    proj = d.get_series_projections(sid)
    assert proj["full_dose"].shape == (NVIEWS, NC, NR)
    # the GE low-dose PROJECTION is captured even without an LD recon image
    assert proj["low_dose_real"] is not None
    assert proj["low_dose_real"].shape == (NVIEWS, NC, NR)
    assert proj["geometry"]["vendor"] == "GE"
