# WS-1 — Dataset (Track 9 sub-track 9a)

The **PWM Low-Dose CT Benchmark Dataset**: a content-addressed harmonization of multi-source CT data, distributable via PhysioNet + Zenodo, supported by a *Nature Scientific Data* paper. Released in two stages per the 2026-05-21 director decision — see [`data_needs.md`](data_needs.md) for the strategy doc.

> **Status (D9 + 12, 2026-06-01):** **v0.5 (public-data harmonization) is the current ship target** — manuscript active in [`paper_draft/manuscript.tex`](paper_draft/manuscript.tex); D9 + 180 submission window. v0.5 unifies LIDC-IDRI + AAPM 2016 + Mayo LDCT-PD under one schema, one Python loader, one harmonized annotation convention, and one content-addressed manifest; cross-vendor (GE ↔ Siemens) paired-dose comes free from the Mayo cohort. **v1.0 (prospective multi-vendor + multi-site extension)** is preserved in [`paper_draft/manuscript_v1.tex`](paper_draft/manuscript_v1.tex) for the D9 + 365–540 submission window once Track K + IRB + clinical acquisition land. The two manuscripts coexist — do not conflate them.

---

## Goals

1. **Publish a peer-reviewed paper** at ***Nature Scientific Data*** (primary) describing the dataset, its construction protocol, and its quality controls. Fallback: *Radiology: Artificial Intelligence*.
2. **Register L3 spec on PWMRegistry** so any submission to the leaderboard (WS-4) is evaluated against a cryptographically-anchored benchmark version.
3. **Distribute the dataset on PhysioNet** under credentialed access (HIPAA Safe Harbor compliant) so any external researcher can download and use it.

A successful WS-1 means: an external researcher can `pip install pwm_ldct_loader`, request PhysioNet credentials, download the dataset, and reproduce any published baseline within a single afternoon.

---

## Target specs

| Item | Target |
|---|---|
| Patient scans, paired (normal + matched low-dose) | ≥ 500 (stretch 1,000) |
| Real low-dose pairs (not just simulated) | ≥ 50 patients |
| Vendor coverage | ≥ 2 of {Siemens, GE, Canon, Philips}; goal 3 |
| Anatomy | Chest (lung-screening primary) + abdomen (oncology follow-up) |
| Sites | UTSW lead + ≥ 1 partner academic medical center |
| Annotations | Lesion bbox / segmentation by ≥ 2 board-certified radiologists; majority-vote ground truth |
| Format | DICOM raw projections + reconstructed images + annotations + metadata |
| Distribution | PhysioNet credentialed (HIPAA-compliant) |
| Patient-level split | 60 / 20 / 20 train / val / test; no patient appears in two splits |
| Citations target (24 mo post-release) | ≥ 50 |

---

## Tasks

### Phase 1 — Public-data substrate (D9 + 0 → D9 + 90)

| # | Task | Output |
|---|---|---|
| 1.1 | Download and stage LIDC-IDRI 50-patient subset (NBIA Data Retriever) | Raw DICOM tree on disk |
| 1.2 | Request AAPM 2016 access (Mayo); 1-2 wk lead time | Access granted; raw DICOM staged |
| 1.3 | Author canonical metadata schema (`schema/dataset_schema.md`) | Schema doc + DICOM cleaning spec |
| 1.4 | Build `Dockerfile.lidc_idri` (HU window, 512×512 resize, Poisson-noise simulated low-dose at 25% photon count) | Working Docker image; HDF5 shards |
| 1.5 | Build `Dockerfile.aapm_2016` (uses *real* 25% mA pairs) | Working Docker image; HDF5 shards |
| 1.6 | Build `pwm_ldct_loader` Python data loader; pytest suite verifying schema invariants | Pip-installable package; tests green |
| 1.7 | Validate that downstream code (`baselines/`, `reference_method/v0.1/`) consumes the loader without modification | Integration smoke test |

### Phase 2 — Clinical acquisition (D9 + 120 → D9 + 270)

| # | Task | Output |
|---|---|---|
| 2.1 | IRB submission to UTSW Radiology (gated by Track K — new PI) | IRB approval letter |
| 2.2 | Partner-site MOU; second-vendor acquisition (target ≥ 200 scans) | Signed MOU; raw scans arriving |
| 2.3 | Annotation pipeline: ≥ 2 board-certified radiologists × honoraria; majority-vote ground truth | Annotated cases |
| 2.4 | PHI scrubbing per HIPAA Safe Harbor; verify against DICOM cleaning whitelist | Clean DICOM exports |
| 2.5 | Build `Dockerfile.utsw_clinical` (consumes clean DICOM, produces HDF5 matching schema) | Working Docker image |

### Phase 3 — Paper + listing + on-chain (D9 + 270 → D9 + 540)

