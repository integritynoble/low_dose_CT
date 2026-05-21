# LIDC-IDRI download recipe

LIDC-IDRI is a free, public dataset of 1,018 thoracic CT scans with multi-radiologist lung-nodule annotations. Distributed by The Cancer Imaging Archive (TCIA) via NBIA Data Retriever.

**Citation:** Armato III SG, McLennan G, Bidaut L, et al. The Lung Image Database Consortium (LIDC) and Image Database Resource Initiative (IDRI): A Completed Reference Database of Lung Nodules on CT Scans. Medical Physics 38(2):915-931, 2011.

## Step 1: TCIA / NBIA registration

1. Visit https://wiki.cancerimagingarchive.net/display/NBIA/NBIA+Data+Retriever+Downloads
2. Create a free TCIA account if you don't have one (5 minutes).
3. Download the NBIA Data Retriever for your platform (Windows / macOS / Linux available).

## Step 2: Locate the LIDC-IDRI dataset

1. Go to https://www.cancerimagingarchive.net/collection/lidc-idri/
2. Click "Search and Download" → opens the data portal.
3. Filter by Collection = `LIDC-IDRI`.

## Step 3: Download the 50-patient subset (Phase 1)

For Phase 1 of WS-1, we need a 50-patient subset (~10 GB) to test the
pipeline before committing to the full 125-GB download.

Recommended subset (first 50 patients by ID):
```
LIDC-IDRI-0001, LIDC-IDRI-0002, ..., LIDC-IDRI-0050
```

Steps:
1. In the TCIA data portal, search for "LIDC-IDRI".
2. Filter by Subject ID and select LIDC-IDRI-0001 through LIDC-IDRI-0050.
3. Click "Save Cart"; export the cart as a `.tcia` manifest file.
4. Open the manifest with the NBIA Data Retriever desktop app.
5. Set download destination to `D:/lidc_idri_raw/`.
6. Start download.

**Throughput:** NBIA throttles individual users to ~5-10 MB/s. The 50-patient subset (~10 GB) takes 3-6 hours; the full 1,018-patient cohort (~125 GB) takes 3-7 days.

## Step 4: Verify integrity

After download:

```bash
cd D:/lidc_idri_raw/
# Count expected patient directories
ls -d LIDC-IDRI-* | wc -l
# Expected: 50

# Verify each patient has DICOM
for p in LIDC-IDRI-*; do
  echo "$p: $(find $p -name '*.dcm' | wc -l) DICOM files"
done
```

## Step 5: Process via the WS-1 LIDC pipeline

Once the WS-1 Phase 1 Dockerfile is built (see [`../WS-1_dataset/pipelines/`](../WS-1_dataset/) when it lands), run:

```bash
docker build -t pwm-ldct-prep-lidc:v1 -f WS-1_dataset/pipelines/Dockerfile.lidc_idri .
docker run --rm \
    -v D:/lidc_idri_raw:/data/raw \
    -v D:/lidc_idri_processed:/data/out \
    pwm-ldct-prep-lidc:v1 \
    prep --input /data/raw --output /data/out --seed 42 --subset 50
```

Output: HDF5 shards under `D:/lidc_idri_processed/{train,val,test}/`.

## Common gotchas

- **NBIA Data Retriever requires Java 8+.** Most modern systems have it; verify with `java -version`.
- **TCIA download URLs occasionally rotate.** If the manifest download fails, refresh the cart and re-export.
- **Some LIDC patients have multiple scan series.** Our schema selects the *thin-slice* series (slice thickness $\leq$ 1.5mm) per patient; the WS-1 pipeline handles the selection automatically.
- **Annotations are in a separate XML file per scan.** The pipeline expects to find `.xml` alongside `.dcm`. If missing, re-export the manifest with "Annotations" checked.

## License

LIDC-IDRI is released under CC BY 3.0 (Creative Commons Attribution).
Citation is mandatory in any publication; commercial use is permitted.
