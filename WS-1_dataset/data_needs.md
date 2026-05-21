# WS-1 — What datasets we still need

A gap analysis between what the WS-1 manuscript [`paper_draft/manuscript.tex`](paper_draft/manuscript.tex) currently claims and what data must actually be in hand to submit to *Nature Scientific Data*. Use this file as the single status doc for dataset acquisition.

Last revised: 2026-05-21.

---

## 1. Public data — start today

These are downloadable now (with free academic registration) and unblock Phase 1 of the dataset pipeline.

| Dataset | Used for | Status | Action |
|---|---|---|---|
| **LIDC-IDRI 50-pt subset** (~10 GB) | Phase 1 pipeline test + lung-nodule task | Free, NBIA registration | Already documented in [`../data_acquisition/lidc_idri_download.md`](../data_acquisition/lidc_idri_download.md) — start the download |
| **LIDC-IDRI full 1,018 patients** (~125 GB) | Larger-cohort downstream-task analysis | Free, NBIA | Phase 2 stretch |
| **AAPM 2016 Low-Dose CT Grand Challenge** (~40 GB) | Real paired-dose comparator; the *only* prior public real-paired dataset | Mayo Clinic email request, **1–2 wk lead time** | Send the email template at [`../data_acquisition/aapm_2016_request.md`](../data_acquisition/aapm_2016_request.md) today — biggest critical-path unblock |
| **Mayo LDCT-and-Projection-Data** (LIDC-scale) | Cited in manuscript Table 1 (dataset-comparison) | TCIA, free with registration | Download alongside LIDC |

---

## 2. Prospective clinical acquisition — needs IRB + Track K

These do not exist yet and **cannot be substituted with public data** — they are what makes PWM-LDCT a new dataset rather than a re-packaging of existing ones.

| What | Target | Lead time | Blocked by |
|---|---|---|---|
| **Real paired full-dose + 25%-dose CT acquisitions on the same patient** | ≥ 50 patients minimum (paper's stated floor), ideally ≥ 200 across vendors | 6–12 months total | UTSW IRB + Track K (new PI) + partner-site MOU |
| **Multi-vendor coverage** | ≥ 2 of {Siemens, GE, Canon, Philips} | Same | Partner-site recruitment (Year 2) |
| **Multi-site coverage** | UTSW + ≥ 1 partner academic center | Same | Partner-site MOU |
| **Anatomy mix** | Chest (lung-cancer screening) + abdomen (oncology follow-up) | Same | Embedded in IRB-approved protocol |
| **Pediatric subset** | Out of v1 scope; planned as a companion dataset | 12+ months | Deferred |

**Realistic minimum to ship the v1 dataset paper to *Nature Scientific Data***: ~500 paired patients, ≥ 2 vendors, ≥ 2 sites. The 50-real-paired floor comes from the manuscript's stated inclusion criterion in §Methods.

---

## 3. Annotation data — needs radiologist panel

| What | Per-patient cost | Per-paper need | Status |
|---|---|---|---|
| **Lung-nodule bounding boxes (chest scans)** | ≥ 2 board-certified radiologists × per-scan time | All chest patients | Panel + protocol not yet set up |
| **Liver-lesion segmentation masks (abdominal scans)** | Same, more time-intensive | All abdomen patients | Same |
| **Diagnostic-quality Likert scores** | Per-reconstruction (4 dose levels × 3 recons = 12 scores per patient) | All patients | Same |
| **Inter-rater audit / calibration subset** | 20-patient training set drawn from outside the release | Once, at panel onboarding | Same |

Annotation honoraria are a real budget item — typically $50–$200 per scan for radiologist time. Estimated total: **~$25K–$100K** depending on cohort size and panel rate.

---

## 4. Phantom + technical-validation data

| What | Purpose | Status |
|---|---|---|
| **AAPM CT performance phantom scans per vendor** | HU-calibration offset measurement (Methods §Cross-vendor harmonization) | Scan once per participating scanner; ~1 day per site |
| **MTF measurements per reconstruction kernel** | Recorded in `metadata.json` for the kernel-matching analysis | ~1–2 hours per kernel |
| **Real-vs-simulated low-dose comparison subset** | Figure 1 (sim_vs_real); requires the AAPM 2016 paired data above | Blocked on AAPM access |

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

The single longest item is **AAPM 2016 access**: 1–2 weeks for the Mayo response, then 1–2 weeks for DUA + UTSW pre-award sign-off. **Send the access-request email today** from a UTSW-affiliated address; everything else can proceed in parallel.

After AAPM access is in hand, the next critical path is **Track K (new UTSW PI) → IRB submission → IRB approval → prospective clinical acquisition**, which is the multi-month exogenous lag the WS-1 plan budgets for in its 24-month timeline.

---

## Fallback: a v0.5 "public-data only" preview

If the prospective clinical acquisition slips, we can ship a v0.5 dataset paper using **only public data** (LIDC + AAPM 2016 + Mayo LDCT-PD), framed as the substrate the leaderboard launches against, with the multi-vendor clinical extension positioned as a v1.0 follow-up. This fallback is documented in the WS-1 [`README.md`](README.md) Dependencies section and preserves the Year-1 publication target if Track K slips past D9 + 270.

Trade-off: v0.5 cannot make the multi-vendor or real-paired-acquisition claims that distinguish PWM-LDCT from existing public datasets. *Nature Scientific Data* may push back on novelty; the fallback positioning has to be honest about the v0.5 → v1.0 progression.

---

## Cross-references

- [`paper_draft/manuscript.tex`](paper_draft/manuscript.tex) — the manuscript whose `\todo{}` placeholders depend on the data above being acquired
- [`README.md`](README.md) — WS-1 workstream Goals / Tasks / Timeline / Done when
- [`../data_acquisition/checklist.md`](../data_acquisition/checklist.md) — master acquisition checklist with current status
- [`../data_acquisition/aapm_2016_request.md`](../data_acquisition/aapm_2016_request.md) — Mayo email template (critical-path unblock)
- [`../data_acquisition/lidc_idri_download.md`](../data_acquisition/lidc_idri_download.md) — NBIA download recipe
- [`../WS-5_grants/`](../WS-5_grants/) — R21 funding that could backfill annotation honoraria budget
