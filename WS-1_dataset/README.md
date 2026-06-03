# WS-1 — Dataset (Track 9 sub-track 9a)

The **PWM Low-Dose CT Benchmark Dataset**: a content-addressed harmonization of multi-source CT data, distributable via PhysioNet + Zenodo, supported by a *Nature Scientific Data* paper. Released in two stages per the 2026-05-21 director decision — see [`data_needs.md`](data_needs.md) for the strategy doc.

> **Status (D9 + 14, 2026-06-03):** **v0.5 (public-data harmonization) is the current ship target** — manuscript active in [`paper_draft/manuscript.tex`](paper_draft/manuscript.tex); D9 + 180 submission window. v0.5 unifies LIDC-IDRI + AAPM 2016 + Mayo LDCT-PD under one schema, one Python loader, one harmonized annotation convention, and one content-addressed manifest; cross-vendor (GE ↔ Siemens) paired-dose comes free from the Mayo cohort. **v1.0 (prospective multi-vendor + multi-site extension)** is preserved in [`paper_draft/manuscript_v1.tex`](paper_draft/manuscript_v1.tex) for the D9 + 365–540 submission window once Track K + IRB + clinical acquisition land. The two manuscripts coexist — do not conflate them.

---

## Goals

1. **Publish a peer-reviewed paper** at ***Nature Scientific Data*** (primary) describing the dataset, its construction protocol, and its quality controls. Fallback: *Radiology: Artificial Intelligence*.
2. **Content-address the dataset release** by SHA-256 hash, with PhysioNet DOI + Zenodo as the primary deposit / citation channels and the PWM L3 registry as an optional mirror, so any submission to the leaderboard (WS-4) is evaluated against a cryptographically-pinned benchmark version. (Per the 2026-05-25 reframe — content-addressing is the methodological substance; the L3 registry is one of several resolvers.)
3. **Distribute the dataset on PhysioNet** under credentialed access (HIPAA Safe Harbor compliant) so any external researcher can download and use it.

A successful WS-1 means: an external researcher can `pip install pwm_ldct_loader`, request PhysioNet credentials, download the dataset, and reproduce any published baseline within a single afternoon.

---

## Target specs

The two releases have different scope. v0.5 ships the harmonization layer over existing public data; v1.0 adds the prospective clinical contribution. **Where a row differs between releases, both values are shown.**

| Item | v0.5 (current ship target) | v1.0 (future, gated on Track K + IRB) |
|---|---|---|
| Patient scans, paired full-dose / reduced-dose | **208 unique paired-dose / 1,226 unique union** (LIDC + AAPM 2016 + Mayo LDCT-PD); AAPM paired FD+QD covers the 10 training patients (testing is QD-only, FD withheld) | ≥ 500 (stretch 1,000) prospectively acquired |
| Credential-issuance regime (per WS-2 [V3-9 power sim](../WS-2_framework/theory/proofs/estimator.md), D9 + 14) | At AUC ≈ 0.92 (typical lung-nodule operating point) and the v0.3 AUC default `ε = 0.05`, the cohort satisfies WS-2's (S3) sample-size formula (n ≈ 130–250 required) **but sits in the empirical INDETERMINATE-dominated regime**: P(`PASS`) under the null ≈ 0.40 at n = 200, lifting to ≈ 0.94 at n = 500. Downstream users should **expect `INDETERMINATE` verdicts on the v0.5 cohort for genuinely equivalent methods** — absence of `PASS` is not evidence of non-equivalence, only of insufficient n. Non-AUC metrics (Dice, MAE, contrast-recovery) are well-served at typical `σ_Δ` values. For tighter margins (`ε = 0.02`) the cohort is undersized by both the formula and the empirical power criterion. | Prospective n ≥ 500 lifts cleanly into the **P(`PASS`) ≈ 0.94** regime at the typical AUC / `ε = 0.05` operating point; supports reliable `PASS` verdicts on equivalent methods and (with the upper end of the cohort range) the tighter `ε = 0.02` margin. |
| Reduced-dose nature | **Measured-reference vs.\ our-simulation**: AAPM/Mayo "low-dose" is Mayo's validated projection-domain noise insertion from the real full-dose projections, not a second physical scan (corrected 2026-05-26); LIDC reduced-dose is our Poisson-noise simulation at 25% photon count | Re-acquired paired-dose physical scans (≥ 50 patients) |
| Vendor coverage | **Two-vendor: ~99 GE + ~101 Siemens** in the Mayo LDCT-PD cohort (corrected 2026-05-26 from prior "Siemens-only" framing); cross-vendor (GE ↔ Siemens) paired-dose is a v0.5 strength | + Canon and/or Philips via partner-site acquisition (≥ 3 vendors total) |
| Anatomy | Chest (lung-screening primary) + abdomen (oncology follow-up, partial coverage) | Chest + abdomen at multi-site scale |
| Sites | Public sources only — no PHI-bearing institutional acquisition | UTSW lead + ≥ 1 partner academic medical center |
| Annotations | Re-use LIDC-IDRI's 4-radiologist annotations; top up AAPM + Mayo chest cases that lack equivalents per [`schema/annotation_qa_protocol.md`](schema/annotation_qa_protocol.md) | Same protocol extended to the prospective cohort |
| Format | HDF5 shards + DICOM-CT-PD projections (where source provides) + harmonized annotations + content-addressed manifest | Same + raw projections from the prospective acquisitions |
| Distribution | PhysioNet DOI + Zenodo (primary); PWM L3 registry as an optional mirror (post-2026-05-25 reframe) | Same |
| Patient-level split | Already deposited under [`hdf5/{train,val,test}/`](pipelines/) (pid-bucketed for Mayo, ckey-bucketed for AAPM); 60 / 20 / 20 | Same protocol over the larger cohort |
| Citations target (24 mo post-release) | ≥ 25 (v0.5 alone) | ≥ 50 (combined v0.5 + v1.0) |

