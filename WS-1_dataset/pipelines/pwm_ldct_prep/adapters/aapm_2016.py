"""AAPM 2016 Low-Dose CT Grand Challenge adapter (path-based discovery).

Unlike the Mayo LDCT-PD TCIA distribution (which the tag-based :class:`SiemensPairedAdapter`
handles), the AAPM/Box distribution ships Siemens ``.IMA`` files with ``PatientID='Anonymous'``
and no ``SeriesDescription`` — patient (``L###``), dose (full/quarter), domain (image/projection)
and recon (thickness/kernel) live only in the path (see :mod:`..stage`). So this adapter discovers
by **path** after the zips are staged into a local tree.

A paired record needs a full-dose reconstruction to anchor, which exists only for the 10 *training*
patients (testing is quarter-dose only — FD was withheld for the challenge); testing patients are
therefore skipped, matching the "AAPM 10" cohort count. The cross-source canonical key is hashed
from the path-derived ``L###`` (not the ``Anonymous`` tag) so AAPM ⊂ Mayo overlaps de-duplicate.
"""
from __future__ import annotations

import glob
import os
from typing import Dict, Iterator, List, Optional

from ..stage import classify_aapm_path
from ._siemens import _anatomy_of
from .base import (PatientScans, Series, SourceAdapter, canonical_patient_key, demographics_from,
                   read_ct_volume, read_projection_series)

_PREFERRED_RECON = ("1mm", "b30")  # standard thin-slice soft-tissue reconstruction


def _recon_rank(recon: str) -> tuple:
    return (0 if "1mm" in recon else 1, 0 if "b30" in recon else 1, recon)


class Aapm2016Adapter(SourceAdapter):
    source = "aapm"
    default_anatomy = "abdomen"
    with_sinograms = False  # projection ingest is opt-in (see cli --with-sinograms)

    def iter_patients(self, input_dir: str, subset: Optional[int] = None) -> Iterator[PatientScans]:
        # group every staged DICOM by (patient, role, domain) -> {recon: [files]}
        groups: Dict[tuple, Dict[str, List[str]]] = {}
        for ext in ("*.IMA", "*.ima", "*.dcm", "*.DCM"):
            for f in glob.iglob(os.path.join(input_dir, "**", ext), recursive=True):
                c = classify_aapm_path(os.path.relpath(f, input_dir))
                if c["patient"] is None or c["role"] is None:
                    continue
                groups.setdefault((c["patient"], c["role"], c["domain"]), {}) \
                      .setdefault(c["recon"] or "_", []).append(f)

        registry: Dict[str, str] = {}
        n = 0
        for native_pid in sorted({k[0] for k in groups}):
            roles_domains = {(k[1], k[2]) for k in groups if k[0] == native_pid}
            if ("fd", "image") not in roles_domains:
                continue  # need a full-dose recon to anchor (selects the training patients)
            if subset is not None and n >= subset:
                break
            patient_id = self.reindex(native_pid, registry)
            ckey = canonical_patient_key(native_pid)

            fd = self._build_image(groups[(native_pid, "fd", "image")], patient_id, "fd")
            fd.canonical_key = ckey
            ld_img = groups.get((native_pid, "ld", "image"))
            ld = self._build_image(ld_img, patient_id, "ld") if ld_img else None
            if ld is not None:
                ld.canonical_key = ckey

            if self.with_sinograms:
                self._attach(fd, groups.get((native_pid, "fd", "projection")))
                ld_proj = groups.get((native_pid, "ld", "projection"))
                if ld is not None:
                    self._attach(ld, ld_proj)
                elif ld_proj is not None:
                    fd.ld_sinogram, _ = read_projection_series(self._pick(ld_proj))

            yield PatientScans(patient_id=patient_id, fd=fd, ld=ld)
            n += 1

    @staticmethod
    def _pick(recon_map: Dict[str, List[str]]) -> List[str]:
        """Pick the preferred reconstruction's files (1mm B30 if present, else best available)."""
        if not recon_map:
            return []
        best = sorted(recon_map.keys(), key=_recon_rank)[0]
        return recon_map[best]

    def _build_image(self, recon_map: Dict[str, List[str]], patient_id: str, role: str) -> Series:
        volume, acq, positions, ref = read_ct_volume(self._pick(recon_map))
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
            src_uids={"series": str(getattr(ref, "SeriesInstanceUID", "")),
                      "study": str(getattr(ref, "StudyInstanceUID", ""))},
        )

    def _attach(self, series: Series, proj_map: Optional[Dict[str, List[str]]]) -> None:
        if not proj_map:
            return
        series.sinogram, series.geometry = read_projection_series(self._pick(proj_map))
