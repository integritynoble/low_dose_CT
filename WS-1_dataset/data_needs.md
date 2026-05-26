# WS-1 — What datasets we still need

A gap analysis between what the WS-1 manuscript [`paper_draft/manuscript.tex`](paper_draft/manuscript.tex) currently claims and what data must actually be in hand to submit to *Nature Scientific Data*. Use this file as the single status doc for dataset acquisition.

Last revised: 2026-05-21.

---

## Release strategy: v0.5 first, then v1.0

**Director decision (2026-05-21):** ship a v0.5 dataset paper using public data only as soon as feasible, then follow up with the full multi-vendor clinical v1.0 once Track K + IRB land. This is the primary plan, not a fallback.

| Release | Data scope | Target submission | Distinguishing claim |
|---|---|---|---|
| **v0.5 (priority)** | Public data only: LIDC-IDRI + AAPM 2016 + Mayo LDCT-PD, harmonized under a single content-addressed schema and the PWM L3 spec | D9 + 180 (within 6 months of mainnet) | First content-addressed, on-chain-anchored, multi-task-annotated harmonization of existing public CT data; substrate the PWM Low-Dose CT Challenge launches against |
| **v1.0** | v0.5 contents + ≥ 500 prospectively-acquired paired-dose multi-vendor multi-site UTSW + partner clinical scans | D9 + 365–540 (gated on Track K + IRB) | Adds real paired-dose acquisitions at multi-vendor scale; closes the cross-vendor evaluation gap that no existing public dataset addresses |

**Why a v0.5 release is publishable on its own.** Even using only public data, v0.5 is the first release to (a) anchor the dataset version to a public-registry content hash so leaderboard submissions are cryptographically tied to a specific frozen benchmark, (b) provide a single unified Python loader / preprocessing pipeline across the three public sources (each currently requires its own re-implementation), (c) provide majority-vote multi-task annotations across all three sources rather than each having its own per-task annotation convention, and (d) ship paired baseline reproductions + 5-tuple credentials per the signal-equivalence framework~\citep{ws2framework}. The v0.5 paper's value is the harmonization layer + the on-chain anchoring + the credential format, not the underlying scans.

**Vendor coverage — corrected 2026-05-26.** The public Mayo LDCT-PD cohort is **two-vendor — ~99 GE and ~101 Siemens patients across both anatomies** (verified from TCIA metadata + a GE projection file). So v0.5 **does** provide real cross-vendor (GE vs Siemens) paired-dose coverage; the earlier "Siemens-only" framing was a factual error and has been corrected throughout the manuscript. What v0.5 still cannot claim: Canon/Philips coverage, prospective/multi-site acquisition, and ≥500-patient scale — those remain v1.0's distinguishing contributions (now re-scoped to prospective + multi-site + additional vendors + new tasks, not "multi-vendor" per se).

**Manuscript implication.** The current [`paper_draft/manuscript.tex`](paper_draft/manuscript.tex) is written for v1.0. Before submitting v0.5, the abstract, Background & Summary, Methods (Cohort recruitment), Data Records (cohort tables), and Limitations sections need a focused rewrite to scope claims to public-data-only. The framework holds; the numbers shift.

---

## 1. Public data — REQUIRED FOR v0.5; start today

These are downloadable now (with free academic registration) and unblock Phase 1 of the dataset pipeline.

| Dataset | Used for | Status | Action |
|---|---|---|---|
| **LIDC-IDRI 50-pt subset** (~10 GB) | Phase 1 pipeline test + lung-nodule task | Free, NBIA registration | Already documented in [`../data_acquisition/lidc_idri_download.md`](../data_acquisition/lidc_idri_download.md) — start the download |
| **LIDC-IDRI full 1,018 patients** (~125 GB) | Larger-cohort downstream-task analysis | Free, NBIA | Phase 2 stretch |
| **AAPM 2016 Low-Dose CT Grand Challenge** (~40 GB) | Real paired-dose comparator; the *only* prior public real-paired dataset | Mayo Clinic email request, **1–2 wk lead time** | Send the email template at [`../data_acquisition/aapm_2016_request.md`](../data_acquisition/aapm_2016_request.md) today — biggest critical-path unblock |
| **Mayo LDCT-and-Projection-Data** (LIDC-scale) | Cited in manuscript Table 1 (dataset-comparison) | TCIA, free with registration | Download alongside LIDC |

