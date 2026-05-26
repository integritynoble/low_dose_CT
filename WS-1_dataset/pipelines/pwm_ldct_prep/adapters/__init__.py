"""Source adapters: raw DICOM tree -> harmonized PatientScans."""
from .aapm_2016 import Aapm2016Adapter
from .base import PatientScans, Series, SourceAdapter
from .lidc_idri import LidcIdriAdapter
from .mayo_ldct_pd import MayoLdctPdAdapter

ADAPTERS = {
    "lidc": LidcIdriAdapter,
    "aapm": Aapm2016Adapter,
    "mayo": MayoLdctPdAdapter,
}


def get_adapter(source: str) -> SourceAdapter:
    if source not in ADAPTERS:
        raise ValueError(f"unknown source {source!r}; choose from {sorted(ADAPTERS)}")
    return ADAPTERS[source]()


__all__ = ["ADAPTERS", "get_adapter", "PatientScans", "Series", "SourceAdapter"]
