# PWM-LDCT v0.5 — DICOM de-identification & cleaning specification

This document defines the **de-identification whitelist** and the **two-stage verification
protocol** that the manuscript's *Methods → De-identification verification* section describes.
It is run by every preprocessing Dockerfile on each scan before any harmonized artifact is written.

All three source datasets are **already** de-identified to HIPAA Safe Harbor by their original
release teams; this pipeline is a **belt-and-suspenders re-verification** plus a second
de-identification layer over our own re-indexed identifiers. We never relax a source's
de-identification; we only add to it. **v0.5 release scope: LIDC-IDRI only; the AAPM 2016 and
Mayo LDCT-PD sources are v1.0 roadmap** — this spec covers all three sources by design, but the
v0.5 deposited cohort contains LIDC scans only.

- **Schema version:** `0.5.0`. Companion: [`dataset_schema.md`](dataset_schema.md),
  [`dicom_to_hdf5_mapping.md`](dicom_to_hdf5_mapping.md).
- Tooling: PyDICOM (tag handling) + Tesseract OCR (burned-in-text sweep).

---

## 1. HIPAA Safe Harbor identifiers (must be absent)

The 18 Safe Harbor identifier classes must not appear in any retained tag or in pixel data:
names; geographic subdivisions smaller than state; all date elements finer than year (and any
age > 89); telephone/fax; email; SSN; MRN; health-plan/account/certificate numbers; vehicle/device
identifiers; URLs; IP addresses; biometric identifiers; full-face photos; and any other unique
identifying number, characteristic, or code. The pipeline enforces this by **whitelisting** (§2):
anything not explicitly retained is removed, so unknown/private identifier-bearing tags fail closed.

---

## 2. Retained-tag whitelist

**Only** the tags below survive cleaning. Every other standard or private element is deleted
(Stage 1, §3). Tags are retained because the harmonized schema or coordinate recovery needs them,
and none is a Safe Harbor identifier.

| Tag | Keyword | Retained because |
|---|---|---|
| (0008,0016) | SOPClassUID | distinguish CT Image vs Raw Data Storage |
| (0008,0060) | Modality | always `CT` |
| (0008,0070) | Manufacturer | harmonization / per-vendor stratification |
| (0008,1090) | ManufacturerModelName | per-model acquisition table |
| (0008,103E) | SeriesDescription | role inference (full/low dose); scrubbed of free-text PHI (§3.4) |
| (0018,0060) | KVP | acquisition metadata |
| (0018,0050) | SliceThickness | thin-series selection |
| (0018,0088) | SpacingBetweenSlices | geometry |
| (0018,0090) | DataCollectionDiameter | fan-beam geometry |
| (0018,1100) | ReconstructionDiameter | geometry |
| (0018,1110) | DistanceSourceToDetector | sinogram geometry |
| (0018,1111) | DistanceSourceToPatient | sinogram geometry |
| (0018,1120) | GantryDetectorTilt | geometry |
| (0018,1130) | TableHeight | geometry |
| (0018,1140) | RotationDirection | geometry |
| (0018,1150) | ExposureTime | dose / sim calibration |
| (0018,1151) | XRayTubeCurrent | dose / sim calibration |
| (0018,1152) | Exposure | dose / sim calibration |
| (0018,1160) | FilterType | bowtie/spectrum handling |
| (0018,1210) | ConvolutionKernel | kernel preservation |
| (0018,9305–9311) | Spiral pitch / geometry items | pitch, single-collimation, etc. |
| (0020,0032) | ImagePositionPatient | voxel→patient coordinate recovery |
| (0020,0037) | ImageOrientationPatient | orientation (preserved, not reoriented) |
| (0020,0013) | InstanceNumber | slice ordering |
| (0018,5100) | PatientPosition | e.g. `HFS` |
| (0028,0010) | Rows | array shape |
| (0028,0011) | Columns | array shape |
| (0028,0030) | PixelSpacing | in-plane spacing |
| (0028,0100–0103) | BitsAllocated/Stored/HighBit/PixelRepresentation | pixel decode |
| (0028,1052) | RescaleIntercept | HU conversion |
| (0028,1053) | RescaleSlope | HU conversion |
| (0028,1054) | RescaleType | HU units check |
| (7FE0,0010) | PixelData | the image (subject to Stage 2 OCR sweep) |

**Demographics (conditionally retained, generalized):**

| Tag | Keyword | Handling |
|---|---|---|
| (0010,0040) | PatientSex | retained verbatim (`M`/`F`/`O`) |
| (0010,1010) | PatientAge | retained only if ≤ 89 y; else set to `090Y+` bucket |
| (0010,1020)/(0010,1030) | PatientSize / PatientWeight | retained to derive BMI; raw values then dropped |
| (0018,0015) | BodyPartExamined | anatomy inference |

