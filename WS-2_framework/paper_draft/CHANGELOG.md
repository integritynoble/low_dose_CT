# `manuscript.tex` changelog

This file records substantive edits to the signal-equivalence framework
manuscript draft. Each entry lists the audit item it closed, the commit it
landed in, and what the change was for. Trivial typo and formatting fixes are
not logged here — see `git log -- manuscript.tex` for the full history.

The audit-item labels (A1–A6, B1–B5) refer to the Nature Methods
reviewer-readiness audit posted in the 2026-06-01 working session.

---

## v0.3 — in flight (D9 + 13 → D9 + 14, 2026-06-02 → 2026-06-03)

**The manuscript text itself is unchanged since v0.2.** This section records the supporting artifacts that landed at D9 + 13 / D9 + 14 and the v0.3 manuscript edits those artifacts now make actionable. v0.3 will be cut when the listed edits are applied to `manuscript.tex` and the credential `schema_version` bumps (if any schema-breaking edits land).

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

### Triggered manuscript edits (v0.2 → v0.3, pending)

These are the manuscript-text changes the landings above *make actionable*. Each is a small targeted edit; together they constitute v0.3.

1. **AUC-task default `ε` correction.** `proofs/sample_size.md` §5 shows that the v0.1 hedge "n ≥ 192 for ε = 0.02, α = 0.05" was wrong — the implicit parameterisation took σ as a per-arm AUC SD, not the DeLong placement-difference SD. At realistic placement variances, ε = 0.02 needs n ≈ 1500 at AUC = 0.85. **Action:** in §methods-estimator the canonical AUC default should become ε = 0.05 (n ≈ 130–250 across the AUC range — comfortably within the WS-1 v0.5 cohort of 208 unique paired patients); non-AUC metrics (Dice, MAE, contrast-recovery) keep ε = 0.02 as the recommended default. The framework remains parametric in ε.
2. **Estimator-default text rewrite.** The v0.2 §methods-estimator paragraph "library defaults to BCa in this regime with an explicit warning" should be replaced with: "library defaults to DeLong for AUC tasks (300× faster than the bootstrap variants in our coverage simulations) and to percentile bootstrap otherwise; BCa is opt-in." Cite [`theory/proofs/estimator.md`](../theory/proofs/estimator.md) for the empirical justification.
3. **Software-rigor numbers.** §software_rigor currently carries `\todo{$N_{\textrm{tests}}$}`, `\todo{$N_{\textrm{integ}}$}`, `\todo{≥ 90 %}`, and `\todo{0.1.0}` placeholders. Action: fill with 60 unit tests, 0 integration tests (the suite is unit-only at v0.1.0 alpha; integration tests land at v0.2.0 alongside BCa), 100 % line coverage on 230 statements, and `v0.1.0`. This closes audit item B5.
4. **PET Table 1 footnote.** `proofs/pet_reduction.md` §3 recommends a one-line footnote on Methods Table 1 row 3 ("Poisson-thinning of list-mode counts at rate `r`") clarifying that the canonical operator is *activity-reduction*; scan-time reduction is out-of-scope for v1.
5. **Cross-link the proofs.** Methods §estimator, §framework, and Discussion §"Point-evaluated by design" should pick up explicit `\citep{}`/footnote references to `theory/proofs/{estimator,sample_size,mri_mask,pet_reduction,composition}.md` so the manuscript signposts the theory-side anchors. (Optional; sharpens but not strictly required.)

### Schema (unchanged at v0.3-in-flight)

Credential JSON `schema_version` remains `pwm-signal-equivalence/v0.2`. None of the triggered edits above change the credential schema; they change defaults and prose. A schema bump would only happen if a v0.3 edit adds a new field or renames an existing one (none are currently planned).

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
