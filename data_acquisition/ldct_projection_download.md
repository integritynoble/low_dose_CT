# LDCT-and-Projection-Data download recipe

The **LDCT-and-Projection-Data** collection (a.k.a. the Mayo "Low Dose CT Image and Projection Data" set) provides, for 299 subjects, both **DICOM-CT-PD projection data** (raw sinograms, full-dose and simulated reduced-dose) and **DICOM reconstructed images** (FBP). It is the projection-domain superset behind the AAPM 2016 Grand Challenge images, and is the primary WS-1 v0.5 public dataset.

**Distributed by:** The Cancer Imaging Archive (TCIA) — DOI [10.7937/9npb-2637](https://doi.org/10.7937/9npb-2637).

**Citation:**
> Moen TR, Chen B, Holmes III DR, et al. Low-dose CT image and projection dataset. *Medical Physics* 48(2):902-911, 2021.
> McCollough C, Chen B, Holmes III DR, et al. Low Dose CT Image and Projection Data (LDCT-and-Projection-data) (Version 7). The Cancer Imaging Archive, 2021.

## Scope: what is public vs. restricted

The full collection is **1,045 series / ~1.29 TB** across 299 subjects (99 head, 100 chest, 100 abdomen, 1 phantom). Access is split:

| Portion | Series | Size | Access |
|---|---|---|---|
| Chest + Abdomen + Phantom | **698** | **~863 GB** | **Public, CC-BY 4.0** — no login; served by the public NBIA REST API |
| Head (neuro), 99 subjects | ~347 | ~463 GB | **Restricted** — credentialed access via Genomic Data Commons; needs an approved TCIA data-access request + login. Not returned by the public API. |

WS-1 v0.5 uses the **public 698-series** portion only (see the two-stage strategy). The head portion requires a separate credentialed request and is out of scope until/unless v1.0 needs it.

Per-patient layout: each subject has 4 series — `Full dose projections`, `Low dose projections` (DICOM-CT-PD, ~1–6 GB each), plus `Full Dose Images`, `Low Dose Images` (512×512 FBP recons, tens–hundreds of MB).

## Download method: NBIA REST API (scripted, no GUI)

Unlike the manual NBIA Data Retriever recipe used for LIDC-IDRI, this collection was pulled programmatically via the public NBIA REST API — reproducible and resumable, with no Java GUI.

### Step 1 — enumerate the public series

```bash
curl -s 'https://services.cancerimagingarchive.net/nbia-api/services/v1/getSeries?Collection=LDCT-and-Projection-Data' -o ldct_series.json
# -> 698 records, each with SeriesInstanceUID, PatientID, SeriesDescription, ImageCount, FileSize
```

### Step 2 — download each series as a zip

```bash
# one series -> zip of <NNNNNNNN>.dcm files + a LICENSE
curl 'https://services.cancerimagingarchive.net/nbia-api/services/v1/getImage?SeriesInstanceUID=<SeriesInstanceUID>' -o series.zip
```

No authentication is required for the 698 public series.

### Step 3 — stage to GCS (`gs://low-dose-ct/ldct_and_projection_data/`)

Because the public portion (~863 GB) exceeds typical local disk, the staging job streams **per series**: download zip → extract → verify count → upload → delete local. NBIA throttles to ~5–10 MB/s per connection; with 3 concurrent series the full 863 GB takes the better part of a day.

**Bucket layout convention:** each series is stored as a `uuid4/` folder containing `uuid4.dcm` files (the LICENSE entry is dropped). Folder/file names are therefore **not** the SeriesInstanceUID — to identify which series a folder holds, read DICOM tag `(0020,000E)` from any file inside it.

## Step 4 — verify integrity

Completeness (every public series present) and integrity (every series holds its full image count) are both checked against the API's `ImageCount`:

```bash
# completeness: distinct SeriesInstanceUIDs in the bucket vs. the 698 from getSeries  -> expect 0 missing
# integrity:    object count of each series folder vs. its ImageCount                 -> expect 0 mismatches
```

The total public collection is **8,044,937 DICOM files** across 698 series. A folder with fewer files than its `ImageCount` is a partial/interrupted download — delete it and re-fetch that single SeriesInstanceUID.

## Common gotchas

- **Don't trust `gsutil ls -r` for sizing** — 8 M objects; a recursive listing or `du` times out. List one level deep (`delimiter='/'`) for folder counts, and parallelize per-folder counts with the GCS client.
- **The head data is genuinely gated.** It will not appear in `getSeries` and cannot be fetched with `getImage` without GDC-approved credentials. Don't mistake the 698 vs. 1,045 gap for an incomplete download.
- **`getImage` returns the whole series in one stream** — no HTTP range/resume. On a dropped connection, retry the series from scratch; keep a per-series done-list so reruns skip completed series.
- **Reconstructed images are 512×512 (~526 KB/file); projection files differ.** A series of ~526 KB files is a recon ("…Images"); large multi-GB series are projections ("…projections").

## License

CC BY 4.0 (Creative Commons Attribution). Citation is mandatory in any publication; commercial use permitted.
