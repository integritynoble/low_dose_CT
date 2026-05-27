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
- Low-dose simulation (`lowdose_sim.py`): a physically-grounded **projection-domain** forward
  model (manuscript Eq. 1 — forward Radon → Poisson photon-counting + electronic noise → log →
  reconstruct-and-insert the noise), reusing the validated `recon_sanity` Radon/FBP. Prefers
  `pwm_core.contrib.modalities.ct_radon` when installed. Calibration (`I0`, `σ_e`) is recorded in
  metadata and should be tuned per scanner; the CPU reference model is slow on full volumes.

- **DICOM-CT-PD projection ingestion** (GE & Siemens): `read_projection_series` +
  `extract_ct_pd_geometry` produce native `[V, C, R]` line integrals + decoded geometry; enable
  with `--with-sinograms`. Validated on real GE + Siemens samples. Exact source/detector-distance
  and channel-angle calibration is flagged in `geometry.calibration_status` pending the official
  DICOM-CT-PD data dictionary ([`../schema/dicom_to_hdf5_mapping.md`](../schema/dicom_to_hdf5_mapping.md) §3–§4).
- **LIDC nodule XML → harmonized annotations** (`lidc_annotations.py`): namespace-agnostic parse →
  per-reader per-slice boxes + texture → majority-vote consolidation
  ([`../schema/annotation_qa_protocol.md`](../schema/annotation_qa_protocol.md) §7). NOTE: the LIDC
  XMLs are **not** part of an image-only API pull — they are sourced separately (NBIA Data
  Retriever download / TCIA's LIDC-XML set) and the converter activates when an `*.xml` sits
  alongside a patient's DICOMs.

- **Reconstruction-sanity harness** (`recon_sanity.py`): numpy parallel-beam Radon + FBP +
  agreement metric (max_abs / rmse / frac_within_tol / pearson) + a phantom self-consistency
  round-trip (validated). CLI: `recon-sanity --output <tree>`. NOTE: the per-series check on real
  *helical* DICOM-CT-PD data is **approximate and uncalibrated** (crude parallel rebinning) and
  returns a status flag saying so — a faithful fan/helical round-trip needs the data-dictionary
  geometry.

**Still pending:**
- Per-scanner calibration of the low-dose-sim `I0`/`σ_e` (and optional swap to `pwm_core` /
  calibrated fan-beam geometry) for production-grade noise magnitude.
- Real-data runs (need AAPM Mayo-access + the LIDC annotation XML set).

## Tests

```bash
cd WS-1_dataset/pipelines && PYTHONPATH=. python -m pytest    # needs pwm_ldct_loader installed
```

`tests/test_end_to_end.py` builds synthetic CT DICOM, runs `prep` + `finalize`, and asserts the
output passes `validate()`, contains no PHI, and loads through `LowDoseCTDataset`.
