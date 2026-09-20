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
- [x] **Baseline method selection** — **closed, re-verified 2026-09-11 at HEAD `cb88439`:** the three
  non-RED-CNN baselines are chosen and registered in
  `baselines/src/pwm_ldct_baselines/models/__init__.py` (`_REGISTRY` = `ctformer` / `corediff` /
  `learn`, plus the standing `blur` trap) — transformer (CTformer), diffusion (CoreDiff),
  unrolled-iterative (LEARN). The `\todo{select published method...}` placeholder no longer exists in
  `manuscript.tex` (0 `\todo{`).
- [x] **Baseline results** `tab:baselines_v05` (PSNR/SSIM/LPIPS per dose) — **filled, re-verified
  2026-09-11:** the four methods plus the blur trap were evaluated on the same **n = 764** test slices
  at every dose level, and `tab:baselines_v05` / `tab:detectability_v05` are regenerated from the
  committed harness results by the committed `analysis/extract_baselines_tables.py` (build provenance:
  5 result files, combined SHA-256
  `14bd54f64b3004d6726d00c395f85bf42878d9392be54111db067b9b9774472d`); the per-model JSONs ship in
  `baselines/results/`. **v0.5 trains on the LIDC-only split**; AAPM/Mayo data are v1.0 roadmap inputs.
- [x] **Harmonization validation** `tab:harmonization_v05` — v0.5: LIDC single-source consistency
  (per-scan Reconstruction-sanity + HU-histogram checks); **Wasserstein threshold** set to **150 HU**
  (smallest round bound above the worst observed vendor pair, 144.9 HU, Philips-Toshiba), values
  regenerated by the committed `analysis/extract_harmonization_table.py` (pooled aggregate, 160 HU bins,
  up to 26 slices/series; build provenance: 120 metadata files, combined SHA-256
  `42d8803c11df8850cca117654cc2d2a7b3c06d8576bdf41b423a3013c00c5738`). The previously published
  200 HU threshold and its 199.3 HU worst pair traced to an uncommitted `hv_fast.py` and were replaced.
  (Cross-source comparison is a v1.0 item when AAPM/Mayo join.)
- [x] **Annotation-reuse fidelity** Supplementary table — **float reference in place, re-verified
  2026-09-11:** `manuscript.tex` §Annotation-reuse fidelity (L373) cites
  `Supplementary Table~\ref{tab:mv_reconciliation_supp}` (label at L403) and enumerates the 17
  attribute-level discrepancies; the `\todo{ref}` placeholder is gone. Sourcing the LIDC nodule XMLs
  (§3 of this checklist) remains the open prerequisite for the underlying check itself.
- [x] **Reconstruction-sanity FP tolerance** — **resolved, re-verified 2026-09-11:** the released
  tolerance is **$\leq$ 0.5 HU at every voxel**. `manuscript.tex` §Reconstruction sanity reports the
  per-voxel comparison completed for all **1{,}008** non-simulated LIDC scans (maximum per-voxel
  absolute difference 0.344 HU; maximum mean absolute error 0.167 HU; 100% of voxels within 1 HU), and
  the `\todo{FP tolerance}` placeholder is gone. Harness:
  `pipelines/pwm_ldct_prep/recon_sanity.py` (the AAPM 2016 helical-FBP sinogram path stays v1.0).
