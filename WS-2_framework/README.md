# WS-2 — Signal-Equivalence Framework (Track 9 sub-track 9b)

The **signal-equivalence framework**: a formal, modality-general mathematical replacement for vendor-style claims like *"50% dose reduction"*, *"4× MRI acceleration"*, or *"25% activity PET"*. Each claim is converted into a testable 5-tuple credential `(signal_ratio, task, ε, α, subpopulation)`.

> **Status (D9 + 16, 2026-06-05):** manuscript at **v0.3 working draft**, 22 pp incl. 3-pp Supplementary S1 ([`paper_draft/CHANGELOG.md`](paper_draft/CHANGELOG.md) v0.2 → v0.3 → v0.3-polish → v0.3-evidence-completion → Library v0.2.0 → v0.3-reviewer-reproduction-surface). Theory side: [`theory/proofs/`](theory/proofs/) holds 6 v0.1+ writeups (estimator.md now at v0.4); backing experiments are **four sims closing the per-modality metric trio** in [`experiments/estimator_coverage/`](experiments/estimator_coverage/) (AUC coverage + AUC power + Dice + CR), plus the 6-credential cross-modality demo in [`experiments/cross_modality_consistency/`](experiments/cross_modality_consistency/). Library side: [`pwm_dose_equivalence/`](pwm_dose_equivalence/) at **v0.2.0 alpha** — pip-installable, **81/81 tests** (incl. 10 end-to-end integration tests), 100 % line coverage on 265 statements; v0.2.0 added BCa estimator + small-$n$ anti-conservativeness warning + `bound_M` for unbounded metrics + integration tests; plus **four tutorial notebooks** ([`pwm_dose_equivalence/notebooks/`](pwm_dose_equivalence/notebooks/) — three per validated modality + one extending-to-a-new-modality worked example). Reviewer + user + extension surface: two reviewer-facing companions — [`paper_draft/reproduction_guide.md`](paper_draft/reproduction_guide.md) maps every numerical claim in the manuscript to its repo anchor + the command that re-derives it (16-row per-claim table; for code-savvy reviewers); [`paper_draft/credential_reading_guide.md`](paper_draft/credential_reading_guide.md) walks a credential JSON field-by-field with verdict semantics + framework-hash guarantees + a 9-entry red-flag checklist (for non-coder reviewers / regulators / clinicians) — closes the manuscript §software_rigor "Credential reading guide" claim. Validated-modality tutorials show new users how to compute their own credentials end-to-end; the Optical extension tutorial closes the manuscript Methods Table 7 "user-implementable" claim. Real-cohort per-modality Results tables remain gated on WS-2 Phase 1 (CT) and Phase 3 (MRI / PET data integrations).

---

## Goals

1. **Publish a peer-reviewed paper** at ***Nature Methods*** (primary) introducing the framework. Fallback: *IEEE Transactions on Medical Imaging* or *Medical Image Analysis*. Working draft is at v0.3 in [`paper_draft/`](paper_draft/) — see [`paper_draft/CHANGELOG.md`](paper_draft/CHANGELOG.md) for the v0.1 → v0.2 → v0.3 deltas.
2. **Ship `pwm_dose_equivalence` on PyPI** with ≥ 2 modality validators (CT + MRI minimum; PET stretch). `pip install pwm_dose_equivalence` works for any external user. The pip-installable scaffold lives at [`pwm_dose_equivalence/`](pwm_dose_equivalence/) at **v0.2.0 alpha** (81/81 tests incl. 10 end-to-end integration tests, 100 % line coverage on 265 statements; **four tutorial notebooks** in [`pwm_dose_equivalence/notebooks/`](pwm_dose_equivalence/notebooks/) — three per validated modality + one extending-to-a-new-modality (Optical) closing the manuscript "user-implementable" claim); v0.2.0 added BCa + small-$n$ warning + `bound_M` + integration tests + tutorials. The synthetic-only [`experiments/cross_modality_consistency/`](experiments/cross_modality_consistency/) prototype is preserved as the modality-general consistency anchor. Phase 3 remaining: TestPyPI publish (D9 + 365), real-data CT / MRI / PET integrations, macOS / Windows CI runners, v1.0.0 release (D9 + 540).
3. **Register the framework definition on PWMRegistry** as a content-addressed L2 specification, so every leaderboard submission is verified against the SHA-256 hash of the framework version the credential was issued under. The PWM registry is one of three hash-resolvers (local file / pinned PyPI release / PWMRegistry) that the manuscript enumerates; content-addressing itself is the methodological substance, the registry is the long-term decentralized resolver.

A successful WS-2 means: an external researcher can compute a 5-tuple credential for their reconstruction method on the L3 dataset in under one hour on commodity hardware, and any reviewer can verify the credential by re-running the same library against the same framework hash.

---

## The framework, in one line

Method **M** is **signal-equivalent at level (r, T, ε, α)** over subpopulation **Π** iff the population-mean task performance on reduced-signal scans is within `ε` of the population-mean performance of a reference method on full-signal scans. The `1 − α` is the confidence level at which the paired-bootstrap estimator returns `PASS` on a test set drawn from Π — population claim and finite-sample evidence are kept distinct (manuscript v0.3 §framework). Π is formalized to carry the **acquisition-protocol metadata** that determines `T_r` for the modality (CT vendor / kVp; MRI mask family; PET tracer / scanner), so the 5-tuple shape holds verbatim across CT, MRI, and PET.

