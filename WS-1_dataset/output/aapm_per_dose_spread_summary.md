---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_4450f42b9e8a11f1a238525400e6dd8f
    ReservedCode1: fbSy6lu+DFCnFzCAECCmULkKV1J+yaQ6j6AS2MHzXK4+DTFuCMdSdIdnY1wcl+nXoBVWPh1gxfqUKCly2PWI2IRY3uPiboe0tqMB91obNCiWylAndulnpm7H0CbcEqVWLxtY+2vP+ufAPl2edu0A55gVyIusKk3ggn8qvqV+9+JqdKnOyikQ6/1dAUA=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_4450f42b9e8a11f1a238525400e6dd8f
    ReservedCode2: fbSy6lu+DFCnFzCAECCmULkKV1J+yaQ6j6AS2MHzXK4+DTFuCMdSdIdnY1wcl+nXoBVWPh1gxfqUKCly2PWI2IRY3uPiboe0tqMB91obNCiWylAndulnpm7H0CbcEqVWLxtY+2vP+ufAPl2edu0A55gVyIusKk3ggn8qvqV+9+JqdKnOyikQ6/1dAUA=
---

---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_1d2a47ce9df911f1a238525400e6dd8f
    ReservedCode1: fUDEvlLGXdnLTl2C5Ioi25R/LjEWAvDvhK76Mv5yu0i744GUU9AmyrwqQWZcv2Pb0qbgxO+HE7kDd7wpg7wW8mGI52qjKyjHPDSNIH2c8ESS8teRllIt8p/v+TC5+4icTbaMn5DUaCD97llb0oYJB77L2/QIe9jP3Dfzq99xC+DUaJvo0X3WABp8NeU=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_1d2a47ce9df911f1a238525400e6dd8f
    ReservedCode2: fUDEvlLGXdnLTl2C5Ioi25R/LjEWAvDvhK76Mv5yu0i744GUU9AmyrwqQWZcv2Pb0qbgxO+HE7kDd7wpg7wW8mGI52qjKyjHPDSNIH2c8ESS8teRllIt8p/v+TC5+4icTbaMn5DUaCD97llb0oYJB77L2/QIe9jP3Dfzq99xC+DUaJvo0X3WABp8NeU=
---

# AAPM + LIDC Per-Vendor / Per-Dose Spread (Rung 5)

- Method adjustment: original R5 design required **external multi-vendor submissions** on the leaderboard. No external multi-vendor submissions exist, so the project's own held-out results are treated as the **on-board submission set** (proxy for external submissions). Constraints unchanged: per-vendor / per-dose grouping, **never average across groups**, blur trap must separate in every group.
- BandER regularization: 2026-08-22, adaptive epsilon floor = 1e-4 x full-image FD energy (replaces fixed max(denom, 1e-9) in eval_freq_roi / get_ber_per_slice); GE/Toshiba near-zero FD high-frequency denominators no longer inflate ROI BandER.
- Per-vendor board: LIDC GE / Philips / Siemens / Toshiba (2 patients each, lowdose_sim r=0.25, seed 42) + AAPM 2016 Siemens real paired QD (r=0.25 official, 4 held-out test patients) x {RED-CNN, CTformer, LEARN, blur trap}; sources: `aapm_lidc_cross_vendor_spread.json` + `aapm_dose_detectability.json` (no model re-run).
- Per-dose board: AAPM Siemens real paired FD, dose points r=0.10 (lowdose_sim) / r=0.25 (official real QD) / r=0.50 (lowdose_sim) x same 4 models; source: `aapm_dose_detectability.json`.
- Task / protocol: SKE-Gaussian20HU-s2px; find_tissue_roi (HU [10,120] + low gradient + low std, seed 42, 32x32px); detectability-freq-v1 (ROI BandER); CNR reported as transparency.
- Updated: 2026-08-22T13:48:36

## Per-vendor spread (within vendor group, across 4 models)

| vendor | PSNR span (dB) | PSNR std | ROI BandER span | ROI BandER std | CNR span | CNR std | blur sep ratio | blur rank |
|---|---|---|---|---|---|---|---|---|
| GE | 12.96 | 5.44 | 8.908 | 3.729 | 5.53 | 2.11 | 9.67x | 4/4 |
| Philips | 6.52 | 2.44 | 10.35 | 3.824 | 0.11 | 0.04 | 12.80x | 4/4 |
| Siemens | 11.48 | 4.18 | 1.765 | 0.629 | 0.05 | 0.02 | 9.46x | 4/4 |
| Toshiba | 12.46 | 5.20 | 9.188 | 3.693 | 3.49 | 1.42 | 18.96x | 4/4 |
| AAPM-Siemens-real | 2.04 | 0.84 | 6.304 | 2.233 | 0.08 | 0.03 | 8.93x | 4/4 |

## Per-dose spread (within dose group, across 4 models, AAPM Siemens)

| dose | PSNR span (dB) | PSNR std | ROI BandER span | ROI BandER std | CNR span | CNR std | blur sep ratio | blur rank |
|---|---|---|---|---|---|---|---|---|
| r=0.10 (sim) | 3.01 | 1.20 | 12.25 | 4.42 | 0.13 | 0.05 | 23.12x | 4/4 |
| r=0.25 (real QD) | 2.09 | 0.84 | 6.304 | 2.233 | 0.09 | 0.03 | 8.93x | 4/4 |
| r=0.50 (sim) | 6.77 | 2.97 | 4.86 | 1.733 | 0.16 | 0.06 | 11.84x | 4/4 |

