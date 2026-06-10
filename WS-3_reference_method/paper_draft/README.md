# `WS-3_reference_method/paper_draft/` — *Scientific Data* Data Descriptor

**Target venue:** *Scientific Data* (Nature Portfolio) — **Data Descriptor** — primary.
**Status:** v0.3 working draft (reframed 2026-06-10 from the prior MICCAI method draft).

## Why the venue changed (and what the paper now is)

*Scientific Data* publishes **Data Descriptors**: the reviewed object must be a
released, reusable **dataset**, not an algorithm. The review criteria are
completeness of the data record, technical validation **of the data**, and
reuse potential — not algorithmic novelty or benchmark-beating performance. A
reconstruction-method paper is out of scope and gets desk-rejected.

So WS-3 has been **inverted**: the reconstruction pipeline is demoted to
*"how the data were generated"* (the Methods section), and the contribution is
now a **deposited derived-data corpus**:

> For every WS-1 test scan × dose level (10/25/50/100%) × vendor — a reference
> reconstruction, a per-pixel ensemble **uncertainty** map, the paired per-pixel
> **error** map, a downstream-task **score** map, and a machine-readable
> **signal-equivalence credential**, plus matched reconstructions of five
> baselines.

This is the reconstruction/uncertainty/credential **layer on top of** WS-1's raw
scans, and is deliberately distinct from WS-1 (which releases the raw paired CT).

## Files

| File | Purpose |
|---|---|
| `manuscript.tex` | **Data Descriptor** manuscript (current primary) |
| `manuscript_method_miccai.tex` | Prior MICCAI/TMI **method** draft, preserved as a fallback should the venue strategy change |
| `manuscript.pdf` | Compiled Data Descriptor (8 pp) |
| `refs.bib` | Bibliography |
| `figures/` (later) | Reliability diagram + architecture diagram + example reconstructions |

## Build

```
pdflatex manuscript && bibtex manuscript && pdflatex manuscript && pdflatex manuscript
```

Compiles clean under vanilla `article` (8 pp). At submission, reformat to the
*Scientific Data* LaTeX template (the journal also accepts Word); the section
order below is mandatory and already matches.

## Mandatory *Scientific Data* section order (already in the draft)

1. **Background & Summary** — why the derived-data layer is missing; what the corpus enables.
2. **Methods** — the generating pipeline (unrolled iterative + 5-model deep ensemble + `ct_radon` forward model), framed as data provenance.
3. **Data Records** — file-level manifest, directory tree, formats, per-record fields, counts/sizes, repository DOI.
4. **Technical Validation** — fidelity (PSNR/SSIM/LPIPS), cross-vendor consistency, **uncertainty↔error agreement (Spearman ρ — the central reuse validation)**, downstream-task validity, credential audit, regeneration reproducibility.
5. **Usage Notes** — loading, intended reuses, reuse cautions, licensing.
6. **Code Availability** — Apache-2.0 pipeline + RunBundle/IPFS CID + L4 cert.
   Plus a **Data Citations** list (required).

There is **no** Discussion/Conclusion — that framing signals method-paper scope.

## What's complete

- All six sections written in the mandatory order; abstract rewritten around the data records and reuse.
- Data Records section with a real directory layout, a record-type table, a naming/indexing convention (`scan_id` back-links to WS-1), and a counts/sizes table stub.
- Technical-Validation tables/figures stubbed and wired to the eventual Phase-3 outputs, with the uncertainty↔error Spearman table called out as the load-bearing validation.
- Usage Notes + Code Availability + Data Citations.

## What's placeholder (gated on WS-3 Phase 3, D9+270, + deposit)

- **The corpus itself must be generated and deposited** — every `\todo` in the
  validation tables blocks on real Phase-3 reconstructions/ensembles/cross-vendor
  runs. *Scientific Data will not review a Data Descriptor whose data do not exist.*
- Repository **DOI** (figshare/Zenodo) — fill `\datadoi{}` at deposit; IPFS CID is supplementary, not a substitute.
- Record counts + total sizes (`tab:records_counts`).
- Fidelity / cross-vendor / UQ-calibration / task-AUC / credential tables + reliability figure.
- Baseline selections (transformer / diffusion) finalized and reproduced ≤ 0.5 dB.

## Deposit kit

The deposit checklist and the `dataset_metadata.json` spec live in
[`../deposit/`](../deposit/): `DEPOSIT_CHECKLIST.md` (generate → validate →
package → DOI → fill → submit), `dataset_metadata.schema.json` (JSON Schema for
the corpus root metadata), and `dataset_metadata.example.json` (a validating
template with deposit-time placeholders).

## Submission-readiness gates (hard requirements)

- [ ] Corpus generated on **real** data (not synthetic placeholders) and deposited with a DOI.
- [ ] Data licensed **CC BY 4.0**; confirm WS-1 terms permit redistributing derived reconstructions.
- [ ] `MANIFEST.sha256` + `dataset_metadata.json` present in the deposit.
- [ ] One explicit sentence distinguishing this corpus from WS-1 (already in Background & Summary) so it is not bounced as redundant with the companion WS-1 *Scientific Data* paper.
- [ ] Every credential re-auditable with `pwm-audit` from the deposit.

## Dependencies on other workstreams

- Derived from [`../../WS-1_dataset/`](../../WS-1_dataset/) (raw paired scans; cite as the source dataset)
- Credentials computed via [`../../WS-2_framework/`](../../WS-2_framework/) library (`pwm_dose_equivalence` / `pwm-audit`)
- Reconstructions become reference records for [`../../WS-4_leaderboard/`](../../WS-4_leaderboard/)
- RunBundle anchored at [`../../pwm_integration/l4_cert.md`](../../pwm_integration/l4_cert.md)