The formal definition lives in [`theory/dose-equivalence-framework.md`](theory/dose-equivalence-framework.md) (v0.1; intentionally lags the manuscript v0.3 pending the literature depth-pass per [`theory/open_questions.md`](theory/open_questions.md) §1). It sharpens the one-liner across six points (patient vs image; operator vs scalar; reference-acquisition vs reference-algorithm; performance functional form; subpopulation-as-acquisition-protocol-bearing measure; aggregate vs per-patient) — the same six points appear in the manuscript as clarifications C1–C6.

---

## Scope: modality-general by construction

| Modality | Signal-reduction parameter `r` | Validator status |
|---|---|---|
| **CT** (primary) | `r = mA_red / mA_ref` (tube-current dose ratio) | *Synthetic Poisson channel:* **done** ([`experiments/cross_modality_consistency/`](experiments/cross_modality_consistency/)). *Empirical:* Phase 1 pilot on AAPM 2016 + LIDC-IDRI (D9 + 90). |
| **MRI accelerated reconstruction** | `r = 1 / R` (acceleration factor reciprocal); mask family rides inside Π | *Synthetic Cartesian-mask channel:* **done** ([`experiments/cross_modality_consistency/`](experiments/cross_modality_consistency/)). *Empirical:* Phase 3 worked example on fastMRI knee (D9 + 270). |
| **PET low-dose / low-activity** | `r = A_red / A_ref` (injected-activity ratio) | *Synthetic list-mode channel:* **done** ([`experiments/cross_modality_consistency/`](experiments/cross_modality_consistency/)). *Empirical:* Phase 3 worked example on NEMA NU-2 IQ phantom (D9 + 270). |
| Optical / fluorescence (stretch) | `r = exposure_red / exposure_ref` | v2 extension; `T_r` specified in the manuscript Methods table (Table 1) but not validated. |

The framework's SHA-256 hash registers as an L2 specification on PWMRegistry when **CT + at least one of {MRI, PET}** have a working **empirical** validator (the synthetic-channel demonstrations are necessary but not sufficient for this ship gate).

---

## Tasks

### Phase 1 — Phase A pilot (D9 + 60 → D9 + 90)

| # | Task | Output | Status @ v0.3 |
|---|---|---|---|
| 1.1 | Compute the 5-tuple credential for each of the 3 reproduced WS-3 baselines on AAPM 2016 + LIDC-IDRI | `validation/heyang_pilot_5_tuples.json` | pending (data-blocked on Phase 1 cohort) |
| 1.2 | End-to-end implementability check — does the v0.1 definition survive contact with real data? | Decision: commit to v0.1 or revise before Phase 2 | **partial** — definition revised twice (v0.2: A3 / A5 / B1 / B3 / A4; v0.3: V3-1 / V3-2 / V3-4 / V3-5 propagating the proofs landings — per [`paper_draft/CHANGELOG.md`](paper_draft/CHANGELOG.md)); empirical "survive contact" test still gated on 1.1 |
| 1.3 | Methodology memo: how the pilot computes the credential | `validation/methodology.md` | pending — manuscript Methods §Estimator now covers the protocol; pilot-specific memo gated on 1.1 |
| 1.4 | Known limitations memo | `validation/known_limitations.md` | pending — manuscript Discussion §"Failure modes of the framework" covers the methodological limits; pilot-specific limitations gated on 1.1 |

### Phase 2 — Theoretical depth (D9 + 150 → D9 + 365)

Per [`theory/open_questions.md`](theory/open_questions.md), 10 items prioritized BLOCK / SHARPEN / DEFER (~8 weeks total). Sequenced:

| # | Open question | Priority | Effort (wk) | Status @ v0.3 |
|---|---|---|---|---|
| 2.1 | §1 Literature pass (related-work memo + positioning) | SHARPEN | 1.5 | **seeded** — [`theory/related_work.md`](theory/related_work.md) v0.1 (3 TB-IQ + 2 statistical anchor cites + novelty-gate skeleton); manuscript intro carries TB-IQ positioning; depth-pass reading pending |
| 2.2 | §3 Estimator validity / coverage simulations | BLOCK | 1.5 | **done @ D9 + 13/14/15; per-modality trio CLOSED** — [`theory/proofs/estimator.md`](theory/proofs/estimator.md) v0.4 backed by 4 sims in [`experiments/estimator_coverage/`](experiments/estimator_coverage/): AUC coverage (D9 + 13, 27 cells) + AUC power (D9 + 14, 24 cells, V3-9) + Dice (D9 + 15, 18 cells) + CR (D9 + 15, 24 cells); estimator defaults recorded (percentile / DeLong-for-AUC / BCa opt-in); both BLOCK sub-deliverables of §3 closed; per-modality trio (AUC / Dice / CR) closed; small-$n$ anti-conservativeness regime (n < 30) surfaced for the v0.2.0 library |
| 2.3 | §2 Sample-size formula (closed-form + numerical table) | BLOCK | 2.0 | **done @ D9 + 13** — [`theory/proofs/sample_size.md`](theory/proofs/sample_size.md) v0.1 with (S1) / (S3) / (S4) derivations + numerical tables + empirical validation vs §3 simulation. **Surfaces a v0.3 manuscript correction**: bump AUC-task default `ε` from 0.02 to 0.05 |
| 2.4 | §7 MRI mask distribution decision | BLOCK (MRI) | 1.0 | **done @ D9 + 13** — [`theory/proofs/mri_mask.md`](theory/proofs/mri_mask.md) v0.1 records option (c): `mask_family` rides inside Π as acquisition-protocol metadata, preserving 5-tuple shape across modalities |
| 2.5 | §5 Conditional monotonicity-in-r | SHARPEN | 1.0 | **partial @ D9 + 14** — [`theory/proofs/monotonicity.md`](theory/proofs/monotonicity.md) v0.1 records the conjecture + counterexample sketch + manuscript implication (V3-7); empirical check (compute credentials at r ∈ {0.40, 0.55, 0.70, 0.85} for 3 baselines that PASS at r = 0.25) still gated on Phase 1 pilot data |
| 2.6 | §8 PET model under list-mode reduction | SHARPEN | 0.5 | **done @ D9 + 13** — [`theory/proofs/pet_reduction.md`](theory/proofs/pet_reduction.md) v0.1 canonicalises activity-reduction as the v1 PET `T_r`; scan-time-reduction documented as v2 distinction |
| 2.7 | §6 Per-patient vs aggregate guidance | SHARPEN | 0.5 | **done at manuscript level** — Definition 2 (per-patient) opt-in; Discussion §"Aggregate-vs-per-patient" guidance present |
| 2.8 | §4 Composition law (likely negative result) | DEFER | 0.5 | **done @ D9 + 13** — [`theory/proofs/composition.md`](theory/proofs/composition.md) v0.1 records the negative-result position: no clean composition law exists; framework is point-evaluated by design |

