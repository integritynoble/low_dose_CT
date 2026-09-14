# Target journals — every planned paper in this repository

_Compiled 2026-09-14 at `24e2883`, read from each manuscript's own header rather than from plan documents. This file records where each paper is aimed; it makes no submission decision and changes no manuscript._

## The register

| # | Paper | Target venue | Article type |
|---|---|---|---|
| WS-1 | PWM-LDCT v0.5: a content-addressed, multi-task harmonization of the LIDC-IDRI low-dose CT dataset | **Nature Scientific Data** | Data Descriptor |
| WS-2 | Signal-equivalence: testable dose-reduction claims for medical imaging | **Nature Methods** | Article |
| WS-2b | PWM-PET-IQ 1.0: paired full- and reduced-count NEMA NU-2 phantom PET acquisitions | **Nature Scientific Data** | Data Descriptor |
| WS-3 | A multi-vendor corpus of reference low-dose CT reconstructions with calibrated per-pixel uncertainty | **Nature Scientific Data** | Data Descriptor |
| WS-3b | The same reference method, as a method paper | **MICCAI 2027** | LNCS conference paper |
| WS-4 | State of the Field: Year 1 of the PWM Low-Dose CT Challenge | **npj Digital Medicine** | Annual review |
| H | What tolerance a benchmark comparison actually needs — cross-environment reproduction | **Medical Physics** (primary) / **Scientific Reports** (alternative) | Technical Note |

Rows WS-1 to WS-4 are read from the `%% Target venue:` header of each `paper_draft/manuscript.tex`. Row H is proposed in [`HEYANG_PAPER_SCOPE_REPRODUCTION.md`](HEYANG_PAPER_SCOPE_REPRODUCTION.md) and is not yet drafted. WS-5 and WS-6 hold no manuscript.

## What the shape of this plan implies

Six of the seven rows are Nature Portfolio. Three are Data Descriptors, which is the lowest-friction route of the three Nature article types here: a Data Descriptor is judged on the reuse value of the records and the completeness of their technical validation, not on the novelty of a finding. **WS-2 at Nature Methods is by a wide margin the hardest ask**, and it is also the one with a known mathematical correction ahead of it (`FIELD_COLLAPSE_PROBLEMS.md` §8).

Two rows are gated by something other than writing. WS-4 is an annual review of a challenge that has no external submissions yet — rung 5's own method adjustment records that the project's held-out results are standing in as the submission set, and §11 requires adoption to be measured rather than promised. WS-3's credential runs through the detectability channel, whose direction §1 lists as unresolved.

No two rows compete for the same venue in the same cycle, except the two Scientific Data descriptors (WS-1, WS-2b, WS-3), which should be staggered rather than submitted together.

## Row H — why Medical Physics, and the correction it carries

The scoping note's first draft listed *Journal of Medical Imaging*, *Medical Physics*, **ReScience C** and a MICCAI/MIDL reproducibility workshop. **ReScience C is withdrawn from that list.** It exists for *independent, third-party* replication of other groups' published work. The recalculation here was performed by an independent role inside the same project, on the project's own benchmark — self-reproduction, not third-party replication. It would likely be out of scope, and listing it would misstate the relationship.

**Medical Physics is the primary recommendation** on audience rather than prestige: it is AAPM's journal, the AAPM 2016 Low-Dose CT Grand Challenge was published there, and a study of whether metrics computed on that challenge's data reproduce across environments belongs in front of that readership. The Technical Note format fits the content without padding.

**Scientific Reports is the alternative if the priority is that this paper sit in Nature Portfolio with the rest.** It is the only Nature-family venue that accepts work on technical soundness alone, which is exactly this paper's profile. Neither Scientific Data (no new dataset) nor Nature Methods (insufficient methodological novelty) fits.

Other reasonable homes, in descending order of fit: *Physics in Medicine & Biology*, then *Journal of Medical Imaging*. A MICCAI or MIDL reproducibility workshop is viable for visibility but thin as a first-author credential.

### The one change that would make row H a full paper

A **third** environment would turn a pairwise offset into a systematic, metric-dependent one across environments, which is a materially stronger claim than the current two-environment result. The compute is free — the Linux workstation runs torch 2.13.0+cu130 on an RTX 5090 and drives all five models. The blocker is not compute: the A1 checkpoints and the data trees live on the machine that produced them, and moving them is governed by the deposit procedure's use-agreement constraints. Worth considering only if a full paper is wanted; the Technical Note stands without it.

## Maintenance

Each manuscript's `%% Target venue:` header is the source of truth for its row. When a venue changes, change it there first and update this table to match.
