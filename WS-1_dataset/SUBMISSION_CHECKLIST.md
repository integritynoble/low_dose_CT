# PWM-LDCT v0.5 — consolidated submission checklist

Every open item across the WS-1 v0.5 package (manuscript, schema, code, PhysioNet listing, Reporting
Summary, cover letter), with its source file. Verify by searching the tree for `\todo{` (LaTeX) and
`[CONFIRM]` (everything else). Grouped by what unblocks each item.

**Gating legend:** 🔴 blocks submission · 🟠 needed but can finalize during review · 🟢 assigned at
acceptance.

---

## 1. People & declarations 🔴
- [ ] **Author list, affiliations, ORCIDs, corresponding author** — `paper_draft/manuscript.tex`
  title block ("Authors to be confirmed") + `\todo{}` Author contributions (CRediT);
  `paper_draft/cover_letter.md`; `physionet_listing/listing.md`.
- [ ] **CRediT contribution statement** — `manuscript.tex` Author contributions `\todo`.
- [ ] **Per-author competing interests** (PWM Protocol Foundation: equity/tokens/consulting/board) —
  `manuscript.tex` Competing interests `\todo`; mirrored in listing + cover letter.
- [ ] **IRB non-human-subjects / exempt determination number** (obtain the letter; cite the number) —
  `manuscript.tex` Ethics `\todo{IRB determination no.}`; `listing.md`; `reporting_summary.md`;
  `cover_letter.md`.
- [ ] **Funding / grant numbers** — `physionet_listing/listing.md`; add to manuscript Acknowledgements.

## 2. Repository deposit & identifiers 🔴 (data must be deposited at submission)
- [ ] **Deposit the value-added records to PhysioNet** (annotations, metadata, splits, manifest,
  LIDC-derived sim, code) → obtain **PhysioNet DOI** — fills `manuscript.tex` `\todo{prefix}` (×2),
  `\todo{PhysioNet URL}`; `listing.md`; `reporting_summary.md`; `cover_letter.md`. Use `listing.md`
  as the submission content.
- [ ] **Mirror to Zenodo** → **Zenodo DOI** — `manuscript.tex` `\todo{Zenodo DOI}` (×2); listing;
  reporting summary; cover letter.
- [ ] **(Optional) IPFS CID** — `manuscript.tex` `\todo{CID}` (demoted to an optional mirror; can omit).
- [ ] **Publish `pwm_ldct_loader` to PyPI** — Code Availability link in `manuscript.tex`.
- [ ] **Make the GitHub repo public** so every Code-Availability URL resolves
  (`github.com/integritynoble/low_dose_CT`).
- [ ] 🟢 **Scientific Data paper DOI** — assigned at acceptance; backfill `listing.md` associated
  publication.

## 3. Annotation campaign 🔴 (produces the new data records the descriptor is built on)
- [ ] **Source the LIDC nodule XMLs** (not in the image-only bucket pull; NBIA Data Retriever / TCIA
  LIDC-XML set) — converter ready (`pipelines/pwm_ldct_prep/lidc_annotations.py`).
- [ ] **Recruit radiologist panel; run calibration → top-up → Likert → adjudication** per
  `schema/annotation_qa_protocol.md`. Produces the AAPM/Mayo top-up + Likert records and the κ values.
- [ ] **Annotation budget figure** — `manuscript.tex` `\todo{\$X}`.

## 4. Data acquisition & remaining harmonization builds 🟠
- [x] **Mayo LDCT-PD** downloaded + harmonized recon build → `gs://low-dose-ct/pwm_ldct_v0_5`
  (199 patients; cohort row filled with real splits 118/37/44).
- [ ] **AAPM 2016 access** (Mayo email) — required for the sim-vs-reference validation figure.
- [ ] **Run LIDC + AAPM harmonized builds** (`run_mayo.py` pattern / the LIDC & AAPM Dockerfiles) →
  fills their cohort + demographics + acquisition rows.

## 5. Technical Validation & Data Records numbers 🔴 (gated on §3–§4 + a GPU)
- [ ] **Baseline method selection** — choose the 3 non-RED-CNN baselines: `manuscript.tex`
  `\todo{select published method...}` (transformer e.g. CTformer/TransCT; diffusion; unrolled e.g.
  LEARN). Register them in `baselines/.../models/__init__.py`.
