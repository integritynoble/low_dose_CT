# AAPM R3: Noise-ROI Detectability on Real Tissue Volumes (held-out test)

- Corpus: AAPM 2016 held-out test = aapm-0003, aapm-0005, aapm-0006, aapm-0009 (1mm B30, FD vs QD real pairing)
- Task: SKE-Gaussian20HU-s2px (sigma=2.0px, contrast=20.0HU, location_known=True)
- ROI protocol: find_tissue_roi per slice (HU band [10,120] + low Sobel gradient + low std, seed 42, 32x32px) on FD reference
- Freq protocol: detectability-freq-v1 (1px high-pass residual): roi BandER + full-image BandER + roi tm_auc
- Transparency: CNR/CHO/NPWE insertion protocol (v2-comparable, first-slice ROI reuse)
- Updated: 2026-08-22T19:36:01

## test aggregate (per-patient mean ± [min,max])

| model | PSNR | SSIM | ROI BandER | full BandER | ROI TM-AUC | CNR | CHO AUC | NPWE | n_roi/pat |
|---|---|---|---|---|---|---|---|---|---|
| red_cnn | 41.2 [40.1,42.4] | 0.934 [0.918,0.953] | 3.876 [3.433,4.521] | 1.524 [1.421,1.586] | 0.990 [0.990,0.990] | 0.10 [0.09,0.13] | 1.000 [1.000,1.000] | 223914.780 [223766.064,224051.984] | 48 |
| ctformer | 39.6 [38.6,40.5] | 0.912 [0.895,0.928] | 6.735 [5.116,8.668] | 2.197 [2.112,2.304] | 0.990 [0.990,0.990] | 0.09 [0.08,0.10] | 1.000 [1.000,1.000] | 222908.326 [222330.448,223212.217] | 48 |
| learn | 41.6 [40.2,43.3] | 0.936 [0.920,0.954] | 3.854 [3.408,4.516] | 1.514 [1.407,1.584] | 0.990 [0.990,0.990] | 0.10 [0.09,0.13] | 1.000 [1.000,1.000] | 222629.693 [222379.920,223207.770] | 48 |
| blur | 41.6 [40.7,42.5] | 0.965 [0.954,0.977] | 0.432 [0.352,0.523] | 0.430 [0.394,0.492] | 0.990 [0.990,0.990] | 0.17 [0.15,0.21] | 1.000 [1.000,1.000] | 220804.563 [220803.965,220805.266] | 48 |

ROI protocol compliance (mean over selected ROIs per patient):
- red_cnn: ROI HU mean=56.6 (band [10,120]), ROI HU std=56.8, ROI gradient mean=179.00
- ctformer: ROI HU mean=56.6 (band [10,120]), ROI HU std=56.8, ROI gradient mean=179.00
- learn: ROI HU mean=56.6 (band [10,120]), ROI HU std=56.8, ROI gradient mean=179.00
- blur: ROI HU mean=56.6 (band [10,120]), ROI HU std=56.8, ROI gradient mean=179.00

## Per-patient detail

### aapm-0003 (636 slices)

| model | PSNR | SSIM | ROI BandER | full BandER | ROI TM-AUC | CNR | CHO AUC | NPWE | n_roi |
|---|---|---|---|---|---|---|---|---|---|
| red_cnn | 40.12 | 0.9179 | 3.492 | 1.586 | 0.990 | 0.09 | 1.000 | 223882.400 | 48 |
| ctformer | 38.65 | 0.8955 | 5.116 | 2.112 | 0.990 | 0.08 | 1.000 | 222903.769 | 48 |
| learn | 40.21 | 0.9202 | 3.479 | 1.584 | 0.990 | 0.09 | 1.000 | 222503.736 | 48 |
| blur | 40.69 | 0.9539 | 0.352 | 0.394 | 0.990 | 0.17 | 1.000 | 220805.266 | 48 |

### aapm-0005 (1200 slices)

| model | PSNR | SSIM | ROI BandER | full BandER | ROI TM-AUC | CNR | CHO AUC | NPWE | n_roi |
|---|---|---|---|---|---|---|---|---|---|
| red_cnn | 41.41 | 0.9361 | 3.433 | 1.516 | 0.990 | 0.11 | 1.000 | 223766.064 | 48 |
| ctformer | 39.91 | 0.9181 | 5.971 | 2.250 | 0.990 | 0.09 | 1.000 | 223186.871 | 48 |
| learn | 41.98 | 0.9379 | 3.408 | 1.506 | 0.990 | 0.11 | 1.000 | 222379.920 | 48 |
| blur | 42.09 | 0.9691 | 0.457 | 0.439 | 0.990 | 0.16 | 1.000 | 220803.965 | 48 |

### aapm-0006 (1050 slices)

| model | PSNR | SSIM | ROI BandER | full BandER | ROI TM-AUC | CNR | CHO AUC | NPWE | n_roi |
|---|---|---|---|---|---|---|---|---|---|
| red_cnn | 42.41 | 0.9532 | 4.059 | 1.421 | 0.990 | 0.13 | 1.000 | 224051.984 | 48 |
| ctformer | 40.52 | 0.9275 | 8.668 | 2.304 | 0.990 | 0.10 | 1.000 | 223212.217 | 48 |
| learn | 43.27 | 0.9543 | 4.013 | 1.407 | 0.990 | 0.13 | 1.000 | 222427.346 | 48 |
| blur | 42.46 | 0.9769 | 0.523 | 0.492 | 0.990 | 0.21 | 1.000 | 220804.278 | 48 |

### aapm-0009 (1220 slices)

| model | PSNR | SSIM | ROI BandER | full BandER | ROI TM-AUC | CNR | CHO AUC | NPWE | n_roi |
|---|---|---|---|---|---|---|---|---|---|
| red_cnn | 40.86 | 0.9287 | 4.521 | 1.572 | 0.990 | 0.09 | 1.000 | 223958.672 | 48 |
| ctformer | 39.26 | 0.9068 | 7.186 | 2.121 | 0.990 | 0.08 | 1.000 | 222330.448 | 48 |
| learn | 40.99 | 0.9309 | 4.516 | 1.560 | 0.990 | 0.09 | 1.000 | 223207.770 | 48 |
| blur | 41.27 | 0.9614 | 0.394 | 0.395 | 0.990 | 0.15 | 1.000 | 220804.744 | 48 |
