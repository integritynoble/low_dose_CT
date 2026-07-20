# PhysioNet listing — PWM-LDCT 1.0

Paste-ready content for the PhysioNet project submission (authoring system: one block per
content section below). Values in **[CONFIRM]** are author/release decisions to finalize at
submission. This deposit hosts the **openly-licensed value-added records + code** — it does **not**
redistribute the source DICOM (obtained from NBIA / Mayo / TCIA), consistent with each source DUA.

---

## Discovery metadata (form fields)

| Field | Value |
|---|---|
| **Title** | PWM-LDCT 1.0: A Content-Addressed, Multi-Task Harmonization of Three Public Low-Dose CT Datasets |
| **Resource type** | Database (includes software: loader + preprocessing pipelines) |
| **Version** | 1.0.0 |
| **Access policy** | **Open** — deposited records (annotations, metadata, splits, manifest, code, LIDC-derived simulated low-dose) contain no PHI |
| **License** | Data records: **CC BY 4.0**; code (`pwm_ldct_loader`, pipelines, baselines): **Apache-2.0**; manifest: CC0. (LIDC-derived records: CC BY 3.0, per LIDC.) |
| **Data Use Agreement** | None (Open). Source DICOM is obtained under each source's own terms. |
| **Required training** | None |
| **Topics / keywords** | low-dose CT, computed tomography, image reconstruction, denoising, lung nodule, benchmark, harmonization, DICOM-CT-PD, reproducibility, content-addressing |
| **Associated publication** | Data Descriptor in *Scientific Data* (DOI **[CONFIRM]**) |
| **Assigned DOI** | `10.13026/[CONFIRM]` (PhysioNet-assigned on publication) |
| **Corresponding author** | **[CONFIRM]** (name, email, ORCID, affiliation) |
| **Authors / affiliations / ORCID** | **[CONFIRM]** — UTSW + PWM Protocol Foundation (CRediT roles in the paper) |
| **Funding** | **[CONFIRM]** (grant numbers) |
| **Parent projects / source datasets** | LIDC-IDRI (10.7937/K9/TCIA.2015.LO9QL9SX); AAPM 2016 Low-Dose CT Grand Challenge; Mayo LDCT-and-Projection-Data (10.7937/9npb-2637) |
| **Code repository** | https://github.com/integritynoble/low_dose_CT |

---

## Abstract

Three public low-dose CT (LDCT) datasets — LIDC-IDRI, the 2016 AAPM-Mayo Low-Dose CT Grand
Challenge, and the Mayo LDCT-and-Projection-Data collection — together anchor most published
deep-learning LDCT reconstruction evaluation, yet they are distributed in incompatible formats with
heterogeneous annotations and no shared, frozen version identifier. PWM-LDCT 1.0 is a unified,
content-addressed harmonization of these three sources. This project deposits the new,
openly-licensed value-added records — harmonized multi-task annotations (majority-vote lung-nodule
labels reused from the four-radiologist LIDC annotations and topped up on AAPM/Mayo, per-scan
diagnostic-quality Likert scores, and the raw per-reader labels), physically-derived simulated
low-dose images for the full-dose-only LIDC scans, harmonized per-scan metadata, and deterministic
patient-level splits — together with a pip-installable Python loader (`pwm_ldct_loader`) and three
Docker preprocessing pipelines that regenerate bit-identical HDF5 shards from each source's raw
distribution. The release is identified by a SHA-256 content hash of its manifest. Notably, the
public Mayo cohort spans two vendors (~half GE, ~half Siemens), so 1.0 provides genuine
cross-vendor paired-dose coverage. The underlying DICOM scans are not redistributed; users obtain
them from each source and run the pipelines locally.

## Background

Public datasets have driven a decade of progress in deep-learning low-dose CT reconstruction, but
the three sources above are not designed to be used together. Three structural gaps prevent
treating their union as a coherent benchmark: (1) **loader fragmentation** — each is distributed in
its own format, so every method re-implements preprocessing, causing silent format-conversion drift
between papers; (2) **annotation heterogeneity** — LIDC ships four-radiologist nodule XML, AAPM has
no built-in lesion labels, Mayo has labels on a subset, with no shared tooling; (3) **benchmark
drift** — none has a content-addressed version identifier, so a result tied to "LIDC-IDRI" in one
paper is not guaranteed to be on the same scans as another. PWM-LDCT 1.0 closes these by adding an
annotation-and-infrastructure layer over the existing sources rather than collecting new scans.

## Methods

**Sources & cohort.** LIDC-IDRI (1,010 full-dose thoracic CT, of the canonical 1,018); AAPM 2016 (10 patients, paired
full/quarter-dose); Mayo LDCT-PD public portion (199 patients — chest + abdomen, ~half GE / ~half
Siemens; the 99 head subjects are Genomic Data Commons credentialed-access and out of scope, and one
ACR phantom is excluded). Union = 1,218 unique subjects (1,219 source records; one patient, L143,
is shared by AAPM 2016 and Mayo LDCT-PD and de-duplicated via the cross-source canonical key; LIDC
contributes 1,010 of its canonical 1,018 patients, the 8 missing unavailable in this distribution).

**Cross-source harmonization.** A single schema with per-source Hounsfield-unit offset correction,
optional pixel-spacing resampling (native preserved by default), thin-slice selection, and
preservation of vendor reconstruction kernels (no re-reconstruction). Full specification:
`schema/dataset_schema.md`.

**Low-dose data.** AAPM/Mayo reduced-dose data is produced by Mayo's validated projection-domain
**noise-insertion** technique applied to the real full-dose projections (not a second physical
scan). For the full-dose-only LIDC scans we additionally provide physically-calibrated **simulated**
low-dose at r ∈ {0.10, 0.25, 0.50} via a documented forward model.

