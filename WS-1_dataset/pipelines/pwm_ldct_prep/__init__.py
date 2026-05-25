"""pwm_ldct_prep — preprocessing pipelines that build the harmonized PWM-LDCT v0.5 tree.

Reads each source's raw DICOM, de-identifies (re-verification), harmonizes to the canonical
schema, simulates low-dose, and writes schema-conformant HDF5 + metadata that pass
``pwm_ldct_loader.validate``. Run via ``python -m pwm_ldct_prep {prep,finalize,validate}``.

The schema constants are imported from ``pwm_ldct_loader`` so the pipeline output and the loader
can never drift. See ../schema/ for the normative specs.
"""
__version__ = "0.5.0"
