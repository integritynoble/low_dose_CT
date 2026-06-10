# WS-3 corpus — deposit checklist (*Scientific Data* Data Descriptor)

Gating checklist for depositing the **derived-reconstruction corpus** and
submitting the Data Descriptor (`paper_draft/manuscript.tex`) to *Scientific
Data*. Nothing in the manuscript's Technical Validation can be filled until the
corpus exists and is deposited; this checklist is the path from
"manuscript shell" to "submittable."

Order matters: **generate → validate → package → deposit → fill manuscript →
submit**. Do not request a DOI before the corpus is frozen, and do not submit
before the DOI is minted.

---

## 0. Preconditions (gated on WS-3 Phase 3, D9+270)

- [ ] v1 deep ensemble (5 seeds) trained on the **real** WS-1 training split — not synthetic placeholders.
- [ ] Cross-vendor leave-one-vendor-out models trained (one per held-out vendor).
- [ ] Five baselines reproduced within ≤ 0.5 dB PSNR of published numbers, each run through the identical emit path.
- [ ] Frozen lung-nodule detector pinned (single version, held constant across all methods).

*Scientific Data will not review a Data Descriptor whose data records do not
exist. This section is the real blocker — everything below is mechanical once
it clears.*

---

## 1. Corpus generation (produce every record)

For every `{vendor × scan_id × dose r∈{010,025,050,100}}` in the **test** split:

- [ ] `recon_mean.nii.gz` — ensemble-mean reconstruction (HU, float32, `512×512×Z`).
- [ ] `uncertainty_sigma.nii.gz` — per-pixel ensemble std dev, same grid/dtype.
- [ ] `error_abs.nii.gz` — `|recon − full_dose_ref|`, same grid/dtype.
- [ ] `task_nodule_score.nii.gz` — frozen-detector score map on the reconstruction.
- [ ] `credential.json` — signal-equivalence credential (see §4).
- [ ] `scan_meta.json` — vendor, `r`, anatomy, split, **WS-1 source `scan_id`** (back-link).
- [ ] Same six fields emitted for each of the 5 baselines under `baselines/<method>/...`.
- [ ] `credentials/all_credentials.jsonl` — flat index of every `credential.json`.
- [ ] `checksums_and_versions.json` — exact library pins used for generation.

Directory layout must match `paper_draft/manuscript.tex` §Data Records exactly
(reusers and the manuscript manifest must agree).

---

## 2. Technical-validation artifacts (feed the manuscript tables)

Compute on the held-out test split and save the raw numbers + the figure source:

- [ ] Fidelity: PSNR / SSIM / LPIPS per method × dose, with 95% bootstrap CIs (B=1000) → `tab:reconstruction_quality`.
- [ ] Cross-vendor: leave-one-vendor-out PSNR Δ per held-out vendor → `tab:cross_vendor`.
- [ ] **Uncertainty↔error agreement: Spearman ρ (per-pixel + per-case) per dose, with CI** → `tab:uq_calibration`. *(The load-bearing reuse validation — do not skip.)*
- [ ] Reliability diagram (predicted σ vs observed error) → `fig:reliability`.
- [ ] Downstream-task AUC (frozen detector, fixed FPR=0.1) per method × dose → `tab:task_auc`.
- [ ] Credential audit: run `pwm-audit` over every `credential.json`; summarize verdicts → `tab:credentials`.
- [ ] Record counts + total sizes per record type → `tab:records_counts`.

---

## 3. Packaging & integrity

- [ ] Freeze the corpus tree under a single root `pwm-ldct-recon-corpus/`.
- [ ] Generate `MANIFEST.sha256` — SHA-256 of **every leaf file**, relative paths, sorted.
- [ ] Write `dataset_metadata.json` at the archive root (validate against `deposit/dataset_metadata.schema.json` — see §6).
- [ ] Package the Apache-2.0 generating pipeline as a pinned Docker RunBundle; record the **image digest** and **IPFS CID**.
- [ ] Verify regeneration: `docker run` on a fresh machine reproduces records bit-identically within IEEE-754 tolerance.
- [ ] (Optional but recommended) split very large NIfTI archives into per-vendor tarballs so partial download is possible.

---

## 4. Credential records