**Annotation harmonization + QA.** LIDC's four-radiologist nodule annotations are consolidated by
majority vote; AAPM/Mayo chest cases are topped up by ≥2 board-certified radiologists following the
LIDC protocol; per-scan diagnostic-quality Likert scores are collected on paired-dose subsets. A
calibration + drift-monitoring + discordance-adjudication QA loop governs quality
(`schema/annotation_qa_protocol.md`); raw per-reader labels are preserved.

**De-identification re-verification.** All sources are already de-identified to HIPAA Safe Harbor.
We re-verify via a whitelist-based DICOM tag-cleaning pass + UID re-hashing + a Tesseract OCR sweep
for burned-in text, and apply a second re-indexing layer (`schema/dicom_cleaning_spec.md`).
Deposited records are whitelist-derived and contain no PHI.

**Splits.** Patients (not scans) are partitioned 60/20/20 train/val/test, stratified by source and
anatomy, deterministically from a published seed.

## Data Description

This PhysioNet deposit contains the **value-added records and code** (not the source DICOM):

```
annotations/lidc_majority_vote/{patient_id}.json   consolidated LIDC nodule labels (CC BY 3.0)
annotations/topup_aapm|topup_mayo/{patient_id}.json top-up nodule labels (CC BY 4.0)
annotations/likert/{series_id}.json                per-scan diagnostic Likert (CC BY 4.0)
annotations/raw_per_reader/{patient_id}/{reader}.json  pre-consolidation labels (CC BY 4.0)
sim_lowdose/lidc/{patient_id}/{series_id}.h5       LIDC-derived simulated low-dose (CC BY 3.0)
metadata/{series_id}.json                          harmonized per-scan metadata (CC BY 4.0)
splits/{train,val,test}.txt                        source-prefixed patient IDs (CC BY 4.0)
manifest.sha256                                    SHA-256 of every released artifact (CC0)
pwm_ldct_loader/                                   pip-installable loader (Apache-2.0)
pipelines/                                         Dockerfiles + pwm_ldct_prep (Apache-2.0)
baselines/                                         RED-CNN train/eval harness (Apache-2.0)
schema/                                            normative specifications
```

Record formats are normatively defined in `schema/dataset_schema.md` (§5 metadata, §6 annotations)
and `schema/dicom_to_hdf5_mapping.md`. The harmonized reconstructed/projection HDF5 for the
DUA-restricted AAPM/Mayo scans is **regenerated locally** by the pipelines and is not part of this
deposit.

## Usage Notes

```bash
pip install pwm_ldct_loader
# obtain the source DICOM from NBIA (LIDC), Mayo (AAPM 2016), TCIA (Mayo LDCT-PD),
# then regenerate the harmonized HDF5 with the Docker pipelines, then:
from pwm_ldct_loader import LowDoseCTDataset, validate
ds = LowDoseCTDataset(root="/path/pwm_ldct_1_0", split="train", seed=42)
assert validate("/path/pwm_ldct_1_0").ok
```

Any locally-built copy can be verified bit-for-bit against `manifest.sha256`. Baseline reproductions
(RED-CNN; others pluggable) train/evaluate via `pwm_ldct_baselines`. See the GitHub repository and
`schema/` for full details.

## Release Notes

**1.0.0** — first release. Public-data-only harmonization (LIDC + AAPM 2016 + Mayo LDCT-PD public
portion). Provides cross-vendor (GE + Siemens) paired-dose coverage via the Mayo cohort, harmonized
multi-task annotations, simulated low-dose for LIDC, content-addressed manifest, loader, pipelines,
and a baseline harness. **Known scope:** reduced-dose is simulated/noise-inserted (no re-acquired
paired dose); no Canon/Philips; no head subjects (GDC-restricted); annotation top-up limited to the
chest lung-nodule task. A planned prospective companion release adds prospectively-acquired, multi-site, additional-vendor
data and new tasks.

## Ethics

No new scans were collected. The three source datasets are de-identified to HIPAA Safe Harbor by
their original release teams; we re-verify de-identification (above). The annotation top-up campaign
involved board-certified radiologists reading already-public, already-de-identified images and
generated only image-level labels — no patient contact, no new PHI; the UTSW IRB issued a
non-human-subjects-research / exempt determination (**[CONFIRM] determination no.**). No PHI was
detected in any deposited record. The authors declare the data are used in compliance with each
source's data-use terms.

## Acknowledgements

We thank the LIDC-IDRI, AAPM 2016, and Mayo LDCT-and-Projection-Data release teams for the
underlying scans and existing annotation infrastructure, the radiologists who contributed top-up
annotations, and the open-source maintainers of PyTorch, NumPy, h5py, PyDICOM, and Tesseract.

## Conflicts of Interest

One or more authors are affiliated with the PWM Protocol Foundation, which contributed the
open-source registry tooling used in preprocessing. The dataset is fully usable, citable, and
verifiable through the PhysioNet DOI and the Zenodo archive; this affiliation confers no privileged
access. **[CONFIRM]** each author's specific financial interests at submission.

## References

1. Armato SG III, et al. The LIDC/IDRI: A Completed Reference Database of Lung Nodules on CT.
   Med Phys 38(2):915-931, 2011.
2. McCollough CH, et al. Low-Dose CT for the Detection and Classification of Metastatic Liver
   Lesions: Results of the 2016 Low Dose CT Grand Challenge. Med Phys 44(10):e339-e352, 2017.
3. Moen TR, et al. Low-dose CT image and projection dataset. Med Phys 48(2):902-911, 2021.
4. Chen H, et al. Low-Dose CT with a Residual Encoder-Decoder CNN (RED-CNN). IEEE TMI
   36(12):2524-2535, 2017.