Phase 2 work runs in parallel with the WS-1 IRB lag — no IRB dependency.

### Phase 3 — Library + multi-modality validation (D9 + 180 → D9 + 365)

| # | Task | Output | Status @ v0.3 |
|---|---|---|---|
| 3.1 | Implement `pwm_dose_equivalence.signal_equivalence_credential()` (CT validator) | Core library + CT example | **partial** — productionised package [`pwm_dose_equivalence/`](pwm_dose_equivalence/) at **v0.2.0 alpha** (modality-agnostic API + percentile / DeLong / **BCa** estimators + sample-size pre-flight with `bound_M` for unbounded metrics + small-$n$ anti-conservativeness warning + content-addressed framework hash + Tr_ct/Tr_mri/Tr_pet operators); **81/81 tests (incl. 10 end-to-end integration tests)** at 100 % line coverage on 265 statements; real-data CT example gated on Phase 1 pilot |
| 3.2 | Implement MRI validator (fastMRI knee dataset; variable-density Cartesian masks) | MRI example + integration test | **partial** — synthetic Cartesian-mask channel verified in [`experiments/cross_modality_consistency/`](experiments/cross_modality_consistency/) and via library `Tr_mri`; real fastMRI integration pending (D9 + 270) |
| 3.3 | Implement PET validator (NEMA IQ phantom; Poisson list-mode thinning) | PET example + integration test | **partial** — synthetic list-mode channel verified in `experiments/` and via library `Tr_pet`; real NEMA phantom integration pending (D9 + 270) |
| 3.4 | Pip-package; publish v0.1 to TestPyPI; gather feedback | TestPyPI listing | pending — `pyproject.toml` ready, package installs cleanly via `pip install -e ".[test]"`; TestPyPI upload is a single-command step gated on PyPI account auth (D9 + 365) |
| 3.5 | v1.0.0 release to PyPI alongside paper acceptance | PyPI listing | pending |
| 3.6 | Outreach to ≥ 3 external research groups to validate the library on their methods | Usage testimonials | pending |

### Phase 4 — Paper + on-chain (D9 + 270 → D9 + 540)

| # | Task | Output | Status @ v0.3 |
|---|---|---|---|
| 4.1 | Draft manuscript (intro, framework definition, theory, validators, three worked examples, discussion) | Draft v1 | **largely done at v0.3** — 19-pp draft in [`paper_draft/`](paper_draft/); intro / framework / methods (with corrected sample-size formula + estimator defaults) / discussion / software-rigor numbers complete; per-modality Results tables remain `\todo` pending 1.1, 3.2, 3.3 |
| 4.2 | Submit to *Nature Methods*; respond to reviewer comments (~6 mo) | Acceptance letter | pending |
| 4.3 | Author and register L2 spec on PWMRegistry (concurrent with submission) | Framework SHA-256 hash registered as L2 spec | pending |

---

## Timeline (D9-anchored)

D9 anchor ≈ 2026-05-20 (theory v0.1 seed date); today (2026-06-05) is **≈ D9 + 16**. Several pre-empirical milestones originally scheduled for D9 + 150, D9 + 240, and D9 + 270 landed ahead of schedule via the v0.2 reviewer-readiness pass (D9 + 12), the D9 + 13 theory-and-library pass, the D9 + 14 manuscript-side v0.3 propagation pass, the D9 + 15 path-1 non-AUC extension + library v0.2.0, and the D9 + 16 reviewer-reproduction surface (integration tests + reproduction guide).

