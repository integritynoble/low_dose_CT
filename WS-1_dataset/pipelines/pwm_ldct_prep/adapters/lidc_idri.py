"""LIDC-IDRI adapter.

Full-dose thoracic CT only (no real low-dose, no projections). The harmonized record's low-dose
images are produced by simulation downstream. One CT series per patient is selected (the thin
diagnostic series = the series with the most slices). Native four-radiologist nodule XML is
converted by a separate step (see ../schema/annotation_qa_protocol.md); not wired in the scaffold.
"""
from __future__ import annotations

import glob
import os
from typing import Dict, Iterator, Optional

from .. import lidc_annotations as la
from .base import (PatientScans, Series, SourceAdapter, canonical_patient_key, demographics_from,
                   group_dicom, read_ct_volume)


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
                canonical_key=canonical_patient_key(native_pid),
            )
            annotations = self._load_annotations(g["files"], positions, acq["pixel_spacing_mm"])
            yield PatientScans(patient_id=patient_id, fd=fd, ld=None, annotations=annotations)

    @staticmethod
    def _load_annotations(files, positions, pixel_spacing):
        """Find a LIDC reading XML alongside the series DICOMs and convert it, or return None."""
        seen = set()
        xmls = []
        for f in files:
            d = os.path.dirname(f)
            if d in seen:
                continue
            seen.add(d)
            xmls.extend(glob.glob(os.path.join(d, "*.xml")))
        if not xmls:
            return None
        from pwm_ldct_loader.annotations import consolidate_readers
        parsed = la.parse_lidc_xml(sorted(xmls)[0])
        per_reader = la.to_harmonized(parsed, positions, pixel_spacing)
        majority = consolidate_readers(per_reader)
        return {"per_reader": per_reader, "majority": majority}
