# NEMA NU-2 IQ phantom — PET acquisition note

The NEMA NU-2 IQ (Image Quality) phantom is a standard PET test object with six fillable spheres of known sizes (10, 13, 17, 22, 28, 37 mm) used to measure contrast recovery, image quality, and quantitative accuracy. For WS-2's PET validator we need acquisitions at full + reduced activity levels.

**Reference:** NEMA Standards Publication NU 2-2018, "Performance Measurements of Positron Emission Tomographs".

## Why this (and not a public phantom dataset)?

Public PET phantom datasets exist but are rarely paired across activity levels in a way that supports signal-equivalence framework validation. The NEMA NU-2 phantom is physically present at every academic medical center with a PET scanner; an in-house acquisition campaign is faster and more controlled than searching for a public paired-activity release.

## Step 1: Identify a partnering PET site

Default: UTSW Nuclear Medicine (PET scanners typically include Siemens Biograph, GE Discovery, or similar).

Alternative: any academic medical center with:
- A clinical or research PET scanner
- A NEMA NU-2 phantom on site (almost all clinical PET sites have one for QC)
- A nuclear medicine physicist or technologist willing to perform the acquisition

## Step 2: Plan the acquisition protocol

We need paired acquisitions at:
- **Full activity** — manufacturer's recommended reference activity for the NEMA NU-2 phantom (typically 5 mCi $^{18}$F-FDG in the background, with 4:1 spheres-to-background ratio)
- **50% activity** — same phantom fill, 50% radiotracer
- **25% activity** — same phantom fill, 25% radiotracer
- **10% activity** — same phantom fill, 10% radiotracer

Each acquisition: 10-minute static scan, standard reconstruction (OSEM with the vendor's default regularization), list-mode raw data preserved.

**Critical:** Use the *same physical phantom* with the *same fill geometry* across all four acquisitions. The activity reduction is the only varying parameter.

## Step 3: Acquisition coordination

Email template to the partnering PET site / physicist:

```
Subject: Research request — NEMA NU-2 phantom paired-activity acquisitions

Dear [Physicist / NM Director],

I am working on a methodological framework for evaluating reduced-signal
medical imaging methods (signal-equivalence framework, target Nature
Methods 2027; see [link to WS-2 manuscript draft]).

For the PET validator I need NEMA NU-2 IQ phantom acquisitions at four
activity levels (full / 50% / 25% / 10%) on a clinical or research PET
scanner. Each acquisition: 10-min static scan with list-mode data
preservation.

Estimated time: 1 hour of phantom acquisition (4 scans x ~10 min each
+ setup), plus reconstruction time. The phantom can stay on the scanner
across the four scans; only the radiotracer activity changes.

Would your facility be able to support this acquisition? I would
coordinate scheduling around clinical workload and cover any costs
related to phantom-fill consumables.

Thank you,
[Name]
```

## Step 4: Process via WS-2 PET validator

Once the WS-2 PET validator lands (Phase 3 stretch), see
[`../WS-2_framework/`](../WS-2_framework/).

The validator's contract:
- Input: list-mode counts + reconstructed images at the four activity levels
- Reference method ($\mathcal{M}_{\textrm{ref}}$): OSEM at full activity
- Method under test: any user-supplied reconstruction method
- Task: contrast recovery coefficient (CRC) for each sphere size; or sphere-quantification accuracy
- Output: 5-tuple signal-equivalence credential at $r = 0.25$ for the canonical
  CRC-by-sphere-size task.

## Storage

Modest: ~1 GB per acquisition (list-mode) + reconstructed images. Total ~5 GB. Stage at `D:/nema_phantom/`.

## Year-1 stretch

PET is the **second-modality stretch** for WS-2 Year 1. If only one of {MRI, PET} fits the manuscript timeline, drop PET — MRI alone satisfies the multi-modality bar for *Nature Methods*. The PET worked example can be added in WS-2's v2 paper or in the WS-2 follow-up paper that closes the open questions in [`../WS-2_framework/theory/open_questions.md`](../WS-2_framework/theory/open_questions.md) §8.

## Note on alternative public PET data

If in-house acquisition is delayed:
- The Ultra-Low-Dose PET Imaging Challenge (uPET) released a public paired-activity dataset in 2022; useful as fallback but limited to one scanner manufacturer.
- The University of Bern released anatomically-realistic PET phantom data (XCAT-derived) at multiple activity levels; useful but synthetic.

Both are inferior to in-house NEMA acquisition for framework-validation purposes because they fix one or more of {scanner model, phantom, fill protocol} that we want to control.
