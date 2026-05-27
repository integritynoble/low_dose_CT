# PWM-LDCT v0.5 — deposit procedure (PhysioNet + Zenodo + PyPI)

How to package, deposit, and DOI-mint the v0.5 release, then backfill the identifiers across the
manuscript and submission docs. The listing **content** is in [`listing.md`](listing.md); this is the
**mechanics**. Prerequisite: the value-added records exist (annotation campaign + LIDC/AAPM builds,
SUBMISSION_CHECKLIST §3–§5). `[CONFIRM]` marks account/DOI decisions.

> **What is deposited** (openly licensed; **not** the DICOM): `annotations/`, `sim_lowdose/lidc/`,
> `metadata/`, `splits/`, `manifest.sha256`, `deident_audit.jsonl`, plus the code (`pwm_ldct_loader`,
> `pipelines/pwm_ldct_prep`, `baselines`, `schema/`). The AAPM/Mayo DICOM and their DUA-restricted
> pixel derivatives are **excluded** — users regenerate those locally (Data Records table).

---

## Step 1 — Assemble the deposit tree
Stage exactly the deposited artifacts (no DICOM, no DUA-restricted HDF5, no build cruft):
```
pwm_ldct_v0_5_deposit/
├── annotations/{lidc_majority_vote,topup_*,likert,raw_per_reader}/   (CC BY 4.0 / 3.0)
├── sim_lowdose/lidc/                                                 (CC BY 3.0; LIDC-derived)
├── metadata/  splits/  deident_audit.jsonl
├── code/ -> pwm_ldct_loader, pipelines/pwm_ldct_prep, baselines, schema   (Apache-2.0)
├── manifest.sha256
└── LICENSE/  README   (point to the paper + repo)
```
Pull the data records from `gs://low-dose-ct/pwm_ldct_v0_5` (built records) + the campaign outputs;
the code from the repo. Exclude `*.pyc`, `__pycache__`, `*.egg-info`, the harmonized AAPM/Mayo HDF5.

## Step 2 — Manifest + content hash (the citable identifier)
Regenerate the manifest over the complete deposit (sha256sum format, which `validate` parses):
```bash
cd pwm_ldct_v0_5_deposit
find . -type f ! -name manifest.sha256 -print0 | sort -z | xargs -0 sha256sum > manifest.sha256
CONTENT_HASH=$(sha256sum manifest.sha256 | cut -d' ' -f1)   # the content address cited in the paper
python -c "from pwm_ldct_loader import validate; r=validate('.'); print('ok',r.ok,r.errors[:3])"
```
Record `CONTENT_HASH`; it is invariant across all deposit channels.

## Step 3 — Zenodo (mirror DOI, available immediately)
Two options; Zenodo issues a DOI on publish (useful at *submission*, before PhysioNet review finishes):
- **A (recommended for code+docs):** enable Zenodo↔GitHub, then publish a tagged GitHub **release**
  (`v0.5.0`) of `low_dose_CT` → Zenodo auto-archives it and mints a version + concept DOI.
- **B (data records):** create a Zenodo upload, attach the Step-1 tree (or a tarball), set
  **CC BY 4.0**, version `0.5.0`, link the paper; publish → DOI.
Record the **Zenodo DOI** (and concept DOI).

## Step 4 — PhysioNet (primary DOI)
1. Create a project on physionet.org → type **Database**; paste each section from `listing.md`.
2. Upload the Step-1 deposit tree through PhysioNet's file interface (records + code; **no DICOM**).
3. Set **access = Open**, **license = CC BY 4.0**, version `0.5.0`; link the associated publication
   and the Zenodo DOI; include the `CONTENT_HASH` in the project notes.
4. Run PhysioNet's automated checks; submit for editorial review. **PhysioNet assigns the
   `10.13026/…` DOI on publication.**

## Step 5 — PyPI (the loader)
```bash
cd WS-1_dataset/pwm_ldct_loader && python -m build && python -m twine upload dist/*
```
Confirms the `pip install pwm_ldct_loader` Code-Availability link. **[CONFIRM]** PyPI account/token.

## Step 6 — Public repository
Make `github.com/integritynoble/low_dose_CT` public so every Code-Availability URL resolves; tag the
`v0.5.0` release used for the Zenodo archive (Step 3A).

## Step 7 — Backfill identifiers (then re-verify)
Replace the placeholders with the minted DOIs across **all four** docs and rebuild:
| Placeholder | Files |
|---|---|
| `\todo{prefix}` ×2, `\todo{PhysioNet URL}` | `manuscript.tex`; `listing.md`; `reporting_summary.md`; `cover_letter.md` |
| `\todo{Zenodo DOI}` ×2 | same four |
| `\todo{CID}` (optional IPFS mirror) | `manuscript.tex` (can omit) |
| `[CONFIRM]` DOIs | `listing.md`, `reporting_summary.md`, `cover_letter.md` |
Then: rebuild `manuscript.pdf` (pdflatex ×2 + bibtex), confirm the Data/Code-Availability statements
match across all four, and run the SUBMISSION_CHECKLIST sweep (`grep -rn '\\todo{'` / `'\[CONFIRM'`
should be empty except the schema `[CONFIRM:…]` defaults).

## Verification
- `pwm_ldct_loader.validate(deposit)` → ok (manifest verifies, no unresolved de-id hits).
- `CONTENT_HASH` recorded in PhysioNet + Zenodo + the paper; all three resolve to the same content.
- `pip install pwm_ldct_loader` works; repo public; every manuscript URL resolves.

## [CONFIRM]
PhysioNet + Zenodo + PyPI accounts (+ ORCID) · final license (Open / CC BY 4.0) · whether to include
the IPFS/L3 optional mirrors · the corresponding-author/DOI fields in `listing.md`.
