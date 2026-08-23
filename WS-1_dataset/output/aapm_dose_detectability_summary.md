# AAPM Real Paired Dose-Detectability Curve (Rung 4, held-out test)

- Corpus: AAPM 2016 held-out test = aapm-0003, aapm-0005, aapm-0006, aapm-0009
- Dose points: r=0.25 official real QD; r=0.10 / r=0.50 lowdose_sim projection-domain (Eq. 1, seed 42)
- Detectability: freq-ROI protocol (ROI BandER, 1px HF band retention inside tissue ROI patch, 48 slices/patient)
- Fidelity: PSNR/SSIM over all paired slices; CNR/CHO/NPWE reported as transparency
- Detectability knee = dose ratio where ROI BandER first reaches tau=0.5 (linear interpolation)
- Updated: 2026-08-22T21:18:06

## test aggregate (per-patient mean over 4 patients)

| model | r=0.10 PSNR | r=0.25 PSNR | r=0.50 PSNR | r=0.10 ROI-BER | r=0.25 ROI-BER | r=0.50 ROI-BER | knee(BER=0.50) | CNR(0.25) | Rose-cross |
|---|---|---|---|---|---|---|---|---|---|
| red_cnn | n/a | n/a | n/a | n/a | n/a | n/a | 0.500 | 0.11 | not_reached |
| ctformer | n/a | n/a | n/a | n/a | n/a | n/a | 0.500 | 0.09 | not_reached |
| learn | n/a | n/a | n/a | n/a | n/a | n/a | 0.500 | 0.11 | not_reached |
| blur | n/a | n/a | n/a | n/a | n/a | n/a | not_reached | 0.17 | not_reached |

## Per-patient detail

### aapm-0003 (636 slices)

| dose | model | PSNR | SSIM | ROI BandER | full BandER | TM-AUC | CNR | CHO AUC |
|---|---|---|---|---|---|---|---|---|
| sim_r010 | red_cnn | 44.37 | 0.9639 | 2.743 | 1.428 | 0.990 | 0.11 | 1.000 |
| sim_r010 | ctformer | 41.01 | 0.9313 | 4.517 | 1.982 | 0.990 | 0.09 | 1.000 |
| sim_r010 | learn | 44.59 | 0.9639 | 2.758 | 1.434 | 0.990 | 0.11 | 1.000 |
| sim_r010 | blur | 42.03 | 0.9678 | 0.199 | 0.360 | 0.990 | 0.25 | 1.000 |
| real_r025 | red_cnn | 40.06 | 0.9171 | 3.492 | 1.586 | 0.990 | 0.08 | 1.000 |
| real_r025 | ctformer | 38.60 | 0.8946 | 5.116 | 2.112 | 0.990 | 0.07 | 1.000 |
| real_r025 | learn | 40.14 | 0.9194 | 3.479 | 1.584 | 0.990 | 0.08 | 1.000 |
| real_r025 | blur | 40.71 | 0.9537 | 0.352 | 0.394 | 0.990 | 0.15 | 1.000 |
| sim_r050 | red_cnn | 49.87 | 0.9891 | 1.264 | 1.067 | 0.990 | 0.14 | 1.000 |
| sim_r050 | ctformer | 43.19 | 0.9561 | 2.657 | 1.569 | 0.990 | 0.11 | 1.000 |
| sim_r050 | learn | 50.81 | 0.9890 | 1.260 | 1.066 | 0.990 | 0.14 | 1.000 |
| sim_r050 | blur | 42.25 | 0.9711 | 0.157 | 0.350 | 0.990 | 0.29 | 1.000 |

### aapm-0005 (1200 slices)

| dose | model | PSNR | SSIM | ROI BandER | full BandER | TM-AUC | CNR | CHO AUC |
|---|---|---|---|---|---|---|---|---|
| sim_r010 | red_cnn | 42.27 | 0.9500 | 7.599 | 2.036 | 0.990 | 0.11 | 1.000 |
| sim_r010 | ctformer | 40.06 | 0.9181 | 11.609 | 2.948 | 0.990 | 0.09 | 1.000 |
| sim_r010 | learn | 43.09 | 0.9498 | 7.714 | 2.045 | 0.990 | 0.11 | 1.000 |
| sim_r010 | blur | 43.15 | 0.9787 | 0.370 | 0.415 | 0.990 | 0.22 | 1.000 |
| real_r025 | red_cnn | 41.42 | 0.9361 | 3.433 | 1.516 | 0.990 | 0.12 | 1.000 |
| real_r025 | ctformer | 39.92 | 0.9183 | 5.971 | 2.250 | 0.990 | 0.10 | 1.000 |
| real_r025 | learn | 42.00 | 0.9379 | 3.408 | 1.506 | 0.990 | 0.12 | 1.000 |
| real_r025 | blur | 42.12 | 0.9693 | 0.457 | 0.439 | 0.990 | 0.19 | 1.000 |
| sim_r050 | red_cnn | 46.96 | 0.9853 | 1.996 | 1.176 | 0.990 | 0.16 | 1.000 |
| sim_r050 | ctformer | 42.87 | 0.9537 | 4.558 | 1.921 | 0.990 | 0.12 | 1.000 |
| sim_r050 | learn | 49.61 | 0.9829 | 2.003 | 1.168 | 0.990 | 0.16 | 1.000 |
| sim_r050 | blur | 43.57 | 0.9827 | 0.223 | 0.391 | 0.990 | 0.28 | 1.000 |

