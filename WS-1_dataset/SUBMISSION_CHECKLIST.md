# PWM-LDCT v0.5 — consolidated submission checklist

Every open item across the WS-1 v0.5 package (manuscript, schema, code, PhysioNet listing, Reporting
Summary, cover letter), with its source file. Verify by searching the tree for `\todo{` (LaTeX) and
`[CONFIRM]` (everything else). Grouped by what unblocks each item.

**Version scope:** v0.5 = **LIDC-IDRI first release** (1,010 patients, 4 readers/case, majority-vote
consolidation, simulated low-dose at dose ratios 0.10/0.25/0.50). **AAPM 2016 + Mayo LDCT-PD are
v1.0 roadmap items** and are not part of the v0.5 deposit (no real paired-dose data, no AAPM/Mayo
data tree in v0.5).

**Gating legend:** 🔴 blocks submission · 🟠 needed but can finalize during review · 🟢 assigned at
acceptance.

---

## 0. Completed since this checklist was created ✅
- **Corrections:** vendor (LIDC four-vendor; GE/Siemens v1.0) · real-vs-noise-inserted low-dose
  wording — manuscript + specs reconciled, compiles.
- **Software substrate built + tested:** DICOM-CT-PD projection reader (GE + Siemens, validated on
  real data; v1.0 inputs) · LIDC nodule-XML→annotation converter (awaits the XMLs, §3) ·
  reconstruction-sanity harness · `pwm_ldct_baselines` (RED-CNN; others pluggable).
- **v0.5 LIDC build:** 1,010 LIDC patients harmonized (train 589 / val 216 / test 205); simulated
  low-dose records generated via projection-domain forward model (`projection_domain_v1_gpu`,
  dose ratios 0.10/0.25/0.50); full-dose real reconstructions + simulated low-dose.
- **Low-dose simulation:** in-repo projection-domain Eq. 1 implemented, optimized (scikit-image
  radon/iradon, ~7×), and **first-order calibrated** against the Mayo L004 reference (25%;
  `I0_REF=1e8` → ~24 HU vs the 18.9 HU reference). Refinement still advised (§5).
- **Submission docs drafted:** PhysioNet listing, Nature Reporting Summary, cover letter.

## 1. People & declarations 🔴
> **Fill-in template for all of §1** (roster, CRediT role matrix, ready-to-paste title block /
> contributions / COI statements, IRB + funding fields) — `paper_draft/author_metadata.md`.
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
> **Mechanics for all of §2** — packaging, manifest/content-hash, Zenodo+PhysioNet upload, PyPI,
> public repo, and the DOI backfill — are in `physionet_listing/deposit_procedure.md`.
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

## 3. Annotation records 🟠 (LIDC inherited labels; top-up is v1.0)
- [ ] **Source the LIDC nodule XMLs** (not in the image-only bucket pull) — steps in
  `../data_acquisition/lidc_xml_acquisition.md` (Method A: NBIA Data Retriever, XMLs co-located;
  Method B: standalone TCIA XML set + remap). Converter ready (`pipelines/pwm_ldct_prep/lidc_annotations.py`).
- [x] **LIDC four-radiologist raw labels + majority-vote consolidation** — v0.5 reuses the inherited
  LIDC annotations (4 readers/case; consensus requires ≥3-of-4 per `annotation_qa_protocol.md` §3);
  per-reader raw labels preserved in `annotations/raw_per_reader/`; inter-rater κ reported in
  `tab:irr_v05` (real LIDC results, see §5).
- [ ] **(v1.0) Recruit radiologist panel; run calibration → top-up → Likert → adjudication** per
  `schema/annotation_qa_protocol.md` — operational plan (scope: AAPM/Mayo chest nodule top-up +
  Likert; panel, tooling, timeline, ~$9–12K budget, deliverables) in `annotation_campaign_plan.md`.
  Produces the top-up + Likert records and the v1.0 κ values.
- [ ] **Annotation budget figure** — `manuscript.tex` `\todo{\$X}` (v1.0 top-up; LIDC reuse has no
  new annotation cost).