- [ ] **Baseline results** `tab:baselines_v05` (PSNR/SSIM/LPIPS per dose) — run `pwm_ldct_baselines`
  on a **GPU** against the dataset.
- [ ] **Cross-source harmonization** `tab:harmonization_v05` + **Wasserstein threshold (HU)** `\todo`.
- [ ] **Annotation-reuse fidelity** Supplementary table — `manuscript.tex` `\todo{ref}`.
- [ ] **Reconstruction-sanity FP tolerance** `\todo{FP tolerance}` — harness in
  `pipelines/pwm_ldct_prep/recon_sanity.py` (helical FBP still needs calibrated geometry).
- [ ] **Sim-vs-reference figure** `fig:sim_vs_real_v05` (AAPM).
- [ ] **Inter-rater reliability** `tab:irr_v05` + **κ threshold** `\todo{$\kappa$ threshold}` (from §3).
- [ ] **(Supplementary, optional) credentials** `tab:credentials_v05` — depends on the companion
  WS-2 framework; severable.
- [ ] **Demographics table** — age med(IQR)/range, sex m/f(%), BMI, scan-date (×4 sources each;
  `\todo` ×~20) — extract from source DICOM headers.
- [ ] **Acquisition table** — LIDC scanner models / effective mAs / pitch `\todo{varies}` (×4).
- [ ] **Cohort table** — LIDC + AAPM train/val/test estimates + union totals `\todo{$\sim$…}`
  (Mayo row already real).
- [ ] **Source maintenance-status date** `\todo{date}`; **errata triage SLA** `\todo{N}` business days.

## 6. Schema pre-registered parameters 🟠 (ratify; the manuscript and specs must agree)
- [ ] **Per-source HU offsets** — `pipelines/pwm_ldct_prep/harmonize.py` `HU_OFFSET` `[CONFIRM]`
  (default 0.0); + `schema/dataset_schema.md` `[CONFIRM]`.
- [ ] **Annotation κ threshold** `[CONFIRM: 0.60]` (calibration + drift) — `annotation_qa_protocol.md`;
  must equal the manuscript `\todo{$\kappa$ threshold}`.
- [ ] **Nodule-match / discordance IoU** `[CONFIRM: 0.3]` (×2) — `annotation_qa_protocol.md`.
- [ ] **OCR confidence threshold** `[CONFIRM: 60]` — `schema/dicom_cleaning_spec.md`.

## 7. Final assembly (just before submission) 🔴
- [ ] Choose **access policy / license** on PhysioNet = Open / CC BY 4.0 (per `listing.md`); confirm
  it suits all deposited records.
- [ ] **Transcribe `reporting_summary.md`** into the official Nature Portfolio Reporting Summary PDF.
- [ ] **Backfill all DOIs** (PhysioNet, Zenodo, paper) into manuscript + listing + cover letter +
  reporting summary; ensure the **Data/Code Availability** statements match across all four.
- [ ] **Rebuild `manuscript.pdf`** (pdflatex ×2 + bibtex) and confirm 0 errors + no stray `\todo`.
- [ ] Confirm **Mayo cohort = 199** everywhere (already corrected) and figures are real PDFs.

---

## Appendix — placeholder index (for verification)
`\todo{}` count is in `manuscript.tex`; `[CONFIRM]` counts per file:

| File | markers |
|---|---|
| `paper_draft/manuscript.tex` | ~45 `\todo{}` (tables/figures + fields above) |
| `physionet_listing/listing.md` | 8 `[CONFIRM]` |
| `paper_draft/reporting_summary.md` | 6 `[CONFIRM]` |
| `paper_draft/cover_letter.md` | 3 `[CONFIRM]` |
| `schema/dataset_schema.md` | 2 `[CONFIRM]` |
| `schema/annotation_qa_protocol.md` | κ/IoU `[CONFIRM:…]` |
| `schema/dicom_cleaning_spec.md` | OCR `[CONFIRM: 60]` |
| `pipelines/pwm_ldct_prep/harmonize.py` | 2 `[CONFIRM]` (HU offsets) |

> Sweep before submitting: `grep -rn '\\todo{' WS-1_dataset/paper_draft/manuscript.tex` and
> `grep -rn '\[CONFIRM' WS-1_dataset` must both come back empty (except the schema `[CONFIRM:…]`
> defaults you choose to keep).
