# `WS-3_reference_method/paper_draft/` — MICCAI 2027 manuscript

**Target venue:** MICCAI 2027 (Lecture Notes in Computer Science) — primary.
**Fallback:** *IEEE Transactions on Medical Imaging* (longer page budget, more space for ablations).
**Status:** v0.1 working draft.

## Page budget

MICCAI: **8 pages** main + **up to 4 pages supplementary**. Current draft is close to 8 pages in LNCS format; if it overflows, the candidate trims are (a) move ablation table to supplement, (b) compress cross-vendor section to a single figure.

## Files

| File | Purpose |
|---|---|
| `manuscript.tex` | Main manuscript |
| `refs.bib` | Bibliography |
| `figures/` (later) | Architecture diagram + reliability calibration plot + example reconstructions |

## Build

```
pdflatex manuscript && bibtex manuscript && pdflatex manuscript && pdflatex manuscript
```

To switch to real LNCS template at submission:
```
\documentclass[runningheads]{llncs}
```
(Download `llncs.cls` from Springer; `splncs04.bst` for the bibliography style.)

## What's complete

- **Abstract** — full prose, ~250 words.
- **Introduction** — three structural problems with current low-dose CT method papers + architecture rationale (3 reasons for unrolled iterative) + the "top-25% with all four properties" goal.
- **Method** — full architecture spec: forward model (reusing `pwm_core`), unrolled iteration algorithm with pseudocode, deep ensembles for UQ, training data + augmentation.
- **Experiments section** — dataset list, baseline list, cross-vendor splits, metrics list (5 categories).
- **Conclusion** — Apache 2.0 release + leaderboard seed + invitation for community improvement.

## What's placeholder

- Table 1 (PSNR/SSIM at 3 dose levels for 5 methods) — fill at D9+270 after v1 training
- Table 2 (cross-vendor PSNR drops) — fill after cross-vendor experiments
- Table 3 (downstream task AUC) — fill after lung-nodule detector evaluation
- Table 4 (5-tuple credentials) — fill after WS-2 library validates on this method
- Figure: reliability diagram for ensemble UQ calibration
- Figure: architecture diagram
- Figure: example reconstructions at three dose levels (visual comparison)
- Ablation: K iterations sensitivity
- Diffusion baseline selection (CTformer / Restormer-LDCT / etc.)
- Transformer baseline selection

## Submission notes

MICCAI is double-blind. Author affiliations and any identifying acknowledgments
must be redacted in the submission version. The draft as written reveals
the PWM Protocol Foundation; that has to be anonymized at submission and
re-added at camera-ready.

The MICCAI reviewer pool is heavily methodological — they will scrutinize:
- Whether the unrolled iterative architecture is genuinely novel or a re-derivation
  (it isn't novel; the contribution is the *reference role* + UQ calibration +
  cross-vendor + open release, not the architecture per se — the abstract and
  intro make this explicit)
- Whether the deep ensemble is justified vs cheaper UQ (we cite Ovadia 2019)
- Whether cross-vendor evaluation is methodologically sound (leave-one-vendor-out
  with patient-level split, not slice-level)

## Why MICCAI over IEEE TMI

MICCAI's reviewer pool moves faster (5-6 month cycle vs 9-12 for TMI), the
conference has a dedicated low-dose CT track historically, and a MICCAI paper
that wins a Young Scientist Award or Best Paper drops a stronger faculty-CV
line than a TMI paper. The downside is the 8-page limit. If the cross-vendor
section needs more space than the supplementary can hold, route to TMI instead.

## Dependencies on other workstreams

- Trains and evaluates on [`../../WS-1_dataset/`](../../WS-1_dataset/)
- Credentials computed via [`../../WS-2_framework/`](../../WS-2_framework/) library
- Becomes the seed entry in [`../../WS-4_leaderboard/`](../../WS-4_leaderboard/)
- L4 cert anchored at [`../../pwm_integration/l4_cert.md`](../../pwm_integration/l4_cert.md)