## 4. Data acquisition & v1.0 roadmap builds 🟠 (v0.5 LIDC build done)
- [x] **v0.5 LIDC harmonized build** — 1,010 patients (train 589 / val 216 / test 205); full-dose
  real reconstructions + simulated low-dose records (0.10/0.25/0.50) via `projection_domain_v1_gpu`.
- [ ] **(v1.0) Mayo LDCT-PD** downloaded + harmonized recon build (199 patients; see
  `../data_acquisition/` notes).
- [ ] **(v1.0) AAPM 2016 access** (Mayo email, `data_acquisition/aapm_2016_request.md`) — required for
  the v1.0 sim-vs-reference validation; **first verify** the challenge cases aren't already in the
  public TCIA collection we have.
- [ ] **(v1.0) Reconcile the AAPM 2016 ∩ Mayo LDCT-PD overlap** against the authoritative challenge
  patient manifest — steps + decision tree in
  `../data_acquisition/aapm_mayo_overlap_reconciliation.md` (de-dup machinery already in place;
  finalizes the v1.0 union count).
- [ ] **(v1.0) Run AAPM + Mayo harmonized builds** (`run_mayo.py` pattern / the AAPM & Mayo
  Dockerfiles) → fills their cohort + demographics + acquisition rows in the v1.0 manuscript.
- [ ] **(v1.0) Regenerate the Mayo sim in GCS with the calibrated model** — deferred to GPU/cluster
  (~125 h on this CPU even optimized; a partial GCS refresh would break the content-hash manifest,
  so do it within a full regeneration). The eventual run picks up `I0_REF=1e8` automatically.

## 5. Technical Validation & Data Records numbers 🔴 (v0.5 LIDC numbers; v1.0 items marked)
- [ ] **Baseline method selection** — choose the 3 non-RED-CNN baselines: `manuscript.tex`
  `\todo{select published method...}` (transformer e.g. CTformer/TransCT; diffusion; unrolled e.g.
  LEARN). Register them in `baselines/.../models/__init__.py`.
- [ ] **Baseline results** `tab:baselines_v05` (PSNR/SSIM/LPIPS per dose) — run `pwm_ldct_baselines`
  on a **GPU** per `baselines/RUN_PLAN.md` (method candidates, compute ~50–120 GPU-h, protocol,
  data-quality prereq: calibrated-sim regen or real-LD-only subset). **v0.5 trains on the LIDC-only
  split**; AAPM/Mayo data are v1.0 roadmap inputs.
- [ ] **Harmonization validation** `tab:harmonization_v05` — v0.5: LIDC single-source consistency
  (per-scan Reconstruction-sanity + HU-histogram checks); **Wasserstein threshold (HU)** `\todo`.
  (Cross-source comparison is a v1.0 item when AAPM/Mayo join.)
- [ ] **Annotation-reuse fidelity** Supplementary table — `manuscript.tex` `\todo{ref}`.
- [ ] **Reconstruction-sanity FP tolerance** `\todo{FP tolerance}` — harness in
  `pipelines/pwm_ldct_prep/recon_sanity.py` (helical FBP still needs calibrated geometry).
- [ ] **(v1.0) Sim-vs-reference figure** `fig:sim_vs_real_v05` — the sim is first-order calibrated
  (≈24 HU vs 18.9 HU reference on Mayo L004); the v1.0 figure needs the per-anatomy runs (chest via
  r=0.10, abdomen via r=0.25) and ideally per-scanner `I0`/`σ_e` refinement. v0.5 reports the
  simulated low-dose records with calibration provenance, not a real-reference comparison.
- [x] **Inter-rater reliability** `tab:irr_v05` — **filled with real LIDC results** (see
  `annotation_qa_protocol.md` §5): anon group (677 cases) detection Cohen's κ 0.926–0.997 (all six
  pairs ≥ 0.60 gate); texture linearly-weighted κ 0.330–0.471 (disclosed as low); reader1–4 (21
  cases) 0.243–0.751; anonymous (6 cases) 0.748–1.000; Likert ICC(2,k) not covered (no Likert
  series in v0.5). Reader-ID naming is inconsistent across groups (four schemes) and not merged.
  ⚠️ **Integrity flag (found 2026-07):** the earlier LIDC row (7,060 nodules / 623 patients / 3.64
  readers / 81.9%) was **not reproduced from any committed artifact** and is replaced by the
  per-pair κ computed from `raw_per_reader` (see `interrater_metrics.py`). The LIDC XML sourcing
  (§3) remains open for the annotation-reuse-fidelity check.
