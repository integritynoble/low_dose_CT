# PWM-LDCT v0.5 — DICOM ↔ HDF5 mapping

This document is the side-by-side mapping between the **source DICOM tags retained** by the
de-identification whitelist ([`dicom_cleaning_spec.md`](dicom_cleaning_spec.md) §2) and the
**harmonized HDF5 datasets / attributes and `metadata.json` fields** ([`dataset_schema.md`](dataset_schema.md)).
Its purpose, stated in the manuscript's *Methods → DICOM conformance*, is to let a downstream user
recover original DICOM coordinates and acquisition parameters for any released scan **without
re-downloading the source**.

- **Schema version:** `0.5.0`.
- SOP classes handled: `CT Image Storage` (1.2.840.10008.5.1.4.1.1.2) for reconstructed images;
  research-purpose `Raw Data Storage` / vendor DICOM-CT-PD for projection data (AAPM/Mayo).

---

## 1. Axis and coordinate conventions

| Array | HDF5 path | Axes (C-order) | Definition |
|---|---|---|---|
| Reconstructed volume | `recon/*` | `[Z, H, W]` | `Z` slice (increasing `ImagePositionPatient[2]`), `H` rows, `W` columns |
| Sinogram | `sinogram/*` | `[Z, V, D]` | `Z` matched recon slice, `V` projection views over rotation, `D` detector channels |

- **Patient coordinate system:** LPS (DICOM standard), **preserved**. No reorientation, no flips.
- **Slice ordering:** ascending `ImagePositionPatient[2]`; ties broken by `InstanceNumber`.
- **HU:** stored pixels are `HU = RawPixel * RescaleSlope + RescaleIntercept + hu_offset`
  (per-source `hu_offset`, [`dataset_schema.md`](dataset_schema.md) §5.1).

---

## 2. Reconstructed-image tag mapping

| DICOM tag | Keyword | → HDF5 / metadata location | Transform |
|---|---|---|---|
| (7FE0,0010) | PixelData | `recon/full_dose` (or `low_dose_real`) | decode → HU (§1); cast float32 |
| (0028,1053)/(0028,1052) | RescaleSlope/Intercept | applied, recorded in `provenance` | HU conversion |
| (0028,0010)/(0028,0011) | Rows/Columns | `recon` shape `H`,`W` | — |
| (0028,0030) | PixelSpacing | `acquisition.pixel_spacing_mm` `[row,col]` | verbatim (mm) |
| (0018,0050) | SliceThickness | `acquisition.slice_thickness_mm` | verbatim (mm) |
| (0018,0088) | SpacingBetweenSlices | derives `Z` spacing (fallback: Δ`ImagePositionPatient`) | mm |
| (0020,0032) | ImagePositionPatient | `provenance.slice_positions[z]` | per-slice `[x,y,z]` mm |
| (0020,0037) | ImageOrientationPatient | `acquisition.image_orientation_patient` (6 floats) | verbatim |
| (0018,5100) | PatientPosition | `acquisition.patient_position` | e.g. `HFS` |
| (0018,0060) | KVP | `acquisition.kvp` | verbatim |
| (0018,1152)/(0018,1151)/(0018,1150) | Exposure/TubeCurrent/ExposureTime | `acquisition.exposure_mas` (+ raw) | effective mAs |
| (0018,1210) | ConvolutionKernel | `acquisition.recon_kernel` | verbatim; **not** re-reconstructed |
| (0008,0070)/(0008,1090) | Manufacturer/Model | `acquisition.manufacturer`/`model` | verbatim |
| (0018,0015) | BodyPartExamined | `anatomy` (+ override table) | mapped → `chest`/`abdomen` |

Per-slice arrays (`provenance.slice_positions`) are stored so a voxel index can be mapped back to
patient coordinates (§5) for any released slice.

---

## 3. Projection (sinogram) tag mapping — AAPM / Mayo only

DICOM-CT-PD projection objects carry vendor geometry that the schema serializes as HDF5 datasets
plus per-slice geometry in metadata. Detector/view axes are interpreted explicitly:

| DICOM tag (or DICOM-CT-PD item) | Meaning | → HDF5 / metadata |
|---|---|---|
| projection frames | line-integral measurements | `sinogram/full_dose` `[Z,V,D]` |
| number of views per rotation | `V` | `geometry.n_views` |
| number of detector channels | `D` | `geometry.n_det_channels` |
| (0018,1110) DistanceSourceToDetector | SDD (mm) | `geometry.sdd_mm` |
| (0018,1111) DistanceSourceToPatient | SID (mm) | `geometry.sid_mm` |
| detector element spacing | fan channel pitch | `geometry.det_pitch_mm` |
| detector shape | flat / cylindrical | `geometry.detector_shape` |
| start angle / angular increment | view sampling | `geometry.start_angle_deg`, `geometry.angle_increment_deg` |
| (0018,1120) GantryDetectorTilt | tilt | `geometry.gantry_tilt_deg` |
| (0018,9311) SpiralPitchFactor | helical pitch | `acquisition.pitch` |

`geometry` is a sub-object of `metadata.json` present only for sources with sinograms. It is
sufficient to instantiate a matching forward/back projector (e.g. the manuscript's
`pwm_core.contrib.modalities.ct_radon`) and reproduce the FBP reconstruction (manuscript
*Technical Validation → Reconstruction sanity*).

---

## 4. Sinogram geometry object (`metadata.geometry`)

```jsonc
"geometry": {
  "detector_shape": "cylindrical|flat",
  "n_views": 0, "n_det_channels": 0, "n_det_rows": 1,
  "sid_mm": 0.0, "sdd_mm": 0.0,
  "det_pitch_mm": 0.0,
  "start_angle_deg": 0.0, "angle_increment_deg": 0.0,
  "gantry_tilt_deg": 0.0,
  "fan_angle_deg": 0.0,
  "rebinned": false           // true if the source projection was parallel-rebinned before storage
}
```

For helical acquisitions the per-slice sinogram is the set of views contributing to that slice's
reconstruction; `provenance.slice_positions[z]` gives the table position so users can re-bin if
they prefer a different slice definition.

---

## 5. Recovering original patient coordinates

For voxel `(z, h, w)` in `recon/*`:

```
P(z,h,w) = ImagePositionPatient[z]
           + h * PixelSpacing[0] * RowDir
           + w * PixelSpacing[1] * ColDir
```

where `RowDir = ImageOrientationPatient[0:3]`, `ColDir = ImageOrientationPatient[3:6]`, and
`ImagePositionPatient[z] = metadata.provenance.slice_positions[z]`. `P` is in LPS millimeters,
identical to the source DICOM frame. (All of `ImageOrientationPatient`, `PixelSpacing`, and the
per-slice positions are retained by the whitelist, so this recovery needs no source re-download.)

If the loader was called with `resample_spacing` set, the HDF5 it produced is on the resampled
grid; the **deposited** metadata always records the **native** spacing and positions, and the
resampling transform is invertible from `acquisition.pixel_spacing_mm` + the requested target.

---

## 6. Round-trip guarantee

The pipeline asserts, per scan, that re-deriving `Rows/Columns/PixelSpacing/ImagePositionPatient`
from the HDF5 + metadata reproduces the retained DICOM values exactly (integers/strings) or within
IEEE-754 tolerance (floats). Failures block the scan from the release and are logged to the
de-identification audit (`stage1`), consistent with the *Reconstruction sanity* validation in the
manuscript.
