# `WS-1_dataset/pipelines/` — preprocessing pipelines

Build the harmonized **PWM-LDCT v0.5** tree from each source's raw DICOM. The shared package
`pwm_ldct_prep` reads DICOM, re-verifies de-identification, harmonizes to the canonical schema,
simulates low-dose, and writes HDF5 + metadata that pass `pwm_ldct_loader.validate`. Each
Dockerfile bakes one source.

| Image | Source | Build |
|---|---|---|
| `pwm-ldct-prep-lidc:v0.5`  | LIDC-IDRI (image-only + simulated LD) | `docker build -f pipelines/Dockerfile.lidc_idri .` |
| `pwm-ldct-prep-aapm:v0.5`  | AAPM 2016 (real paired + projections) | `docker build -f pipelines/Dockerfile.aapm_2016 .` |
| `pwm-ldct-prep-mayo:v0.5`  | Mayo LDCT-PD (real paired + projections) | `docker build -f pipelines/Dockerfile.mayo_ldct_pd .` |

> **Build context is `WS-1_dataset/`** (the parent), so the sibling `pwm_ldct_loader` package —
> the source of truth for the schema constants `pwm_ldct_prep` imports — is in scope. The schema
> specs are in [`../schema/`](../schema/).

## Workflow

Run `prep` once per source into **one shared output tree**, then `finalize` once, then `validate`:

```bash
cd WS-1_dataset
docker build -t pwm-ldct-prep-mayo:v0.5 -f pipelines/Dockerfile.mayo_ldct_pd .

# 1) harmonize each source into the SAME output tree
docker run --rm -v /raw/mayo:/data/raw -v /out:/data/out \
    pwm-ldct-prep-mayo:v0.5 prep --input /data/raw --output /data/out --seed 42
# (repeat with the lidc / aapm images into the same /out)

# 2) write splits + manifest over the combined tree
docker run --rm -v /out:/data/out pwm-ldct-prep-mayo:v0.5 finalize --output /data/out

# 3) conformance check (dataset_schema.md §8)
docker run --rm -v /out:/data/out pwm-ldct-prep-mayo:v0.5 validate --output /data/out
```

`--source` defaults to the image's baked `PWM_LDCT_SOURCE`; `--subset N` limits to the first N
patients (pipeline-test mode); `--no-sim` skips low-dose simulation.

## What is implemented vs. pending

**Implemented (reconstructed-image path, end-to-end, tested):**
- DICOM discovery + grouping; CT volume reading → HU (`adapters/base.py`).
- Source adapters: LIDC (image-only, largest CT series), AAPM/Mayo (Siemens paired, by
  SeriesDescription) — `adapters/`.
- De-identification re-verification: whitelist tag cleaning, UID re-hash, audit log
  (`deident.py`; [`../schema/dicom_cleaning_spec.md`](../schema/dicom_cleaning_spec.md)). Outputs
  are whitelist-derived, so PHI cannot propagate (asserted in tests).
- Harmonization + `metadata.json` (`harmonize.py`); HDF5 / splits / manifest writers
  (`writers.py`); deterministic split placement.
- Low-dose simulation adapter (`lowdose_sim.py`): uses `pwm_core.contrib.modalities.ct_radon`
  when available, else a clearly-flagged non-production fallback.

**Pending (require the projection data + iteration):**
- **DICOM-CT-PD projection ingestion** (sinogram + geometry) for AAPM/Mayo — the
  `_attach_projections` hook in `adapters/_siemens.py` raises `NotImplementedError`; default runs
  are reconstructed-image-only (which `validate()` accepts). See
  [`../schema/dicom_to_hdf5_mapping.md`](../schema/dicom_to_hdf5_mapping.md) §3–§4 for the target.
- **LIDC nodule XML → harmonized annotations** conversion (the QA loop lives in
  [`../schema/annotation_qa_protocol.md`](../schema/annotation_qa_protocol.md)).
- Wiring `pwm_core` as the production low-dose forward model.

## Tests

```bash
cd WS-1_dataset/pipelines && PYTHONPATH=. python -m pytest    # needs pwm_ldct_loader installed
```

`tests/test_end_to_end.py` builds synthetic CT DICOM, runs `prep` + `finalize`, and asserts the
output passes `validate()`, contains no PHI, and loads through `LowDoseCTDataset`.
