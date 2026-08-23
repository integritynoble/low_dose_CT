# PhysioNet listing — PWM-LDCT 0.5

Paste-ready content for the PhysioNet project submission (authoring system: one block per
content section below). Values in **[CONFIRM]** are author/release decisions to finalize at
submission. This deposit hosts the **openly-licensed value-added records + code** — it does **not**
redistribute the source DICOM (obtained from NBIA), consistent with the source DUA. **Versioning:
this listing describes v0.5, the LIDC-IDRI first release. AAPM 2016 and Mayo LDCT-PD are planned
for v1.0 (roadmap) and are not part of this deposit.**

---

## Discovery metadata (form fields)

| Field | Value |
|---|---|
| **Title** | PWM-LDCT 0.5: A Content-Addressed, Multi-Task Harmonization of the LIDC-IDRI Lung-Nodule CT Dataset with Simulated Low-Dose |
| **Resource type** | Database (includes software: loader + preprocessing pipelines) |
| **Version** | 0.5.0 |
| **Access policy** | **Open** — deposited records (annotations, metadata, splits, manifest, code, LIDC-derived simulated low-dose) contain no PHI |
| **License** | Data records: **CC BY 4.0**; code (`pwm_ldct_loader`, pipelines, baselines): **Apache-2.0**; manifest: CC0. (LIDC-derived records: CC BY 3.0, per LIDC.) |
| **Data Use Agreement** | None (Open). Source DICOM is obtained under each source's own terms. |
| **Required training** | None |
| **Topics / keywords** | low-dose CT, computed tomography, image reconstruction, denoising, lung nodule, benchmark, harmonization, reproducibility, content-addressing, LIDC-IDRI |
| **Associated publication** | Data Descriptor in *Scientific Data* (DOI **[CONFIRM]**) |
| **Assigned DOI** | `10.13026/[CONFIRM]` (PhysioNet-assigned on publication) |
| **Corresponding author** | **[CONFIRM]** (name, email, ORCID, affiliation) |
| **Authors / affiliations / ORCID** | **[CONFIRM]** — UTSW + PWM Protocol Foundation (CRediT roles in the paper) |
| **Funding** | **[CONFIRM]** (grant numbers) |
| **Parent projects / source datasets** | LIDC-IDRI (10.7937/K9/TCIA.2015.LO9QL9SX) |
| **Code repository** | https://github.com/integritynoble/low_dose_CT |

---

## Abstract

The LIDC-IDRI collection anchors most published deep-learning low-dose CT (LDCT) reconstruction and
lung-nodule evaluation work, yet it ships without a shared, frozen version identifier, with
heterogeneous tooling, and with no low-dose variant. **PWM-LDCT 0.5** is a unified, content-addressed
harmonization of LIDC-IDRI's 1,010 full-dose thoracic CT patients: this project deposits the new,
openly-licensed value-added records — harmonized multi-task annotations (majority-vote lung-nodule
labels reused from the four-radiologist LIDC annotations, plus the raw per-reader labels),
physically-calibrated **simulated** low-dose images for the full-dose-only LIDC scans at dose ratios
0.10 / 0.25 / 0.50 (projection-domain forward model), harmonized per-scan metadata, and
deterministic patient-level splits — together with a pip-installable Python loader
(`pwm_ldct_loader`) and the Docker preprocessing pipeline that regenerates bit-identical HDF5
shards from the source raw distribution. The release is identified by a SHA-256 content hash of its
manifest. The underlying DICOM scans are not redistributed; users obtain them from NBIA and run the
pipeline locally. **Planned v1.0 (roadmap):** AAPM 2016 and Mayo LDCT-PD sources, real paired-dose
noise-inserted reference data, and cross-vendor paired-dose coverage.

## Background

Public datasets have driven a decade of progress in deep-learning low-dose CT reconstruction and
lung-nodule analysis, but LIDC-IDRI — the canonical full-dose reference — has no low-dose variant and
no frozen, content-addressed version identifier, so a result tied to "LIDC-IDRI" in one paper is not
guaranteed to be on the same scans as another. PWM-LDCT 0.5 closes this by adding a
harmonization-and-infrastructure layer over LIDC-IDRI: a single schema, a single loader, a frozen
manifest hash, and physically-calibrated simulated low-dose. Multi-source extension (AAPM 2016, Mayo
LDCT-PD) is planned for v1.0.

## Methods

**Source & cohort.** LIDC-IDRI (1,010 full-dose thoracic CT, of the canonical 1,018; the 8 missing
are unavailable in the public distribution used here). Train / val / test = 589 / 216 / 205.

**Harmonization.** A single schema with per-source Hounsfield-unit offset correction, optional
pixel-spacing resampling (native preserved by default), thin-slice selection, and preservation of
vendor reconstruction kernels (no re-reconstruction). Full specification:
`schema/dataset_schema.md`.

**Low-dose data.** LIDC scans are full-dose only; we provide physically-calibrated **simulated**
low-dose at r ∈ {0.10, 0.25, 0.50} via a documented projection-domain forward model
(`projection_domain_v1_gpu`). **v0.5 contains no measured/real low-dose and no paired-dose
acquisitions** — real paired-dose data (AAPM 2016 / Mayo LDCT-PD noise-inserted reference and
prospective re-acquired scans) is a v1.0 roadmap item.

