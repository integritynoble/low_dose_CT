# WS-1 — Dataset (Track 9 sub-track 9a)

The **PWM Low-Dose CT Benchmark Dataset**: a content-addressed harmonization of multi-source CT data, distributable via PhysioNet + Zenodo, supported by a *Nature Scientific Data* paper. Released in two stages per the 2026-05-21 director decision — see [`data_needs.md`](data_needs.md) for the strategy doc.

> **Status (2026-08-18):** **v0.5 (LIDC-IDRI first release) is the current ship target** — manuscript active in [`paper_draft/manuscript.tex`](paper_draft/manuscript.tex). **v0.5 = LIDC-only: 1,010 LIDC-IDRI patients** (train 589 / val 216 / test 205), each with the inherited 4-radiologist raw annotations + majority-vote consensus; low-dose is **simulated** (projection-domain forward model `projection_domain_v1_gpu`, dose ratios 0.10/0.25/0.50); full-dose real reconstructions + simulated low-dose. **AAPM 2016 + Mayo LDCT-PD are v1.0 roadmap items** and are NOT part of the v0.5 release (no real paired-dose data, no AAPM/Mayo data tree in v0.5). **v1.0 (multi-source + prospective multi-vendor + multi-site extension)** is preserved in [`paper_draft/manuscript_v1.tex`](paper_draft/manuscript_v1.tex) for the D9 + 365–540 submission window once Track K + IRB + clinical acquisition land. The two manuscripts coexist — do not conflate them.

