# WS-3 Data Descriptor — reviewer-simulation pass

**Purpose.** A pre-submission dry run of *Scientific Data*'s review, against
`manuscript.tex` as of 2026-06-11 (9 pp). It is a **simulation**, not a real
referee report: a structured self-critique in the voice of the editor + two
referees, mapping every gap to the artifact/action that closes it. Use it as
the submission-readiness gate alongside [`../deposit/DEPOSIT_CHECKLIST.md`](../deposit/DEPOSIT_CHECKLIST.md).

*Scientific Data*'s four review questions: (Q1) Are the methods described in
enough detail to reproduce the data? (Q2) Is the data record complete? (Q3) Is
the technical validation sufficient to support reuse? (Q4) Repository /
metadata / licensing / ethics compliance.

Severity legend: **[BLOCK]** desk-reject or reject-pending; **[MAJOR]** must fix
before acceptance; **[MINOR]** strengthening / discretionary.

---

## Editorial pre-screen (scope + completeness gates)

| ID | Finding | Severity | Action to close |
|---|---|---|---|
| E1 | **Data are not yet deposited; no DOI.** `\datadoi{}` and the RunBundle CID are placeholders. *Scientific Data* will not send a descriptor to review until the data sit in an approved repository with a DOI. | **BLOCK** | Generate the Phase-3 corpus; deposit to figshare/Zenodo; mint DOI; fill `\datadoi{}` + §Code Availability CID. |
| E2 | **Author list / ORCIDs / affiliations / Acknowledgments are placeholders** (`\author{...to be confirmed}`, `\todo{Fill at submission}`). A corresponding author with ORCID is mandatory. | **BLOCK** | Fill author block, ORCIDs, funding, competing interests. |
| E3 | **Approved-repository requirement.** IPFS RunBundle + PWM L4 cert are supplementary integrity anchors, not an SD-recognised repository. | **MAJOR** | Make figshare/Zenodo the primary deposit; keep IPFS/L4 as "additionally mirrored." |
| E4 | **Companion-submission overlap.** WS-1 (raw scans) is a separate *Scientific Data* paper; redundancy is a desk-reject risk. The Background distinctness sentence is present and correct. | **MINOR** | Declare the related WS-1/WS-2 submissions in the cover letter; keep the distinctness sentence. |

## Q1 — Methods sufficiency / reproducibility

| ID | Finding | Severity | Action to close |
|---|---|---|---|
| M1 | **Supplementary Table S1 (hyperparameters, seeds, compute) is referenced but absent** from the draft. Reproducibility claims hang on it. | **~~MAJOR~~ ADDRESSED (skeleton, 2026-06-11)** | `supplementary.tex` authored (3 pp): Table S1 hyperparameters, S2 determinism + software pins + framework hash, S3 compute disclosure. Fixed values mirror Methods; `\todo` entries set at training time. Main-text refs repointed to S1/S2/S3. |
| M2 | **The frozen lung-nodule detector is underspecified** — architecture, version, training data, and the FPR=0.1 operating-point provenance are not given. Every task-AUC number and the AUC credentials depend on it. | **MAJOR** | Name + version the detector; deposit or cite it; state how the operating point was fixed. Without this the task layer is not reproducible. |
| M3 | **Internal inconsistency: the abdomen / liver-lesion Dice task is unsupported in Methods.** §"Derived per-record quantities" describes only a *lung-nodule* score map, and the only task-score record type is `task_nodule_score.nii.gz`, yet `tab:credentials` includes a liver-lesion Dice row and the data dictionary lists `anatomy=abdomen`. A referee will catch this. | **~~MAJOR~~ RESOLVED (2026-06-11)** | Option (b) applied: v1 is **lung-nodule-only**. Removed the liver-lesion credential row + abdomen from the data dictionary; added an explicit v1-scope note in Methods (abdominal liver-lesion deferred to a future release). Propagated to `dataset_metadata.example.json` (`anatomy:["chest"]`) and the fixture (chest/AUC-only; Dice/percentile path retains unit coverage in `corpus_emit/tests`). Text, metadata, and tooling now agree. |
| M4 | **`r = 1.00` semantics are ambiguous.** The dose set includes 1.00, but a "reconstruction" and an `error_abs` at full dose are degenerate (error ≈ 0; no credential). | **~~MINOR~~ RESOLVED (2026-06-11)** | Methods now states $r=1.00$ is the reference (not a credentialed level): no error map and no credential at $r=1$; all error/task/credential records are at $r \in \{0.10, 0.25, 0.50\}$. |
| M5 | **Real-paired vs simulated low-dose is not delineated.** "simulated/real low-dose" is inherited from WS-1 but a referee will want to know which (vendor, dose) strata are real-paired acquisitions vs simulated photon-count reductions. | **~~MAJOR~~ ADDRESSED (text, 2026-06-11)** | Methods now records per-record `low_dose_origin ∈ {real_paired, simulated}` (simulated = Poisson photon-count reduction in `ct_radon`), with a cohort table (`tab:cohort`) breaking strata down by kind. Field added to the data dictionary + fixture. Per-stratum *numbers* still gated on data. |

## Q2 — Data-record completeness

