# Corrected patient-block bootstrap — 14 September 2026

The [v2 numeric result](lidc_simulated_bootstrap_stats_full764_patient_v2.json)
supersedes the patient-resampling implementation used for
[`lidc_simulated_bootstrap_stats_full764_patient.json`](lidc_simulated_bootstrap_stats_full764_patient.json).
That earlier artifact is retained for audit and must not be used as a valid
replacement-bootstrap interval: Boolean membership selection discarded repeated
patient draws. Its dose levels were also drawn independently when forming a knee.

The corrected implementation repeats all slices each time a patient is drawn,
uses a common patient draw across doses for each knee, and uses paired blocks
for each model/blur ratio. It estimates a mean or median of pooled slices, not
an equally weighted average of patient means. The LEARN median convention and
the fixed CNR/Rose threshold are inherited descriptive choices; they are not
validated clinical endpoints or a newly selected dose criterion.

## Evidence and limits

Five committed result files contain 764 slices per dose but only **three distinct
patient identifiers**, with cluster sizes 261, 238 and 265. The repeated seed
maps agree and add no independent patients. These records are a small evaluated
subset, not all 205 patients in the release's nominal test split. Source/generator
hashes are in the [run provenance](lidc_simulated_bootstrap_patient_v2_provenance.json).

At 4,000 draws and seed 20260831, CTformer-small's descriptive knee point is
approximately 0.131. Its stored percentile bounds change from `[0.10, 0.2876]`
under the invalid patient implementation to `[0.10, 0.4331]` under v2. The lower
value is censored at the lowest tested ratio: 1,084 draws cross at or below 0.10,
and 2,916 cross within the measured range. It is not an established minimum dose.

The legacy summary also replaced an interval with `[observed, observed]` whenever
the observed crossing was at the boundary, regardless of the replacement draws.
V2 corrects that reporting defect. Its results are:

| Method | Stored percentile bounds | Draws crossing above 0.10 |
|---|---|---:|
| Blur | [0.10, 0.1151] | 163 / 4000 |
| CoreDiff | [0.10, 0.1279] | 157 / 4000 |
| CTformer-small | [0.10, 0.4331] | 2916 / 4000 |
| LEARN | [0.10, 0.1290] | 149 / 4000 |
| RED-CNN | [0.10, 0.1341] | 171 / 4000 |

Each lower endpoint is left-censored at the lowest tested ratio, encoded as
0.10 rather than an exactly measured crossing. The output records that status
and all draw-kind counts. If any draw is unreached or nonfinite, v2 returns a
null interval with an explicit unavailable status instead of silently excluding
it. The historical slice-mode recipe retains its legacy summary convention;
this correction and output are specifically for patient mode.

With only three patients, these percentile intervals are **exploratory**. This
rerun does not establish population coverage, adequate power, clinical
noninferiority or transfer to physical lower-dose acquisition. Matching patient
labels across files checks consistency; independent source mapping and slice
alignment still require provenance from the data holder.

## Reproduce from committed numeric records

```bash
python WS-1_dataset/analysis/bootstrap_lidc_sim.py \
  --unit patient --pooling distinct --B 4000 --seed 20260831 \
  --out WS-1_dataset/output/lidc_simulated_bootstrap_stats_full764_patient_v2.json
```

Run from the repository root. Python 3.11.16 and NumPy 2.4.6 were used. No image,
model, GPU or reader computation is involved. Existing slice-bootstrap outputs
and the original R6 reference comparison are preserved separately.
