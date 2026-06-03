# WS-2 — Signal-Equivalence Framework (Track 9 sub-track 9b)

The **signal-equivalence framework**: a formal, modality-general mathematical replacement for vendor-style claims like *"50% dose reduction"*, *"4× MRI acceleration"*, or *"25% activity PET"*. Each claim is converted into a testable 5-tuple credential `(signal_ratio, task, ε, α, subpopulation)`.

> **Status (D9 + 14, 2026-06-03):** manuscript at **v0.3 working draft**, 19 pp ([`paper_draft/CHANGELOG.md`](paper_draft/CHANGELOG.md) v0.2 → v0.3). v0.3 applied the 5 edits triggered by the D9 + 13 theory-and-library pass: AUC default $\varepsilon$ corrected (0.02 → 0.05; non-AUC stays at 0.02); §methods-estimator estimator-default paragraph rewritten (percentile / DeLong-for-AUC / BCa opt-in); B5 software-rigor placeholders filled (60 tests, 100 % coverage, v0.1.0); PET Table 1 footnote; proofs cross-linked. Theory side: [`theory/proofs/`](theory/proofs/) v0.1 writeups + 27-cell coverage sim in [`experiments/estimator_coverage/`](experiments/estimator_coverage/). Library side: [`pwm_dose_equivalence/`](pwm_dose_equivalence/) v0.1.0 alpha — pip-installable, 60/60 tests, 100 % line coverage. Real-cohort per-modality Results tables remain gated on WS-2 Phase 1 (CT) and Phase 3 (MRI / PET data integrations).

---

## Goals

1. **Publish a peer-reviewed paper** at ***Nature Methods*** (primary) introducing the framework. Fallback: *IEEE Transactions on Medical Imaging* or *Medical Image Analysis*. Working draft is at v0.3 in [`paper_draft/`](paper_draft/) — see [`paper_draft/CHANGELOG.md`](paper_draft/CHANGELOG.md) for the v0.1 → v0.2 → v0.3 deltas.
2. **Ship `pwm_dose_equivalence` on PyPI** with ≥ 2 modality validators (CT + MRI minimum; PET stretch). `pip install pwm_dose_equivalence` works for any external user. The pip-installable scaffold lives at [`pwm_dose_equivalence/`](pwm_dose_equivalence/) at **v0.1.0 alpha** (60/60 tests, 100 % line coverage); the synthetic-only [`experiments/cross_modality_consistency/`](experiments/cross_modality_consistency/) prototype is preserved as the modality-general consistency anchor. Phase 3 remaining: TestPyPI publish (D9 + 365), real-data CT / MRI / PET integrations, v1.0.0 release (D9 + 540).
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

| # | Task | Output | Status @ v0.2 |
|---|---|---|---|
| 1.1 | Compute the 5-tuple credential for each of the 3 reproduced WS-3 baselines on AAPM 2016 + LIDC-IDRI | `validation/heyang_pilot_5_tuples.json` | pending (data-blocked on Phase 1 cohort) |
| 1.2 | End-to-end implementability check — does the v0.1 definition survive contact with real data? | Decision: commit to v0.1 or revise before Phase 2 | **partial** — definition revised to v0.2 (A3 / A5 / B1 / B3 / A4 per [`paper_draft/CHANGELOG.md`](paper_draft/CHANGELOG.md)); empirical "survive contact" test still gated on 1.1 |
| 1.3 | Methodology memo: how the pilot computes the credential | `validation/methodology.md` | pending — manuscript Methods §Estimator now covers the protocol; pilot-specific memo gated on 1.1 |
| 1.4 | Known limitations memo | `validation/known_limitations.md` | pending — manuscript Discussion §"Failure modes of the framework" covers the methodological limits; pilot-specific limitations gated on 1.1 |

### Phase 2 — Theoretical depth (D9 + 150 → D9 + 365)

Per [`theory/open_questions.md`](theory/open_questions.md), 10 items prioritized BLOCK / SHARPEN / DEFER (~8 weeks total). Sequenced:

| # | Open question | Priority | Effort (wk) | Status @ v0.2 |
|---|---|---|---|---|
| 2.1 | §1 Literature pass (related-work memo + positioning) | SHARPEN | 1.5 | **seeded** — [`theory/related_work.md`](theory/related_work.md) v0.1 (3 TB-IQ + 2 statistical anchor cites + novelty-gate skeleton); manuscript intro carries TB-IQ positioning; depth-pass reading pending |
| 2.2 | §3 Estimator validity / coverage simulations | BLOCK | 1.5 | **done @ D9 + 13** — [`theory/proofs/estimator.md`](theory/proofs/estimator.md) v0.1 backed by 27-cell sim in [`experiments/estimator_coverage/`](experiments/estimator_coverage/); estimator defaults recorded (percentile / DeLong-for-AUC / BCa opt-in); non-null power sim is the follow-up |
| 2.3 | §2 Sample-size formula (closed-form + numerical table) | BLOCK | 2.0 | **done @ D9 + 13** — [`theory/proofs/sample_size.md`](theory/proofs/sample_size.md) v0.1 with (S1) / (S3) / (S4) derivations + numerical tables + empirical validation vs §3 simulation. **Surfaces a v0.3 manuscript correction**: bump AUC-task default `ε` from 0.02 to 0.05 |
| 2.4 | §7 MRI mask distribution decision | BLOCK (MRI) | 1.0 | **done @ D9 + 13** — [`theory/proofs/mri_mask.md`](theory/proofs/mri_mask.md) v0.1 records option (c): `mask_family` rides inside Π as acquisition-protocol metadata, preserving 5-tuple shape across modalities |
| 2.5 | §5 Conditional monotonicity-in-r | SHARPEN | 1.0 | pending (best after Phase 1 pilot data lands for empirical check) |
| 2.6 | §8 PET model under list-mode reduction | SHARPEN | 0.5 | **done @ D9 + 13** — [`theory/proofs/pet_reduction.md`](theory/proofs/pet_reduction.md) v0.1 canonicalises activity-reduction as the v1 PET `T_r`; scan-time-reduction documented as v2 distinction |
| 2.7 | §6 Per-patient vs aggregate guidance | SHARPEN | 0.5 | **done at manuscript level** — Definition 2 (per-patient) opt-in; Discussion §"Aggregate-vs-per-patient" guidance present |
| 2.8 | §4 Composition law (likely negative result) | DEFER | 0.5 | **done @ D9 + 13** — [`theory/proofs/composition.md`](theory/proofs/composition.md) v0.1 records the negative-result position: no clean composition law exists; framework is point-evaluated by design |

Phase 2 work runs in parallel with the WS-1 IRB lag — no IRB dependency.

### Phase 3 — Library + multi-modality validation (D9 + 180 → D9 + 365)

| # | Task | Output | Status @ v0.2 |
|---|---|---|---|
| 3.1 | Implement `pwm_dose_equivalence.signal_equivalence_credential()` (CT validator) | Core library + CT example | **partial** — productionised package [`pwm_dose_equivalence/`](pwm_dose_equivalence/) at v0.1.0 alpha (modality-agnostic API + percentile / DeLong estimators + sample-size pre-flight + content-addressed framework hash + Tr_ct/Tr_mri/Tr_pet operators); 60/60 tests pass at 100 % line coverage; real-data CT example gated on Phase 1 pilot |
| 3.2 | Implement MRI validator (fastMRI knee dataset; variable-density Cartesian masks) | MRI example + integration test | **partial** — synthetic Cartesian-mask channel verified in [`experiments/cross_modality_consistency/`](experiments/cross_modality_consistency/) and via library `Tr_mri`; real fastMRI integration pending (D9 + 270) |
| 3.3 | Implement PET validator (NEMA IQ phantom; Poisson list-mode thinning) | PET example + integration test | **partial** — synthetic list-mode channel verified in `experiments/` and via library `Tr_pet`; real NEMA phantom integration pending (D9 + 270) |
| 3.4 | Pip-package; publish v0.1 to TestPyPI; gather feedback | TestPyPI listing | pending — `pyproject.toml` ready, package installs cleanly via `pip install -e ".[test]"`; TestPyPI upload is a single-command step gated on PyPI account auth (D9 + 365) |
| 3.5 | v1.0.0 release to PyPI alongside paper acceptance | PyPI listing | pending |
| 3.6 | Outreach to ≥ 3 external research groups to validate the library on their methods | Usage testimonials | pending |