- [ ] **(v1.0) Sim-vs-reference figure** `fig:sim_vs_real_v05` — **partly realised, superseded as of
  2026-09-11:** `manuscript.tex` now carries the AAPM 2016 validation-subset subsection
  "Simulation vs. reference noise-inserted low-dose" (L409–417) with
  `figures/fig_sim_vs_real_v05.png` included and a simulation/reference noise ratio of
  0.982 ± 0.017 over 10 patients — i.e. the real-reference comparison **is** now reported, so the
  earlier "v0.5 reports ... not a real-reference comparison" wording is no longer accurate. Still open:
  the per-anatomy runs (chest via r=0.10, abdomen via r=0.25) and the per-scanner `I0`/`σ_e`
  refinement (see §0's "Refinement still advised" note).
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
- [x] **Demographics table** — **regenerated from a committed artifact, re-verified 2026-09-11:** the
  LIDC row of `tab:demographics_v05` is produced by the committed `analysis/extract_demographics.py`
  from `metadata.json` (build provenance: 1,010 files, combined SHA-256
  `20476a8105319e6192eebf233e274a4f6f5f787a574bd605809963f3160df870`), so the cells previously flagged
  as "not reproduced from any committed artifact" now are; the `\todo` ×~20 placeholders are gone.
  (v1.0 adds the AAPM/Mayo rows.)
- [x] **Acquisition table** — **provenance flag closed, re-verified 2026-09-11:** the LIDC row of
  `tab:acquisition_v05` is regenerated by the committed `analysis/extract_acquisition.py` from
  `metadata.json` (build provenance: 1,010 files, combined SHA-256
  `20476a8105319e6192eebf233e274a4f6f5f787a574bd605809963f3160df870`); the 2026-07 provenance flag
  ("already-filled cells not reproduced from any committed artifact") is therefore closed and the
  caption `\todo`s are gone. (v1.0 keeps AAPM/Mayo as roadmap rows.)
- [x] **Cohort table** — **filled, re-verified 2026-09-11:** `tab:cohort_v05` in `manuscript.tex`
  carries the LIDC rows (train 589 / val 216 / test 205 / total 1,010, with the caption's provenance
  "1,018 canonical LIDC patients, 8 unavailable in the public distribution used here"), marks the
  AAPM 2016 row (4 / 2 / 4 / 10) as the v1.0 validation subset, and records Mayo LDCT-PD as out of
  scope; the `\todo{$\sim$…}` placeholder is gone.
- [ ] **Errata triage SLA** — **maintenance date closed, SLA still open (re-verified 2026-09-11):**
  `manuscript.tex` now states the source maintenance status "as of 2026-06", so the `\todo{date}` is
  gone, and the errata policy is described (GitHub issues with an `errata-v0.5` label, batched PATCH
  releases) — but it still names **no numeric triage SLA**, so this line stays open for that decision.

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
Reproduce with:
```bash
grep -rn '\\todo{' WS-1_dataset/paper_draft/manuscript.tex
grep -rn '\[CONFIRM' WS-1_dataset
```

**Manuscript `\todo` (2026-05-27 sweep — retained as history, superseded):** 53 `\todo{` occurrences
across 29 lines; 3 are non-fillable (1 status comment + the `\todotable`/`\todofig` macro defs) →
**50 fillable placeholders** (RESULTS tables/figures + the §1–§6 fields above).

> **Dated amendment 2026-09-11 — placeholder index re-swept at HEAD `cb88439`.** The **submission**
> manuscript `paper_draft/manuscript.tex` (757 lines) now contains **0 `\todo{`** and **0
> `\todotable` / `\todofig`** — the 53/50 above is the 2026-05-27 state and is kept only as history.
> Two consequences for reading this appendix:
> 1. The §1/§2 fields that are still open (author list, CRediT, COI, IRB number, funding; PhysioNet /
>    Zenodo DOIs) are carried in the manuscript as **natural-language placeholders**, not `\todo{}`
>    macros — e.g. `\textit{Authors to be confirmed at submission}`, "DOI (to be assigned at
>    submission)" ×2, "To be completed at submission using the CRediT taxonomy". A `\todo`-only sweep
>    therefore **under-reports** the paper's open fields; the §1–§6 tracking items in this checklist
>    remain the authoritative open list.
> 2. Non-submitted drafts still carry `\todo`s and are unaffected (deliberately preserved, not in the
>    submission package): `manuscript_tex_pre_ctformer_retrain.tex` (pre-retrain archive) and
>    `manuscript_v1.tex` (v1.0 target).
> The `[CONFIRM]` index below is unchanged from the 2026-05-27 sweep and was **not** re-derived in this
> refresh; the `\todo` counts in this block supersede the numbers above.

> **Dated amendment 2026-09-18 — appendix counts re-verified at HEAD `3823498` (full-repo sweep).**
> 1. Submission manuscript `paper_draft/manuscript.tex` still contains **0 `\todo{`** (re-verified);
>    the **53/50 counts above are the 2026-05-27 historical value**, kept only as history.
> 2. `manuscript_v1.tex` (v1.0 target draft, **non-current — not in the submission package**)
>    still carries **62 `\todo{`** occurrences; `manuscript_tex_pre_ctformer_retrain.tex`
>    (pre-retrain archive, non-current) carries 10.
> 3. Full-repo sweep 2026-09-18: **388 `\todo`-family markers across 37 files** (md/tex/py;
>    regex `\todo\{|\todotable|\todofig`), of which this checklist itself accounts for 22 and the
>    non-current WS-2b / WS-3 / WS-4 manuscripts for the bulk.
> 4. Full-repo `[CONFIRM]` sweep 2026-09-18: **83 markers across 18 files**; **81 are substantive
>    decision markers** (unchanged from the 2026-09-15 audit). The **2 remaining markers are grep
>    command-example lines** — this appendix (L190) and `physionet_listing/deposit_procedure.md`
>    (L111) — now fenced as code blocks below so they are not miscounted as decision markers.
> The per-file tables in Appendices A/B/C below remain the 2026-05-27 snapshot and are
> **historical values**; per-file counts have since drifted (e.g. `listing.md` now 7 `[CONFIRM]`,
> `reporting_summary.md` 9, `cover_letter.md` 6 — full table in PENDING_ITEMS_AUDIT_2026-09-18.md).

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
