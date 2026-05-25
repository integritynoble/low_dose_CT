"""AAPM 2016 Low-Dose CT Grand Challenge adapter.

Siemens paired-dose dataset (10 patients) with real full-dose and 25%-dose acquisitions plus
projections. Same SeriesDescription scheme as Mayo LDCT-PD, so it reuses the shared adapter.
"""
from __future__ import annotations

from ._siemens import SiemensPairedAdapter


class Aapm2016Adapter(SiemensPairedAdapter):
    source = "aapm"
    default_anatomy = "abdomen"
