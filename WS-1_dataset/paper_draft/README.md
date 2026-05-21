# `WS-1_dataset/paper_draft/` — Nature Scientific Data manuscript

**Target venue:** *Nature Scientific Data* (Data Descriptor format) — primary.
**Fallback:** *Radiology: Artificial Intelligence* (clinical-AI scope).
**Status:** v0.1 working draft. Builds; `\todo{}` markers flag every placeholder for numbers / counts / figures that depend on Phase 1-3 dataset construction.

## Files

| File | Purpose |
|---|---|
| `manuscript.tex` | Main manuscript, ~3500 words of substantive prose + placeholders |
| `refs.bib` | Bibliography (BibTeX) |
| `figures/` (later) | Figure PDFs; create as Phase 1 baselines + validation lands |

## Build

```
pdflatex manuscript
bibtex   manuscript
pdflatex manuscript
pdflatex manuscript
```

(Two `pdflatex` passes after `bibtex` to resolve all cross-references.)

## What's complete vs placeholder

**Complete (real prose, ready to submit pending edits):**

- Abstract scaffold
- Background & Summary (three structural problems framing, dataset positioning)
- Methods: acquisition protocol, low-dose simulation (with calibrated Poisson formula citing forward model), reconstruction triple (FBP / vendor IR / TV), annotation protocol, de-identification, splits
- Usage Notes: loader API, baseline reproduction recipe, leaderboard submission pointer, cross-vendor evaluation API
- Code Availability section with stable URLs
- Reference list

**Placeholder (`\todo{}` markers) — fill as data lands:**

- Patient counts per vendor / site / split (Phase 2)
- Real-vs-simulated low-dose discrepancy figure (Phase 1 + Phase 2 paired-acquisition data)
- Inter-rater agreement metrics (Phase 2 annotation campaign)
- Baseline reproduction performance table (after WS-3 Phase 1 baselines reproduce)
- 5-tuple credential summary table (after WS-2 Phase 1 pilot)
- IRB protocol number (Phase 1 IRB submission)
- Collection start / end dates
- PhysioNet URL (Phase 3 listing)
- L3 spec contract address (Phase 3 on-chain registration)

## What this draft does NOT yet contain (intentional)

- Specific figure files. Figures should be generated from real data using
  the comparison harness `WS-3_reference_method/baselines/comparison/`.
- Concrete vendor names beyond placeholders. The two-vendor minimum is
  enforced by inclusion criteria; we name actual vendors only after
  Phase 2 site commitments lock.
- Concrete radiologist names. Authorship is filled at submission.

## Submission notes

*Nature Scientific Data* requires the dataset to be deposited on a stable
public repository (PhysioNet here) before submission. The on-chain L3
spec is supplementary; it does not replace the PhysioNet deposit.

The Data Descriptor format is shorter than a typical research paper:
~3500-5000 words total, with the heaviest weight on Methods + Technical
Validation. Avoid speculative prose; reviewers look for replicability.