> **AAPM paired held-out baseline (2026-08-21):** AAPM 2016 10 training patients (1mm B30) staged as real FD/QD pairs; split 3/3/4 into [`splits/aapm_{train,val,test}.txt`](splits/aapm_train.txt) + [`splits/split_assignment.csv`](splits/split_assignment.csv). Geometric pairing validated 10/10 (Pearson=1.0, see [`output/aapm_pairing_validation.json`](output/aapm_pairing_validation.json)). Complete held-out baseline run executed on the paired tree — RED-CNN / CTformer / LEARN + permanent Gaussian blur trap, fidelity (PSNR/SSIM/LPIPS) + detectability (CNR/CHO-AUC/NPWE, task_spec SKE-Gaussian 20HU/s2px) per split and per patient: [`output/aapm_paired_baselines_v2.json`](output/aapm_paired_baselines_v2.json) + [`output/aapm_paired_baselines_v2_summary.md`](output/aapm_paired_baselines_v2_summary.md). **Task-spec calibration 2026-08-21 (Rung 1 closed):** the insertion contrast/sigma grid (20–60 HU × 0.5–3 px, + 80HU/4px, disk micro-structures to 240 HU) is **not discriminative** on real anatomy (CHO AUC saturated ≥ 0.92–1.000 for all incl. blur; blur-vs-model AUC gap ≤ 0.02); the calibrated discriminative dimension is the frequency-domain protocol `detectability-freq-v1` (`schema/detectability_task_spec.md` §6): 1-px high-pass band-energy retention (BandER) separates blur (0.247) from RED-CNN (0.636) / CTformer (1.040) / LEARN (0.631) by 2.6–4.2× on the same held-out test, while blur scores the **highest SSIM (0.929)** and comparable PSNR (39.46) — the blur trap is now a demonstrated "high fidelity, low detectability" failure on real anatomy. Remaining before full Rung 1 closure: independent recomputation by a domain verifier.

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
| Patient scans, paired full-dose / reduced-dose | **1,010 LIDC-IDRI patients** (LIDC-only first release; train 589 / val 216 / test 205). Low-dose is **simulated** (projection-domain forward model, dose ratios 0.10/0.25/0.50); no real paired-dose data in v0.5. **AAPM 2016 + Mayo LDCT-PD are v1.0 roadmap items** (208 unique paired-dose / 1,226 unique union once AAPM + Mayo join) | ≥ 500 (stretch 1,000) prospectively acquired + AAPM/Mayo sources |
| Credential-issuance regime (per WS-2 [V3-9 power sim](../WS-2_framework/theory/proofs/estimator.md), D9 + 14; per-modality trio closed at D9 + 15 with V3-10 / V3-11) | For the v1.0 AAPM+Mayo paired-dose cohort at AUC ≈ 0.92 (typical lung-nodule operating point) and the v0.3 AUC default `ε = 0.05`, the cohort would satisfy WS-2's (S3) sample-size formula (n ≈ 130–250 required) **but sits in the empirical INDETERMINATE-dominated regime**: P(`PASS`) under the null ≈ 0.40 at n = 200, lifting to ≈ 0.94 at n = 500. **v0.5 (LIDC-only, simulated low-dose) is not a real paired-dose cohort and is not suited to credential issuance** — downstream users should treat v0.5 as a methodological/data-format release and wait for v1.0 paired-dose for WS-2 credentials. **For Dice-type segmentation tasks at the non-AUC default `ε = 0.02`**, a v1.0 paired cohort would be *comfortably* in the PASS regime per WS-2 V3-10 (`proofs/estimator.md` §4b): at clinical $\sigma_\Delta \approx 0.05$ and n = 200, P(`PASS`) under the null = 1.000. For tighter AUC margins (`ε = 0.02`) the cohort is undersized by both the formula and the empirical power criterion. The CR small-$n$ anti-conservativeness finding from V3-11 (`proofs/estimator.md` §4c) applies once the v1.0 paired cohort exists (n = 208 ≫ 30 in the union once AAPM+Mayo join). | Prospective n ≥ 500 lifts cleanly into the **P(`PASS`) ≈ 0.94** regime at the typical AUC / `ε = 0.05` operating point; supports reliable `PASS` verdicts on equivalent methods and (with the upper end of the cohort range) the tighter `ε = 0.02` margin. For Dice and CR derived tasks, n ≥ 500 is well above all thresholds in WS-2's `proofs/estimator.md` §§4b / 4c. |
| Reduced-dose nature | **v0.5: simulated low-dose only** — LIDC reduced-dose is our Poisson-noise/projection-domain simulation at dose ratios 0.10/0.25/0.50 (forward model `projection_domain_v1_gpu`); no measured real low-dose in v0.5. (v1.0 adds Mayo's validated projection-domain noise-inserted reference for AAPM/Mayo and prospective re-acquired scans.) | Re-acquired paired-dose physical scans (≥ 50 patients) + AAPM/Mayo noise-inserted reference |
| Vendor coverage | **v0.5: LIDC-IDRI four-vendor** (GE / Siemens / Philips / Toshiba; 669 / 201 / 74 / 66), full-dose real reconstructions + simulated low-dose. No GE↔Siemens paired-dose in v0.5. | v1.0 adds **~99 GE + ~101 Siemens** (Mayo LDCT-PD; corrected 2026-05-26) for cross-vendor paired-dose, + Canon and/or Philips via partner-site acquisition (≥ 3 vendors total) |
| Anatomy | Chest (lung-screening primary; LIDC) | Chest + abdomen at multi-site scale (AAPM/Mayo oncology + prospective) |
| Sites | Public source only — LIDC-IDRI (US multi-site consortium); no PHI-bearing institutional acquisition | AAPM 2016 + Mayo LDCT-PD public sources + UTSW lead + ≥ 1 partner academic medical center |
| Annotations | Re-use LIDC-IDRI's 4-radiologist annotations (raw_per_reader + majority-vote consensus) per [`schema/annotation_qa_protocol.md`](schema/annotation_qa_protocol.md) | Same protocol + top-up AAPM/Mayo chest cases + prospective cohort |
| Format | HDF5 shards + harmonized annotations + content-addressed manifest (LIDC) | Same + DICOM-CT-PD projections (AAPM/Mayo) + raw projections from the prospective acquisitions |
| Distribution | PhysioNet DOI + Zenodo (primary); PWM L3 registry as an optional mirror (post-2026-05-25 reframe) | Same |
| Patient-level split | LIDC: 589 / 216 / 205 (train / val / test; 60 / 20 / 20) | Same protocol over the larger cohort |
| Citations target (24 mo post-release) | ≥ 25 (v0.5 alone) | ≥ 50 (combined v0.5 + v1.0) |

---

## Tasks

### Phase 1 — Public-data substrate (D9 + 0 → D9 + 90)

| # | Task | Output | Status @ v0.5 |
|---|---|---|---|
| 1.1 | Download and stage LIDC-IDRI full cohort (NBIA Data Retriever) | Raw DICOM tree on disk | **done** — staged; pipeline runs end-to-end; 1,010 patients in the v0.5 build |
| 1.2 | **(v1.0)** Request AAPM 2016 access (Mayo); 1-2 wk lead time | Access granted; raw DICOM staged | **roadmap** — staged at `gs://low-dose-ct/aapm_2016_grand_challenge/` (52 zips, 174.7 GB); unzip step wired in commit `a4a14ec` |
| 1.3 | Author canonical metadata schema (`schema/dataset_schema.md`) | Schema doc + DICOM cleaning spec | **done** — 4 specs + README in [`schema/`](schema/) |
| 1.4 | Build `Dockerfile.lidc_idri` (HU window, 512×512 resize, simulated low-dose at dose ratios 0.10/0.25/0.50 via `projection_domain_v1_gpu`) | Working Docker image; HDF5 shards | **done** — pipeline built; HDF5 shards land under `hdf5/{train,val,test}/` (589 / 216 / 205) |
| 1.5 | **(v1.0)** Build `Dockerfile.aapm_2016` (uses Mayo projection-domain noise-inserted low-dose) | Working Docker image; HDF5 shards | **roadmap** — pipeline built; AAPM unzip + DICOM-CT-PD projection ingest wired; output is ckey-bucketed |
| 1.6 | Build `pwm_ldct_loader` Python data loader; pytest suite verifying schema invariants | Pip-installable package; tests green | **done** — 24 pytest green on synthetic fixture; reads pipeline output; folder-authoritative split discovery (commit `7b94070`) |
| 1.7 | Validate that downstream code (`baselines/`, `reference_method/v0.1/`) consumes the loader without modification | Integration smoke test | **partial** — `baselines/` RED-CNN trains/evals via loader (5 tests green); 3 other methods pluggable; benchmark numbers gated on GPU |

### Phase 2 — Clinical acquisition (D9 + 120 → D9 + 270)

**Deferred to v1.0 per the 2026-05-21 two-stage strategy.** Phase 2 is what makes the v1.0 paper distinct from v0.5; it is not on the v0.5 critical path. The table below is preserved for v1.0 planning.

| # | Task | Output | Status @ v0.5 / v1.0 |
|---|---|---|---|
| 2.1 | IRB submission to UTSW Radiology (gated by Track K — new PI) | IRB approval letter | v1.0 — pending Track K |
| 2.2 | Partner-site MOU; second-vendor acquisition (target ≥ 200 scans) | Signed MOU; raw scans arriving | v1.0 — pending Track K + partner-site recruitment |
| 2.3 | Annotation pipeline: ≥ 2 board-certified radiologists × honoraria; majority-vote ground truth | Annotated cases | v0.5 uses [`schema/annotation_qa_protocol.md`](schema/annotation_qa_protocol.md) on inherited LIDC 4-reader annotations; **top-up AAPM/Mayo is v1.0**; v1.0 extends to prospective cohort |
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

D9 anchor ≈ 2026-05-20; today (2026-06-05) is **≈ D9 + 16**. The two-stage strategy reorders the original single-track timeline: the v0.5 Phase 1 substrate landed ahead of schedule, the v0.5 submission window is brought forward to D9 + 180, and the v1.0 critical-path items move to the D9 + 365 → D9 + 540 window.

| Date | Milestone | Status |
|---|---|---|
| D9 + 12 (2026-06-01) | **LIDC-IDRI Docker pipeline** reproducible end-to-end ([`pipelines/`](pipelines/)) | **done** ahead of schedule (was D9 + 30) |
| D9 + 12 (2026-06-01) | **(v1.0 roadmap)** AAPM 2016 Docker pipeline reproducible end-to-end (unzip + DICOM-CT-PD ingest, commit `a4a14ec`) | **roadmap** — not part of v0.5 release |
| D9 + 12 (2026-06-01) | **Metadata schema ratified** ([`schema/`](schema/), 4 specs); **`pwm_ldct_loader` passes 24 pytest** on synthetic fixture | **done** ahead of schedule (was D9 + 90) |
| 2026-08-18 | **v0.5 scope locked: LIDC-only 1,010 patients** (train 589 / val 216 / test 205); AAPM/Mayo deferred to v1.0 roadmap | **done** |
| D9 + 12 (2026-06-01) | **v0.5 manuscript active** in [`paper_draft/manuscript.tex`](paper_draft/manuscript.tex); PhysioNet listing drafted in [`physionet_listing/`](physionet_listing/) | **active** — `[CONFIRM]` fields = authors / DOI / IRB / funding |
| D9 + 90 | RED-CNN + 3 pluggable baselines benchmarked on v0.5 LIDC splits (needs GPU); paper Figure 1 (real-vs-simulated low-dose) generated | pending — gated on GPU access |
| D9 + 180 | **v0.5 paper submitted to *Nature Scientific Data*; PhysioNet DOI + Zenodo deposit live** | pending (v0.5 ship target) |
| D9 + 120 | IRB submitted to UTSW Radiology (v1.0 critical path) | pending — gated on Track K |
| D9 + 270 | UTSW IRB approved; first clinical scans acquired (v1.0 critical path) | pending — gated on Track K + IRB |
| D9 + 365 | v0.5 paper accepted (within ~6 mo of submission); v1.0 prospective acquisition underway | pending |
| D9 + 540 | **v1.0 paper submitted (≥ 500 prospectively-acquired paired scans across ≥ 2 vendors + ≥ 2 sites + AAPM/Mayo); v0.5 widely cited** | pending (v1.0 ship target) |

The critical-path leg for **v0.5** is now GPU access and LIDC-only baselines (months ~D9 + 30 → D9 + 90); **AAPM/Mayo top-up annotation is a v1.0 item**, not on the v0.5 critical path. The critical-path leg for **v1.0** remains the IRB lag (months 5–9), still exogenous; the v0.5 release plus parallel-tracked WS-2 and WS-3 work absorb that window.

---

## Done when

The two-stage release strategy has two separate ship gates. The intermediate-progress section shows what is already in hand at D9 + 16.

### v0.5 progress at D9 + 16 (intermediate, not terminal)

- [x] Public-data substrate (**LIDC-IDRI 1,010 patients**) staged and reproducibly preprocessed under `pwm_ldct_prep` (AAPM 2016 + Mayo LDCT-PD pipelines built but **deferred to v1.0**)
- [x] Canonical schema + DICOM cleaning + annotation-QA protocol drafted in [`schema/`](schema/) (4 specs)
- [x] `pwm_ldct_loader` scaffolded; 24 pytest green on synthetic fixture; folder-authoritative split discovery
- [x] v0.5 scope locked: **LIDC-only 1,010 patients** (train 589 / val 216 / test 205); simulated low-dose at 0.10/0.25/0.50 via `projection_domain_v1_gpu`
- [x] v0.5 manuscript drafted with real prose for Abstract / Background / Methods / Data Records / Usage Notes / Roadmap ([`paper_draft/manuscript.tex`](paper_draft/manuscript.tex))
- [x] PhysioNet listing drafted (paste-ready; `[CONFIRM]` fields = authors / DOI / IRB / funding)
- [ ] RED-CNN + 3 pluggable baselines benchmarked on v0.5 LIDC splits (gated on GPU)
- [ ] Figure 1 (real-vs-simulated low-dose) generated from LIDC simulated low-dose
- [ ] *(v1.0)* Radiologist top-up annotation campaign on AAPM + Mayo chest cases per `schema/annotation_qa_protocol.md`

### v0.5 ship gate (D9 + 180 → D9 + 365)

- [ ] v0.5 paper submitted to *Nature Scientific Data*
- [ ] v0.5 paper accepted (or fallback: *Radiology: Artificial Intelligence*)
- [ ] PhysioNet DOI + Zenodo deposit live for the v0.5 release artifacts
- [ ] `pwm_ldct_loader` v0.5.0 published on PyPI
- [ ] PWM L3 registry mirror entry recorded (optional per the 2026-05-25 reframe)

### v1.0 ship gate (D9 + 365 → D9 + 540, gated on Track K + IRB)

- [ ] ≥ 500 prospectively-acquired paired scans across ≥ 2 vendors and ≥ 2 sites (UTSW + partner; Canon and/or Philips coverage)
- [ ] **v1.0** paper submitted and accepted at *Nature Scientific Data* (incl. AAPM 2016 + Mayo LDCT-PD sources)
- [ ] ≥ 3 external research groups have used the v0.5 + v1.0 dataset (early adoption signal across both releases)
- [ ] Per-vendor cross-validation analyses included in v1.0 (extending v0.5 LIDC four-vendor coverage with v1.0 GE↔Siemens paired-dose cross-vendor result)

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

- **Two-stage release strategy (decision taken 2026-05-21; scope update 2026-08-18).** The public-data-only first dataset paper (v0.5) is the **primary current ship target** ([`data_needs.md`](data_needs.md)). **v0.5 ships as LIDC-only (1,010 patients) at D9 + 180**; **AAPM 2016 + Mayo LDCT-PD are deferred to v1.0** (D9 + 365–540) together with the prospective clinical extension. The Track K + IRB lag no longer blocks the first paper; it only governs the second.
- **Track K** (new UTSW PI confirmed) — required for **v1.0** IRB submission and prospective acquisition. v0.5 does not depend on Track K.
- **Forward model** `packages/pwm_core/contrib/modalities/ct_radon.py` — single source of truth for simulated low-dose generation. Do not reimplement.
- **PhysioNet DOI + Zenodo deposit** (primary v0.5 distribution channels per the 2026-05-25 reframe) and the optional [`../pwm_integration/l3_spec.md`](../pwm_integration/l3_spec.md) PWM L3 registry mirror — release payloads depend on this folder's final dataset specs.

---

## Cross-references

**Inside WS-1 (strategy + status):**

- [`data_needs.md`](data_needs.md) — the 2026-05-21 two-stage strategy doc; gap analysis between manuscript claims and actual data; the single canonical source for v0.5 vs v1.0 scoping. Read this first if the two-stage framing is unfamiliar.
- [`paper_draft/README.md`](paper_draft/README.md) — paper_draft folder status; coexistence of `manuscript.tex` (v0.5 active) and `manuscript_v1.tex` (v1.0 preserved); per-section completeness for v0.5.
- [`SUBMISSION_CHECKLIST.md`](SUBMISSION_CHECKLIST.md) — consolidated open-items checklist for the v0.5 submission.
- [`annotation_campaign_plan.md`](annotation_campaign_plan.md) — operational plan for the radiologist top-up annotation campaign on AAPM + Mayo chest cases (**v1.0 scope**; v0.5 reuses LIDC's inherited 4-reader annotations).

**Inside WS-1 (specs + code):**

- [`schema/`](schema/) — dataset schema, DICOM cleaning spec, annotation QA protocol; the normative documents the manuscript Methods section references.
- [`pwm_ldct_loader/`](pwm_ldct_loader/) — pip-installable loader; the read-side API for the v0.5 release artifacts.
- [`pipelines/`](pipelines/) — Dockerfiles + `pwm_ldct_prep` package; the write-side (DICOM → de-id → harmonize → HDF5 → validate) for each source.
- [`physionet_listing/`](physionet_listing/) — paste-ready PhysioNet listing for the v0.5 submission.

**Sibling workstreams:**

- [`../WS-2_framework/`](../WS-2_framework/) — the signal-equivalence framework's CT validation runs against this dataset. **The cross-workstream flow is bidirectional** (as of D9 + 14): WS-1 → WS-2 carries the v0.5 annotation QA protocol verbatim into WS-2's Methods → Estimator section for ground-truth provenance; WS-2 → WS-1 carries the V3-9 power-sim cohort-sizing implication into both this entry's downstream-user note (`d0569f3`) and the Target specs *Credential-issuance regime* row (`7817fad`). The bidirectional tracking is logged in [`../WS-2_framework/paper_draft/CHANGELOG.md`](../WS-2_framework/paper_draft/CHANGELOG.md)'s v0.3-polish *Downstream-doc propagation* subsection (7-place audit trail). **Downstream-user note (as of D9 + 16):** the WS-2 library [`pwm_dose_equivalence/`](../WS-2_framework/pwm_dose_equivalence/) at **v0.2.0 alpha** is the tool external users will use to compute 5-tuple credentials on WS-1 cohorts (modality-agnostic API; percentile + DeLong + BCa estimators; sample-size pre-flight with `bound_M` for unbounded metrics; small-$n$ anti-conservativeness warning for n < 30 non-AUC calls; content-addressed framework hash; 81/81 tests incl. 10 end-to-end integration tests, 100 % line coverage on 265 statements). For reviewers wanting to verify any specific WS-2 numerical claim against the WS-1 cohort or otherwise: [`paper_draft/reproduction_guide.md`](../WS-2_framework/paper_draft/reproduction_guide.md) maps every claim to its repo anchor + the command that re-derives it (16-row per-claim table). For *non-coder* reviewers / regulators / clinicians who need to **interpret a published credential** issued on a WS-1 cohort without re-running the bootstrap: [`paper_draft/credential_reading_guide.md`](../WS-2_framework/paper_draft/credential_reading_guide.md) (added at D9 + 16; v1.1 at D9 + 16) walks the credential JSON field-by-field with verdict semantics (PASS / FAIL / INDETERMINATE), CI vs $\varepsilon$ reading, framework-hash guarantees, the `sample_size_check` field — and **calls out the WS-1 v0.5 INDETERMINATE-dominated regime by name** (at n ≈ 208 / AUC ≈ 0.92, P(`PASS`) ≈ 0.40, lifting to 0.94 at n = 500) so a reviewer reading a credential on this dataset has the cohort-sizing context in hand without having to chase it back to the WS-2 proofs. For those willing to run *one* Python call (no bootstrap re-run needed, no test data needed): the v0.2.1 library exposes `audit_credential(json_dict)` which validates schema, checks the framework hash, re-derives the verdict from the published CI, inspects `sample_size_check.ok` for the undersized-PASS pattern, and flags BCa-as-headline — every check the reading guide describes as "what to look for", in one call. For those who would rather *not* write Python at all: the v0.2.2 library registers a `pwm-audit` console entry point so the same audit runs from the shell (`pwm-audit their_credential.json` for human-readable output; `--json` for machine-readable; `-` for stdin). The exit code is `0` on ok / `1` on hard issue / `2` on I/O error — directly usable in CI hooks and submission-checklist scripts. For tooling that does not have Python at all: a standalone [`credential_schema.json`](../WS-2_framework/pwm_dose_equivalence/credential_schema.json) (D9 + 19) is the draft-07 JSON Schema artifact, usable by `ajv` / JSON-Schema-aware editors / registry validators without any Python dependency. A concrete starting point for downstream WS-1 users: [`pwm_dose_equivalence/examples/valid_ct_lung_nodule.json`](../WS-2_framework/pwm_dose_equivalence/examples/valid_ct_lung_nodule.json) (added D9 + 19) is a clean PASS credential at the v0.5 lung-nodule operating point (n_test = 500, ε = 0.05, DeLong) — the shape a downstream credential issued on a WS-1 cohort would take. For downstream researchers learning how to compute their own credentials on the v0.5 cohort: [`pwm_dose_equivalence/notebooks/`](../WS-2_framework/pwm_dose_equivalence/notebooks/) holds four tutorial notebooks — `01_ct_lung_nodule_auc.py` is the natural starting point for CT-cohort credential issuance against the WS-1 dataset; the companion notebooks cover MRI (`02`) and PET (`03`) for cross-modality reference; and `04_optical_extending.py` (R3-3) is the user-implementable template for researchers in modalities the framework does not yet validate (Optical / OCT / Ultrasound / …) who want to apply the same credential discipline to their own data. **Cohort-sizing reality on the v0.5 cohort** (per WS-2's V3-9 non-null power simulation, [`theory/proofs/estimator.md`](../WS-2_framework/theory/proofs/estimator.md) §4a, landed D9 + 14): at WS-2's v0.3 AUC-task default `ε = 0.05` and a typical lung-nodule operating point (AUC ≈ 0.92), the v0.5 cohort of 208 unique paired patients satisfies the **(S3) sample-size formula** in [`theory/proofs/sample_size.md`](../WS-2_framework/theory/proofs/sample_size.md) (n ≈ 130–250 across the typical AUC range), but the empirical **verdict distribution** is dominated by `INDETERMINATE` rather than `PASS`: P(`PASS`) under the null is only ≈ 0.40 at n = 200 and lifts to ≈ 0.94 at n = 500. Downstream users should **expect `INDETERMINATE` verdicts on the v0.5 cohort even for genuinely equivalent methods** — absence of `PASS` is not evidence of non-equivalence, only of insufficient n. For tighter margins (`ε = 0.02`) the cohort is undersized by both the formula and the empirical power criterion; non-AUC metrics (Dice, MAE, contrast-recovery) are now empirically backed at WS-2 D9 + 15 (per-modality trio closed via V3-10 + V3-11; `proofs/estimator.md` §§4b / 4c) and are well-served at typical `σ_Δ` values within the v0.5 cohort.
- [`../WS-3_reference_method/`](../WS-3_reference_method/) — trains and evaluates on this dataset; its baselines populate v0.5 manuscript Tables.
- [`../WS-4_leaderboard/`](../WS-4_leaderboard/) — community submissions are scored on this dataset's test split.

**PWM integration:**

- [`../pwm_integration/l3_spec.md`](../pwm_integration/l3_spec.md) — public-registry resolver for the v0.5 dataset manifest hash. Per the 2026-05-25 reframe, PhysioNet DOI + Zenodo are the primary deposit / citation channels; the PWM L3 registry is one optional mirror.
