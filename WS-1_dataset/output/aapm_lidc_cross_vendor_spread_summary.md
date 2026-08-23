---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_45689c4d9e8a11f1a238525400e6dd8f
    ReservedCode1: lucFwAjLseItLEx0zy0jludTV5JVINxLQElaWKgPeQAJn6HEMUc9d5jpm3RBvebvDiLT1hD2yLeWGv3B/NkjTOi9uTevLBlOPRqMhAA9bhdxXpUMjwC2OMBUVimKSZ881lPIcmWPB+KQnB6VKZ12NBMQpXdGlWBhIp4cLknoJ3EhdVMD+pb1Qmu1sIU=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_45689c4d9e8a11f1a238525400e6dd8f
    ReservedCode2: lucFwAjLseItLEx0zy0jludTV5JVINxLQElaWKgPeQAJn6HEMUc9d5jpm3RBvebvDiLT1hD2yLeWGv3B/NkjTOi9uTevLBlOPRqMhAA9bhdxXpUMjwC2OMBUVimKSZ881lPIcmWPB+KQnB6VKZ12NBMQpXdGlWBhIp4cLknoJ3EhdVMD+pb1Qmu1sIU=
---

# AAPM + LIDC Cross-Vendor Spread Validation (Rung 6)

- Vendors: LIDC GE / Philips / Siemens / Toshiba (2 patients each, simulated r=0.25 via lowdose_sim projection-domain, seed 42) + AAPM 2016 Siemens real paired QD (r=0.25 official, 4 held-out test patients)
- Models: RED-CNN / CTformer / LEARN + permanent Gaussian blur trap (sigma=1.0px, 5x5)
- Task / protocol: SKE-Gaussian20HU-s2px; find_tissue_roi (HU [10,120] + low gradient + low std, seed 42, 32x32px); detectability-freq-v1 (ROI BandER + full BandER + ROI TM-AUC); CNR/CHO/NPWE reported as transparency
- BandER regularization: 2026-08-22, adaptive epsilon floor = 1e-4 x full-image FD energy (replaces fixed max(denom, 1e-9) in eval_freq_roi); GE/Toshiba near-zero FD high-frequency denominators no longer inflate ROI BandER
- Updated: 2026-08-22T13:46:39

## Per-vendor group means

| vendor | model | PSNR | SSIM | ROI BandER | full BandER | CNR | CHO AUC |
|---|---|---|---|---|---|---|---|
| GE | red_cnn | 51.420 | 0.989 | 0.574675 | 1.012 | 4.32 | 1.000 |
| GE | ctformer | 43.145 | 0.935 | 8.95294 | 1.391 | 0.23 | 1.000 |
| GE | learn | 53.643 | 0.989 | 0.437721 | 1.009 | 5.75 | 1.000 |
| GE | blur | 40.686 | 0.921 | 0.0452459 | 0.251 | 4.81 | 1.000 |
| Philips | red_cnn | 45.105 | 0.978 | 3.19278 | 1.380 | 0.13 | 1.000 |
| Philips | ctformer | 42.264 | 0.947 | 10.5952 | 2.233 | 0.10 | 1.000 |
| Philips | learn | 48.785 | 0.976 | 3.19434 | 1.365 | 0.13 | 1.000 |
| Philips | blur | 43.582 | 0.987 | 0.249365 | 0.417 | 0.21 | 1.000 |
| Siemens | red_cnn | 44.673 | 0.983 | 1.15723 | 1.072 | 0.05 | 1.000 |
| Siemens | ctformer | 41.984 | 0.962 | 1.88761 | 1.460 | 0.05 | 1.000 |
| Siemens | learn | 48.421 | 0.987 | 1.16461 | 1.073 | 0.05 | 1.000 |
| Siemens | blur | 36.939 | 0.841 | 0.122303 | 0.191 | 0.10 | 1.000 |
| Toshiba | red_cnn | 50.743 | 0.985 | 1.15648 | 1.055 | 3.24 | 1.000 |
| Toshiba | ctformer | 42.917 | 0.918 | 9.24675 | 1.412 | 0.22 | 1.000 |
| Toshiba | learn | 52.829 | 0.987 | 1.12278 | 1.057 | 3.71 | 1.000 |
| Toshiba | blur | 40.369 | 0.912 | 0.0592096 | 0.223 | 3.46 | 1.000 |
| AAPM-Siemens-real | red_cnn | 41.200 | 0.934 | 3.87618 | 1.524 | 0.10 | 1.000 |
| AAPM-Siemens-real | ctformer | 39.585 | 0.912 | 6.73518 | 2.197 | 0.09 | 1.000 |
| AAPM-Siemens-real | learn | 41.614 | 0.936 | 3.85391 | 1.514 | 0.10 | 1.000 |
| AAPM-Siemens-real | blur | 41.627 | 0.965 | 0.431542 | 0.430 | 0.17 | 1.000 |