---

## 3. Stage 1 — automated tag cleaning (PyDICOM)

Order of operations, per file:

1. **Whitelist filter.** Delete every element whose tag is not in §2 (including **all** private
   tags, curve/overlay groups `60xx`, and `0x...` group-length elements). Fails closed on unknowns.
2. **UID re-hashing.** Replace `StudyInstanceUID`, `SeriesInstanceUID`, `SOPInstanceUID`, and
   `FrameOfReferenceUID` with salted re-hashes:
   `new_uid = "2.25." + int(sha256(salt + old_uid))`. The `salt` is project-secret and **not**
   released, breaking linkage back to the source UID while keeping intra-series consistency.
   The re-hashed Study/Series UIDs are recorded in `metadata.provenance` (§5 of
   [`dataset_schema.md`](dataset_schema.md)).
3. **Date generalization.** Drop all Date/Time VRs except a derived **year** (`scan_year`), itself
   retained only when the source already published a date; otherwise `null`. No month/day survives.
4. **Free-text scrub.** `SeriesDescription` is matched against a deny-regex (names, dates, MRN-like
   digit runs ≥ 6, `DOB`, etc.); on any hit the value is reduced to the canonical role token
   (`Full dose`/`Low dose` + `projections`/`images`) and the original is discarded.
5. **Re-index to `patient_id`.** Assign the schema's `{source}-{NNNN}` identifier (§4); the native
   subject ID is never written to any output.

---

## 4. Second de-identification layer (re-indexing)

Beyond Safe Harbor, we replace each source's native de-identified subject ID with our own
`patient_id` (`{source}-{NNNN}`). The native→`patient_id` crosswalk is held only in a
project-internal, **unpublished** file. This means a released record cannot be joined back to the
source distribution's per-subject ID without that crosswalk, reducing residual re-identification
risk from cross-dataset linkage.

---

## 5. Stage 2 — burned-in-text OCR sweep (Tesseract)

Some CT slices carry burned-in annotations (rare in these sources, but possible in scout/localizer
or vendor overlays). For **every** reconstructed slice:

1. Window the slice to a display range (`[-160, 240]` HU) and render to 8-bit grayscale.
2. Run Tesseract (`--psm 11`, sparse-text mode) over the full frame and over the 4 image corners
   at 2× upscaling (where burned-in text usually sits).
3. Any recognized token with confidence ≥ **[CONFIRM: 60]** is matched against PHI patterns
   (alphabetic name-like runs, digit runs ≥ 6, date patterns, `MRN`/`DOB`/`ACC` keywords).
4. A positive match **flags the slice for manual radiologist/curator review**; the scan is held
   out of the release until cleared or the region is masked.

OCR hits, confidences, and review dispositions are written to the audit log (§6).

---

## 6. Verification & audit log

The pipeline emits one append-only audit row per scan to `deident_audit.jsonl` (published as
Supplementary Material; `deident_audit_id` links each `metadata.provenance` entry to its row):

```jsonc
{
  "deident_audit_id": "string",
  "scan_uid": "string",
  "source": "lidc|aapm|mayo",
  "stage1": {
    "tags_deleted": 0, "private_tags_deleted": 0,
    "uids_rehashed": 4, "dates_generalized": 0, "seriesdesc_scrubbed": false
  },
  "stage2_ocr": {
    "slices_scanned": 0, "hits": 0,
    "hit_detail": [ {"slice": 0, "token": "REDACTED", "conf": 0.0, "disposition": "cleared|masked|dropped"} ]
  },
  "result": "pass|held_for_review",
  "tool_versions": {"pydicom": "x.y.z", "tesseract": "x.y.z"},
  "timestamp_utc": "ISO-8601"
}
```

**Release gate:** a scan enters the release only when its row reads `result: "pass"` with zero
unresolved Stage-2 hits. Per the manuscript, no PHI was detected in any released scan; the audit log
is the evidence. A PHI hit discovered post-release triggers a PATCH release (manuscript
*Errata* policy) that removes/masks the affected scan and regenerates `manifest.sha256`.

---

## 7. What this spec deliberately does not do

- It does not re-window, re-reconstruct, or denoise pixels (only HU rescale + offset; see
  [`dataset_schema.md`](dataset_schema.md) §5.1).
- It does not attempt facial-defacing of head CT — **out of v0.5 scope** (no head data in the
  public v0.5 cohort; the Mayo head subset is restricted-access and excluded).
- It does not re-distribute the cleaned DICOM. Cleaning runs locally inside the pipeline; only the
  derived harmonized artifacts and metadata leave the user's machine.
