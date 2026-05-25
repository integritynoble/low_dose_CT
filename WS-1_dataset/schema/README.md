# `WS-1_dataset/schema/` — PWM-LDCT v0.5 specifications

The normative specifications that `pwm_ldct_loader` and the three preprocessing Dockerfiles
implement, and that the *Nature Scientific Data* manuscript
([`../paper_draft/manuscript.tex`](../paper_draft/manuscript.tex)) points to. Together they are the
single source of truth for the harmonized schema, de-identification, DICOM↔HDF5 mapping, and
annotation QA.

| File | Defines | Manuscript section |
|---|---|---|
| [`dataset_schema.md`](dataset_schema.md) | Identifier scheme, release layout, HDF5 layout, loader contract, `metadata.json` schema, HU/orientation/spacing conventions, low-dose-sim params, splits & determinism | Methods → Cross-source harmonization; Data Records |
| [`dicom_cleaning_spec.md`](dicom_cleaning_spec.md) | HIPAA Safe Harbor enforcement, retained-tag whitelist, UID re-hash / date generalization, Tesseract OCR sweep, audit-log format | Methods → De-identification verification |
| [`dicom_to_hdf5_mapping.md`](dicom_to_hdf5_mapping.md) | DICOM-tag → HDF5/metadata mapping, axis conventions, HU rescale, fan-beam sinogram geometry, voxel→patient coordinate recovery | Methods → DICOM conformance |
| [`annotation_qa_protocol.md`](annotation_qa_protocol.md) | Annotator eligibility, calibration, majority-vote consolidation, drift monitoring, discordance adjudication, calibration provenance, κ metrics, annotation JSON formats | Methods → Annotation harmonization; Tech. Validation → Inter-rater reliability |

## Conventions

- **Schema version:** `0.5.0` (`MAJOR.MINOR.PATCH`). All four specs must agree on this version.
- **`[CONFIRM]`** marks a pre-registered parameter to be ratified at release; each corresponds to a
  `\todo{}` in the manuscript and the two must match at submission (e.g. calibration κ threshold,
  HU offsets, OCR confidence, IoU/diameter discordance thresholds).
- **Release-time artifacts** referenced by the specs but generated at build/annotation time (not
  checked into this folder): `anatomy_overrides.csv`, `splits/split_assignment.csv`,
  `annotations/calibration_windows.json`, `deident_audit.jsonl`. These are produced by the pipelines
  and the annotation campaign and are hashed into `manifest.sha256`.

## Status

These are **specifications**, drafted ahead of the implementation. The matching code
(`pwm_ldct_loader`, the Dockerfiles) and the release artifacts they describe are the Phase-1/Phase-2
deliverables tracked in [`../README.md`](../README.md) and [`../data_needs.md`](../data_needs.md);
the specs are the contract those deliverables must satisfy and the conformance target for
`pwm_ldct_loader.validate(root)`.