---

## Tasks

### Phase 1 — Public-data substrate (D9 + 0 → D9 + 90)

| # | Task | Output | Status @ v0.5 |
|---|---|---|---|
| 1.1 | Download and stage LIDC-IDRI 50-patient subset (NBIA Data Retriever) | Raw DICOM tree on disk | **done** — staged; pipeline runs end-to-end |
| 1.2 | Request AAPM 2016 access (Mayo); 1-2 wk lead time | Access granted; raw DICOM staged | **done** — staged at `gs://low-dose-ct/aapm_2016_grand_challenge/` (52 zips, 174.7 GB); unzip step wired in commit `a4a14ec` |
| 1.3 | Author canonical metadata schema (`schema/dataset_schema.md`) | Schema doc + DICOM cleaning spec | **done** — 4 specs + README in [`schema/`](schema/) |
| 1.4 | Build `Dockerfile.lidc_idri` (HU window, 512×512 resize, Poisson-noise simulated low-dose at 25% photon count) | Working Docker image; HDF5 shards | **done** — pipeline built; HDF5 shards land under `hdf5/{train,val,test}/` |
| 1.5 | Build `Dockerfile.aapm_2016` (uses Mayo projection-domain noise-inserted low-dose) | Working Docker image; HDF5 shards | **done** — pipeline built; AAPM unzip + DICOM-CT-PD projection ingest wired; output is ckey-bucketed |
| 1.6 | Build `pwm_ldct_loader` Python data loader; pytest suite verifying schema invariants | Pip-installable package; tests green | **done** — 24 pytest green on synthetic fixture; reads pipeline output; folder-authoritative split discovery (commit `7b94070`) |
| 1.7 | Validate that downstream code (`baselines/`, `reference_method/v0.1/`) consumes the loader without modification | Integration smoke test | **partial** — `baselines/` RED-CNN trains/evals via loader (5 tests green); 3 other methods pluggable; benchmark numbers gated on GPU |

### Phase 2 — Clinical acquisition (D9 + 120 → D9 + 270)

**Deferred to v1.0 per the 2026-05-21 two-stage strategy.** Phase 2 is what makes the v1.0 paper distinct from v0.5; it is not on the v0.5 critical path. The table below is preserved for v1.0 planning.

| # | Task | Output | Status @ v0.5 / v1.0 |
|---|---|---|---|
| 2.1 | IRB submission to UTSW Radiology (gated by Track K — new PI) | IRB approval letter | v1.0 — pending Track K |
| 2.2 | Partner-site MOU; second-vendor acquisition (target ≥ 200 scans) | Signed MOU; raw scans arriving | v1.0 — pending Track K + partner-site recruitment |
| 2.3 | Annotation pipeline: ≥ 2 board-certified radiologists × honoraria; majority-vote ground truth | Annotated cases | v0.5 uses [`schema/annotation_qa_protocol.md`](schema/annotation_qa_protocol.md) on existing LIDC + top-up AAPM/Mayo; v1.0 extends to prospective cohort |
| 2.4 | PHI scrubbing per HIPAA Safe Harbor; verify against DICOM cleaning whitelist | Clean DICOM exports | v1.0 — public data is already de-identified upstream; whitelist applies to prospective acquisitions |
| 2.5 | Build `Dockerfile.utsw_clinical` (consumes clean DICOM, produces HDF5 matching schema) | Working Docker image | v1.0 — pending UTSW data arrival |