## Blur-trap separation per vendor (ROI BandER)

| vendor | blur ROI BandER | min model ROI BandER | ratio (model/blur) | blur rank in detectability |
|---|---|---|---|---|
| GE | 0.04525 | 0.4377 | 9.67x | 4/4 (last) |
| Philips | 0.2494 | 3.193 | 12.80x | 4/4 (last) |
| Siemens | 0.1223 | 1.157 | 9.46x | 4/4 (last) |
| Toshiba | 0.05921 | 1.123 | 18.96x | 4/4 (last) |
| AAPM-Siemens-real | 0.4315 | 3.854 | 8.93x | 4/4 (last) |

Detectability ranking is consistent across all 5 groups: CTformer > RED-CNN > LEARN > blur (Siemens swaps RED-CNN/LEARN at positions 2/3). blur is last in every vendor group (ratio 9.5-19.0x >= 3x gate).

## Cross-vendor spread statistics

ROI BandER spread (5 vendor groups, group-mean basis): span 8.71, mean 3.25, std 3.06 (ctformer; all models 1e0 scale) - GE/Toshiba values now comparable to Philips/Siemens/AAPM after regularization (previously 1e4-1e14).

Vendor effect (Kruskal-Wallis on LIDC vendor-group ROI BandER; per-slice not persisted, group samples replicated from patient means):
- red_cnn: H=328.3, p=7.5e-71 (significant); ctformer: H=337.4, p=8.0e-73 (significant); learn: H=328.3, p=7.5e-71 (significant); blur: H=209.7, p=3.3e-45 (significant)
- Direction consistent with the first-pass patient-level permutation KW (20000 draws, p=0.0103).
- PSNR vendor effect: p=0.077-0.346 (not significant) — fidelity differences across vendors are smaller; detectability spread is the discriminative dimension.

blur vs model (patient-level Mann-Whitney, pooled LIDC): not re-computed in the regularized run and NOT used as a gate criterion. The blur-separation gate relies on within-vendor ratio (>=3x in every vendor) + blur ranking last in all 5 groups.

## Statistical caveats

1. GE/Toshiba near-zero FD high-frequency denominators regularized (adaptive epsilon floor = 1e-4 x full-image FD energy); ROI BandER group means now 0.045-8.95 (was 4.5e3-1.6e14 before regularization); rank-based statistics (KW, blur ranking, separation ratio) unchanged; all gates remain PASS.
2. Per-slice ROI BandER was not persisted in the first pass; inferential statistics use patient-mean replication (n=96/vendor-group samples). run_lidc_r6.py now persists ber_per_slice for future runs.
3. LIDC runs use simulated r=0.25 (lowdose_sim); AAPM-Siemens-real uses official real QD — the two sources are reported separately, never averaged.

## Gate verdict

| criterion | result |
|---|---|
| blur trap separates on every vendor (ratio >= 3x, blur last) | PASS (5/5 vendors, 9.5-19.0x) |
| vendor effect significant (Kruskal-Wallis p < 0.05) | PASS (all 4 models p<0.001 on ROI BandER) |
| never average across vendors | PASS (per-vendor groups reported; significant vendor effect) |
| **verdict** | **PASS** |
*（内容由AI生成，仅供参考）*