| # | Task | Output |
|---|---|---|
| 3.1 | Draft dataset paper (Methods, Validation, Usage, Code Availability sections) | Draft v1 |
| 3.2 | PhysioNet metadata + access docs; submit listing | PhysioNet page live |
| 3.3 | Submit paper to *Nature Scientific Data*; revise to acceptance (~6 mo) | Acceptance letter |
| 3.4 | Author and register L3 spec on PWMRegistry (concurrent with paper submission) | L3 hash on chain |

---

## Timeline (D9-anchored)

| Date | Milestone | Status |
|---|---|---|
| D9 + 30 | LIDC-IDRI Docker pipeline reproducible end-to-end | pending |
| D9 + 60 | AAPM 2016 Docker pipeline reproducible end-to-end | pending |
| D9 + 90 | Metadata schema ratified; data loader passes pytest on both datasets | pending |
| D9 + 120 | IRB submitted to UTSW Radiology | pending |
| D9 + 180 | Partner-site MOU signed; clinical scan acquisition underway | pending |
| D9 + 270 | UTSW IRB approved; first clinical scans annotated | pending |
| D9 + 365 | **Paper submitted to *Nature Scientific Data*; L3 spec on chain** | pending |
| D9 + 540 | **Paper accepted; PhysioNet listing live; ≥ 500 paired scans archived** | pending |

The critical-path leg is the IRB lag (months 5-9). It is exogenous and the only mitigation is parallel-tracking WS-2 and WS-3 during that window.

---

## Done when

- [ ] ≥ 500 paired scans across ≥ 2 vendors and ≥ 2 sites
- [ ] *Nature Scientific Data* paper accepted
- [ ] L3 spec hash registered on PWM mainnet
- [ ] PhysioNet listing live; external download verified
- [ ] `pwm_ldct_loader` published on PyPI
- [ ] ≥ 3 external research groups have used the dataset (early adoption signal)

---

## Subfolders (created on demand)

| Path | Purpose | Status |
|---|---|---|
| `schema/` | Metadata schema, DICOM cleaning spec, DICOM→HDF5 mapping, annotation-QA protocol | **specs drafted** (4 specs + README) |
| `pwm_ldct_loader/` | Pip-installable loader package (`LowDoseCTDataset` + `validate`) | **scaffolded**: implements schema §4 contract + §8 validate; 24 pytest green on synthetic fixture; reads pipeline output |
| `pipelines/` | Dockerfiles for LIDC-IDRI, AAPM 2016, Mayo LDCT-PD + shared `pwm_ldct_prep` package | **built**: full pipeline (DICOM→de-id→harmonize→HDF5→validate) incl. DICOM-CT-PD projections + LIDC annotations + recon-sanity; ran on real Mayo data → `gs://low-dose-ct/pwm_ldct_v0_5` (199 patients) |
| `baselines/` | `pwm_ldct_baselines` train/eval harness + RED-CNN + GPU Dockerfile | **scaffolded**: RED-CNN implemented; train/eval → per-dose PSNR/SSIM/LPIPS `results.json`; 5 tests green. 3 other methods pluggable (need published impls); benchmark numbers need a GPU |
| `physionet_listing/` | PhysioNet metadata + access docs | **drafted**: paste-ready listing (all sections + discovery fields), Open access / CC BY 4.0; `[CONFIRM]` fields = authors/DOI/IRB/funding |
| `paper_draft/` | *Nature Scientific Data* manuscript | pending Phase 3 |

Do not pre-create empty directories. Create each one when the work that fills it begins.

---

## Dependencies

- **Track K** (new UTSW PI confirmed) — required for IRB submission. If Track K slips past D9 + 270, fall back to a public-data-only first dataset paper (LIDC-IDRI + AAPM 2016) submitted at D9 + 365 with a clinical-data follow-up later.
- **Forward model** `packages/pwm_core/contrib/modalities/ct_radon.py` — single source of truth for simulated low-dose generation. Do not reimplement.
- **L3 spec** ([`../pwm_integration/l3_spec.md`](../pwm_integration/l3_spec.md)) — registry payload depends on this folder's final dataset specs.

---

## Cross-references

- [`SUBMISSION_CHECKLIST.md`](SUBMISSION_CHECKLIST.md) — consolidated open-items checklist (single source of truth).
- [`annotation_campaign_plan.md`](annotation_campaign_plan.md) — operational plan for the radiologist annotation campaign.
- [`../WS-2_framework/`](../WS-2_framework/) — the framework's CT validation runs against this dataset.
- [`../WS-3_reference_method/`](../WS-3_reference_method/) — trains and evaluates on this dataset.
- [`../WS-4_leaderboard/`](../WS-4_leaderboard/) — community submissions are scored on this dataset's test split.
- [`../pwm_integration/l3_spec.md`](../pwm_integration/l3_spec.md) — on-chain spec.
