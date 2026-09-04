# PWM-PET-IQ 1.0 — submission checklist

Maps every `\todo{}` in `paper_draft/manuscript.tex` to the acquisition / analysis /
deposit step that fills it. Verify open items by searching the tree for `\todo{`.

**Gating legend:** 🔴 blocks submission · 🟠 needed but finalizable during review ·
🟢 assigned at acceptance.

---

## 1. Phantom fill & experiment design 🔴 (before any scanning)
- [x] **Sphere-to-background ratio** (`\todo{SBR}`) — **design-locked: 4:1**.
      Recorded in `analysis/task_spec.json` + manuscript (Phase A). *(Filled 2026-08-21.)*
- [x] **Hot/cold sphere assignment** (`\todo{hot/cold sphere assignment}`) —
      **design-locked: hot 10–22 mm / cold 28–37 mm**. Recorded in
      `analysis/task_spec.json` + manuscript. *(Filled 2026-08-21.)*
- [ ] **Background activity concentration** at reference start (`\todo{background conc.}`).
- [ ] **Radiotracer + half-life** (`\todo{radiotracer}`, `\todo{$T_{1/2}$}`).
- [x] **Count-level plan** — **design-locked: `r ∈ {1.0, 0.50, 0.25, 0.10}`**, `K` decayed
      levels = 4, thinned realizations per level `N` (value acquisition-independent, chosen
      at Phase A; current draft placeholder). Count levels recorded in
      `analysis/task_spec.json`.

## 1b. Embodied acquisition authorization 🔴 (gates §2, before any scanning)
- [ ] **Read + sign `ACQUISITION_AUTHORIZATION.md`** — names the irreversible act
      (one fill → reference + decayed series at `r ∈ {1.0,0.50,0.25,0.10}`), the grant
      (site PI / radiation-safety office + PWM deposit owner), and the raw-data hosting
      lineage (secured scratch → processing container → PhysioNet/Zenodo; read-only raw,
      two copies). No scanning begins until the signature block is complete.
- [ ] **Record radiation-safety authorization no.** (`\todo{radiation-safety authorization no.}`)
      in the grant block.

## 2. Acquisition 🔴 (produces the dataset the descriptor is about)
- [ ] **Scanner model + TOF/PSF capability** (`\todo{scanner model}`, `\todo{TOF/PSF...}`).
- [ ] **Reference activity (MBq)** and **frame durations** (`\todo{reference activity}`,
      `\todo{reference frame duration}`, `\todo{decayed frame duration}`).
- [ ] **Decayed acquisitions across tracer decay** at each target `r` — the physical
      reduced-activity references. Record decay timepoints / elapsed times / decay-corrected
      activities → `metadata.json`.
- [ ] **Dose-calibrator model + cross-calibration window** (`\todo{dose-calibrator model}`,
      `\todo{cross-calibration window}`).
- [ ] **Radiation-safety authorization no.** (`\todo{radiation-safety authorization no.}`).

## 3. Processing & reconstruction 🔴
- [ ] **List-mode Poisson thinning** — implement seeded thinner
      `(series_id, r, realization_index)`; emit `thinning/seed_recipe.json`. Confirm
      bit-for-bit regeneration (Technical Validation `tab:reproducibility`).
- [ ] **Reconstruction protocol** — fix algorithm/iterations/subsets/matrix/voxel/PSF/TOF/
      post-filter/corrections (`\todo{algorithm}` … `\todo{post-filter}`); pin in a container.
- [ ] **FBP reference** per series where toolchain permits (`\todo{FBP availability}`).
- [ ] **`ground_truth.json`** — sphere diameters, measured fill concentrations
      (decay-corrected per series), true contrasts, NEMA 12-region ROI geometry.
- [ ] **`metadata.json`** — per-series acquisition + reconstruction params, count levels,
      seeds, randoms fractions.

## 4. Technical Validation numbers 🔴 (gated on §2–§3, committed analysis scripts)
- [ ] **`tab:acq_params`** — regenerate every cell from `metadata.json` (currently all
      provisional/`\todo`).
- [ ] **`fig:examples`** — representative slices per count level.
- [ ] **`tab:crc`** — contrast-recovery coefficient per sphere × count level vs ground truth
      (primary endpoint).
- [ ] **`fig:cnr_vs_count`** — background variability + CNR vs count level.
- [ ] **`fig:decayed_vs_thinned`** — Bland–Altman decayed vs thinned; randoms/noise-texture
      deltas (**the key validation**).
- [ ] **`tab:reproducibility`** — across-realization mean/variance + seed-regeneration check.

## 5. Deposit & identifiers 🔴 (data must be deposited at submission)
- [ ] **Deposit all records to PhysioNet** → **PhysioNet DOI** (fills `\todo{PhysioNet URL}`,
      `\todo{DOI}`). Phantom = no DUA, so deposit list-mode/sinograms/recon in full.
- [ ] **Confirm list-mode redistribution license** (`\todo{confirm list-mode redistribution
      license}`) — if vendor format is non-redistributable, deposit sinograms +
      `seed_recipe.json` so thinned realizations remain reproducible.
- [ ] **Mirror to Zenodo** → **Zenodo DOI** (`\todo{Zenodo DOI}`).
- [ ] **No long embargo:** make both records **public at manuscript submission** (Scientific Data
      requires data available to reviewers at submission and public on publication; target
      submission→publication ≤ 6 months, zero embargo by design — phantom data has no DUA, so
      nothing here should need one).
