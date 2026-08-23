# WS-1 — What datasets we still need

A gap analysis between what the WS-1 manuscript [`paper_draft/manuscript.tex`](paper_draft/manuscript.tex) currently claims and what data must actually be in hand to submit to *Nature Scientific Data*. Use this file as the single status doc for dataset acquisition.

Last revised: 2026-08-21.

---

## Release strategy: v0.5 first, then v1.0

**Director decision (2026-08-21):** ship a v0.5 dataset paper using public data only as soon as feasible, then follow up with a v1.0 release scoped to **public sources only**: LIDC-IDRI simulated-dose primary corpus + the AAPM 2016 10-patient real-paired validation subset. **Mayo LDCT-PD and prospective clinical acquisition are NOT available and are removed from all v1.0 planning.** This is the primary plan, not a fallback.

| Release | Data scope | Target submission | Distinguishing claim |
|---|---|---|---|
| **v0.5 (priority)** | Public data only: **LIDC-IDRI (1,010 patients)** with inherited four-radiologist annotations and simulated low-dose (projection-domain thinning, 0.10/0.25/0.50), harmonized under a single content-addressed schema and the PWM L3 spec. **AAPM 2016 is a v1.0 roadmap addition and is NOT in v0.5.** | D9 + 180 (within 6 months of mainnet) | First content-addressed, on-chain-anchored, single-source harmonization of LIDC with simulated low-dose under a unified schema; substrate the PWM Low-Dose CT Challenge launches against |
| **v1.0** | v0.5 contents + **AAPM 2016 (10 training patients, FD+QD geometric pairing)** as a real-paired **validation subset**; LIDC-IDRI remains the primary simulated-dose corpus | D9 + 365–540 | Adds a real paired-dose reference (Siemens, 1 mm B30) for validation of the simulated-dose primary corpus, with DICOM-geometry pairing verification (Pearson > 0.99). No scale or multi-vendor claim |

**Why a v0.5 release is publishable on its own.** Even with a single public source, v0.5 is the first release to (a) anchor the dataset version to a public-registry content hash so leaderboard submissions are cryptographically tied to a specific frozen benchmark, (b) provide a single unified Python loader / preprocessing pipeline for LIDC (whose raw distribution currently requires its own re-implementation), (c) provide majority-vote multi-task annotations reusing LIDC's existing four-radiologist labels, and (d) ship paired baseline reproductions + 5-tuple credentials per the signal-equivalence framework~\citep{ws2framework}. The v0.5 paper's value is the harmonization layer + the on-chain anchoring + the credential format, not the underlying scans.

**Vendor coverage — v0.5 vs v1.0.** v0.5 is a **single-source, four-vendor image-only release** (LIDC-IDRI spans GE, Siemens, Philips, Toshiba; no sinograms, no real paired-dose). v1.0 keeps LIDC-IDRI as the primary simulated-dose corpus and adds the **AAPM 2016 10-patient real-paired validation subset** (Siemens, 1 mm B30, FD+QD geometric pairing) — a validation, not a scale claim. Mayo LDCT-PD and prospective clinical acquisition are **not included** in any release plan. What the project still cannot claim at v1.0: sinogram/paired-dose data at scale, prospective/multi-site acquisition, and ≥500-patient real-paired scale.

**Manuscript implication.** [`paper_draft/manuscript.tex`](paper_draft/manuscript.tex) has been rewritten for v0.5 as LIDC-only, with v1.0 scoped to LIDC simulated-dose primary corpus + AAPM 2016 10-patient real-paired validation subset; Mayo LDCT-PD and prospective clinical acquisition statements (including ≥500-patient and IRB-gated claims) are removed. The framework holds; the numbers reflect the public-source cohorts only.

---

## 1. Public data — REQUIRED FOR v0.5; start today

These are downloadable now (with free academic registration) and unblock Phase 1 of the dataset pipeline.