### Phase 4 — Paper + on-chain (D9 + 270 → D9 + 540)

| # | Task | Output | Status @ v0.2 |
|---|---|---|---|
| 4.1 | Draft manuscript (intro, framework definition, theory, validators, three worked examples, discussion) | Draft v1 | **largely done at v0.2** — 19-pp draft in [`paper_draft/`](paper_draft/); intro / framework / methods / discussion complete; per-modality Results tables remain `\todo` pending 1.1, 3.2, 3.3 |
| 4.2 | Submit to *Nature Methods*; respond to reviewer comments (~6 mo) | Acceptance letter | pending |
| 4.3 | Author and register L2 spec on PWMRegistry (concurrent with submission) | Framework SHA-256 hash registered as L2 spec | pending |

---

## Timeline (D9-anchored)

D9 anchor ≈ 2026-05-20 (theory v0.1 seed date); today (2026-06-02) is **≈ D9 + 13**. Several pre-empirical milestones originally scheduled for D9 + 150, D9 + 240, and D9 + 270 landed ahead of schedule via the v0.2 reviewer-readiness pass and the D9 + 13 theory-and-library pass.

| Date | Milestone | Status |
|---|---|---|
| **D9 + 12 (2026-06-01)** | **Manuscript v0.2 reviewer-readiness pass landed** — 7 pure-text edits closing 6 audit items + 1 synthetic experiment; 19 pp; credential JSON `schema_version` bumped to v0.2. See [`paper_draft/CHANGELOG.md`](paper_draft/CHANGELOG.md). | **done** |
| D9 + 12 (2026-06-01) | [`experiments/cross_modality_consistency/`](experiments/cross_modality_consistency/) — seed-reproducible 6-credential demonstration (3 modalities × 2 candidates) that the same code path produces 3 expected PASS + 3 expected FAIL verdicts. | **done** |
| D9 + 12 (2026-06-01) | [`theory/related_work.md`](theory/related_work.md) seeded — 3 new TB-IQ anchor cites (Barrett 1990; Barrett & Myers 2013; AAPM TG-233) on top of the 2 pre-existing statistical cites (Schuirmann; Piaggio), plus a "what is genuinely new" novelty-gate skeleton. Manuscript intro carries the TB-IQ positioning paragraph. | **seeded** (depth-pass pending) |
| **D9 + 13 (2026-06-02)** | **`theory/proofs/{mri_mask,pet_reduction,composition}.md` v0.1 writeups** paired with manuscript v0.2 commitments — closes open_questions §4, §7, §8 at the theory-side. | **done** |
| D9 + 13 (2026-06-02) | **`theory/proofs/estimator.md`** v0.1 + 27-cell coverage simulation in [`experiments/estimator_coverage/`](experiments/estimator_coverage/) — closes open_questions §3 BLOCK; library estimator defaults recorded (percentile / DeLong-for-AUC / BCa opt-in). Original D9 + 240 target. | **done ahead of schedule** |
| D9 + 13 (2026-06-02) | **`theory/proofs/sample_size.md`** v0.1 — closes open_questions §2 BLOCK with (S1) / (S3) / (S4) formulas, numerical tables, and empirical validation. **Surfaces a v0.3 manuscript correction** (AUC-task default `ε`). Original D9 + 240 target. | **done ahead of schedule** |
| D9 + 13 (2026-06-02) | **[`pwm_dose_equivalence/`](pwm_dose_equivalence/) v0.1.0 alpha** — pip-installable scaffold with modality-agnostic API + percentile / DeLong + sample-size pre-flight + content-addressed framework hash + Tr_ct/Tr_mri/Tr_pet operators. 60/60 tests, 100 % line coverage. Original D9 + 365 TestPyPI target's *codebase* ships today; the publish step is gated on PyPI auth. | **done ahead of schedule** |
| D9 + 90 | Phase 1 pilot 5-tuples computed on real cohorts (CT) — fills `Results` Table 2 (`\todo` placeholder until then). | pending |
| D9 + 150 | Literature pass **depth-read** complete (fastMRI reader studies; one CHO-for-low-dose-CT paper; Wunderlich/Noo observer-variance) → `theory/dose-equivalence-framework.md` bumped from v0.1 to v0.2 with the [SHARPEN-N] points reconciled against the manuscript v0.2. | pending |
| D9 + 270 | MRI worked-example data wrangling for the Results Table 3 fill; theory-side decision already recorded at D9 + 13 via [`proofs/mri_mask.md`](theory/proofs/mri_mask.md). | pending — data side only |
| D9 + 270 | PET worked-example data wrangling for Results Table 4 fill (NEMA NU-2 IQ phantom at multiple activity levels); theory-side decision already recorded at D9 + 13 via [`proofs/pet_reduction.md`](theory/proofs/pet_reduction.md). | pending — data side only |
| D9 + 365 | **Paper submitted to *Nature Methods*; framework SHA-256 hash registered as L2 spec on PWMRegistry; `pwm_dose_equivalence` v0.1 on TestPyPI**. | pending — package ready; submission + registration are real-world actions |
| D9 + 540 | **Paper accepted; library v1.0.0 on PyPI; ≥ 3 external groups using it.** | pending |