### Phase 3 — Paper + listing + content-addressed deposit (D9 + 270 → D9 + 540)

For v0.5 this phase is **brought forward** by ~D9 + 90 because the substrate (Phase 1) is already done. The v0.5 submission window is D9 + 180; the v1.0 window remains D9 + 365–540.

| # | Task | Output | Status @ v0.5 |
|---|---|---|---|
| 3.1 | Draft dataset paper (Methods, Validation, Usage, Code Availability sections) | Draft v1 | **active** — v0.5 manuscript drafted with real prose for Abstract / Background / Methods / Data Records / Usage Notes / Roadmap; placeholders for figures + per-source counts + reproduction table tracked in [`paper_draft/README.md`](paper_draft/README.md) |
| 3.2 | PhysioNet metadata + access docs; submit listing | PhysioNet page live | **drafted** — paste-ready listing in [`physionet_listing/`](physionet_listing/) (Open access / CC BY 4.0); `[CONFIRM]` fields = authors / DOI / IRB / funding |
| 3.3 | Submit paper to *Nature Scientific Data*; revise to acceptance (~6 mo) | Acceptance letter | pending (D9 + 180 submission target) |
| 3.4 | Register the v0.5 dataset manifest on PhysioNet DOI + Zenodo (primary); PWM L3 registry as optional mirror | DOI + Zenodo record + (optional) L3 hash | pending — re-scoped to PhysioNet/Zenodo-first per the 2026-05-25 reframe; L3 registry is no longer the primary anchor |

---

## Timeline (D9-anchored)

D9 anchor ≈ 2026-05-20; today (2026-06-03) is **≈ D9 + 14**. The two-stage strategy reorders the original single-track timeline: the v0.5 Phase 1 substrate landed ahead of schedule, the v0.5 submission window is brought forward to D9 + 180, and the v1.0 critical-path items move to the D9 + 365 → D9 + 540 window.

| Date | Milestone | Status |
|---|---|---|
| D9 + 12 (2026-06-01) | **LIDC-IDRI Docker pipeline** reproducible end-to-end ([`pipelines/`](pipelines/)) | **done** ahead of schedule (was D9 + 30) |
| D9 + 12 (2026-06-01) | **AAPM 2016 Docker pipeline** reproducible end-to-end (unzip + DICOM-CT-PD ingest, commit `a4a14ec`) | **done** ahead of schedule (was D9 + 60) |
| D9 + 12 (2026-06-01) | **Metadata schema ratified** ([`schema/`](schema/), 4 specs); **`pwm_ldct_loader` passes 24 pytest** on synthetic fixture | **done** ahead of schedule (was D9 + 90) |
| D9 + 12 (2026-06-01) | **Cohort count locked**: 208 unique paired-dose / 1,226 unique union (commit `bdd42b7`); deposited under `gs://low-dose-ct/pwm_ldct_v0_5` | **done** |
| D9 + 12 (2026-06-01) | **v0.5 manuscript active** in [`paper_draft/manuscript.tex`](paper_draft/manuscript.tex); PhysioNet listing drafted in [`physionet_listing/`](physionet_listing/) | **active** — `[CONFIRM]` fields = authors / DOI / IRB / funding |
| D9 + 90 | RED-CNN + 3 pluggable baselines benchmarked on v0.5 splits (needs GPU); paper Figure 1 (real-vs-simulated low-dose) generated | pending — gated on GPU access |
| D9 + 180 | **v0.5 paper submitted to *Nature Scientific Data*; PhysioNet DOI + Zenodo deposit live** | pending (v0.5 ship target) |
| D9 + 120 | IRB submitted to UTSW Radiology (v1.0 critical path) | pending — gated on Track K |
| D9 + 270 | UTSW IRB approved; first clinical scans acquired (v1.0 critical path) | pending — gated on Track K + IRB |
| D9 + 365 | v0.5 paper accepted (within ~6 mo of submission); v1.0 prospective acquisition underway | pending |
| D9 + 540 | **v1.0 paper submitted (≥ 500 prospectively-acquired paired scans across ≥ 2 vendors + ≥ 2 sites); v0.5 widely cited** | pending (v1.0 ship target) |

