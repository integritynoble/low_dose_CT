# PWM-PET-IQ 1.0 — Technical-Validation analysis

These scripts compute every numeric endpoint in the manuscript's Technical Validation
section against the physical ground truth (`ground_truth.json`). The design deliberately
splits the **image-dependent** step from the **arithmetic**, so the arithmetic is proven
correct now, before any phantom scan exists.

| Stage | File | Status |
|---|---|---|
| NEMA metric math (CRC, background variability, CNR, Bland–Altman, replicate variance) | `nema_metrics.py` | **complete + unit-tested** |
| Per-level / decayed-vs-thinned tables from ROI means | `analyze_phantom.py` | **complete + tested** |
| ROI-mean extraction from reconstructed volumes | `extract_roi_means.py` | **stub — acquisition-gated** (VOI localization) |

## Manuscript tables/figures fed by this

- `tab:crc` ← `analyze_phantom.py` per-level CRC
- `fig:cnr_vs_count` ← per-level background variability + CNR
- `fig:decayed_vs_thinned` ← `analyze_phantom.decayed_vs_thinned` (the central validation)
- `tab:reproducibility` ← `nema_metrics.across_realization_stats`

## Run (once ROI means are extracted)

```bash
python analyze_phantom.py --roi-means roi_means.json --out tables
# -> tables/image_quality.json + tables/image_quality.tex
```

`roi_means.json` is produced by `extract_roi_means.py` from the reconstructed volumes.
The metric math over those means is finished; the **only** unimplemented piece is spatial
VOI placement (finding the sphere centres and NEMA's 12×5 background ROIs in each volume),
which cannot exist until the scans do. `extract_roi_means.py` raises `NotImplementedError`
with the exact NEMA placement recipe rather than fabricating any ROI mean.

## Proof it works now

`test_nema_metrics.py` verifies every formula on hand-computed inputs (e.g. a hot sphere at
4:1 fill recovering to 100 %, an 80 % partial recovery, Bland–Altman bias/limits), and runs
`analyze_phantom.py` end-to-end over `fixtures/roi_means.json`:

```bash
python -m pytest test_nema_metrics.py -q     # 6 passed
```

The fixture is synthetic and asserts no dataset fact; it pins the arithmetic so that when
real ROI means arrive, the Technical-Validation tables regenerate deterministically.