| ID | Finding | Severity | Action to close |
|---|---|---|---|
| D1 | **`tab:records_counts` is entirely `\todo`** (counts + sizes). | **BLOCK** | `package_corpus.py` fills these from the frozen corpus. |
| D2 | **NIfTI affine provenance unstated.** Conventions say `sform` = scaled identity; a referee will ask whether patient orientation/origin from the source DICOM is preserved or discarded. | **~~MINOR~~ RESOLVED (2026-06-11)** | Conventions now state the affine is an orientation-normalised scaled identity by design (DICOM position/origin not propagated, as de-identification); records are in a canonical voxel frame, not re-registrable to source-patient coordinates. |
| D3 | **No cohort-composition summary** — number of patients, scans per vendor, per anatomy, per dose. Reusers need the sampling shape. | **MAJOR — table added (2026-06-11); numbers gated** | `tab:cohort` now reports per-vendor patients/scans + real-paired-vs-simulated strata; `package_corpus.py` derives the counts at deposit. |
| D4 | **Baseline records lack uncertainty maps** — asymmetry vs the reference record set. Correct (single-model baselines have no ensemble σ) but unstated. | **~~MINOR~~ RESOLVED (2026-06-11)** | §Baselines now states baselines are single-model and carry no `uncertainty_sigma` (ensemble disagreement is defined only for the deep-ensemble reference). |

## Q3 — Technical-validation sufficiency

| ID | Finding | Severity | Action to close |
|---|---|---|---|
| V1 | **All four validation tables + the reliability figure are `\todo`** (fidelity, cross-vendor, UQ Spearman, task AUC, credentials). Validation is the heart of an SD review; it is currently unverifiable. | **BLOCK** | Fill from Phase-3 runs. |
| V2 | **UQ calibration reported only as Spearman ρ.** Rank-correlation shows monotone tracking but not calibration magnitude; a UQ-savvy referee will ask for a calibration curve / expected-calibration-error or σ-interval coverage. | **~~MAJOR~~ ADDRESSED (methodology, 2026-06-11)** | Validation now reports calibration three ways: rank (Spearman), magnitude (reliability diagram + ECE), and interval coverage (±kσ for k∈{1,2,3}, new `tab:uq_coverage`). Numbers gated on data; the methodology gap is closed. |
| V3 | **Cross-vendor "interpolation vs extrapolation" framing** is only meaningful once the Δ numbers exist. | (folds into V1) | Fill `tab:cross_vendor`. |
| V4 | **No validation that the released `error_abs` equals `|recon − full_dose|`** by construction-check on a sample (a reuser's trust anchor). | **MINOR** | Add a one-line integrity check in Technical Validation (e.g., spot-recompute error on N random records). |

## Q4 — Standards / metadata / licensing / ethics

| ID | Finding | Severity | Action to close |
|---|---|---|---|
| S1 | **Ethics statement present** (no new PHI; derived; identifiers stripped; pseudonymous `scan_id`). Good. The governing IRB/approval is not named. | **MINOR** | Name the WS-1 governing approval / data-use agreement once finalised. |
| S2 | **CC BY 4.0 redistribution basis asserted but unevidenced.** The draft says WS-1 terms permit redistributing derived reconstructions; an editor may request the clause. | **MAJOR** | Confirm against the actual WS-1 DUA that *derived* imagery may be released CC BY 4.0; cite the clause. If not permitted, fall back to the most open compatible licence. |
| S3 | **Data Citations need real identifiers** — WS-1 DOI, the corpus DOI, WS-2 framework. | **MAJOR** | Fill once DOIs exist. |
| S4 | **Metadata format.** `dataset_metadata.json` is a custom (validated) schema; SD collects its own structured metadata at submission and prefers community standards where they exist. | **MINOR** | Keep the JSON as a deposit artifact; complete SD's submission-portal metadata separately. |

---

## Simulated decision

**Current state → desk-reject / reject-resubmit**, on E1+E2 alone (no deposited
data, no DOI, no authors) and V1/D1 (validation + record tables empty). This is
expected: the manuscript is a **complete, well-formed shell** whose substance is
gated on Phase-3 data — not an editorial weakness, a sequencing fact.

**After the BLOCK items clear** (corpus deposited + DOI + authors + tables
filled), the descriptor is structurally sound and the likely decision is
**minor-to-major revision**, with the MAJOR items most likely to be raised by
referees being: M2 (detector spec), M3 (abdomen-task consistency), M5
(real-vs-simulated provenance), D3 (cohort composition), V2 (calibration beyond
Spearman), and S2 (licence basis for derived data).

## Pre-submission gate (ordered)

1. **Task scope — DONE (M3):** v1 is lung-nodule-only; text, metadata, and fixture are consistent. Generate data to this single-task shape.
2. **Generate Phase-3 corpus**; specify the detector (M2) and real-vs-simulated provenance (M5).
3. **Deposit + DOI** (E1, E3); confirm the licence basis (S2).
4. **Fill** all validation/record/cohort tables + reliability figure + Supplementary S1 (V1, V2, D1, D3, M1); add the calibration metric.
5. **Authors, ORCIDs, citations, ethics approval name** (E2, S1, S3).
6. Run `package_corpus.py` to refresh metadata/manifest; re-audit all credentials; rebuild PDF; remove every `\todo`.

The non-data items draftable before Phase 3 are now **all applied**
(2026-06-11): ~~M3~~ scope decision, ~~M5~~ provenance scaffold + cohort
table, ~~V2~~ three-axis calibration methodology, ~~D4~~ baseline-σ sentence,
~~M4~~ r100 clarification, ~~D2~~ affine statement, ~~D3~~ cohort-table
structure. What remains is **data-gated** (fill every `\todo` from Phase-3
runs) and **process** (E1–E3 deposit/DOI/authors, M1 Supplementary S1, M2
detector spec, S2 licence basis, S3 citations).
