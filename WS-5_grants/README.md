# WS-5 — NIH Grants (Track 9 sub-track 9e)

External NIH funding that backfills Reserve burn, validates that the protocol's research wins federal funding, and seeds a long-term R01 trajectory.

**No paper deliverable** in this workstream — the deliverable is a *funded grant*. (WS-5 still participates in the L2/L3/L4 ecosystem by citing those artifacts in the Specific Aims.)

---

## Goals

1. **R21 submitted on time** at D9 + 365 (first available NIH cycle: Jun 16, 2027 or Oct 16, 2027).
2. **R21 funded** at D9 + 730 (stretch — base rate ~25% per submission; expect 2-3 cycles).
3. **R01 LOI submitted** at D9 + 900 (after R21 funded AND faculty appointment confirmed).

A successful WS-5 means: $275K direct over 2 years arrives via R21, backfilling ~50% of Phase 2+3 burn for the rest of Track 9. Long-term: R01 PI status post-faculty-appointment establishes funded-PI track record.

---

## Hard constraint — PI eligibility

NIH R-series requires PI eligibility. The current Track 9 lead is a **Research Associate at UTSW**, not yet PI-eligible. This means:

- **R21:** New UTSW PI (Track K) = PI; Track 9 lead = Co-I.
- **R01:** Track 9 lead = PI only after faculty appointment (target Q1 2028+).

**Track K (new UTSW PI confirmed) is a hard dependency** for the R21 submission cycle. If Track K slips past D9 + 270, the R21 submission slips by at least one NIH cycle (~4 months).

---

## Target institutes

| Institute | Why |
|---|---|
| **NIBIB** | Bioengineering — primary fit for reconstruction methodology |
| **NCI** | Cancer — lung-cancer screening is the central downstream task |
| **NHLBI** | Heart, lung, blood — chest CT for cardiopulmonary screening |

LOI may be submitted to multiple institutes; pick primary based on which study section best matches the Specific Aims (likely BMIT-A or equivalent imaging study section).

---

## Tasks

### Phase 1 — Pre-LOI prep (D9 + 180 → D9 + 270)

| # | Task | Output |
|---|---|---|
| 1.1 | Confirm Track K status — is new UTSW PI on board? | Yes / no decision |
| 1.2 | Draft Specific Aims around WS-1 (dataset) + WS-2 (framework); circulate to mentors for pre-review | Aims v1 |
| 1.3 | Identify target institute + study section | Decision recorded |
| 1.4 | Budget sketch — confirm ~$275K direct fits R21 budget cap; pre-award office consulted | Budget v1 |
| 1.5 | Biosketch refresh; CV-relevant papers in pipeline | Updated biosketches |
| 1.6 | PWM / UTSW IP and conflict-of-interest disclosure filed | COI clearance |

### Phase 2 — R21 LOI + full submission (D9 + 270 → D9 + 365)

| # | Task | Output |
|---|---|---|
| 2.1 | R21 LOI submitted (typically required ~30 days before full app) | LOI receipt |
| 2.2 | Specific Aims v2 — incorporate mentor feedback; sharpen significance + innovation | Aims v2 |
| 2.3 | Research Strategy (Significance, Innovation, Approach) drafted | Strategy v1 |
| 2.4 | Letters of support from collaborators (WS-1 partner sites, radiologists) | Letters in hand |
| 2.5 | Pre-award office review; institutional sign-offs | Routing complete |
| 2.6 | **R21 full application submitted** at next NIH cycle (Jun 16 or Oct 16, 2027) | Submission confirmation |

### Phase 3 — Review + revision (D9 + 365 → D9 + 730)

| # | Task | Output |
|---|---|---|
| 3.1 | Study section review (~4 mo standard cycle) | Summary statement |
| 3.2 | If scored in fundable range: respond to JIT requests; await funding decision | NoA (Notice of Award) |
| 3.3 | If not funded: revise per reviewer comments; resubmit next cycle (standard 2-3-cycle path) | Revised submission |