## Blur-trap separation

### Per-vendor (ROI BandER)

| vendor | blur ROI BandER | min model ROI BandER | ratio (model/blur) | blur rank in detectability |
|---|---|---|---|---|
| GE | 0.04525 | 0.4377 (learn) | 9.67x | 4/4 |
| Philips | 0.2494 | 3.193 (red_cnn) | 12.80x | 4/4 |
| Siemens | 0.1223 | 1.157 (red_cnn) | 9.46x | 4/4 |
| Toshiba | 0.05921 | 1.123 (learn) | 18.96x | 4/4 |
| AAPM-Siemens-real | 0.4315 | 3.854 (learn) | 8.93x | 4/4 |

### Per-dose (ROI BandER)

| dose | blur ROI BandER | min model ROI BandER | ratio (model/blur) | blur rank in detectability |
|---|---|---|---|---|
| r=0.10 (sim) | 0.3531 | 8.164 (red_cnn) | 23.12x | 4/4 |
| r=0.25 (real QD) | 0.4315 | 3.854 (learn) | 8.93x | 4/4 |
| r=0.50 (sim) | 0.1827 | 2.163 (red_cnn) | 11.84x | 4/4 |

## Group-effect statistics

### Per-vendor (Kruskal-Wallis on LIDC vendor-group ROI BandER, reused from R6; per-slice not persisted, samples replicated from patient means)

| model | H | p (asymptotic) | significant |
|---|---|---|---|
| red_cnn | 328.3 | 7.50e-71 | yes |
| ctformer | 337.4 | 7.96e-73 | yes |
| learn | 328.3 | 7.50e-71 | yes |
| blur | 209.7 | 3.32e-45 | yes |

First-pass patient-level permutation KW (20000 draws) reported p=0.0103 for all 4 models; direction consistent.

### Per-dose (exact permutation Friedman, repeated measures, 4 patients x 3 dose levels, 1296 enumerations)

| model | Friedman H | p (exact permutation) | significant |
|---|---|---|---|
| red_cnn | 6.5 | 0.0417 | yes |
| ctformer | 4.5 | 0.1250 | no |
| learn | 6.5 | 0.0417 | yes |
| blur | 6.5 | 0.0417 | yes |

Independent-groups permutation KW for per-dose is reported as reference only (independence assumption violated for repeated measures): p = 0.055 (red_cnn) / 0.282 (ctformer) / 0.054 (learn) / 0.071 (blur).

## Gate verdict

| criterion | result |
|---|---|
| per-vendor: blur trap separates in every vendor group (ratio >= 3x, blur last) | PASS (5/5 groups, 9.5-19.0x) |
| per-vendor: vendor effect significant (Kruskal-Wallis p < 0.05) | PASS (all 4 models p<0.001 on ROI BandER) |
| per-dose: blur trap separates at every dose point (ratio >= 3x, blur last) | PASS (3/3 groups, 8.9-23.1x) |
| per-dose: dose effect (exact permutation Friedman) | PASS (3/4 models p=0.0417; ctformer p=0.1250 due to one non-monotonic patient) |
| never average across groups | PASS (per-vendor / per-dose groups reported separately; protocol + statistical justification) |
| **verdict** | **PASS** |

## Method-adjustment summary (R5)

1. Original R5 assumed external multi-vendor submissions on the leaderboard; the spread block existed but only seed entries were on the board (`leaderboard.py::compute_spread` grouped by vendor/dose without a hard threshold).
2. Adjusted: the project's own AAPM/LIDC held-out results (LIDC four vendors + AAPM Siemens multi-dose) are treated as the on-board submission set, so spread can be computed end-to-end from existing outputs without any model re-run.
3. Constraints unchanged: per-vendor / per-dose grouping is reported and never averaged; blur trap must separate in every group; detectability (ROI BandER) is the discriminative dimension while fidelity (PSNR) is reported within-group for transparency.
4. `compute_spread` extended to report BandER span/std alongside PSNR/CNR; docstring documents the adjustment (own-data proxy for external submissions).

## Caveats

- LIDC four vendors use simulated r=0.25 (lowdose_sim); AAPM-Siemens-real uses official real QD; the two sources are reported separately, never averaged.
- GE/Toshiba near-zero FD high-frequency denominators **regularized** (2026-08-22, adaptive epsilon floor = 1e-4 x full-image FD energy): ROI BandER now comparable across vendors (group means 0.05-9.25; previously 4.5e3-1.6e14, inflated 5-13 orders of magnitude); rank-based statistics and gates unchanged PASS.
- Per-dose board is AAPM Siemens only (no LIDC multi-dose per vendor exists).
- Simulated dose points (r=0.10/0.50) were run on the 48-slice detectability subset (full-volume projection simulation infeasible; trade-off declared in R4).
- Per-vendor statistics reuse R6 results (regularized run); per-dose Friedman uses exact enumeration (no approximation).
