# WS-2 — Signal-Equivalence Framework (Track 9 sub-track 9b)

The **signal-equivalence framework**: a formal, modality-general mathematical replacement for vendor-style claims like *"50% dose reduction"*, *"4× MRI acceleration"*, or *"25% activity PET"*. Each claim is converted into a testable 5-tuple credential `(signal_ratio, task, ε, α, subpopulation)`.

> **Status (D9 + 12, 2026-06-01):** manuscript at **v0.2 working draft**, 19 pp — see [`paper_draft/CHANGELOG.md`](paper_draft/CHANGELOG.md) for the v0.1 → v0.2 delta. The same code path is verified across CT / MRI / PET on synthetic data ([`experiments/cross_modality_consistency/`](experiments/cross_modality_consistency/), 6/6 verdicts as expected). Real-cohort per-modality Results tables are gated on WS-2 Phase 1 (CT) and Phase 3 (MRI / PET).

---

## Goals

1. **Publish a peer-reviewed paper** at ***Nature Methods*** (primary) introducing the framework. Fallback: *IEEE Transactions on Medical Imaging* or *Medical Image Analysis*. Working draft is at v0.2 in [`paper_draft/`](paper_draft/) — see [`paper_draft/CHANGELOG.md`](paper_draft/CHANGELOG.md) for the v0.1 → v0.2 delta.
2. **Ship `pwm_dose_equivalence` on PyPI** with ≥ 2 modality validators (CT + MRI minimum; PET stretch). `pip install pwm_dose_equivalence` works for any external user. A prototype of the modality-agnostic API ships today in [`experiments/cross_modality_consistency/`](experiments/cross_modality_consistency/); the productionised library is Phase 3 (D9 + 365 TestPyPI → D9 + 540 v1.0.0).
3. **Register the framework definition on PWMRegistry** as a content-addressed L2 specification, so every leaderboard submission is verified against the SHA-256 hash of the framework version the credential was issued under. The PWM registry is one of three hash-resolvers (local file / pinned PyPI release / PWMRegistry) that the manuscript enumerates; content-addressing itself is the methodological substance, the registry is the long-term decentralized resolver.

A successful WS-2 means: an external researcher can compute a 5-tuple credential for their reconstruction method on the L3 dataset in under one hour on commodity hardware, and any reviewer can verify the credential by re-running the same library against the same framework hash.

---

## The framework, in one line

Method **M** is **signal-equivalent at level (r, T, ε, α)** over subpopulation **Π** iff the population-mean task performance on reduced-signal scans is within `ε` of the population-mean performance of a reference method on full-signal scans. The `1 − α` is the confidence level at which the paired-bootstrap estimator returns `PASS` on a test set drawn from Π — population claim and finite-sample evidence are kept distinct (manuscript v0.2 §framework). Π is formalized to carry the **acquisition-protocol metadata** that determines `T_r` for the modality (CT vendor / kVp; MRI mask family; PET tracer / scanner), so the 5-tuple shape holds verbatim across CT, MRI, and PET.

The formal definition lives in [`theory/dose-equivalence-framework.md`](theory/dose-equivalence-framework.md) (v0.1; intentionally lags the manuscript v0.2 pending the literature depth-pass per [`theory/open_questions.md`](theory/open_questions.md) §1). It sharpens the one-liner across six points (patient vs image; operator vs scalar; reference-acquisition vs reference-algorithm; performance functional form; subpopulation-as-acquisition-protocol-bearing measure; aggregate vs per-patient) — the same six points appear in the manuscript as clarifications C1–C6.

---

## Scope: modality-general by construction

| Modality | Signal-reduction parameter `r` | Validator status |
|---|---|---|
| **CT** (primary) | `r = mA_red / mA_ref` (tube-current dose ratio) | Phase 1 pilot validates on AAPM 2016 + LIDC-IDRI |
| **MRI accelerated reconstruction** | `r = 1 / R` (acceleration factor reciprocal) | Phase 2 worked example (fastMRI knee dataset) |
| **PET low-dose / low-activity** | `r = A_red / A_ref` (injected-activity ratio) | Phase 2 worked example (public NEMA IQ phantom) |
| Optical / fluorescence (stretch) | `r = exposure_red / exposure_ref` | v2 extension |

The L2 spec ships when **CT + at least one of {MRI, PET}** have a working validator.

---

## Tasks

### Phase 1 — Phase A pilot (D9 + 60 → D9 + 90)

| # | Task | Output |
|---|---|---|
| 1.1 | Compute the 5-tuple credential for each of the 3 reproduced WS-3 baselines on AAPM 2016 + LIDC-IDRI | `validation/heyang_pilot_5_tuples.json` |
| 1.2 | End-to-end implementability check — does the v0.1 definition survive contact with real data? | Decision: commit to v0.1 or revise before Phase 2 |
| 1.3 | Methodology memo: how the pilot computes the credential | `validation/methodology.md` |
| 1.4 | Known limitations memo | `validation/known_limitations.md` |

### Phase 2 — Theoretical depth (D9 + 150 → D9 + 365)

