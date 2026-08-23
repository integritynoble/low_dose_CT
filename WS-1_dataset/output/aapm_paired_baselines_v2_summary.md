---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_10b60aeb9d9211f1a54f525400f8a581
    ReservedCode1: OyPSrW/gLhGMO7WTfsrPFcuu65JvxjL9dxAj3HG461whpEMdsC1PVwtFbnAP4MzCdZJNmQC5NjxjtdjdDwHudLat1ii4iIqn1XFtS+EQWpBO/atCdIlX1nXfCdhAU5+fYSO9pHp0jcTUSnDjK9cv1vBjbvUHeajuOhAMdeqmNqaP+AT62pgQ74ZOBj4=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_10b60aeb9d9211f1a54f525400f8a581
    ReservedCode2: OyPSrW/gLhGMO7WTfsrPFcuu65JvxjL9dxAj3HG461whpEMdsC1PVwtFbnAP4MzCdZJNmQC5NjxjtdjdDwHudLat1ii4iIqn1XFtS+EQWpBO/atCdIlX1nXfCdhAU5+fYSO9pHp0jcTUSnDjK9cv1vBjbvUHeajuOhAMdeqmNqaP+AT62pgQ74ZOBj4=
---

# AAPM Paired Baseline Results v2 (held-out test, Rung 1 closure)

- Corpus: AAPM 2016 10 training patients (1mm B30), FD vs QD geometric pairing Pearson=1.0; held-out test = aapm-0003, aapm-0005, aapm-0006, aapm-0009
- Task: SKE-Gaussian20HU-s2px (sigma=2.0px, contrast=20.0HU, location_known=True)
- Protocol: fidelity over all slices (PSNR/SSIM/LPIPS + band_energy_ratio 1px-band); detectability 48 slices x 24 trials/slice (CNR Rose>=3; CHO DOG-4; NPWE eye filter) + tm_auc template-match detection
- Updated: 2026-08-22T02:27:29

## test (per-patient mean ± [min,max], n patients)

| model | PSNR | SSIM | LPIPS | BandER | CNR | CHO AUC | TM-AUC | n |
|---|---|---|---|---|---|---|---|---|
| red_cnn | 40.6 [39.5,42.0] | 0.886 [0.860,0.931] | 0.089 [0.079,0.096] | 0.636 [0.600,0.693] | 0.17 [0.14,0.22] | 1.000 [1.000,1.000] | 0.990 [0.990,0.990] | 4 |
| ctformer | 39.5 [38.5,40.5] | 0.903 [0.882,0.923] | 0.061 [0.058,0.063] | 1.040 [0.888,1.276] | 0.11 [0.09,0.13] | 1.000 [1.000,1.000] | 0.990 [0.990,0.990] | 4 |
| learn | 41.0 [39.6,42.8] | 0.889 [0.864,0.932] | 0.087 [0.078,0.094] | 0.631 [0.600,0.686] | 0.17 [0.14,0.22] | 1.000 [1.000,1.000] | 0.990 [0.990,0.990] | 4 |
| blur | 39.5 [38.4,40.7] | 0.929 [0.909,0.952] | 0.166 [0.146,0.185] | 0.247 [0.215,0.307] | 0.26 [0.20,0.37] | 1.000 [1.000,1.000] | 0.990 [0.990,0.990] | 4 |

## Per-patient detail

### aapm-0003 (test, 636 slices)

| model | PSNR | SSIM | LPIPS | BandER | CNR | CHO AUC | TM-AUC |
|---|---|---|---|---|---|---|---|
| red_cnn | 39.51 | 0.8603 | 0.0956 | 0.600 | 0.14 | 1.000 | 0.990 |
| ctformer | 38.54 | 0.8825 | 0.0621 | 0.888 | 0.10 | 1.000 | 0.990 |
| learn | 39.60 | 0.8639 | 0.0940 | 0.600 | 0.14 | 1.000 | 0.990 |
| blur | 38.39 | 0.9093 | 0.1850 | 0.215 | 0.20 | 1.000 | 0.990 |

### aapm-0005 (test, 1200 slices)

| model | PSNR | SSIM | LPIPS | BandER | CNR | CHO AUC | TM-AUC |
|---|---|---|---|---|---|---|---|
| red_cnn | 40.79 | 0.8892 | 0.0852 | 0.638 | 0.17 | 1.000 | 0.990 |
| ctformer | 39.81 | 0.9104 | 0.0597 | 1.078 | 0.12 | 1.000 | 0.990 |
| learn | 41.29 | 0.8908 | 0.0831 | 0.632 | 0.17 | 1.000 | 0.990 |
| blur | 39.90 | 0.9369 | 0.1553 | 0.249 | 0.25 | 1.000 | 0.990 |

### aapm-0006 (test, 1050 slices)

| model | PSNR | SSIM | LPIPS | BandER | CNR | CHO AUC | TM-AUC |
|---|---|---|---|---|---|---|---|
| red_cnn | 41.97 | 0.9314 | 0.0786 | 0.693 | 0.22 | 1.000 | 0.990 |
| ctformer | 40.45 | 0.9226 | 0.0578 | 1.276 | 0.13 | 1.000 | 0.990 |
| learn | 42.78 | 0.9320 | 0.0779 | 0.686 | 0.22 | 1.000 | 0.990 |
| blur | 40.67 | 0.9520 | 0.1460 | 0.307 | 0.37 | 1.000 | 0.990 |

### aapm-0009 (test, 1220 slices)

| model | PSNR | SSIM | LPIPS | BandER | CNR | CHO AUC | TM-AUC |
|---|---|---|---|---|---|---|---|
| red_cnn | 40.11 | 0.8646 | 0.0957 | 0.612 | 0.14 | 1.000 | 0.990 |
| ctformer | 39.15 | 0.8953 | 0.0626 | 0.919 | 0.09 | 1.000 | 0.990 |
| learn | 40.25 | 0.8680 | 0.0926 | 0.606 | 0.14 | 1.000 | 0.990 |
| blur | 38.90 | 0.9194 | 0.1790 | 0.218 | 0.21 | 1.000 | 0.990 |
*（内容由AI生成，仅供参考）*
