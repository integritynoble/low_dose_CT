"""Mayo LDCT-and-Projection-Data adapter.

Siemens paired-dose projection dataset (chest + abdomen). The public portion is staged at
``gs://low-dose-ct/ldct_and_projection_data`` as one UUID folder per series; each folder's
DICOM headers carry the SeriesDescription / BodyPartExamined / PatientID this adapter keys on.
"""
from __future__ import annotations

from ._siemens import SiemensPairedAdapter


class MayoLdctPdAdapter(SiemensPairedAdapter):
    source = "mayo"
    default_anatomy = "abdomen"  # collection skews abdomen; per-scan BodyPartExamined still wins