| Date | Milestone | Status |
|---|---|---|
| **D9 + 12 (2026-06-01)** | **Manuscript v0.2 reviewer-readiness pass landed** — 7 pure-text edits closing 6 audit items + 1 synthetic experiment; 19 pp; credential JSON `schema_version` bumped to v0.2. See [`paper_draft/CHANGELOG.md`](paper_draft/CHANGELOG.md). | **done** |
| D9 + 12 (2026-06-01) | [`experiments/cross_modality_consistency/`](experiments/cross_modality_consistency/) — seed-reproducible 6-credential demonstration (3 modalities × 2 candidates) that the same code path produces 3 expected PASS + 3 expected FAIL verdicts. | **done** |
| D9 + 12 (2026-06-01) | [`theory/related_work.md`](theory/related_work.md) seeded — 3 new TB-IQ anchor cites (Barrett 1990; Barrett & Myers 2013; AAPM TG-233) on top of the 2 pre-existing statistical cites (Schuirmann; Piaggio), plus a "what is genuinely new" novelty-gate skeleton. Manuscript intro carries the TB-IQ positioning paragraph. | **seeded** (depth-pass pending) |
| **D9 + 13 (2026-06-02)** | **`theory/proofs/{mri_mask,pet_reduction,composition}.md` v0.1 writeups** paired with manuscript v0.2 commitments — closes open_questions §4, §7, §8 at the theory-side. | **done** |
| D9 + 13 (2026-06-02) | **`theory/proofs/estimator.md`** v0.1 + 27-cell coverage simulation in [`experiments/estimator_coverage/`](experiments/estimator_coverage/) — closes open_questions §3 BLOCK (first sub-deliverable, under the null); library estimator defaults recorded (percentile / DeLong-for-AUC / BCa opt-in). Original D9 + 240 target. The non-null power second sub-deliverable landed at D9 + 14 (V3-9). | **done ahead of schedule** |
| D9 + 13 (2026-06-02) | **`theory/proofs/sample_size.md`** v0.1 — closes open_questions §2 BLOCK with (S1) / (S3) / (S4) formulas, numerical tables, and empirical validation. **Surfaces a v0.3 manuscript correction** (AUC-task default `ε`). Original D9 + 240 target. | **done ahead of schedule** |
| D9 + 13 (2026-06-02) | **[`pwm_dose_equivalence/`](pwm_dose_equivalence/) v0.1.0 alpha** — pip-installable scaffold with modality-agnostic API + percentile / DeLong + sample-size pre-flight + content-addressed framework hash + Tr_ct/Tr_mri/Tr_pet operators. 60/60 tests, 100 % line coverage. Original D9 + 365 TestPyPI target's *codebase* ships today; the publish step is gated on PyPI auth. | **done ahead of schedule** |
| **D9 + 14 (2026-06-03)** | **Manuscript v0.2 → v0.3 propagation pass + v0.3 polish** — main pass applied V3-1 (AUC default ε corrected 0.02 → 0.05; non-AUC stays at 0.02), V3-2 (estimator-default text rewritten: percentile / DeLong-for-AUC / BCa opt-in), V3-3 (B5 software-rigor placeholders filled: 60 tests, 100 % coverage, v0.1.0), V3-4 (PET Table 1 footnote, fix `6fb1ee7` for the `\footnotemark` workaround), V3-5 (proofs cross-linked from §framework + Discussion). v0.3 polish (later same day) added V3-6 (Supplementary S1 on the Bernstein correction, +3 pp), V3-7 (`theory/proofs/monotonicity.md` v0.1), V3-8 (pinned-library-version fill), V3-9 (non-null power simulation closing the second deliverable of `open_questions.md` §3). Final: **22 pp**. See [`paper_draft/CHANGELOG.md`](paper_draft/CHANGELOG.md). | **done** |
| D9 + 90 | Phase 1 pilot 5-tuples computed on real cohorts (CT) — fills `Results` Table 2 (`\todo` placeholder until then). | pending |
| D9 + 150 | Literature pass **depth-read** complete (fastMRI reader studies; one CHO-for-low-dose-CT paper; Wunderlich/Noo observer-variance) → `theory/dose-equivalence-framework.md` bumped from v0.1 to v0.2 with the [SHARPEN-N] points reconciled against the manuscript v0.2. | pending |
| D9 + 270 | MRI worked-example data wrangling for the Results Table 3 fill; theory-side decision already recorded at D9 + 13 via [`proofs/mri_mask.md`](theory/proofs/mri_mask.md). | pending — data side only |
| D9 + 270 | PET worked-example data wrangling for Results Table 4 fill (NEMA NU-2 IQ phantom at multiple activity levels); theory-side decision already recorded at D9 + 13 via [`proofs/pet_reduction.md`](theory/proofs/pet_reduction.md). | pending — data side only |
| D9 + 365 | **Paper submitted to *Nature Methods*; framework SHA-256 hash registered as L2 spec on PWMRegistry; `pwm_dose_equivalence` v0.1 on TestPyPI**. | pending — package ready; submission + registration are real-world actions |
| D9 + 540 | **Paper accepted; library v1.0.0 on PyPI; ≥ 3 external groups using it.** | pending |

---

## Done when

### Progress at D9 + 14 (intermediate, not terminal)

**Landed at D9 + 12 (manuscript v0.2 reviewer-readiness pass):**

- [x] Manuscript v0.2 reviewer-readiness pass — 7 audit items closed (see [`paper_draft/CHANGELOG.md`](paper_draft/CHANGELOG.md))
- [x] Cross-modality consistency synthetic anchor — same code path, 6 expected verdicts, seed-reproducible ([`experiments/cross_modality_consistency/`](experiments/cross_modality_consistency/))
- [x] Task-based image-quality positioning + [`theory/related_work.md`](theory/related_work.md) seeded with 3 new TB-IQ anchor cites (Barrett 1990 / Barrett & Myers 2013 / AAPM TG-233)
- [x] Ground-truth protocol borrowed verbatim from WS-1 v0.5 annotation QA into `Methods → Estimator`
- [x] Π formalized as carrying acquisition-protocol metadata (CT vendor / MRI mask family / PET tracer); 5-tuple shape preserved across modalities

