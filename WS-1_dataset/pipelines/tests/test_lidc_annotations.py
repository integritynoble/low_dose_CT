"""LIDC annotation path: synthetic LidcReadMessage XML + recon DICOM -> prep ->
majority-vote + raw-per-reader files written, consolidated correctly, and slice-attached.
"""
import json
import os

import numpy as np
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import CTImageStorage, ExplicitVRLittleEndian, generate_uid

from pwm_ldct_loader import LowDoseCTDataset, validate
from pwm_ldct_loader.splits import assign_split
from pwm_ldct_prep.cli import main as prep_main

LIDC_XML = """<?xml version="1.0" encoding="UTF-8"?>
<LidcReadMessage xmlns="http://www.nih.gov">
  <ResponseHeader><SeriesInstanceUid>1.2.3</SeriesInstanceUid></ResponseHeader>
  <readingSession>
    <servicingRadiologistID>R1</servicingRadiologistID>
    <unblindedReadNodule>
      <noduleID>N1</noduleID>
      <characteristics><texture>5</texture><malignancy>3</malignancy></characteristics>
      <roi>
        <imageZposition>1.0</imageZposition><imageSOP_UID>s1</imageSOP_UID><inclusion>TRUE</inclusion>
        <edgeMap><xCoord>10</xCoord><yCoord>10</yCoord></edgeMap>
        <edgeMap><xCoord>20</xCoord><yCoord>10</yCoord></edgeMap>
        <edgeMap><xCoord>20</xCoord><yCoord>20</yCoord></edgeMap>
        <edgeMap><xCoord>10</xCoord><yCoord>20</yCoord></edgeMap>
      </roi>
    </unblindedReadNodule>
  </readingSession>
  <readingSession>
    <servicingRadiologistID>R2</servicingRadiologistID>
    <unblindedReadNodule>
      <noduleID>N1b</noduleID>
      <characteristics><texture>5</texture><malignancy>4</malignancy></characteristics>
      <roi>
        <imageZposition>1.0</imageZposition><imageSOP_UID>s1</imageSOP_UID><inclusion>TRUE</inclusion>
        <edgeMap><xCoord>11</xCoord><yCoord>11</yCoord></edgeMap>
        <edgeMap><xCoord>21</xCoord><yCoord>11</yCoord></edgeMap>
        <edgeMap><xCoord>21</xCoord><yCoord>21</yCoord></edgeMap>
        <edgeMap><xCoord>11</xCoord><yCoord>21</yCoord></edgeMap>
      </roi>
    </unblindedReadNodule>
  </readingSession>
</LidcReadMessage>
"""


def _write_recon_slice(path, patient, study, series, z):
    ds = Dataset()
    fm = FileMetaDataset()
    fm.MediaStorageSOPClassUID = CTImageStorage
    fm.MediaStorageSOPInstanceUID = generate_uid()
    fm.TransferSyntaxUID = ExplicitVRLittleEndian
    ds.file_meta = fm
    ds.SOPClassUID = CTImageStorage
    ds.SOPInstanceUID = fm.MediaStorageSOPInstanceUID
    ds.PatientID = patient
    ds.PatientName = patient
    ds.Modality = "CT"
    ds.StudyInstanceUID = study
    ds.SeriesInstanceUID = series
    ds.SeriesDescription = "Diagnostic CT"
    ds.BodyPartExamined = "CHEST"
    ds.Manufacturer = "GE"
    ds.ConvolutionKernel = "STANDARD"
    ds.SliceThickness = 1.0
    ds.PixelSpacing = [0.7, 0.7]
    ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
    ds.ImagePositionPatient = [0.0, 0.0, float(z)]
    ds.PatientPosition = "FFS"
    ds.InstanceNumber = z + 1
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.Rows, ds.Columns = 32, 32
    ds.BitsAllocated, ds.BitsStored, ds.HighBit = 16, 16, 15
    ds.PixelRepresentation = 1
    ds.RescaleIntercept, ds.RescaleSlope = -1024, 1
    ds.PixelData = np.random.default_rng(z).integers(0, 2000, (32, 32), dtype=np.int16).tobytes()
    ds.save_as(path, enforce_file_format=True)


def _build_lidc_patient(root):
    pid = "LIDC-IDRI-0007"
    study, series = generate_uid(), generate_uid()
    d = root / pid
    d.mkdir(parents=True)
    for z in range(3):                       # slices at z = 0, 1, 2 mm
        _write_recon_slice(str(d / f"{z}.dcm"), pid, study, series, z)
    (d / "069.xml").write_text(LIDC_XML)     # reading XML alongside the DICOMs
    return pid


def test_lidc_annotation_conversion(tmp_path):
    raw = tmp_path / "lidc_raw"
    _build_lidc_patient(raw)
    out = str(tmp_path / "pwm_ldct_v0_5")

    assert prep_main(["prep", "--source", "lidc", "--input", str(raw), "--output", out, "--seed", "42"]) == 0
    assert prep_main(["finalize", "--output", out]) == 0
    assert validate(out).ok

    # majority-vote file: one consolidated nodule on slice 1, texture 5, from 2 readers
    mv = json.load(open(os.path.join(out, "annotations", "lidc_majority_vote", "lidc-0001.json")))
    assert len(mv["nodules"]) == 1
    nod = mv["nodules"][0]
    assert nod["slice_index"] == 1                      # z=1.0 -> slice index 1
    assert nod["ground_truth"] == "majority_vote"
    assert nod["n_contributing_readers"] == 2
    assert nod["texture"] == 5
    assert abs(nod["diameter_mm"] - 7.0) < 0.5          # ~10 px * 0.7 mm

    # raw-per-reader: two reader files preserved
    raw_dir = os.path.join(out, "annotations", "raw_per_reader", "lidc-0001")
    assert sorted(os.listdir(raw_dir)) == ["R1.json", "R2.json"]

    # loader attaches the nodule to slice 1 and nothing to slices 0/2
    split = assign_split("lidc-0001", 42)
    ds = LowDoseCTDataset(root=out, split=split, backend="numpy")
    by_z = {ds[i]["slice_index"]: ds[i] for i in range(len(ds))}
    assert len(by_z[1]["annotations"]["nodules"]) == 1
    assert len(by_z[0]["annotations"]["nodules"]) == 0
    assert len(by_z[2]["annotations"]["nodules"]) == 0
