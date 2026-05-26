"""LIDC-IDRI adapter.

Full-dose thoracic CT only (no real low-dose, no projections). The harmonized record's low-dose
images are produced by simulation downstream. One CT series per patient is selected (the thin
diagnostic series = the series with the most slices). Native four-radiologist nodule XML is
converted by a separate step (see ../schema/annotation_qa_protocol.md); not wired in the scaffold.
"""
from __future__ import annotations

from typing import Dict, Iterator, Optional

from .base import (PatientScans, Series, SourceAdapter, demographics_from, group_dicom,
                   read_ct_volume)


class LidcIdriAdapter(SourceAdapter):
    source = "lidc"
    default_anatomy = "chest"

    def iter_patients(self, input_dir: str, subset: Optional[int] = None) -> Iterator[PatientScans]:
        groups = group_dicom(input_dir)
        # bucket CT series by native PatientID; keep the largest series per patient
        by_patient: Dict[str, list] = {}
        for suid, g in groups.items():
            hdr = g["header"]
            if str(getattr(hdr, "Modality", "")) != "CT":
                continue
            pid = str(getattr(hdr, "PatientID", "unknown"))
            by_patient.setdefault(pid, []).append((len(g["files"]), suid, g))

        registry: Dict[str, str] = {}
        for n, (native_pid, series_list) in enumerate(sorted(by_patient.items())):
            if subset is not None and n >= subset:
                break
            _, suid, g = max(series_list, key=lambda t: t[0])  # most slices = thin diagnostic series
            volume, acq, positions, ref = read_ct_volume(g["files"])
            patient_id = self.reindex(native_pid, registry)
            anatomy = self.default_anatomy
            fd = Series(
                patient_id=patient_id,
                series_id=f"{patient_id}_{anatomy}_fd",
                source=self.source,
                anatomy=anatomy,
                role="fd",
                volume_hu=volume,
                acquisition=acq,
                slice_positions=positions,
                demographics=demographics_from(ref),
                src_uids={"series": suid, "study": str(getattr(ref, "StudyInstanceUID", ""))},
            )
            yield PatientScans(patient_id=patient_id, fd=fd, ld=None)