**Annotation harmonization + QA.** LIDC's four-radiologist nodule annotations are consolidated by
majority vote (≥3-of-4). A calibration + drift-monitoring + discordance-adjudication QA loop governs
quality (`schema/annotation_qa_protocol.md`); raw per-reader labels are preserved. Inter-rater
reliability is reported in the manuscript (detection Cohen's κ, texture κ, Likert ICC when
available). **Top-up annotation on AAPM/Mayo chest cases is a v1.0 roadmap item.**

**De-identification re-verification.** The source is already de-identified to HIPAA Safe Harbor. We
re-verify via a whitelist-based DICOM tag-cleaning pass + UID re-hashing + a Tesseract OCR sweep for
burned-in text (`schema/dicom_cleaning_spec.md`). Deposited records are whitelist-derived and
contain no PHI.

**Splits.** Patients (not scans) are partitioned 60/20/20 train/val/test (589/216/205),
deterministically from a published seed.

## Data Description

This PhysioNet deposit contains the **value-added records and code** (not the source DICOM):

```
annotations/lidc_majority_vote/{patient_id}.json   consolidated LIDC nodule labels (CC BY 3.0)
annotations/raw_per_reader/{patient_id}/{reader}.json  pre-consolidation labels (CC BY 4.0)
sim_lowdose/lidc/{patient_id}/{series_id}.h5       LIDC-derived simulated low-dose (CC BY 3.0)
metadata/{series_id}.json                          harmonized per-scan metadata (CC BY 4.0)
splits/{train,val,test}.txt                        source-prefixed patient IDs (CC BY 4.0)
manifest.sha256                                    SHA-256 of every released artifact (CC0)
pwm_ldct_loader/                                   pip-installable loader (Apache-2.0)
pipelines/                                         Dockerfile + pwm_ldct_prep (Apache-2.0)
baselines/                                         RED-CNN train/eval harness (Apache-2.0)
schema/                                            normative specifications
```

Record formats are normatively defined in `schema/dataset_schema.md` (§5 metadata, §6 annotations)
and `schema/dicom_to_hdf5_mapping.md`.

## Usage Notes

```bash
pip install pwm_ldct_loader
# obtain the source DICOM from NBIA (LIDC-IDRI), then regenerate the harmonized HDF5 with the
# Docker pipeline, then:
from pwm_ldct_loader import LowDoseCTDataset, validate
ds = LowDoseCTDataset(root="/path/pwm_ldct_0_5", split="train", seed=42)
assert validate("/path/pwm_ldct_0_5").ok
```

Any locally-built copy can be verified bit-for-bit against `manifest.sha256`. Baseline reproductions
(RED-CNN; others pluggable) train/evaluate via `pwm_ldct_baselines`. See the GitHub repository and
`schema/` for full details.

## Release Notes

**0.5.0** — first release. LIDC-IDRI-only (1,010 patients, train/val/test = 589/216/205):
harmonized multi-task annotations, simulated low-dose at r ∈ {0.10, 0.25, 0.50}, content-addressed
manifest, loader, pipeline, and a baseline harness. **Known scope:** simulated low-dose only (no
measured/re-acquired paired dose); single source (LIDC); no head subjects; no Canon/Philips.
**v1.0 roadmap:** AAPM 2016 + Mayo LDCT-PD sources (real noise-inserted paired-dose reference,
cross-vendor GE↔Siemens coverage) and prospectively-acquired, multi-site, additional-vendor data.

## Ethics

No new scans were collected. The source dataset (LIDC-IDRI) is de-identified to HIPAA Safe Harbor by
its original release team; we re-verify de-identification (above). No patient contact, no new PHI.
The authors declare the data are used in compliance with each source's data-use terms. **No
annotation top-up was performed in v0.5** (LIDC's inherited four-radiologist annotations are reused);
top-up annotation campaigns on AAPM/Mayo (v1.0) will follow the IRB / exemption process documented in
`annotation_campaign_plan.md`.

## Acknowledgements

We thank the LIDC-IDRI release team for the underlying scans and existing annotation infrastructure,
and the open-source maintainers of PyTorch, NumPy, h5py, PyDICOM, and Tesseract. (AAPM 2016 and Mayo
LDCT-and-Projection-Data teams will be acknowledged in the v1.0 release.)

## Conflicts of Interest

One or more authors are affiliated with the PWM Protocol Foundation, which contributed the
open-source registry tooling used in preprocessing. The dataset is fully usable, citable, and
verifiable through the PhysioNet DOI and the Zenodo archive; this affiliation confers no privileged
access. **[CONFIRM]** each author's specific financial interests at submission.

## References

1. Armato SG III, et al. The LIDC/IDRI: A Completed Reference Database of Lung Nodules on CT.
   Med Phys 38(2):915-931, 2011.
2. Chen H, et al. Low-Dose CT with a Residual Encoder-Decoder CNN (RED-CNN). IEEE TMI
   36(12):2524-2535, 2017.
