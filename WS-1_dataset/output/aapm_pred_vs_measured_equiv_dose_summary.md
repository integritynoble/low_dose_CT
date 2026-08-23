# WS-2 P2-3: Predicted vs Measured Equivalent-Dose Error (AAPM real paired data)

- Corpus: AAPM 2016 held-out test = aapm-0003, aapm-0005, aapm-0006, aapm-0009 (FD vs official real QD, r=0.25)
- Metric: Δr = |r̂ − r*| / r*  (predicted_vs_measured_dose.md, P2-3)
- Physical dose-response: input-image SSIM/PSNR/ROI-BandER (no restoration) at r=0.10/0.25/0.50/1.0, 48-slice subset per patient
- r* (measured equivalent dose) = QD acquisition performance through the physical curve; verified == 0.25 (official reference)
- r̂ (predicted equivalent dose) = model restored-output performance (on QD input, R4 reused) through the same curve
- Equivalent-dose channels: SSIM (anchor r=1.0→1.0) / PSNR (high end clamped at r=0.50)
- Detectability contrast channel: ε_BandER = |BandER_pred − BandER_QD_phys| / BandER_QD_phys (physical BandER is noise-HF-dominated and non-monotone, so it cannot map to dose; used as contrast to expose blur)
- Organization: per volume (per patient per model); R3/R4 persisted only per-patient ROI BandER means
- Updated: 2026-08-22T12:14:51

## Per-model results (test aggregate, per-patient mean ± std)

| model | output SSIM | r̂_SSIM | Δr_SSIM | r̂_PSNR | Δr_PSNR | output BandER | ε_BandER |
|---|---|---|---|---|---|---|---|
| red_cnn | 0.9338±0.0131 | 0.189±0.098 | 0.258±0.382 | 0.181±0.091 | 0.275±0.363 | 3.876±0.446 | 0.096±0.010 |
| ctformer | 0.9116±0.0121 | 0.227±0.144 | 0.531±0.244 | 0.202±0.123 | 0.445±0.282 | 6.735±1.336 | 0.568±0.239 |
| learn | 0.9356±0.0127 | 0.184±0.095 | 0.263±0.380 | 0.247±0.015 | 0.060±0.016 | 3.854±0.448 | 0.101±0.007 |
| blur | 0.9654±0.0086 | 0.349±0.148 | 0.693±0.171 | 0.230±0.022 | 0.109±0.047 | 0.432±0.065 | 0.898±0.018 |

## Blur trap identification

- ε_BandER (detectability contrast): blur = 0.898 vs red_cnn = 0.096, ctformer = 0.568, learn = 0.101
- Δr_SSIM (fidelity channel): blur = 0.693 — small, blur's high SSIM masks its detectability failure (pseudo-low error)
- Detectability channel identifies blur: True
- Fidelity mask observed: True (blur Δr_SSIM < ε_BandER)

## Why ROI BandER cannot be a physical dose-response scale

Physical input BandER = 1 + HF_noise/HF_fd in the ROI; low-dose noise is broadband high-frequency, so BandER *rises* as dose decreases (e.g. aapm-0003: r=0.10→3.28, r=0.25→3.87, r=0.50→1.44, r=1.0→1.0) and the curve is non-monotone. Dose mapping is therefore ill-posed for BandER; it is reported only as a contrast channel against the QD physical reference.

## Metric definition (from predicted_vs_measured_dose.md)

- Δr = |r̂ − r*| / r*: relative deviation between predicted and measured equivalent-dose level
- r* = measured equivalent dose: physical acquisition performance mapped back through the physical dose-response curve
- r̂ = predicted equivalent dose: twin/model predicted performance mapped back through the same curve
- Acceptance gate: credential equivalence verdict must be stable under ±Δr perturbation of the operating point

## Per-patient detail

### aapm-0003 (r*: SSIM=0.250, PSNR=0.250, official=0.25; QD physical BandER ref=3.869)

| model | output SSIM | r̂_SSIM | Δr_SSIM | r̂_PSNR | Δr_PSNR | output BandER | ε_BandER |
|---|---|---|---|---|---|---|---|
| red_cnn | 0.9171 | 0.243 | 0.028 | 0.235 | 0.059 | 3.492 | 0.097 |
| ctformer | 0.8946 | 0.330 | 0.319 | 0.295 | 0.182 | 5.116 | 0.322 |
| learn | 0.9194 | 0.234 | 0.062 | 0.232 | 0.073 | 3.479 | 0.101 |
| blur | 0.9537 | 0.102 | 0.591 | 0.208 | 0.166 | 0.352 | 0.909 |

### aapm-0005 (r*: SSIM=0.250, PSNR=0.250, official=0.25; QD physical BandER ref=3.759)

| model | output SSIM | r̂_SSIM | Δr_SSIM | r̂_PSNR | Δr_PSNR | output BandER | ε_BandER |
|---|---|---|---|---|---|---|---|
| red_cnn | 0.9361 | 0.020 | 0.920 | 0.024 | 0.904 | 3.433 | 0.087 |
| ctformer | 0.9183 | 0.020 | 0.920 | 0.020 | 0.920 | 5.971 | 0.589 |
| learn | 0.9379 | 0.020 | 0.920 | 0.259 | 0.036 | 3.408 | 0.093 |
| blur | 0.9693 | 0.399 | 0.595 | 0.264 | 0.054 | 0.457 | 0.879 |

### aapm-0006 (r*: SSIM=0.250, PSNR=0.250, official=0.25; QD physical BandER ref=4.450)

| model | output SSIM | r̂_SSIM | Δr_SSIM | r̂_PSNR | Δr_PSNR | output BandER | ε_BandER |
|---|---|---|---|---|---|---|---|
| red_cnn | 0.9533 | 0.236 | 0.057 | 0.227 | 0.093 | 4.059 | 0.088 |
| ctformer | 0.9269 | 0.168 | 0.329 | 0.162 | 0.350 | 8.668 | 0.948 |
| learn | 0.9543 | 0.239 | 0.046 | 0.264 | 0.057 | 4.013 | 0.098 |
| blur | 0.9769 | 0.498 | 0.990 | 0.232 | 0.072 | 0.523 | 0.882 |

### aapm-0009 (r*: SSIM=0.250, PSNR=0.250, official=0.25; QD physical BandER ref=5.086)

| model | output SSIM | r̂_SSIM | Δr_SSIM | r̂_PSNR | Δr_PSNR | output BandER | ε_BandER |
|---|---|---|---|---|---|---|---|
| red_cnn | 0.9286 | 0.257 | 0.029 | 0.239 | 0.046 | 4.521 | 0.111 |
| ctformer | 0.9067 | 0.389 | 0.558 | 0.332 | 0.327 | 7.186 | 0.413 |
| learn | 0.9308 | 0.244 | 0.024 | 0.231 | 0.075 | 4.516 | 0.112 |
| blur | 0.9617 | 0.399 | 0.597 | 0.214 | 0.144 | 0.394 | 0.922 |
