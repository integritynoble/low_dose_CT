# PWM-LDCT 1.0 — table extraction (committed provenance)

These scripts regenerate the manuscript's Data-Records tables **from the deposited
artifacts**, so no table cell is asserted by hand. This resolves the recurring
"provisional / not reproduced from a committed artifact" flags on:

| Manuscript table | Script | Input (deposited) |
|---|---|---|
| `tab:demographics_v05` | `extract_demographics.py` | `metadata/*.json` → `demographics` block (schema §5) |
| `tab:acquisition_v05` | `extract_acquisition.py` | `metadata/*.json` → `acquisition` block (schema §5) |
| `tab:irr_v05` | `extract_inter_rater.py` | `annotations/lidc_majority_vote/*.json` (schema §6) |

## Run

```bash
# once the harmonized builds have written metadata/ and the LIDC consolidation:
python build_tables.py --root /path/to/pwm_ldct_1_0 --out tables --n-patients-total 1010
```

Outputs, per table `<stem>`:
- `tables/<stem>.json` — the numbers,
- `tables/<stem>.tex` — LaTeX rows to `\input` into the manuscript (replaces the hand-typed cells),
- `tables/provenance.json` — file count + combined SHA-256 of every input consumed, so a
  caption can honestly state the table was regenerated from a specific set of deposited files.

## Why this exists

The manuscript previously carried cells (LIDC demographics, acquisition splits, and an
inter-rater row) that were typed in and, in one case, **internally inconsistent** — a stated
"mean 7.75 nodules per annotated patient" against counts that divide to 11.3. Here the
per-patient mean is a `consensus_nodules / annotated_patients` division
(`extract_inter_rater.py`), so it can never disagree with the counts it is printed beside.
The `.tex` output even emits a `% check:` comment showing the division.

## Proof it works now (before the real data exists)

`test_extractors.py` runs all three extractors over `fixtures/` (a handful of synthetic
`metadata` + `lidc_majority_vote` records with hand-verifiable values) and asserts exact
numbers — e.g. 5 consensus nodules over 2 annotated patients ⇒ 2.5/patient. Run:

```bash
python -m pytest test_extractors.py -q
```

The fixtures are synthetic and carry no data claim; they exist only to pin the extractor
logic. When the real `metadata/` and `lidc_majority_vote/` land, point `build_tables.py` at
the release root and `\input` the generated `.tex` files.

## Field contract

Reads exactly the fields defined in `../schema/dataset_schema.md` §5 (`acquisition.*`,
`demographics.*`, `provenance.canonical_patient_key`) and §6 (consensus nodules, each with
`n_contributing_readers`). `○`-marked (optionally-present) fields are treated as unknown
when absent — never fabricated (e.g. AAPM's stripped age/sex render as `N/A`, not a guess).