| Dataset | Used for | Status | Action |
|---|---|---|---|
| **LIDC-IDRI 50-pt subset** (~10 GB) | Phase 1 pipeline test + lung-nodule task | Free, NBIA registration | Already documented in [`../data_acquisition/lidc_idri_download.md`](../data_acquisition/lidc_idri_download.md) — start the download |
| **LIDC-IDRI full 1,018 patients** (~125 GB) | v0.5 release cohort (1,010 patients after availability filters) | Free, NBIA | Phase 1 download; v0.5 ships this source only |
| **AAPM 2016 Low-Dose CT Grand Challenge** (~175 GB: ~19 GB image + ~156 GB DICOM-CT-PD projections) | **v1.0 real-paired validation subset**: noise-insertion low-dose comparator (Mayo projection-domain noise insertion, not re-acquired); the *only* prior public dataset with such a paired low-dose reference | Box shared link (obtained 2026-05-28); staged at `gs://low-dose-ct/aapm_2016_grand_challenge/`; locally staged at `E:\AAPM_staged\` | **Done** — downloaded & verified (52 zips, 174.7 GB). Paired FD+QD exists only for the 10 training patients; testing is QD-only (FD withheld). **Mayo LDCT-PD is not in the v1.0 scope; AAPM 2016 is the only real-paired source.** |

---

## 2. Prospective clinical acquisition — REMOVED FROM ALL RELEASE PLANS

~~These are deferred to v1.0. They cannot be substituted with public data — they are what makes PWM-LDCT v1.0 a new dataset rather than a re-packaging of existing ones. v0.5 ships without them.~~

**Not available (2026-08-21):** prospective clinical acquisition is **removed from all release plans**. There is no Track K / IRB-gated pathway, no multi-vendor multi-site recruitment, and no ≥500-patient prospective cohort in v1.0. The v1.0 scope is public sources only (LIDC-IDRI + AAPM 2016). The former prospective rows (real paired full-dose + 25%-dose acquisitions, multi-vendor coverage, multi-site coverage, anatomy mix, pediatric subset) are deleted; the realistic-minimum-to-ship claim of ~500 paired patients no longer applies to v1.0.

---

## 3. Annotation data — scaled differently for v0.5 vs v1.0

| What | Per-patient cost | v0.5 need | v1.0 need | Status |
|---|---|---|---|---|
| **Lung-nodule bounding boxes (chest scans)** | ≥ 2 board-certified radiologists × per-scan time | **Re-use only** — LIDC-IDRI's existing 4-radiologist annotations (converted by `pipelines/pwm_ldct_prep/lidc_annotations.py`); **no new top-up in v0.5** | LIDC primary + AAPM 2016 chest cases as validation subset | Panel + protocol not yet set up (v1.0) |
| **Liver-lesion segmentation masks (abdominal scans)** | Same, more time-intensive | Defer or out-of-scope for v0.5 (LIDC is chest-only) | All abdomen patients | Same |
| **Diagnostic-quality Likert scores** | Per-reconstruction (4 dose levels × 3 recons = 12 scores per patient) | **Not in v0.5** (Likert needs paired-dose scans, which are v1.0 roadmap) | All patients (AAPM 2016 paired-dose cohort first) | Same |
| **Inter-rater audit / calibration subset** | 20-patient training set drawn from outside the release | Not required for v0.5 (LIDC annotations are inherited; reliability is reported from the existing four readers, see `tab:irr_v05`) | Required once at panel onboarding | Same |

**v0.5 annotation budget**: **~$0** — LIDC annotations already exist (four radiologists/case) and are converted, not re-collected. **v1.0 annotation budget**: estimated **~$2K–$4K** for the AAPM 2016 validation-subset top-up + Likert (see `annotation_campaign_plan.md`); the former AAPM/Mayo/prospective budget estimate no longer applies.

The v0.5 strategy of reusing LIDC's existing 4-radiologist nodule annotations is a substantive cost-saver and a natural-fit for the harmonization story: the v0.5 paper's contribution is a unified loader + schema over the inherited LIDC annotations plus simulated low-dose, not generating new annotations.

---

## 4. Phantom + technical-validation data — mostly v1.0

| What | Purpose | v0.5 need | v1.0 need |
|---|---|---|---|
| **AAPM CT performance phantom scans per vendor** | HU-calibration offset measurement (Methods §Cross-vendor harmonization) | Not applicable (no AAPM vendor data in v0.5) | AAPM 2016 Siemens subset only (public phantom data); no per-site scanning |
| **MTF measurements per reconstruction kernel** | Recorded in `metadata.json` for the kernel-matching analysis | Not applicable | ~1–2 hours per kernel |
| **Real-vs-simulated low-dose comparison subset** | Figure showing sim-vs-real distributional agreement; requires the AAPM 2016 paired data | **Not in v0.5** — deferred to v1.0 with the AAPM 2016 source (v0.5 reports only simulated low-dose fidelity checks) | Uses AAPM 2016 10 training patients on Siemens hardware (single-vendor validation, not multi-vendor) |

---

## What we explicitly do NOT need

The manuscript intentionally does not claim:

- Long-term follow-up clinical outcomes (this is not a longitudinal study)
- Patient-reported outcomes (Year-3 stretch per [`../WS-4_leaderboard/`](../WS-4_leaderboard/))
- Genomic / proteomic linkage
- Cardiac-gated CT
- Dual-energy CT (single-energy only in v1)

Scope creep into any of these would push v1 submission well past D9 + 365 and is not currently justified.

---

## Critical-path summary

### For v0.5 (priority)

| Step | Lead time | Status |
|---|---|---|
| LIDC-IDRI 50-patient subset download (NBIA) | 3–6 hours background download | Can start today |
| LIDC-IDRI full 1,018-patient download (NBIA) | 6–12 hours background download | Can start today |
| Build unified loader + harmonized schema for the LIDC source (simulated low-dose, projection-domain thinning) | 4–6 weeks | Phase 1 |
| Convert inherited 4-radiologist LIDC annotations (`lidc_annotations.py` → `lidc_majority_vote/`) | 1 week | Phase 1 |
| Compute inter-rater reliability (`interrater_metrics.py`) and baselines | 1–2 weeks (GPU needed for baselines) | Phase 1 |
| **AAPM 2016 access-request email to Mayo** | — | **v1.0 validation-subset data already staged; not blocking v0.5** |
| **AAPM 2016 DUA + access link from Mayo** | — | **v1.0 validation-subset data already staged; not blocking v0.5** |
| Baseline reproductions + 5-tuple credentials (WS-2 framework + WS-3 reference method) | 8–10 weeks parallel | Phase 1–2 |
| v0.5 manuscript finalize (LIDC-only scope) | 2–3 weeks at end | Phase 2 |
| **v0.5 submitted to *Nature Scientific Data*** | **D9 + 180 (~6 months)** | Target |

The single critical-path item for v0.5 is **LIDC-IDRI full download + the LIDC harmonized build** (simulated low-dose, annotation conversion, reliability/baselines). AAPM 2016 access is **v1.0 roadmap only and does not block v0.5**.

### For v1.0 (follow-up)

After v0.5 ships, v1.0's critical path is the previously-documented one, **re-scoped to public sources only**: **AAPM 2016 (10 training patients, FD+QD paired) integration → held-out paired-dose validation run → annotation top-up on the AAPM validation subset → v1.0 submission**. Mayo LDCT-PD and prospective clinical acquisition (Track K / IRB / UTSW) have been **removed from the v1.0 plan (2026-08-21)** and no longer gate any milestone. v1.0 submits at D9 + 365–540 depending on when the AAPM validation pipeline lands; the v0.5 publication does not consume v1.0's remaining budget and ships in parallel.

---

## Honest comparison: v0.5 vs v1.0 claims

| Claim | v0.5 | v1.0 |
|---|---|---|
| Content-addressed dataset hash on PWM registry | ✅ | ✅ |
| Unified Python loader across the released source | ✅ (LIDC single source) | ✅ (LIDC + AAPM validation subset) |
| Majority-vote multi-task annotations | ✅ (inherited LIDC 4-reader annotations, `lidc_majority_vote/`) | ✅ (adds AAPM top-up + Likert on validation subset) |
| Reproducibility contract (Docker, SHA-256 manifest) | ✅ | ✅ |
| 5-tuple credential framework integration | ✅ | ✅ |
| Multi-vendor coverage | ✅ (four vendors in LIDC images: GE, Siemens, Philips, Toshiba) | ✅ (four-vendor LIDC simulation + AAPM Siemens real validation) |
| Real paired-dose acquisitions | ❌ (simulated low-dose only; no real paired-dose in v0.5) | ◑ (AAPM 2016 10 patients, Siemens, validation nature — does not carry a scale claim) |
| Cross-vendor evaluation API | ◑ (LIDC-only vendor holdout in v0.5) | ◑ (LIDC 4-vendor holdout + AAPM Siemens validation; no multi-vendor real paired claim) |
| Pediatric subset | ❌ (deferred to companion dataset) | ❌ (also deferred) |

**The honest v0.5 → v1.0 positioning for *Nature Scientific Data***: v0.5 is the harmonization-layer + content-addressing contribution on the LIDC source with **simulated low-dose coverage** (projection-domain thinning) and inherited four-reader annotations; v1.0 adds the AAPM 2016 public source as a **real-paired validation subset** (10 patients, Siemens), making the simulation-vs-reference discrepancy measurable at a scale sufficient for validation but **not** for multi-vendor or scale claims. Reviewers should see them as two complementary papers, not as competing claims.

---

## Cross-references

- [`paper_draft/manuscript.tex`](paper_draft/manuscript.tex) — the manuscript whose `\todo{}` placeholders depend on the data above being acquired
- [`README.md`](README.md) — WS-1 workstream Goals / Tasks / Timeline / Done when
- [`../data_acquisition/checklist.md`](../data_acquisition/checklist.md) — master acquisition checklist with current status
- [`../data_acquisition/aapm_2016_request.md`](../data_acquisition/aapm_2016_request.md) — AAPM 2016 access-request template (historical; data already staged at `E:\AAPM_staged\`)
- [`../data_acquisition/lidc_idri_download.md`](../data_acquisition/lidc_idri_download.md) — NBIA download recipe
- [`../WS-5_grants/`](../WS-5_grants/) — R21 funding that could backfill annotation honoraria budget