Emitted by [`../corpus_emit/`](../corpus_emit/) (`emit_stratum_credential` →
`rebuild_index`); credentials are **cohort-level**, one per
`(task × dose × method × vendor)` stratum under
`credentials/<task>/r<dd>/<method>__<vendor>.json`.

- [ ] Every `credential.json` validates against the WS-2 `credential_schema.json` (the emitter builds via the WS-2 API, so this holds by construction).
- [ ] Each carries the **framework hash** (`sha256:b366f51c…`) so reusers know the framework version.
- [ ] `verify_corpus_credentials(corpus_root)` returns `ok=True` (equivalently `pwm-audit` returns `ok=True` on every record) — the emitter already blocks hard-audit failures at write time.
- [ ] `credentials/all_credentials.jsonl` regenerated with `rebuild_index` after the last credential lands.
- [ ] `INDETERMINATE` verdicts annotated as sample-size artifacts (per WS-2), not negative findings.

---

## 5. Repository, DOI & licensing (*Scientific Data* house rules)

- [ ] Deposit in an **approved repository with a DOI** — figshare or Zenodo. **IPFS CID is supplementary, not a substitute** for the DOI.
- [ ] Data licence: **CC BY 4.0** (journal preference). Code/RunBundle licence: **Apache 2.0**.
- [ ] Confirm WS-1 terms permit **redistributing derived reconstructions** under CC BY 4.0 (check the WS-1 data-use agreement; derived imagery can inherit upstream restrictions).
- [ ] Mint the DOI; record it in `dataset_metadata.json` (`doi`) and `manuscript.tex` (`\datadoi{}`).
- [ ] Set the repository landing page title/description to match the manuscript title.
- [ ] Mark the deposit **version 1.0.0**; reserve the DOI before final upload if the repository supports it.

---

## 6. Metadata (`dataset_metadata.json`)

- [ ] Fill `deposit/dataset_metadata.example.json` with real values.
- [ ] Validate against `deposit/dataset_metadata.schema.json`:
      `python -c "import json,jsonschema; jsonschema.validate(json.load(open('dataset_metadata.json')), json.load(open('dataset_metadata.schema.json')))"`
- [ ] `related_identifiers` includes: WS-1 source DOI, WS-2 framework hash, RunBundle CID, L4 cert id, and (once known) the manuscript DOI.
- [ ] `creators[]` have ORCIDs (the journal requires a corresponding author with ORCID).
- [ ] `record_types[]` counts/sizes match `MANIFEST.sha256` and `tab:records_counts`.

---

## 7. Manuscript fill & distinctness

- [ ] Replace every `\todo{}` in `manuscript.tex` validation tables with deposited numbers.
- [ ] Replace `\datadoi{}` with the minted DOI; fill the IPFS CID in §Code Availability.
- [ ] Fill `tab:records_counts` Ns + sizes.
- [ ] Confirm the Background & Summary distinctness sentence vs WS-1 is present and accurate (raw scans vs derived layer) — prevents a redundancy desk-reject against the companion WS-1 paper.
- [ ] Author list + ORCIDs + Acknowledgments filled.
- [ ] Rebuild PDF clean; check no `\todo` remains: `! grep -n "TODO" manuscript.pdf` via source grep.

---

## 8. Ethics / governance

- [ ] Confirm no PHI in any released NIfTI header or filename (de-identify DICOM-derived metadata; `scan_id` must be the WS-1 pseudonymous id, not an MRN).
- [ ] IRB/data-use statement consistent with WS-1's; cite the governing approval.
- [ ] Competing-interests + funding statements drafted for the submission portal.

---

## 9. Submission

- [ ] Format to the *Scientific Data* template (LaTeX or Word); section order already matches.
- [ ] Upload manuscript + the **Data Citations** list (WS-1 DOI, this corpus DOI, WS-2 framework).
- [ ] Provide the repository DOI in the submission's "Data availability" field.
- [ ] Suggest reviewers with imaging + uncertainty-quantification expertise.
- [ ] Cover letter: state the artifact (derived corpus), its reuse value, and its distinctness from WS-1.

---

### Quick status legend
`[ ]` not started · `[~]` in progress · `[x]` done. Update inline as Phase 3 lands.
The chain is hard-gated at §0 (data must exist) and §5 (DOI must be minted before §7 fill).