- [ ] **Choose license** (`\todo{license}`) — recommend CC BY 4.0 (records) / Apache 2.0 (code).
- [ ] **Publish `pwm_pet_iq` loader to PyPI**; add `pipelines/` + `analysis/` to the repo
      (Code Availability `\todo`s).

## 6. Manuscript finalization 🔴
- [ ] Fill **author list / CRediT / competing interests / acknowledgments** `\todo`s.
- [ ] Replace **placeholder refs** in `refs.bib` (`lowcountpet`, `reader2021artificial`) with
      authoritative citations; backfill WS-1/WS-2 DOIs.
- [ ] **Rebuild** (`pdflatex ×2 + bibtex`); confirm 0 errors and **no stray `\todo`**.
- [ ] Transcribe the **Nature Reporting Summary**.

---

### Design note — why the decayed-vs-thinned pairing matters
The single most novel, reviewer-defensible element is that the dataset provides, for the
*same* phantom geometry, both a **physically-decayed** reduced-activity acquisition and a
**seeded list-mode-thinned** realization at matched count levels. That makes
`fig:decayed_vs_thinned` a real measurement of the thinning-model error that most low-count
PET work (and the WS-2 PET `T_r`) assumes. Do not cut it to save scanner time.

---

## 7. Phased acquisition timeline (milestones & dependencies)

All dates are D9-anchored (D9 = 2026-05-20, PWM mainnet launch). The workflow is currently
**SKELETON** (analysis scripts done; no phantom data). Each phase gates the next; check the
dependency column before starting. Durations assume a single scanner + one fill session with
sequential decayed acquisitions; parallelize Phases C–D where the scanner schedule allows.

| Phase | Milestone | Inputs / dependencies | Exit criterion | Target window |
|---|---|---|---|---|
| **A. Design freeze** | SBR (4:1 or 8:1), hot/cold sphere assignment, background conc., radiotracer + T₁/₂, count levels `r∈{1.0,0.50,0.25,0.10}`, `K` decayed levels, `N` thinned realizations | §1 decisions; NEMA NU-2 standard; WS-2 PET `T_r` spec (count-level plan must match WS-2) | §1 checklist all checked; decisions recorded in `analysis/design_log.md` | D9 + 90 → D9 + 150 |
| **B. Site & scanner** | Scanner model + TOF/PSF, radiation-safety authorization no., dose-calibrator model, cross-calibration window | Institution / imaging-site partnership; local radiation-safety office; scanner vendor docs | §2 scanner + safety items checked; scan time booked | D9 + 120 → D9 + 180 |
| **C. Acquisition** | One phantom fill → reference full-count scan → sequential decayed scans at each `r` (physics-limited: requires tracer decay between levels; ~2–3 half-lives total) | Phase A + B; phantom filled per §1; dose calibrator cross-calibrated | §2 acquisition items complete; raw list-mode/DICOM + `metadata.json` staged to secured scratch storage | D9 + 180 → D9 + 240 |
| **D. Processing & reconstruction** | Seeded Poisson thinner `(series_id, r, realization_index)` → `seed_recipe.json`; fixed recon protocol in container; FBP reference; `ground_truth.json` + `metadata.json` frozen | Phase C raw data; §3 spec; `analysis/extract_roi_means.py` (ROI stub replaced by real VOI geometry) | §3 items complete; bit-for-bit thinning regeneration demo passes on 1 series | D9 + 210 → D9 + 280 |
| **E. Technical validation** | `tab:crc`, `fig:cnr_vs_count`, `fig:decayed_vs_thinned` (Bland–Altman), `tab:reproducibility` from `analysis/nema_metrics.py` + `analyze_phantom.py` | Phase D outputs; committed analysis scripts (already tested: 6/6) | §4 tables/figures regenerable from committed scripts + data | D9 + 240 → D9 + 310 |
| **F. Deposit & identifiers** | PhysioNet DOI (primary) + Zenodo mirror DOI; list-mode redistribution license confirmed; CC BY 4.0 / Apache 2.0 chosen; `pwm_pet_iq` on PyPI | Phase E; license/legal review; PhysioNet account | §5 all checked; both DOIs minted and cited in manuscript | D9 + 280 → D9 + 330 |
| **G. Manuscript & submission** | All `\todo{}` replaced; rebuild clean; Nature Reporting Summary | Phase F DOIs; WS-1/WS-2 companion DOIs | §6 complete; submission to *Scientific Data* (align with WS-2 manuscript cycle) | D9 + 300 → D9 + 365 |

**Key dependencies to protect:**
- **Phase C is the schedule-critical path.** A single fill only yields the decayed sequence once;
  missed timepoints force a refill (new fill activity must be re-planned → returns to Phase A
  count-level plan). Book the longest contiguous scanner window first.
- **Phase A's count-level plan must be locked before Phase C** because the decayed levels are
  determined by elapsed physical decay, not by request.
- **Phase F's license check gates deposit only, not scanning** — but the vendor
  list-mode-format redistribution question (§5) must be answered **before Phase C raw files are
  archived**, since non-redistributable formats change what gets deposited (sinograms + seeds
  instead of raw list-mode).
- **Phase G aligns with WS-2** (WS-2b is the Data-Descriptor companion to the WS-2 framework
  paper; the WS-2 PET `T_r` validation consumes this dataset's decayed-vs-thinned comparison).
- **Buffer:** add +4 weeks slack to Phase C for refill/scanner-schedule risk; do not compress
  E–F (they are mechanical once D is done).
