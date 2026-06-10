# `WS-3_reference_method/deposit/` — corpus deposit kit

Artifacts for depositing the WS-3 **derived-reconstruction corpus** and
submitting the *Scientific Data* Data Descriptor (`../paper_draft/manuscript.tex`).

| File | Purpose |
|---|---|
| [`DEPOSIT_CHECKLIST.md`](DEPOSIT_CHECKLIST.md) | End-to-end gating checklist: generate → validate → package → deposit (DOI) → fill manuscript → submit. Hard-gated on Phase-3 data existing and on a minted figshare/Zenodo DOI. |
| [`dataset_metadata.schema.json`](dataset_metadata.schema.json) | JSON Schema (draft-07) for the `dataset_metadata.json` that ships at the corpus archive root. Pins record types, licences, source-dataset relation, credential framework hash, integrity manifest. |
| [`dataset_metadata.example.json`](dataset_metadata.example.json) | Seed template with descriptive fields + deposit-time placeholders. The human fills the descriptive fields; `package_corpus.py` overlays the counts/sizes. Validates against the schema today. |
| [`package_corpus.py`](package_corpus.py) | Writes `dataset_metadata.json` (counts/sizes filled from disk) **then** `MANIFEST.sha256` (covers the metadata). `verify` recomputes hashes vs the manifest. CLI + importable API; 13 tests. |

## Package + verify the corpus

```
# fill metadata counts from disk + write the integrity manifest
python package_corpus.py package <corpus_root> --seed dataset_metadata.example.json

# later (reuser / CI): confirm nothing drifted
python package_corpus.py verify <corpus_root>          # -> {"ok": true, ...}
# or with standard tooling, from the corpus root:
( cd <corpus_root> && sha256sum -c MANIFEST.sha256 )
```

`package` writes metadata first so the manifest covers it; the filled metadata is
validated against `dataset_metadata.schema.json` (pass `--require-schema-valid`
to make a violation a non-zero exit).

## Validate the metadata standalone

```
python -c "import json,jsonschema; jsonschema.validate(
  json.load(open('dataset_metadata.json')),
  json.load(open('dataset_metadata.schema.json')))" && echo VALID
```

## Two things that block submission (not writing — data + DOI)

1. **The corpus must exist** — generated on real Phase-3 data (D9+270), not synthetic. *Scientific Data* will not review a Data Descriptor whose records don't exist.
2. **A real DOI** — figshare/Zenodo, data under CC BY 4.0. The IPFS RunBundle CID is a supplementary integrity anchor, not a substitute for the DOI.

See [`../paper_draft/README.md`](../paper_draft/README.md) for the reframe rationale and the manuscript's section structure.
