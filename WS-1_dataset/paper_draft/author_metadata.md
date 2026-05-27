# PWM-LDCT v0.5 — author metadata + CRediT template

Fill this once; it feeds every author/ethics/COI field across the package (manuscript title block,
Author contributions, Competing interests; PhysioNet `listing.md`; `cover_letter.md`;
`reporting_summary.md`). `[FILL]` = enter real values. *Scientific Data* uses the CRediT taxonomy and
requires a corresponding author (ORCID strongly encouraged).

---

## 1. Author roster  `[FILL]`
| # | Full name | ORCID | Affiliation(s) | Email | Corresponding? | Equal-contrib? |
|---|---|---|---|---|---|---|
| 1 | [FILL] | [FILL] | [FILL: UTSW …] | [FILL] | ✓ | |
| 2 | [FILL] | [FILL] | [FILL] | | |
| … | | | | | | |

List affiliations once and index them (matches the LaTeX `\affil[n]` below).

## 2. CRediT roles (the 14) — mapped to this descriptor's work
Assign each author one or more. For PWM-LDCT v0.5 the work concentrates in **Software**,
**Data curation**, **Methodology**, **Validation**:

| CRediT role | What it covers here |
|---|---|
| Conceptualization | the harmonized-benchmark idea; v0.5/v1.0 strategy |
| **Data curation** | harmonization, de-identification re-verification, the deposited records |
| Formal analysis | inter-rater κ, distributional metrics, baseline metrics |
| Funding acquisition | grants (also Acknowledgements) |
| Investigation | annotation campaign (radiologist readers), data acquisition |
| **Methodology** | schema, low-dose forward model, annotation QA protocol, splits/de-dup |
| Project administration | coordination, timeline |
| Resources | compute, source-data access, radiologist honoraria |
| **Software** | `pwm_ldct_loader`, `pwm_ldct_prep` pipelines, `pwm_ldct_baselines`, schema specs |
| Supervision | PI oversight |
| **Validation** | technical validation, reconstruction-sanity, baseline reproductions |
| Visualization | figures/tables |
| Writing – original draft | manuscript first draft |
| Writing – review & editing | revisions |

### Per-author role matrix  `[FILL]` (✓ where applicable)
| Author | Concept | DataCur | FormAnal | Funding | Investig | Method | ProjAdmin | Resources | Software | Superv | Valid | Visual | Write-orig | Write-rev |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | | | | | | | |
| 2 | | | | | | | | | | | | | | |

## 3. Ready-to-paste outputs (after filling §1–§2)

**3a. Manuscript title block** (replace "Authors to be confirmed" in `manuscript.tex`):
```latex
\author[1]{First A. Author}
\author[1,2]{Second B. Author}
% ...
\affil[1]{[FILL] University of Texas Southwestern Medical Center, Dallas, TX, USA}
\affil[2]{[FILL] PWM Protocol Foundation}
% corresponding author: add a footnote/email per the Scientific Data template
```

**3b. Author contributions** (replace the `\todo{}` in `manuscript.tex`; CRediT prose):
> [Author 1] and [Author 2] conceived the study (Conceptualization). [Authors] developed the
> harmonization schema, low-dose forward model, and annotation QA protocol (Methodology) and
> implemented the loader, pipelines, and baseline harness (Software). [Authors] curated and
> de-identified the data (Data curation) and performed the technical validation (Validation).
> [Radiologist authors] performed the annotation campaign (Investigation). [PI] supervised
> (Supervision) and acquired funding (Funding acquisition). [Authors] wrote the original draft
> (Writing – original draft); all authors reviewed and edited (Writing – review & editing).

**3c. Competing interests** (fill the `\todo{}` in `manuscript.tex`; the affiliation disclosure is
already drafted — append the specifics):
> Authors [FILL names] are affiliated with / hold [equity | tokens | paid consulting | board role]
> in the PWM Protocol Foundation. The remaining authors declare no competing interests.
> [If none beyond affiliation: "The authors declare no competing financial interests."]

**3d. Other docs** (just need names/ORCID/corresponding from §1): `physionet_listing/listing.md`
authors field; `cover_letter.md` sign-off; `reporting_summary.md` (no author block, but ethics).

## 4. Ethics / IRB  `[FILL]`
- **IRB determination no.:** `[FILL]` (UTSW non-human-subjects / exempt determination for the
  annotation campaign). Feeds `manuscript.tex` Ethics, `listing.md`, `reporting_summary.md`,
  `cover_letter.md`.
- **Funding / grant numbers:** `[FILL]` → manuscript Acknowledgements + `listing.md`.

## 5. After filling — clears these placeholders
`manuscript.tex`: title block, `\todo{}` Author contributions, `\todo{}` Competing interests,
`\todo{IRB determination no.}` · `listing.md` author/funding/DOI `[CONFIRM]` · `cover_letter.md`
corresponding-author `[CONFIRM]` · `reporting_summary.md` ethics `[CONFIRM]`. Re-run the
SUBMISSION_CHECKLIST grep sweep afterward.
