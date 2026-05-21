# Data-acquisition master checklist

**Use this file as the single source of truth for current data-acquisition state.** Mark items `[x]` when done.

## Status legend

- `[ ]` Not started
- `[~]` In progress (note status inline)
- `[x]` Complete

---

## LIDC-IDRI (chest CT, free, public)

- [ ] Create TCIA/NBIA account at https://wiki.cancerimagingarchive.net/display/NBIA/
- [ ] Install NBIA Data Retriever (Windows / Mac / Linux: https://wiki.cancerimagingarchive.net/display/NBIA/NBIA+Data+Retriever+Command-Line+Interface+Guide)
- [ ] Download the 50-patient subset listed in [`lidc_idri_download.md`](lidc_idri_download.md) (~10 GB)
- [ ] Stage at `D:/lidc_idri_raw/` (or per local storage policy)
- [ ] Run the WS-1 LIDC-IDRI Dockerfile to produce HDF5 shards (see [`../WS-1_dataset/`](../WS-1_dataset/))
- [ ] (Optional, Phase 2) Download full 1,018-patient cohort (~125 GB)

**Lead time:** Account creation 5 min, NBIA download throttled to ~5-10 MB/s = several hours for 50 patients.

---

## AAPM 2016 Low-Dose CT Grand Challenge (chest + abdomen, Mayo-controlled)

- [ ] Send the email in [`aapm_2016_request.md`](aapm_2016_request.md) **from a UTSW-affiliated email address** to Mayo (current contact: aapm-grand-challenge@mayo.edu — verify before sending)
- [~] Await Mayo response (typically 5-14 days)
- [ ] Sign the Mayo data sharing agreement when it arrives
- [ ] Receive download link
- [ ] Download the 10-patient public release (~30 GB raw + ~10 GB reconstructed)
- [ ] Stage at `D:/aapm_2016_raw/`
- [ ] Run the WS-1 AAPM 2016 Dockerfile (see [`../WS-1_dataset/`](../WS-1_dataset/))

**Lead time:** Mayo response 1-2 weeks; total elapsed time including signing + download ~3 weeks.

**Critical:** This is the **only** dataset in the four with paired real low-dose acquisitions for the same patient. The full-dose-only datasets (LIDC) cannot substitute.

---

## fastMRI knee (MRI, NYU-controlled)

- [ ] Register at https://fastmri.med.nyu.edu/ (NYU Langone account; affiliation field accepts academic and PWM affiliations)
- [ ] Sign the fastMRI data-use agreement (electronic, immediate)
- [ ] Download the knee subset for the WS-2 MRI validator (singlecoil + multicoil knee training subset ~100 GB; brain dataset NOT needed for WS-2 v1)
- [ ] Stage at `D:/fastmri_knee/`
- [ ] Run the WS-2 MRI validator pipeline (see [`../WS-2_framework/`](../WS-2_framework/))

**Lead time:** Registration + agreement ~15 minutes; download throttled to ~5 MB/s typically = several hours to days.

**Note:** fastMRI brain is a separate dataset with separate agreement — only needed if WS-2 Phase 3 MRI validation later includes brain (not Year-1 scope).

---

## NEMA NU-2 IQ phantom (PET, manufacturer-provided)

- [ ] Identify a partnering PET site (UTSW Nuclear Medicine is the default) that has the physical phantom
- [ ] Schedule phantom scans at full activity + 50% / 25% / 10% activity
- [ ] Acquire reconstructed images + sinograms in DICOM
- [ ] Stage at `D:/nema_phantom/`
- [ ] Run the WS-2 PET validator pipeline (see [`../WS-2_framework/`](../WS-2_framework/))

**Lead time:** Phantom acquisition can be scheduled within 2-4 weeks at most academic medical centers; the phantom itself is permanently installed at the scanner site.

**Note:** PET is the second-modality stretch validator. If only one of {MRI, PET} fits the Year-1 manuscript timeline, drop PET — MRI satisfies the multi-modality bar for *Nature Methods* alone.

---

## What to do today

Highest-leverage action: send the AAPM 2016 email (5-minute write + send; unblocks the longest lead-time dependency).
Second: register for fastMRI (15 min).
Third: register for NBIA and queue the LIDC-IDRI 50-patient download (background download).

These three actions take ~45 minutes of active time and unblock $\geq$ 90% of the public-data dependencies for WS-1/2/3.

## Storage budget summary

| Dataset | Estimated size (final) | Where |
|---|---|---|
| LIDC-IDRI 50-patient subset | ~10 GB | `D:/lidc_idri_raw/` |
| LIDC-IDRI full (Phase 2 stretch) | ~125 GB | `D:/lidc_idri_full/` |
| AAPM 2016 public release | ~40 GB | `D:/aapm_2016_raw/` |
| fastMRI knee | ~100 GB | `D:/fastmri_knee/` |
| NEMA phantom | ~5 GB | `D:/nema_phantom/` |
| **Total active (no LIDC full)** | **~155 GB** | |

Plan ahead: a 1-TB external drive is comfortable; OneDrive is *not* a good staging location for these datasets due to credentialed-redistribution constraints. Stage on local non-synced storage.
