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
| Projections | `sinogram/*` | `[V, C, R]` | `V` projection views (helical, ordered by `InstanceNumber`), `C` detector channels, `R` detector rows. Native, series-level (not per-slice). |

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

## 3. Projection (DICOM-CT-PD) mapping — AAPM / Mayo only

The Mayo DICOM-CT-PD format stores **one projection view per DICOM object** (SOP class
`Raw Data Storage`, UID `1.2.840.10008.5.1.4.1.1.66`), with the detector readout as the pixel
array. GE and Siemens share the same private-tag layout (groups `7029/7031/7033/7037/...`); only
the detector dimensions differ (GE `888 × 64`, Siemens `736 × 64` channels × rows). The reader
sorts views by `InstanceNumber` and stacks them into the native `sinogram/full_dose` `[V, C, R]`.

| Source element | Meaning | → HDF5 / metadata |
|---|---|---|
| PixelData (per view) | detector readout `[C, R]` | one slab of `sinogram/full_dose[v]` |
| (0028,1053)/(0028,1052) RescaleSlope/Intercept | stored → line integral | applied per view |
| (0028,0010)/(0028,0011) Rows/Columns | `C` / `R` | `geometry.n_det_channels` / `n_det_rows` |
| (0020,0013) InstanceNumber | view index | view ordering (axis `V`) |
| priv (7029,1011)/(7029,1010) | detector channels / rows | cross-check `C` / `R` |
| priv (7029,100B) | detector shape | `geometry.detector_shape` (e.g. `CYLINDRICAL`) |
| priv (7037,1009)/(7037,100A) | scan / beam type | `geometry.scan_type` / `beam_geometry` (`HELICAL`/`FANBEAM`) |
| priv (7033,1065) | per-channel detector positions (`C` floats) | `geometry.detector_channel_positions` |
| priv (7033,1013) | views per rotation | `geometry.views_per_rotation` |
| priv (7031,1003) | source→isocenter distance (mm, **inferred**) | `geometry.source_to_isocenter_mm` |
| priv (7031,1031) | source→detector distance (mm, **inferred**) | `geometry.source_to_detector_mm` |
| (0018,9311) SpiralPitchFactor | helical pitch | `geometry.pitch`, `acquisition.pitch` |
| (0018,0060) KVP | tube voltage | `geometry.kvp` |
| (0018,0090) DataCollectionDiameter | FOV (mm) | `geometry.data_collection_diameter_mm` |

All decoded private numeric tags are also retained verbatim in `geometry.raw_private_geometry`
(keyed `"gggg,eeee"`). Fields marked **inferred** are decoded by value/position; their exact
semantics require the collection's official DICOM-CT-PD **data dictionary** — `geometry.calibration_status`
records this. With the channel positions, detector shape, SID/SDD, pitch, and views-per-rotation a
matching fan-beam projector (e.g. `pwm_core.contrib.modalities.ct_radon`) can be instantiated to
reproduce the FBP reconstruction (manuscript *Technical Validation → Reconstruction sanity*).

---

## 4. Projection geometry object (`metadata.geometry`)

```jsonc
"geometry": {
  "vendor": "GE|SIEMENS",
  "detector_shape": "CYLINDRICAL|FLAT",
  "scan_type": "HELICAL", "beam_geometry": "FANBEAM",
  "n_views": 0, "n_det_channels": 0, "n_det_rows": 0,
  "views_per_rotation": 0,
  "detector_channel_positions": [/* n_det_channels floats */],
  "source_to_isocenter_mm": 0.0,    // inferred (priv 7031,1003); confirm vs data dictionary
  "source_to_detector_mm": 0.0,     // inferred (priv 7031,1031); confirm vs data dictionary
  "pitch": 0.0, "kvp": 0, "data_collection_diameter_mm": 0.0,
  "raw_private_geometry": { "7031,1001": 0.0 },   // all decoded private numerics, semantics per dictionary
  "calibration_status": "private tags decoded; exact source/detector-distance + channel-angle semantics require the DICOM-CT-PD data dictionary"
}
```

For helical acquisitions the projection array is the full set of views; `provenance.slice_positions[z]`
gives the per-slice table position so users can re-bin views to a slice if
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