---

## 2. Prospective clinical acquisition — REQUIRED FOR v1.0; needs IRB + Track K

These are deferred to v1.0. They cannot be substituted with public data — they are what makes PWM-LDCT v1.0 a new dataset rather than a re-packaging of existing ones. v0.5 ships without them.

| What | Target | Lead time | Blocked by |
|---|---|---|---|
| **Real paired full-dose + 25%-dose CT acquisitions on the same patient** | ≥ 50 patients minimum (paper's stated floor), ideally ≥ 200 across vendors | 6–12 months total | UTSW IRB + Track K (new PI) + partner-site MOU |
| **Multi-vendor coverage** | ≥ 2 of {Siemens, GE, Canon, Philips} | Same | Partner-site recruitment (Year 2) |
| **Multi-site coverage** | UTSW + ≥ 1 partner academic center | Same | Partner-site MOU |
| **Anatomy mix** | Chest (lung-cancer screening) + abdomen (oncology follow-up) | Same | Embedded in IRB-approved protocol |
| **Pediatric subset** | Out of v1 scope; planned as a companion dataset | 12+ months | Deferred |

**Realistic minimum to ship the v1 dataset paper to *Nature Scientific Data***: ~500 paired patients, ≥ 2 vendors, ≥ 2 sites. The 50-real-paired floor comes from the manuscript's stated inclusion criterion in §Methods.

---

## 3. Annotation data — scaled differently for v0.5 vs v1.0

| What | Per-patient cost | v0.5 need | v1.0 need | Status |
|---|---|---|---|---|
| **Lung-nodule bounding boxes (chest scans)** | ≥ 2 board-certified radiologists × per-scan time | Re-use LIDC-IDRI's existing 4-radiologist annotations where present; new annotations only for AAPM 2016 + Mayo LDCT-PD chest cases that lack them | All chest patients (including prospective UTSW cohort) | Panel + protocol not yet set up |
| **Liver-lesion segmentation masks (abdominal scans)** | Same, more time-intensive | Defer or out-of-scope for v0.5 (LIDC is chest-only; AAPM 2016 has limited abdominal) | All abdomen patients | Same |
| **Diagnostic-quality Likert scores** | Per-reconstruction (4 dose levels × 3 recons = 12 scores per patient) | Subset only — score the AAPM 2016 paired-dose cohort across reconstructions | All patients | Same |
| **Inter-rater audit / calibration subset** | 20-patient training set drawn from outside the release | Required once at panel onboarding | Same | Same |

**v0.5 annotation budget**: estimated **~$5K–$15K** because most LIDC-IDRI annotations already exist and the AAPM 2016 + Mayo top-up is small. **v1.0 annotation budget**: estimated **~$25K–$100K** depending on prospective cohort size.

The v0.5 strategy of reusing LIDC's existing 4-radiologist nodule annotations is a substantive cost-saver and a natural-fit for the harmonization story: the v0.5 paper's contribution is a unified loader + schema across heterogeneous existing annotations, not generating new ones.

---

## 4. Phantom + technical-validation data — mostly v1.0

| What | Purpose | v0.5 need | v1.0 need |
|---|---|---|---|
| **AAPM CT performance phantom scans per vendor** | HU-calibration offset measurement (Methods §Cross-vendor harmonization) | Not applicable (no UTSW vendor data in v0.5) | Scan once per participating scanner; ~1 day per site |
| **MTF measurements per reconstruction kernel** | Recorded in `metadata.json` for the kernel-matching analysis | Not applicable | ~1–2 hours per kernel |
| **Real-vs-simulated low-dose comparison subset** | Figure showing sim-vs-real distributional agreement; requires the AAPM 2016 paired data | Required for v0.5 — uses AAPM 2016 paired-dose patients on Siemens hardware | Extended to multi-vendor in v1.0 |

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
| Send AAPM 2016 access-request email to Mayo | Today (1 hour) | Pending |
| LIDC-IDRI 50-patient subset download (NBIA) | 3–6 hours background download | Can start today |
| AAPM 2016 DUA + access link from Mayo | 2–4 weeks after email sent | Blocked on email |
| Mayo LDCT-PD download (TCIA) | 3–6 hours background download | Can start today |
| Build unified loader + harmonized schema across all three sources | 4–6 weeks | Phase 1 |
| Annotation top-up on AAPM + Mayo cases (~$5K–$15K) | 4–8 weeks parallel | Phase 1–2 |
| Baseline reproductions + 5-tuple credentials (WS-2 framework + WS-3 reference method) | 8–10 weeks parallel | Phase 1–2 |
| v0.5 manuscript revision (scope to public-data-only) | 2–3 weeks at end | Phase 2 |
| **v0.5 submitted to *Nature Scientific Data*** | **D9 + 180 (~6 months)** | Target |

The single critical-path item is **AAPM 2016 access**. Send the [`../data_acquisition/aapm_2016_request.md`](../data_acquisition/aapm_2016_request.md) email today.

### For v1.0 (follow-up)

After v0.5 ships, v1.0's critical path is the previously-documented one: **Track K (new UTSW PI) → IRB submission → IRB approval → prospective clinical acquisition → annotation campaign → v1.0 submission**, the multi-month exogenous lag the WS-1 plan budgets for. v1.0 submits at D9 + 365–540 depending on when Track K lands. The v0.5 publication does not consume v1.0's IRB or recruitment budget; it ships in parallel.

---

## Honest comparison: v0.5 vs v1.0 claims

| Claim | v0.5 | v1.0 |
|---|---|---|
| Content-addressed dataset hash on PWM registry | ✅ | ✅ |
| Unified Python loader across multiple CT sources | ✅ | ✅ |
| Majority-vote multi-task annotations | ✅ (reusing LIDC + topping up AAPM/Mayo) | ✅ (full panel campaign) |
| Reproducibility contract (Docker, SHA-256 manifest) | ✅ | ✅ |
| 5-tuple credential framework integration | ✅ | ✅ |
| Multi-vendor coverage | ✅ (GE + Siemens via public Mayo LDCT-PD) | ✅ (adds Canon / Philips, prospective) |
| Real paired-dose acquisitions at ≥ 500-patient scale | ❌ (210: AAPM 10 + public Mayo 200) | ✅ |
| Cross-vendor evaluation API | ◑ (GE↔Siemens leave-one-vendor-out in v0.5) | ✅ (≥ 3 vendors) |
| Pediatric subset | ❌ (deferred to companion dataset) | ❌ (also deferred) |

**The honest v0.5 → v1.0 positioning for *Nature Scientific Data***: v0.5 is the harmonization-layer + content-addressing contribution **plus genuine two-vendor (GE + Siemens) real paired-dose coverage**; v1.0 is the prospective, multi-site, additional-vendor (Canon/Philips), larger-scale, new-clinical-task contribution. Reviewers should see them as two complementary papers, not as competing claims.

---

## Cross-references

- [`paper_draft/manuscript.tex`](paper_draft/manuscript.tex) — the manuscript whose `\todo{}` placeholders depend on the data above being acquired
- [`README.md`](README.md) — WS-1 workstream Goals / Tasks / Timeline / Done when
- [`../data_acquisition/checklist.md`](../data_acquisition/checklist.md) — master acquisition checklist with current status
- [`../data_acquisition/aapm_2016_request.md`](../data_acquisition/aapm_2016_request.md) — Mayo email template (critical-path unblock)
- [`../data_acquisition/lidc_idri_download.md`](../data_acquisition/lidc_idri_download.md) — NBIA download recipe
- [`../WS-5_grants/`](../WS-5_grants/) — R21 funding that could backfill annotation honoraria budget
