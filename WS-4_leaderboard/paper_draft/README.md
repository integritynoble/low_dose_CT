# `WS-4_leaderboard/paper_draft/` — npj Digital Medicine annual review

**Target venue:** *npj Digital Medicine* (Nature Portfolio, clinical-AI scope) — primary.
**Fallback:** *Medical Image Analysis* (review article track).
**Status:** v0.1 **template** working draft.

## What this draft is

Unlike WS-1/2/3, this draft is **not** an attempt at the actual paper. The
competition that this paper reviews does not exist yet (Year-1 submission
window opens at D9+540 and closes at D9+730). What lives here is the
**manuscript template** that will be cloned each year and re-populated
with that year's submission cohort, trends, and clinical-impact analysis.

The template establishes:
- Section structure (Introduction / The Challenge / Year-N Cohort / Cross-Method Trends / Clinical-Impact Analysis / Open Problems / Next-Year Protocol / Discussion)
- Tone (peer-reviewed review; not marketing)
- Citation conventions (cite every submission from the year covered)
- Recurring elements (architecture-family table; verification statistics; license-posture breakdown; credential-coverage distribution; clinical-impact-by-task-and-subpopulation table; named-open-problems list)

Each year, the team duplicates this manuscript, increments the year number,
swaps in the year's data, and updates the open-problems list per cross-year
trends.

## Files

| File | Purpose |
|---|---|
| `manuscript.tex` | Year-1 template (most numerical content is `\todo{}`) |
| `refs.bib` | Bibliography (will grow each year with citations to every submission) |
| `figures/` (later) | PSNR distribution / task-AUC distribution / credential-coverage figures |

## Build

```
pdflatex manuscript && bibtex manuscript && pdflatex manuscript && pdflatex manuscript
```

## What's complete in the template

- Abstract scaffold
- Introduction (motivation for a recurring annual review; field's structural problems)
- The Challenge section (benchmark + framework + submission protocol + prize structure)
- Section headings for Cohort / Trends / Clinical-Impact / Open Problems / Next-Year Protocol
- Discussion section emphasizing 3 structural properties of the challenge worth replicating in other fields
- Acknowledgments scaffold

## What's placeholder

Essentially all numbers:
- Year-1 submission counts (architecture, institution, country, vendor)
- Verification pass / fail / reject statistics
- License posture breakdown
- PSNR / SSIM / LPIPS distributions
- Task-AUC distribution and PSNR-vs-task-AUC correlation
- Cross-vendor PSNR drops
- UQ calibration metrics
- Credential coverage at $r = 0.25$ vs $r = 0.10$
- Best-passing-$r$ table by task and subpopulation
- Year-1 deadlines and Year-2 protocol dates

These fill at D9+730 when the Year-1 submission window closes.

## Recurring-paper math

By 2031 (the long-term-vision 5-year horizon), WS-4 alone produces
**4 lead-author papers in a Nature sister journal** on a predictable
annual cadence:

| Year | Paper | Cumulative WS-4 papers |
|---|---|---|
| 2028 (D9+730) | State of the Field — Year 1 | 1 |
| 2029 | State of the Field — Year 2 | 2 |
| 2030 | State of the Field — Year 3 | 3 |
| 2031 | State of the Field — Year 4 | 4 |
| 2032 | State of the Field — Year 5 | 5 |

This is the most compounding component of Track 9 — more lead-author papers
by 2031 than WS-1 + WS-2 + WS-3 combined.

## Submission notes

*npj Digital Medicine* word limit for review articles: ~5000 words main text + extended figures. Current template is ~3000 words of prose; once Year-1 data lands the placeholders expand the word count by perhaps 1000-1500 words (tables, results paragraphs, named-method discussions).

The clinical framing — "what dose can we reduce to and still safely diagnose lung nodule X in subpopulation Y" — is exactly what *npj Digital Medicine* publishes. Avoid the trap of writing a methods-review (that's what *Medical Image Analysis* publishes); keep the angle clinical / digital-health.

## Dependencies on other workstreams

- Cites every Year-1 submission (the leaderboard scoring service produces the submission list)
- Cites [`../../WS-1_dataset/`](../../WS-1_dataset/) (the benchmark)
- Cites [`../../WS-2_framework/`](../../WS-2_framework/) (the evaluation framework)
- Cites [`../../WS-3_reference_method/`](../../WS-3_reference_method/) (the seed entry)
- Pulls cohort data from the [`../scoring/`](../) service (when built)
