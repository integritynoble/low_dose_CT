# PWM-PET-IQ 1.0 — submission checklist

Maps every `\todo{}` in `paper_draft/manuscript.tex` to the acquisition / analysis /
deposit step that fills it. Verify open items by searching the tree for `\todo{`.

**Gating legend:** 🔴 blocks submission · 🟠 needed but finalizable during review ·
🟢 assigned at acceptance.

---

## 1. Phantom fill & experiment design 🔴 (before any scanning)
- [ ] **Sphere-to-background ratio** (`\todo{SBR}`) — decide (NEMA standard 4:1 or 8:1)
      and record. Appears in abstract, phantom, limitations.
- [ ] **Hot/cold sphere assignment** (`\todo{hot/cold sphere assignment}`).
- [ ] **Background activity concentration** at reference start (`\todo{background conc.}`).
- [ ] **Radiotracer + half-life** (`\todo{radiotracer}`, `\todo{$T_{1/2}$}`).
- [ ] **Count-level plan** — confirm `r ∈ {1.0, 0.50, 0.25, 0.10}` and the number of
      decayed levels `K` (`\todo{K}`, `\todo{levels}`), plus thinned realizations per
      level `N` (`\todo{N}`).

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