---

## Done when

### Progress at D9 + 13 (intermediate, not terminal)

**Landed at D9 + 12 (manuscript v0.2 pass):**

- [x] Manuscript v0.2 reviewer-readiness pass — 7 audit items closed (see [`paper_draft/CHANGELOG.md`](paper_draft/CHANGELOG.md))
- [x] Cross-modality consistency synthetic anchor — same code path, 6 expected verdicts, seed-reproducible ([`experiments/cross_modality_consistency/`](experiments/cross_modality_consistency/))
- [x] Task-based image-quality positioning + [`theory/related_work.md`](theory/related_work.md) seeded with 3 new TB-IQ anchor cites (Barrett 1990 / Barrett & Myers 2013 / AAPM TG-233)
- [x] Ground-truth protocol borrowed verbatim from WS-1 v0.5 annotation QA into `Methods → Estimator`
- [x] Π formalized as carrying acquisition-protocol metadata (CT vendor / MRI mask family / PET tracer); 5-tuple shape preserved across modalities

**Landed at D9 + 13 (theory-and-library pass):**

- [x] Coverage simulations (open_questions §3) — [`theory/proofs/estimator.md`](theory/proofs/estimator.md) + 27-cell sim in [`experiments/estimator_coverage/`](experiments/estimator_coverage/); library estimator defaults recorded
- [x] Closed-form sample-size derivation (open_questions §2) — [`theory/proofs/sample_size.md`](theory/proofs/sample_size.md) with (S1) / (S3) / (S4) formulas, numerical tables, empirical validation; **v0.3 manuscript correction surfaced** (AUC-task default `ε`)
- [x] `theory/proofs/{mri_mask,pet_reduction,composition}.md` v0.1 — closes open_questions §4 / §7 / §8 at the theory side
- [x] [`pwm_dose_equivalence/`](pwm_dose_equivalence/) v0.1.0 alpha scaffold — pip-installable; **60/60 tests pass at 100 % line coverage** (well above the manuscript's 90 % v0.2 target)

**Still pending (theory-time-blocked, not data-blocked):**

- [ ] Literature depth-pass complete (fastMRI reader studies / one CHO-for-LDCT paper / Wunderlich–Noo observer-variance) → `theory/dose-equivalence-framework.md` bumped from v0.1 to v0.2
- [ ] Non-null power simulation for the paired-bootstrap estimator (open_questions §3 second deliverable)
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
| [`paper_draft/`](paper_draft/) | *Nature Methods* manuscript | **v0.3 working draft** (19 pp; see [`paper_draft/CHANGELOG.md`](paper_draft/CHANGELOG.md)) |
| [`theory/`](theory/) | Formal definition ([`dose-equivalence-framework.md`](theory/dose-equivalence-framework.md)), open-questions work plan ([`open_questions.md`](theory/open_questions.md)), related-work memo ([`related_work.md`](theory/related_work.md)) | **v0.1 seeded** — definition + work plan + related-work memo |
| [`theory/proofs/`](theory/proofs/) | Theory-side decision writeups paired with the manuscript v0.2 commitments: `mri_mask.md` (§7), `pet_reduction.md` (§8), `composition.md` (§4), `estimator.md` (§3, with empirical coverage), `sample_size.md` (§2, with numerical table + manuscript-correction note) | **5 writeups landed at D9 + 13** — sections §2 / §3 / §4 / §7 / §8 closed; §1 depth-pass + §5 monotonicity still pending |
| [`experiments/cross_modality_consistency/`](experiments/cross_modality_consistency/) | Synthetic anchor for the modality-general claim — same bootstrap code path applied to 3 `T_r` operators; 6 credentials (3 PASS + 3 FAIL) at seed=42 | **reproducible** — `results.json` committed; not data-blocked |
| [`experiments/estimator_coverage/`](experiments/estimator_coverage/) | 27-cell empirical coverage simulation for the paired-bootstrap estimator across percentile / BCa / DeLong CI variants; backs the estimator-default decision in `theory/proofs/estimator.md` | **reproducible** — `results.json` committed; ~35 min wall time at seed = 42 |
| [`pwm_dose_equivalence/`](pwm_dose_equivalence/) | Pip-installable Python library; the productionised counterpart to the experiments-folder prototype | **v0.1.0 alpha** — 60/60 tests pass at 100 % line coverage; TestPyPI publish pending (D9 + 365); v1.0.0 alongside paper acceptance (D9 + 540) |
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

- [`paper_draft/CHANGELOG.md`](paper_draft/CHANGELOG.md) — v0.1 → v0.2 → v0.3 deltas with one row per closed audit item / triggered edit and its commit; the manifest for the reviewer-readiness pass + the D9 + 13 / D9 + 14 propagation passes.
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
- [`experiments/estimator_coverage/`](experiments/estimator_coverage/) — 27-cell coverage simulation across (AUC × n × CI variant); backs the `theory/proofs/estimator.md` decision.
- [`pwm_dose_equivalence/`](pwm_dose_equivalence/) — pip-installable v0.1.0 alpha library. Modality-agnostic `signal_equivalence_credential` + percentile / DeLong estimators + sample-size pre-flight + content-addressed framework hash + Tr_ct/Tr_mri/Tr_pet operators. 60/60 tests, 100 % line coverage.

**Sibling workstreams:**

- [`../WS-1_dataset/`](../WS-1_dataset/) — provides the CT validation data and the **annotation QA protocol** that WS-2's Methods → Estimator section borrows verbatim for ground-truth provenance.
- [`../WS-3_reference_method/`](../WS-3_reference_method/) — Phase 1 pilot consumes WS-3 baselines as `M_ref` candidates; each WS-3 release must publish under a 5-tuple credential issued via this framework.
- [`../WS-4_leaderboard/`](../WS-4_leaderboard/) — every leaderboard submission is verified by recomputing the credential against the content-addressed framework hash. The manuscript's end-to-end case study points at WS-4 as the acceptance-test community.

**PWM integration:**

- [`../pwm_integration/l2_spec.md`](../pwm_integration/l2_spec.md) — public-registry resolver for the SHA-256 hash of the framework definition. One of three resolvers (local file / PyPI release / PWM registry) the manuscript enumerates; the registry is a deployment option for long-term decentralized resolution, not the methodological substance of the credential schema.
