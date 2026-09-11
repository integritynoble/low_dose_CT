---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_460e38549e8a11f1a54f525400f8a581
    ReservedCode1: hIzvoleRRfiJiVH4QS0cAOMtxwXWlgsLPhGPrjoSCoGdcZ1XJ0gx73KfEyP2kBitQ8U1wBlOBqJ853sJuymyMYmtM+6Syh/GvBLdTvMZ1yvDLjbA4adNYl4CSZUWrzgRs26IcbPcobcMRv2rFl4bGPX3uCqwjYmzpSgTc4PtBowqdMeHTwqAzemShMY=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_460e38549e8a11f1a54f525400f8a581
    ReservedCode2: hIzvoleRRfiJiVH4QS0cAOMtxwXWlgsLPhGPrjoSCoGdcZ1XJ0gx73KfEyP2kBitQ8U1wBlOBqJ853sJuymyMYmtM+6Syh/GvBLdTvMZ1yvDLjbA4adNYl4CSZUWrzgRs26IcbPcobcMRv2rFl4bGPX3uCqwjYmzpSgTc4PtBowqdMeHTwqAzemShMY=
---

# AAPM Observer Sensitivity on Real Tissue (held-out test)

- Corpus: AAPM 2016 test = aapm-0003/0005/0006/0009 (FD/QD real pairing)
- Metric: per-slice ROI BandER (detectability-freq-v1), R3 noise-ROI protocol, 32x32, seed 42
- Observer model: slice-level bootstrap + paired binomial rank-flip test + random-subset stability
- Updated: 2026-08-22T21:52:16

## Per-slice ROI BandER (all test slices)
| model | n_slices | mean | std |
|---|---|---|---|
| red_cnn | 192 | 3.876 | 0.965 |
| ctformer | 192 | 6.735 | 2.085 |
| learn | 192 | 3.854 | 0.957 |
| blur | 192 | 0.432 | 0.102 |

## Bootstrap ranking stability (n_bootstrap=4000, blur-last = worst detectability)
- P(blur ranks last) = **1.0000**
- blur rank-sum over 4000 draws = 16000 (min possible 4000, max 16000)

## Paired binomial rank-flip (blur vs each baseline, aligned slices)
| baseline | aligned slices | blur-lower frac | sign-test p (greater) |
|---|---|---|---|
| red_cnn | 192 | 1.0000 | 1.593e-58 |
| ctformer | 192 | 1.0000 | 1.593e-58 |
| learn | 192 | 1.0000 | 1.593e-58 |

## Observers needed for stable separation (random-subset ranking)
| k observers | slices/observer | P(blur last) |
|---|---|---|
| 1 | 192 | 1.0000 |
| 2 | 96 | 1.0000 |
| 4 | 48 | 1.0000 |
| 8 | 24 | 1.0000 |
| 16 | 12 | 1.0000 |
| 32 | 6 | 1.0000 |

- **Min k for >=95% stable blur-last separation: 1**

## Method notes
- Slice-level bootstrap approximates observer variance (no true multi-observer readings)
- Binomial sign tests assume slice independence; within-patient correlation makes p conservative
- blur ranks last in detectability iff its mean ROI BandER is the lowest (least high-frequency retention)
- n observers needed = smallest k with >=95% of k-subset rankings placing blur last

## Comparison vs synthetic version (WS-4 observer_sensitivity.py)
- Synthetic: channel-response perturbation on CHO observer channels, rank shifts estimated from synthetic noise
- Real: actual per-slice ROI BandER on AAPM paired tissue; ranking stability under slice-level observer variance
