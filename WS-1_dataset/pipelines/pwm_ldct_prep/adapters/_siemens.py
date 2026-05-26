"""Shared adapter for the Siemens paired-dose projection datasets (AAPM 2016, Mayo LDCT-PD).

Both distribute, per patient, four series identified by SeriesDescription:
``Full/Low Dose Images`` (reconstructed) and ``Full/Low Dose Projections`` (DICOM-CT-PD sinograms).
The reconstructed-image path is fully implemented; projection reading is a documented hook.
"""
from __future__ import annotations

import os
from typing import Dict, Iterator, Optional

import numpy as np

from .base import (PatientScans, Series, SourceAdapter, demographics_from, group_dicom,
                   read_ct_volume, read_projection_series)


def _classify(series_desc: str):
    """Return (role, domain) from a SeriesDescription, or None if unrecognized."""
    d = series_desc.lower()
    role = "fd" if "full" in d else ("ld" if "low" in d else None)
    if role is None:
        return None
    domain = "image" if "image" in d else ("projection" if "projection" in d else None)
    if domain is None:
        return None
    return role, domain


def _anatomy_of(hdr) -> str:
    bp = str(getattr(hdr, "BodyPartExamined", "")).upper()
    return "abdomen" if "ABDOMEN" in bp or "LIVER" in bp else "chest"


class SiemensPairedAdapter(SourceAdapter):
    with_sinograms = False  # projection parsing is opt-in; see read_projections

    def iter_patients(self, input_dir: str, subset: Optional[int] = None) -> Iterator[PatientScans]:
        groups = group_dicom(input_dir)
        # bucket series by native PatientID, then by (role, domain)
        patients: Dict[str, Dict] = {}
        for suid, g in groups.items():
            hdr = g["header"]
            cls = _classify(str(getattr(hdr, "SeriesDescription", "")))
            if cls is None:
                continue
            role, domain = cls
            pid = str(getattr(hdr, "PatientID", "unknown"))
            patients.setdefault(pid, {})[(role, domain)] = (suid, g)

        registry: Dict[str, str] = {}
        for n, (native_pid, series_map) in enumerate(sorted(patients.items())):
            if subset is not None and n >= subset:
                break
            if ("fd", "image") not in series_map:
                continue  # need a full-dose reconstruction to anchor the record
            patient_id = self.reindex(native_pid, registry)
            fd = self._build(series_map[("fd", "image")], patient_id, "fd")
            ld = self._build(series_map[("ld", "image")], patient_id, "ld") if ("ld", "image") in series_map else None
            if self.with_sinograms:
                self._attach_projections(fd, series_map.get(("fd", "projection")))
                ld_proj = series_map.get(("ld", "projection"))
                if ld is not None:
                    self._attach_projections(ld, ld_proj)
                elif ld_proj is not None:
                    # GE: low-dose projections exist but no LD reconstructed image; keep the
                    # low-dose projection on the fd record (-> sinogram/low_dose_real).
                    fd.ld_sinogram, _ = read_projection_series(ld_proj[1]["files"])
            yield PatientScans(patient_id=patient_id, fd=fd, ld=ld)

    def _build(self, series_entry, patient_id: str, role: str) -> Series:
        suid, g = series_entry
        volume, acq, positions, ref = read_ct_volume(g["files"])
        anatomy = _anatomy_of(ref)
        return Series(
            patient_id=patient_id,
            series_id=f"{patient_id}_{anatomy}_{role}",
            source=self.source,
            anatomy=anatomy,
            role=role,
            volume_hu=volume,
            acquisition=acq,
            slice_positions=positions,
            demographics=demographics_from(ref),
            src_uids={"series": suid, "study": str(getattr(ref, "StudyInstanceUID", ""))},
        )

    def _attach_projections(self, series: Series, proj_entry) -> None:
        """Ingest the matching DICOM-CT-PD projection series into ``series.sinogram`` + ``geometry``.

        Native ``[V, C, R]`` line integrals + decoded acquisition geometry (GE & Siemens share the
        private-tag layout); see read_projection_series / ../schema/dicom_to_hdf5_mapping.md §3-§4.
        Exact source/detector-distance and channel-angle calibration is flagged in
        ``geometry.calibration_status`` pending the official DICOM-CT-PD data dictionary.
        """
        if proj_entry is None:
            return
        _, g = proj_entry
        sino, geom = read_projection_series(g["files"])
        series.sinogram = sino
        series.geometry = geom