**Landed at D9 + 13 (theory-and-library pass):**

- [x] Coverage simulation (open_questions §3 first deliverable) — [`theory/proofs/estimator.md`](theory/proofs/estimator.md) + 27-cell sim in [`experiments/estimator_coverage/`](experiments/estimator_coverage/); library estimator defaults recorded. (Non-null power sim — second deliverable — landed at D9 + 14 as V3-9.)
- [x] Closed-form sample-size derivation (open_questions §2) — [`theory/proofs/sample_size.md`](theory/proofs/sample_size.md) with (S1) / (S3) / (S4) formulas, numerical tables, empirical validation; **v0.3 manuscript correction surfaced** (AUC-task default `ε`)
- [x] `theory/proofs/{mri_mask,pet_reduction,composition}.md` v0.1 — closes open_questions §4 / §7 / §8 at the theory side
- [x] [`pwm_dose_equivalence/`](pwm_dose_equivalence/) v0.1.0 alpha scaffold — pip-installable; **60/60 tests pass at 100 % line coverage** (well above the manuscript's 90 % v0.2 target)

**Landed at D9 + 14 (manuscript v0.2 → v0.3 propagation pass):**

- [x] **V3-1**: AUC-task default `ε` corrected (0.02 → 0.05; WS-1 v0.5 cohort now adequate); non-AUC keeps `ε = 0.02`. §methods-estimator "Sample-size formula" paragraph rewritten with the (S1) / (S3) formulas.
- [x] **V3-2**: §methods-estimator "Estimator defaults" paragraph rewritten — percentile / DeLong-for-AUC / BCa opt-in. Discussion §"Estimator failure modes" softened to DeLong + Monte-Carlo-SE language.
- [x] **V3-3**: B5 software-rigor placeholders filled — 60 unit tests, 100 % line coverage on 230 statements, v0.1.0 (alpha). Closes audit item B5.
- [x] **V3-4**: PET Table 1 footnote (activity-reduction canonical; scan-time-reduction is v2); `\footnote` → `\footnotemark` + `\footnotetext` typesetting fix so the body actually renders.
- [x] **V3-5**: `theory/proofs/{estimator,sample_size,mri_mask,pet_reduction,composition}.md` cross-linked from §framework, §methods-estimator, Discussion §"Point-evaluated by design", and the PET Table 1 footnote.
- [x] **V3-6**: Supplementary Section S1 (Bernstein finite-sample correction) appended to the manuscript inside `\appendix`; `\todo{supp section}` placeholder replaced with `\ref{supp:bernstein}`. PDF +3 pages (19 → 22).
- [x] **V3-7**: `theory/proofs/monotonicity.md` v0.1 closes the theory side of open_questions §5; empirical check (compute credentials at r ∈ {0.40, 0.55, 0.70, 0.85} for 3 baselines that PASS at r = 0.25) still gated on Phase 1 pilot data.
- [x] **V3-8**: `\todo{pinned-version-at-submission}` filled with `pwm_dose_equivalence==0.1.0` (released against credential schema v0.2; re-pinned at submission).
- [x] **V3-9**: Non-null power simulation — second deliverable of `open_questions.md` §3 closed. `experiments/estimator_coverage/power_sim.py` + frozen `power_results.json` (24 cells, ~25 min, seed = 42); `theory/proofs/estimator.md` bumped v0.1 → v0.2 with new §4a (verdict-distribution table + cohort-sizing implication: WS-1 v0.5 cohort of n ≈ 208 is exactly where INDETERMINATE-but-truly-equivalent is the modal null outcome — absence of `PASS` is not evidence of non-equivalence).

**Landed at D9 + 15 (path-1 non-AUC extension pass):**

- [x] **Dice coverage + power sim** ([`experiments/estimator_coverage/dice_sim.py`](experiments/estimator_coverage/dice_sim.py), commit `d8c45e1`): 18 cells; closes the *AUC-only* caveat in `proofs/estimator.md` §5.1. Headline: at realistic clinical $\sigma_\Delta = 0.05$ and $n \geq 200$, the framework PASSes cleanly under the null (P(`PASS`) = 1.000) — substantively different from the AUC-at-the-same-n case (P(`PASS`) ≈ 0.40). `proofs/estimator.md` bumped v0.2 → v0.3 with new §4b.
- [x] **CR (PET phantom) coverage + power sim** ([`experiments/estimator_coverage/cr_sim.py`](experiments/estimator_coverage/cr_sim.py), commit `1911b68`): 24 cells; **per-modality metric trio CLOSED** (AUC + Dice + CR). Headline finding: percentile bootstrap is anti-conservative at very small $n$ (n=6: coverage 0.82–0.88; n=12: 0.88–0.93). At $n \geq 30$ coverage returns to nominal. Recommended PET phantom cohort: $n \geq 30$ (≥ 5 acquisitions). `proofs/estimator.md` bumped v0.3 → v0.4 with new §4c; §5.1 caveat closed; v0.2.0 library item recorded (small-$n$ warning for non-AUC metrics).

**Landed at D9 + 15, late (Library v0.2.0):**

- [x] **L0.2-1 BCa estimator exposure** (commit `8e6dbdb`): generalised Efron 1987 bias-corrected accelerated bootstrap exposed as `estimator="bca"`; opt-in only per the v0.3 §4 decision; degenerate-input fallback to percentile.
- [x] **L0.2-2 Small-$n$ anti-conservativeness warning** (commit `8e6dbdb`): `UserWarning` fires for any percentile or BCa call at $n < 30$, citing the V3-11 finding in `proofs/estimator.md` §4c.
- [x] **L0.2-3 `bound_M` argument** (commit `8e6dbdb`): exposes the Bernstein bound's $M$ parameter for unbounded metrics (MAE / MSE). Larger `bound_M` strictly grows the Bernstein requirement; CLT bound unaffected.
- [x] Library version bump 0.1.0 → 0.2.0; 60/60 → 71/71 tests at 100 % coverage on 265 statements.

**Landed at D9 + 16 (reviewer-reproduction surface):**

- [x] **L0.2-4 Integration tests** (commit `a5b5163`): 10 new end-to-end tests in `tests/test_integration.py` exercising the full credential-issuance pipeline through the public API (CT AUC / MRI Dice / PET CR per-modality; cross-modality consistency via production library; JSON round-trip + framework-hash audit; seeded reproducibility; T_r integration; verdict transitions). 71/71 → **81/81 tests** at 100 % coverage (unchanged 265 statements; integration tests exercise existing code paths).
- [x] **R3-1 `paper_draft/reproduction_guide.md`** (commit `558d112`): 12-section reviewer walkthrough mapping every numerical claim in v0.3 to its repo anchor + the command that re-derives it; 16-row per-claim anchor table; introduces the `R3-N` ID convention for reviewer-facing reproduction artifacts.
- [x] **R3-2 Tutorial notebooks** (commit `db1d31b`): three pedagogical tutorials in [`pwm_dose_equivalence/notebooks/`](pwm_dose_equivalence/notebooks/), one per validated modality — `01_ct_lung_nodule_auc.py` (DeLong + §4a cohort-sizing table); `02_mri_meniscus_dice.py` (percentile + (S1) / (S4) pre-flight + BCa opt-in); `03_pet_phantom_cr.py` (activity-reduction + small-n warning demo at n = 6). Format: `.py` with `#%%` cell markers — runs as both Python scripts and Jupyter notebooks. Closes the manuscript §software_rigor "three tutorial notebooks (one per validated modality)" claim.
- [x] **R3-3 Modality-extension tutorial** (commit `00880ed`): `notebooks/04_optical_extending.py` shows how a user defines their own `T_r` operator (worked example: Optical / fluorescence at 25 % exposure) and plugs it through the unchanged `signal_equivalence_credential` API. Closes the manuscript Methods Table 7 "Optical / fluorescence: specified; not validated; **user-implementable**" claim with a concrete worked example; PASS verdict at n = 80 specimens.
- [x] **R3-4 Credential reading guide** (this commit): new [`paper_draft/credential_reading_guide.md`](paper_draft/credential_reading_guide.md) — 8-section walk through a published credential JSON for reviewers / regulators / clinicians who need to *interpret* a credential without re-running the bootstrap themselves. Covers verdict semantics (PASS / FAIL / INDETERMINATE), CI vs $\varepsilon$ reading, the framework-hash guarantees + non-guarantees (3 + 3), the `sample_size_check` field (with the WS-1 v0.5 INDETERMINATE-dominated regime called out by name at n ≈ 208 / AUC ≈ 0.92), 7 common reviewer / regulator questions, and a 9-entry red-flag checklist. Audience-disjoint from `reproduction_guide.md`: the reproduction guide answers "how do I re-derive the numbers?"; the reading guide answers "how do I read a credential someone else published?" `reproduction_guide.md` §10a + library README "Tutorial notebooks" section + manuscript §software_rigor "Documentation and tutorial notebooks" paragraph updated to point at both companion documents. **Closes the manuscript §software_rigor "Credential reading guide" claim**, leaving zero unbacked claims in that paragraph.

**Still pending (theory-time-blocked / data-blocked, not in-session executable):**

- [ ] Literature depth-pass complete (fastMRI reader studies / one CHO-for-LDCT paper / Wunderlich–Noo observer-variance) → `theory/dose-equivalence-framework.md` bumped from v0.1 to v0.2
- [ ] Conditional monotonicity-in-`r` empirical check (open_questions §5; best after Phase 1 pilot data)

### Terminal acceptance criteria

- [ ] *Nature Methods* paper accepted (or fallback venue: *IEEE TMI* / *Medical Image Analysis*)
- [ ] Per-modality Results tables filled with real-cohort numbers — Table 2 (CT, Phase 1 pilot), Table 3 (MRI, fastMRI knee), Table 4 (PET, NEMA NU-2 IQ phantom)
- [ ] `pwm_dose_equivalence` v1.0.0 on PyPI with ≥ 2 modality validators
- [ ] Framework SHA-256 hash registered as L2 spec on PWMRegistry mainnet
- [ ] ≥ 3 external research groups have computed a credential under the framework
- [ ] Phase 1 pilot data published as supplementary alongside the manuscript

---

## Subfolders

| Path | Purpose | Status |
|---|---|---|
| [`paper_draft/`](paper_draft/) | *Nature Methods* manuscript + reviewer-facing reproduction guide + non-coder reading guide | **v0.3 working draft** (22 pp incl. 3-pp Supplementary S1; see [`paper_draft/CHANGELOG.md`](paper_draft/CHANGELOG.md)). Two reviewer-facing companions: [`paper_draft/reproduction_guide.md`](paper_draft/reproduction_guide.md) maps every numerical claim to its repo anchor + the command that re-derives it (16-row per-claim table; for code-savvy reviewers); [`paper_draft/credential_reading_guide.md`](paper_draft/credential_reading_guide.md) walks a credential JSON field-by-field with verdict semantics + framework-hash guarantees + a 9-entry red-flag checklist (for non-coder reviewers / regulators / clinicians). |
| [`theory/`](theory/) | Formal definition ([`dose-equivalence-framework.md`](theory/dose-equivalence-framework.md)), open-questions work plan ([`open_questions.md`](theory/open_questions.md)), related-work memo ([`related_work.md`](theory/related_work.md)) | **v0.1 seeded** — definition + work plan + related-work memo |
| [`theory/proofs/`](theory/proofs/) | Theory-side decision writeups paired with the manuscript v0.2 / v0.3 commitments: `mri_mask.md` (§7), `pet_reduction.md` (§8), `composition.md` (§4), `estimator.md` (§3, **v0.4 with AUC + Dice + CR sims backing — per-modality trio closed**), `sample_size.md` (§2, numerical table + the AUC `ε` correction that v0.3 V3-1 applied), `monotonicity.md` (§5, conjecture + counterexample sketch; empirical check gated on Phase 1 pilot) | **6 writeups landed at D9 + 13/14; estimator.md extended to v0.4 at D9 + 15 with Dice + CR sims; manuscript-side propagation landed at D9 + 14** (V3-1 / V3-2 / V3-4 / V3-5 / V3-6 / V3-7 / V3-8 / V3-9 — see [`paper_draft/CHANGELOG.md`](paper_draft/CHANGELOG.md)). Sections §2 / §3 / §4 / §7 / §8 closed (all BLOCKs done; §3 per-modality trio closed); §5 partially closed (theory side; empirical check gated on Phase 1 pilot); §1 depth-pass still pending. |
| [`experiments/cross_modality_consistency/`](experiments/cross_modality_consistency/) | Synthetic anchor for the modality-general claim — same bootstrap code path applied to 3 `T_r` operators; 6 credentials (3 PASS + 3 FAIL) at seed=42 | **reproducible** — `results.json` committed; not data-blocked |
| [`experiments/estimator_coverage/`](experiments/estimator_coverage/) | **Four** seed-reproducible simulations of the paired-bootstrap estimator covering the per-modality trio: `coverage_sim.py` (27 cells, ~35 min, AUC null) + `power_sim.py` (24 cells, ~25 min, AUC non-null) + `dice_sim.py` (18 cells, ~2.5 min, Dice / MRI) + `cr_sim.py` (24 cells, ~3 min, CR / PET phantom). All four back the estimator-default decision in `theory/proofs/estimator.md` §§2 / 4a / 4b / 4c; the CR sim surfaces a small-$n$ anti-conservativeness regime (n < 30) recorded as a v0.2.0 library item. | **reproducible** — `results.json` + `power_results.json` + `dice_results.json` + `cr_results.json` committed; seed = 42 |
| [`pwm_dose_equivalence/`](pwm_dose_equivalence/) | Pip-installable Python library + four tutorial notebooks in `notebooks/` (three per validated modality + one extending-to-a-new-modality worked example); the productionised counterpart to the experiments-folder prototype | **v0.2.0 alpha** — 81/81 tests (incl. 10 end-to-end integration tests) at 100 % line coverage on 265 statements; v0.2.0 added BCa + small-$n$ warning + `bound_M` + integration tests + tutorial notebooks (R3-2 / R3-3); TestPyPI publish pending (D9 + 365); v1.0.0 alongside paper acceptance (D9 + 540) |
| `validation/` | Per-modality empirical 5-tuple computation on **real patient cohorts** (CT first, then MRI / PET). Distinct from `experiments/`, which is synthetic. | pending Phase 1 pilot (D9 + 90) |

---

## Why generalize beyond CT

| Reason | Detail |
|---|---|
| **Venue bar** | *Nature Methods* publishes general methodological frameworks. A CT-only framework is *IEEE TMI* material. CT + MRI + PET is the *Nature Methods* story. |
| **Theoretical cost is low — empirically backed at v0.2** | The formal definition in [`theory/dose-equivalence-framework.md`](theory/dose-equivalence-framework.md) is signal-reduction-agnostic by construction. The synthetic [`experiments/cross_modality_consistency/`](experiments/cross_modality_consistency/) demonstration shows the *same code path* applied to three modality-specific `T_r` operators (Poisson CT, Cartesian-mask MRI, list-mode PET) produces the expected 3 PASS + 3 FAIL verdicts at seed=42 — so "modality-general" is not rhetorical. The remaining MRI / PET cost is one *empirical* worked example each on real data, not new theory. |
| **Schema survives modality transitions** | The 5-tuple shape (`r, T, ε, α, Π`) holds across modalities because Π is formalized to carry acquisition-protocol metadata (CT vendor / kVp; MRI mask family; PET tracer / scanner). The single-API-call claim in the manuscript's Results section is therefore a real schema invariant, not a presentational convenience. |
| **Citation surface** | A modality-general framework gets cited by MRI groups and PET groups, not just CT. Cross-modality citations compound the WS-2 paper's reach. |
| **Lineage compatibility** | The framework composes cleanly with the existing task-based image-quality assessment lineage (Barrett 1990 / Barrett & Myers 2013 / AAPM TG-233 — see [`theory/related_work.md`](theory/related_work.md)). Any TB-IQ figure of merit (channelized Hotelling observer; ideal-observer SNR) is a valid metric `P` inside a credential. TB-IQ itself is a modality-general tradition, so multi-modal positioning is the natural fit, not a stretch. |

---

## Cross-references

**Inside WS-2 — documents:**

- [`paper_draft/CHANGELOG.md`](paper_draft/CHANGELOG.md) — v0.1 → v0.2 → v0.3 → v0.3-polish deltas with one row per closed audit item / triggered edit and its commit; the manifest for the reviewer-readiness pass + the D9 + 13 / D9 + 14 propagation passes; also logs the V3-9 downstream-doc propagation into the WS-1 README in two passes (Cross-references entry + Target specs new row), the **bidirectional-flow framing landings** across both READMEs (`88c963a`, `5c4d028`), and the 7-place audit trail for the V3-9 finding.
- [`theory/dose-equivalence-framework.md`](theory/dose-equivalence-framework.md) — formal definition v0.1. Intentionally lags the manuscript v0.2; its own header says it is superseded by v0.2 after the literature pass (see `open_questions.md` §1).
- [`theory/open_questions.md`](theory/open_questions.md) — BLOCK / SHARPEN / DEFER work plan for Phase 2 theory; the §-numbering is cross-referenced from `related_work.md`, the `theory/proofs/*.md` writeups, and this README's `Phase 2` task table above.
- [`theory/related_work.md`](theory/related_work.md) — 5-paper memo (2 statistical + 3 TB-IQ anchor cites) seeded alongside the manuscript A6 positioning paragraph. Hosts the "what is genuinely new" novelty gate for the theory-doc v0.2 bump.

**Inside WS-2 — `theory/proofs/` (theory-side writeups paired with manuscript v0.2 / v0.3 commitments):**

- [`theory/proofs/estimator.md`](theory/proofs/estimator.md) — open_questions §3. Coverage theorem + 27-cell empirical table; estimator-default decision (percentile / DeLong-for-AUC / BCa opt-in).
- [`theory/proofs/sample_size.md`](theory/proofs/sample_size.md) — open_questions §2. (S1) / (S3) / (S4) formulas + numerical tables + empirical validation; surfaces a v0.3 manuscript correction on AUC-task default `ε`.
- [`theory/proofs/mri_mask.md`](theory/proofs/mri_mask.md) — open_questions §7. `mask_family` rides inside Π as acquisition-protocol metadata.
- [`theory/proofs/pet_reduction.md`](theory/proofs/pet_reduction.md) — open_questions §8. Activity-reduction canonicalised as v1 PET `T_r`; scan-time-reduction is v2.
- [`theory/proofs/composition.md`](theory/proofs/composition.md) — open_questions §4. Negative-result note: no clean composition law; framework is point-evaluated by design.

**Inside WS-2 — experiments and library:**

- [`experiments/cross_modality_consistency/`](experiments/cross_modality_consistency/) — synthetic anchor for the modality-general claim; ships seed-reproducible `results.json` and is cited from the manuscript's Cross-modality consistency Results subsection.
- [`experiments/estimator_coverage/`](experiments/estimator_coverage/) — four simulations covering the per-modality metric trio: 27-cell AUC coverage + 24-cell AUC power (V3-9) + 18-cell Dice + 24-cell CR (PET phantom). All four back the `theory/proofs/estimator.md` decisions; the CR sim also surfaces a small-$n$ anti-conservativeness regime (n < 30) recorded as a v0.2.0 library item.
- [`pwm_dose_equivalence/`](pwm_dose_equivalence/) — pip-installable **v0.2.0 alpha** library. Modality-agnostic `signal_equivalence_credential` + percentile / DeLong / **BCa** estimators + sample-size pre-flight (incl. `bound_M` for unbounded metrics) + small-$n$ anti-conservativeness warning + content-addressed framework hash + Tr_ct/Tr_mri/Tr_pet operators. 81/81 tests (incl. 10 end-to-end integration tests), 100 % line coverage on 265 statements. **Four tutorial notebooks** in [`pwm_dose_equivalence/notebooks/`](pwm_dose_equivalence/notebooks/) — three validated (CT AUC / MRI Dice / PET CR) + one extending-to-new-modality (Optical, R3-3).

**Sibling workstreams:**

- [`../WS-1_dataset/`](../WS-1_dataset/) — provides the CT validation data and the **annotation QA protocol** that WS-2's Methods → Estimator section borrows verbatim for ground-truth provenance. The cross-workstream flow is now bidirectional: WS-2's V3-9 power-sim cohort-sizing implication is surfaced into the WS-1 README in two places — the Cross-references → WS-2 entry (`d0569f3`) and the Target specs *Credential-issuance regime* table row (`7817fad`) — telling downstream WS-1 users to expect `INDETERMINATE` verdicts on the v0.5 cohort for genuinely equivalent methods.
- [`../WS-3_reference_method/`](../WS-3_reference_method/) — Phase 1 pilot consumes WS-3 baselines as `M_ref` candidates; each WS-3 release must publish under a 5-tuple credential issued via this framework.
- [`../WS-4_leaderboard/`](../WS-4_leaderboard/) — every leaderboard submission is verified by recomputing the credential against the content-addressed framework hash. The manuscript's end-to-end case study points at WS-4 as the acceptance-test community.

**PWM integration:**

- [`../pwm_integration/l2_spec.md`](../pwm_integration/l2_spec.md) — public-registry resolver for the SHA-256 hash of the framework definition. One of three resolvers (local file / PyPI release / PWM registry) the manuscript enumerates; the registry is a deployment option for long-term decentralized resolution, not the methodological substance of the credential schema.