The critical-path leg for **v0.5** is now GPU access and the radiologist top-up annotation campaign on AAPM + Mayo chest cases (months ~D9 + 30 → D9 + 90). The critical-path leg for **v1.0** remains the IRB lag (months 5–9), still exogenous; the v0.5 release plus parallel-tracked WS-2 and WS-3 work absorb that window.

---

## Done when

The two-stage release strategy has two separate ship gates. The intermediate-progress section shows what is already in hand at D9 + 14.

### v0.5 progress at D9 + 14 (intermediate, not terminal)

- [x] Public-data substrate (LIDC-IDRI + AAPM 2016 + Mayo LDCT-PD) staged and reproducibly preprocessed under `pwm_ldct_prep`
- [x] Canonical schema + DICOM cleaning + annotation-QA protocol drafted in [`schema/`](schema/) (4 specs)
- [x] `pwm_ldct_loader` scaffolded; 24 pytest green on synthetic fixture; folder-authoritative split discovery
- [x] Cohort count locked: 208 unique paired-dose / 1,226 unique union; deposited at `gs://low-dose-ct/pwm_ldct_v0_5`
- [x] v0.5 manuscript drafted with real prose for Abstract / Background / Methods / Data Records / Usage Notes / Roadmap ([`paper_draft/manuscript.tex`](paper_draft/manuscript.tex))
- [x] PhysioNet listing drafted (paste-ready; `[CONFIRM]` fields = authors / DOI / IRB / funding)
- [ ] RED-CNN + 3 pluggable baselines benchmarked on v0.5 splits (gated on GPU)
- [ ] Figure 1 (real-vs-simulated low-dose) generated from AAPM 2016 paired-dose training subset
- [ ] Radiologist top-up annotation campaign on AAPM + Mayo chest cases per `schema/annotation_qa_protocol.md`

### v0.5 ship gate (D9 + 180 → D9 + 365)

- [ ] v0.5 paper submitted to *Nature Scientific Data*
- [ ] v0.5 paper accepted (or fallback: *Radiology: Artificial Intelligence*)
- [ ] PhysioNet DOI + Zenodo deposit live for the v0.5 release artifacts
- [ ] `pwm_ldct_loader` v0.5.0 published on PyPI
- [ ] PWM L3 registry mirror entry recorded (optional per the 2026-05-25 reframe)

### v1.0 ship gate (D9 + 365 → D9 + 540, gated on Track K + IRB)

- [ ] ≥ 500 prospectively-acquired paired scans across ≥ 2 vendors and ≥ 2 sites (UTSW + partner; Canon and/or Philips coverage)
- [ ] v1.0 paper submitted and accepted at *Nature Scientific Data*
- [ ] ≥ 3 external research groups have used the v0.5 + v1.0 dataset (early adoption signal across both releases)
- [ ] Per-vendor cross-validation analyses included in v1.0 (extending the v0.5 GE↔Siemens cross-vendor result)

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

- **Two-stage release strategy (decision taken 2026-05-21).** The public-data-only first dataset paper (v0.5) is *no longer a fallback* — it is the **primary current ship target** ([`data_needs.md`](data_needs.md)). v0.5 ships at D9 + 180 using LIDC + AAPM 2016 + Mayo LDCT-PD; v1.0 follows at D9 + 365–540 with the prospective clinical extension. The Track K + IRB lag no longer blocks the first paper; it only governs the second.
- **Track K** (new UTSW PI confirmed) — required for **v1.0** IRB submission and prospective acquisition. v0.5 does not depend on Track K.
- **Forward model** `packages/pwm_core/contrib/modalities/ct_radon.py` — single source of truth for simulated low-dose generation. Do not reimplement.
- **PhysioNet DOI + Zenodo deposit** (primary v0.5 distribution channels per the 2026-05-25 reframe) and the optional [`../pwm_integration/l3_spec.md`](../pwm_integration/l3_spec.md) PWM L3 registry mirror — release payloads depend on this folder's final dataset specs.

---

## Cross-references

**Inside WS-1 (strategy + status):**

