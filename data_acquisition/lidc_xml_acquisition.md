# LIDC-IDRI radiologist-annotation (XML) acquisition

The four-radiologist nodule annotations for LIDC-IDRI are distributed as **XML reading files**
(`LidcReadMessage`), separate from the DICOM images. Our converter
([`../WS-1_dataset/pipelines/pwm_ldct_prep/lidc_annotations.py`](../WS-1_dataset/pipelines/pwm_ldct_prep/lidc_annotations.py))
consumes them and majority-votes per the QA protocol
([`../WS-1_dataset/schema/annotation_qa_protocol.md`](../WS-1_dataset/schema/annotation_qa_protocol.md)).

> **Why this is needed.** The LIDC images already staged at `gs://low-dose-ct/lidc_idri` were pulled
> via the image-only NBIA REST API — **no XMLs** (verified: 60k objects, all `.dcm`). The XML
> annotations must be acquired separately. They are CC BY 3.0 (attribution required).

The converter activates when an `*.xml` sits **in the same directory as a scan's DICOM files**
(it globs the series' DICOM directory for `*.xml`). So acquisition is really two things: (1) get the
XMLs, and (2) co-locate each XML with its scan's DICOMs in a per-series directory layout.

---

## Method A (recommended) — NBIA Data Retriever, XMLs co-located

The NBIA Data Retriever desktop app downloads LIDC-IDRI in a `Patient / Study / Series/` layout with
the reading XML **already placed in each Series folder** alongside the DICOMs — exactly what the
converter expects, no remapping.

1. Create a free TCIA account and install the NBIA Data Retriever (see
   [`lidc_idri_download.md`](lidc_idri_download.md) §1).
2. On the LIDC-IDRI collection page → **Search and Download**; build a cart of the subjects you need
   (start with the v0.5 subset, then the full 1,018).
3. **Important:** when exporting/downloading, ensure annotations are included (export the cart with
   the radiologist-annotation option enabled; the Data Retriever then writes the XML into each
   Series folder). If a download has DICOM but no XML, re-export with that option checked.
4. Point the LIDC pipeline at that local tree:
   ```bash
   docker run --rm -v /lidc_with_xml:/data/raw -v /out:/data/out \
       pwm-ldct-prep-lidc:v0.5 prep --source lidc --input /data/raw --output /data/out --seed 42
   ```
   The adapter discovers the `*.xml` beside each series and emits
   `annotations/lidc_majority_vote/` + `raw_per_reader/`.

## Method B — standalone TCIA "LIDC-XML-only" set, then remap

TCIA also publishes the annotations as a **standalone XML archive** on the LIDC-IDRI page (under the
Data / supporting-files section; historically `LIDC-XML-only.zip`, ~tens of MB — verify the exact
name/URL on the page, it may rotate). Use this if you already have the DICOMs and only need XMLs.

1. Download and unzip the XML archive → a tree of `*.xml` reading files (not co-located with DICOMs).
2. Each XML's `<ResponseHeader>` carries `<SeriesInstanceUid>` (and `<StudyInstanceUid>`). **Remap**:
   for each XML, read its SeriesInstanceUID and copy it into the directory holding that series' DICOMs.
   Sketch:
   ```python
   import glob, os, shutil, xml.etree.ElementTree as ET, pydicom
   def ln(t): return t.split('}')[-1]
   def xml_series(p):
       for e in ET.parse(p).getroot().iter():
           if ln(e.tag) in ("SeriesInstanceUid", "SeriesInstanceUID") and e.text:
               return e.text.strip()
   # map SeriesInstanceUID -> a directory in the local DICOM tree (read one header per dir)
   ser2dir = {}
   for d in {os.path.dirname(f) for f in glob.glob("/lidc_dicom/**/*.dcm", recursive=True)}:
       h = pydicom.dcmread(glob.glob(d+"/*.dcm")[0], stop_before_pixels=True, force=True)
       ser2dir[str(h.SeriesInstanceUID)] = d
   for x in glob.glob("/lidc_xml/**/*.xml", recursive=True):
       d = ser2dir.get(xml_series(x))
       if d: shutil.copy(x, d)
   ```
3. Then run the LIDC pipeline on that co-located tree as in Method A.

> **Bucket-layout caveat.** The `gs://low-dose-ct/lidc_idri` copy stores **one DICOM per UUID folder**,
> so a series' slices are spread across many folders — there is no single per-series directory to drop
> an XML into. For annotations, prefer Method A (NBIA download → proper `Series/` layout), or first
> reorganize the DICOMs into per-series folders before remapping XMLs.

---

## Verification

- **Counts:** LIDC-IDRI has **1,018 scans**; expect on the order of ~1,018 nodule reading XMLs (some
  scans carry blinded + unblinded reads). Also download TCIA's **nodule-size / nodule-count list** to
  cross-check.
- **Coverage:** after `prep`, the number of `annotations/lidc_majority_vote/*.json` should match the
  LIDC patients processed; spot-check that nodule counts/attributes recover the published LIDC values
  (this is the manuscript's *annotation-reuse fidelity* validation, `tab` in Technical Validation).
- **Format:** the converter is namespace-agnostic over `LidcReadMessage` →
  `readingSession / unblindedReadNodule / roi / edgeMap` + `characteristics/texture`; sub-3 mm nodules
  (single edge point) become degenerate boxes.

## License & citation
CC BY 3.0. Cite Armato SG III, et al. *Med Phys* 38(2):915-931, 2011 (and the TCIA collection DOI).