### aapm-0006 (1050 slices)

| dose | model | PSNR | SSIM | ROI BandER | full BandER | TM-AUC | CNR | CHO AUC |
|---|---|---|---|---|---|---|---|---|
| sim_r010 | red_cnn | 39.36 | 0.9114 | 17.579 | 3.417 | 0.990 | 0.08 | 1.000 |
| sim_r010 | ctformer | 37.85 | 0.8749 | 26.214 | 4.746 | 0.990 | 0.07 | 1.000 |
| sim_r010 | learn | 39.76 | 0.9116 | 17.896 | 3.455 | 0.990 | 0.08 | 1.000 |
| sim_r010 | blur | 42.92 | 0.9788 | 0.631 | 0.510 | 0.990 | 0.19 | 1.000 |
| real_r025 | red_cnn | 42.33 | 0.9533 | 4.059 | 1.421 | 0.990 | 0.12 | 1.000 |
| real_r025 | ctformer | 40.48 | 0.9269 | 8.668 | 2.304 | 0.990 | 0.10 | 1.000 |
| real_r025 | learn | 43.17 | 0.9543 | 4.013 | 1.407 | 0.990 | 0.12 | 1.000 |
| real_r025 | blur | 42.48 | 0.9769 | 0.523 | 0.492 | 0.990 | 0.18 | 1.000 |
| sim_r050 | red_cnn | 45.12 | 0.9780 | 3.796 | 1.420 | 0.990 | 0.13 | 1.000 |
| sim_r050 | ctformer | 41.90 | 0.9434 | 8.952 | 2.367 | 0.990 | 0.10 | 1.000 |
| sim_r050 | learn | 47.03 | 0.9783 | 3.828 | 1.413 | 0.990 | 0.13 | 1.000 |
| sim_r050 | blur | 43.71 | 0.9865 | 0.228 | 0.456 | 0.990 | 0.26 | 1.000 |

### aapm-0009 (1220 slices)

| dose | model | PSNR | SSIM | ROI BandER | full BandER | TM-AUC | CNR | CHO AUC |
|---|---|---|---|---|---|---|---|---|
| sim_r010 | red_cnn | 44.20 | 0.9638 | 4.735 | 1.493 | 0.990 | 0.12 | 1.000 |
| sim_r010 | ctformer | 41.00 | 0.9302 | 8.088 | 2.099 | 0.990 | 0.09 | 1.000 |
| sim_r010 | learn | 44.53 | 0.9632 | 4.789 | 1.490 | 0.990 | 0.12 | 1.000 |
| sim_r010 | blur | 42.39 | 0.9711 | 0.213 | 0.365 | 0.990 | 0.22 | 1.000 |
| real_r025 | red_cnn | 40.88 | 0.9286 | 4.521 | 1.572 | 0.990 | 0.10 | 1.000 |
| real_r025 | ctformer | 39.27 | 0.9067 | 7.186 | 2.121 | 0.990 | 0.08 | 1.000 |
| real_r025 | learn | 41.01 | 0.9308 | 4.516 | 1.560 | 0.990 | 0.10 | 1.000 |
| real_r025 | blur | 41.31 | 0.9617 | 0.394 | 0.395 | 0.990 | 0.18 | 1.000 |
| sim_r050 | red_cnn | 49.62 | 0.9891 | 1.594 | 1.083 | 0.990 | 0.15 | 1.000 |
| sim_r050 | ctformer | 43.24 | 0.9551 | 4.002 | 1.617 | 0.990 | 0.10 | 1.000 |
| sim_r050 | learn | 50.85 | 0.9878 | 1.595 | 1.073 | 0.990 | 0.15 | 1.000 |
| sim_r050 | blur | 42.62 | 0.9741 | 0.123 | 0.353 | 0.990 | 0.25 | 1.000 |