- [ ] **(Supplementary, optional) credentials** `tab:credentials_v05` — depends on the companion
  WS-2 framework; severable.
- [ ] **Demographics table** — age med(IQR)/range, sex m/f(%), BMI, scan-date (LIDC row; v1.0 adds
  AAPM/Mayo rows; `\todo` ×~20) — extract from source DICOM headers.
- [ ] **Acquisition table** — v0.5 keeps the LIDC row; AAPM/Mayo rows are marked v1.0 roadmap
  (`\todo{varies}` ×4). ⚠️ **Provenance flag (found 2026-07):** the *already-filled* cells
  (demographics LIDC 61 yr / 140-141; acquisition LIDC manufacturer 669/201/74/66, mAs medians) are
  **not reproduced from any committed artifact**, and the acquisition caption claims they are
  "extracted from the deposited `metadata.json`". Regenerate every filled cell from a committed
  extraction script before submission, or mark provisional. Flagged inline with `\todo` in both
  captions.
- [ ] **Cohort table** — v0.5: LIDC-only rows (train 589 / val 216 / test 205 / total 1,010);
  AAPM/Mayo rows are v1.0 roadmap (`\todo{$\sim$…}`).
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
- [ ] Confirm **v0.5 LIDC cohort = 1,010** (589/216/205) everywhere, **no AAPM/Mayo rows in v0.5
  tables** (marked v1.0 roadmap), and figures are real PDFs.

---

## Appendix — placeholder index (verified by sweep, 2026-05-27)
Reproduce with: `grep -rn '\\todo{' WS-1_dataset/paper_draft/manuscript.tex` and
`grep -rn '\[CONFIRM' WS-1_dataset`.

**Manuscript `\todo`:** 53 `\todo{` occurrences across 29 lines; 3 are non-fillable (1 status
comment + the `\todotable`/`\todofig` macro defs) → **50 fillable placeholders** (RESULTS
tables/figures + the §1–§6 fields above).

**`[CONFIRM]` markers — three classes** (raw `grep -o` counts; each deliverable also has ~1
convention-header mention that is descriptive, not fillable):

*(A) Submission deliverables — must clear before submit:*
| File | decision `[CONFIRM]` |
|---|---|
| `physionet_listing/listing.md` | 8 |
| `paper_draft/reporting_summary.md` | 7 |
| `paper_draft/cover_letter.md` | 3 |
| `schema/dataset_schema.md` | 2 (HU offsets) |
| `pipelines/pwm_ldct_prep/harmonize.py` | 2 (HU offsets) |
| `schema/annotation_qa_protocol.md` | 1 |

*(B) Operational planning docs — `[CONFIRM]` = before-kickoff decisions; persist until that activity runs:*
| File | decision `[CONFIRM]` |
|---|---|
| `annotation_campaign_plan.md` | 7 |
| `baselines/RUN_PLAN.md` | 7 |
| `physionet_listing/deposit_procedure.md` | 4 |

*(C) Pre-registered schema defaults `[CONFIRM:…]` — intentionally retained (14 total):* κ ≥ 0.60,
nodule-match IoU ≥ 0.3, OCR confidence ≥ 60 (+ the campaign honorarium estimate), mirrored across
`annotation_qa_protocol.md` / `dicom_cleaning_spec.md` / `annotation_campaign_plan.md`. Ratify the
values; do not blank them.

Totals across the package: **58 decision `[CONFIRM]`** + **14 default `[CONFIRM:…]`** (the remainder
of the 58 beyond A+B are meta/convention references in this checklist and the READMEs).

> Low-dose-sim `I0_REF` is now calibrated (no longer a `[CONFIRM]`), but per-scanner/anatomy
> refinement remains recommended (§5).

> **Submission gate:** all manuscript `\todo{}` and every class-(A) `[CONFIRM]` must be cleared;
> class-(C) schema defaults may be kept (ratify the values); class-(B) markers clear as each
> activity (campaign / GPU run / deposit) completes.
