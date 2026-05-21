# `theory/` — WS-2 theoretical work

The canonical home for the **signal-equivalence framework** that anchors WS-2 (Track 9 sub-track 9b). The framework converts vendor-style claims of *"50% dose reduction"* / *"4× MRI acceleration"* / *"25% activity PET"* into testable, comparable, citable 5-tuple credentials `(signal_ratio, task, ε, α, subpopulation)`.

The framework is **modality-general by construction**: the formal definition is signal-reduction-agnostic. CT is the Phase 1 pilot validation; MRI and PET are Phase 2 worked examples for the *Nature Methods* (primary) / *IEEE TMI* (fallback) submission.

---

## Files

| File | Purpose | Status |
|---|---|---|
| [`dose-equivalence-framework.md`](dose-equivalence-framework.md) | Canonical formal definition, glossary, properties, estimator sketch | v0.1 working draft |
| [`open_questions.md`](open_questions.md) | Theoretical gaps that must close before *Nature Methods* submission | v0.1 seeded |
| `related_work.md` (later) | 3-5 papers to skim as part of weeks 1-4 grounding | not started |
| `paper_outline.md` (later) | *Nature Methods* manuscript outline (sections, figure list, page budget) | not started — month 8-9 |
| `proofs/` (later) | Concentration inequalities, sample-size derivations, multi-task extension proofs | not started — month 5-12 |

Files are created on demand. Do not pre-create empty directories.

---

## How this folder connects to the rest of WS-2

- **WS-2 framework paper** is drafted from the artifacts in this folder.
- **L2 cert** on PWMRegistry hashes the final `dose-equivalence-framework.md` (frozen at submission).
- **`pwm_dose_equivalence` Python library** (`../pwm_dose_equivalence/`, later) is the executable counterpart to the definition here.
- **WS-3 reference method** must report a 5-tuple per the definition here — that's the bridge that turns the L4 cert into a *credential against the L2 framework*, not just a number.
- **Phase 1 pilot** (`../validation/`, later) is the empirical sanity check that this definition is implementable end-to-end on real baselines before the team invests in full proofs.

---

## Reading order for a new collaborator

1. [`../README.md`](../README.md) — high-level WS-2 scope (Goals / Tasks / Timeline).
2. [`dose-equivalence-framework.md`](dose-equivalence-framework.md) — the formal definition itself.
3. [`open_questions.md`](open_questions.md) — what's not yet proven; the work plan for Phase B theory time.

---

*Last revised: 2026-05-20.*
