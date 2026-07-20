# AAPM 2016 Low-Dose CT Grand Challenge — Mayo access-request email

**Send from:** a UTSW-affiliated email address (Mayo's data-sharing policy requires academic-institution affiliation for the requesting account).
**Send to:** `aapm-grand-challenge@mayo.edu` (verify on https://www.aapm.org/grandchallenge/lowdosect/ before sending — the contact address has been stable but may rotate).
**Cc:** PI / UTSW supervisor.

> **Verify first — you may already have this data.** The 2016 AAPM-Mayo challenge images are a
> subset of the now-public **LDCT-and-Projection-Data** collection on TCIA, which is already
> downloaded to `gs://low-dose-ct/ldct_and_projection_data` (199 public patients). Before sending,
> check whether the 10 challenge cases (abdomen, the original quarter-dose challenge set) are present
> there by PatientID — if so, a separate Mayo request is unnecessary and AAPM 2016 can be sourced
> from the same public TCIA collection. Send this email only if the specific challenge release is
> needed beyond what TCIA provides.

---

## Email template

```
Subject: Data access request — 2016 NIH-AAPM-Mayo Clinic Low Dose CT Grand Challenge

Dear AAPM Grand Challenge Data Sharing Committee,

I am writing to request access to the 2016 NIH-AAPM-Mayo Clinic Low Dose
CT Grand Challenge dataset (the 10-patient public release: full-dose
acquisitions with the matched quarter-dose data produced by Mayo's
validated projection-domain noise-insertion method).

I am a researcher at the University of Texas Southwestern Medical Center.
We are preparing an open Data Descriptor (target: Scientific Data) for
PWM-LDCT v0.5, a content-addressed harmonization of three public low-dose
CT datasets — LIDC-IDRI, this AAPM 2016 Grand Challenge release, and the
Mayo LDCT-and-Projection-Data collection — under a single schema, with a
unified loader, reproducible preprocessing pipelines, and harmonized
multi-task annotations. AAPM 2016 is one of the three source datasets in
that harmonization and is the community's reference paired full-dose /
reduced-dose set.

Importantly, our release does NOT redistribute any DICOM. We deposit only
derived, openly-licensed records (harmonized annotations, per-scan
metadata, data splits, and a content-hash manifest) plus open-source code;
users obtain the AAPM 2016 scans from Mayo through this same channel and
regenerate the harmonized files locally. We commit to:
  - Using the data only for the research purpose described above
  - Not redistributing the DICOM; directing all downstream users to
    request access from Mayo
  - Citing the AAPM 2016 Grand Challenge (and McCollough et al., Med Phys
    2017) in any publication that uses the dataset
  - Reporting any reproducibility, quality, or de-identification issues
    we encounter

For clarity on scope: PWM-LDCT v0.5 uses public data only; no new clinical
acquisition is involved, so no UTSW IRB applies to its use of the AAPM 2016
data (which we will use under Mayo's existing institutional release as a
public dataset). Companion methodological work (an evaluation framework and
an open reference reconstruction method) builds on the same harmonized
substrate.

I would appreciate any information on:
  - The current data-sharing agreement template
  - The download mechanism (link, FTP, or other)
  - Any institutional confirmations Mayo requires before granting access

Thank you for maintaining this dataset and for its impact on the low-dose
CT community. Please let me know what additional information would help
expedite the request.

Sincerely,

[CONFIRM: Your name]
[CONFIRM: UTSW title / lab affiliation]
[CONFIRM: UTSW email address]
[CONFIRM: UTSW phone, optional]
```

## What to expect

| Step | Typical timing |
|---|---|
| Mayo first response (acknowledgment + DUA attachment) | 3-7 business days |
| Review the DUA (have UTSW pre-award office sign if institutional) | 1-7 days |
| Sign + return | 1 day |
| Download link issued | 1-3 days |
| Download (~40 GB, throttled) | several hours |

**Total elapsed:** 1-3 weeks. **Send today.**

## Notes

- Mayo's response sometimes includes a request to confirm IRB approval. UTSW IRB has not been submitted yet for the new clinical-data acquisition, but the AAPM 2016 dataset is already de-identified and shared under their own institutional approval — no UTSW IRB is required to *use* it. If Mayo asks, clarify that the AAPM 2016 data will be used under Mayo's institutional approval as a public dataset, not under a UTSW IRB.
- If the email bounces or no response within 14 days, escalate via the AAPM contact page: https://www.aapm.org/grandchallenge/contact.asp
- If Mayo's contact email has rotated, the canonical entry point is the AAPM Grand Challenge page: https://www.aapm.org/grandchallenge/lowdosect/