### Phase 4 — R01 planning (D9 + 730+, contingent on R21 + faculty offer)

| # | Task | Output |
|---|---|---|
| 4.1 | If R21 funded AND faculty offer landed: R01 outline (PI-as-self) | R01 outline |
| 4.2 | R01 LOI submitted | LOI receipt |
| 4.3 | R01 full submission | Submission confirmation |

---

## Timeline (D9-anchored)

| Date | Milestone | Status |
|---|---|---|
| D9 + 180 | Pre-LOI work starts; Specific Aims v1 | pending |
| D9 + 270 | **R21 LOI submitted; aims locked** | pending |
| D9 + 365 | **R21 full application submitted (first NIH cycle)** | pending |
| D9 + 540 | Study section review (summary statement received) | pending |
| D9 + 730 | **R21 funded (stretch — base-rate scenario)** | pending |
| D9 + 730+ | R01 LOI prep (contingent on R21 + faculty offer) | pending |
| D9 + 900 | R01 LOI submitted | pending |

---

## Done when

- [ ] R21 LOI submitted on time at D9 + 270
- [ ] R21 full application submitted at D9 + 365
- [ ] R21 funded (may require 2-3 cycles — standard NIH base rate)
- [ ] R01 LOI submitted post-faculty-appointment

---

## Specific Aims sketch (R21)

To be refined at D9 + 270; current direction:

**Aim 1.** Construct and release a multi-vendor paired-dose CT benchmark dataset on PhysioNet. *(WS-1 deliverable; cite L3 spec on PWMRegistry.)*

**Aim 2.** Develop and validate a probabilistic signal-equivalence framework for low-dose CT reconstruction methods, generalizing to MRI accelerated reconstruction and PET low-activity scans. *(WS-2 deliverable; cite L2 spec on PWMRegistry.)*

**(Aim 3 — stretch, may not fit R21 budget):** Develop a reference reconstruction method with uncertainty quantification and demonstrate cross-vendor generalization. *(WS-3 deliverable; cite L4 cert on PWMRegistry.)*

The PWM on-chain citations in the Aims are not decorative — they are the reviewer's *verifiable* evidence that the preliminary work exists, is reproducible, and is publicly available. This is a structural advantage few R21 applications have.

---

## Subfolders (created on demand)

| Path | Purpose | Status |
|---|---|---|
| `r21_loi/` | LOI draft + mentor comments + Specific Aims sketches | pending Phase 2 |
| `r21_full/` | Full R21 application package | pending Phase 2 |
| `study_section/` | Reviewer comments + revision tracking | pending Phase 3 |
| `r01_planning/` | R01 outline contingent on R21 funding + faculty offer | pending Phase 4 |

---

## Critical-path checks before R21 submission

- [ ] Track K complete: new UTSW PI confirmed and on board as PI
- [ ] WS-1 has tangible early results (Phase 1 baselines + draft dataset paper)
- [ ] WS-2 has at least a Phase 1 pilot demonstrating the framework is implementable
- [ ] Budget approved by UTSW pre-award office
- [ ] PWM / UTSW IP and conflict-of-interest disclosure filed and cleared
- [ ] Biosketches refreshed; CV-relevant papers visible (WS-1 + WS-2 in submission)

---

## Risk: R21 not funded first cycle

Base rate is ~25% funding probability per submission. Standard mitigation: resubmit on next cycle with reviewer-comment response. **Not a failure mode** — the typical R21 path is 2-3 cycles. Continue Track 9 work on Reserve funding until grant lands.

---

## Cross-references

- [`../WS-1_dataset/`](../WS-1_dataset/) — Specific Aim 1 deliverable
- [`../WS-2_framework/`](../WS-2_framework/) — Specific Aim 2 deliverable
- [`../WS-3_reference_method/`](../WS-3_reference_method/) — stretch Aim 3
- [`../pwm_integration/`](../pwm_integration/) — on-chain artifacts cited in the Aims as verifiable preliminary work
