# `manuscript.tex` changelog

This file records substantive edits to the signal-equivalence framework
manuscript draft. Each entry lists the audit item it closed, the commit it
landed in, and what the change was for. Trivial typo and formatting fixes are
not logged here — see `git log -- manuscript.tex` for the full history.

The audit-item labels (A1–A6, B1–B5) refer to the Nature Methods
reviewer-readiness audit posted in the 2026-06-01 working session.

---

## v0.3 polish — D9 + 14 (2026-06-03, late)

Four post-v0.3 items closing remaining `\todo{}` placeholders, an open theory section, and the second deliverable of `open_questions.md` §3 (power simulation). The manuscript text grows by ~3 pp (the Bernstein supplementary); the credential schema is unchanged. V3-6 / V3-7 / V3-8 landed in `1ca1a15`; the power sim (V3-9) landed in `c25b81f`.

| ID | What landed | Commit |
|---|---|---|
| **V3-6** | **Supplementary Section S1: Bernstein finite-sample correction.** Self-contained derivation of (S4) appended at the end of `manuscript.tex` inside a `\appendix` block: setup with bounded `|Δ_k - μ| ≤ M`, Bernstein's inequality (cite Boucheron–Lugosi–Massart 2013), substitution at $t = \varepsilon$, the boxed (S4) bound, numerical comparison to (S1), library-behaviour note (both bounds reported in `sample_size_check`), practical guidance ((S1) for n ≥ 100; (S4) for n < 100), two caveats (unbounded metrics → Hoeffding; paired AUC → DeLong instead of (S4)). The §methods-estimator `\todo{supp section}` placeholder is replaced with `\ref{supp:bernstein}`. | `1ca1a15` |
| **V3-7** | **`theory/proofs/monotonicity.md` v0.1** — closes the theory side of `open_questions.md` §5 (SHARPEN). Frames naive monotonicity as false in general; defines the class $\mathcal{M}_{[r_{\min}, 1]}$ of methods trained over a signal-ratio distribution covering the range; states the conditional-monotonicity conjecture precisely; sketches two candidate counterexamples (catastrophic-overfit-to-low-end; equivariance-breaking architecture); scopes the empirical-check plan against Phase 1 pilot data; recommends a v0.4 manuscript design-recommendation paragraph supported by 3 baselines. Empirical validation gated on D9 + 90 (the Phase 1 pilot's 5-tuples). | `1ca1a15` |
| **V3-8** | **Pinned library version placeholder filled.** §Code availability: `\todo{pinned-version-at-submission}` → "`pwm_dose_equivalence==0.1.0` (released against credential schema `pwm-signal-equivalence/v0.2`; will be pinned to the journal-acceptance release at submission)". | `1ca1a15` |
| **V3-9** | **Non-null power simulation — closes `open_questions.md` §3 second deliverable.** The D9 + 13 coverage sim verified the CI's containment of true Δ under the null; this sim verifies the *verdict distribution* under controlled non-null shifts ($\Delta_{\text{AUC,true}} \in \{0, \varepsilon, 2\varepsilon\}$). New `experiments/estimator_coverage/power_sim.py` + frozen `power_results.json` (24 cells; ~25 min wall time; seed = 42). `theory/proofs/estimator.md` bumped from v0.1 to v0.2 with a new §4a (verdict-distribution table + 5 readings: framework conservatively INDET-s rather than over-commits; P(`PASS`) under null hits nominal at AUC = 0.92, n = 500; power at $2\varepsilon$ ≥ 0.90 across the typical operating range; INDETERMINATE dominates at the boundary; percentile and DeLong agree on power to within 1.5 pp). §5 caveats trimmed (the v0.1 "null only" caveat now superseded). **Cohort-sizing implication recorded**: the WS-1 v0.5 cohort ($n \approx 208$) is *exactly* in the regime where INDETERMINATE-but-truly-equivalent is the modal outcome; absence of a `PASS` verdict is not evidence of non-equivalence, only of insufficient n. No manuscript text change (the §methods-estimator "Estimator defaults" paragraph already cites `proofs/estimator.md` inline via V3-2); the manuscript inherits the §4a finding through that link. | `c25b81f` |

PDF rebuilds at **22 pages** (was 19 before V3-6; +3 pp is Supplementary S1). 0 LaTeX errors, 0 undefined references.

### Remaining `\todo` placeholders in the manuscript (intentional, submission-gated)

- §Discussion / point-evaluated-by-design list: `\todo{supp v2}` — task-bundle extension supplementary, deferred to v2 of the framework.
- §Data availability: `\todo{supp tab}` — test-split manifest hash table, gated on real Phase 1 / Phase 3 cohorts.
- §Author contributions: `\todo{Fill at submission per CRediT taxonomy: ...}`.
- §Competing interests: `\todo{Declare at submission. ...}`.
- §Acknowledgments: `\todo{Fill at submission. ...}`.

The remaining placeholders are all submission-time fields; no further v0.3-level work is feasible without external action (real cohort, author confirmation, journal upload, PyPI auth).

### `open_questions.md` re-priority after V3-9

V3-9 closes the second deliverable of §3 (non-null power), leaving §1 (literature depth-pass — external) and §5 (monotonicity *empirical* check — gated on Phase 1 pilot) as the only open theory items. All BLOCK items are now fully done. The recommendation in `proofs/estimator.md` §6 ("estimator-default decision survives under both null coverage and non-null power") is the new theory-side anchor for the v0.3 manuscript's §methods-estimator "Estimator defaults" paragraph; the cohort-sizing implication is the new theory-side anchor for the §sample-size paragraph.

### Downstream-doc propagation

The V3-9 cohort-sizing finding was propagated downstream across the WS-1 dataset README in two passes:

* **Pass 1 — WS-1 Cross-references → WS-2 entry sharpening** (commit `d0569f3`). The prior "(S3) formula is met → cohort is comfortably sized" framing was sharpened with the empirical verdict-distribution evidence. The new note tells downstream WS-1 users to **expect `INDETERMINATE` verdicts on the v0.5 cohort even for genuinely equivalent methods** at AUC ≈ 0.92 / n ≈ 200, and that **absence of `PASS` is not evidence of non-equivalence** — only of insufficient n (P(`PASS`) under the null is ≈ 0.40 at n = 200, lifting to ≈ 0.94 at n = 500).
* **Pass 2 — WS-1 Target specs new row** (commit `7817fad`). A "Credential-issuance regime (per V3-9 power sim, D9 + 14)" row was added to the v0.5 / v1.0 Target specs table, immediately after the patient-counts row. This puts the formula-side fact + empirical-side fact + operational message in the table a downstream researcher *actually consults when sizing an experiment*. v0.5 column carries the INDETERMINATE-dominated message above; v1.0 column carries the complementary "n ≥ 500 lifts into the P(`PASS`) ≈ 0.94 regime; supports tighter ε = 0.02 at the upper cohort range" message.

The (S3) sample-size formula and the V3-9 power simulation are consistent — they just answer different questions (formula: minimum n for the CI half-width to be ≤ ε in expectation; power sim: empirical verdict-distribution behaviour at the threshold n). Both passes now surface in the WS-1 README — Pass 1 in the Cross-references prose; Pass 2 in the Target specs table.

The WS-2 README was correspondingly refreshed at D9 + 14 across the status pin, Phase 2.2 status, Timeline, Subfolders proofs/ + experiments/ rows, Cross-references, and the "Done when" intermediate D9 + 14 sub-block (commits `b301b04`, `964e8c0`), plus a residual 19 pp → 22 pp page-count cleanup (commit `d253e4e`).

**Bidirectional-flow framing across both READMEs.** With V3-9 making the cross-workstream flow explicitly bidirectional (WS-1 → WS-2 contributed the annotation QA protocol; WS-2 → WS-1 now contributes the cohort-sizing implication), the sibling-workstream cross-references on both sides were updated to name the relationship symmetrically: WS-2 README's WS-1 entry (commit `88c963a`) and WS-1 README's WS-2 entry (commit `5c4d028`). Both now lead with "The cross-workstream flow is bidirectional (as of D9 + 14)" and enumerate the same two propagation commits (`d0569f3`, `7817fad`).

The V3-9 finding now appears in 7 places with consistent numbers: manuscript `proofs/estimator.md` §4a (canonical); `experiments/estimator_coverage/` (the simulation); WS-2 README; WS-2 CHANGELOG (this file); WS-1 README Cross-references; WS-1 README Target specs; the WS-2 §methods-estimator "Estimator defaults" paragraph (via the V3-2 / V3-5 inline cross-link to `proofs/estimator.md`).

---

## v0.3 — 2026-06-03 (D9 + 14)

v0.3 applies the five manuscript edits triggered by the D9 + 13 / D9 + 14 theory-and-library pass. The supporting artifacts (proofs writeups + library) had already landed; v0.3 is the manuscript-side propagation of their consequences. PDF rebuilds at 19 pages (same length as v0.2 — the new prose displaces the corrected hedges rather than adding to them).

### Theory landings

| Artifact | `open_questions.md` ref | Commit | What landed |
|---|---|---|---|
| [`theory/proofs/mri_mask.md`](../theory/proofs/mri_mask.md) | §7 (BLOCK MRI) | `526baaa` | Records option (c): `mask_family` rides inside Π as acquisition-protocol metadata, preserving the 5-tuple shape. Manuscript-side already adopted via A3 / clarification C5; this is the theory-side anchor. |
| [`theory/proofs/pet_reduction.md`](../theory/proofs/pet_reduction.md) | §8 (SHARPEN) | `526baaa` | Canonicalises activity-reduction as the v1 PET `T_r`; scan-time reduction is documented as v2. Surfaces a footnote item for Table 1 row 3. |
| [`theory/proofs/composition.md`](../theory/proofs/composition.md) | §4 (DEFER) | `526baaa` | Negative-result note: no clean composition law; framework is point-evaluated by design. Theory-side mirror of manuscript Discussion §"Point-evaluated by design". |
| [`theory/proofs/estimator.md`](../theory/proofs/estimator.md) | §3 (BLOCK) | `44a58f0` | Theorem statement (cites Efron 1979, Bickel–Freedman 1981); 27-cell empirical coverage table; estimator-default decision: **percentile** for general use, **DeLong** auto-selected for AUC tasks (~300× faster with mild conservativeness), **BCa opt-in only** (does not robustly beat percentile under the null). The v0.1 manuscript hedge "library defaults to BCa for AUC > 0.95" is **withdrawn**. |
| [`theory/proofs/sample_size.md`](../theory/proofs/sample_size.md) | §2 (BLOCK) | `e3c1ee2` | (S1) general CLT formula + (S3) paired-AUC DeLong specialisation + (S4) Bernstein finite-sample correction; numerical tables at canonical operating points; empirical validation against the §3 simulation. **Surfaces a v0.3 manuscript correction** — see *Triggered manuscript edits* below. |
| [`experiments/estimator_coverage/`](../experiments/estimator_coverage/) | §3 backing | `44a58f0` | 27-cell coverage simulation (AUC × n × CI variant), seed = 42; ~35 min wall time; `results.json` committed. |

### Library landings

| Artifact | Commit | What landed |
|---|---|---|
| [`pwm_dose_equivalence/`](../pwm_dose_equivalence/) v0.1.0 alpha | `0836162` (scaffold) + `e18121f` (gitignore) | Pip-installable package: modality-agnostic `signal_equivalence_credential` API; percentile + DeLong estimators with the v0.3 defaults baked in; (S1) / (S3) / (S4) sample-size pre-flight; content-addressed framework hash; `Tr_ct` / `Tr_mri` / `Tr_pet` operators consistent with the proofs writeups. |
| Same, test suite | `3a4b0f1` (coverage) + `909d505` (README number bumps) | **60/60 tests pass; 100 % line coverage** (230/230 statements). Well above the manuscript §software_rigor's 90 % v0.2 floor. Includes regression tests for the (S1)/(S3) numerical-table values, the estimator coverage-under-null, the verdict logic, and every documented `ValueError` branch in the public API. |

### Landed (manuscript-side propagation of the D9 + 13 / D9 + 14 landings)

| ID | What changed | Why |
|---|---|---|
| **V3-1** | **AUC-task default `ε` correction.** §methods-estimator rewritten with the corrected (S1) general CLT formula and the (S3) paired-AUC specialisation in terms of the DeLong placement-difference SD. The four end-to-end AUC code-block instances of `epsilon=0.02` (lung-nodule-AUC case study + Discussion sentence + §methods-library API showcase) bumped to `epsilon=0.05`; the API showcase comment now says "AUC default; 0.02 for non-AUC metrics". Reproducible n ≈ 130–250 across the typical AUC operating range — comfortably within the WS-1 v0.5 cohort. Non-AUC metrics keep ε = 0.02. | `proofs/sample_size.md` §5: the v0.1 hedge "n ≥ 192 for ε = 0.02" was wrong (took σ as per-arm AUC SD instead of DeLong placement-difference SD); at realistic placement variances, ε = 0.02 needs n ≈ 1500 at AUC = 0.85. |
| **V3-2** | **Estimator-default text rewrite.** Replaced the §methods-estimator "Coverage of percentile CIs near boundary" paragraph (which recommended BCa for AUC > 0.95 with `n < 200`) with a new "Estimator defaults" paragraph: percentile is the default; DeLong is auto-selected when `task.metric == "auc"` (mildly conservative; $\sim 300\times$ faster than the bootstrap variants); BCa remains opt-in. Discussion §"Estimator failure modes" softened the v0.2 "the library defaults to BCa in this regime with an explicit warning" to the new DeLong-and-MC-SE language. | `proofs/estimator.md` §3.2: BCa coverage at AUC = 0.97 / $n = 100$ is $0.900$ vs percentile $0.935$. BCa does not robustly outperform percentile under the null. |
| **V3-3** | **B5 software-rigor numbers.** Filled four `\todo` placeholders in §software_rigor: 60 unit tests (integration tests land at v0.2.0 alongside BCa); 100 % line coverage on 230 statements; current version `0.1.0` (alpha). Test inventory rewritten to match the actual v0.1.0 test suite (percentile + DeLong coverage; sample-size formulas vs numerical-table values; `T_r` operator invariants including NaN sentinel; JSON round-trip + framework-hash stability; verdict logic at boundaries; mode-misuse / sample-size-warning / ValueError branches). | Library at v0.1.0 alpha now exists with 60/60 tests passing at 100 % coverage; the placeholders had no reason to remain. Closes audit item B5. |
| **V3-4** | **PET Table 1 footnote.** Added a footnote on Methods Table 1 row 3 clarifying that the canonical PET `$T_r$` for v1 is *activity reduction*; *scan-time reduction* at full activity is statistically equivalent at the level of total counts but not physically equivalent (motion blur, kinetic modelling differ) and is documented as a v2 distinction. Footnote cites `experiments/cross_modality_consistency/` and `theory/proofs/pet_reduction.md`. Implemented as `\footnotemark[1]` in the table cell + `\footnotetext[1]{...}` after `\end{table}` (see *Typesetting fixes* below). | `proofs/pet_reduction.md` §3 explicitly recommended this footnote. |
| **V3-5** | **Cross-link the proofs.** Added inline pointers in §framework (to `proofs/mri_mask.md`, on the subpopulation-as-acquisition-protocol-bearing-measure paragraph) and Discussion §"Point-evaluated by design" (to `proofs/composition.md`, on the algebraic-combination-not-derivable paragraph). The §methods-estimator "Sample-size formula" and "Estimator defaults" paragraphs (V3-1 / V3-2) already cite `proofs/sample_size.md` and `proofs/estimator.md` inline. The PET Table 1 footnote (V3-4) cites `proofs/pet_reduction.md`. | Signposting the theory-side anchors so a reader/reviewer can pull the supporting derivations without leaving the manuscript text-flow. |

### Typesetting fixes

| ID | Issue | Fix | Commit |
|---|---|---|---|
| **V3-4-fix** | The V3-4 commit (`6416881`) placed `\footnote{...}` directly inside a `tabular` inside a `\begin{table}` float. LaTeX silently drops footnote bodies in this configuration: the marker (¹) rendered next to "rate `$r$`" in the PET row, but the footnote text never appeared on the page. Confirmed via `pdftotext` (grep for "canonical PET" returned nothing). | Switched the footnote to `\footnotemark[1]` in the table cell + `\footnotetext[1]{...}` placed immediately after `\end{table}`. The footnote body now renders at the bottom of page 10 with the standard horizontal rule above it. | `6fb1ee7` |

This is a recurring LaTeX footgun. For future table-cell footnotes in the manuscript, use the `\footnotemark` + `\footnotetext` pattern directly.

### Status changes

- Manuscript header status comment + `\date{}` bumped from v0.2 to v0.3 (commit `6416881`).
- Credential JSON `schema_version` unchanged at `pwm-signal-equivalence/v0.2` (none of V3-1 .. V3-5 change the JSON schema).
- PDF rebuilds at 19 pages, **517 KB** (was 453 KB at the V3-4-fix-pending commit `6416881`; the +64 KB is the now-rendered PET footnote body).
- Clean build: 0 LaTeX errors, 0 undefined references / citations, 0 BibTeX warnings. The only overfull `\hbox` warnings are the two pre-existing ones at lines 118–119 (verbatim listing) and 190–202 (comparison table), unchanged from v0.2.

### `open_questions.md` table — re-priority after D9 + 14

| § | Was | Now |
|---|---|---|
| §1 Literature depth-pass | SHARPEN, 1.5 wk | **still pending** — genuinely external work (reading specific papers) |
| §2 Sample-size formula | BLOCK, 2.0 wk | **done** — `proofs/sample_size.md` |
| §3 Estimator validity | BLOCK, 1.5 wk | **done (null only)** — `proofs/estimator.md`; non-null power sim is the follow-up |
| §4 Composition law | DEFER, 0.5 wk | **done** — `proofs/composition.md` |
| §5 Conditional monotonicity | SHARPEN, 1.0 wk | **still pending** — best after Phase 1 pilot data lands |
| §6 Per-patient guidance | SHARPEN, 0.5 wk | **done at manuscript level** (Definition 2 opt-in; Discussion paragraph) |
| §7 MRI mask decision | BLOCK MRI, 1.0 wk | **done** — `proofs/mri_mask.md` |
| §8 PET model | SHARPEN, 0.5 wk | **done** — `proofs/pet_reduction.md` |
| §9 Multi-task aggregation | DEFER (v2 acknowledgment) | unchanged |
| §10 Cross-subpopulation | DEFER (v2 acknowledgment) | unchanged |

Effort accounting: of the ~8 weeks of theory work originally scheduled, ~5.5 weeks closed across D9 + 13 / D9 + 14. The remaining items (§1 depth-pass; §5 monotonicity) are genuinely externally gated, not theory-time-blocked.

### Theory-doc lag (narrowed but not closed)

`theory/dose-equivalence-framework.md` still at **v0.1**. The gap to v0.2 is now narrowed to the literature depth-pass: the manuscript-side commitments that the proofs writeups anchored (Π-as-metadata; population-vs-sample evidence; estimator defaults; composition as non-derivable; activity-reduction-as-canonical-PET-`T_r`) are all consistent across (manuscript v0.2 + proofs/*.md v0.1), and a future theory-doc v0.2 will incorporate them with the depth-pass reading in the same pass.

---

## v0.2 — 2026-06-01

Seven pure-text edits + one synthetic experiment, all done before any Phase 1
or Phase 3 empirical work landed. The draft is now reviewer-readier than v0.1
without depending on data the team does not yet have.

### Landed

| ID | Commit | What changed | Why |
|---|---|---|---|
| **A4** | `5e90b88` | Demoted the on-chain registry from "contribution #4" to a deployment-only detail; SHA-256 content-addressing is now the methodological substance. Renamed `l2_framework_hash` → `framework_hash`; removed *blockchain* / *on-chain* / *L2 spec* jargon from the abstract, intro, results case study, and discussion. | The blockchain framing was the most reviewer-hostile claim in v0.1; Nature Methods reviewers reach for "gimmick" when they see *blockchain* attached to a methods paper. Content-addressing is the actual contribution and survives that framing intact. |
| **B2** | `5e90b88` | Title shortened from "Signal-Equivalence: A Probabilistic Framework for Comparing Reconstruction Methods Across Reduced-Signal Imaging Modalities" (18 words) to "Signal-equivalence: testable dose-reduction claims for medical imaging" (8 words). Abstract restructured into four beats (problem / framework / library + worked examples / implications) without literal headings. | v0.1 title front-loaded "probabilistic" and was too long for Nature Methods house style. |
| **A3** | `5e90b88` | In §framework and clarification C5: `Π` carries acquisition-protocol metadata (CT vendor/kVp, MRI mask family, PET tracer/scanner). The MRI mask family rides inside `Π`, not as a sixth tuple slot. | open_questions §7 had flagged that the 5-tuple was effectively a 6-tuple for MRI. This edit closes the asymmetry inside the manuscript, not just in the proofs. |
| **B3** | `5e90b88` | "Out-of-scope claim types" rewritten as "Point-evaluated by design"; superiority / cross-modality / composition / multi-task framed as deliberate non-derivability rather than refusals. "Subpopulation failure modes" softened to "Subpopulation specificity" with explicit FDA subgroup-stratified-reporting alignment. | v0.1 read as a list of apologies. Same content, defensive instead of apologetic. |
| **B1** | `1cb17dd` | Added "Population claim vs.\ sample evidence" paragraph immediately after Definition 1: the two expectations are deterministic population objects the credential **asserts**; the bootstrap procedure at significance `α` provides finite-sample **evidence** from a test set drawn from `Π`. The credential records `n_test` and a slug resolving to the operational sampling protocol. | v0.1 conflated "population mean" (LHS of Eq. 1) with "α-confidence under the paired bootstrap" inside a single iff. The cleanest reviewer attack on the v0.1 draft. |
| **A5** | `5f0317e` | New "Ground-truth protocol" paragraph at the top of §methods-estimator borrowing the PWM-LDCT v0.5 annotation QA protocol verbatim (eligibility / 20-case calibration κ ≥ 0.60 / IoU ≥ 0.3 matching / >50 % majority-vote consolidation / third-rad discordance adjudication / rotating 5-case drift re-calibration). New "Label-noise refusal threshold" paragraph: the library refuses to issue a credential when documented inter-reader disagreement exceeds `ε/2`. Unified the credential JSON `ground_truth_protocol` field across the two worked-example JSONs. | v0.1's `ground_truth = "majority-vote-2-rads"` slug was hand-waved; for lung-nodule AUC this is the single most attackable claim in the paper. |
| **A6** | `120c61b` | New "Relation to task-based image-quality assessment" intro paragraph positioning signal-equivalence as complementary to the Barrett 1990 / Barrett & Myers 2013 / AAPM TG-233 lineage. Three anchor cites added to `refs.bib`. Theory folder: seeded `theory/related_work.md` with the four-paper memo skeleton and a "what is genuinely new" novelty gate for the v0.2 framework draft. | Closes the "you have reinvented task-based image quality" reviewer attack. open_questions §1 literature pass has a head start. |
| **A2** | `a5b67e2` | New Results subsection "Cross-modality consistency on synthetic data" with **real numbers** (not `\todo`): six credentials (3 modalities × 2 candidates) produced by the same paired-bootstrap code path show 3 expected PASS and 3 expected FAIL verdicts. New `experiments/cross_modality_consistency/` with a self-contained Python script, frozen `results.json`, and README. | The three independent per-modality worked examples did not rule out the possibility that the framework's generality is rhetorical. This experiment closes the gap with reproducible (seed = 42, bit-for-bit) numbers. |

### Schema bumps

- Credential JSON `schema_version`: `pwm-signal-equivalence/v0.1` → `v0.2`. Field renames (`l2_framework_hash` → `framework_hash`; `ground_truth` → `ground_truth_protocol`) are technically breaking; in pre-v1 we bump MINOR rather than introduce a parallel-versioning shim. The library, once it exists in Phase 3, ships against the v0.2 schema directly.

### What v0.2 still does **not** contain

- **Real per-modality Results tables.** Gated on WS-2 Phase 1 (CT, D9+90) and Phase 3 (MRI + PET validators, D9+270 → D9+365).
- **Numbers in the end-to-end worked example prose** (B4). Gated on the per-modality tables.
- **Real software-rigor counts.** `$N_{\textrm{tests}}$` and coverage % remain `\todo` until Phase 3 `pwm_dose_equivalence` v0.1 ships.
- **Closed-form sample-size derivation + coverage simulations.** open_questions §2 (BLOCK, ~2 wk) and §3 (BLOCK, ~1.5 wk); not data-gated but theory work that has not been scheduled into this pass.

### Theory-doc lag (intentional)

`theory/dose-equivalence-framework.md` remains at **v0.1**. Its own headline says it "Will be superseded by v0.2 after literature pass (see [`open_questions.md`](open_questions.md) §1)," and the literature pass has only been *seeded* (`theory/related_work.md` v0.1) rather than completed in depth. The manuscript-side v0.2 has therefore moved ahead of the theory-doc v0.1 — that is the documented gap.

What would close the gap: the depth-pass reading of fastMRI reader studies, one CHO-for-low-dose-CT paper, and Wunderlich/Noo on observer-model variance (listed in `theory/related_work.md` §5). At that point the theory doc bumps to v0.2 with the [SHARPEN-N] points reconciled against the manuscript edits in this changelog.

---

## v0.1 — 2026-05-20

Initial Nature Methods working draft seeded alongside `theory/dose-equivalence-framework.md` v0.1 and `theory/open_questions.md` v0.1. Not logged in detail here; see commit `5e90b88`'s parent for the seed state.
