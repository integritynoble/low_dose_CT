# `WS-2_framework/paper_draft/` — Nature Methods manuscript

**Target venue:** *Nature Methods* — primary.
**Fallback:** *IEEE Transactions on Medical Imaging* / *Medical Image Analysis*.
**Status:** v0.2 working draft. See [`CHANGELOG.md`](CHANGELOG.md) for the v0.1 → v0.2 delta.

## Files

| File | Purpose |
|---|---|
| `manuscript.tex` | Main manuscript (~6500 words of substantive prose, 19-page draft) |
| `refs.bib` | Bibliography (23 entries) |
| [`CHANGELOG.md`](CHANGELOG.md) | v0.1 → v0.2 delta — landed edits and what is still gated on data |
| `figures/` (later) | Figures (cross-modality consistency, coverage plot, worked example tables as figures) |

## Build

```
pdflatex manuscript && bibtex manuscript && pdflatex manuscript && pdflatex manuscript
```

## What's complete

Most of the *intellectual* content is in:

- **Abstract** — four-beat (problem / framework / library + worked examples / implications) without literal headings.
- **Introduction** — three failures of current reporting (undefined task / subpopulation / statistics); positioning vs TOST/CONSORT; positioning vs task-based image-quality assessment (Barrett 1990; Barrett & Myers 2013; AAPM TG-233); four separable contributions.
- **Results** — framework overview + three worked-example sections (CT / MRI / PET) + the cross-modality consistency synthetic experiment with real numbers + tool-coverage comparison + end-to-end case study.
- **Discussion** — three implications (reviewer / regulatory / agent practice), failure modes with the out-of-scope claims reframed as point-evaluated-by-design.
- **Methods** — full Section 4:
  - 4.1 The framework, formally — Definition 1 (aggregate) + Definition 2 (per-patient), with $\Pi$ explicitly carrying acquisition-protocol metadata so the 5-tuple shape survives modality transitions; modality-specific $T_r$ table.
  - 4.2 Six type-signature clarifications (C1-C6) — the "SHARPEN" points from [`../theory/dose-equivalence-framework.md`](../theory/dose-equivalence-framework.md).
  - 4.3 Estimator — ground-truth protocol borrowed from WS-1 v0.5; label-noise refusal threshold; population-claim-vs-sample-evidence separation; paired bootstrap + sample-size formula + BCa option for AUC-boundary regime.
  - 4.4 Open-source library — single-call API signature.
  - 4.5 Content-addressed credential schema — SHA-256 hash of framework definition; three resolver backends (local / PyPI / PWM registry); the on-chain registry is a deployment option, not the methodological substance.

## What's placeholder

- Per-modality Results tables (CT / MRI / PET on real cohorts) — gated on WS-2 Phase 1 pilot (CT, D9+90) and Phase 3 validators (MRI / PET, D9+270 → D9+365). The cross-modality consistency table (synthetic, six credentials) is real and lives in [`../experiments/cross_modality_consistency/`](../experiments/cross_modality_consistency/).
- Figure: cross-modality coverage plot — generate from library coverage sims (open_questions §3)
- Figure: type-signature clarifications visual — optional
- Software-rigor counts (`$N_{\textrm{tests}}$`, coverage %) — gated on Phase 3 `pwm_dose_equivalence` v0.1 ship
- Supplementary Bernstein-correction derivation (open_questions §2)
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