Per [`theory/open_questions.md`](theory/open_questions.md), 10 items prioritized BLOCK / SHARPEN / DEFER (~8 weeks total). Sequenced:

| # | Open question | Priority | Effort (wk) |
|---|---|---|---|
| 2.1 | §1 Literature pass (related-work memo + positioning) | SHARPEN | 1.5 |
| 2.2 | §3 Estimator validity / coverage simulations | BLOCK | 1.5 |
| 2.3 | §2 Sample-size formula (closed-form + numerical table) | BLOCK | 2.0 |
| 2.4 | §7 MRI mask distribution decision | BLOCK (MRI) | 1.0 |
| 2.5 | §5 Conditional monotonicity-in-r | SHARPEN | 1.0 |
| 2.6 | §8 PET model under list-mode reduction | SHARPEN | 0.5 |
| 2.7 | §6 Per-patient vs aggregate guidance | SHARPEN | 0.5 |
| 2.8 | §4 Composition law (likely negative result) | DEFER | 0.5 |

Phase 2 work runs in parallel with the WS-1 IRB lag — no IRB dependency.

### Phase 3 — Library + multi-modality validation (D9 + 180 → D9 + 365)

| # | Task | Output |
|---|---|---|
| 3.1 | Implement `pwm_dose_equivalence.signal_equivalence_credential()` (CT validator) | Core library + CT example |
| 3.2 | Implement MRI validator (fastMRI knee dataset; variable-density Cartesian masks) | MRI example + integration test |
| 3.3 | Implement PET validator (NEMA IQ phantom; Poisson list-mode thinning) | PET example + integration test |
| 3.4 | Pip-package; publish v0.1 to TestPyPI; gather feedback | TestPyPI listing |
| 3.5 | v1.0.0 release to PyPI alongside paper acceptance | PyPI listing |
| 3.6 | Outreach to ≥ 3 external research groups to validate the library on their methods | Usage testimonials |

### Phase 4 — Paper + on-chain (D9 + 270 → D9 + 540)

| # | Task | Output |
|---|---|---|
| 4.1 | Draft manuscript (intro, framework definition, theory, validators, three worked examples, discussion) | Draft v1 |
| 4.2 | Submit to *Nature Methods*; respond to reviewer comments (~6 mo) | Acceptance letter |
| 4.3 | Author and register L2 spec on PWMRegistry (concurrent with submission) | L2 hash on chain |

---

## Timeline (D9-anchored)

D9 anchor ≈ 2026-05-20 (theory v0.1 seed date); today (2026-06-01) is **≈ D9 + 12**. Several pre-empirical milestones originally scheduled for D9 + 150 and D9 + 270 landed ahead of schedule via the v0.2 reviewer-readiness pass.

| Date | Milestone | Status |
|---|---|---|
| **D9 + 12 (2026-06-01)** | **Manuscript v0.2 reviewer-readiness pass landed** — 7 pure-text edits closing 6 audit items + 1 synthetic experiment; 19 pp; credential JSON `schema_version` bumped to v0.2. See [`paper_draft/CHANGELOG.md`](paper_draft/CHANGELOG.md). | **done** |
| D9 + 12 (2026-06-01) | [`experiments/cross_modality_consistency/`](experiments/cross_modality_consistency/) — seed-reproducible 6-credential demonstration (3 modalities × 2 candidates) that the same code path produces 3 expected PASS + 3 expected FAIL verdicts. | **done** |
| D9 + 12 (2026-06-01) | [`theory/related_work.md`](theory/related_work.md) seeded — 3 new TB-IQ anchor cites (Barrett 1990; Barrett & Myers 2013; AAPM TG-233) on top of the 2 pre-existing statistical cites (Schuirmann; Piaggio), plus a "what is genuinely new" novelty-gate skeleton. Manuscript intro carries the TB-IQ positioning paragraph. | **seeded** (depth-pass pending) |
| D9 + 90 | Phase 1 pilot 5-tuples computed on real cohorts (CT) — fills `Results` Table 2 (`\todo` placeholder until then). | pending |
| D9 + 150 | Literature pass **depth-read** complete (fastMRI reader studies; one CHO-for-low-dose-CT paper; Wunderlich/Noo observer-variance) → `theory/dose-equivalence-framework.md` bumped from v0.1 to v0.2 with the [SHARPEN-N] points reconciled against the manuscript v0.2. | pending |
| D9 + 240 | Estimator validity coverage simulations (open_questions §3) + closed-form sample-size formula (open_questions §2) landed under `theory/proofs/`. | pending |
| D9 + 270 | MRI worked-example data wrangling for the Results Table 3 fill; theory-side [`proofs/mri_mask.md`](theory/) decision recorded (manuscript-side already closed at D9 + 12 via the Π-as-acquisition-metadata convention). | partial |
| D9 + 270 | PET worked-example data wrangling for Results Table 4 fill (NEMA NU-2 IQ phantom at multiple activity levels). | pending |
| D9 + 365 | **Paper submitted to *Nature Methods*; L2 spec on PWMRegistry; `pwm_dose_equivalence` v0.1 on TestPyPI**. | pending |
| D9 + 540 | **Paper accepted; library v1.0.0 on PyPI; ≥ 3 external groups using it.** | pending |

