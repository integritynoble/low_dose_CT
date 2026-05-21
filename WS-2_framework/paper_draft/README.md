# `WS-2_framework/paper_draft/` — Nature Methods manuscript

**Target venue:** *Nature Methods* — primary.
**Fallback:** *IEEE Transactions on Medical Imaging* / *Medical Image Analysis*.
**Status:** v0.1 working draft.

## Files

| File | Purpose |
|---|---|
| `manuscript.tex` | Main manuscript (~5500 words of substantive prose) |
| `refs.bib` | Bibliography |
| `figures/` (later) | Figures (cross-modality consistency, coverage plot, worked example tables as figures) |

## Build

```
pdflatex manuscript && bibtex manuscript && pdflatex manuscript && pdflatex manuscript
```

## What's complete

Most of the *intellectual* content is in:

- **Abstract** — the framework, motivation, contributions, claim.
- **Introduction** — three failures of current reporting (undefined task / subpopulation / statistics), framework positioning, contributions list.
- **Results** — framework overview + three worked-example sections (CT / MRI / PET) with API code snippet showing cross-modality consistency.
- **Discussion** — three implications (reviewer / regulatory / agent practice), limitations.
- **Methods** — full Section 4:
  - 4.1 The framework, formally — Definition 1 (aggregate) + Definition 2 (per-patient), with modality-specific $T_r$ table.
  - 4.2 Six type-signature clarifications (C1-C6) — the "SHARPEN" points from [`../theory/dose-equivalence-framework.md`](../theory/dose-equivalence-framework.md).
  - 4.3 Estimator — paired bootstrap + sample-size formula + BCa option for AUC-boundary regime.
  - 4.4 Open-source library — single-call API signature.
  - 4.5 Cryptographic anchoring — PWM L2 registry, benchmark-drift attack class eliminated.

## What's placeholder

- Table 2 (CT results) — fill at D9+90 after WS-2 Phase 1 pilot
- Table 3 (MRI results) — fill at D9+270 after WS-2 Phase 3 MRI validator
- Table 4 (PET results) — fill after WS-2 Phase 3 PET validator
- Figure: cross-modality coverage plot — generate from library coverage sims
- Figure: type-signature clarifications visual — optional
- Supplementary Bernstein-correction derivation
- Author list / CRediT / acknowledgments

## Submission notes

*Nature Methods* word limits (approximate):
- Abstract: 200 words (current draft is ~280 — needs trimming)
- Main text (intro + results + discussion): ~3000 words
- Methods: unlimited but typically 2000-3500
- References: capped at 40 in main text

Current draft is at the upper end. Trim opportunities: (a) the type-signature clarifications can move to Methods supplement; (b) one worked example can be moved to supplement.

The framework definition (Definition 1) is the load-bearing artifact. Reviewers will scrutinize:
- Whether the paired bootstrap is the right estimator (Section 4.3)
- Whether the modality-general $T_r$ formulation is genuinely general (Table 1)
- Whether the cross-modality library API call signature really preserves shape across modalities (Section 4.4 + Results "Cross-modality consistency")

## Dependencies on other workstreams

- The CT worked example consumes [`../../WS-1_dataset/`](../../WS-1_dataset/).
- The CT reference method used as $\Mref$ in the worked example is [`../../WS-3_reference_method/`](../../WS-3_reference_method/) v1.
- The L2 spec frozen at submission lives in [`../../pwm_integration/l2_spec.md`](../../pwm_integration/l2_spec.md).

## Why this paper goes to Nature Methods, not IEEE TMI

The framework is a *methodological contribution* — a reporting standard, not a CT reconstruction method. Nature Methods publishes methodological frameworks intended for adoption across multiple modalities (e.g., Cell Painting, STAR-FISH protocols). A CT-only equivalence framework belongs in IEEE TMI; the modality-general framing makes it Nature Methods.
