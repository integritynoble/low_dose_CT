# `data_acquisition/` — Templates and recipes for sourcing the public datasets

The PWM-LDCT benchmark (WS-1) and the four manuscripts (WS-1/2/3/4) depend on four public datasets, each with different access mechanisms:

| Dataset | Modality | Access | Used in |
|---|---|---|---|
| **LIDC-IDRI** | Chest CT | Free (NBIA registration) | WS-1, WS-2, WS-3 |
| **AAPM 2016 Low-Dose CT Grand Challenge** | Chest+abdomen CT | Mayo email request (1-2 wk) | WS-1, WS-2, WS-3 |
| **fastMRI knee** | MRI | NYU registration | WS-2 (MRI validator) |
| **NEMA NU-2 IQ phantom** | PET | Manufacturer-provided | WS-2 (PET validator) |

This folder contains, for each dataset:
- An access-request email template (if the dataset requires one)
- A download recipe (script or step-by-step)
- A storage budget and a where-to-stage recommendation
- A processing checklist (what to do after the data lands)

Files in this folder:

| File | Purpose |
|---|---|
| [`checklist.md`](checklist.md) | Master data-acquisition checklist with current status |
| [`lidc_idri_download.md`](lidc_idri_download.md) | NBIA Data Retriever download recipe + 50-patient subset script |
| [`ldct_projection_download.md`](ldct_projection_download.md) | LDCT-and-Projection-Data: scripted NBIA REST API recipe, public/restricted scope, GCS staging + verification |
| [`aapm_2016_request.md`](aapm_2016_request.md) | Mayo Clinic access-request email template |
| [`fastmri_request.md`](fastmri_request.md) | NYU fastMRI registration template + agreement notes |
| [`nema_phantom_note.md`](nema_phantom_note.md) | PET phantom data sourcing note |

## Critical-path note

The single longest lead time is **AAPM 2016**: Mayo's response typically arrives in 5-14 days, and access requires a UTSW-affiliated submitting email. Send that request **today**; the LIDC-IDRI subset download and the fastMRI registration can both be done in the same session.

## What this folder does NOT do

- We do not include the actual data. All four datasets are credentialed or have terms that prohibit re-distribution.
- We do not include scripts that pre-register your email on third-party services.
- We do not include UTSW or other institutional-letterhead email accounts; the access requests must originate from a UTSW-affiliated address per Mayo's policy.