- [`data_needs.md`](data_needs.md) — the 2026-05-21 two-stage strategy doc; gap analysis between manuscript claims and actual data; the single canonical source for v0.5 vs v1.0 scoping. Read this first if the two-stage framing is unfamiliar.
- [`paper_draft/README.md`](paper_draft/README.md) — paper_draft folder status; coexistence of `manuscript.tex` (v0.5 active) and `manuscript_v1.tex` (v1.0 preserved); per-section completeness for v0.5.
- [`SUBMISSION_CHECKLIST.md`](SUBMISSION_CHECKLIST.md) — consolidated open-items checklist for the v0.5 submission.
- [`annotation_campaign_plan.md`](annotation_campaign_plan.md) — operational plan for the radiologist top-up annotation campaign on AAPM + Mayo chest cases.

**Inside WS-1 (specs + code):**

- [`schema/`](schema/) — dataset schema, DICOM cleaning spec, annotation QA protocol; the normative documents the manuscript Methods section references.
- [`pwm_ldct_loader/`](pwm_ldct_loader/) — pip-installable loader; the read-side API for the v0.5 release artifacts.
- [`pipelines/`](pipelines/) — Dockerfiles + `pwm_ldct_prep` package; the write-side (DICOM → de-id → harmonize → HDF5 → validate) for each source.
- [`physionet_listing/`](physionet_listing/) — paste-ready PhysioNet listing for the v0.5 submission.

**Sibling workstreams:**

- [`../WS-2_framework/`](../WS-2_framework/) — the signal-equivalence framework's CT validation runs against this dataset. **The cross-workstream flow is bidirectional** (as of D9 + 14): WS-1 → WS-2 carries the v0.5 annotation QA protocol verbatim into WS-2's Methods → Estimator section for ground-truth provenance; WS-2 → WS-1 carries the V3-9 power-sim cohort-sizing implication into both this entry's downstream-user note (`d0569f3`) and the Target specs *Credential-issuance regime* row (`7817fad`). The bidirectional tracking is logged in [`../WS-2_framework/paper_draft/CHANGELOG.md`](../WS-2_framework/paper_draft/CHANGELOG.md)'s v0.3-polish *Downstream-doc propagation* subsection (7-place audit trail). **Downstream-user note (as of D9 + 14):** the WS-2 library [`pwm_dose_equivalence/`](../WS-2_framework/pwm_dose_equivalence/) v0.1.0 alpha is the tool external users will use to compute 5-tuple credentials on WS-1 cohorts (modality-agnostic API; percentile + DeLong estimators; sample-size pre-flight; content-addressed framework hash; 60/60 tests, 100 % line coverage). **Cohort-sizing reality on the v0.5 cohort** (per WS-2's V3-9 non-null power simulation, [`theory/proofs/estimator.md`](../WS-2_framework/theory/proofs/estimator.md) §4a, landed D9 + 14): at WS-2's v0.3 AUC-task default `ε = 0.05` and a typical lung-nodule operating point (AUC ≈ 0.92), the v0.5 cohort of 208 unique paired patients satisfies the **(S3) sample-size formula** in [`theory/proofs/sample_size.md`](../WS-2_framework/theory/proofs/sample_size.md) (n ≈ 130–250 across the typical AUC range), but the empirical **verdict distribution** is dominated by `INDETERMINATE` rather than `PASS`: P(`PASS`) under the null is only ≈ 0.40 at n = 200 and lifts to ≈ 0.94 at n = 500. Downstream users should **expect `INDETERMINATE` verdicts on the v0.5 cohort even for genuinely equivalent methods** — absence of `PASS` is not evidence of non-equivalence, only of insufficient n. For tighter margins (`ε = 0.02`) the cohort is undersized by both the formula and the empirical power criterion; non-AUC metrics (Dice, MAE, contrast-recovery) are well-served at typical `σ_Δ` values within the v0.5 cohort.
- [`../WS-3_reference_method/`](../WS-3_reference_method/) — trains and evaluates on this dataset; its baselines populate v0.5 manuscript Tables.
- [`../WS-4_leaderboard/`](../WS-4_leaderboard/) — community submissions are scored on this dataset's test split.

**PWM integration:**

- [`../pwm_integration/l3_spec.md`](../pwm_integration/l3_spec.md) — public-registry resolver for the v0.5 dataset manifest hash. Per the 2026-05-25 reframe, PhysioNet DOI + Zenodo are the primary deposit / citation channels; the PWM L3 registry is one optional mirror.
