# CTformer Retraining Report (2026-08-28)

> **[superseded 2026-08-31]** 本文档为 CTformer 重训当日的 n=30 子集快照（CNR 0.52/0.98/1.44、未达 Rose）；全量 n=764 sweep 后 CTformer（重训版）CNR 为 2.57/4.61/6.86，r025 起越过 Rose、knee 0.131 [0.128, 0.135]，见手稿 tab:detectability_v05 / tab:lidc_sim_knee_ci。以下为历史记录，保留供追溯。

## 1. Problem

The official-patch CTformer reproduction under-converged on the simulated LIDC
task (PWM-LDCT v0.5, LIDC-only split). Reported v0.5 test numbers:

| dose | PSNR (dB) | CNR |
|------|-----------|-----|
| r010 | 42.28     | 0.21 |
| r025 | 43.06     | 0.22 |
| r050 | 43.34     | 0.22 |

PSNR stayed 5--10 dB below the convolutional baselines and CNR was flat across
dose, which broke the "fidelity gain implies detectability gain" assumption and
made the model an outlier in the detectability sweep.

Root cause (see `ctformer_significance_audit.md`): a **training-convergence
issue, not a model defect**. The wrapper used the official published
configuration (embed_dim 768, depth 12, lr 1e-4, batch 1, whole-slice input),
which is heavily over-parameterized (87.6M parameters) for the v0.5 task and
did not converge in the reproduction budget.

## 2. Fix

Added a compact variant `ctformer_small` to `ctformer_wrapper.py`
(`variant="compact"`: embed_dim 192, depth 6, ~2.42M parameters), registered
under `get_model("ctformer_small")`, and retrained from scratch:

- model: `ctformer_small` (embed_dim 192 / depth 6 / 2.42M params)
- optimizer: AdamW, lr 1e-4
- batch size: 4, num_workers: 4
- steps: 20,000 (max-steps), seed 42
- training loss: 5.3e-4 (1k steps) -> 7e-6 (7.4k steps) -> 2e-6 (20k steps)
- checkpoint: `baselines/checkpoints/ctformer_small_retrain.pt` (9.7 MB)
- legacy under-converged checkpoint archived as `ctformer_pre_retrain.pt`

Note on hardware: the base Anaconda environment shipped a CPU-only torch
(2.13.0+cpu); training and the first evaluations therefore ran on CPU. GPU
torch (cu128) was installed afterwards and the remaining evaluations (full-scale
fidelity n=764, 5-seed detectability) run on the two RTX 4090s.

## 3. Results (seed 42, n = 30 test slices / dose, same protocol as all baselines)

| dose | PSNR (dB) | SSIM | CNR |
|------|-----------|------|-----|
| r010 | 47.63     | 0.980| 0.52 |
| r025 | 51.33     | 0.990| 0.98 |
| r050 | 53.73     | 0.994| 1.44 |

vs. RED-CNN (same n=30): r010 47.66, r025 50.64, r050 52.27
vs. LEARN (same n=30): 48.17, 52.14, 54.94

Interpretation:
- Fidelity is fully repaired: r010 is on par with RED-CNN, r025/r050 now
  exceed RED-CNN (and approach LEARN at r050).
- CNR improved ~2.5--6.5x (0.21/0.22/0.22 -> 0.52/0.98/1.44) but **still stays
  below the Rose criterion (CNR 3.0) at every simulated dose**, so the
  simulated knee remains "not reached" for CTformer.
- The blur trap (CNR 1.67/2.99/4.04) still out-scores the retrained CTformer on
  the simulated CNR task, which re-affirms the manuscript's core point: a
  CNR-only criterion cannot separate the blur trap from learned methods;
  BandER remains the discriminating dimension (8.9--15.6x separation on the
  real AAPM paired data).

## 4. Files touched

- `baselines/src/pwm_ldct_baselines/ctformer_wrapper.py` (+ compact variant)
- `baselines/checkpoints/ctformer_small_retrain.pt` (new, released)
- `baselines/checkpoints/ctformer_pre_retrain.pt` (legacy archive)
- `baselines/results/ctformer_results_det.json` (overwritten with retrained
  seed-42 n=30 values; legacy saved as `ctformer_results_det_legacy.json`)
- `baselines/results/ctformer_results.json` (full-scale fidelity, overwritten;
  legacy saved as `ctformer_results.json.legacy`)
- `output/dose_detectability_curve.png` + `output/dose_detectability_stats.json`
  (rebuilt from retrained values)
- `paper_draft/manuscript.tex`: CTformer rows in Tables
  `tab:baselines_v05` / `tab:detectability_v05`, figure caption
  `fig:dose_detectability`, and a retraining note after Table `tab:baselines_v05`
  (backup: `manuscript_tex_pre_ctformer_retrain.tex`)

## 5. Remaining

- 5-seed detectability eval (fixed seed set 42/2023/7/12345/999) for the
  slice-level bootstrap table (Table `tab:lidc_sim_knee_ci` CTformer row).
- Re-check `metrics_discrimination_compare.md` and the simulated bootstrap
  report with the retrained numbers.