---

## Done when

### v0.2 progress at D9 + 12 (intermediate, not terminal)

- [x] Manuscript v0.2 reviewer-readiness pass — 7 audit items closed (see [`paper_draft/CHANGELOG.md`](paper_draft/CHANGELOG.md))
- [x] Cross-modality consistency synthetic anchor — same code path, 6 expected verdicts, seed-reproducible (`experiments/cross_modality_consistency/`)
- [x] Task-based image-quality positioning + [`theory/related_work.md`](theory/related_work.md) seeded with 3 new TB-IQ anchor cites (Barrett 1990 / Barrett & Myers 2013 / AAPM TG-233)
- [x] Ground-truth protocol borrowed verbatim from WS-1 v0.5 annotation QA into `Methods → Estimator`
- [x] Π formalized as carrying acquisition-protocol metadata (CT vendor / MRI mask family / PET tracer); 5-tuple shape preserved across modalities
- [ ] Literature depth-pass complete (fastMRI reader studies / one CHO-for-LDCT paper / Wunderlich–Noo observer-variance) → `theory/dose-equivalence-framework.md` bumped from v0.1 to v0.2
- [ ] Coverage simulations (open_questions §3) + closed-form sample-size derivation (open_questions §2) landed under `theory/proofs/`

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
| [`paper_draft/`](paper_draft/) | *Nature Methods* manuscript | **v0.2 working draft** (19 pp; see [`paper_draft/CHANGELOG.md`](paper_draft/CHANGELOG.md)) |
| [`theory/`](theory/) | Formal definition ([`dose-equivalence-framework.md`](theory/dose-equivalence-framework.md)), open-questions work plan ([`open_questions.md`](theory/open_questions.md)), related-work memo ([`related_work.md`](theory/related_work.md)); (later) `proofs/` for sample-size and coverage derivations | **v0.1 seeded** — 3 files in place; depth-pass pending |
| [`experiments/cross_modality_consistency/`](experiments/cross_modality_consistency/) | Synthetic anchor for the modality-general claim — same bootstrap code path applied to 3 `T_r` operators; 6 credentials (3 PASS + 3 FAIL) at seed=42 | **reproducible** — `results.json` committed; not data-blocked |
| `validation/` | Per-modality empirical 5-tuple computation on **real patient cohorts** (CT first, then MRI / PET). Distinct from `experiments/`, which is synthetic. | pending Phase 1 pilot (D9 + 90) |
| `pwm_dose_equivalence/` | Pip-installable Python library; the productionised counterpart to the experiments-folder prototype. | pending Phase 3 (D9 + 365 TestPyPI; D9 + 540 v1.0.0) |

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

**Inside WS-2:**

- [`paper_draft/CHANGELOG.md`](paper_draft/CHANGELOG.md) — v0.1 → v0.2 delta with one row per closed audit item and its commit; the manifest for the reviewer-readiness pass.
- [`theory/dose-equivalence-framework.md`](theory/dose-equivalence-framework.md) — formal definition v0.1. Intentionally lags the manuscript v0.2; its own header says it is superseded by v0.2 after the literature pass (see `open_questions.md` §1).
- [`theory/open_questions.md`](theory/open_questions.md) — BLOCK / SHARPEN / DEFER work plan for Phase 2 theory; the §-numbering is cross-referenced from `related_work.md` and from this README's `Phase 2` task table above.
- [`theory/related_work.md`](theory/related_work.md) — 5-paper memo (2 statistical + 3 TB-IQ anchor cites) seeded alongside the manuscript A6 positioning paragraph. Hosts the "what is genuinely new" novelty gate for the theory-doc v0.2 bump.
- [`experiments/cross_modality_consistency/`](experiments/cross_modality_consistency/) — synthetic anchor for the modality-general claim; ships seed-reproducible `results.json` and is cited from the manuscript's Cross-modality consistency Results subsection.

**Sibling workstreams:**

- [`../WS-1_dataset/`](../WS-1_dataset/) — provides the CT validation data and the **annotation QA protocol** that WS-2's Methods → Estimator section borrows verbatim for ground-truth provenance.
- [`../WS-3_reference_method/`](../WS-3_reference_method/) — Phase 1 pilot consumes WS-3 baselines as `M_ref` candidates; each WS-3 release must publish under a 5-tuple credential issued via this framework.
- [`../WS-4_leaderboard/`](../WS-4_leaderboard/) — every leaderboard submission is verified by recomputing the credential against the content-addressed framework hash. The manuscript's end-to-end case study points at WS-4 as the acceptance-test community.

**PWM integration:**

- [`../pwm_integration/l2_spec.md`](../pwm_integration/l2_spec.md) — public-registry resolver for the SHA-256 hash of the framework definition. One of three resolvers (local file / PyPI release / PWM registry) the manuscript enumerates; the registry is a deployment option for long-term decentralized resolution, not the methodological substance of the credential schema.
