# `pwm_ldct_recon` — WS-3 reference reconstruction method

The improvable reference method of the WS-3 plan: an **unrolled iterative reconstruction**
(physical Radon prior + a shared-weight learned denoiser per iteration) with **deep-ensemble
uncertainty quantification**, that emits the Phase-3 derived-data corpus the *Scientific Data*
Data Descriptor (`../paper_draft/manuscript.tex`) describes.

This package is the implementation the manuscript's Methods + Supplementary Table S1 specify;
the synthetic `../fixture/` is its stand-in for CI, and `../corpus_emit` + `../deposit` are the
downstream tools it drives.

## Layout

| Module | Role |
|---|---|
| `physics.py` | Parallel-beam Radon forward / backprojection / FBP (differentiable). Self-contained drop-in for `pwm_core ct_radon` (not vendored here). The data-term gradient is taken by **autograd through `forward`**, so the adjoint is always exactly consistent. |
| `measurement.py` | Forms the data term from **measured** low-dose projections (`get_series_projections`, fan-beam `[V,C,R]`) or **simulated** (`op.forward(low)`); records `real_paired`/`simulated` provenance. Both **axial** (row→slice) and **helical** (360°-LI single-slice rebinning) geometries → fan→parallel rebinning onto the parallel-beam operator. Only genuinely insufficient geometry falls back to simulated. |
| `models/unet.py` | Compact residual U-Net denoiser `f_theta` (S1: 4 stages, `(32,64,128,256)`, GroupNorm/GELU). |
| `models/unrolled.py` | K-step unrolled loop: `x ← f_theta(x − τ·Rᵀ(Rx − y))`, learned τ, weights shared (S1). |
| `data.py` | `PairedSlices` over the WS-1 `pwm_ldct_loader` (same contract as the WS-1 baselines) + `SyntheticPairs` for tests. |
| `train.py` | Train one seeded member (AdamW + cosine/warmup, L1 on HU — S1). |
| `ensemble.py` | M seeded members → `recon_mean` + per-pixel `uncertainty_sigma` (ensemble std). |
| `detector.py` | **Frozen** task detector plug point (nnDetection/LUNA16; manuscript `sec:detector`) + a deterministic stub for the pipeline/tests. |
| `emit_corpus.py` | **The Phase-3 corpus run.** Ensemble inference over scans × doses → the deposit record layout → credentials + manifest + construction-check. |
| `config.py` | `ReconConfig` / `EnsembleConfig` mirroring Supplementary Table S1 cell-for-cell. |

## Quickstart

```bash
pip install -e .            # needs torch (CPU is fine for the smoke run)
pwm-recon info             # resolved S1 config + parameter counts
pwm-recon smoke /tmp/corpus  # synthetic end-to-end: train tiny ensemble → emit → deposit-verify
pytest                     # 16 CPU tests (physics, model, train, ensemble, emit→deposit)
```

`smoke` is the one-command reproduction that runs anywhere with no Phase-3 data: it trains a
2-member toy ensemble, reconstructs two synthetic scans, and proves the emitted corpus passes
the credential audit, the manifest checksum, and the `error_abs == |recon − x_ref|` construction
check — the same pipeline a real run exercises at scale.

## Running the real Phase-3 corpus

The real run is **GPU- and data-gated** (no GPU on the current host; the harmonized WS-1 HDF5
tree and the pinned LUNA16 detector weights must be present):

```bash
pwm-recon train-ensemble --data-root <WS-1 tree> --out ensemble.pt    # 3.1 train (5 seeds)
# then wire the held-out split + pinned detector + cohort scores into emit_corpus.run
#   (see cli.py `cmd_emit`) and emit the corpus → fills every \todo table in the manuscript.
```

## Notes / honesty

- **Parameters per member ≈ 3.1M** as realized (S1 says "≈4M"; that cell is finalised at freeze —
  widen the bottleneck if exact parity is wanted).
- **Measurement model.** Reconstruction/emit can use the **measured** low-dose projections
  (`measurement.py`: fan→parallel rebinning of `get_series_projections`, with `real_paired`
  provenance) — pass them via `emit_corpus.ScanInput.low_dose_proj`. Both **axial** and
  **helical** (360°-LI single-slice rebinning) acquisitions are supported; without projections,
  or with genuinely insufficient geometry, it falls back to the simulated `y = R(low)`. Training
  still uses the simulated measurement (`data.PairedSlices`). The real-projection numbers remain
  GPU- + data-gated (validated here on synthetic geometry: SSR recovers the target z-plane).
- `torch` is a real dependency (~190 MB); the lightweight WS-3 deposit CI does **not** install it,
  so these tests run in a separate torch-enabled environment, exactly as the WS-1 baselines do.
