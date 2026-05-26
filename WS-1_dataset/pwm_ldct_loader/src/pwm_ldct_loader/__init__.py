"""pwm_ldct_loader — unified loader for the PWM-LDCT v0.5 harmonized low-dose CT dataset.

Surfaces LIDC-IDRI + AAPM 2016 + Mayo LDCT-PD under one schema. Implements the loader
contract (§4) and the conformance check (§8) defined in
``WS-1_dataset/schema/dataset_schema.md`` (schema version 0.5.0).
"""
from .schema import SCHEMA_VERSION, SOURCES
from .dataset import LowDoseCTDataset
from .validate import validate, ValidationReport
from ._seed import seed_everything

__all__ = [
    "SCHEMA_VERSION",
    "SOURCES",
    "LowDoseCTDataset",
    "validate",
    "ValidationReport",
    "seed_everything",
]
__version__ = SCHEMA_VERSION
