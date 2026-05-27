# `WS-1_dataset/physionet_listing/`

Draft content + metadata for the **PhysioNet** project listing of PWM-LDCT v0.5.

- [`deposit_procedure.md`](deposit_procedure.md) — **how to deposit**: package the records, build the
  manifest/content-hash, upload to Zenodo + PhysioNet, publish to PyPI, make the repo public, and
  backfill the minted DOIs across the manuscript + submission docs.
- [`listing.md`](listing.md) — paste-ready content for every PhysioNet authoring section
  (Abstract, Background, Methods, Data Description, Usage Notes, Release Notes, Ethics,
  Acknowledgements, Conflicts of Interest, References) plus the discovery/metadata form fields
  (title, version, access policy, license, topics, DOI, authors, funding).

## Key decisions encoded in the draft (review before submitting)

- **Access policy: Open.** The deposit hosts only *value-added, non-PHI* records (annotations,
  metadata, splits, manifest, code, LIDC-derived simulated low-dose) — not the source DICOM. If any
  record is later judged sensitive, switch to Credentialed (adds DUA + CITI training).
- **License: CC BY 4.0** for data records (CC BY 3.0 for LIDC-derived; CC0 for the manifest),
  **Apache-2.0** for code. Mirrors the manuscript Data Records licensing.
- **Not redistributed:** the AAPM/Mayo DICOM and their DUA-restricted pixel derivatives — users
  obtain scans from NBIA/Mayo/TCIA and regenerate HDF5 locally.

## Before submission — fill the `[CONFIRM]` fields

Authors + affiliations + ORCID + corresponding author · funding/grant numbers · IRB determination
number · the *Scientific Data* paper DOI · per-author competing-interest specifics. PhysioNet
assigns the `10.13026/...` DOI on publication.

## Submission steps (operational)

1. Create the project on physionet.org (type **Database**), paste each section from `listing.md`.
2. Upload the deposit files (annotations / metadata / splits / manifest / `sim_lowdose/lidc` / code).
   The DUA-restricted HDF5 pixels are **not** uploaded.
3. Set access = Open, license = CC BY 4.0, version 0.5.0, link the associated publication.
4. Run PhysioNet's automated checks; submit for editorial review.

> Note: PhysioNet requires the deposit files to be uploaded through its system; this folder is the
> descriptive content/metadata, not the data payload.
