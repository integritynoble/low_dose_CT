# WS-2 — Signal-Equivalence Framework (Track 9 sub-track 9b)

The **signal-equivalence framework**: a formal, modality-general mathematical replacement for vendor-style claims like *"50% dose reduction"*, *"4× MRI acceleration"*, or *"25% activity PET"*. Each claim is converted into a testable 5-tuple credential `(signal_ratio, task, ε, α, subpopulation)`.

---

## Goals

1. **Publish a peer-reviewed paper** at ***Nature Methods*** (primary) introducing the framework. Fallback: *IEEE Transactions on Medical Imaging* or *Medical Image Analysis*.
2. **Ship `pwm_dose_equivalence` on PyPI** with ≥ 2 modality validators (CT + MRI minimum; PET stretch). `pip install pwm_dose_equivalence` works for any external user.
3. **Register L2 spec on PWMRegistry** so every leaderboard submission must report a 5-tuple credential under a cryptographically-anchored framework version.

A successful WS-2 means: an external researcher can compute a 5-tuple credential for their reconstruction method on the L3 dataset in under one hour on commodity hardware, and any reviewer can verify the credential by re-running the same library.

---

## The framework, in one line

Method **M** is **signal-equivalent at level (r, T, ε, α)** over subpopulation **Π** iff the population-mean task performance on reduced-signal scans is within `ε` of the population-mean performance of a reference method on full-signal scans, with confidence `≥ 1 − α`.

The formal definition lives in [`theory/dose-equivalence-framework.md`](theory/dose-equivalence-framework.md) (v0.1 working draft). It sharpens the one-liner across six points (patient vs image, operator vs scalar, reference-acquisition vs reference-algorithm, performance functional form, subpopulation-as-measure, aggregate vs per-patient).

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

| Date | Milestone | Status |
|---|---|---|
| D9 + 90 | Phase 1 pilot 5-tuples computed; framework definition committed (or revised) | pending |
| D9 + 150 | Literature pass complete; v0.2 framework draft published; theory work in flight | pending |
| D9 + 240 | Estimator validity + sample-size formula proofs landed | pending |
| D9 + 270 | MRI mask decision finalized; manuscript draft outlined | pending |
| D9 + 365 | **Paper submitted to *Nature Methods*; L2 spec on chain; `pwm_dose_equivalence` v0.1 on TestPyPI** | pending |
| D9 + 540 | **Paper accepted; library v1.0.0 on PyPI; ≥ 3 external groups using it** | pending |

---

## Done when

- [ ] *Nature Methods* paper accepted (or fallback venue)
- [ ] `pwm_dose_equivalence` v1.0.0 on PyPI with ≥ 2 modality validators
- [ ] L2 spec hash on PWM mainnet
- [ ] ≥ 3 external groups have computed a credential under the framework
- [ ] Phase 1 pilot data published as supplementary

---

## Subfolders

| Path | Purpose | Status |
|---|---|---|
| [`theory/`](theory/) | Formal definition + open-questions work plan + (later) proofs | **v0.1 seeded** |
| [`experiments/cross_modality_consistency/`](experiments/cross_modality_consistency/) | Synthetic anchor for the modality-general claim — same bootstrap code path, 3 `T_r` operators, 3 PASS + 3 FAIL credentials | **seed-reproducible** |
| `pwm_dose_equivalence/` | Pip-installable Python library | pending Phase 3 |
| `validation/` | Empirical 5-tuple computation on real data | pending Phase 1 pilot |
| [`paper_draft/`](paper_draft/) | *Nature Methods* manuscript | **v0.2 working draft** (19 pp; see [`paper_draft/CHANGELOG.md`](paper_draft/CHANGELOG.md)) |

---

## Why generalize beyond CT

| Reason | Detail |
|---|---|
| **Venue bar** | *Nature Methods* publishes general methodological frameworks. A CT-only framework is *IEEE TMI* material. CT + MRI + PET is the *Nature Methods* story. |
| **Theoretical cost is low** | The formal definition in [`theory/dose-equivalence-framework.md`](theory/dose-equivalence-framework.md) is signal-reduction-agnostic by construction. Validation on MRI / PET requires one worked example each, not new theory. |
| **Citation surface** | A modality-general framework gets cited by MRI groups and PET groups, not just CT. Cross-modality citations compound the WS-2 paper's reach. |

---

## Cross-references

- [`theory/dose-equivalence-framework.md`](theory/dose-equivalence-framework.md) — formal definition v0.1
- [`theory/open_questions.md`](theory/open_questions.md) — work plan for Phase 2 theory
- [`../WS-1_dataset/`](../WS-1_dataset/) — provides the CT validation data
- [`../WS-3_reference_method/`](../WS-3_reference_method/) — Phase 1 pilot consumes WS-3 baselines
- [`../pwm_integration/l2_spec.md`](../pwm_integration/l2_spec.md) — on-chain spec (will hash a frozen `dose-equivalence-framework.md` at submission)
